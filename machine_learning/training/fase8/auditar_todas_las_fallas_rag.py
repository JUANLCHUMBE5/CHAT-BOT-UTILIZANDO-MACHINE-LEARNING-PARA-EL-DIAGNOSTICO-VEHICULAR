import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
import sys
sys.path.insert(0, str(BASE_DIR))
from machine_learning.models.taxonomia_sistemas import TAXONOMIA_MACRO_SISTEMAS, FALLA_A_SISTEMA

with open(BASE_DIR / "machine_learning/manuals/metadatos_manuales.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Auditando los {len(data)} procedimientos...")

corregir = []
for d in data:
    pid = d["id_procedimiento"]
    tit = d["titulo"].lower()
    falla = d.get("falla", "")
    sis = d.get("sistema", "")
    
    # Check 1: RAG_PROC_059, 062, 203 (disco de embrague)
    if pid in ["RAG_PROC_059", "RAG_PROC_062", "RAG_PROC_203"]:
        corregir.append((d, "Disco de embrague desgastado o patinando", "TRANSMISION"))
    # Check 2: RAG_PROC_092 (bombin de embrague)
    elif pid == "RAG_PROC_092":
        corregir.append((d, "Falla en bombin o bomba hidraulica de embrague", "TRANSMISION"))
    # Check 3: RAG_PROC_046 (purga y reemplazo de bombin)
    elif pid == "RAG_PROC_046" and "bombin" in tit:
        corregir.append((d, "Falla en bombin o bomba hidraulica de embrague", "TRANSMISION"))

print(f"Total correcciones puntuales identificadas: {len(corregir)}")
for item, n_falla, n_sis in corregir:
    print(f"  [{item['id_procedimiento']}] {item['titulo'][:60]}... -> Falla: '{n_falla}' | Sist: '{n_sis}'")
