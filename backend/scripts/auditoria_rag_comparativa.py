import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from src.infrastructure.motor_rag import MotorRAG

bench_path = ROOT / "machine_learning/manuals/candidates/v1/benchmarks/benchmark_dataset_alineado.json"
with open(bench_path, "r", encoding="utf-8") as f:
    bench_data = json.load(f)

queries = bench_data["queries"]

def evaluar_motor_rag(version_id: str):
    print(f"\n--- EVALUANDO MOTOR RAG: {version_id} ---")
    rag = MotorRAG(rag_version=version_id)
    latencias = []
    hit1, hit3 = 0, 0
    contaminacion_macro = 0
    casos_contaminados = []

    for item in queries:
        q = item["query"]
        exp_falla = item["expected_class_name"]
        exp_macro = item.get("expected_macro", "").upper()
        top_fallas = [{"falla": exp_falla, "probabilidad": 0.85}]

        t0 = time.perf_counter()
        doc_txt, tit, sim, meta = rag.recuperar_procedimiento_hibrido(
            consulta=q,
            macro_sistema=exp_macro,
            top_fallas=top_fallas,
        )
        lat = (time.perf_counter() - t0) * 1000.0
        latencias.append(lat)

        ret_falla = (meta.get("falla") or meta.get("titulo") or "").strip().lower()
        ret_macro = (meta.get("system") or meta.get("macro_sistema") or meta.get("subsystem") or "").strip().upper()

        coincide_falla = (exp_falla.lower() in ret_falla or ret_falla in exp_falla.lower()) if ret_falla else False
        
        # Hit@1
        if coincide_falla or (sim > 0.35 and ret_macro == exp_macro):
            hit1 += 1
        
        # Contaminación de macrosistema
        if ret_macro and exp_macro and ret_macro != exp_macro:
            contaminacion_macro += 1
            casos_contaminados.append({
                "query": q,
                "exp_macro": exp_macro,
                "ret_macro": ret_macro,
                "titulo": tit
            })

    n = len(queries)
    lat_p50 = sorted(latencias)[n // 2]
    lat_p95 = sorted(latencias)[int(n * 0.95)]
    
    return {
        "version": version_id,
        "hit1_pct": (hit1 / n) * 100.0,
        "contaminacion_pct": (contaminacion_macro / n) * 100.0,
        "lat_p50_ms": round(lat_p50, 2),
        "lat_p95_ms": round(lat_p95, 2),
        "n": n,
        "contaminados": casos_contaminados
    }

# Evaluar Baseline F8.3 vs Candidate V1 sobre el MISMO benchmark alineado
res_base = evaluar_motor_rag("baseline_f8_3")
res_cand = evaluar_motor_rag("candidate_v1")

print("\n=== COMPARATIVA DIRECTA SOBRE EL MISMO BENCHMARK CORREGIDO (N=122) ===")
print(f"BASELINE F8.3:")
print(f"  Hit@1:         {res_base['hit1_pct']:.2f}%")
print(f"  Contaminación: {res_base['contaminacion_pct']:.2f}% ({len(res_base['contaminados'])} casos)")
print(f"  Latencia p50:  {res_base['lat_p50_ms']} ms | p95: {res_base['lat_p95_ms']} ms")

print(f"\nCANDIDATE V1 (Paquete Congelado):")
print(f"  Hit@1:         {res_cand['hit1_pct']:.2f}%")
print(f"  Contaminación: {res_cand['contaminacion_pct']:.2f}% ({len(res_cand['contaminados'])} casos)")
print(f"  Latencia p50:  {res_cand['lat_p50_ms']} ms | p95: {res_cand['lat_p95_ms']} ms")

# Investigar el 3.33% de contaminación de la ablación de 30 casos
print("\n=== INVESTIGACIÓN DEL 3.33% (1 CASO) EN LA MUESTRA DE ABLACIÓN ===")
muestra_30 = queries[::4][:30]
rag_cand = MotorRAG(rag_version="candidate_v1")

for idx, item in enumerate(muestra_30):
    q = item["query"]
    exp_falla = item["expected_class_name"]
    exp_macro = item.get("expected_macro", "").upper()
    top_fallas = [{"falla": exp_falla, "probabilidad": 0.85}]

    doc_txt, tit, sim, meta = rag_cand.recuperar_procedimiento_hibrido(
        consulta=q,
        macro_sistema=exp_macro,
        top_fallas=top_fallas,
    )
    ret_macro = (meta.get("system") or meta.get("macro_sistema") or meta.get("subsystem") or "").strip().upper()
    
    if ret_macro and exp_macro and ret_macro != exp_macro:
        print(f"Caso contaminado en ablación [#{idx}]:")
        print(f"  Query:      '{q}'")
        print(f"  Esperado:   Macro={exp_macro} | Falla={exp_falla}")
        print(f"  Retornado:  Macro={ret_macro} | Titulo='{tit}' | Sim={sim:.4f}")
        print(f"  Explicación: Diferencia entre macro_sistema predicho/esperado vs metadato del documento retornado.")

out_data = {
    "baseline_f8_3": res_base,
    "candidate_v1": res_cand,
}
with open(ROOT / "machine_learning/models/auditoria_comparativa_rag.json", "w", encoding="utf-8") as f:
    json.dump(out_data, f, indent=2)
