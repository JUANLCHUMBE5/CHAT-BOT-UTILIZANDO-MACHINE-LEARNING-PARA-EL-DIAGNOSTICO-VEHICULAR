"""Cinco ablaciones explícitas; regresión observada, nunca exactitud clínica de campo.

Alex se carga solo desde un fixture externo autorizado con SHA256 obligatorio.
Sus mensajes se reproducen en secuencia mediante el orquestador en memoria.
No se concatena historia para simular una conversación ni se publican datos privados.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import time
import unicodedata
from pathlib import Path
from types import SimpleNamespace

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from src.config import settings
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.diagnostico.enrutador_sistema import (
    detectar_areas_tecnicas,
    filtrar_causas,
    resolver_sistema_activo,
)
from src.core.diagnostico.models import PrediccionML
from src.core.diagnostico.procesador_texto.clasificacion_ml import ejecutar_clasificacion_ml
from src.core.gestor_diagnostico import GestorDiagnostico


def norm(value):
    return " ".join(''.join(c for c in unicodedata.normalize('NFKD', str(value).lower())
                           if not unicodedata.combining(c)).split())


def coincide(pred, referencia):
    """Igualdad de etiqueta normalizada; sin substring ni equivalencias de piezas."""
    return bool(norm(pred)) and norm(pred) == norm(referencia)


def cargar_fixture(path, sha256):
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != sha256:
        raise ValueError('Fixture distinto del hash autorizado')
    return json.loads(data)


def evaluar_variantes(gestor, caso):
    text = caso['texto']
    clean = gestor._purificar_sintoma_para_vectorizador_ml(text)
    original = gestor.modelo_ml.predecir_top_fallas_svm_raw(clean, limite=12)
    adjusted = gestor.modelo_ml.predecir_top_fallas(clean, limite=12)
    raw = [PrediccionML(**p) for p in original]
    system = resolver_sistema_activo(text)
    routed = filtrar_causas(system, raw, text) if system else raw
    # Rules receive original SVM values; routing is explicitly disabled.
    raw_model = SimpleNamespace(predecir_top_fallas=lambda *args, **kw: original[:kw.get('limite', 3)])
    proxy = SimpleNamespace(modelo_ml=raw_model,
                            _purificar_sintoma_para_vectorizador_ml=lambda x: x,
                            _es_perdida_potencia_bajo_carga=gestor._es_perdida_potencia_bajo_carga)
    rules = ejecutar_clasificacion_ml(proxy, text, None, None, detectar_areas_tecnicas(text),
                                     system, None, False, False, aplicar_enrutamiento=False)[2]
    result = gestor.procesar_consulta_texto(texto_usuario=text, session_id='benchmark-'+caso['id'],
                                          marca_modelo=caso.get('vehiculo') or None, proveedor='web')
    return {
        'svm_original': [p.model_dump() for p in raw[:3]],
        'svm_ajustado': adjusted[:3],
        'svm_enrutador': [p.model_dump() for p in routed[:3]],
        'svm_reglas': [p.model_dump() for p in rules[:3]],
        'hibrido': [p.model_dump() for p in result.predicciones_ml[:3]],
        'decision_hibrida': result.diagnostico_ml,
        'abstention_reason': result.motivo_abstencion,
        'modo': result.modo_diagnostico,
        'latencias_ms': {'ml': result.tiempo_ml_ms, 'rag': result.tiempo_rag_ms,
                         'llm': result.tiempo_llm_ms, 'pipeline': result.tiempo_total_ms},
    }


async def reproducir_alex(data, gestor):
    conversations = {c['case_id']: c for c in data.get('conversaciones', [])}
    orch = OrquestadorConversacion(InMemoryConversationRepository())
    records = []
    for index, case in enumerate(data['diagnosticos'], 1):
        conversation = conversations.get(case['case_id'], {})
        turns = [m['texto'] for m in conversation.get('mensajes', []) if m.get('direccion') == 'entrada']
        outputs = []
        for text in turns:
            result = await orch.procesar_turno(session_id=f'alex-regression-{index}', texto_usuario=text,
                                               gestor_diagnostico=gestor, proveedor='web',
                                               marca_modelo=case.get('vehiculo'))
            state = result.get('estado')
            outputs.append({'decision': result.get('diagnostico_ml'), 'case_id': getattr(state, 'case_id', None),
                            'status': result.get('status')})
        records.append({'id': f'A_{index:02d}', 'turn_count': len(turns), 'results': outputs,
                        'reference': case.get('falla_principal'),
                        'reference_status': 'historica_no_equivalente_a_confirmacion_fisica_verificada'})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--alex-fixture', type=Path)
    parser.add_argument('--alex-sha256')
    args = parser.parse_args()
    if args.alex_fixture and not args.alex_sha256:
        parser.error('--alex-sha256 obligatorio para verificar el fixture externo')
    settings.groq_chat_enabled = False
    settings.groq_api_key = ''
    settings.gemini_api_key = ''
    fixture = BACKEND_DIR / 'tests/fixtures/generalizacion_v1'
    manifest = json.loads((fixture/'manifest.json').read_text(encoding='utf8'))
    data = cargar_fixture(fixture/manifest['file'], manifest['sha256'])
    gestor = GestorDiagnostico()
    gestor._registrar_en_tracker = lambda **kw: None
    report = {'version': 2, 'scope': data['scope'], 'independent_validation': False,
              'fixture_sha256': manifest['sha256'], 'groups': {}}
    variants = ('svm_original', 'svm_ajustado', 'svm_enrutador', 'svm_reglas', 'hibrido')
    for group, cases in data['groups'].items():
        rows = []
        for case in cases:
            start = time.perf_counter()
            result = evaluar_variantes(gestor, case)
            row = {'id': case['id'], 'reference': case['gt'], 'outputs': result,
                   'duration_ms': (time.perf_counter()-start)*1000, 'scores': {}}
            for variant in variants:
                labels = [p['falla'] for p in result[variant]]
                decision = result['decision_hibrida'] if variant == 'hibrido' else (labels[0] if labels else '')
                row['scores'][variant] = {'top1': coincide(decision, case['gt']),
                                         'top3': any(coincide(p, case['gt']) for p in labels)}
            rows.append(row)
        report['groups'][group] = {'n': len(cases), 'rows': rows, 'metrics': {
            v: {'top1': sum(r['scores'][v]['top1'] for r in rows),
                'top3': sum(r['scores'][v]['top3'] for r in rows)} for v in variants}}
    report['groups']['A'] = {'n_expected': 30, 'status': 'fixture_externo_no_proporcionado'}
    if args.alex_fixture:
        alex = cargar_fixture(args.alex_fixture, args.alex_sha256)
        report['groups']['A'] = {'fixture_sha256': args.alex_sha256,
                                 'records': asyncio.run(reproducir_alex(alex, gestor)),
                                 'scope': 'regresion_multiturno_en_memoria_no_e2e_webhook'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({g: {k: v for k, v in info.items() if k not in ('rows', 'records')}
                      for g, info in report['groups'].items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
