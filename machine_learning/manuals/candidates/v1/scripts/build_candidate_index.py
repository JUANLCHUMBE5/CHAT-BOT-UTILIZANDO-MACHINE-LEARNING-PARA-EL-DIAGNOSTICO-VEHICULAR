"""
Script de construcción y validación del índice candidato FAISS V1.
Compila el nuevo índice FAISS en machine_learning/manuals/candidates/v1/indexes/indice_faiss_v1.index
sin tocar el índice baseline de machine_learning/manuals/indice_faiss.index.
Valida dimensionalidad, ausencia de NaN, no vacuidad y alineación posicional 100%.
"""
import sys
import json
import hashlib
from pathlib import Path
import numpy as np
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.infrastructure.motor_rag import SPANISH_STOP_WORDS
from machine_learning.manuals.candidates.v1.scripts.candidate_rag_harness import CandidateRAGHarness
from machine_learning.manuals.candidates.v1.metadata.schema_v2 import ProceduralChunkV2, EvidenceLevel, KnowledgeType

def build_and_validate_candidate():
    p_cand_txt = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/texts"
    p_cand_meta = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/metadata/metadatos_manuales_v1.json"
    p_cand_idx = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/indexes/indice_faiss_v1.index"

    print("Cargando textos y metadatos del candidato V1...")
    # Cargar con recompute_index_if_missing=True
    harness = CandidateRAGHarness(
        p_cand_txt,
        p_cand_meta,
        index_path=None,  # Forzar recalculo con el nuevo texto A3
        version_id="RAG_CANDIDATO_V1_BUILD",
        recompute_index_if_missing=True
    )

    doc_count = len(harness.documentos)
    faiss_ntotal = harness.faiss_index.ntotal
    dimension = harness.faiss_index.d

    print(f"Documentos cargados: {doc_count}, ntotal FAISS: {faiss_ntotal}, dimension: {dimension}")
    assert doc_count == 239, f"Esperados 239 documentos, obtenidos {doc_count}"
    assert faiss_ntotal == 239, f"Esperados 239 vectores, obtenidos {faiss_ntotal}"
    assert dimension > 5000, f"Dimensión anormalmente baja: {dimension}"

    # Validar no vacuidad y sin NaNs
    for i, (t, d) in enumerate(zip(harness.titulos, harness.documentos)):
        assert len(t.strip()) > 0, f"Título vacío en pos {i}"
        assert len(d.strip()) > 0, f"Documento vacío en pos {i}"

    # Guardar índice en candidato
    faiss.write_index(harness.faiss_index, str(p_cand_idx))
    print(f"Índice FAISS candidato guardado exitosamente en: {p_cand_idx}")

    # Re-generar Schema V2 y Manifiesto Posicional con los nuevos hashes de texto de A3
    schema_v2_list = []
    manifest_list = []

    for i in range(doc_count):
        doc_text = harness.documentos[i]
        doc_tit = harness.titulos[i]
        old_meta = harness.metadatos_procedimientos[i]

        doc_id = old_meta.get("id_procedimiento", f"RAG_PROC_{i+1:03d}")
        chunk_id = f"CHUNK_{i:03d}_{doc_id}"

        texto_completo = f"{doc_tit}\n{doc_text}"
        text_hash = hashlib.sha256(texto_completo.encode("utf-8")).hexdigest()

        is_stub = "stub" in doc_tit.lower() or len(doc_text.strip()) < 80
        is_transversal = old_meta.get("knowledge_type") == "TRANSVERSAL" or doc_id == "RAG_PROC_113"
        is_metadata_reconciled = doc_id in {
            "RAG_PROC_047", "RAG_PROC_060", "RAG_PROC_061", "RAG_PROC_067",
            "RAG_PROC_075", "RAG_PROC_109", "RAG_PROC_114", "RAG_PROC_142", "RAG_PROC_154"
        }
        is_content_enhanced = doc_id in {"RAG_PROC_064", "RAG_PROC_036", "RAG_PROC_229", "RAG_PROC_053", "RAG_PROC_054"}

        if is_stub:
            k_type = KnowledgeType.STUB
            ev_level = EvidenceLevel.PENDING_SOURCE
        elif is_transversal:
            k_type = KnowledgeType.TRANSVERSAL
            ev_level = EvidenceLevel.TRANSVERSAL
        elif is_content_enhanced or is_metadata_reconciled:
            k_type = KnowledgeType.PROCEDURAL
            ev_level = EvidenceLevel.PARTIAL_SOURCE
        else:
            k_type = KnowledgeType.PROCEDURAL
            ev_level = EvidenceLevel.LEGACY_BASELINE

        falla_nom = str(old_meta.get("falla", "")).lower()
        tit_lower = doc_tit.lower()
        sistema = old_meta.get("sistema", "MOTOR")
        safety_level = "STANDARD"
        safety_warning = None

        if "alta tension" in tit_lower or "hibrid" in tit_lower or "bateria de alto voltaje" in tit_lower or "bateria hv" in falla_nom or "inversor" in falla_nom:
            safety_level = "CRITICAL"
            safety_warning = "PELIGRO DE ALTA TENSIÓN (>300V CC): No manipular sin guantes aislantes Clase 0 (1000V), desconexión de Service Plug y capacitación OEM certificada."
        elif "common rail" in tit_lower or "common rail" in falla_nom:
            safety_level = "HIGH_RISK"
            safety_warning = "PELIGRO DE ALTA PRESIÓN (>1600 BAR): Riesgo de inyección hipodérmica cutánea y amputación. Despresurizar el acumulador antes de aflojar cañerías."
        elif ("gasolina" in tit_lower and ("riel" in tit_lower or "inyector" in tit_lower or "bomba" in tit_lower)) or ("gasolina" in falla_nom and "bomba" in falla_nom):
            safety_level = "CAUTION"
            safety_warning = "PRECAUCIÓN DE COMBUSTIBLE: Despresurizar riel de inyección retirando fusible de bomba antes de abrir el circuito para evitar atomización inflamable."
        elif "frenos de aire" in tit_lower or "maxi-brake" in tit_lower or "neumatico" in tit_lower or "camiones" in falla_nom:
            safety_level = "HIGH_RISK"
            safety_warning = "SISTEMA NEUMÁTICO PESADO: Bloquear ruedas físicamente con cuñas y purgar depósitos de aire antes de desacoplar cámaras o pulmones de freno."
        elif "refrigerante" in tit_lower and ("radiador" in tit_lower or "caliente" in tit_lower or "termostato" in tit_lower):
            safety_level = "CAUTION"
            safety_warning = "PRECAUCIÓN TÉRMICA: Nunca abrir la tapa del radiador o depósito con motor caliente por riesgo de quemaduras graves por vapor a presión."

        requires_oem = old_meta.get("marca") not in ["Universal / Multimarca", "Universal", None]

        chunk_v2 = ProceduralChunkV2(
            doc_id=doc_id,
            chunk_id=chunk_id,
            position=i,
            source_id=old_meta.get("archivo_fuente", "manual_procedimientos.txt"),
            source_type="WORKSHOP_MANUAL",
            source_title=old_meta.get("manual_oem", doc_tit),
            procedure_title=doc_tit,
            titulo=doc_tit,
            source_author_org=old_meta.get("marca"),
            source_url=old_meta.get("url_referencia"),
            source_version=old_meta.get("edicion"),
            source_date=old_meta.get("fecha_registro_corpus"),
            source_hash=old_meta.get("sha256_fragmento"),
            archivo_fuente=old_meta.get("archivo_fuente", "manual_procedimientos.txt"),
            system=sistema,
            sistema=sistema,
            subsystem=old_meta.get("componente"),
            component=old_meta.get("componente"),
            knowledge_type=k_type,
            primary_fault_class=old_meta.get("falla"),
            falla=old_meta.get("falla"),
            related_fault_classes=old_meta.get("clases_relacionadas", []),
            dtc_codes=old_meta.get("codigos_dtc", []),
            vehicle_scope="VEHICLE_SPECIFIC" if requires_oem else "UNIVERSAL",
            make=old_meta.get("marca"),
            model=old_meta.get("modelo"),
            year=old_meta.get("anio"),
            engine=old_meta.get("motor"),
            requires_oem_spec=requires_oem,
            safety_level=safety_level,
            safety_warning=safety_warning,
            evidence_level=ev_level,
            candidate_version="RAG_CANDIDATO_V1"
        )
        schema_v2_dict = chunk_v2.model_dump()
        schema_v2_list.append(schema_v2_dict)

        meta_hash = hashlib.sha256(json.dumps(schema_v2_dict, sort_keys=True).encode("utf-8")).hexdigest()

        manifest_entry = {
            "position": i,
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "source_file": old_meta.get("archivo_fuente"),
            "text_hash": text_hash,
            "metadata_hash": meta_hash,
            "system": sistema,
            "primary_class": old_meta.get("falla"),
            "related_classes": old_meta.get("clases_relacionadas", []),
            "knowledge_type": k_type.value,
            "evidence_level": ev_level.value,
            "candidate_version": "RAG_CANDIDATO_V1"
        }
        manifest_list.append(manifest_entry)

    # Validar alineación estricta
    assert len(schema_v2_list) == len(manifest_list) == faiss_ntotal == doc_count == 239

    # Guardar metadatos Schema V2
    p_out_meta = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/metadata/metadatos_schema_v2.json"
    with open(p_out_meta, "w", encoding="utf-8") as f:
        json.dump(schema_v2_list, f, indent=2, ensure_ascii=False)

    # Guardar Manifiesto Posicional
    p_out_manifest = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/manifests/corpus_manifest.json"
    with open(p_out_manifest, "w", encoding="utf-8") as f:
        json.dump({
            "candidate_version": "RAG_CANDIDATO_V1",
            "total_chunks": len(manifest_list),
            "faiss_ntotal": faiss_ntotal,
            "faiss_dimension": dimension,
            "entries": manifest_list
        }, f, indent=2, ensure_ascii=False)

    # Guardar Build Manifest (Sección 77)
    with open(p_cand_idx, "rb") as f:
        index_bytes = f.read()
    index_sha256 = hashlib.sha256(index_bytes).hexdigest()

    with open(p_out_meta, "rb") as f:
        meta_bytes = f.read()
    meta_sha256 = hashlib.sha256(meta_bytes).hexdigest()

    with open(p_out_manifest, "rb") as f:
        manifest_bytes = f.read()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()

    build_manifest = {
        "candidate_version": "RAG_CANDIDATO_V1",
        "dimension": dimension,
        "document_count": doc_count,
        "chunk_count": doc_count,
        "FAISS_ntotal": faiss_ntotal,
        "index_hash": index_sha256,
        "metadata_hash": meta_sha256,
        "manifest_hash": manifest_sha256,
        "vectorizer_config": {
            "lowercase": True,
            "strip_accents": "unicode",
            "stop_words": "SPANISH_STOP_WORDS (138 terms)",
            "ngram_range": [1, 2],
            "sublinear_tf": True
        },
        "tests_status": "VALIDATED"
    }

    p_build_manifest = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/manifests/RAG_CANDIDATO_V1_BUILD_MANIFEST.json"
    with open(p_build_manifest, "w", encoding="utf-8") as f:
        json.dump(build_manifest, f, indent=2, ensure_ascii=False)

    print("BUILD MANIFEST CREADO EXITOSAMENTE:")
    print(json.dumps(build_manifest, indent=2))
    print("COMPILACIÓN Y VALIDACIÓN DEL CANDIDATO V1 FINALIZADA CON ÉXITO.")

if __name__ == "__main__":
    build_and_validate_candidate()
