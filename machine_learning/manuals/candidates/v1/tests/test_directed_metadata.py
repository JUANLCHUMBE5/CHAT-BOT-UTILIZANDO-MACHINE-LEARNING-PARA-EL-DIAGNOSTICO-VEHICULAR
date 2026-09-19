"""
Test dirigido para validar la corrección de metadatos (CHG-001 a CHG-010).
Verifica que las 10 correcciones se reflejen en la metadata del candidato
y que los filtros de relevancia no asocien erróneamente estos procedimientos
con starter, embrague manual o misfire.
"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from machine_learning.manuals.candidates.v1.scripts.candidate_rag_harness import CandidateRAGHarness

def test_directed_metadata():
    p_cand_txt = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/texts"
    p_cand_meta = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/metadata/metadatos_manuales_v1.json"
    p_cand_idx = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/indexes/indice_faiss_v1.index"

    harness = CandidateRAGHarness(p_cand_txt, p_cand_meta, p_cand_idx, version_id="A1_METADATA")

    # Mapeo rápido de procedimientos por id
    proc_map = {m["id_procedimiento"]: m for m in harness.metadatos_procedimientos}

    # 1. VVT != starter
    for pid in ["RAG_PROC_047", "RAG_PROC_067", "RAG_PROC_142"]:
        item = proc_map[pid]
        assert item["sistema"] == "MOTOR", f"{pid} sistema debe ser MOTOR, es {item['sistema']}"
        assert "sincronizacion variable" in item["falla"], f"{pid} falla incorrecta: {item['falla']}"
        assert "arranque" not in item["falla"].lower(), f"{pid} contiene 'arranque' en falla"

    # 2. A/C compressor clutch != manual clutch
    item_ac = proc_map["RAG_PROC_060"]
    assert item_ac["sistema"] == "CLIMATIZACION", f"RAG_PROC_060 sistema debe ser CLIMATIZACION, es {item_ac['sistema']}"
    assert "aire acondicionado" in item_ac["falla"].lower(), f"RAG_PROC_060 falla incorrecta: {item_ac['falla']}"
    assert "disco de embrague" not in item_ac["falla"].lower(), "RAG_PROC_060 asociado a disco de embrague"

    # 3. EVAP != misfire
    for pid in ["RAG_PROC_075", "RAG_PROC_109", "RAG_PROC_154"]:
        item = proc_map[pid]
        assert item["sistema"] == "MOTOR", f"{pid} sistema debe ser MOTOR, es {item['sistema']}"
        assert "evap" in item["falla"].lower() or "emisiones evaporativas" in item["falla"].lower(), f"{pid} falla incorrecta: {item['falla']}"
        assert "misfire" not in item["falla"].lower() and "bujias" not in item["falla"].lower(), f"{pid} asociado a misfire"

    # 4. TPMS != misfire
    item_tpms = proc_map["RAG_PROC_113"]
    assert item_tpms["sistema"] == "SUSPENSION_CHASIS", f"RAG_PROC_113 sistema debe ser SUSPENSION_CHASIS, es {item_tpms['sistema']}"
    assert item_tpms.get("knowledge_type") == "TRANSVERSAL"
    assert item_tpms.get("falla") is None or "misfire" not in str(item_tpms.get("falla")).lower()

    # 5. TCC != manual clutch
    item_tcc = proc_map["RAG_PROC_114"]
    assert item_tcc["sistema"] == "TRANSMISION"
    assert "cvt / dsg" in item_tcc["falla"].lower() or "caja automatica" in item_tcc["falla"].lower()
    assert "disco de embrague desgastado" not in item_tcc["falla"].lower()

    # 6. DSG != manual clutch
    item_dsg = proc_map["RAG_PROC_061"]
    assert item_dsg["sistema"] == "TRANSMISION"
    assert "cvt / dsg" in item_dsg["falla"].lower()
    assert "disco de embrague desgastado" not in item_dsg["falla"].lower()

    print("TEST DIRIGIDO DE METADATOS: TODOS LOS CASOS PASARON SATISFACTORIAMENTE (10/10)!")

if __name__ == "__main__":
    test_directed_metadata()
