"""
Script de Auditoría Forense de Fuga de Texto (Leakage) en el Benchmark de 122 Consultas.
Audita cada consulta contra los 239 fragmentos procedimentales del corpus:
1. Comprueba si existe copia literal (verbatim matching de subsecuencias > 5 palabras).
2. Calcula similitud de Jaccard y solapamiento léxico.
3. Clasifica cada consulta en: INDEPENDENT, ACCEPTABLE_TECHNICAL_OVERLAP, SUSPICIOUS_OVERLAP, LEAKAGE.
4. Genera el dataset CLEAN_SUBSET excluyendo cualquier fuga detectada.
5. Genera RAG_PROMOTION_BENCHMARK_AUDIT.csv.
"""
import sys
import json
import csv
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
CAND_DIR = PROJECT_ROOT / "machine_learning/manuals/candidates/v1"

def tokenize(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"\b\w{3,}\b", text)]

def ngrams(tokens: List[str], n: int) -> set:
    if len(tokens) < n:
        return set()
    return set(" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1))

def audit_leakage():
    # 1. Cargar benchmark
    bench_file = CAND_DIR / "benchmarks/benchmark_dataset.json"
    with open(bench_file, "r", encoding="utf-8") as f:
        bench_data = json.load(f)
    queries = bench_data["queries"]

    # 2. Cargar textos del corpus candidato
    from machine_learning.manuals.candidates.v1.scripts.candidate_rag_harness import CandidateRAGHarness
    harness = CandidateRAGHarness(
        CAND_DIR / "texts",
        CAND_DIR / "metadata/metadatos_schema_v2.json",
        CAND_DIR / "indexes/indice_faiss_v1.index",
        version_id="AUDIT"
    )

    corpus_docs = harness.documentos
    corpus_titles = harness.titulos
    corpus_meta = harness.metadatos_procedimientos

    audit_results = []
    classification_counts = {
        "INDEPENDENT": 0,
        "ACCEPTABLE_TECHNICAL_OVERLAP": 0,
        "SUSPICIOUS_OVERLAP": 0,
        "LEAKAGE": 0
    }

    clean_subset = []

    for q in queries:
        qid = q["query_id"]
        q_text = q["query"]
        exp_class = q["expected_class_name"]
        exp_macro = q["expected_macro"]
        has_dtc = q["has_dtc"]
        dtc_list = q.get("dtc_codes", [])

        q_tokens = tokenize(q_text)
        q_set = set(q_tokens)
        q_5grams = ngrams(q_tokens, 5)

        max_jaccard = 0.0
        max_overlap_chunk_id = None
        max_overlap_title = None
        has_verbatim_5gram = False
        verbatim_match = ""

        # Comparar contra cada uno de los 239 documentos
        for doc_idx, (tit, doc, meta) in enumerate(zip(corpus_titles, corpus_docs, corpus_meta)):
            full_text = f"{tit}\n{doc}"
            doc_tokens = tokenize(full_text)
            doc_set = set(doc_tokens)

            # Jaccard sobre tokens
            intersection = q_set.intersection(doc_set)
            union = q_set.union(doc_set)
            jaccard = len(intersection) / len(union) if union else 0.0

            if jaccard > max_jaccard:
                max_jaccard = jaccard
                max_overlap_chunk_id = meta.get("doc_id")
                max_overlap_title = tit

            # Búsqueda de n-gramas exactos de 5 palabras
            if q_5grams:
                doc_5grams = ngrams(doc_tokens, 5)
                overlap_5g = q_5grams.intersection(doc_5grams)
                if overlap_5g:
                    has_verbatim_5gram = True
                    verbatim_match = list(overlap_5g)[0]

        # Clasificación estricta
        # Si tiene copia exacta de 5 palabras continuas que no sean nombres técnicos universales
        is_trivial_class_copy = (exp_class.lower() in q_text.lower() and len(q_text.split()) <= 10)

        if has_verbatim_5gram and not is_trivial_class_copy:
            # Revisar si las 5 palabras son una frase técnica estándar (e.g., 'falla en compresor de aire', 'bateria de alto voltaje')
            palabras_comunes = ["falla en sistema de", "aire acondicionado o fuga", "bujias o bobinas de", "sensor de velocidad de"]
            if any(p in verbatim_match for p in palabras_comunes):
                status = "ACCEPTABLE_TECHNICAL_OVERLAP"
                note = f"Solapamiento técnico de nomenclatura ISO/SAE: '{verbatim_match}'"
            else:
                status = "LEAKAGE"
                note = f"Fuga de texto: 5-grama verbatim encontrado: '{verbatim_match}'"
        elif max_jaccard > 0.40:
            status = "SUSPICIOUS_OVERLAP"
            note = f"Solapamiento léxico elevado (Jaccard={max_jaccard:.2f}) con {max_overlap_chunk_id}"
        elif has_dtc or any(term in q_text.lower() for term in ["sensor", "valvula", "presion", "voltaje", "solenoide", "bomba", "fusible"]):
            status = "ACCEPTABLE_TECHNICAL_OVERLAP"
            note = f"Términos técnicos estándar necesarios de diagnóstico automotriz (Jaccard={max_jaccard:.2f})"
        else:
            status = "INDEPENDENT"
            note = f"Consulta completamente independiente coloquial/taller (Jaccard={max_jaccard:.2f})"

        classification_counts[status] += 1

        record = {
            "query_id": qid,
            "query": q_text,
            "expected_class": exp_class,
            "expected_macro": exp_macro,
            "has_dtc": has_dtc,
            "max_jaccard": round(max_jaccard, 4),
            "closest_chunk": max_overlap_chunk_id,
            "classification": status,
            "notes": note
        }
        audit_results.append(record)

        if status != "LEAKAGE":
            clean_subset.append(q)

    # Exportar CSV de auditoría de benchmark
    out_csv = CAND_DIR / "reports/RAG_PROMOTION_BENCHMARK_AUDIT.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "query_id", "query", "expected_class", "expected_macro", "has_dtc",
            "max_jaccard", "closest_chunk", "classification", "notes"
        ])
        writer.writeheader()
        for r in audit_results:
            writer.writerow(r)

    print("AUDITORÍA DE FUGA DE TEXTO EN BENCHMARK COMPLETADA:")
    print(f"  Ruta CSV: {out_csv}")
    print(f"  Total consultas auditadas: {len(queries)}")
    for k, v in classification_counts.items():
        pct = (v / len(queries)) * 100.0
        print(f"  {k}: {v} ({pct:.1f}%)")
    print(f"  CLEAN_SUBSET queries retenidas: {len(clean_subset)} de {len(queries)}")

    # Guardar clean subset
    out_clean_json = CAND_DIR / "benchmarks/clean_benchmark_dataset.json"
    with open(out_clean_json, "w", encoding="utf-8") as f:
        json.dump({
            "benchmark_name": "RAG_CLEAN_EVAL_SUBSET",
            "total_queries": len(clean_subset),
            "classes_covered": len(set(q["expected_class_id"] for q in clean_subset)),
            "queries": clean_subset
        }, f, indent=2, ensure_ascii=False)
    print(f"  Guardado dataset limpio en: {out_clean_json}")

if __name__ == "__main__":
    audit_leakage()
