"""
Test de prevención de contaminación semántica cruzada (Sección 63).
Verifica que las correcciones de metadata no generen falsos bonos de relevancia
en consultas cruzadas.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from machine_learning.manuals.candidates.v1.scripts.candidate_rag_harness import CandidateRAGHarness

def test_contamination():
    p_cand_txt = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/texts"
    p_cand_meta = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/metadata/metadatos_manuales_v1.json"
    p_cand_idx = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/indexes/indice_faiss_v1.index"

    harness = CandidateRAGHarness(p_cand_txt, p_cand_meta, p_cand_idx, version_id="CANDIDATE_CONTAMINATION")

    # 1. Consulta misfire NO debe rankear TPMS en top 3
    res_misfire = harness.recuperar_procedimiento(
        consulta="falla de encendido cascabeleo bujias cilindro 1 misfire",
        macro_sistema="MOTOR",
        top_fallas=[{"falla": "Falla en bujias o bobinas de encendido (misfire)", "probabilidad": 0.85}],
        k_candidatos=5
    )
    for r in res_misfire[:3]:
        assert "TPMS" not in r["titulo"], "Contaminación: TPMS apareció en top 3 de misfire!"

    # 2. Consulta starter NO debe rankear VVT en top 3
    res_starter = harness.recuperar_procedimiento(
        consulta="no da arranque solo se escucha un clac seco solenoide de marcha",
        macro_sistema="ELECTRICO",
        top_fallas=[{"falla": "Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)", "probabilidad": 0.90}],
        k_candidatos=5
    )
    for r in res_starter[:3]:
        assert "VVT" not in r["titulo"] and "OCV" not in r["titulo"], "Contaminación: VVT apareció en top 3 de arranque!"

    # 3. Consulta clutch manual NO debe rankear compresor A/C en top 3
    res_clutch = harness.recuperar_procedimiento(
        consulta="embrague patina pedal alto aceleras y no avanza disco gastado",
        macro_sistema="TRANSMISION",
        top_fallas=[{"falla": "Disco de embrague desgastado o patinando", "probabilidad": 0.88}],
        k_candidatos=5
    )
    for r in res_clutch[:3]:
        assert "ELECTROMAGN" not in r["titulo"], "Contaminación: Clutch de A/C apareció en top 3 de embrague manual!"

    # 4. Consulta A/C NO debe rankear disco de embrague manual en top 3
    res_ac = harness.recuperar_procedimiento(
        consulta="aire acondicionado no enfria sale caliente compresor no acopla gas r134a",
        macro_sistema="CLIMATIZACION",
        top_fallas=[{"falla": "Falla en compresor de aire acondicionado o fuga de gas R134a", "probabilidad": 0.92}],
        k_candidatos=5
    )
    for r in res_ac[:3]:
        assert "DISCO DE EMBRAGUE" not in r["titulo"] and "MECATR" not in r["titulo"], "Contaminación: Transmisión apareció en top 3 de A/C!"

    # 5. Consulta EVAP NO debe favorecer misfire
    res_evap = harness.recuperar_procedimiento(
        consulta="olor a gasolina canister valvula de purga codigo p0440 p0442",
        macro_sistema="MOTOR",
        top_fallas=[{"falla": "Falla en sistema de control de emisiones evaporativas EVAP (canister o valvula de purga)", "probabilidad": 0.89}],
        k_candidatos=5
    )
    # Debe priorizar procedimientos EVAP
    assert any("EVAP" in r["titulo"] or "PURGA" in r["titulo"] for r in res_evap[:2]), "EVAP no fue priorizado en consulta de emisiones evaporativas"

    print("TEST DE NO CONTAMINACIÓN: TODOS LOS CASOS PASARON SATISFACTORIAMENTE (5/5)!")

if __name__ == "__main__":
    test_contamination()
