# -*- coding: utf-8 -*-
"""Script Maestro de Ejecución del Experimento RAG-03C.

Construye Corpus A (239) y Corpus B (256), entrena vectorizadores e índices FAISS temporales,
ejecuta benchmark de 25 consultas y emite métricas completas en resultados/.
"""

import csv
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import faiss
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent
CORPUS_DIR = BASE_DIR / "corpus_experimental"
INDICES_DIR = BASE_DIR / "indices_temporales"
RESULTADOS_DIR = BASE_DIR / "resultados"

CORPUS_DIR.mkdir(parents=True, exist_ok=True)
INDICES_DIR.mkdir(parents=True, exist_ok=True)
RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)

# Importar configuraciones locales
sys.path.insert(0, str(BASE_DIR))
from benchmark_queries import BENCHMARK_QUERIES
from fragmentos_data import FRAGMENTOS_5PDFS

# Cargar stop words de CarBot
ROOT_DIR = Path(".").resolve()
sys.path.insert(0, str(ROOT_DIR / "backend"))
from src.infrastructure.rag_checks.vectorizer_config import SPANISH_STOP_WORDS


def normalizar_texto(t: str) -> str:
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def cargar_corpus_original_239() -> list[dict]:
    v1_dir = ROOT_DIR / "machine_learning/manuals/candidates/v1"
    meta_path = v1_dir / "metadata/metadatos_schema_v2.json"
    texts_dir = v1_dir / "texts"

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    by_title = {item["titulo"].strip().lower(): item for item in meta}
    registered = {item["archivo_fuente"].replace("\\", "/") for item in meta}

    corpus = []
    seen = set()
    for rel in sorted(registered):
        p = texts_dir / rel
        content = p.read_text(encoding="utf-8")
        for match in re.finditer(
            r"^===\s*(.*?)\s*===\s*\n(.*?)(?=^===|\Z)", content, flags=re.M | re.S
        ):
            title = match.group(1).strip()
            body = match.group(2).strip()
            key = title.lower()
            if not body or key in seen or key not in by_title:
                continue
            seen.add(key)
            m = by_title[key]
            corpus.append(
                {
                    "doc_id": m.get("doc_id") or m.get("id_procedimiento"),
                    "titulo": title,
                    "texto": body,
                    "marca": m.get("marca", "Universal"),
                    "modelo": m.get("modelo", "Universal"),
                    "anio": m.get("anio", "Universal"),
                    "motor": m.get("motor", "Universal"),
                    "sistema": m.get("sistema", "GENERAL"),
                    "falla": m.get("falla", ""),
                    "pagina": m.get("pagina", 1),
                    "manual_oem": m.get("manual_oem", ""),
                    "archivo_fuente": rel,
                    "es_experimental": False,
                    "requiere_confirmacion_oem": False,
                }
            )
    return corpus


def main():
    print("=" * 70)
    print("CARBOT — INICIO EXPERIMENTO RAG-03C")
    print("=" * 70)

    # 1. Cargar y registrar Corpus A (Original 239)
    corpus_A = cargar_corpus_original_239()
    assert len(corpus_A) == 239, f"Se esperaban 239 documentos, se obtuvieron {len(corpus_A)}"
    path_corpus_A = CORPUS_DIR / "corpus_A_original_239.json"
    path_corpus_A.write_text(json.dumps(corpus_A, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[FASE 1] Corpus A (Inmutable Original): {len(corpus_A)} documentos registrados.")

    # 2. Registrar fragmentos nuevos y generar Corpus B (256)
    path_frag = CORPUS_DIR / "fragmentos_nuevos_5pdfs.json"
    path_frag.write_text(json.dumps(FRAGMENTOS_5PDFS, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[FASE 1] Fragmentos autorizados extraídos: {len(FRAGMENTOS_5PDFS)} unidades.")

    fragmentos_B = []
    for f in FRAGMENTOS_5PDFS:
        cuerpo = (
            f"{f['titulo']}\n"
            f"Sistema: {f['sistema']} | Subsistema: {f['subsistema']}\n"
            f"Fabricante: {f['fabricante']} | Vehiculo: {f['vehiculo']}\n"
            f"Condiciones de medicion: {f['condiciones_medicion']}\n"
            f"Tolerancias y unidades: {f['tolerancias_unidades']}\n"
            f"Procedimiento:\n{f['procedimiento']}\n"
            f"Advertencias de seguridad: {f['advertencias_seguridad']}"
        )
        fragmentos_B.append(
            {
                "doc_id": f["doc_id"],
                "titulo": f["titulo"],
                "texto": cuerpo,
                "marca": f["fabricante"],
                "modelo": f["vehiculo"],
                "anio": f.get("anios_aplicables", "Universal"),
                "motor": f.get("motores_aplicables", "Universal"),
                "mercado": f.get("mercados_aplicables", "Global"),
                "sistema": f["sistema"],
                "falla": f["subsistema"],
                "componente": f.get("componente", f["subsistema"]),
                "pagina": f["pagina"],
                "paginas": f.get("paginas", [f["pagina"]]),
                "rango_paginas": f.get("rango_paginas", str(f["pagina"])),
                "manual_oem": f["pdf_origen"],
                "archivo_fuente": f"pdfs_autorizados/{f['pdf_origen']}",
                "es_experimental": True,
                "requiere_confirmacion_oem": f["requiere_confirmacion_oem"],
                "alcance_aplicacion": f.get("alcance_aplicacion", ""),
                "sha256_pdf": f.get("sha256_pdf", ""),
                "marcas_aplicables": f.get("marcas_aplicables", []),
                "modelos_aplicables": f.get("modelos_aplicables", []),
                "anios_aplicables": f.get("anios_aplicables", ""),
                "motores_aplicables": f.get("motores_aplicables", ""),
                "mercados_aplicables": f.get("mercados_aplicables", ""),
                "condiciones_uso": f.get("condiciones_uso", ""),
                "cifras_trazadas": f.get("cifras_trazadas", []),
            }
        )

    corpus_B = corpus_A + fragmentos_B
    assert len(corpus_B) == len(corpus_A) + len(FRAGMENTOS_5PDFS), f"Se esperaban {len(corpus_A) + len(FRAGMENTOS_5PDFS)} documentos, se obtuvieron {len(corpus_B)}"
    path_corpus_B = CORPUS_DIR / "corpus_B_experimental.json"
    path_corpus_B.write_text(json.dumps(corpus_B, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[FASE 1] Corpus B (Experimental): {len(corpus_B)} documentos creados.")

    # 3. Construcción de Vectorizadores e Índices Temporales
    def construir_indice(corpus, tag):
        textos = [f"{doc['titulo']}\n{doc['texto']}" for doc in corpus]
        vec = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            stop_words=SPANISH_STOP_WORDS,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        matriz = vec.fit_transform(textos).toarray().astype(np.float32)
        faiss.normalize_L2(matriz)
        dim = matriz.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(matriz)

        # Validacion estricta de correspondencia vector a vector (<= 1e-6)
        max_err = 0.0
        for i in range(index.ntotal):
            vec_idx = index.reconstruct(i)
            diff = float(np.max(np.abs(vec_idx - matriz[i])))
            if diff > max_err:
                max_err = diff
        assert max_err <= 1e-6, f"Error de correspondencia FAISS/TF-IDF: {max_err} mayor que 1e-6"
        print(f"[FASE 2] Coherencia Indice {tag}: correspondencia perfecta, error maximo={max_err:.2e}")

        vec_path = INDICES_DIR / f"vectorizador_test_{tag}.joblib"
        idx_path = INDICES_DIR / f"indice_faiss_test_{tag}.index"
        joblib.dump(vec, vec_path)
        faiss.write_index(index, str(idx_path))
        print(f"[FASE 2] Índice Temporal {tag} construido exitosamente: dimensión={dim}, docs={index.ntotal}")
        return vec, index

    vec_A, idx_A = construir_indice(corpus_A, "A")
    vec_B, idx_B = construir_indice(corpus_B, "B")

    # 4. Función de búsqueda y evaluación
    def buscar(query: str, vec, index, corpus, k=3):
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
                    "doc_id": doc["doc_id"],
                    "titulo": doc["titulo"],
                    "sistema": doc["sistema"],
                    "pagina": doc["pagina"],
                    "manual_oem": doc["manual_oem"],
                    "texto": doc["texto"],
                    "score": float(score),
                    "es_experimental": doc.get("es_experimental", False),
                }
            )
        return results

    UMBRAL_ABSTENCION = 0.16

    print("\n[FASE 3] Ejecutando evaluación comparativa de 25 consultas de taller...")
    resultados_eval = []

    for bq in BENCHMARK_QUERIES:
        q = bq["consulta"]
        cat = bq["categoria"]
        espera_cob = bq["espera_cobertura"]
        tokens_target = [normalizar_texto(t) for t in bq["tokens_clave"]]

        # Medir A
        t0 = time.perf_counter()
        res_A = buscar(q, vec_A, idx_A, corpus_A, k=3)
        lat_A = (time.perf_counter() - t0) * 1000.0

        # Medir B
        t0 = time.perf_counter()
        res_B = buscar(q, vec_B, idx_B, corpus_B, k=3)
        lat_B = (time.perf_counter() - t0) * 1000.0

        def evaluar_salida(res):
            if not res or res[0]["score"] < UMBRAL_ABSTENCION:
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
                top_text = normalizar_texto(
                    f"{res[0]['titulo']} {res[0]['sistema']} {res[0]['texto'][:300]}"
                )
                match_p1 = any(tk in top_text for tk in tokens_target) if espera_cob else False

                if espera_cob:
                    p1 = 1.0 if match_p1 else 0.0
                    # R@3
                    found_r3 = False
                    for r in res:
                        txt_r = normalizar_texto(f"{r['titulo']} {r['sistema']} {r['texto'][:300]}")
                        if any(tk in txt_r for tk in tokens_target):
                            found_r3 = True
                            break
                    r3 = 1.0 if found_r3 else 0.0
                    incorrecto = not match_p1
                else:
                    # No esperaba cobertura pero recuperó algo => alucinación / falso positivo
                    p1 = 0.0
                    r3 = 0.0
                    incorrecto = True

                top_doc = res[0]["titulo"]
                top_score = res[0]["score"]
                top_pag = res[0]["pagina"]
                top_oem = res[0]["manual_oem"]
                trazable = bool(top_oem and ((isinstance(top_pag, (int, float)) and top_pag > 0) or (isinstance(top_pag, str) and top_pag.strip() not in ('', '0'))))

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

        resultados_eval.append(
            {
                "id": bq["id"],
                "categoria": cat,
                "consulta": q,
                "espera_cobertura": espera_cob,
                "eval_A": ev_A,
                "lat_A_ms": lat_A,
                "eval_B": ev_B,
                "lat_B_ms": lat_B,
                "mejora": mejora,
                "empeoro": empeoro,
            }
        )

    # 5. Generar Reporte JSON y CSV
    path_rep_json = RESULTADOS_DIR / "reporte_evaluacion_rag03c.json"
    path_rep_json.write_text(
        json.dumps(resultados_eval, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    path_rep_csv = RESULTADOS_DIR / "comparacion_metrica_A_vs_B.csv"
    with open(path_rep_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "id",
                "categoria",
                "espera_cobertura",
                "A_P1",
                "A_R3",
                "A_Abst",
                "A_DocTop",
                "A_Score",
                "B_P1",
                "B_R3",
                "B_Abst",
                "B_DocTop",
                "B_Score",
                "Mejora",
                "Empeoro",
            ]
        )
        for r in resultados_eval:
            writer.writerow(
                [
                    r["id"],
                    r["categoria"],
                    r["espera_cobertura"],
                    r["eval_A"]["p1"],
                    r["eval_A"]["r3"],
                    r["eval_A"]["abstencion"],
                    r["eval_A"]["top_doc"],
                    f"{r['eval_A']['top_score']:.4f}",
                    r["eval_B"]["p1"],
                    r["eval_B"]["r3"],
                    r["eval_B"]["abstencion"],
                    r["eval_B"]["top_doc"],
                    f"{r['eval_B']['top_score']:.4f}",
                    r["mejora"],
                    r["empeoro"],
                ]
            )

    # 6. Calcular métricas consolidadas
    # Overall
    p1_A_all = np.mean([r["eval_A"]["p1"] for r in resultados_eval])
    r3_A_all = np.mean([r["eval_A"]["r3"] for r in resultados_eval])
    abst_A_ood = np.mean(
        [r["eval_A"]["abstencion"] for r in resultados_eval if not r["espera_cobertura"]]
    )
    inc_A_all = np.mean([1.0 if r["eval_A"]["incorrecto"] else 0.0 for r in resultados_eval])
    traz_A_all = np.mean([1.0 if r["eval_A"]["trazable"] else 0.0 for r in resultados_eval if r["eval_A"]["p1"] == 1.0] or [0.0])
    lat_A_mean = np.mean([r["lat_A_ms"] for r in resultados_eval])

    p1_B_all = np.mean([r["eval_B"]["p1"] for r in resultados_eval])
    r3_B_all = np.mean([r["eval_B"]["r3"] for r in resultados_eval])
    abst_B_ood = np.mean(
        [r["eval_B"]["abstencion"] for r in resultados_eval if not r["espera_cobertura"]]
    )
    inc_B_all = np.mean([1.0 if r["eval_B"]["incorrecto"] else 0.0 for r in resultados_eval])
    traz_B_all = np.mean([1.0 if r["eval_B"]["trazable"] else 0.0 for r in resultados_eval if r["eval_B"]["p1"] == 1.0] or [0.0])
    lat_B_mean = np.mean([r["lat_B_ms"] for r in resultados_eval])

    # In-domain (20 queries)
    in_domain = [r for r in resultados_eval if r["espera_cobertura"]]
    p1_A_in = np.mean([r["eval_A"]["p1"] for r in in_domain])
    r3_A_in = np.mean([r["eval_A"]["r3"] for r in in_domain])
    p1_B_in = np.mean([r["eval_B"]["p1"] for r in in_domain])
    r3_B_in = np.mean([r["eval_B"]["r3"] for r in in_domain])

    n_mejora = sum(1 for r in resultados_eval if r["mejora"])
    n_empeoro = sum(1 for r in resultados_eval if r["empeoro"])
    n_igual = len(resultados_eval) - n_mejora - n_empeoro

    resumen = {
        "metricas_consolidadas": {
            "corpus_A_239": {
                "precision_at_1_total": round(p1_A_all * 100, 2),
                "recall_at_3_total": round(r3_A_all * 100, 2),
                "precision_at_1_indomain": round(p1_A_in * 100, 2),
                "recall_at_3_indomain": round(r3_A_in * 100, 2),
                "abstencion_correcta_ood": round(abst_A_ood * 100, 2),
                "tasa_recuperacion_incorrecta": round(inc_A_all * 100, 2),
                "trazabilidad_documental": round(traz_A_all * 100, 2),
                "latencia_promedio_ms": round(lat_A_mean, 2),
            },
            "corpus_B_256": {
                "precision_at_1_total": round(p1_B_all * 100, 2),
                "recall_at_3_total": round(r3_B_all * 100, 2),
                "precision_at_1_indomain": round(p1_B_in * 100, 2),
                "recall_at_3_indomain": round(r3_B_in * 100, 2),
                "abstencion_correcta_ood": round(abst_B_ood * 100, 2),
                "tasa_recuperacion_incorrecta": round(inc_B_all * 100, 2),
                "trazabilidad_documental": round(traz_B_all * 100, 2),
                "latencia_promedio_ms": round(lat_B_mean, 2),
            },
            "balance_casos": {
                "total_consultas": len(resultados_eval),
                "consultas_mejoradas": n_mejora,
                "consultas_empeoradas": n_empeoro,
                "consultas_sin_cambio": n_igual,
            },
        }
    }

    (RESULTADOS_DIR / "resumen_metricas.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\n" + "=" * 70)
    print("RESULTADOS CONSOLIDADOS DEL EXPERIMENTO RAG-03C:")
    print("=" * 70)
    print(
        f"Corpus A (Original 239) -> P@1 Total: {p1_A_all*100:.1f}% | In-Domain: {p1_A_in*100:.1f}% | R@3 In-Domain: {r3_A_in*100:.1f}% | Latencia: {lat_A_mean:.2f} ms"
    )
    print(
        f"Corpus B (Experim. 256) -> P@1 Total: {p1_B_all*100:.1f}% | In-Domain: {p1_B_in*100:.1f}% | R@3 In-Domain: {r3_B_in*100:.1f}% | Latencia: {lat_B_mean:.2f} ms"
    )
    print(f"Abstención OOD: A={abst_A_ood*100:.1f}% | B={abst_B_ood*100:.1f}%")
    print(f"Tasa Doc Incorrecto: A={inc_A_all*100:.1f}% | B={inc_B_all*100:.1f}%")
    print(f"Balance: Mejoraron {n_mejora} casos, Empeoraron {n_empeoro} casos, Iguales {n_igual} casos.")
    print("=" * 70)


if __name__ == "__main__":
    main()
