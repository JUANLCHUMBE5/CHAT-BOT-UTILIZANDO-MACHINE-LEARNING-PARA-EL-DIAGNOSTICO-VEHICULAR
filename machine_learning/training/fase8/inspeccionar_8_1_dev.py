import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
with open(BASE_DIR / "machine_learning/models/reporte_fase8_1_candidata.json", "r", encoding="utf-8") as f:
    d = json.load(f)

dev_cases = d["resultados_dev_60_casos"]["detalles_casos"]
miss_top1 = [c for c in dev_cases if not c["hit_top1_puro"]]
miss_top3 = [c for c in dev_cases if not c["hit_top3_puro"]]

print(f"Total fallos Top-1 Puro en DEV ({len(miss_top1)}/60):")
for c in miss_top1:
    print(f"  {c['id']}: GT='{c['gt_falla']}' | Pred='{c['pred_top1_puro']}' (conf: {c['conf_puro']}) | Top-3: {c['hit_top3_puro']}")

print(f"\nTotal fallos Top-3 Puro en DEV ({len(miss_top3)}/60):")
for c in miss_top3:
    print(f"  {c['id']}: GT='{c['gt_falla']}' | Pred='{c['pred_top1_puro']}' (conf: {c['conf_puro']})")
