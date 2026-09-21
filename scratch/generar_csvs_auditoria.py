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

# Load sources
df_orig = pd.read_csv(base_dir / "machine_learning/data/dataset_sintomas_limpio.csv")
df_f10 = pd.read_csv(base_dir / "machine_learning/data/fase10/dataset_fase10_master_v1_1_2440.csv")
df_tr10 = pd.read_csv(base_dir / "machine_learning/data/fase10/train10_v1.csv")
df_dev10 = pd.read_csv(base_dir / "machine_learning/data/fase10/dev10_v1.csv")

f83_model = joblib.load(base_dir / "machine_learning/models/modelo_diagnostico.pkl")
c1_model = joblib.load(base_dir / "machine_learning/training/fase10/candidates/C1/modelo_diagnostico_c1.pkl")

# Canonical order (1..61)
unique_f10_ordered = []
for c in df_f10['clase_objetivo']:
    if c not in unique_f10_ordered:
        unique_f10_ordered.append(c)

orig_set = set(df_orig['falla'].unique())
f10_set = set(df_f10['clase_objetivo'].unique())
tr10_set = set(df_tr10['clase_objetivo'].unique())
dev10_set = set(df_dev10['clase_objetivo'].unique())
f83_set = set(f83_model.classes_)
c1_set = set(c1_model.classes_)
code_set = set(FALLA_A_SISTEMA.keys())

# Value counts
cnt_orig = df_orig['falla'].value_counts().to_dict()
cnt_f10 = df_f10['clase_objetivo'].value_counts().to_dict()
cnt_tr10 = df_tr10['clase_objetivo'].value_counts().to_dict()
cnt_dev10 = df_dev10['clase_objetivo'].value_counts().to_dict()

# 1. AUDITORIA_TAXONOMIA_61_FASE10.csv
rows_audit = []
for idx, c in enumerate(unique_f10_ordered, 1):
    macro = FALLA_A_SISTEMA.get(c, df_f10[df_f10['clase_objetivo'] == c]['macro_sistema'].iloc[0])
    m_orig = c in orig_set
    m_f10 = c in f10_set
    m_tr10 = c in tr10_set
    m_dev10 = c in dev10_set
    m_f83 = c in f83_set
    m_c1 = c in c1_set
    
    obs = "CONFORME_EXACTO" if (m_orig and m_f10 and m_tr10 and m_dev10 and m_f83 and m_c1) else "DISCREPANCIA_DETECTADA"
    
    rows_audit.append({
        "numero_clase": idx,
        "etiqueta_canonica": c,
        "macro_canonica": macro,
        "train_original_match": "SI" if m_orig else "NO",
        "fase10_match": "SI" if m_f10 else "NO",
        "train10_match": "SI" if m_tr10 else "NO",
        "dev10_match": "SI" if m_dev10 else "NO",
        "f83_match": "SI" if m_f83 else "NO",
        "c1_match": "SI" if m_c1 else "NO",
        "observacion": obs
    })

df_auditoria_61 = pd.DataFrame(rows_audit)
out_dir = base_dir / "machine_learning/data/fase10/auditoria_etapa31"
out_dir.mkdir(parents=True, exist_ok=True)
df_auditoria_61.to_csv(out_dir / "AUDITORIA_TAXONOMIA_61_FASE10.csv", index=False, encoding="utf-8")
df_auditoria_61.to_csv(base_dir / "AUDITORIA_TAXONOMIA_61_FASE10.csv", index=False, encoding="utf-8")
print(f"Generado AUDITORIA_TAXONOMIA_61_FASE10.csv ({len(df_auditoria_61)} filas)")

# 2. MAPEO_TAXONOMIAS_FASE10.csv
rows_mapeo = []
# All unique labels across everything (which is exactly 61)
all_unique_labels = unique_f10_ordered

for c in all_unique_labels:
    macro = FALLA_A_SISTEMA.get(c, "NO_EN_CODIGO")
    rows_mapeo.append({
        "label": c,
        "en_train_original": "SI" if c in orig_set else "NO",
        "en_fase10": "SI" if c in f10_set else "NO",
        "en_train10": "SI" if c in tr10_set else "NO",
        "en_dev10": "SI" if c in dev10_set else "NO",
        "en_f83": "SI" if c in f83_set else "NO",
        "en_c1": "SI" if c in c1_set else "NO",
        "en_codigo": "SI" if c in code_set else "NO",
        "macro": macro,
        "cantidad_train_original": cnt_orig.get(c, 0),
        "cantidad_fase10": cnt_f10.get(c, 0),
        "cantidad_train10": cnt_tr10.get(c, 0),
        "cantidad_dev10": cnt_dev10.get(c, 0)
    })

df_mapeo = pd.DataFrame(rows_mapeo)
df_mapeo.to_csv(out_dir / "MAPEO_TAXONOMIAS_FASE10.csv", index=False, encoding="utf-8")
df_mapeo.to_csv(base_dir / "MAPEO_TAXONOMIAS_FASE10.csv", index=False, encoding="utf-8")
print(f"Generado MAPEO_TAXONOMIAS_FASE10.csv ({len(df_mapeo)} filas)")
