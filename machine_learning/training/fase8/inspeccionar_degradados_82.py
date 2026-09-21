import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
with open(BASE_DIR / "machine_learning/models/reporte_fase8_2_candidata.json", "r", encoding="utf-8") as f:
    d = json.load(f)

detalles = d["detalles"]
degradados = [c for c in detalles if c["es_top1_ml"] and c["categoria_e2e"] != "ESTRICTO"]

print(f"Total casos con ML Top-1 correcto pero E2E degradado: {len(degradados)}")
for c in degradados:
    print(f"\nID: {c['id']}")
    print(f"  Esperada: {c['esperada']}")
    print(f"  Top1 ML:  {c['top1_ml']} (conf: {c['conf_ml']})")
    print(f"  Diag E2E: {c['diag_e2e']} (cat: {c['categoria_e2e']})")
    print(f"  Interrogador activado: {c['activado_interrogador']}")
