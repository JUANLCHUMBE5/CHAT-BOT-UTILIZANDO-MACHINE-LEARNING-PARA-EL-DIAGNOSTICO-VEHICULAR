import sys
import hashlib
import json
from datetime import datetime
import pandas as pd
from pathlib import Path

base_dir = Path('.').resolve()
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))
if str(base_dir / "backend") not in sys.path:
    sys.path.insert(0, str(base_dir / "backend"))

from backend.src.core.diagnostico.taxonomia_sistemas import FALLA_A_SISTEMA

def calcular_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

ruta_tr10_orig = base_dir / "machine_learning/data/fase10/train10_v1.csv"
ruta_dev10_orig = base_dir / "machine_learning/data/fase10/dev10_v1.csv"

h_tr10_orig = calcular_sha256(ruta_tr10_orig)
h_dev10_orig = calcular_sha256(ruta_dev10_orig)

assert h_tr10_orig == "ec407886b48d66c4d9be6fc8b72decf605f4f94ac1af0575d9c4fa0db005e92b"
assert h_dev10_orig == "b44a752ca58fb4e27c7d9167198747e076d0c3cd5c4b07eaa03919777d1fd2b6"

df_tr_orig = pd.read_csv(ruta_tr10_orig)
df_dev_orig = pd.read_csv(ruta_dev10_orig)

# 1. Create derived copies
df_tr_fix = df_tr_orig.copy()
df_dev_fix = df_dev_orig.copy()

# 2. Replace macro_sistema
df_tr_fix["macro_sistema"] = df_tr_fix["clase_objetivo"].map(FALLA_A_SISTEMA)
df_dev_fix["macro_sistema"] = df_dev_fix["clase_objetivo"].map(FALLA_A_SISTEMA)

# 3. Check for any unmapped or NaN
assert df_tr_fix["macro_sistema"].isna().sum() == 0, "NaN found in train macro_sistema!"
assert df_dev_fix["macro_sistema"].isna().sum() == 0, "NaN found in dev macro_sistema!"

# 4. Check other columns identical
for col in df_tr_orig.columns:
    if col != "macro_sistema":
        assert df_tr_orig[col].equals(df_tr_fix[col]), f"Column {col} differs in TRAIN10!"
        assert df_dev_orig[col].equals(df_dev_fix[col]), f"Column {col} differs in DEV10!"
print("Validación: Todas las columnas excepto 'macro_sistema' son 100% idénticas.")

# 5. Save derived versions
ruta_tr10_fix = base_dir / "machine_learning/data/fase10/train10_v1_1_macrofix.csv"
ruta_dev10_fix = base_dir / "machine_learning/data/fase10/dev10_v1_1_macrofix.csv"

df_tr_fix.to_csv(ruta_tr10_fix, index=False, encoding="utf-8")
df_dev_fix.to_csv(ruta_dev10_fix, index=False, encoding="utf-8")

# Also copy to root for ease of access if requested
df_tr_fix.to_csv(base_dir / "train10_v1_1_macrofix.csv", index=False, encoding="utf-8")
df_dev_fix.to_csv(base_dir / "dev10_v1_1_macrofix.csv", index=False, encoding="utf-8")

h_tr10_fix = calcular_sha256(ruta_tr10_fix)
h_dev10_fix = calcular_sha256(ruta_dev10_fix)

print(f"TRAIN10 macrofix: {ruta_tr10_fix} | SHA-256: {h_tr10_fix}")
print(f"DEV10 macrofix:   {ruta_dev10_fix} | SHA-256: {h_dev10_fix}")

# 6. Validate macros
expected_macros = {
    "MOTOR", "FRENOS", "TRANSMISION", "SUSPENSION_CHASIS",
    "ELECTRICO", "CLIMATIZACION", "CARROCERIA_NEUMATICA"
}
tr_macros = set(df_tr_fix["macro_sistema"].unique())
dev_macros = set(df_dev_fix["macro_sistema"].unique())

assert tr_macros == expected_macros, f"TRAIN macros mismatch: {tr_macros}"
assert dev_macros == expected_macros, f"DEV macros mismatch: {dev_macros}"
assert df_tr_fix["clase_objetivo"].nunique() == 61
assert df_dev_fix["clase_objetivo"].nunique() == 61
assert len(df_tr_fix) == 6904
assert len(df_dev_fix) == 1725

print("\n--- DISTRIBUCIÓN TRAIN10 MACROFIX (n=6904) ---")
tr_dist = []
for m in sorted(list(expected_macros)):
    sub = df_tr_fix[df_tr_fix["macro_sistema"] == m]
    n_cl = sub["clase_objetivo"].nunique()
    tr_dist.append({
        "macro": m,
        "filas": len(sub),
        "porcentaje": f"{len(sub)/len(df_tr_fix)*100:.2f}%",
        "n_clases": n_cl
    })
print(pd.DataFrame(tr_dist).to_string(index=False))

print("\n--- DISTRIBUCIÓN DEV10 MACROFIX (n=1725) ---")
dev_dist = []
for m in sorted(list(expected_macros)):
    sub = df_dev_fix[df_dev_fix["macro_sistema"] == m]
    n_cl = sub["clase_objetivo"].nunique()
    dev_dist.append({
        "macro": m,
        "filas": len(sub),
        "porcentaje": f"{len(sub)/len(df_dev_fix)*100:.2f}%",
        "n_clases": n_cl
    })
print(pd.DataFrame(dev_dist).to_string(index=False))

# 7. Create MACROFIX_MANIFEST.json
manifest = {
    "version": "10.1-MACROFIX",
    "timestamp": datetime.now().isoformat(),
    "estado": "DATASETS_MACRO_SANEADOS",
    "source_train": "machine_learning/data/fase10/train10_v1.csv",
    "source_train_hash": h_tr10_orig,
    "fixed_train": "machine_learning/data/fase10/train10_v1_1_macrofix.csv",
    "fixed_train_hash": h_tr10_fix,
    "source_dev": "machine_learning/data/fase10/dev10_v1.csv",
    "source_dev_hash": h_dev10_orig,
    "fixed_dev": "machine_learning/data/fase10/dev10_v1_1_macrofix.csv",
    "fixed_dev_hash": h_dev10_fix,
    "mapping_source": "backend/src/core/diagnostico/taxonomia_sistemas.py:FALLA_A_SISTEMA",
    "mapping_file": "MAPEO_CANONICO_61_A_7.csv",
    "mapping_hash": calcular_sha256(base_dir / "MAPEO_CANONICO_61_A_7.csv"),
    "filas_train": len(df_tr_fix),
    "filas_dev": len(df_dev_fix),
    "clases_falla": 61,
    "macros": 7,
    "macros_lista": sorted(list(expected_macros)),
    "columnas_modificadas": ["macro_sistema"],
    "columnas_inmutables": [c for c in df_tr_orig.columns if c != "macro_sistema"]
}

with open(base_dir / "machine_learning/data/fase10/MACROFIX_MANIFEST.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

with open(base_dir / "MACROFIX_MANIFEST.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print("\nGuardado MACROFIX_MANIFEST.json exitosamente.")
