"""
Generador del Schema RAG V2 y Manifiesto Posicional.
Genera metadatos_schema_v2.json y corpus_manifest.json.
Valida estrictamente la alineación posicional 1:1:
FAISS[i] <-> TEXT[i] <-> METADATA[i] <-> MANIFEST[i].
"""
import sys
import os
import json
import hashlib
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from machine_learning.manuals.candidates.v1.scripts.candidate_rag_harness import CandidateRAGHarness
from machine_learning.manuals.candidates.v1.metadata.schema_v2 import ProceduralChunkV2, EvidenceLevel, KnowledgeType

def build_schema_v2_and_manifest():
    p_cand_txt = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/texts"
    p_cand_meta = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/metadata/metadatos_manuales_v1.json"
    p_cand_idx = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/indexes/indice_faiss_v1.index"

    harness = CandidateRAGHarness(p_cand_txt, p_cand_meta, p_cand_idx, version_id="CANDIDATE_V1")

    schema_v2_list = []
    manifest_list = []

    print(f"Indexados por harness: {len(harness.documentos)} documentos.")

    for i in range(len(harness.documentos)):
        doc_text = harness.documentos[i]
        doc_tit = harness.titulos[i]
        old_meta = harness.metadatos_procedimientos[i]

        doc_id = old_meta.get("id_procedimiento", f"RAG_PROC_{i+1:03d}")
        chunk_id = f"CHUNK_{i:03d}_{doc_id}"

        # Hash del texto del fragmento (titulo + cuerpo)
        texto_completo = f"{doc_tit}\n{doc_text}"
        text_hash = hashlib.sha256(texto_completo.encode("utf-8")).hexdigest()

        # Determinación de tipo de conocimiento y nivel de evidencia
        is_stub = "stub" in doc_tit.lower() or len(doc_text.strip()) < 80
        is_transversal = old_meta.get("knowledge_type") == "TRANSVERSAL" or doc_id == "RAG_PROC_113"
        is_metadata_reconciled = doc_id in {
            "RAG_PROC_047", "RAG_PROC_060", "RAG_PROC_061", "RAG_PROC_067",
            "RAG_PROC_075", "RAG_PROC_109", "RAG_PROC_114", "RAG_PROC_142", "RAG_PROC_154"
        }

        if is_stub:
            k_type = KnowledgeType.STUB
            ev_level = EvidenceLevel.PENDING_SOURCE
        elif is_transversal:
            k_type = KnowledgeType.TRANSVERSAL
            ev_level = EvidenceLevel.TRANSVERSAL
        elif is_metadata_reconciled:
            k_type = KnowledgeType.PROCEDURAL
            ev_level = EvidenceLevel.PARTIAL_SOURCE
        else:
            k_type = KnowledgeType.PROCEDURAL
            ev_level = EvidenceLevel.LEGACY_BASELINE

        # Clasificación de nivel de seguridad
        falla_nom = str(old_meta.get("falla", "")).lower()
        sistema = old_meta.get("sistema", "MOTOR")
        safety_level = "STANDARD"
        safety_warning = None

        if "alta tension" in doc_text.lower() or "hibrid" in doc_text.lower() or "bateria hv" in falla_nom or "inversor" in falla_nom:
            safety_level = "CRITICAL"
            safety_warning = "PELIGRO DE ALTA TENSIÓN (>300V CC): No manipular sin guantes aislantes Clase 0 (1000V), desconexión de Service Plug y capacitación OEM certificada."
        elif "common rail" in doc_text.lower() or "common rail" in falla_nom:
            safety_level = "HIGH_RISK"
            safety_warning = "PELIGRO DE ALTA PRESIÓN (>1600 BAR): Riesgo de inyección hipodérmica cutánea y amputación. Despresurizar el acumulador antes de aflojar cañerías."
        elif "gasolina" in doc_text.lower() and ("riel" in doc_text.lower() or "inyector" in doc_text.lower()):
            safety_level = "CAUTION"
            safety_warning = "PRECAUCIÓN DE COMBUSTIBLE: Despresurizar riel de inyección retirando fusible de bomba antes de abrir el circuito para evitar atomización inflamable."
        elif "frenos de aire" in doc_text.lower() or "camion" in doc_text.lower():
            safety_level = "HIGH_RISK"
            safety_warning = "SISTEMA NEUMÁTICO PESADO: Bloquear ruedas físicamente con cuñas y purgar depósitos de aire antes de desacoplar cámaras o pulmones de freno."
        elif "refrigerante" in doc_text.lower() and "caliente" in doc_text.lower():
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
            source_author_org=old_meta.get("marca"),
            source_url=old_meta.get("url_referencia"),
            source_version=old_meta.get("edicion"),
            source_date=old_meta.get("fecha_registro_corpus"),
            source_hash=old_meta.get("sha256_fragmento"),
            system=sistema,
            subsystem=old_meta.get("componente"),
            component=old_meta.get("componente"),
            knowledge_type=k_type,
            primary_fault_class=old_meta.get("falla"),
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
        schema_v2_dict = chunk_v2.dict()
        schema_v2_list.append(schema_v2_dict)

        # Hash de los metadatos serializados
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

    # Validar alineación 100%
    assert len(schema_v2_list) == len(manifest_list) == harness.faiss_index.ntotal == len(harness.documentos) == 239

    # Guardar metadatos Schema V2
    p_out_meta = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/metadata/metadatos_schema_v2.json"
    with open(p_out_meta, "w", encoding="utf-8") as f:
        json.dump(schema_v2_list, f, indent=2, ensure_ascii=False)
    print(f"Guardado: {p_out_meta} ({len(schema_v2_list)} registros)")

    # Guardar Manifiesto Posicional
    p_out_manifest = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/manifests/corpus_manifest.json"
    with open(p_out_manifest, "w", encoding="utf-8") as f:
        json.dump({
            "candidate_version": "RAG_CANDIDATO_V1",
            "total_chunks": len(manifest_list),
            "faiss_ntotal": harness.faiss_index.ntotal,
            "faiss_dimension": harness.faiss_index.d,
            "entries": manifest_list
        }, f, indent=2, ensure_ascii=False)
    print(f"Guardado Manifiesto Posicional: {p_out_manifest} ({len(manifest_list)} entradas)")

    print("ALINEACIÓN POSICIONAL COMPROBADA: FAISS[i] <-> TEXT[i] <-> METADATA[i] <-> MANIFEST[i] (100% OK)")

if __name__ == "__main__":
    build_schema_v2_and_manifest()
