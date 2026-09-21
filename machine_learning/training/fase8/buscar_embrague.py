import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
with open(BASE_DIR / "machine_learning/manuals/metadatos_manuales.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for d in data:
    tit = d.get("titulo", "").lower()
    if any(k in tit for k in ["patina", "patinando", "desgaste de embrague", "prensa", "disco de embrague"]):
        print(f"ID: {d['id_procedimiento']} | Tit: {d['titulo']} | Falla: {d.get('falla')}")
