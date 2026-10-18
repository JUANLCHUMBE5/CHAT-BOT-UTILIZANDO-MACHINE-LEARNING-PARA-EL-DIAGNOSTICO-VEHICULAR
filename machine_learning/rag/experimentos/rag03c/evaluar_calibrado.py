# -*- coding: utf-8 -*-
import json
import pathlib
import sys
import unicodedata
import faiss
import joblib
import numpy as np

BASE_DIR = pathlib.Path("machine_learning/rag/experimentos/rag03c")
CORPUS_DIR = BASE_DIR / "corpus_experimental"
INDICES_DIR = BASE_DIR / "indices_temporales"
RESULTADOS_DIR = BASE_DIR / "resultados"

sys.path.insert(0, str(BASE_DIR))
from benchmark_queries import BENCHMARK_QUERIES

def normalizar_texto(t):
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")

corpus_A = json.loads((CORPUS_DIR / "corpus_A_original_239.json").read_text(encoding="utf-8"))
corpus_B = json.loads((CORPUS_DIR / "corpus_B_experimental.json").read_text(encoding="utf-8"))

vec_A = joblib.load(INDICES_DIR / "vectorizador_test_A.joblib")
idx_A = faiss.read_index(str(INDICES_DIR / "indice_faiss_test_A.index"))

vec_B = joblib.load(INDICES_DIR / "vectorizador_test_B.joblib")
idx_B = faiss.read_index(str(INDICES_DIR / "indice_faiss_test_B.index"))

UMBRAL_CALIBRADO = 0.10

def buscar(query, vec, index, corpus, k=3):
    q_vec = vec.transform([query]).toarray().astype(np.float32)
    faiss.normalize_L2(q_vec)
    scores, indices = index.search(q_vec, k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(corpus):
            continue
        doc = corpus[idx]
        results.append({
            "doc_id": doc["doc_id"],
            "titulo": doc["titulo"],
            "sistema": doc["sistema"],
            "pagina": doc["pagina"],
            "manual_oem": doc["manual_oem"],
            "texto": doc["texto"],
            "score": float(score),
            "es_experimental": doc.get("es_experimental", False),
        })
    return results

resultados_eval = []
for bq in BENCHMARK_QUERIES:
    q = bq["consulta"]
    cat = bq["categoria"]
    espera_cob = bq["espera_cobertura"]
    tokens_target = [normalizar_texto(t) for t in bq["tokens_clave"]]

    res_A = buscar(q, vec_A, idx_A, corpus_A, k=3)
    res_B = buscar(q, vec_B, idx_B, corpus_B, k=3)

    def evaluar_salida(res):
        if not res or res[0]["score"] < UMBRAL_CALIBRADO:
            abst = True
            p1 = 1.0 if not espera_cob else 0.0
            r3 = 1.0 if not espera_cob else 0.0
            top_doc = "ABSTENCIÓN (Sin cobertura suficiente)"
            top_score = 0.0
            top_pag = 0
            top_oem = "N/A"
            incorrecto = False
            trazable = False
        else:
            abst = False
            top_text = normalizar_texto(f"{res[0]['titulo']} {res[0]['sistema']} {res[0]['texto'][:500]}")
            match_p1 = any(tk in top_text for tk in tokens_target) if espera_cob else False

            if espera_cob:
                p1 = 1.0 if match_p1 else 0.0
                found_r3 = False
                for r in res:
                    txt_r = normalizar_texto(f"{r['titulo']} {r['sistema']} {r['texto'][:500]}")
                    if any(tk in txt_r for tk in tokens_target):
                        found_r3 = True
                        break
                r3 = 1.0 if found_r3 else 0.0
                incorrecto = not match_p1
            else:
                p1 = 0.0
                r3 = 0.0
                incorrecto = True

            top_doc = res[0]["titulo"]
            top_score = res[0]["score"]
            top_pag = res[0]["pagina"]
            top_oem = res[0]["manual_oem"]
            trazable = bool(top_oem and top_pag > 0)

        return {
            "abstencion": abst,
            "p1": p1,
            "r3": r3,
            "incorrecto": incorrecto,
            "trazable": trazable,
            "top_doc": top_doc,
            "top_score": top_score,
            "top_pag": top_pag,
            "top_oem": top_oem,
        }

    ev_A = evaluar_salida(res_A)
    ev_B = evaluar_salida(res_B)
    mejora = (ev_B["p1"] > ev_A["p1"]) or (ev_B["r3"] > ev_A["r3"])
    empeoro = (ev_B["p1"] < ev_A["p1"]) or (ev_B["r3"] < ev_A["r3"])

    resultados_eval.append({
        "id": bq["id"],
        "categoria": cat,
        "consulta": q,
        "espera_cobertura": espera_cob,
        "eval_A": ev_A,
        "eval_B": ev_B,
        "mejora": mejora,
        "empeoro": empeoro,
    })

p1_A_all = np.mean([r["eval_A"]["p1"] for r in resultados_eval])
r3_A_all = np.mean([r["eval_A"]["r3"] for r in resultados_eval])
in_domain = [r for r in resultados_eval if r["espera_cobertura"]]
p1_A_in = np.mean([r["eval_A"]["p1"] for r in in_domain])
r3_A_in = np.mean([r["eval_A"]["r3"] for r in in_domain])

p1_B_all = np.mean([r["eval_B"]["p1"] for r in resultados_eval])
r3_B_all = np.mean([r["eval_B"]["r3"] for r in resultados_eval])
p1_B_in = np.mean([r["eval_B"]["p1"] for r in in_domain])
r3_B_in = np.mean([r["eval_B"]["r3"] for r in in_domain])

abst_A_ood = np.mean([r["eval_A"]["abstencion"] for r in resultados_eval if not r["espera_cobertura"]])
abst_B_ood = np.mean([r["eval_B"]["abstencion"] for r in resultados_eval if not r["espera_cobertura"]])

n_mejora = sum(1 for r in resultados_eval if r["mejora"])
n_empeoro = sum(1 for r in resultados_eval if r["empeoro"])
n_igual = len(resultados_eval) - n_mejora - n_empeoro

print("=== EVALUACION CON UMBRAL DE PRODUCCION (0.10) ===")
print(f"Corpus A (Original 239) -> P@1 Total: {p1_A_all*100:.1f}% | In-Domain P@1: {p1_A_in*100:.1f}% | R@3: {r3_A_in*100:.1f}%")
print(f"Corpus B (Experim. 256) -> P@1 Total: {p1_B_all*100:.1f}% | In-Domain P@1: {p1_B_in*100:.1f}% | R@3: {r3_B_in*100:.1f}%")
print(f"Abstención OOD: A={abst_A_ood*100:.1f}% | B={abst_B_ood*100:.1f}%")
print(f"Balance: Mejoraron {n_mejora} casos, Empeoraron {n_empeoro} casos, Iguales {n_igual} casos.")

(RESULTADOS_DIR / "reporte_evaluacion_rag03c_calibrado_010.json").write_text(
    json.dumps(resultados_eval, indent=2, ensure_ascii=False), encoding="utf-8"
)
