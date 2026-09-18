"""
Aplica correcciones de metadatos estrictamente validadas en metadatos_manuales.json:
- RAG_PROC_059: Kit de embrague manual -> Falla: Disco de embrague desgastado o patinando (TRANSMISION)
- RAG_PROC_062: Kit de embrague manual -> Falla: Disco de embrague desgastado o patinando (TRANSMISION)
- RAG_PROC_092: Bomba y cilindro de embrague -> Falla: Falla en bombin o bomba hidraulica de embrague (TRANSMISION)
- RAG_PROC_203: Prueba de calado de embrague -> Falla: Disco de embrague desgastado o patinando (TRANSMISION)
- RAG_PROC_049: Fluido CVT/ATF -> agregar P0841 a codigos_dtc (además de P0700 y P0730)
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
META_PATH = BASE_DIR / "machine_learning" / "manuals" / "metadatos_manuales.json"

with open(META_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

modificados = 0
for d in data:
    pid = d.get("id_procedimiento")
    if pid in ["RAG_PROC_059", "RAG_PROC_062", "RAG_PROC_203"]:
        d["falla"] = "Disco de embrague desgastado o patinando"
        d["sistema"] = "TRANSMISION"
        modificados += 1
    elif pid == "RAG_PROC_092":
        d["falla"] = "Falla en bombin o bomba hidraulica de embrague"
        d["sistema"] = "TRANSMISION"
        modificados += 1
    elif pid == "RAG_PROC_049":
        dtcs = d.get("codigos_dtc", [])
        if "P0841" not in dtcs:
            dtcs.append("P0841")
            d["codigos_dtc"] = dtcs
            modificados += 1

with open(META_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Metadatos corregidos exitosamente: {modificados} procedimientos actualizados.")
