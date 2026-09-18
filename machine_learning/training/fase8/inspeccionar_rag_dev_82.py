import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
with open(BASE_DIR / "machine_learning/models/metricas_dev_fase8.json", "r", encoding="utf-8") as f:
    d = json.load(f)

detalles = d["detalles"]
miss_rag1 = [c for c in detalles if not c["rag_hit1"]]
miss_rag3 = [c for c in detalles if not c["rag_hit3"]]

print(f"RAG Hit@1: {len(detalles) - len(miss_rag1)}/60 ({(len(detalles) - len(miss_rag1))/60*100:.2f}%)")
print(f"RAG Hit@3: {len(detalles) - len(miss_rag3)}/60 ({(len(detalles) - len(miss_rag3))/60*100:.2f}%)")

print(f"\nCasos que fallan RAG Hit@1 ({len(miss_rag1)}):")
for c in miss_rag1:
    print(f"  {c['id']}: Esperada='{c['esperada']}' | RAG Top1='{c['rag_top1']}' | In Hit@3: {c['rag_hit3']}")

print(f"\nCasos que fallan RAG Hit@3 ({len(miss_rag3)}):")
for c in miss_rag3:
    print(f"  {c['id']}: Esperada='{c['esperada']}' | RAG Top1='{c['rag_top1']}'")
