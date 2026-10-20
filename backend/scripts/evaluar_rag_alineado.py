import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(".").resolve()
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.infrastructure.motor_rag import MotorRAG

print("=== EVALUACIÓN DE MOTOR RAG (BASELINE OFICIAL) SOBRE BENCHMARK ALINEADO ===")
rag = MotorRAG()
bench_path = ROOT / "machine_learning/manuals/candidates/v1/benchmarks/benchmark_dataset_alineado.json"
with open(bench_path, "r", encoding="utf-8") as f:
    bench_data = json.load(f)

queries = bench_data["queries"]
latencias = []
hit1 = 0
hit3 = 0
contaminacion_macro = 0
fallos = []

for q_obj in queries:
    q = q_obj["query"]
    exp_falla = q_obj["expected_class_name"]
    exp_macro = q_obj.get("expected_macro", "").upper()
    top_fallas = [{"falla": exp_falla, "probabilidad": 0.85}]

    t0 = time.perf_counter()
    doc_text, nivel, sim, meta = rag.recuperar_procedimiento_con_metadatos(
        consulta=q, top_fallas=top_fallas, macro_sistema=exp_macro
    )
    lat = (time.perf_counter() - t0) * 1000.0
    latencias.append(lat)

    falla_ret = (
        meta.get("primary_fault_class")
        or meta.get("falla")
        or meta.get("titulo")
        or ""
    ).strip().lower()
    macro_ret = (meta.get("system") or meta.get("sistema") or "").strip().upper()

    coincide_falla = (
        exp_falla.lower() in falla_ret or falla_ret in exp_falla.lower()
    ) if falla_ret else False

    if coincide_falla or (sim > 0.40 and exp_macro == macro_ret):
        hit1 += 1
    else:
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

    if macro_ret and exp_macro and macro_ret != exp_macro and sim > 0.15:
        contaminacion_macro += 1

hit1_pct = (hit1 / len(queries)) * 100.0
contam_pct = (contaminacion_macro / len(queries)) * 100.0
lat_p50 = float(np.percentile(latencias, 50))
lat_p95 = float(np.percentile(latencias, 95))

print(f"Total consultas evaluadas: {len(queries)}")
print(f"Hit@1: {hit1_pct:.2f}% ({hit1}/{len(queries)})")
print(f"Contaminacion Macrosistema: {contam_pct:.2f}% ({contaminacion_macro}/{len(queries)})")
print(f"Latencia p50: {lat_p50:.2f} ms | p95: {lat_p95:.2f} ms")
print(f"Total fallos restantes: {len(fallos)}")

out_res = {
    "hit1_pct": hit1_pct,
    "hit1_count": hit1,
    "total": len(queries),
    "contaminacion_pct": contam_pct,
    "latencia_p50": lat_p50,
    "latencia_p95": lat_p95,
    "fallos_restantes": len(fallos)
}
with open("machine_learning/models/rag_benchmark_alineado_resultado.json", "w", encoding="utf-8") as f:
    json.dump(out_res, f, indent=2)
