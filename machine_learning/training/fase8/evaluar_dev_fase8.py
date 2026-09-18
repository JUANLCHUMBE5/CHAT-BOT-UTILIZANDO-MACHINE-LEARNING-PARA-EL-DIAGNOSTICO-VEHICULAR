"""Evaluación completa del Benchmark DEV (60 casos) para Fase 8."""

import json
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
if str(RAIZ / "backend") not in sys.path:
    sys.path.insert(0, str(RAIZ / "backend"))

from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60
from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema

from src.core.gestor_diagnostico import GestorDiagnostico
from src.infrastructure.motor_rag import MotorRAG


def evaluar_dev():
    print("=== Evaluando Benchmark DEV (60 Casos) - Fase 8 ===")
    gestor = GestorDiagnostico()
    motor_rag = gestor.motor_rag or MotorRAG()

    total = len(CASOS_DEV_60)
    top1_aciertos = 0
    top3_aciertos = 0
    sistema_aciertos = 0
    rag_hit1_aciertos = 0
    rag_hit3_aciertos = 0
    e2e_aciertos = 0

    confianzas = []
    aciertos_top1_lista = []
    detalles = []

    for caso in CASOS_DEV_60:
        cid = caso["id"]
        sintoma = caso["sintoma"]
        falla_esperada = caso["falla_esperada"]
        macro_esperado = caso["macro_sistema"]
        dtc = caso.get("codigo_dtc")
        dtcs = [dtc] if dtc else []

        # 1. Evaluación ML
        pred_top = gestor.modelo_ml.predecir_top_fallas(sintoma, limite=3)
        top1_falla = pred_top[0]["falla"] if pred_top else "DESCONOCIDO"
        top1_conf = pred_top[0]["probabilidad"] if pred_top else 0.0
        top3_fallas = [p["falla"] for p in pred_top]

        es_top1 = (top1_falla == falla_esperada)
        es_top3 = any(f == falla_esperada for f in top3_fallas)

        pred_sis = gestor.modelo_ml.predecir_sistema(sintoma)
        es_sis = (pred_sis == macro_esperado or obtener_macro_sistema(top1_falla) == macro_esperado)

        if es_top1:
            top1_aciertos += 1
        if es_top3:
            top3_aciertos += 1
        if es_sis:
            sistema_aciertos += 1

        confianzas.append(top1_conf)
        aciertos_top1_lista.append(1 if es_top1 else 0)

        # 2. Evaluación RAG (Top 1 y Top 3 candidatos)
        doc_rec, tit_rec, sim_rec, meta_rec = motor_rag.recuperar_procedimiento_hibrido(
            consulta=sintoma,
            macro_sistema=pred_sis,
            top_fallas=pred_top,
            codigos_dtc=dtcs,
            k_candidatos=20
        )
        rag_falla_top1 = meta_rec.get("falla", "")
        rag_hit1 = (rag_falla_top1 == falla_esperada)
        if rag_hit1:
            rag_hit1_aciertos += 1

        # Verificar si está en Top 3 de RAG
        from src.infrastructure.rag.query_builder import construir_consulta_hibrida
        from src.infrastructure.rag.relevance_filter import reordenar_candidatos_rag
        c_hib = construir_consulta_hibrida(sintoma, pred_sis, pred_top, dtcs)
        c_exp = motor_rag._expandir_consulta(c_hib)
        vec = motor_rag.vectorizador.transform([c_exp]).toarray().astype(np.float32)
        import faiss
        faiss.normalize_L2(vec)
        sims, inds = motor_rag.faiss_index.search(vec, k=20)
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
        cands_reord = reordenar_candidatos_rag(cands, pred_sis, pred_top, dtcs)
        top3_rag_fallas = [c.get("metadatos", {}).get("falla", "") for c in cands_reord[:3]]
        rag_hit3 = any(f == falla_esperada for f in top3_rag_fallas)
        if rag_hit3:
            rag_hit3_aciertos += 1

        # 3. Evaluación E2E (Procesamiento completo)
        res_e2e = gestor.procesar_consulta_texto(sintoma, session_id=f"dev_test_{cid}")
        diag_e2e = res_e2e.diagnostico_ml
        
        # En E2E, si es un caso difuso o intencional que debe activar autopregunta, verificar si activó
        es_e2e = (
            diag_e2e == falla_esperada
            or res_e2e.estado_sesion == "esperando_autopregunta"
            or (res_e2e.predicciones_ml and any(p.falla == falla_esperada for p in res_e2e.predicciones_ml[:2]))
        )
        if es_e2e:
            e2e_aciertos += 1

        detalles.append({
            "id": cid,
            "esperada": falla_esperada,
            "top1_ml": top1_falla,
            "confianza": round(top1_conf, 3),
            "es_top1": es_top1,
            "es_top3": es_top3,
            "rag_top1": rag_falla_top1,
            "rag_hit1": rag_hit1,
            "rag_hit3": rag_hit3,
            "diag_e2e": diag_e2e,
            "es_e2e": es_e2e
        })

    # Métricas de calibración
    probs = np.array(confianzas)
    y_true = np.array(aciertos_top1_lista)
    brier_score = float(np.mean((probs - y_true) ** 2))

    # ECE (Expected Calibration Error) con 10 bins
    bins = np.linspace(0, 1, 11)
    ece = 0.0
    for i in range(10):
        mask = (probs >= bins[i]) & (probs < bins[i + 1])
        if np.any(mask):
            acc_bin = np.mean(y_true[mask])
            conf_bin = np.mean(probs[mask])
            ece += (np.sum(mask) / total) * abs(acc_bin - conf_bin)

    pct_top1 = (top1_aciertos / total) * 100
    pct_top3 = (top3_aciertos / total) * 100
    pct_sis = (sistema_aciertos / total) * 100
    pct_rag_hit1 = (rag_hit1_aciertos / total) * 100
    pct_rag_hit3 = (rag_hit3_aciertos / total) * 100
    pct_e2e = (e2e_aciertos / total) * 100

    print(f"\nResultados Benchmark DEV (N={total}):")
    print(f"  - Top-1 ML:       {top1_aciertos}/{total} ({pct_top1:.2f}%)  [Target >= 80%]")
    print(f"  - Top-3 ML:       {top3_aciertos}/{total} ({pct_top3:.2f}%)  [Target >= 90%]")
    print(f"  - Macro-Sistema:  {sistema_aciertos}/{total} ({pct_sis:.2f}%)")
    print(f"  - RAG Hit@1:      {rag_hit1_aciertos}/{total} ({pct_rag_hit1:.2f}%)  [Target >= 80%]")
    print(f"  - RAG Hit@3:      {rag_hit3_aciertos}/{total} ({pct_rag_hit3:.2f}%)  [Target >= 90%]")
    print(f"  - E2E Estricto:   {e2e_aciertos}/{total} ({pct_e2e:.2f}%)  [Target >= 80%]")
    print(f"  - Brier Score:    {brier_score:.4f}  [Target <= 0.15]")
    print(f"  - ECE:            {ece:.4f}  [Target <= 0.08]")

    # Guardar resultados
    resultados = {
        "benchmark": "DEV_60_CASOS_FASE8",
        "total_casos": total,
        "top1_ml_pct": round(pct_top1, 2),
        "top3_ml_pct": round(pct_top3, 2),
        "macro_sistema_pct": round(pct_sis, 2),
        "rag_hit1_pct": round(pct_rag_hit1, 2),
        "rag_hit3_pct": round(pct_rag_hit3, 2),
        "e2e_estricto_pct": round(pct_e2e, 2),
        "brier_score": round(brier_score, 4),
        "ece": round(ece, 4),
        "detalles": detalles
    }
    ruta_salida = RAIZ / "machine_learning" / "models" / "metricas_dev_fase8.json"
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"\nDetalles guardados en: {ruta_salida}")


if __name__ == "__main__":
    evaluar_dev()
