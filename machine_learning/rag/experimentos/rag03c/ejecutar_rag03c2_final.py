# -*- coding: utf-8 -*-
"""Script Maestro RAG-03C.2: Evaluación con Control Estricto de Especificaciones OEM.

Ejecuta:
1. Re-evaluación del Benchmark de 100 consultas con el controlador de especificaciones OEM.
2. Evaluación del conjunto de 30 Pruebas Adversariales Independientes.
3. Tipificación de los 5 niveles documentales.
4. Generación de métricas finales antes/después y reporte consolidado de aptitud de integración.
"""

import csv
import json
import math
import sys
import time
import unicodedata
from pathlib import Path

import faiss
import joblib
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = Path(".").resolve()
CORPUS_DIR = BASE_DIR / "corpus_experimental"
INDICES_DIR = BASE_DIR / "indices_temporales"
RESULTADOS_DIR = BASE_DIR / "resultados"

sys.path.insert(0, str(BASE_DIR))
from benchmark_100_queries import BENCHMARK_100_QUERIES
from controlador_especificaciones_oem import clasificar_y_filtrar_candidato_rag03c2, normalizar
from fragmentos_data import FRAGMENTOS_5PDFS
from pruebas_adversariales_30 import PRUEBAS_ADVERSARIALES_30

# Cargar indices y corpus
corpus_A = json.loads((CORPUS_DIR / "corpus_A_original_239.json").read_text(encoding="utf-8"))
corpus_B = json.loads((CORPUS_DIR / "corpus_B_experimental.json").read_text(encoding="utf-8"))

vec_A = joblib.load(INDICES_DIR / "vectorizador_test_A.joblib")
idx_A = faiss.read_index(str(INDICES_DIR / "indice_faiss_test_A.index"))

vec_B = joblib.load(INDICES_DIR / "vectorizador_test_B.joblib")
idx_B = faiss.read_index(str(INDICES_DIR / "indice_faiss_test_B.index"))

STOP_WORDS_GEN = {
    "cual",
    "como",
    "procedimiento",
    "prueba",
    "revisar",
    "vehiculo",
    "motor",
    "sistema",
    "falla",
    "problema",
    "manual",
    "tecnico",
    "consulta",
    "hacer",
    "medir",
    "pasos",
    "diagnostico",
    "especificacion",
    "tolerancia",
    "par",
    "apriete",
    "torque",
    "presion",
    "maximo",
    "minimo",
    "oficial",
    "grados",
    "valor",
    "admisible",
    "permitido",
}


def wilson_score_interval(successes: int, total: int, confidence: float = 0.95):
    if total == 0:
        return 0.0, 0.0, 0.0
    p = successes / total
    z = 1.96
    denom = 1 + z**2 / total
    centre_adj_prob = p + z**2 / (2 * total)
    adjusted_std_dev = math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total)
    lower = max(0.0, (centre_adj_prob - z * adjusted_std_dev) / denom)
    upper = min(1.0, (centre_adj_prob + z * adjusted_std_dev) / denom)
    return p, lower, upper


def buscar_raw(query: str, vec, index, corpus, k=5):
    q_vec = vec.transform([query]).toarray().astype(np.float32)
    faiss.normalize_L2(q_vec)
    scores, indices = index.search(q_vec, k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(corpus):
            continue
        doc = corpus[idx]
        results.append(
            {
                **doc,
                "doc_id": doc["doc_id"],
                "titulo": doc["titulo"],
                "sistema": doc["sistema"],
                "marca": doc.get("marca", "Universal"),
                "modelo": doc.get("modelo", "Universal"),
                "pagina": doc["pagina"],
                "manual_oem": doc["manual_oem"],
                "documento": doc["texto"],
                "texto": doc["texto"],
                "similitud": float(score),
                "es_experimental": doc.get("es_experimental", False),
            }
        )
    return results


def evaluar_suite(suite_queries, nombre_suite="benchmark_100"):
    UMBRAL = 0.10
    resultados = []

    for item in suite_queries:
        q_id = item["id"]
        fam = item.get("familia", "GENERAL")
        q = item["consulta"]
        veh = item.get("vehiculo", "Universal")
        sis = item.get("sistema", "GENERAL")
        espera_cob = item["espera_cobertura"]
        tokens_target = [normalizar(t) for t in item["tokens_clave"]]
        tokens_q = {t for t in normalizar(q).split() if len(t) >= 4 and t not in STOP_WORDS_GEN}

        # Buscar en B raw
        cands_B_raw = buscar_raw(q, vec_B, idx_B, corpus_B, k=5)

        # Aplicar Pipeline Híbrido: Relevancia + Controlador OEM
        cands_B_c2 = []
        for c in cands_B_raw:
            score_base = float(c["similitud"])
            texto_doc = normalizar(c["titulo"] + " " + c["texto"])
            coincidencias = {t for t in tokens_q if t in texto_doc}

            # 1. Filtro de anclaje léxico
            f_rel = 1.0
            if len(coincidencias) == 0:
                f_rel *= 0.02
            elif len(coincidencias) == 1 and score_base < 0.25:
                f_rel *= 0.20

            # 2. Controlador de componentes y especificaciones OEM
            categoria_doc, f_oem, dictamen = clasificar_y_filtrar_candidato_rag03c2(
                q, c, vehiculo_consulta=veh, sistema_consulta=sis
            )

            score_final = score_base * f_rel * f_oem
            c_mod = dict(c)
            c_mod["categoria_doc"] = categoria_doc
            c_mod["similitud"] = score_final
            c_mod["dictamen"] = dictamen
            cands_B_c2.append(c_mod)

        cands_B_c2.sort(key=lambda x: x["similitud"], reverse=True)

        def evaluar_salida(cands):
            if not cands or cands[0]["similitud"] < UMBRAL:
                abst = True
                p1 = 1.0 if not espera_cob else 0.0
                r3 = 1.0 if not espera_cob else 0.0
                top_doc = "ABSTENCIÓN (Sin especificación OEM verificada)"
                score = 0.0
                cat_doc = "AUSENCIA_DOCUMENTACION"
                falso_pos = False
            else:
                abst = False
                top_doc_full = normalizar(f"{cands[0]['titulo']} {cands[0]['sistema']} {cands[0]['texto']}")
                match_p1 = any(tk in top_doc_full for tk in tokens_target) if espera_cob else False

                if espera_cob:
                    p1 = 1.0 if match_p1 else 0.0
                    found_r3 = False
                    for c in cands[:3]:
                        txt_c = normalizar(f"{c['titulo']} {c['sistema']} {c['texto']}")
                        if any(tk in txt_c for tk in tokens_target):
                            found_r3 = True
                            break
                    r3 = 1.0 if found_r3 else 0.0
                    falso_pos = not match_p1
                else:
                    p1 = 0.0
                    r3 = 0.0
                    falso_pos = True

                top_doc = cands[0]["titulo"]
                score = cands[0]["similitud"]
                cat_doc = cands[0]["categoria_doc"]

            return {
                "abstencion": abst,
                "p1": p1,
                "r3": r3,
                "falso_positivo": falso_pos,
                "top_doc": top_doc,
                "score": score,
                "categoria_doc": cat_doc,
            }

        ev_res = evaluar_salida(cands_B_c2)
        resultados.append(
            {
                "id": q_id,
                "familia": fam,
                "consulta": q,
                "vehiculo": veh,
                "sistema": sis,
                "espera_cobertura": espera_cob,
                "eval": ev_res,
            }
        )

    # Métricas consolidadas
    total = len(resultados)
    indomain = [r for r in resultados if r["espera_cobertura"]]
    ood = [r for r in resultados if not r["espera_cobertura"]]

    p1_tot = sum(r["eval"]["p1"] for r in resultados)
    p1_in = sum(r["eval"]["p1"] for r in indomain)
    r3_in = sum(r["eval"]["r3"] for r in indomain)
    abst_ood = sum(1 for r in ood if r["eval"]["abstencion"])
    fp_tot = sum(1 for r in resultados if r["eval"]["falso_positivo"])

    p1_val, p1_low, p1_up = wilson_score_interval(int(p1_tot), total)
    p1_in_val, p1_in_low, p1_in_up = wilson_score_interval(int(p1_in), len(indomain))
    r3_in_val, r3_in_low, r3_in_up = wilson_score_interval(int(r3_in), len(indomain))
    abst_val, abst_low, abst_up = wilson_score_interval(abst_ood, len(ood))
    fp_val, fp_low, fp_up = wilson_score_interval(fp_tot, total)

    # Desglose por familia
    fam_stats = {}
    familias = sorted(list({r["familia"] for r in resultados}))
    for f in familias:
        sub = [r for r in resultados if r["familia"] == f]
        sub_p1 = sum(r["eval"]["p1"] for r in sub)
        sub_abst = sum(1 for r in sub if r["eval"]["abstencion"])
        sub_fp = sum(1 for r in sub if r["eval"]["falso_positivo"])
        fam_stats[f] = {
            "n": len(sub),
            "precision_at_1": round((sub_p1 / len(sub)) * 100, 1),
            "abstencion": round((sub_abst / len(sub)) * 100, 1),
            "falsos_positivos": round((sub_fp / len(sub)) * 100, 1),
        }

    return {
        "suite": nombre_suite,
        "n": total,
        "precision_at_1_total": {"val": round(p1_val * 100, 1), "ci95": [round(p1_low * 100, 1), round(p1_up * 100, 1)]},
        "precision_at_1_indomain": {"val": round(p1_in_val * 100, 1), "ci95": [round(p1_in_low * 100, 1), round(p1_in_up * 100, 1)]},
        "recall_at_3_indomain": {"val": round(r3_in_val * 100, 1), "ci95": [round(r3_in_low * 100, 1), round(r3_in_up * 100, 1)]},
        "abstencion_correcta_ood": {"val": round(abst_val * 100, 1), "ci95": [round(abst_low * 100, 1), round(abst_up * 100, 1)]},
        "tasa_falsos_positivos": {"val": round(fp_val * 100, 1), "ci95": [round(fp_low * 100, 1), round(fp_up * 100, 1)]},
        "por_familia": fam_stats,
        "detalle": resultados,
    }


def main():
    print("=" * 80)
    print("CARBOT — EJECUCIÓN RAG-03C.2 (CONTROL OEM + PRUEBAS ADVERSARIALES)")
    print("=" * 80)

    # 1. Evaluar Benchmark 100 consultas
    res_100 = evaluar_suite(BENCHMARK_100_QUERIES, "benchmark_100_queries")

    # 2. Evaluar Suite 30 Adversariales
    res_adv = evaluar_suite(PRUEBAS_ADVERSARIALES_30, "suite_30_adversariales")

    # Guardar resultados
    (RESULTADOS_DIR / "reporte_rag03c2_benchmark100.json").write_text(
        json.dumps(res_100, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (RESULTADOS_DIR / "reporte_rag03c2_adversariales30.json").write_text(
        json.dumps(res_adv, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\n[BENCHMARK 100 CONSULTAS — CON CONTROLADOR RAG-03C.2]")
    print(f"Precision@1 Global:      {res_100['precision_at_1_total']['val']}% {res_100['precision_at_1_total']['ci95']}")
    print(f"Precision@1 In-Domain:   {res_100['precision_at_1_indomain']['val']}% {res_100['precision_at_1_indomain']['ci95']}")
    print(f"Recall@3 In-Domain:      {res_100['recall_at_3_indomain']['val']}% {res_100['recall_at_3_indomain']['ci95']}")
    print(f"Abstención OOD Correcta: {res_100['abstencion_correcta_ood']['val']}% {res_100['abstencion_correcta_ood']['ci95']}")
    print(f"Tasa Falsos Positivos:   {res_100['tasa_falsos_positivos']['val']}% {res_100['tasa_falsos_positivos']['ci95']}")

    print("\nDesglose por Familias (Benchmark 100):")
    for fam, stats in res_100["por_familia"].items():
        print(f"  * {fam:40s} (n={stats['n']:2d}) -> P@1={stats['precision_at_1']:5.1f}% | Abstención={stats['abstencion']:5.1f}% | Falsos Positivos={stats['falsos_positivos']:5.1f}%")

    print("\n[SUITE 30 PRUEBAS ADVERSARIALES — TRAMPAS LÉXICAS Y MERCADO PERÚ]")
    print(f"Precision@1 Global:      {res_adv['precision_at_1_total']['val']}% {res_adv['precision_at_1_total']['ci95']}")
    print(f"Abstención OOD Correcta: {res_adv['abstencion_correcta_ood']['val']}% {res_adv['abstencion_correcta_ood']['ci95']}")
    print(f"Tasa Falsos Positivos:   {res_adv['tasa_falsos_positivos']['val']}% {res_adv['tasa_falsos_positivos']['ci95']}")

    print("\nDesglose por Familias (Adversariales 30):")
    for fam, stats in res_adv["por_familia"].items():
        print(f"  * {fam:40s} (n={stats['n']:2d}) -> P@1={stats['precision_at_1']:5.1f}% | Abstención={stats['abstencion']:5.1f}% | Falsos Positivos={stats['falsos_positivos']:5.1f}%")

    print("=" * 80)


if __name__ == "__main__":
    main()
