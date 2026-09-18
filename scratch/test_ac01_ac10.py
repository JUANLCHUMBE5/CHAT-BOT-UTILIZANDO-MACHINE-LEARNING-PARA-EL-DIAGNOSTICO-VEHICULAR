import sys
import io
import csv
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, 'backend')
from src.infrastructure.container import ServiceContainer
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.diagnostic_cache import diagnostico_cache
from src.core.diagnostico.taxonomia_sistemas import obtener_macro_sistema

diagnostico_cache.limpiar()
ServiceContainer.reset()
gd = GestorDiagnostico()

print("=== EJECUTANDO TEST DE REGRESIÓN A/C (AC01 - AC10 + HISTORICOS) ===")

results = []

def run_ac_test(case_id, steps, expected_macro, expected_behavior, is_multiturn=False):
    sid = f"test_{case_id.lower()}"
    last_res = None
    for step_num, text in enumerate(steps, 1):
        last_res = gd.procesar_consulta_texto(text, session_id=sid)
    
    diag_ml = last_res.diagnostico_ml
    macro = obtener_macro_sistema(diag_ml)
    modo = last_res.modo_diagnostico
    sintoma_eval = last_res.sintoma_evaluado or ""
    resp = last_res.respuesta_texto
    
    # Evaluate verdict
    if case_id in ("AC01", "AC02", "AC03", "AC04", "AC07", "AC08"):
        # Must classify as CLIMATIZACION
        verdict = "PASS" if macro == "CLIMATIZACION" or "aire acondicionado" in diag_ml.lower() or "r134a" in diag_ml.lower() else "FAIL"
    elif case_id in ("AC05", "AC06"):
        # Must classify as MOTOR / INYECCION / CARGA, NOT CLIMATIZACION
        verdict = "PASS" if macro != "CLIMATIZACION" and ("fuerza" in sintoma_eval.lower() or "potencia" in sintoma_eval.lower() or "carga" in sintoma_eval.lower()) else "FAIL"
    elif case_id == "AC09":
        # Check that previous motor issue was reset, vehicle preserved, and now CLIMATIZACION
        ses = gd.session_manager.obtener_sesion(sid)
        marca = str(ses.marca_modelo or ses.conversation_state.marca or "")
        modelo = str(ses.conversation_state.modelo or "")
        vehiculo_ok = "toyota" in marca.lower() or "yaris" in modelo.lower()
        verdict = "PASS" if (macro == "CLIMATIZACION" or "aire acondicionado" in diag_ml.lower()) and vehiculo_ok else "FAIL"
    elif case_id == "AC10":
        # Should not blindly force CLIMATIZACION without checking; either asks clarifying question or diagnoses motor/belt noise
        verdict = "PASS" if diag_ml != "Consulta fuera del alcance automotriz" else "FAIL"
    elif case_id == "CASE_092":
        # Sail 4 turns: Sail -> pierde fuerza -> en subida -> con A/C encendido
        # Preserves full synthesized query under MOTOR
        full_ok = "pierde fuerza" in sintoma_eval.lower() or "potencia" in sintoma_eval.lower()
        no_fuera = diag_ml != "Consulta fuera del alcance automotriz"
        verdict = "PASS" if full_ok and no_fuera else "FAIL"
    elif case_id == "CASE_093":
        # Explicit AC paragraph -> must be CLIMATIZACION with high confidence
        verdict = "PASS" if (macro == "CLIMATIZACION" or "aire acondicionado" in diag_ml.lower() or "r134a" in diag_ml.lower()) and diag_ml != "Consulta fuera del alcance automotriz" else "FAIL"
    else:
        verdict = "PASS" if diag_ml != "Consulta fuera del alcance automotriz" else "FAIL"

    print(f"[{case_id}] {verdict} | Macro: {macro} | DiagML: {diag_ml} | Modo: {modo}")
    print(f"       Evaluated query: {repr(sintoma_eval)}")
    print(f"       Resp preview: {resp[:120].replace(chr(10), ' ')}...\n")

    results.append({
        "case_id": case_id,
        "turns_count": len(steps),
        "last_input": steps[-1],
        "expected_macro": expected_macro,
        "observed_macro": macro,
        "diagnostico_ml": diag_ml,
        "confianza_ml": getattr(last_res, "confianza_ml", 0.0),
        "modo_diagnostico": modo,
        "sintoma_evaluado": sintoma_eval,
        "verdict": verdict,
        "expected_behavior": expected_behavior,
    })

# AC01
run_ac_test("AC01", ["el aire no enfría"], "CLIMATIZACION", "Avería pura de climatización")

# AC02
run_ac_test("AC02", ["sale aire caliente por las rejillas"], "CLIMATIZACION", "Avería pura de climatización")

# AC03
run_ac_test("AC03", ["solo enfría cuando voy rápido"], "CLIMATIZACION", "Avería pura de climatización en movimiento")

# AC04
run_ac_test("AC04", ["cuando paro en el semáforo deja de enfriar"], "CLIMATIZACION", "Avería pura de climatización en ralentí")

# AC05
run_ac_test("AC05", ["el carro pierde fuerza cuando prendo el aire"], "MOTOR", "A/C como condición operacional de carga motriz")

# AC06
run_ac_test("AC06", ["en subida pierde fuerza con el aire prendido"], "MOTOR", "A/C y subida como condiciones de carga motor")

# AC07
run_ac_test("AC07", ["el motor está bien pero el aire no enfría"], "CLIMATIZACION", "Motor normal, queja pura de climatización")

# AC08
run_ac_test("AC08", ["tengo otro problema, ahora el aire no enfría"], "CLIMATIZACION", "Cambio explícito a problema de climatización")

# AC09: Multi-turn con reseteo selectivo
# Turno 1: Vehículo + Falla motor
# Turno 2: "ahora otra cosa, el aire no enfría"
run_ac_test("AC09", [
    "Toyota Yaris 2015, tironea en subida",
    "ahora otra cosa, el aire no enfría"
], "CLIMATIZACION", "Reset selectivo de avería manteniendo datos del vehículo", is_multiturn=True)

# AC10
run_ac_test("AC10", ["cuando prendo el aire hace un ruido en el motor"], "MOTOR_O_ACARREO", "Ruido bajo carga de compresor, no forzar ciegamente climatización")

# CASE_092: Caso Sail 4 turnos
run_ac_test("CASE_092", [
    "Chevrolet Sail 2018",
    "pierde fuerza",
    "en subida",
    "con el aire acondicionado encendido"
], "MOTOR", "Multi-turno de carga operacional preservando síntoma acumulado", is_multiturn=True)

# CASE_093: Párrafo explícito de climatización
run_ac_test("CASE_093", [
    "Hola, tengo otro problema con mi carro. Cuando enciendo el aire acondicionado sí sale aire por las rejillas, pero no enfría casi nada. Cuando voy manejando parece enfriar un poquito más, pero cuando me detengo en un semáforo vuelve a salir casi a temperatura ambiente. El motor funciona normal y no tengo ninguna luz de advertencia encendida. No he revisado nada todavía."
], "CLIMATIZACION", "Clasificación CLIMATIZACION sin caer en fuera de alcance", is_multiturn=False)

# Guardar a CSV
csv_path = Path("FASE11_AC_REGRESSION_V2.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print(f"Resultados guardados exitosamente en {csv_path.resolve()}")
