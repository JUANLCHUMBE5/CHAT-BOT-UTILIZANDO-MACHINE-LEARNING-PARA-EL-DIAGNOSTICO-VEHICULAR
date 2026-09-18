import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent

# 1. E2E Results
results = list(csv.DictReader(open(base_dir / "FASE11_E2E_RESULTS_V1.csv", encoding="utf-8")))
verdicts = Counter(r["verdict"] for r in results)
cat_verdicts = defaultdict(Counter)
for r in results:
    cat_verdicts[r["category"]][r["verdict"]] += 1

print("=== VEREDICTOS TOTALES ===")
print("Total casos:", len(results))
for v, count in verdicts.items():
    print(f"  {v}: {count} ({count/len(results)*100:.2f}%)")
pass_rate = (verdicts["PASS"] + verdicts["PARTIAL"]) / len(results) * 100
strict_pass_rate = verdicts["PASS"] / len(results) * 100
print(f"Pass Rate (PASS + PARTIAL): {pass_rate:.2f}%")
print(f"Strict Pass Rate (PASS only): {strict_pass_rate:.2f}%")

print("\n=== VEREDICTOS POR CATEGORIA ===")
for cat, counts in sorted(cat_verdicts.items()):
    tot = sum(counts.values())
    p = counts["PASS"]
    part = counts["PARTIAL"]
    f = counts["FAIL"]
    b = counts["BLOCKED"]
    print(f"  {cat:<32}: Total={tot:<2} PASS={p:<2} PARTIAL={part:<2} FAIL={f:<2} BLOCKED={b:<2}")

# 2. Turns
traces = list(csv.DictReader(open(base_dir / "FASE11_TURN_TRACE_V1.csv", encoding="utf-8")))
print(f"\nTotal turnos ejecutados: {len(traces)}")

# 3. Technical Errors
errors = list(csv.DictReader(open(base_dir / "FASE11_TECHNICAL_ERRORS.csv", encoding="utf-8")))
print(f"Total errores tecnicos: {len(errors)}")

# 4. Defects
defects = list(csv.DictReader(open(base_dir / "FASE11_DEFECTS_V1.csv", encoding="utf-8")))
sev_counts = Counter(d["severity"] for d in defects)
print("\n=== DEFECTOS REGISTRADOS ===")
print("Total defectos:", len(defects))
for s in ["P0", "P1", "P2", "P3"]:
    print(f"  {s}: {sev_counts.get(s, 0)}")

print("\n--- LISTADO DE DEFECTOS P0 Y P1 ---")
for d in defects:
    if d["severity"] in ("P0", "P1"):
        print(f"[{d['defect_id']}] {d['severity']} | Caso: {d['case_id']} ({d['category']}) | Componente: {d['component']}")
        print(f"   Descripcion: {d['description']}")
        print(f"   Esperado   : {d['expected']}")
        print(f"   Observado  : {d['observed']}")
        print(f"   Causa      : {d['suspected_cause']}")
        print()

# 5. Latency
lat = json.load(open(base_dir / "FASE11_LATENCY_V1.json", encoding="utf-8"))
print("\n=== LATENCIAS ===")
print("E2E Total       :", lat["e2e_total"])
print("ML Inferencia   :", lat["ml_inferencia"])
print("RAG Recuperacion:", lat["rag_recuperacion"])
print("LLM Sintesis    :", lat["llm_sintesis"])

# 6. Session isolation
sessions = list(csv.DictReader(open(base_dir / "FASE11_SESSION_ISOLATION_V1.csv", encoding="utf-8")))
print("\n=== AISLAMIENTO SESIONES ===")
for s in sessions:
    print(f"  Caso {s['case_id']}: Contaminacion={s['contaminacion_detectada']}, Resultado={s['resultado']}")

# 7. RAG Audit
rags = list(csv.DictReader(open(base_dir / "FASE11_RAG_AUDIT_V1.csv", encoding="utf-8")))
rag_rel = Counter(r["relevante"] for r in rags)
print("\n=== AUDITORIA RAG ===")
print("Total consultas RAG auditadas:", len(rags))
print("Relevantes  :", rag_rel.get("SI", 0))
print("Irrelevantes:", rag_rel.get("NO", 0))

# 8. Historical AC Audit
print("\n=== AUDITORIA CASOS AC (GRUPO M) ===")
ac_cases = [r for r in results if r["category"] == "GRUPO_M_HISTORICO_AC"]
for r in ac_cases:
    print(f"  {r['case_id']}: Veredicto={r['verdict']}, Obs={r['observed_behavior']}, Notas={r['notes']}")

# Check turn trace for CASE_092
print("\n--- Trazabilidad Turno por Turno CASE_092 (Sail 2018 A/C) ---")
sail_traces = [t for t in traces if t["case_id"] == "CASE_092"]
for t in sail_traces:
    print(f"  Turno {t['turn']}: Input='{t['user_input']}' -> SynthQuery='{t['synthesized_ml_query']}' | Macro={t['macro_prediction']} | Top1={t['fault_top1']} ({t['macro_confidence']})")

# Check turn trace for CASE_093
print("\n--- Trazabilidad Turno por Turno CASE_093 (Direct A/C) ---")
direct_ac_traces = [t for t in traces if t["case_id"] == "CASE_093"]
for t in direct_ac_traces:
    print(f"  Turno {t['turn']}: Input='{t['user_input'][:80]}...' -> Macro={t['macro_prediction']} | Top1={t['fault_top1']} ({t['macro_confidence']})")
