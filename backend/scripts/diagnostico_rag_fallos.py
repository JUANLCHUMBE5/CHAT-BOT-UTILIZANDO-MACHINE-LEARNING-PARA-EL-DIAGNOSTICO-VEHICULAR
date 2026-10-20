import json
import sys
from pathlib import Path

# Add backend and root
ROOT = Path(".").resolve()
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.infrastructure.motor_rag import MotorRAG

rag = MotorRAG()
bench_path = Path("machine_learning/manuals/candidates/v1/benchmarks/benchmark_dataset.json")
with open(bench_path, "r", encoding="utf-8") as f:
    bench_data = json.load(f)

queries = bench_data["queries"]
fallos = []

for q_obj in queries:
    q = q_obj["query"]
    exp_falla = q_obj["expected_class_name"]
    exp_macro = q_obj.get("expected_macro", "").upper()
    top_fallas = [{"falla": exp_falla, "probabilidad": 0.85}]

    doc_text, nivel, sim, meta = rag.recuperar_procedimiento_con_metadatos(
        consulta=q, top_fallas=top_fallas, macro_sistema=exp_macro
    )

    falla_ret = (
        meta.get("primary_fault_class")
        or meta.get("falla")
        or meta.get("titulo")
        or ""
    ).strip().lower()
    macro_ret = (meta.get("system") or meta.get("sistema") or "").strip().upper()

    coincide = (
        exp_falla.lower() in falla_ret or falla_ret in exp_falla.lower()
    ) if falla_ret else False
    if not (coincide or (sim > 0.40 and exp_macro == macro_ret)):
        fallos.append({
            "query_id": q_obj["query_id"],
            "query": q,
            "expected_class": exp_falla,
            "expected_macro": exp_macro,
            "retrieved_falla": falla_ret,
            "retrieved_macro": macro_ret,
            "similitud": sim,
            "retrieved_titulo": meta.get("titulo") or meta.get("procedure_title"),
            "doc_id": meta.get("doc_id") or meta.get("id_procedimiento")
        })

print(f"Total fallos: {len(fallos)} de {len(queries)}")
print("\n--- MUESTRA DE 12 CASOS FALLIDOS ---")
for i, f in enumerate(fallos[:12]):
    print(f"[{f['query_id']}] Q: \"{f['query']}\"")
    print(f"   Esperado: \"{f['expected_class']}\" ({f['expected_macro']})")
    print(f"   Obtenido: \"{f['retrieved_falla']}\" ({f['retrieved_macro']}) | Doc: {f['doc_id']} | Sim: {f['similitud']:.4f}")
    print(f"   Titulo doc: \"{f['retrieved_titulo']}\"\n")

# Analizar patrones en los fallos
doc_counts = {}
for f in fallos:
    d = f['doc_id'] or 'SIN_DOC'
    doc_counts[d] = doc_counts.get(d, 0) + 1

print("\n--- PROCEDIMIENTOS FRECUENTEMENTE RECUPERADOS ERRÓNEAMENTE (AGUJEROS NEGROS) ---")
for d, c in sorted(doc_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"Doc {d}: {c} veces")
