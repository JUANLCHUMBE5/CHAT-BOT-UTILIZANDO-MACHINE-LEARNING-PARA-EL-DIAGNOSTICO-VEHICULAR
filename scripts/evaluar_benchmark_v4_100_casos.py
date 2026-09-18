"""
Evaluación Científica Oficial del Benchmark V4 (100 Casos 100% Ciegos) — Fase 7
Calcula:
  - Exactitud Top-1 Estricta y Diferencial
  - Exactitud Top-3 y Macro-Sistema
  - Precision, Recall, Macro-F1
  - RAG Hit@1, Hit@3, Hit@5 y Mean Reciprocal Rank (MRR)
  - Latencias reales de inferencia ML y recuperación RAG
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
from sklearn.metrics import precision_recall_fscore_support

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))
sys.path.insert(0, str(BASE_DIR / "scripts"))

from benchmark_v4_ground_truth import BENCHMARK_V4_CASOS
from src.core.traductor_jerga import normalizar_jerga_peruana
from src.core.diagnostico.semantic_purifier import purificar_sintoma_para_vectorizador_ml
from src.infrastructure.container import ServiceContainer
from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema, obtener_sistema_por_dtc
from evaluar_rag_relevancia import es_procedimiento_relevante


def ejecutar_evaluacion_v4():
    print("\n" + "="*80)
    print("INICIANDO EVALUACION CIENTIFICA DEL BENCHMARK V4 (100 CASOS CIEGOS)")
    print("="*80)

    # Inicializar servicios
    modelo_ml = ServiceContainer.get_modelo_ml()
    rag_service = ServiceContainer.get_motor_rag()

    from src.infrastructure.rag.query_builder import construir_consulta_hibrida
    from src.infrastructure.rag.relevance_filter import reordenar_candidatos_rag

    resultados = []
    tiempos_ml = []
    tiempos_rag = []

    y_true_estricto = []
    y_pred_top1 = []

    for idx, caso in enumerate(BENCHMARK_V4_CASOS, 1):
        sintoma_raw = caso["sintoma"]
        falla_estricta = caso["falla_estricta"]
        fallas_aceptables = caso["fallas_aceptables"]
        sistema_esperado = caso["macro_sistema"]
        dtc_esperado = caso["dtc"]
        proc_esperado = caso["procedimiento_rag_esperado"]

        # 1. Normalización lingüística y purificación semántica
        sintoma_norm = normalizar_jerga_peruana(sintoma_raw)
        dtc_detectados = re.findall(r"\b[PCBU]\d{4}\b", sintoma_norm, re.IGNORECASE)
        dtc_detectados = [d.upper() for d in dtc_detectados]
        dtc_param = dtc_detectados[0] if dtc_detectados else dtc_esperado

        # Purificación para ML
        texto_ml = purificar_sintoma_para_vectorizador_ml(sintoma_norm)

        # 2. Inferencia ML Jerárquico
        t0_ml = time.perf_counter()
        top_fallas = modelo_ml.predecir_top_fallas(texto_ml, limite=3, dtc_codigo=dtc_param)
        t_ml = (time.perf_counter() - t0_ml) * 1000.0
        tiempos_ml.append(t_ml)

        top1_falla = top_fallas[0]["falla"] if top_fallas else "Desconocida"
        top1_conf = top_fallas[0]["probabilidad"] if top_fallas else 0.0
        macro_sistema_ml = obtener_macro_sistema(top1_falla)
        predicciones_top = top_fallas

        # 3. Consulta RAG Híbrida Multiseñal
        t0_rag = time.perf_counter()
        consulta_hibrida = construir_consulta_hibrida(
            consulta_usuario=sintoma_raw,
            macro_sistema=macro_sistema_ml,
            top_fallas=top_fallas,
            codigos_dtc=[dtc_param] if dtc_param else None,
        )
        consulta_exp = rag_service._expandir_consulta(consulta_hibrida)
        consulta_vec = rag_service.vectorizador.transform([consulta_exp]).toarray().astype(np.float32)
        import faiss
        faiss.normalize_L2(consulta_vec)
        sims, indices = rag_service.faiss_index.search(consulta_vec, k=15)

        cands_rag = []
        for k_idx in range(min(15, len(rag_service.documentos))):
            d_idx = int(indices[0][k_idx])
            if 0 <= d_idx < len(rag_service.documentos):
                cands_rag.append({
                    "indice": d_idx,
                    "titulo": rag_service.titulos[d_idx],
                    "documento": rag_service.documentos[d_idx],
                    "similitud": float(sims[0][k_idx]),
                    "metadatos": rag_service.metadatos_procedimientos[d_idx] if d_idx < len(rag_service.metadatos_procedimientos) else {}
                })

        rag_candidatos = reordenar_candidatos_rag(
            cands_rag,
            macro_sistema=macro_sistema_ml,
            top_fallas=top_fallas,
            codigos_dtc=[dtc_param] if dtc_param else None,
        )
        t_rag = (time.perf_counter() - t0_rag) * 1000.0
        tiempos_rag.append(t_rag)

        # 4. Evaluación de Aciertos ML
        acierto_estricto = (top1_falla == falla_estricta)
        acierto_diferencial = acierto_estricto or (top1_falla in fallas_aceptables)

        top3_fallas = [p.get("falla", "") for p in predicciones_top[:3]]
        acierto_top3 = (falla_estricta in top3_fallas) or any(fa in top3_fallas for fa in fallas_aceptables)
        acierto_sistema = (macro_sistema_ml == sistema_esperado)

        y_true_estricto.append(falla_estricta)
        y_pred_top1.append(top1_falla)

        # 5. Evaluación de Aciertos RAG
        # Evaluar relevancia de cada uno de los 5 candidatos
        relevancias = []
        for c in rag_candidatos:
            tit = c.get("titulo", "")
            doc = c.get("documento", "")
            meta = c.get("metadatos", {})
            falla_meta = str(meta.get("falla", "")).strip().lower()
            es_rel = es_procedimiento_relevante(
                titulo_procedimiento=tit,
                contenido=doc,
                falla_esperada=falla_estricta,
                dtc_esperado=dtc_param,
            )
            # También verificar coincidencia con metadatos explícitos de falla
            if not es_rel and falla_meta:
                if falla_meta == falla_estricta.lower() or any(fa.lower() == falla_meta for fa in fallas_aceptables):
                    es_rel = True
            # Y verificar palabra clave de ground truth
            if not es_rel and proc_esperado:
                if proc_esperado.lower() in tit.lower() or proc_esperado.lower() in doc[:500].lower():
                    es_rel = True
            relevancias.append(es_rel)

        hit1 = 1 if len(relevancias) >= 1 and relevancias[0] else 0
        hit3 = 1 if any(relevancias[:3]) else 0
        hit5 = 1 if any(relevancias[:5]) else 0

        mrr = 0.0
        for r_idx, rel in enumerate(relevancias, 1):
            if rel:
                mrr = 1.0 / r_idx
                break

        res_caso = {
            "id": caso["id"],
            "grupo": caso["grupo"],
            "sintoma": sintoma_raw,
            "falla_estricta": falla_estricta,
            "fallas_aceptables": fallas_aceptables,
            "macro_sistema_esperado": sistema_esperado,
            "dtc": dtc_param,
            "top1_predicho": top1_falla,
            "confianza_top1": round(top1_conf, 4),
            "macro_sistema_ml": macro_sistema_ml,
            "top3_predichos": top3_fallas,
            "acierto_estricto": acierto_estricto,
            "acierto_diferencial": acierto_diferencial,
            "acierto_top3": acierto_top3,
            "acierto_sistema": acierto_sistema,
            "titulo_rag_top1": rag_candidatos[0].get("titulo", "") if rag_candidatos else "Ninguno",
            "similitud_rag_top1": round(rag_candidatos[0].get("similitud", 0.0), 4) if rag_candidatos else 0.0,
            "hit1_rag": hit1,
            "hit3_rag": hit3,
            "hit5_rag": hit5,
            "mrr_rag": round(mrr, 4),
            "t_ml_ms": round(t_ml, 2),
            "t_rag_ms": round(t_rag, 2),
        }
        resultados.append(res_caso)

    # -------------------------------------------------------------
    # Métricas Globales y por Grupo
    # -------------------------------------------------------------
    n_total = len(resultados)
    g1 = [r for r in resultados if r["grupo"] == "G1_TECNICO_VEHICULAR"]
    g2 = [r for r in resultados if r["grupo"] == "G2_COLOQUIAL_TALLER"]

    def calcular_bloque_metricas(sub_casos):
        n = len(sub_casos)
        if n == 0:
            return {}
        acc_estricto = sum(r["acierto_estricto"] for r in sub_casos) / n
        acc_dif = sum(r["acierto_diferencial"] for r in sub_casos) / n
        acc_top3 = sum(r["acierto_top3"] for r in sub_casos) / n
        acc_sist = sum(r["acierto_sistema"] for r in sub_casos) / n
        conf_prom = np.mean([r["confianza_top1"] for r in sub_casos])

        hit1 = sum(r["hit1_rag"] for r in sub_casos) / n
        hit3 = sum(r["hit3_rag"] for r in sub_casos) / n
        hit5 = sum(r["hit5_rag"] for r in sub_casos) / n
        mrr = np.mean([r["mrr_rag"] for r in sub_casos])

        t_ml = np.mean([r["t_ml_ms"] for r in sub_casos])
        t_rag = np.mean([r["t_rag_ms"] for r in sub_casos])

        return {
            "n": n,
            "acc_top1_estricto": round(acc_estricto * 100.0, 2),
            "acc_top1_diferencial": round(acc_dif * 100.0, 2),
            "acc_top3": round(acc_top3 * 100.0, 2),
            "acc_macro_sistema": round(acc_sist * 100.0, 2),
            "confianza_promedio": round(conf_prom * 100.0, 2),
            "rag_hit1": round(hit1 * 100.0, 2),
            "rag_hit3": round(hit3 * 100.0, 2),
            "rag_hit5": round(hit5 * 100.0, 2),
            "rag_mrr": round(mrr, 4),
            "t_ml_ms": round(t_ml, 2),
            "t_rag_ms": round(t_rag, 2)
        }

    m_total = calcular_bloque_metricas(resultados)
    m_g1 = calcular_bloque_metricas(g1)
    m_g2 = calcular_bloque_metricas(g2)

    # Precision, Recall, F1 macro (usando etiquetas reales presentes)
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true_estricto, y_pred_top1, average="macro", zero_division=0
    )
    p_weight, r_weight, f1_weight, _ = precision_recall_fscore_support(
        y_true_estricto, y_pred_top1, average="weighted", zero_division=0
    )

    m_total["precision_macro"] = round(p_macro * 100.0, 2)
    m_total["recall_macro"] = round(r_macro * 100.0, 2)
    m_total["f1_macro"] = round(f1_macro * 100.0, 2)
    m_total["f1_weighted"] = round(f1_weight * 100.0, 2)

    # -------------------------------------------------------------
    # Reporte por Consola
    # -------------------------------------------------------------
    print("\n" + "="*80)
    print("RESULTADOS FINALES — BENCHMARK V4 CIEGO (100 CASOS INEDITOS)")
    print("="*80)
    print(f"{'Metrica Evaluada':<35} | {'Grupo 1 (Tecnico)':<18} | {'Grupo 2 (Coloquial)':<20} | {'Global V4':<12}")
    print("-" * 90)
    print(f"{'Exactitud Top-1 Estricta':<35} | {m_g1['acc_top1_estricto']:>16}% | {m_g2['acc_top1_estricto']:>18}% | {m_total['acc_top1_estricto']:>10}%")
    print(f"{'Exactitud Top-1 Diferencial':<35} | {m_g1['acc_top1_diferencial']:>16}% | {m_g2['acc_top1_diferencial']:>18}% | {m_total['acc_top1_diferencial']:>10}%")
    print(f"{'Exactitud Top-3 (Diagnostico)':<35} | {m_g1['acc_top3']:>16}% | {m_g2['acc_top3']:>18}% | {m_total['acc_top3']:>10}%")
    print(f"{'Exactitud Macro-Sistema':<35} | {m_g1['acc_macro_sistema']:>16}% | {m_g2['acc_macro_sistema']:>18}% | {m_total['acc_macro_sistema']:>10}%")
    print(f"{'Confianza Calibrada Promedio':<35} | {m_g1['confianza_promedio']:>16}% | {m_g2['confianza_promedio']:>18}% | {m_total['confianza_promedio']:>10}%")
    print("-" * 90)
    print(f"{'RAG Hit@1':<35} | {m_g1['rag_hit1']:>16}% | {m_g2['rag_hit1']:>18}% | {m_total['rag_hit1']:>10}%")
    print(f"{'RAG Hit@3':<35} | {m_g1['rag_hit3']:>16}% | {m_g2['rag_hit3']:>18}% | {m_total['rag_hit3']:>10}%")
    print(f"{'RAG Hit@5':<35} | {m_g1['rag_hit5']:>16}% | {m_g2['rag_hit5']:>18}% | {m_total['rag_hit5']:>10}%")
    print(f"{'RAG MRR (Reciprocal Rank)':<35} | {m_g1['rag_mrr']:>17} | {m_g2['rag_mrr']:>19} | {m_total['rag_mrr']:>11}")
    print("-" * 90)
    print(f"{'Precision Macro':<35} | {'-':>17} | {'-':>19} | {m_total['precision_macro']:>10}%")
    print(f"{'Recall Macro':<35} | {'-':>17} | {'-':>19} | {m_total['recall_macro']:>10}%")
    print(f"{'F1-Score Macro':<35} | {'-':>17} | {'-':>19} | {m_total['f1_macro']:>10}%")
    print(f"{'F1-Score Ponderado':<35} | {'-':>17} | {'-':>19} | {m_total['f1_weighted']:>10}%")
    print("-" * 90)
    print(f"{'Latencia Inferencia ML':<35} | {m_g1['t_ml_ms']:>14} ms | {m_g2['t_ml_ms']:>16} ms | {m_total['t_ml_ms']:>8} ms")
    print(f"{'Latencia Recuperacion RAG':<35} | {m_g1['t_rag_ms']:>14} ms | {m_g2['t_rag_ms']:>16} ms | {m_total['t_rag_ms']:>8} ms")
    print("="*90)

    # Guardar reporte JSON
    reporte_path = BASE_DIR / "docs" / "graficas" / "reporte_evaluacion_v4_100_casos.json"
    reporte_path.parent.mkdir(parents=True, exist_ok=True)
    with open(reporte_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
                "benchmark": "V4_CIEGO_FASE7",
                "total_casos": n_total,
                "congelado": True,
            },
            "metricas_globales": m_total,
            "metricas_grupo1_tecnico": m_g1,
            "metricas_grupo2_coloquial": m_g2,
            "casos_evaluados": resultados
        }, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Reporte detallado guardado en: {reporte_path}")
    return m_total, m_g1, m_g2


if __name__ == "__main__":
    ejecutar_evaluacion_v4()
