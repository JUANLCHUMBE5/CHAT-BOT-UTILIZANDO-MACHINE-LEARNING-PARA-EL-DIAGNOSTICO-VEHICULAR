"""
Optimización de Hiperparámetros de Reranking RAG sobre el Benchmark DEV (60 casos).
Registra y evalúa sistemáticamente combinaciones de:
- Factor de coincidencia DTC (2.5x, 3.0x, 3.5x)
- Factor de Macro-Sistema (adaptativo vs estático)
- Ponderación Top 1, Top 2, Top 3 de ML (proporcional a probabilidad vs fija)
- Penalización cruzada adaptativa por nivel de confianza ML.

Metas DEV: Hit@1 >= 80%, Hit@3 >= 90%. Reporta Hit@1, Hit@3, Hit@5 y MRR.
Blindaje: Se evalúa EXCLUSIVAMENTE sobre DEV (60 casos), sin tocar G1_01-G1_50.
"""

import json
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

import faiss
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60

from src.core.gestor_diagnostico import GestorDiagnostico
from src.infrastructure.rag.query_builder import construir_consulta_hibrida


def _normalizar(texto: str) -> str:
    if not texto:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )

def rerank_candidatos_parametrizado(
    candidatos: List[Dict[str, Any]],
    macro_sistema: Optional[str],
    top_fallas: Optional[List[Dict[str, Any]]],
    codigos_dtc: Optional[List[str]],
    confianza_ml: float,
    boost_dtc: float,
    boost_sistema: float,
    modo_penalizacion_sistema: str, # "estatica", "adaptativa_suave", "adaptativa_continua"
    modo_boost_ml: str, # "fijo", "proporcional_probabilidad"
) -> List[Dict[str, Any]]:
    if not candidatos:
        return []

    dtcs_norm = [c.strip().upper() for c in (codigos_dtc or []) if c]
    sistema_objetivo = (macro_sistema or "").strip().upper()

    top_fallas_norm = []
    top_probs = []
    for f_item in (top_fallas or [])[:3]:
        f_nom = f_item.get("falla") if isinstance(f_item, dict) else getattr(f_item, "falla", str(f_item))
        f_pr = float(f_item.get("probabilidad", 0.0) if isinstance(f_item, dict) else getattr(f_item, "probabilidad", 0.0))
        if f_nom:
            top_fallas_norm.append(_normalizar(f_nom))
            top_probs.append(f_pr)

    candidatos_ajustados = []
    for c in candidatos:
        score_base = float(c.get("similitud", 0.0))
        meta = c.get("metadatos", {}) or {}
        tit_norm = _normalizar(c.get("titulo", ""))
        doc_sistema = str(meta.get("sistema", "")).strip().upper()
        doc_falla = _normalizar(str(meta.get("falla", "")))
        doc_dtcs = [str(d).strip().upper() for d in meta.get("codigos_dtc", []) if d]

        factor_ajuste = 1.0

        # 1. Ajuste por DTC
        coincide_dtc = False
        if dtcs_norm:
            coincide_dtc = any(
                dtc in doc_dtcs or _normalizar(dtc) in tit_norm
                for dtc in dtcs_norm
            )
            if coincide_dtc:
                factor_ajuste *= boost_dtc

        # 2. Ajuste por Macro-Sistema
        if sistema_objetivo and sistema_objetivo != "DESCONOCIDO":
            if doc_sistema == sistema_objetivo:
                if modo_penalizacion_sistema == "adaptativa_continua":
                    factor_ajuste *= (1.0 + max(0.25, min(boost_sistema - 1.0, confianza_ml * 0.75)))
                else:
                    factor_ajuste *= boost_sistema
            elif doc_sistema and doc_sistema != sistema_objetivo:
                if coincide_dtc:
                    # Si coincide con un DTC activo, no se penaliza por sistema
                    pass
                elif modo_penalizacion_sistema == "estatica":
                    factor_ajuste *= (0.35 if dtcs_norm else 0.65)
                elif modo_penalizacion_sistema == "adaptativa_suave":
                    # Si confianza ML es baja (< 0.70) o base similarity es alta, penalizar muy poco
                    if confianza_ml < 0.70 or score_base >= 0.55:
                        factor_ajuste *= 0.80
                    else:
                        factor_ajuste *= (0.45 if dtcs_norm else 0.65)
                elif modo_penalizacion_sistema == "adaptativa_continua":
                    # Penalización proporcional a la confianza ML
                    penalidad = max(0.60, 1.0 - (confianza_ml * 0.45))
                    factor_ajuste *= penalidad

        # 3. Ajuste por coincidencia con Top 1, Top 2, Top 3 de ML
        if top_fallas_norm and doc_falla:
            for rank_ml, (f_norm, p_val) in enumerate(zip(top_fallas_norm, top_probs)):
                if doc_falla in f_norm or f_norm in doc_falla:
                    if modo_boost_ml == "fijo":
                        multiplicadores = [2.20, 1.50, 1.25]
                        factor_ajuste *= multiplicadores[rank_ml]
                    elif modo_boost_ml == "proporcional_probabilidad":
                        # Multiplicador ponderado por la certidumbre estadística
                        factor_ajuste *= (1.15 + (p_val * 1.50))
                    break

        score_ajustado = score_base * factor_ajuste
        candidatos_ajustados.append({
            **c,
            "similitud_ajustada": score_ajustado,
            "falla_doc": meta.get("falla", ""),
        })

    candidatos_ajustados.sort(key=lambda x: x["similitud_ajustada"], reverse=True)
    return candidatos_ajustados

def evaluar_configuraciones():
    print("=" * 80)
    print("OPTIMIZACIÓN DE RERANKING RAG SOBRE BENCHMARK DEV (60 CASOS)")
    print("=" * 80)

    gestor = GestorDiagnostico()
    motor_rag = gestor.motor_rag
    total_casos = len(CASOS_DEV_60)

    # Precomputar búsquedas FAISS crudas para rapidez
    datos_eval = []
    for c in CASOS_DEV_60:
        sintoma = c["sintoma"]
        falla_esperada = c["falla_esperada"]
        dtc = c.get("codigo_dtc")
        dtcs = [dtc] if dtc else []

        pred_top = gestor.modelo_ml.predecir_top_fallas(sintoma, limite=3)
        pred_sis = gestor.modelo_ml.predecir_sistema(sintoma)
        conf_top1 = float(pred_top[0]["probabilidad"]) if pred_top else 0.5

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

        datos_eval.append({
            "id": c["id"],
            "esperada": falla_esperada,
            "pred_sis": pred_sis,
            "pred_top": pred_top,
            "dtcs": dtcs,
            "conf_top1": conf_top1,
            "cands_raw": cands,
        })

    # Configuraciones a explorar
    grid = [
        {"nombre": "Base_Anterior", "boost_dtc": 3.0, "boost_sis": 1.60, "modo_pen": "estatica", "modo_ml": "fijo"},
        {"nombre": "Config_1_Suave", "boost_dtc": 3.2, "boost_sis": 1.60, "modo_pen": "adaptativa_suave", "modo_ml": "fijo"},
        {"nombre": "Config_2_Continua", "boost_dtc": 3.5, "boost_sis": 1.65, "modo_pen": "adaptativa_continua", "modo_ml": "proporcional_probabilidad"},
        {"nombre": "Config_3_Hibrida", "boost_dtc": 3.5, "boost_sis": 1.60, "modo_pen": "adaptativa_suave", "modo_ml": "proporcional_probabilidad"},
        {"nombre": "Config_4_AltaDTC", "boost_dtc": 4.0, "boost_sis": 1.55, "modo_pen": "adaptativa_continua", "modo_ml": "proporcional_probabilidad"},
    ]

    resultados_grid = []

    for cfg in grid:
        hit1 = 0
        hit3 = 0
        hit5 = 0
        mrr_sum = 0.0

        for d in datos_eval:
            reord = rerank_candidatos_parametrizado(
                candidatos=d["cands_raw"],
                macro_sistema=d["pred_sis"],
                top_fallas=d["pred_top"],
                codigos_dtc=d["dtcs"],
                confianza_ml=d["conf_top1"],
                boost_dtc=cfg["boost_dtc"],
                boost_sistema=cfg["boost_sis"],
                modo_penalizacion_sistema=cfg["modo_pen"],
                modo_boost_ml=cfg["modo_ml"],
            )

            fallas_ordenadas = [c["falla_doc"] for c in reord]
            esperada = d["esperada"]

            # Rango del primer acierto
            rank = 0
            for r_idx, f_nom in enumerate(fallas_ordenadas[:20], 1):
                if f_nom == esperada:
                    rank = r_idx
                    break

            if rank == 1:
                hit1 += 1
            if 1 <= rank <= 3:
                hit3 += 1
            if 1 <= rank <= 5:
                hit5 += 1

            if rank > 0:
                mrr_sum += (1.0 / rank)

        pct_hit1 = round((hit1 / total_casos) * 100, 2)
        pct_hit3 = round((hit3 / total_casos) * 100, 2)
        pct_hit5 = round((hit5 / total_casos) * 100, 2)
        mrr = round(mrr_sum / total_casos, 4)

        res_entry = {
            "configuracion": cfg,
            "hit1_pct": pct_hit1,
            "hit3_pct": pct_hit3,
            "hit5_pct": pct_hit5,
            "mrr": mrr,
            "cumple_metas": (pct_hit1 >= 80.0 and pct_hit3 >= 90.0)
        }
        resultados_grid.append(res_entry)

        print(f"[{cfg['nombre']}] -> Hit@1: {pct_hit1}% ({hit1}/{total_casos}) | Hit@3: {pct_hit3}% ({hit3}/{total_casos}) | Hit@5: {pct_hit5}% | MRR: {mrr}")

    # Guardar bitácora de experimentos de reranking
    out_file = BASE_DIR / "machine_learning" / "models" / "experimentos_reranking_rag_dev.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(resultados_grid, f, indent=2, ensure_ascii=False)
    print(f"\nBitácora de optimización RAG guardada en: {out_file}")

if __name__ == "__main__":
    evaluar_configuraciones()
