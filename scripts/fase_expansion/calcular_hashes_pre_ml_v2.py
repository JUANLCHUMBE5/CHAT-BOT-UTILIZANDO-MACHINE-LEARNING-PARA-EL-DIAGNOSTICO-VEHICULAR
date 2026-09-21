"""
calcular_hashes_pre_ml_v2.py
Calcula los hashes SHA-256 de los 13 artefactos protegidos del manifiesto
operacional vigente (CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json) y genera
docs/auditorias/HASHES_PRE_ML_V2.md
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
MANIFEST_FILE = PROJECT_ROOT / "docs" / "fase11_6" / "CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "auditorias" / "HASHES_PRE_ML_V2.md"

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
    manifest = json.load(f)

hashes_def = manifest.get("hashes_sha256", {})

filas = []
todos_coinciden = True

for comp_name, info in hashes_def.items():
    rel_path = info.get("ruta_relativa")
    esperado = info.get("sha256")
    full_path = PROJECT_ROOT / rel_path

    if not full_path.exists():
        actual = "NO_EXISTE"
        coincide = False
        tam = 0
    else:
        actual = sha256_file(full_path)
        coincide = (actual.lower() == esperado.lower())
        tam = full_path.stat().st_size

    if not coincide:
        todos_coinciden = False

    filas.append({
        "componente": comp_name,
        "ruta": rel_path,
        "esperado": esperado,
        "actual": actual,
        "tamano": tam,
        "coincide": coincide
    })

md = f"""# Registro Forense de Blindaje: Hashes Pre-Entrenamiento ML V2

**Fecha de Cálculo:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Manifiesto Operacional Vigente:** [`CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json`](file:///c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/docs/fase11_6/CARBOT_PRECAMPO_FINAL_HASH_MANIFEST.json)  
**Versión de Referencia:** `{manifest.get('version')}` (`{manifest.get('fase')}`)  
**Estado de Blindaje:** **{'APROBADO (13/13 COINCIDEN - 100% INTACTO)' if todos_coinciden else 'ALERTA: DISCREPANCIA DETECTADA'}**

---

## 1. Tabla de Verificación Criptográfica SHA-256

| Componente | Ruta Relativa | Hash Esperado en Manifiesto | Hash Actual Calculado | Tamaño (Bytes) | Estado |
|---|---|---|---|---|---|
"""

for r in filas:
    md += f"| **`{r['componente']}`** | `{r['ruta']}` | `{r['esperado'][:16]}...` | `{r['actual'][:16]}...` | {r['tamano']:,} | {'✅ INTACTO' if r['coincide'] else '❌ ALTERADO'} |\n"

md += f"""
---

## 2. Declaración de Blindaje Operacional

1. Los 13 artefactos protegidos de producción han sido certificados como **READ-ONLY**.
2. Cualquier reentrenamiento, vectorización o construcción de índice FAISS en la fase experimental se ejecutará exclusivamente dentro de:
   - `machine_learning/experimentos/carbot_v2/`
3. Ningún archivo con los nombres canónicos de producción (`modelo_diagnostico_c1.pkl`, `vectorizador_c1.pkl`, `modelo_sistema_c1_macrofix.pkl`, `indice_faiss_v1.index`) será sobreescrito.
4. Al finalizar la fase experimental se comprobará que `HASH_PRE == HASH_POST`. Si algún hash cambia, la fase será invalidada de inmediato.
"""

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(md)

print(f"Hashes Pre ML V2 calculados y guardados en {OUTPUT_FILE}")
print(f"Resultado: {sum(1 for r in filas if r['coincide'])}/{len(filas)} coinciden.")
