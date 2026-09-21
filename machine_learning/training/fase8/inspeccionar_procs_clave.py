import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
with open(BASE_DIR / "machine_learning/manuals/metadatos_manuales.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for d in data:
    falla = d.get("falla", "")
    if any(k in falla for k in ["CVT", "booster", "embrague desgastado", "baja presion de aceite", "actuador de turbo"]):
        print(f"ID: {d['id_procedimiento']} | Falla: {falla}")
        print(f"   Titulo: {d['titulo']}")
        print(f"   DTCs: {d.get('codigos_dtc', [])}")
        print(f"   Fuente: {d.get('archivo_fuente')}")
