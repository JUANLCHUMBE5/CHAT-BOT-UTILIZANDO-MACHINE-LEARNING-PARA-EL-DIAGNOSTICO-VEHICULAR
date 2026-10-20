import csv
import json
import re
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(".").resolve()
reconciled_file = PROJECT_ROOT / "docs/auditorias/rag/RAG_RECONCILIACION_61_CLASES.csv"

with open(reconciled_file, "r", encoding="utf-8-sig") as f:
    clases_data = list(csv.DictReader(f))

# Leer el generador original
orig_path = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/benchmarks/build_independent_benchmark.py"
code_lines = orig_path.read_text(encoding="utf-8").splitlines()

# Extraer el bloque del diccionario TEMPLATES y CONFUSION_MAP
target_code = []
recording = False
for line in code_lines:
    if line.strip().startswith("CONFUSION_MAP ="):
        recording = True
    if line.strip().startswith("for idx, c_info in enumerate(clases_data):"):
        recording = False
        break
    if recording:
        target_code.append(line)

exec_namespace = {}
dedented_code = textwrap.dedent("\n".join(target_code))
exec(dedented_code, exec_namespace)

CONFUSION_MAP = exec_namespace["CONFUSION_MAP"]
SAFETY_CLASSES = exec_namespace["SAFETY_CLASSES"]
TEMPLATES = exec_namespace["TEMPLATES"]

benchmark_items = []
q_counter = 1

for idx, c_info in enumerate(clases_data):
    c1_id_1based = int(c_info["ID_C1"])
    c1_idx_0based = c1_id_1based - 1
    c1_name = c_info["CLASE_EXACTA"].strip()
    c1_macro = c_info["MACRO"].strip()

    pair = TEMPLATES.get(
        c1_idx_0based,
        [
            (f"Falla vehicular en sistema {c1_macro} correspondiente a {c1_name}", "TECHNICAL", False, []),
            (f"consulta de cliente en taller mecanico sobre problema de {c1_name}", "COLLOQUIAL_WHATSAPP", False, []),
        ],
    )

    for q_text, lang_type, has_dtc, dtc_list in pair:
        item = {
            "query_id": f"BENCH_{q_counter:03d}",
            "query": q_text,
            "language_type": lang_type,
            "has_dtc": has_dtc,
            "dtc_codes": dtc_list,
            "confusion_group": CONFUSION_MAP.get(c1_idx_0based, "NONE"),
            "is_safety": c1_idx_0based in SAFETY_CLASSES,
            "expected_class_id": c1_id_1based,
            "expected_class_name": c1_name,
            "expected_macro": c1_macro,
        }
        benchmark_items.append(item)
        q_counter += 1

out_bench = (
    PROJECT_ROOT
    / "machine_learning/manuals/candidates/v1/benchmarks/benchmark_dataset_alineado.json"
)
with open(out_bench, "w", encoding="utf-8") as f:
    json.dump(
        {
            "benchmark_name": "RAG_INDEPENDENT_EVAL_122_ALINEADO",
            "total_queries": len(benchmark_items),
            "classes_covered": 61,
            "queries": benchmark_items,
        },
        f,
        indent=2,
        ensure_ascii=False,
    )

print(f"BENCHMARK ALINEADO CREADO EXITOSAMENTE: {out_bench}")
print(f"Total consultas: {len(benchmark_items)}")
for q in benchmark_items[:8]:
    print(f"[{q['query_id']}] ({q['expected_class_id']}: {q['expected_class_name']}) -> {q['query'][:65]}...")
