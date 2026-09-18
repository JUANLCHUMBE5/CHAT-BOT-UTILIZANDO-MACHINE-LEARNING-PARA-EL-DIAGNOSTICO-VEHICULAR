import sys
import pandas as pd
import joblib
from pathlib import Path

base_dir = Path('.').resolve()
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))
if str(base_dir / "backend") not in sys.path:
    sys.path.insert(0, str(base_dir / "backend"))

from backend.src.core.diagnostico.taxonomia_sistemas import FALLA_A_SISTEMA

# 1. TRAIN original
df_orig = pd.read_csv(base_dir / "machine_learning/data/dataset_sintomas_limpio.csv")
print(f"TRAIN original nulls in 'sistema': {df_orig['sistema'].isna().sum()} / {len(df_orig)}")
orig_macros = sorted([str(x) for x in df_orig['sistema'].dropna().unique()])
print(f"TRAIN original macros ({len(orig_macros)}): {orig_macros}")
print("Distribución por macro en original:")
print(df_orig['sistema'].value_counts(dropna=False))

# 2. Fase10 master
p_f10 = base_dir / "machine_learning/data/fase10/dataset_fase10_master_v1_1_2440.csv"
if not p_f10.exists():
    p_f10 = base_dir / "machine_learning/data/fase10/dataset_fase10_master.csv"
df_f10 = pd.read_csv(p_f10)
f10_macros = sorted(df_f10['macro_sistema'].unique())
print(f"\nFase10 macros ({len(f10_macros)}): {f10_macros}")
print("Distribución por macro en Fase10:")
print(df_f10['macro_sistema'].value_counts())

# 3. TRAIN10
df_tr10 = pd.read_csv(base_dir / "machine_learning/data/fase10/train10_v1.csv")
print(f"TRAIN10 nulls in macro_sistema: {df_tr10['macro_sistema'].isna().sum()} / {len(df_tr10)}")
tr10_macros = sorted([str(x) for x in df_tr10['macro_sistema'].dropna().unique()])
print(f"\nTRAIN10 macros ({len(tr10_macros)}): {tr10_macros}")
print("Distribución por macro en TRAIN10:")
print(df_tr10['macro_sistema'].value_counts(dropna=False))

# 4. DEV10
df_dev10 = pd.read_csv(base_dir / "machine_learning/data/fase10/dev10_v1.csv")
print(f"DEV10 nulls in macro_sistema: {df_dev10['macro_sistema'].isna().sum()} / {len(df_dev10)}")
dev10_macros = sorted([str(x) for x in df_dev10['macro_sistema'].dropna().unique()])
print(f"\nDEV10 macros ({len(dev10_macros)}): {dev10_macros}")
print("Distribución por macro en DEV10:")
print(df_dev10['macro_sistema'].value_counts(dropna=False))

# 5. F8.3 modelo_sistema.pkl
f83_sis_model = joblib.load(base_dir / "machine_learning/models/modelo_sistema.pkl")
f83_sis_classes = sorted(list(f83_sis_model.classes_))
print(f"\nF8.3 modelo_sistema classes ({len(f83_sis_classes)}): {f83_sis_classes}")

# 6. C1 modelo_sistema_c1.pkl
c1_sis_model = joblib.load(base_dir / "machine_learning/training/fase10/candidates/C1/modelo_sistema_c1.pkl")
c1_sis_classes = sorted(list(c1_sis_model.classes_))
print(f"\nC1 modelo_sistema classes ({len(c1_sis_classes)}): {c1_sis_classes}")

# 7. Backend FALLA_A_SISTEMA
code_macros = sorted(list(set(FALLA_A_SISTEMA.values())))
print(f"\nBackend FALLA_A_SISTEMA macros ({len(code_macros)}): {code_macros}")
print("\nBackend fallas por macro:")
from collections import Counter
counts_backend = Counter(FALLA_A_SISTEMA.values())
for m, c in counts_backend.items():
    print(f"  {m}: {c} clases")

# 8. Check which classes map to CARROCERIA_NEUMATICA vs CARROCERIA_CONFORT
print("\nClases con macro en Fase10 que son CARROCERIA_NEUMATICA o CARROCERIA_CONFORT:")
for c in df_f10['clase_objetivo'].unique():
    f10_m = df_f10[df_f10['clase_objetivo'] == c]['macro_sistema'].iloc[0]
    orig_m = df_orig[df_orig['falla'] == c]['sistema'].iloc[0] if c in df_orig['falla'].values else "NO_EN_ORIG"
    code_m = FALLA_A_SISTEMA.get(c, "NO_EN_CODE")
    if "CARROCERIA" in str(f10_m) or "CARROCERIA" in str(orig_m) or "CARROCERIA" in str(code_m) or "CONFORT" in str(f10_m) or "NEUMATICA" in str(f10_m):
        print(f"  Clase: '{c}'")
        print(f"    Fase10 macro:  {f10_m}")
        print(f"    Original macro: {orig_m}")
        print(f"    Backend macro:  {code_m}")
