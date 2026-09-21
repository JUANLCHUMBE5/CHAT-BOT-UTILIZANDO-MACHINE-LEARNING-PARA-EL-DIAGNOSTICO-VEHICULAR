import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

with open(BASE_DIR / "docs" / "graficas" / "reporte_prueba_general_100_casos.json", "r", encoding="utf-8") as f:
    data = json.load(f)

casos = {c["id"]: c for c in data["casos_completos"] if c["grupo"] == "GRUPO_1_TECNICO"}
casos_revisar = ["G1_11", "G1_12", "G1_25", "G1_28", "G1_33", "G1_39", "G1_41"]

out_path = BASE_DIR / "scratch" / "salida_reportes_7.txt"
with open(out_path, "w", encoding="utf-8") as out:
    for cid in casos_revisar:
        c = casos[cid]
        rep = c.get("reporte_tecnico_completo", "")
        out.write(f"==================== {cid} ====================\n")
        out.write(rep[:700] + "\n\n")

print(f"Salida escrita en {out_path}")
