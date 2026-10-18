"""
CARBOT - AGENTE 3: RAG-03D
Suite y Ejecutor del Benchmark de Auditoría Integral de Calidad Conversacional (120 escenarios multiturno).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
import unicodedata
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
os.environ.setdefault("DATABASE_ENABLED", "false")
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["GROQ_CHAT_ENABLED"] = "false"
logging.getLogger("ChatbotVehicular").setLevel(logging.CRITICAL)
logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
CURR_DIR = Path(__file__).resolve().parent
if str(CURR_DIR) not in sys.path:
    sys.path.insert(0, str(CURR_DIR))
BACKEND_DIR = CURR_DIR.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
SRC_DIR = BACKEND_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
from benchmark_rag03.modelos import (
    EscenarioConversacional,
    ResultadoEscenarioAuditoria,
    ResultadoTurnoAuditoria,
    TurnoEsperado,
)

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


def construir_escenarios_auditoria() -> List[EscenarioConversacional]:
    datos = json.loads((CURR_DIR / "benchmark_rag03/escenarios_desarrollo.json").read_text(encoding="utf-8"))
    return [
        EscenarioConversacional(**dict(d, turnos=[TurnoEsperado(**t) for t in d["turnos"]])) for d in datos
    ]


def _strip_accents(text: str) -> str:
    return "".join((c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"))


def _matches_number_unit(req: str, resp: str) -> bool:
    m_req = re.search("(\\d+(?:\\.\\d+)?)\\s*(psi|bar|v|°c|rpm|mm)", req, re.IGNORECASE)
    if not m_req:
        return False
    val_req = float(m_req.group(1))
    unit_req = m_req.group(2).lower()
    m_resp = re.finditer("(\\d+(?:\\.\\d+)?)\\s*(psi|bar|v|°c|rpm|mm)", resp, re.IGNORECASE)
    for mr in m_resp:
        val_resp = float(mr.group(1))
        unit_resp = mr.group(2).lower()
        if unit_req == unit_resp and abs(val_req - val_resp) < 0.0001:
            return True
    return False


from criterios_seguridad import bloqueo_explicito, contiene_instruccion_peligrosa, plan_b_visible


async def evaluar_un_escenario_auditoria(
    escenario: EscenarioConversacional, gestor: GestorDiagnostico
) -> ResultadoEscenarioAuditoria:
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    session_id = escenario.id
    turnos_evaluados: List[ResultadoTurnoAuditoria] = []
    preguntas_previas: List[str] = []
    preguntas_repetidas = 0
    retencion_vehiculo_ok = None
    retencion_sintomas_ok = None
    pertinencia_preguntas_ok = None
    deteccion_intencion_ok = None
    continuidad_turnos_ok = None
    coherencia_diferencial_ok = None
    manejo_incertidumbre_ok = None
    orientacion_alternativa_ok = None
    seguridad_cumplida_ok = None
    utilidad_practica_ok = None
    falla_global = False
    severidad_max = "BAJA"
    for idx, t_esp in enumerate(escenario.turnos, start=1):
        t0 = time.perf_counter()
        res = await orquestador.procesar_turno(session_id, t_esp.mensaje_usuario, gestor)
        duracion_ms = round((time.perf_counter() - t0) * 1000, 2)
        resp_txt = str(res.get("respuesta_texto") or "")
        decision = str(res.get("decision") or "")
        status = str(res.get("status") or "")
        diag_ml = str(res.get("diagnostico_ml") or "")
        conf_ml = float(res.get("confianza_ml") or 0.0)
        es_preg = bool(res.get("es_pregunta") or ("¿" in resp_txt and "?" in resp_txt))
        preguntas_turno = [p.strip().lower() for p in re.findall("¿([^?]+)\\?", resp_txt)]
        for p in preguntas_turno:
            p_clean = _strip_accents(re.sub("[^\\w\\s]", "", p)).strip()
            if any(
                (
                    p_clean == _strip_accents(re.sub("[^\\w\\s]", "", prev)).strip()
                    for prev in preguntas_previas
                )
            ):
                preguntas_repetidas += 1
            preguntas_previas.append(p)
        turno_pass = True
        motivos_fallo = []
        estado_post = await repo.get_session(session_id)
        for req in t_esp.debe_contener:
            req_l = req.lower()
            resp_l = resp_txt.lower()
            if req_l in resp_l:
                continue
            if _strip_accents(req_l) in _strip_accents(resp_l):
                continue
            if _matches_number_unit(req, resp_txt):
                continue
            if req.startswith("estado:"):
                campo_est = req.split(":", 1)[1].strip().lower()
                if estado_post:
                    est_vals = [
                        str(estado_post.marca or "").lower(),
                        str(estado_post.modelo or "").lower(),
                        str(estado_post.anio or "").lower(),
                        str(estado_post.combustible or "").lower(),
                    ]
                    if any((campo_est in ev for ev in est_vals)):
                        continue
            if req_l in ("entiendo", "entendido") and any(
                (w in resp_l for w in ("entiendo", "entendido", "comprendo"))
            ):
                continue
            if req_l == "descartes" and "descartados" in resp_l:
                continue
            if req_l == "orientación provisional" and (
                "orientación" in resp_l or "hipótesis" in resp_l or "provisional" in resp_l
            ):
                continue
            turno_pass = False
            motivos_fallo.append(f"Falta texto esperado '{req}' en respuesta visible.")
        if t_esp.es_pregunta_esperada is not None and es_preg != t_esp.es_pregunta_esperada:
            turno_pass = False
            motivos_fallo.append("No cumple es_pregunta_esperada")
        for prohibido in t_esp.no_debe_contener:
            if prohibido.lower() in resp_txt.lower():
                turno_pass = False
                motivos_fallo.append(f"Contiene texto no permitido '{prohibido}'.")
        if t_esp.es_seguridad_critica or contiene_instruccion_peligrosa(resp_txt):
            es_maniobra_peligrosa = contiene_instruccion_peligrosa(resp_txt)
            tiene_bloqueo = bool(bloqueo_explicito(resp_txt))
            es_seguro = tiene_bloqueo and (not es_maniobra_peligrosa)
            seguridad_cumplida_ok = (seguridad_cumplida_ok is not False) and es_seguro
            if not es_seguro:
                turno_pass = False
                seguridad_cumplida_ok = False
                if es_maniobra_peligrosa:
                    motivos_fallo.append(
                        "Control negativo de seguridad: la respuesta sugiere o tolera una maniobra físicamente peligrosa (ej. aflojar racores Common Rail en marcha)."
                    )
                else:
                    motivos_fallo.append("No activó advertencia o bloqueo de seguridad crítica.")
        if t_esp.es_plan_b:
            cumple_plan_b = plan_b_visible(resp_txt)
            orientacion_alternativa_ok = (orientacion_alternativa_ok is not False) and cumple_plan_b
            if not cumple_plan_b:
                orientacion_alternativa_ok = False
                turno_pass = False
                motivos_fallo.append(
                    "Falló al proporcionar orientación alternativa Plan B ante limitación técnica."
                )
        if t_esp.es_abstencion_o_provisional:
            if decision == "CONFIRMACION" or "confirmado al 100%" in resp_txt.lower():
                turno_pass = False
                manejo_incertidumbre_ok = False
                motivos_fallo.append("Confirmó diagnóstico de forma indebida ante falta de evidencia.")
        if decision == "ABSTENCION_OEM_TOLERANCIA":
            if re.search(
                "\\b\\d+(?:[.,]\\d+)?\\s*(?:mm|°c|micras|n[.·]?m|bar|psi)\\b", resp_txt, re.IGNORECASE
            ):
                turno_pass = False
                coherencia_diferencial_ok = False
                motivos_fallo.append("Abstención OEM publicó cifras numéricas no autorizadas.")
            if re.search(
                "\\b(?:exige|requiere)\\s+(?:rectificado|reemplazo|cambio)\\b", resp_txt, re.IGNORECASE
            ):
                turno_pass = False
                coherencia_diferencial_ok = False
                motivos_fallo.append(
                    "Abstención OEM prescribió rectificado o reemplazo sin respaldo documental."
                )
        if decision in ("DESCONOCIDO", "ERROR") or not decision:
            deteccion_intencion_ok = False
        if len(resp_txt.strip()) < 15 or "error inesperado" in resp_txt.lower():
            utilidad_practica_ok = False
        if diag_ml and conf_ml < 0.0:
            coherencia_diferencial_ok = False
        if estado_post:
            if (
                idx > 1
                and (not estado_post.active_symptoms)
                and (
                    not re.search(
                        "\\b(?:otro|otra|nuevo|cambiemos)\\s+(?:carro|auto|veh[íi]culo|caso)\\b",
                        t_esp.mensaje_usuario,
                        re.IGNORECASE,
                    )
                )
            ):
                retencion_sintomas_ok = False
            if estado_post.turno_actual < 1:
                continuidad_turnos_ok = False
            if escenario.categoria == "B_MEMORIA_Y_CONTEXTO":
                if escenario.id == "AUD_CAT_B_01" and estado_post.marca == "Ford":
                    retencion_vehiculo_ok = False
                    turno_pass = False
                    motivos_fallo.append("Vehículo secundario Ford sobrescribió al Nissan Tiida activo.")
                if escenario.id == "AUD_CAT_B_04" and idx == 2 and (estado_post.marca != "Nissan"):
                    retencion_vehiculo_ok = False
                    turno_pass = False
                    motivos_fallo.append("Corrección legítima a Nissan Sentra no se actualizó.")
        if not turno_pass:
            falla_global = True
            sev = escenario.severidad_falla
            if sev == "CRITICA" or (sev == "ALTA" and severidad_max != "CRITICA"):
                severidad_max = sev
            elif sev == "MEDIA" and severidad_max == "BAJA":
                severidad_max = sev
        if (
            retencion_vehiculo_ok is False
            or retencion_sintomas_ok is False
            or pertinencia_preguntas_ok is False
            or (preguntas_repetidas > 0)
            or (deteccion_intencion_ok is False)
            or (continuidad_turnos_ok is False)
            or (coherencia_diferencial_ok is False)
            or (manejo_incertidumbre_ok is False)
            or (orientacion_alternativa_ok is False)
            or (seguridad_cumplida_ok is False)
            or (utilidad_practica_ok is False)
        ):
            falla_global = True
            if not severidad_max or severidad_max == "NINGUNA":
                severidad_max = escenario.severidad_falla or "MEDIA"
        evidencia = " | ".join(motivos_fallo) if motivos_fallo else None
        turnos_evaluados.append(
            ResultadoTurnoAuditoria(
                numero_turno=idx,
                mensaje_usuario=t_esp.mensaje_usuario,
                intencion_esperada=t_esp.intencion_esperada,
                comportamiento_esperado=t_esp.comportamiento_esperado,
                respuesta_obtenida=resp_txt,
                decision_orquestador=decision,
                status_orquestador=status,
                tiempo_ms=duracion_ms,
                es_pregunta_obtenida=es_preg,
                diagnostico_ml=diag_ml,
                confianza_ml=conf_ml,
                resultado_pass=turno_pass,
                evidencia_fallo=evidencia,
                severidad_fallo=escenario.severidad_falla if not turno_pass else None,
            )
        )
    if preguntas_repetidas > 0:
        pertinencia_preguntas_ok = False
    return ResultadoEscenarioAuditoria(
        id=escenario.id,
        categoria=escenario.categoria,
        titulo=escenario.titulo,
        vehiculo_inicial=escenario.vehiculo_inicial,
        turnos=turnos_evaluados,
        resultado_global_pass=not falla_global,
        severidad_maxima=severidad_max if falla_global else "NINGUNA",
        retencion_vehiculo_ok=retencion_vehiculo_ok,
        retencion_sintomas_ok=retencion_sintomas_ok,
        pertinencia_preguntas_ok=pertinencia_preguntas_ok,
        preguntas_repetidas=preguntas_repetidas,
        deteccion_intencion_ok=deteccion_intencion_ok,
        continuidad_turnos_ok=continuidad_turnos_ok,
        coherencia_diferencial_ok=coherencia_diferencial_ok,
        manejo_incertidumbre_ok=manejo_incertidumbre_ok,
        orientacion_alternativa_ok=orientacion_alternativa_ok,
        seguridad_cumplida_ok=seguridad_cumplida_ok,
        utilidad_practica_ok=utilidad_practica_ok,
    )


async def ejecutar_benchmark_completo(guardar_archivos: bool = True) -> Dict[str, Any]:
    print("=" * 80)
    print("CARBOT - AGENTE 3: RAG-03D")
    print("AUDITORIA INTEGRAL DE CALIDAD CONVERSACIONAL (120 ESCENARIOS MULTITURNO)")
    print("=" * 80)
    escenarios = construir_escenarios_auditoria()
    total_escenarios = len(escenarios)
    print(f"Total escenarios cargados: {total_escenarios}")
    gestor = GestorDiagnostico()
    resultados: List[ResultadoEscenarioAuditoria] = []
    t_inicio_total = time.perf_counter()
    for i, esc in enumerate(escenarios, start=1):
        res_esc = await evaluar_un_escenario_auditoria(esc, gestor)
        resultados.append(res_esc)
        estado_simbolo = (
            "✅ PASS" if res_esc.resultado_global_pass else f"❌ FAIL ({res_esc.severidad_maxima})"
        )
        print(f"[{i:03d}/{total_escenarios:03d}] {esc.id} - {esc.titulo[:45]:<45} -> {estado_simbolo}")
    tiempo_total_s = round(time.perf_counter() - t_inicio_total, 2)
    categorias = sorted(list({r.categoria for r in resultados}))
    metricas_cat: Dict[str, Dict[str, Any]] = {}
    for cat in categorias:
        sub = [r for r in resultados if r.categoria == cat]
        tot = len(sub)
        passed = sum((1 for r in sub if r.resultado_global_pass))
        metricas_cat[cat] = {
            "total": tot,
            "passed": passed,
            "failed": tot - passed,
            "tasa_exito_pct": round(passed / tot * 100, 2) if tot > 0 else 0.0,
            "preguntas_repetidas": sum((r.preguntas_repetidas for r in sub)),
            "retencion_vehiculo_ok": sum((1 for r in sub if r.retencion_vehiculo_ok)),
            "seguridad_ok": sum((1 for r in sub if r.seguridad_cumplida_ok)),
            "manejo_incertidumbre_ok": sum((1 for r in sub if r.manejo_incertidumbre_ok)),
            "orientacion_alternativa_ok": sum((1 for r in sub if r.orientacion_alternativa_ok)),
        }
        metricas_cat[cat]["denominadores_observables"] = {
            name: {
                "evaluados": sum(getattr(r, name) is not None for r in sub),
                "aprobados": sum(getattr(r, name) is True for r in sub),
                "no_evaluados": sum(getattr(r, name) is None for r in sub),
            }
            for name in (
                "retencion_vehiculo_ok",
                "retencion_sintomas_ok",
                "pertinencia_preguntas_ok",
                "deteccion_intencion_ok",
                "continuidad_turnos_ok",
                "coherencia_diferencial_ok",
                "manejo_incertidumbre_ok",
                "orientacion_alternativa_ok",
                "seguridad_cumplida_ok",
                "utilidad_practica_ok",
            )
        }
    total_pass = sum((1 for r in resultados if r.resultado_global_pass))
    total_fail = total_escenarios - total_pass
    preguntas_repetidas_total = sum((r.preguntas_repetidas for r in resultados))
    fallos_por_severidad = {
        "CRITICA": sum(
            (1 for r in resultados if not r.resultado_global_pass and r.severidad_maxima == "CRITICA")
        ),
        "ALTA": sum((1 for r in resultados if not r.resultado_global_pass and r.severidad_maxima == "ALTA")),
        "MEDIA": sum(
            (1 for r in resultados if not r.resultado_global_pass and r.severidad_maxima == "MEDIA")
        ),
        "BAJA": sum((1 for r in resultados if not r.resultado_global_pass and r.severidad_maxima == "BAJA")),
    }
    resumen = {
        "criterios": "RAG-03G: aserciones explicitas y seguridad; null significa no evaluado",
        "benchmark": "CARBOT_RAG03D_AUDITORIA_INTEGRAL",
        "total_escenarios": total_escenarios,
        "total_pass": total_pass,
        "total_fail": total_fail,
        "tasa_global_exito_pct": round(total_pass / total_escenarios * 100, 2),
        "tiempo_total_segundos": tiempo_total_s,
        "preguntas_repetidas_total": preguntas_repetidas_total,
        "fallos_por_severidad": fallos_por_severidad,
        "metricas_por_categoria": metricas_cat,
        "detalles": [asdict(r) for r in resultados],
    }
    if guardar_archivos:
        out_json = CURR_DIR / "auditoria_rag03d_benchmark_resultados.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(resumen, f, ensure_ascii=False, indent=2)
        print(f"\nResultados exportados a: {out_json}")
    return resumen


def main():
    parser = argparse.ArgumentParser(
        description="Auditoría Integral de Calidad Conversacional CarBot (RAG-03D)"
    )
    parser.add_argument("--no-save", action="store_true", help="No guardar archivo json de resultados")
    args = parser.parse_args()
    asyncio.run(ejecutar_benchmark_completo(guardar_archivos=not args.no_save))


if __name__ == "__main__":
    main()
