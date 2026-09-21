import sys
import pickle
import pandas as pd
from pathlib import Path

base_dir = Path('.').resolve()
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))
if str(base_dir / "backend") not in sys.path:
    sys.path.insert(0, str(base_dir / "backend"))

# 1. TRAIN original 6189
df_orig = pd.read_csv(base_dir / "machine_learning/data/dataset_sintomas_limpio.csv")
print(f"Original 6189 shape: {df_orig.shape}, columns: {list(df_orig.columns)}")
orig_classes = sorted(df_orig['falla'].unique())
print(f"Original unique fallas: {len(orig_classes)}")

# 2. Fase 10 v1_1
p_f10 = base_dir / "machine_learning/data/fase10/dataset_fase10_master_v1_1_2440.csv"
if not p_f10.exists():
    p_f10 = base_dir / "machine_learning/data/fase10/dataset_fase10_master.csv"
df_f10 = pd.read_csv(p_f10)
print(f"Fase10 master shape: {df_f10.shape}, columns: {list(df_f10.columns)}")
f10_col = 'clase_objetivo' if 'clase_objetivo' in df_f10.columns else 'falla'
f10_classes = sorted(df_f10[f10_col].unique())
print(f"Fase10 unique classes: {len(f10_classes)}")

# 3. TRAIN10
df_tr10 = pd.read_csv(base_dir / "machine_learning/data/fase10/train10_v1.csv")
print(f"TRAIN10 shape: {df_tr10.shape}, columns: {list(df_tr10.columns)}")
tr10_col = 'clase_objetivo' if 'clase_objetivo' in df_tr10.columns else 'falla'
tr10_classes = sorted(df_tr10[tr10_col].unique())
print(f"TRAIN10 unique classes: {len(tr10_classes)}")

# 4. DEV10
df_dev10 = pd.read_csv(base_dir / "machine_learning/data/fase10/dev10_v1.csv")
print(f"DEV10 shape: {df_dev10.shape}, columns: {list(df_dev10.columns)}")
dev10_col = 'clase_objetivo' if 'clase_objetivo' in df_dev10.columns else 'falla'
dev10_classes = sorted(df_dev10[dev10_col].unique())
print(f"DEV10 unique classes: {len(dev10_classes)}")

import joblib

# 5. F8.3 classes
f83_model = joblib.load(base_dir / "machine_learning/models/modelo_diagnostico.pkl")
f83_classes = sorted(list(f83_model.classes_))
print(f"F8.3 unique classes: {len(f83_classes)}")

# 6. C1 classes
c1_model = joblib.load(base_dir / "machine_learning/training/fase10/candidates/C1/modelo_diagnostico_c1.pkl")
c1_classes = sorted(list(c1_model.classes_))
print(f"C1 unique classes: {len(c1_classes)}")

# 7. Backend taxonomy
from backend.src.core.diagnostico.taxonomia_sistemas import FALLA_A_SISTEMA
code_classes = sorted(list(FALLA_A_SISTEMA.keys()))
print(f"Backend FALLA_A_SISTEMA classes: {len(code_classes)}")
