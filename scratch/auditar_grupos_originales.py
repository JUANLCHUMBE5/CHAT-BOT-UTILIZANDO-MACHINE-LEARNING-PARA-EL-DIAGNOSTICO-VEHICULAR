import sys
import unicodedata
import re
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

base_dir = Path('.').resolve()

# Load TRAIN10 and DEV10
df_tr10 = pd.read_csv(base_dir / "machine_learning/data/fase10/train10_v1.csv")
df_dev10 = pd.read_csv(base_dir / "machine_learning/data/fase10/dev10_v1.csv")

# Filter original rows
tr_orig = df_tr10[df_tr10['synthetic_or_original'] == 'ORIGINAL'].copy()
dev_orig = df_dev10[df_dev10['synthetic_or_original'] == 'ORIGINAL'].copy()

print(f"TRAIN10 original rows: {len(tr_orig)}")
print(f"DEV10 original rows:   {len(dev_orig)}")

# Reconstruct all 6189 original with their assigned id_grupo
df_orig_combined = pd.concat([tr_orig, dev_orig], ignore_index=True)
print(f"Total original combined: {len(df_orig_combined)}")

# Group analysis
grp_sizes = df_orig_combined.groupby('id_grupo').size()
grp_n_classes = df_orig_combined.groupby('id_grupo')['clase_objetivo'].nunique()

n_groups = len(grp_sizes)
n_multi_row = (grp_sizes > 1).sum()
n_single_row = (grp_sizes == 1).sum()
max_size = grp_sizes.max()
multi_class_grps = (grp_n_classes > 1).sum()

print("\n--- RESUMEN DE GRUPOS ORIGINALES ---")
print(f"Total de grupos originales: {n_groups}")
print(f"Grupos con 1 registro:      {n_single_row} ({n_single_row/n_groups*100:.2f}%)")
print(f"Grupos con >1 registro:     {n_multi_row} ({n_multi_row/n_groups*100:.2f}%)")
print(f"Tamaño máximo de grupo:     {max_size}")
print(f"Grupos multi-clase:         {multi_class_grps}")

print("\nDistribución de tamaños de grupo:")
print(grp_sizes.value_counts().sort_index())

# Check if any id_grupo crosses train and dev
tr_grps = set(tr_orig['id_grupo'])
dev_grps = set(dev_orig['id_grupo'])
overlap_grps = tr_grps.intersection(dev_grps)
print(f"\nGrupos con id_grupo compartido entre TRAIN10 y DEV10: {len(overlap_grps)}")

# Now investigate the 327 reported near-duplicate pairs within original dataset!
# Where did the 327 pairs come from? Let's check fase10_leakage_train_dev.csv or SPLIT10_MANIFEST.json
p_leak = base_dir / "machine_learning/data/fase10/fase10_leakage_train_dev.csv"
if p_leak.exists():
    df_leak = pd.read_csv(p_leak)
    print(f"\nArchivo fase10_leakage_train_dev.csv existente: {len(df_leak)} filas")
    print(df_leak.head())
else:
    print("\nCalculando near-duplicates entre TRAIN10 original y DEV10 original (TF-IDF cosine sim >= 0.85)...")

def norm_txt(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()

vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
X_tr = vec.fit_transform(tr_orig['texto_usuario'].apply(norm_txt))
X_dev = vec.transform(dev_orig['texto_usuario'].apply(norm_txt))

sim = cosine_similarity(X_dev, X_tr)

# Find pairs with sim >= 0.85
cross_pairs = []
for dev_idx in range(len(dev_orig)):
    matches = np.where(sim[dev_idx] >= 0.85)[0]
    for tr_idx in matches:
        cross_pairs.append({
            "dev_id": dev_orig.iloc[dev_idx]['id'],
            "dev_row_id": dev_orig.iloc[dev_idx]['source_row_id'],
            "dev_clase": dev_orig.iloc[dev_idx]['clase_objetivo'],
            "dev_grupo": dev_orig.iloc[dev_idx]['id_grupo'],
            "train_id": tr_orig.iloc[tr_idx]['id'],
            "train_row_id": tr_orig.iloc[tr_idx]['source_row_id'],
            "train_clase": tr_orig.iloc[tr_idx]['clase_objetivo'],
            "train_grupo": tr_orig.iloc[tr_idx]['id_grupo'],
            "cosine_sim": round(float(sim[dev_idx, tr_idx]), 4),
            "mismo_target": bool(dev_orig.iloc[dev_idx]['clase_objetivo'] == tr_orig.iloc[tr_idx]['clase_objetivo']),
            "dev_texto": dev_orig.iloc[dev_idx]['texto_usuario'],
            "train_texto": tr_orig.iloc[tr_idx]['texto_usuario']
        })

df_cross = pd.DataFrame(cross_pairs)
print(f"\nTotal pares near-duplicate cruzando TRAIN10 y DEV10 (sim >= 0.85): {len(df_cross)}")
if len(df_cross) > 0:
    print(f"  Pares con misma clase: {df_cross['mismo_target'].sum()}")
    print(f"  Pares con distinta clase: {(~df_cross['mismo_target']).sum()}")

# Export AUDITORIA_GRUPOS_ORIGINALES.csv
# Group statistics export
grp_stats = []
for gid, grp_df in df_orig_combined.groupby('id_grupo'):
    in_train = gid in tr_grps
    in_dev = gid in dev_grps
    grp_stats.append({
        "id_grupo": gid,
        "tamano": len(grp_df),
        "clase_objetivo": grp_df['clase_objetivo'].iloc[0],
        "n_clases_distintas": grp_df['clase_objetivo'].nunique(),
        "split_asignado": "TRAIN" if in_train and not in_dev else ("DEV" if in_dev and not in_train else "AMBOS"),
        "ejemplo_texto": grp_df['texto_usuario'].iloc[0]
    })

df_grp_stats = pd.DataFrame(grp_stats)
out_csv = base_dir / "machine_learning/data/fase10/auditoria_etapa31/AUDITORIA_GRUPOS_ORIGINALES.csv"
df_grp_stats.to_csv(out_csv, index=False, encoding="utf-8")
df_grp_stats.to_csv(base_dir / "AUDITORIA_GRUPOS_ORIGINALES.csv", index=False, encoding="utf-8")
print(f"\nGuardado AUDITORIA_GRUPOS_ORIGINALES.csv ({len(df_grp_stats)} filas)")
