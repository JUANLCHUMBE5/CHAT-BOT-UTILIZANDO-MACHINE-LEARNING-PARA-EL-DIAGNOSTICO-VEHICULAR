import sys
import pandas as pd
from pathlib import Path

base_dir = Path('.').resolve()
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))
if str(base_dir / "backend") not in sys.path:
    sys.path.insert(0, str(base_dir / "backend"))

from backend.src.core.diagnostico.taxonomia_sistemas import FALLA_A_SISTEMA

# Load canonical classes from AUDITORIA_TAXONOMIA_61_FASE10.csv
df_tax = pd.read_csv(base_dir / "AUDITORIA_TAXONOMIA_61_FASE10.csv")
canonical_classes = list(df_tax['etiqueta_canonica'])
assert len(canonical_classes) == 61, f"Expected 61 canonical classes, got {len(canonical_classes)}"

print(f"Total keys in FALLA_A_SISTEMA: {len(FALLA_A_SISTEMA)}")
assert len(FALLA_A_SISTEMA) == 61, f"Expected 61 keys in FALLA_A_SISTEMA, got {len(FALLA_A_SISTEMA)}"

# Check coverage
missing = [c for c in canonical_classes if c not in FALLA_A_SISTEMA]
print(f"Clases sin mapping: {len(missing)}")
assert len(missing) == 0, f"Missing classes in FALLA_A_SISTEMA: {missing}"

extra = [c for c in FALLA_A_SISTEMA if c not in canonical_classes]
print(f"Clases extra en mapping: {len(extra)}")
assert len(extra) == 0, f"Extra classes in FALLA_A_SISTEMA: {extra}"

# Check resulting macros
resulting_macros = sorted(list(set(FALLA_A_SISTEMA.values())))
expected_macros = sorted([
    "MOTOR",
    "FRENOS",
    "TRANSMISION",
    "SUSPENSION_CHASIS",
    "ELECTRICO",
    "CLIMATIZACION",
    "CARROCERIA_NEUMATICA"
])

print(f"\nResulting macros ({len(resulting_macros)}): {resulting_macros}")
print(f"Expected macros  ({len(expected_macros)}): {expected_macros}")
assert resulting_macros == expected_macros, f"Macros mismatch: {resulting_macros} != {expected_macros}"

# Build MAPEO_CANONICO_61_A_7.csv
rows = []
for c in canonical_classes:
    rows.append({
        "clase_objetivo": c,
        "macro_sistema_canonico": FALLA_A_SISTEMA[c]
    })

df_map = pd.DataFrame(rows)
df_map.to_csv(base_dir / "MAPEO_CANONICO_61_A_7.csv", index=False, encoding="utf-8")
df_map.to_csv(base_dir / "machine_learning/data/fase10/MAPEO_CANONICO_61_A_7.csv", index=False, encoding="utf-8")
print(f"\nSaved MAPEO_CANONICO_61_A_7.csv ({len(df_map)} filas)")

print("\nDistribución por macro canónico en taxonomía:")
print(df_map['macro_sistema_canonico'].value_counts())
