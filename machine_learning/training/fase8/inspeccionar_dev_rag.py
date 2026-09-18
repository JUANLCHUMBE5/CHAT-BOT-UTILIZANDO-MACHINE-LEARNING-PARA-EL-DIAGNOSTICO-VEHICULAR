import json

with open("machine_learning/models/metricas_dev_fase8.json", "r", encoding="utf-8") as f:
    res = json.load(f)

print(f"Total casos: {res['total_casos']}")
print(f"Top-1 ML: {res['top1_ml_pct']}%")
print(f"Top-3 ML: {res['top3_ml_pct']}%")
print(f"RAG Hit@1: {res['rag_hit1_pct']}%")
print(f"RAG Hit@3: {res['rag_hit3_pct']}%")
print(f"E2E Estricto: {res['e2e_estricto_pct']}%")

print("\n--- Casos donde RAG Hit@1 falló ---")
for d in res["detalles"]:
    if not d["rag_hit1"]:
        hit3_str = "SÍ" if d["rag_hit3"] else "NO"
        print(f"{d['id']}: Esperada: '{d['esperada']}'\n   -> RAG Top1: '{d['rag_top1']}'\n   -> ML Top1:  '{d['top1_ml']}' (conf={d['confianza']}) [En RAG Top3: {hit3_str}]")
