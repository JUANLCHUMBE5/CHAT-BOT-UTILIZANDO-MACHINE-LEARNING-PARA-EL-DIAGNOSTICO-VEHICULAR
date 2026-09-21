import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
with open(BASE_DIR / "machine_learning/manuals/metadatos_manuales.json", "r", encoding="utf-8") as f:
    data = json.load(f)

sospechosos = []
for d in data:
    pid = d.get("id_procedimiento")
    tit = d.get("titulo", "").lower()
    falla = d.get("falla", "")
    sis = d.get("sistema", "")
    
    # Inconsistencias flagrantes
    if "embrague" in tit and "freno" in falla.lower() and "electromagnetico" not in tit:
        sospechosos.append((pid, d["titulo"], falla, sis, "Deberia ser Embrague / Transmision"))
    elif "freno" in tit and "embrague" in falla.lower():
        sospechosos.append((pid, d["titulo"], falla, sis, "Deberia ser Frenos"))
    elif "pastilla" in tit and "freno" not in sis.lower():
        sospechosos.append((pid, d["titulo"], falla, sis, "Deberia ser FRENOS"))
    elif "bomba de gasolina" in tit and sis != "MOTOR":
        sospechosos.append((pid, d["titulo"], falla, sis, "Deberia ser MOTOR"))

print(f"Total procedimientos sospechosos encontrados: {len(sospechosos)}")
for s in sospechosos:
    print(f"\n[{s[0]}] {s[1]}\n  Falla actual: {s[2]} (Sistema: {s[3]})\n  Correccion propuesta: {s[4]}")
