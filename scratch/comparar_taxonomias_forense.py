import sys
import unicodedata
import pandas as pd
import joblib
from pathlib import Path

base_dir = Path('.').resolve()
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))
if str(base_dir / "backend") not in sys.path:
    sys.path.insert(0, str(base_dir / "backend"))

from backend.src.core.diagnostico.taxonomia_sistemas import FALLA_A_SISTEMA

# Load datasets
df_orig = pd.read_csv(base_dir / "machine_learning/data/dataset_sintomas_limpio.csv")
orig_classes = sorted(list(df_orig['falla'].unique()))

p_f10 = base_dir / "machine_learning/data/fase10/dataset_fase10_master_v1_1_2440.csv"
if not p_f10.exists():
    p_f10 = base_dir / "machine_learning/data/fase10/dataset_fase10_master.csv"
df_f10 = pd.read_csv(p_f10)
f10_col = 'clase_objetivo' if 'clase_objetivo' in df_f10.columns else 'falla'
f10_classes = sorted(list(df_f10[f10_col].unique()))

df_tr10 = pd.read_csv(base_dir / "machine_learning/data/fase10/train10_v1.csv")
tr10_col = 'clase_objetivo' if 'clase_objetivo' in df_tr10.columns else 'falla'
tr10_classes = sorted(list(df_tr10[tr10_col].unique()))

df_dev10 = pd.read_csv(base_dir / "machine_learning/data/fase10/dev10_v1.csv")
dev10_col = 'clase_objetivo' if 'clase_objetivo' in df_dev10.columns else 'falla'
dev10_classes = sorted(list(df_dev10[dev10_col].unique()))

f83_model = joblib.load(base_dir / "machine_learning/models/modelo_diagnostico.pkl")
f83_classes = sorted(list(f83_model.classes_))

c1_model = joblib.load(base_dir / "machine_learning/training/fase10/candidates/C1/modelo_diagnostico_c1.pkl")
c1_classes = sorted(list(c1_model.classes_))

code_classes = sorted(list(FALLA_A_SISTEMA.keys()))

taxonomies = {
    "train_original": orig_classes,
    "fase10": f10_classes,
    "train10": tr10_classes,
    "dev10": dev10_classes,
    "f83": f83_classes,
    "c1": c1_classes,
    "codigo": code_classes
}

# Save individual CSVs
out_dir = base_dir / "machine_learning/data/fase10/auditoria_etapa31"
out_dir.mkdir(parents=True, exist_ok=True)

for name, classes in taxonomies.items():
    csv_p = out_dir / f"taxonomia_{name}.csv"
    pd.DataFrame({"clase": classes}).to_csv(csv_p, index=False, encoding="utf-8")
    print(f"Saved {csv_p} (n={len(classes)})")

print("\n" + "="*80)
print("COMPARACIÓN EXACTA LITERAL (CASE SENSITIVE, CON ACENTOS, EXACTO):")
print("="*80)

def set_diff(a_name, a_set, b_name, b_set):
    diff = sorted(list(set(a_set) - set(b_set)))
    print(f"{a_name} - {b_name} (count={len(diff)}):")
    for item in diff:
        print(f"  + {item}")
    return diff

set_diff("TRAIN_ORIGINAL", orig_classes, "FASE10", f10_classes)
set_diff("FASE10", f10_classes, "TRAIN_ORIGINAL", orig_classes)

set_diff("TRAIN10", tr10_classes, "FASE10", f10_classes)
set_diff("FASE10", f10_classes, "TRAIN10", tr10_classes)

set_diff("DEV10", dev10_classes, "FASE10", f10_classes)
set_diff("FASE10", f10_classes, "DEV10", dev10_classes)

set_diff("F8.3", f83_classes, "FASE10", f10_classes)
set_diff("FASE10", f10_classes, "F8.3", f83_classes)

set_diff("C1", c1_classes, "FASE10", f10_classes)
set_diff("FASE10", f10_classes, "C1", c1_classes)

set_diff("CODIGO", code_classes, "FASE10", f10_classes)
set_diff("FASE10", f10_classes, "CODIGO", code_classes)

# Now check pairwise equality
print("\n" + "="*80)
print("EVALUACIÓN DE IGUALDAD EXACTA ENTRE TODOS:")
print("="*80)
all_same = (orig_classes == f10_classes == tr10_classes == dev10_classes == f83_classes == c1_classes == code_classes)
print(f"¿Son todas exactamente iguales literalmente?: {all_same}")
if not all_same:
    for name, cl in taxonomies.items():
        print(f"  {name} == FASE10? {cl == f10_classes}")
        print(f"  {name} == CODIGO? {cl == code_classes}")
        print(f"  {name} == F8.3? {cl == f83_classes}")
