"""
Evaluación de Regresión y Estrés Externo sobre G1_01 - G1_50 (Fase 8.3 Congelada).
ADVERTENCIA METODOLÓGICA: Este conjunto NO es un test ciego porque su Ground Truth
fue analizado previamente. Se utiliza estrictamente como benchmark de regresión.
"""

import json
import sys
import time
import unicodedata
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
SCRIPTS_DIR = BASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ground_truth_50_casos_data import GROUND_TRUTH_50
from datos_prueba_grupo1 import GRUPO_1_CASOS
from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema
from src.core.gestor_diagnostico import GestorDiagnostico
from machine_learning.training.fase8.experimentar_calibracion_dev import calcular_metricas_calibracion

def norm(texto: str) -> str:
    if not texto:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(texto).lower())
        if unicodedata.category(c) != "Mn"
    ).strip()

def coincide_falla(candidato: str, esperada: str, claves_estrictas: list[str]) -> bool:
    c_norm = norm(candidato)
    e_norm = norm(esperada)
    if c_norm == e_norm:
        return True
    if e_norm in c_norm or c_norm in e_norm:
        return True
    for k in claves_estrictas:
        k_norm = norm(k)
        if k_norm in c_norm:
            return True
    return False

def coincide_rag(doc_titulo: str, esperada: str, claves: list[str]) -> bool:
    t_norm = norm(doc_titulo)
    e_norm = norm(esperada)
    if e_norm in t_norm or t_norm in e_norm:
        return True
    for k in claves:
        if norm(k) in t_norm:
            return True
    return False

def main():
    print("=" * 90)
    print("INICIANDO EVALUACIÓN DE REGRESIÓN/ESTRÉS: G1_01 - G1_50 (Fase 8.3 Congelada)")
    print("=" * 90)

    gestor = GestorDiagnostico()

    mapa_gt = {item["id"]: item for item in GROUND_TRUTH_50}
    mapa_casos = {item["id"]: item["texto"] for item in GRUPO_1_CASOS}

    total = len(GROUND_TRUTH_50)
    top1_ml_hits = 0
    top3_ml_hits = 0
    macro_hits = 0

    rag_hit1 = 0
    rag_hit3 = 0
    rag_hit5 = 0
    rag_mrr_sum = 0.0

    e2e_estricto = 0
    e2e_diferencial = 0
    e2e_incorrecto = 0

    ml_top1_a_e2e_correcto = 0
    ml_top1_inc_a_e2e_rescate = 0
    ml_top1_corr_a_e2e_degradado = 0
    ml_top3_tenia_gt_e2e_perdio = 0

    confianzas_top1 = []
    aciertos_top1_bool = []

    tiempos_ml = []
    tiempos_rag = []
    tiempos_total = []

    detalles = []

    for caso_gt in GROUND_TRUTH_50:
        cid = caso_gt["id"]
        sintoma = mapa_casos.get(cid, "")
        esperada = caso_gt["falla_esperada"]
        macro_esp = caso_gt["macro_sistema"]
        claves = caso_gt.get("claves_estrictas", [])
        claves_dif = caso_gt.get("claves_diferenciales", [])
        req_auto = caso_gt.get("requiere_auto_interrogador", False)

        # 1. Capa ML Pura
        t0_ml = time.perf_counter()
        pred_top = gestor.modelo_ml.predecir_top_fallas(sintoma, limite=3)
        dt_ml = (time.perf_counter() - t0_ml) * 1000
        tiempos_ml.append(dt_ml)

        t1_f = pred_top[0]["falla"] if len(pred_top) > 0 else "DESCONOCIDO"
        t1_c = float(pred_top[0]["probabilidad"]) if len(pred_top) > 0 else 0.0
        t2_f = pred_top[1]["falla"] if len(pred_top) > 1 else "-"
        t3_f = pred_top[2]["falla"] if len(pred_top) > 2 else "-"

        top1_ok = coincide_falla(t1_f, esperada, claves)
        if top1_ok:
            top1_ml_hits += 1

        top3_ok = (
            coincide_falla(t1_f, esperada, claves)
            or (t2_f != "-" and coincide_falla(t2_f, esperada, claves))
            or (t3_f != "-" and coincide_falla(t3_f, esperada, claves))
        )
        if top3_ok:
            top3_ml_hits += 1

        macro_pred = gestor.modelo_ml.predecir_sistema(sintoma)
        if macro_pred == "DESCONOCIDO":
            macro_pred = obtener_macro_sistema(t1_f)
        if macro_pred == macro_esp or obtener_macro_sistema(t1_f) == macro_esp:
            macro_hits += 1

        confianzas_top1.append(t1_c)
        aciertos_top1_bool.append(1 if top1_ok else 0)

        # 2. Capa RAG
        t0_rag = time.perf_counter()
        from src.infrastructure.rag.query_builder import construir_consulta_hibrida
        from src.infrastructure.rag.relevance_filter import reordenar_candidatos_rag
        import faiss

        import re
        dtcs_encontrados = [m.upper() for m in re.findall(r"\b[PBCU]\d{4}\b", sintoma, re.IGNORECASE)]

        c_hib = construir_consulta_hibrida(
            consulta_usuario=sintoma,
            macro_sistema=macro_pred,
            top_fallas=pred_top,
            codigos_dtc=dtcs_encontrados,
        )
        c_exp = gestor.motor_rag._expandir_consulta(c_hib)
        vec_rag = gestor.motor_rag.vectorizador.transform([c_exp]).toarray().astype(np.float32)
        faiss.normalize_L2(vec_rag)
        sims, inds = gestor.motor_rag.faiss_index.search(vec_rag, k=30)

        cands = []
        for kidx in range(len(inds[0])):
            didx = int(inds[0][kidx])
            if 0 <= didx < len(gestor.motor_rag.documentos):
                cands.append({
                    "indice": didx,
                    "titulo": gestor.motor_rag.titulos[didx],
                    "documento": gestor.motor_rag.documentos[didx],
                    "similitud": float(sims[0][kidx]),
                    "metadatos": (
                        gestor.motor_rag.metadatos_procedimientos[didx]
                        if didx < len(gestor.motor_rag.metadatos_procedimientos)
                        else {}
                    ),
                })

        cands_reord = reordenar_candidatos_rag(
            cands,
            macro_sistema=macro_pred,
            top_fallas=pred_top,
            codigos_dtc=dtcs_encontrados,
            confianza_ml=t1_c,
        )
        dt_rag = (time.perf_counter() - t0_rag) * 1000
        tiempos_rag.append(dt_rag)

        rag_rank = 0
        for r_idx, c_item in enumerate(cands_reord[:10], 1):
            f_nom = c_item.get("metadatos", {}).get("falla", "")
            t_nom = c_item.get("titulo", "")
            if coincide_falla(f_nom, esperada, claves) or coincide_rag(t_nom, esperada, claves):
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

        # 3. Capa E2E Completa
        t0_e2e = time.perf_counter()
        session_id = f"g1_eval_83_{cid}_{int(time.time()*1000)%100000}"
        res_e2e = gestor.procesar_consulta_texto(sintoma, session_id=session_id)
        dt_e2e = (time.perf_counter() - t0_e2e) * 1000
        tiempos_total.append(dt_e2e)

        diag_final = res_e2e.diagnostico_ml
        estado_sesion = res_e2e.estado_sesion
        preds_e2e = [p.falla for p in (res_e2e.predicciones_ml or [])]

        activado_interrogador = (estado_sesion == "esperando_autopregunta" or res_e2e.requiere_revision_humana)

        # Evaluación Tricotómica E2E
        # Caso especial G1_49 y G1_50 (deliberadamente ambiguos en el benchmark)
        if cid in ("G1_49", "G1_50"):
            if activado_interrogador:
                cat_e2e = "ESTRICTO"
                e2e_estricto += 1
                diag_final = f"[Auto-Interrogador Activado] {diag_final}"
            else:
                cat_e2e = "INCORRECTO"
                e2e_incorrecto += 1
        else:
            if coincide_falla(diag_final, esperada, claves):
                cat_e2e = "ESTRICTO"
                e2e_estricto += 1
            elif req_auto and activado_interrogador:
                cat_e2e = "ESTRICTO"
                e2e_estricto += 1
                diag_final = f"[Auto-Interrogador Activado] {diag_final}"
            elif any(coincide_falla(f, esperada, claves) or any(norm(kd) in norm(f) for kd in claves_dif) for f in preds_e2e[:3]):
                cat_e2e = "DIFERENCIAL"
                e2e_diferencial += 1
            else:
                cat_e2e = "INCORRECTO"
                e2e_incorrecto += 1

        # Transiciones ML -> E2E
        if top1_ok:
            if cat_e2e == "ESTRICTO":
                ml_top1_a_e2e_correcto += 1
            else:
                ml_top1_corr_a_e2e_degradado += 1
        else:
            if cat_e2e == "ESTRICTO":
                ml_top1_inc_a_e2e_rescate += 1

        if top3_ok and cat_e2e == "INCORRECTO":
            ml_top3_tenia_gt_e2e_perdio += 1

        detalles.append({
            "id": cid,
            "sintoma": sintoma[:50] + "...",
            "esperada": esperada,
            "top1_ml": t1_f,
            "top1_conf": round(t1_c, 3),
            "top1_ok": top1_ok,
            "top3_ok": top3_ok,
            "rag_rank": rag_rank,
            "diag_e2e": diag_final,
            "cat_e2e": cat_e2e,
            "activado_interrogador": activado_interrogador,
        })

    # Calibración
    calib = calcular_metricas_calibracion(np.array(confianzas_top1), np.array(aciertos_top1_bool))

    pct_top1 = round((top1_ml_hits / total) * 100, 2)
    pct_top3 = round((top3_ml_hits / total) * 100, 2)
    pct_macro = round((macro_hits / total) * 100, 2)

    pct_rag_hit1 = round((rag_hit1 / total) * 100, 2)
    pct_rag_hit3 = round((rag_hit3 / total) * 100, 2)
    pct_rag_hit5 = round((rag_hit5 / total) * 100, 2)
    rag_mrr = round(rag_mrr_sum / total, 4)

    pct_e2e_estricto = round((e2e_estricto / total) * 100, 2)
    pct_e2e_diferencial = round((e2e_diferencial / total) * 100, 2)
    pct_e2e_incorrecto = round((e2e_incorrecto / total) * 100, 2)

    print("\n" + "=" * 90)
    print("RESULTADOS OFICIALES G1_01 - G1_50 (FASE 8.3 REGRESIÓN/ESTRÉS)")
    print("=" * 90)
    print(f"Top-1 ML:             {pct_top1}% ({top1_ml_hits}/{total})")
    print(f"Top-3 ML:             {pct_top3}% ({top3_ml_hits}/{total})")
    print(f"Macro-Sistema ML:     {pct_macro}% ({macro_hits}/{total})")
    print(f"RAG Hit@1:            {pct_rag_hit1}% ({rag_hit1}/{total})")
    print(f"RAG Hit@3:            {pct_rag_hit3}% ({rag_hit3}/{total})")
    print(f"RAG Hit@5:            {pct_rag_hit5}% ({rag_hit5}/{total})")
    print(f"RAG MRR:              {rag_mrr:.4f}")
    print(f"E2E Estricto:         {pct_e2e_estricto}% ({e2e_estricto}/{total})")
    print(f"E2E Diferencial:      {pct_e2e_diferencial}% ({e2e_diferencial}/{total})")
    print(f"E2E Incorrecto:       {pct_e2e_incorrecto}% ({e2e_incorrecto}/{total})")
    print("-" * 90)
    print("CALIBRACIÓN EN G1:")
    print(f"Brier Score:          {calib['brier']:.4f}")
    print(f"ECE:                  {calib['ece']:.4f}")
    print(f"Acc >= 80%:           {calib['acc_gte_80']*100:.2f}%")
    print(f"Cov >= 80%:           {calib['cov_gte_80']*100:.1f}%")
    print(f"Conf Aciertos:        {calib['conf_aciertos']:.4f} | Conf Errores: {calib['conf_errores']:.4f}")
    print("-" * 90)
    print("MATRIZ DE TRANSICIÓN ML -> E2E:")
    print(f"(a) ML Top-1 correcto -> E2E correcto:   {ml_top1_a_e2e_correcto}")
    print(f"(b) ML Top-1 incorrecto -> E2E rescate:  {ml_top1_inc_a_e2e_rescate}")
    print(f"(c) ML Top-1 correcto -> E2E degradado: {ml_top1_corr_a_e2e_degradado}")
    print(f"(d) ML Top-3 contenía GT pero se perdió: {ml_top3_tenia_gt_e2e_perdio}")
    print("-" * 90)
    print(f"Latencia Media ML:    {np.mean(tiempos_ml):.2f} ms")
    print(f"Latencia Media RAG:   {np.mean(tiempos_rag):.2f} ms")
    print(f"Latencia Media Total: {np.mean(tiempos_total):.2f} ms")
    print("=" * 90)

    # Comparación con Fase 7 (Baseline)
    # Fase 7 histórico oficial: Top-1 ML 66.0%, Top-3 ML 84.0%, E2E 72.0%, Brier 0.1780, ECE 0.1850
    comparativa_fase7 = {
        "fase7_baseline": {
            "top1_ml": "66.0%",
            "top3_ml": "84.0%",
            "rag_hit1": "64.0%",
            "rag_hit3": "80.0%",
            "e2e_estricto": "72.0%",
            "brier": "0.1780",
            "ece": "0.1850",
        },
        "fase8_3_congelada": {
            "top1_ml": f"{pct_top1}%",
            "top3_ml": f"{pct_top3}%",
            "rag_hit1": f"{pct_rag_hit1}%",
            "rag_hit3": f"{pct_rag_hit3}%",
            "e2e_estricto": f"{pct_e2e_estricto}%",
            "brier": f"{calib['brier']:.4f}",
            "ece": f"{calib['ece']:.4f}",
        },
        "delta": {
            "delta_top1": f"{pct_top1 - 66.0:+.2f}%",
            "delta_top3": f"{pct_top3 - 84.0:+.2f}%",
            "delta_e2e": f"{pct_e2e_estricto - 72.0:+.2f}%",
            "delta_ece": f"{calib['ece'] - 0.1850:+.4f}",
        }
    }

    resultado_completo = {
        "benchmark": "G1_01_a_G1_50_REGRESION_ESTRES",
        "total_casos": total,
        "metricas": {
            "top1_ml": pct_top1,
            "top3_ml": pct_top3,
            "macro_sistema": pct_macro,
            "rag_hit1": pct_rag_hit1,
            "rag_hit3": pct_rag_hit3,
            "rag_hit5": pct_rag_hit5,
            "rag_mrr": rag_mrr,
            "e2e_estricto": pct_e2e_estricto,
            "e2e_diferencial": pct_e2e_diferencial,
            "e2e_incorrecto": pct_e2e_incorrecto,
            "brier": calib["brier"],
            "ece": calib["ece"],
            "acc_gte_80": calib["acc_gte_80"],
            "cov_gte_80": calib["cov_gte_80"],
            "conf_aciertos": calib["conf_aciertos"],
            "conf_errores": calib["conf_errores"],
            "reliability_bins": calib["bins"],
            "transiciones": {
                "ml_top1_a_e2e_correcto": ml_top1_a_e2e_correcto,
                "ml_top1_inc_a_e2e_rescate": ml_top1_inc_a_e2e_rescate,
                "ml_top1_corr_a_e2e_degradado": ml_top1_corr_a_e2e_degradado,
                "ml_top3_tenia_gt_e2e_perdio": ml_top3_tenia_gt_e2e_perdio,
            },
            "latencias_ms": {
                "ml_media": round(float(np.mean(tiempos_ml)), 2),
                "rag_media": round(float(np.mean(tiempos_rag)), 2),
                "total_media": round(float(np.mean(tiempos_total)), 2),
            },
        },
        "comparativa_fase7": comparativa_fase7,
        "detalles_casos": detalles,
    }

    salida = BASE_DIR / "machine_learning" / "models" / "reporte_fase8_3_g1_estres.json"
    salida.write_text(json.dumps(resultado_completo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReporte JSON guardado en:\n{salida}")

if __name__ == "__main__":
    main()
