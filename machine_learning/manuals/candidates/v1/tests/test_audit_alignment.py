"""
Test de verificación estricta de alineación posicional 1:1 en Candidato V1:
FAISS[i] <-> TEXT[i] <-> METADATA[i] <-> MANIFEST[i].
"""
import sys
import json
import hashlib
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from machine_learning.manuals.candidates.v1.scripts.candidate_rag_harness import CandidateRAGHarness

def test_alignment():
    cand_dir = PROJECT_ROOT / "machine_learning/manuals/candidates/v1"
    h = CandidateRAGHarness(
        cand_dir / "texts",
        cand_dir / "metadata/metadatos_schema_v2.json",
        cand_dir / "indexes/indice_faiss_v1.index"
    )

    with open(cand_dir / "manifests/corpus_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)

    entries = manifest["entries"]
    assert len(h.documentos) == 239, f"Documentos={len(h.documentos)}"
    assert len(h.metadatos_procedimientos) == 239, f"Metadatos={len(h.metadatos_procedimientos)}"
    assert h.faiss_index.ntotal == 239, f"FAISS={h.faiss_index.ntotal}"
    assert len(entries) == 239, f"Manifest={len(entries)}"

    for i in range(239):
        m_entry = entries[i]
        assert m_entry["position"] == i, f"Desalineación de posición en {i}"
        meta_item = h.metadatos_procedimientos[i]
        assert m_entry["doc_id"] == meta_item["doc_id"], f"Doc ID mismatch en {i}"

        # Hash check
        full_text = f"{h.titulos[i]}\n{h.documentos[i]}"
        txt_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
        assert m_entry["text_hash"] == txt_hash, f"Text hash mismatch en {i}"

    print("239/239 ALINEACIÓN POSICIONAL COMPROBADA: FAISS[i] <-> TEXT[i] <-> METADATA[i] <-> MANIFEST[i] (100% OK)!")

if __name__ == "__main__":
    test_alignment()
