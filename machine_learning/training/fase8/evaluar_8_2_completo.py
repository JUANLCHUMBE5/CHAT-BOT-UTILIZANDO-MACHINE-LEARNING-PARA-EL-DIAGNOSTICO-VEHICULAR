"""
Evaluador Completo y Auditoría de la Iteración 8.2 (Candidata Fase 8).
Mide y genera el reporte oficial de:
1. Métricas RAG sobre DEV (Hit@1, Hit@3, Hit@5, MRR).
2. Métricas E2E sobre DEV (E2E estricto, diferencial, incorrecto).
3. Matriz de rescate y degradación ML -> E2E.
4. Desempeño del auto-interrogador (sensibilidad y especificidad).
5. Latencias de procesamiento (ML, RAG, LLM, Total E2E).
6. Trazabilidad criptográfica SHA-256.
"""

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
if str(RAIZ / "backend") not in sys.path:
    sys.path.insert(0, str(RAIZ / "backend"))

from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60

from src.core.gestor_diagnostico import GestorDiagnostico


def calcular_sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def evaluar_fase_8_2():
    print("=" * 80)
    print("EVALUACIÓN INTEGRAL FASE 8.2 (RAG + FUSIÓN + E2E + AUTO-INTERROGADOR)")
    print("=" * 80)

    gestor = GestorDiagnostico()
    motor_rag = gestor.motor_rag
    total_casos = len(CASOS_DEV_60)

    # 1. Variables acumuladoras
    rag_hit1 = 0
    rag_hit3 = 0
    rag_hit5 = 0
    rag_mrr_sum = 0.0

    e2e_estricto = 0
    e2e_diferencial = 0
    e2e_incorrecto = 0

    # Matriz ML -> E2E
    ml_top1_a_e2e_correcto = 0     # (a) ML Top-1 correcto -> E2E correcto
    ml_top1_inc_a_e2e_rescate = 0  # (b) ML Top-1 incorrecto -> E2E rescatado
    ml_top1_corr_a_e2e_degradado = 0 # (c) ML Top-1 correcto -> E2E degradado
    ml_top3_tenia_gt_e2e_perdio = 0  # (d) ML Top-3 contenía GT pero E2E lo perdió

    # Auto-interrogador: conjunto de evaluación de ambigüedad clínica
    CASOS_DEV_AMBIGUOS_20 = [
        "Mi carro vibra al andar",
        "Tironea cuando acelero en pista",
        "No arranca en la mañana",
        "Se me apaga en marcha",
        "Tiene un ruido seco en el tren delantero al pasar baches",
        "El pedal de freno está raro",
        "Se recalienta el carro en el tráfico",
        "Pierde fuerza en subida y prende el check",
        "Huele a quemado cuando manejo",
        "Zumba fuerte cuando rueda",
        "Le cuesta entrar los cambios",
        "Tiembla todo el carro",
        "Consume demasiado combustible",
        "Hace un ruido en el motor",
        "Bota humo por el escape",
        "El timón tiene juego y vibra",
        "Las luces del tablero parpadean",
        "El aire acondicionado no enfría",
        "Tiene un ruido al doblar",
        "Se queda acelerado solo",
    ]

    from src.core.diagnostico.auto_interrogador import evaluar_auto_pregunta_descarte

    ambiguos_verdaderos = len(CASOS_DEV_AMBIGUOS_20)
    ambiguos_detectados = 0
    for q_amb in CASOS_DEV_AMBIGUOS_20:
        p_top = gestor.modelo_ml.predecir_top_fallas(q_amb, limite=3)
        t1_f = p_top[0]["falla"] if p_top else ""
        t1_p = p_top[0]["probabilidad"] if p_top else 0.5
        ap = evaluar_auto_pregunta_descarte(q_amb, t1_f, t1_p, p_top)
        if ap and ap.es_necesaria:
            ambiguos_detectados += 1

    claros_verdaderos = total_casos
    claros_no_interrumpidos = 0

    # Latencias
    tiempos_ml = []
    tiempos_rag = []
    tiempos_llm = []
    tiempos_total = []

    detalles_eval = []

    for caso in CASOS_DEV_60:
        cid = caso["id"]
        sintoma = caso["sintoma"]
        falla_esperada = caso["falla_esperada"]
        dtc = caso.get("codigo_dtc")
        dtcs = [dtc] if dtc else []
        es_ambiguo = caso.get("es_ambiguo_intencional", False)

        # A. ML puro y jerárquico
        t0_ml = time.perf_counter()
        pred_top = gestor.modelo_ml.predecir_top_fallas(sintoma, limite=3)
        pred_sis = gestor.modelo_ml.predecir_sistema(sintoma)
        dt_ml = (time.perf_counter() - t0_ml) * 1000
        tiempos_ml.append(dt_ml)

        top1_falla_ml = pred_top[0]["falla"] if pred_top else "DESCONOCIDO"
        conf_top1_ml = pred_top[0]["probabilidad"] if pred_top else 0.0
        top3_fallas_ml = [p["falla"] for p in pred_top]

        es_top1_ml = (top1_falla_ml == falla_esperada)
        es_top3_ml = any(f == falla_esperada for f in top3_fallas_ml)

        # B. RAG Multi-Hit & MRR
        t0_rag = time.perf_counter()
        import faiss

        from src.infrastructure.rag.query_builder import construir_consulta_hibrida
        from src.infrastructure.rag.relevance_filter import reordenar_candidatos_rag

        c_hib = construir_consulta_hibrida(sintoma, pred_sis, pred_top, dtcs)
        c_exp = motor_rag._expandir_consulta(c_hib)
        vec = motor_rag.vectorizador.transform([c_exp]).toarray().astype(np.float32)
        faiss.normalize_L2(vec)
        sims, inds = motor_rag.faiss_index.search(vec, k=30)

        cands = []
        for kidx in range(len(inds[0])):
            didx = int(inds[0][kidx])
            if 0 <= didx < len(motor_rag.documentos):
                cands.append({
                    "indice": didx,
                    "titulo": motor_rag.titulos[didx],
                    "documento": motor_rag.documentos[didx],
                    "similitud": float(sims[0][kidx]),
                    "metadatos": motor_rag.metadatos_procedimientos[didx]
                })

        cands_reord = reordenar_candidatos_rag(
            cands,
            macro_sistema=pred_sis,
            top_fallas=pred_top,
            codigos_dtc=dtcs,
            confianza_ml=conf_top1_ml,
        )
        dt_rag = (time.perf_counter() - t0_rag) * 1000
        tiempos_rag.append(dt_rag)

        fallas_rag_ordenadas = [c.get("metadatos", {}).get("falla", "") for c in cands_reord]
        rag_rank = 0
        for r_idx, f_nom in enumerate(fallas_rag_ordenadas[:20], 1):
            if f_nom == falla_esperada:
                rag_rank = r_idx
                break

        if rag_rank == 1:
            rag_hit1 += 1
        if 1 <= rag_rank <= 3:
            rag_hit3 += 1
        if 1 <= rag_rank <= 5:
            rag_hit5 += 1
        if rag_rank > 0:
            rag_mrr_sum += (1.0 / rag_rank)

        # C. Diagnóstico E2E Real (Pipeline Completo con Fusión)
        t0_e2e = time.perf_counter()
        session_id = f"dev_eval_82_{cid}_{int(time.time()*1000)%100000}"
        res_e2e = gestor.procesar_consulta_texto(sintoma, session_id=session_id)
        dt_e2e = (time.perf_counter() - t0_e2e) * 1000
        tiempos_total.append(dt_e2e)
        tiempos_llm.append(res_e2e.tiempo_llm_ms or 0)

        diag_e2e = res_e2e.diagnostico_ml
        preds_e2e = [p.falla for p in (res_e2e.predicciones_ml or [])]

        # Evaluación de auto-interrogador
        activado_interrogador = (res_e2e.estado_sesion == "esperando_autopregunta")
        if not activado_interrogador:
            claros_no_interrumpidos += 1

        # Clasificación E2E Tricotómica
        # 1. Estricto: diag principal es GT, o si era ambiguo, activó con éxito el interrogador
        if diag_e2e == falla_esperada or (es_ambiguo and activado_interrogador):
            e2e_estricto += 1
            categoria_e2e = "ESTRICTO"
        elif any(f == falla_esperada for f in preds_e2e[:3]):
            e2e_diferencial += 1
            categoria_e2e = "DIFERENCIAL"
        else:
            e2e_incorrecto += 1
            categoria_e2e = "INCORRECTO"

        # Matriz de Transición ML -> E2E
        if es_top1_ml:
            if categoria_e2e == "ESTRICTO":
                ml_top1_a_e2e_correcto += 1
            else:
                ml_top1_corr_a_e2e_degradado += 1
        else:
            if categoria_e2e == "ESTRICTO":
                ml_top1_inc_a_e2e_rescate += 1

        if es_top3_ml and categoria_e2e == "INCORRECTO":
            ml_top3_tenia_gt_e2e_perdio += 1

        detalles_eval.append({
            "id": cid,
            "esperada": falla_esperada,
            "top1_ml": top1_falla_ml,
            "conf_ml": round(conf_top1_ml, 3),
            "es_top1_ml": es_top1_ml,
            "es_top3_ml": es_top3_ml,
            "rag_rank": rag_rank,
            "diag_e2e": diag_e2e,
            "categoria_e2e": categoria_e2e,
            "activado_interrogador": activado_interrogador,
        })

    # Resumen cuantitativo
    pct_hit1 = round((rag_hit1 / total_casos) * 100, 2)
    pct_hit3 = round((rag_hit3 / total_casos) * 100, 2)
    pct_hit5 = round((rag_hit5 / total_casos) * 100, 2)
    mrr = round(rag_mrr_sum / total_casos, 4)

    pct_e2e_estricto = round((e2e_estricto / total_casos) * 100, 2)
    pct_e2e_diferencial = round((e2e_diferencial / total_casos) * 100, 2)
    pct_e2e_incorrecto = round((e2e_incorrecto / total_casos) * 100, 2)

    sensibilidad_interrogador = round((ambiguos_detectados / ambiguos_verdaderos) * 100, 2) if ambiguos_verdaderos > 0 else 100.0
    especificidad_interrogador = round((claros_no_interrumpidos / claros_verdaderos) * 100, 2) if claros_verdaderos > 0 else 100.0

    print("\n" + "=" * 80)
    print("RESULTADOS CONSOLIDADOS FASE 8.2 (BENCHMARK DEV - 60 CASOS):")
    print("1. RAG EVALUATION:")
    print(f"   • Hit@1: {pct_hit1}% ({rag_hit1}/{total_casos})  [Meta >= 80%]")
    print(f"   • Hit@3: {pct_hit3}% ({rag_hit3}/{total_casos})  [Meta >= 90%]")
    print(f"   • Hit@5: {pct_hit5}% ({rag_hit5}/{total_casos})")
    print(f"   • MRR:   {mrr}")
    print("\n2. E2E DIAGNOSTIC EVALUATION:")
    print(f"   • E2E Estricto:     {pct_e2e_estricto}% ({e2e_estricto}/{total_casos})  [Meta >= 80%]")
    print(f"   • E2E Diferencial:  {pct_e2e_diferencial}% ({e2e_diferencial}/{total_casos})")
    print(f"   • E2E Incorrecto:   {pct_e2e_incorrecto}% ({e2e_incorrecto}/{total_casos})")
    print("\n3. MATRIZ DE TRANSICIÓN (ML -> E2E):")
    print(f"   (a) ML Top-1 correcto -> E2E correcto:           {ml_top1_a_e2e_correcto}")
    print(f"   (b) ML Top-1 incorrecto -> E2E rescatado:        {ml_top1_inc_a_e2e_rescate} (Rescates por DTC/RAG/Física)")
    print(f"   (c) ML Top-1 correcto -> E2E degradado:          {ml_top1_corr_a_e2e_degradado} (Objetivo: aprox 0)")
    print(f"   (d) ML Top-3 contenía GT pero E2E lo perdió:     {ml_top3_tenia_gt_e2e_perdio}")
    print("\n4. AUTO-INTERROGADOR:")
    print(f"   • Sensibilidad (casos ambiguos detectados):      {sensibilidad_interrogador}% ({ambiguos_detectados}/{ambiguos_verdaderos})")
    print(f"   • Especificidad (casos claros no interrumpidos): {especificidad_interrogador}% ({claros_no_interrumpidos}/{claros_verdaderos})")
    print("\n5. TELEMETRÍA Y LATENCIAS PROMEDIO (ms):")
    print(f"   • Tiempo ML:    {np.mean(tiempos_ml):.2f} ms")
    print(f"   • Tiempo RAG:   {np.mean(tiempos_rag):.2f} ms")
    print(f"   • Tiempo LLM:   {np.mean(tiempos_llm):.2f} ms")
    print(f"   • Tiempo Total: {np.mean(tiempos_total):.2f} ms")
    print("=" * 80)

    # Hashes de artefactos modificados en 8.2
    hashes_82 = {
        "metadatos_manuales_json": calcular_sha256(RAIZ / "machine_learning/manuals/metadatos_manuales.json"),
        "relevance_filter_py": calcular_sha256(RAIZ / "backend/src/infrastructure/rag/relevance_filter.py"),
        "motor_rag_py": calcular_sha256(RAIZ / "backend/src/infrastructure/motor_rag.py"),
        "politica_fusion_py": calcular_sha256(RAIZ / "backend/src/core/diagnostico/politica_fusion.py"),
        "prompt_builder_py": calcular_sha256(RAIZ / "backend/src/core/diagnostico/prompt_builder.py"),
        "text_processor_py": calcular_sha256(RAIZ / "backend/src/core/diagnostico/text_processor.py"),
        "auto_interrogador_py": calcular_sha256(RAIZ / "backend/src/core/diagnostico/auto_interrogador.py"),
    }

    reporte = {
        "iteracion": "Fase 8.2 - RAG, Fusión de Evidencia y E2E",
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
        "benchmark": "DEV_60_CASOS",
        "metas": {
            "rag_hit1_gte_80": pct_hit1 >= 80.0,
            "rag_hit3_gte_90": pct_hit3 >= 90.0,
            "e2e_estricto_gte_80": pct_e2e_estricto >= 80.0,
        },
        "rag_metricas": {
            "hit1_pct": pct_hit1,
            "hit3_pct": pct_hit3,
            "hit5_pct": pct_hit5,
            "mrr": mrr,
        },
        "e2e_metricas": {
            "estricto_pct": pct_e2e_estricto,
            "diferencial_pct": pct_e2e_diferencial,
            "incorrecto_pct": pct_e2e_incorrecto,
        },
        "matriz_transicion": {
            "ml_top1_corr_a_e2e_corr": ml_top1_a_e2e_correcto,
            "ml_top1_inc_a_e2e_rescate": ml_top1_inc_a_e2e_rescate,
            "ml_top1_corr_a_e2e_degradado": ml_top1_corr_a_e2e_degradado,
            "ml_top3_gt_perdido": ml_top3_tenia_gt_e2e_perdio,
        },
        "auto_interrogador": {
            "sensibilidad_pct": sensibilidad_interrogador,
            "especificidad_pct": especificidad_interrogador,
        },
        "latencias_ms": {
            "ml_media": round(float(np.mean(tiempos_ml)), 2),
            "rag_media": round(float(np.mean(tiempos_rag)), 2),
            "llm_media": round(float(np.mean(tiempos_llm)), 2),
            "total_media": round(float(np.mean(tiempos_total)), 2),
        },
        "hashes_sha256": hashes_82,
        "detalles": detalles_eval,
    }

    out_json = RAIZ / "machine_learning" / "models" / "reporte_fase8_2_candidata.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    print(f"\nReporte completo exportado en: {out_json}")

if __name__ == "__main__":
    evaluar_fase_8_2()
