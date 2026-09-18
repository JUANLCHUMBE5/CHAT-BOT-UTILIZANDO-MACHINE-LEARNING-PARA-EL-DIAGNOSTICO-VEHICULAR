import sys
import io
import csv
import json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, 'backend')
from src.infrastructure.container import ServiceContainer
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.diagnostic_cache import diagnostico_cache

diagnostico_cache.limpiar()
ServiceContainer.reset()
gd = GestorDiagnostico()

# Load suite to find cases requiring clarification
base_dir = Path(__file__).resolve().parent.parent
suite_path = base_dir / "FASE11_CONVERSATIONAL_SUITE_V1.json"
with open(suite_path, "r", encoding="utf-8") as f:
    suite = json.load(f)

print("=== EJECUTANDO TEST DE AUTO-INTERROGADOR V2 ===")

auto_cases = []
for c in suite:
    cid = c["case_id"]
    cat = c["category"]
    exp = c["expected_behavior"].lower()
    # Cases where the expected behavior is to ask a clarifying question or auto-question
    if "preguntar" in exp or "pedir" in exp or "aclaraci" in exp or "auto-pregunta" in exp or "auto-pregunta técnica" in exp:
        auto_cases.append(c)

print(f"Total casos que requieren pregunta de descarte / aclaración: {len(auto_cases)}")

results = []
correct_count = 0
premature_count = 0
loops_count = 0

for c in auto_cases:
    cid = c["case_id"]
    sid = f"auto_{cid.lower()}"
    turns = c["turns"]
    first_msg = turns[0]["user_message"]
    
    res = gd.procesar_consulta_texto(first_msg, session_id=sid)
    diag_ml = res.diagnostico_ml
    modo = res.modo_diagnostico
    resp = res.respuesta_texto
    estado_ses = getattr(res, "estado_sesion", "")
    
    es_pregunta = (
        modo in ("esperando_clarificacion", "aclaracion")
        or estado_ses in ("esperando_autopregunta", "esperando_clarificacion")
        or "?" in resp
        or "¿" in resp
        or "1️⃣" in resp
    )
    
    # Check if premature
    if not es_pregunta and modo in ("completo_ml_rag_llm", "diagnostico_degradado_ml_rag"):
        premature = True
        verdict = "FAIL_PREMATURE"
        premature_count += 1
    elif es_pregunta:
        premature = False
        verdict = "PASS"
        correct_count += 1
    else:
        premature = False
        verdict = "PASS"
        correct_count += 1

    print(f"[{cid}] {verdict} | Modo: {modo} | Ses: {estado_ses} | Premature: {premature}")
    print(f"       Query: {repr(first_msg)}")
    print(f"       Resp: {resp[:120].replace(chr(10), ' ')}...\n")
    
    results.append({
        "case_id": cid,
        "query": first_msg,
        "expected_behavior": c["expected_behavior"],
        "modo_diagnostico": modo,
        "estado_sesion": estado_ses,
        "diagnostico_ml": diag_ml,
        "es_pregunta_correcta": es_pregunta,
        "diagnostico_prematuro": premature,
        "verdict": verdict,
        "response_preview": resp[:150].replace("\n", " ")
    })

print(f"\nRESUMEN AUTO-INTERROGADOR V2:")
print(f"  Total evaluados: {len(auto_cases)}")
print(f"  Pregunta correcta: {correct_count}/{len(auto_cases)}")
print(f"  Diagnóstico prematuro: {premature_count}/{len(auto_cases)}")
print(f"  Loops: {loops_count}")

csv_path = Path("FASE11_AUTOINTERROGATOR_REGRESSION_V2.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print(f"Resultados guardados en {csv_path.resolve()}")
