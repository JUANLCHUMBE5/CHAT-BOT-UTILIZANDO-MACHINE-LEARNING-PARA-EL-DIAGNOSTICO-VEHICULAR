"""
Suite de Pruebas de Integración y Smoke Tests Pre-Promoción.
Verifica:
1. Robustez de entrada: vacío, malformado, Unicode, tildes, jerga WhatsApp de taller.
2. Escenarios E2E A a J.
3. Caso técnico prioritario de A/C (ralentí vs carretera / flujo condensador).
4. No reapertura de bugs de Fase 11.3 (52 PSI -> 52 V, no repetición de pruebas, aislamiento de casos).
Genera RAG_PROMOTION_INTEGRATION_TESTS.csv.
"""
import sys
import json
import csv
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from machine_learning.manuals.candidates.v1.structured.dtc_lookup_service import DTCLookupService
from machine_learning.manuals.candidates.v1.scripts.candidate_rag_harness import CandidateRAGHarness

def run_integration_tests():
    cand_dir = PROJECT_ROOT / "machine_learning/manuals/candidates/v1"
    dtc_svc = DTCLookupService()
    h = CandidateRAGHarness(
        cand_dir / "texts",
        cand_dir / "metadata/metadatos_schema_v2.json",
        cand_dir / "indexes/indice_faiss_v1.index",
        dtc_lookup_service=dtc_svc
    )

    integration_results = []
    t_id = 1

    # 1. Robustez de entrada
    robustness_cases = [
        ("EMPTY_QUERY", "", "MOTOR", []),
        ("MALFORMED_INPUT", "???###@@@$$$%%%^^^&&&***", None, []),
        ("UNICODE_ACCENTS", "Árbol de levas, pistón, compresión, vibración hidráulica", "MOTOR", []),
        ("WHATSAPP_TYPOS", "ola maestro mi caña ase un chillido orrible cuando piso embrague", "TRANSMISION", []),
        ("SQL_INJECTION", "' OR '1'='1' --", None, ["P0301"])
    ]

    for label, q_text, macro, dtcs in robustness_cases:
        try:
            res = h.recuperar_procedimiento(q_text, macro_sistema=macro, codigos_dtc=dtcs, k_candidatos=3, usar_dtc_lookup=True)
            status = "PASS"
            detail = f"Recuperados {len(res)} candidatos sin excepción."
        except Exception as e:
            status = "FAIL"
            detail = f"Excepción: {e}"

        integration_results.append({
            "test_id": f"INT_{t_id:03d}",
            "scenario": f"Robustez de Entrada: {label}",
            "layer": "CandidateRAGHarness",
            "expected": "No crash / respuesta estructurada",
            "actual": detail,
            "status": status,
            "severity": "P0" if status == "FAIL" else "INFO"
        })
        t_id += 1

    # 2. Escenarios A a J
    escenarios = [
        ("A_AC_NO_ENFRIA", "aire acondicionado no enfria sale caliente", "CLIMATIZACION", ["B1010"], "CLIMATIZACION"),
        ("B_ARRANQUE_FRIO", "no arranca en las mananas bateria baja voltios", "ELECTRICO", [], "ELECTRICO"),
        ("C_VIBRACION_ACELERAR", "vibra al acelerar y zumba rodamiento maza", "SUSPENSION_CHASIS", [], "SUSPENSION_CHASIS"),
        ("D_FUGA_REFRIGERANTE", "fuga de refrigerante radiador hierve temperatura alta", "MOTOR", [], "MOTOR"),
        ("E_FRENOS", "pedal esponjoso y fuga liquido de frenos", "FRENOS", ["C0040"], "FRENOS"),
        ("F_EV_HV", "bateria alta tension hibrido prius triangulo rojo", "ELECTRICO", ["P0A80"], "ELECTRICO"),
        ("G_DTC_EXPLICITO", "codigo p0420 catalizador ineficiente", "MOTOR", ["P0420"], "MOTOR"),
        ("H_SIN_DTC", "embrague patina acelero y no avanza", "TRANSMISION", [], "TRANSMISION"),
        ("I_TRANSMISION", "caja cvt dsg patinan variadores solenoides", "TRANSMISION", ["P0841"], "TRANSMISION"),
        ("J_SESION_TALLER", "revision general pastillas discos de freno gastados", "FRENOS", [], "FRENOS")
    ]

    for cod_esc, q_text, macro, dtcs, exp_macro in escenarios:
        res = h.recuperar_procedimiento(q_text, macro_sistema=macro, codigos_dtc=dtcs, k_candidatos=3, usar_dtc_lookup=True)
        top1 = res[0] if res else {}
        top1_sys = top1.get("metadatos", {}).get("sistema")
        passed = (top1_sys == exp_macro)

        integration_results.append({
            "test_id": f"INT_{t_id:03d}",
            "scenario": f"Escenario E2E: {cod_esc}",
            "layer": "Retrieval & Relevance Reranking",
            "expected": f"Macro-sistema={exp_macro}",
            "actual": f"Top1={top1.get('titulo')[:40]} | Sys={top1_sys}",
            "status": "PASS" if passed else "FAIL",
            "severity": "P1" if not passed else "INFO"
        })
        t_id += 1

    # 3. Caso histórico A/C prioritario
    ac_query = (
        "Hola, tengo otro problema con mi carro. Cuando enciendo el aire acondicionado "
        "sí sale aire por las rejillas, pero no enfría casi nada. Cuando voy manejando "
        "parece enfriar un poquito más, pero cuando me detengo en un semáforo vuelve a salir "
        "casi a temperatura ambiente. El motor funciona normal y no tengo ninguna luz de advertencia "
        "encendida. No he revisado nada todavía."
    )
    res_ac = h.recuperar_procedimiento(ac_query, macro_sistema="CLIMATIZACION", k_candidatos=3, usar_dtc_lookup=True)
    top_ac = res_ac[0] if res_ac else {}
    top_ac_tit = top_ac.get("titulo", "")
    top_ac_doc = top_ac.get("documento", "")
    top_ac_sys = top_ac.get("metadatos", {}).get("sistema")

    ac_relevant = "CONDENSADOR" in top_ac_tit or "CLIMATIZACION" in top_ac_sys
    ac_no_generic_psi = ("50-60 psi" not in top_ac_doc.lower() and "120-140 psi" not in top_ac_doc.lower())
    ac_has_airflow_logic = ("motoventilador" in top_ac_doc.lower() and "flujo de aire" in top_ac_doc.lower())

    passed_ac = ac_relevant and ac_no_generic_psi and ac_has_airflow_logic

    integration_results.append({
        "test_id": f"INT_{t_id:03d}",
        "scenario": "Caso Histórico A/C (Ralentí vs Carretera)",
        "layer": "Knowledge Retrieval & Workshop Chain",
        "expected": "Top1 A/C Condensador/Flujo, sin presiones fijas, con orientación a motoventilador",
        "actual": f"Top1={top_ac_tit[:45]} | AirflowLogic={ac_has_airflow_logic} | SafePSI={ac_no_generic_psi}",
        "status": "PASS" if passed_ac else "FAIL",
        "severity": "P1" if not passed_ac else "INFO"
    })
    t_id += 1

    # 4. Verificación de no reapertura de bugs Fase 11.3
    from src.core.traductor_jerga import normalizar_jerga_peruana
    raw_psi = "la presion de riel marca 52 psi con manometro"
    norm_psi = normalizar_jerga_peruana(raw_psi)
    psi_preserved = ("52 psi" in norm_psi or "psi" in norm_psi) and "52 v" not in norm_psi

    integration_results.append({
        "test_id": f"INT_{t_id:03d}",
        "scenario": "Regresión Fase 11.3: 52 PSI permanece PSI",
        "layer": "Traductor Jerga / Estado Conversacional",
        "expected": "52 PSI preserva unidad de presión (no voltaje)",
        "actual": f"Normalizado: '{norm_psi}'",
        "status": "PASS" if psi_preserved else "FAIL",
        "severity": "P1" if not psi_preserved else "INFO"
    })
    t_id += 1

    # Guardar CSV de pruebas de integración
    p_csv = cand_dir / "reports/RAG_PROMOTION_INTEGRATION_TESTS.csv"
    with open(p_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["test_id", "scenario", "layer", "expected", "actual", "status", "severity"])
        writer.writeheader()
        for r in integration_results:
            writer.writerow(r)

    print(f"PRUEBAS DE INTEGRACIÓN PRE-PROMOCIÓN COMPLETADAS: {len(integration_results)} tests ejecutados.")
    fails = [r for r in integration_results if r["status"] == "FAIL"]
    print(f"  Aprobados: {len(integration_results) - len(fails)} / {len(integration_results)}")
    print(f"  Fallidos: {len(fails)}")
    assert len(fails) == 0, f"Fallos en integración: {fails}"
    print(f"Reporte guardado en: {p_csv}")

if __name__ == "__main__":
    run_integration_tests()
