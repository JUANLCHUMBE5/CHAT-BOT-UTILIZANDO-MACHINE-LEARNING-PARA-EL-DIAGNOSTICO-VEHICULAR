"""Sella la entrega existente. No entrena, no reconstruye ni modifica corpus/índices."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXP = ROOT / "machine_learning/rag/experimentos/rag03c"


def main():
    old = json.loads(
        (EXP / "manifiesto_reproducible_rag03f.json").read_text(encoding="utf-8")
    )
    files = {}
    for group in ("archivos_fuente_pdfs", "artefactos_experimentales"):
        for entry in old[group].values():
            rel = entry["ruta_relativa"].replace("\\", "/")
            p = ROOT / rel
            files[rel] = {
                "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
    adapter = (
        "machine_learning/rag/experimentos/rag03c/controlador_especificaciones_oem.py"
    )
    p = ROOT / adapter
    files[adapter] = {
        "bytes": p.stat().st_size,
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
    }
    corpus = json.loads(
        (EXP / "corpus_experimental/corpus_B_experimental.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = dict(
        schema="carbot.rag.experimental/1",
        version="RAG-03G-256",
        procedencia="RAG-03F-AGENTE2-20261018",
        corpus_validado=False,
        receta="titulo+LF+texto;tfidf;float32;l2",
        dimension=35240,
        orden_doc_ids=[d["doc_id"] for d in corpus],
        archivos=files,
        roles={
            k: "machine_learning/rag/experimentos/rag03c/" + v
            for k, v in {
                "corpus": "corpus_experimental/corpus_B_experimental.json",
                "vectorizador": "indices_temporales/vectorizador_test_B.joblib",
                "indice": "indices_temporales/indice_faiss_test_B.index",
                "fragmentos": "corpus_experimental/fragmentos_nuevos_5pdfs.json",
            }.items()
        },
    )
    (EXP / "manifiesto_rag03g.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    print("Manifiesto RAG-03G generado; no habilita uso productivo")


if __name__ == "__main__":
    main()
