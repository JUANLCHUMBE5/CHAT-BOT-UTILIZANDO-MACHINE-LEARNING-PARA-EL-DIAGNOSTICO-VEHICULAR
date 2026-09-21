import sys
import unicodedata
import re
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

base_dir = Path('.').resolve()

# Load F8.3 train dataset
df_orig_all = pd.read_csv(base_dir / "machine_learning/data/dataset_sintomas_limpio.csv")
print(f"F8.3 Train (all 6189) shape: {df_orig_all.shape}")

# Load DEV10
df_dev10 = pd.read_csv(base_dir / "machine_learning/data/fase10/dev10_v1.csv")
dev_orig = df_dev10[df_dev10['synthetic_or_original'] == 'ORIGINAL'].copy()
print(f"DEV10 ORIGINAL shape: {dev_orig.shape}")

def norm_txt(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()

# Build sets from F8.3 train
exact_f83_train = set(df_orig_all['sintoma'].astype(str))
norm_f83_train = set(df_orig_all['sintoma'].apply(norm_txt))

# Fit TF-IDF on F8.3 train for near-duplicate checking
vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
X_f83 = vec.fit_transform(df_orig_all['sintoma'].apply(norm_txt))
X_dev = vec.transform(dev_orig['texto_usuario'].apply(norm_txt))

# Cosine similarity for each dev row against all f83
sim_matrix = cosine_similarity(X_dev, X_f83)

results = []
n_exact = 0
n_norm = 0
n_near = 0
n_unseen = 0

for i, (_, row) in enumerate(dev_orig.iterrows()):
    txt_raw = str(row['texto_usuario'])
    txt_n = norm_txt(txt_raw)
    
    is_exact = txt_raw in exact_f83_train
    is_norm = txt_n in norm_f83_train
    max_sim = float(sim_matrix[i].max())
    is_near = max_sim >= 0.85
    
    if is_exact:
        cat = "EXACT_SEEN"
        n_exact += 1
    elif is_norm:
        cat = "NORMALIZED_SEEN"
        n_norm += 1
    elif is_near:
        cat = "NEAR_DUPLICATE_SEEN"
        n_near += 1
    else:
        cat = "TRULY_UNSEEN"
        n_unseen += 1
        
    results.append({
        "id": row['id'],
        "clase_objetivo": row['clase_objetivo'],
        "source_row_id": row['source_row_id'],
        "is_exact_seen": is_exact,
        "is_norm_seen": is_norm,
        "max_cosine_sim_f83": round(max_sim, 4),
        "category": cat
    })

df_res = pd.DataFrame(results)
out_csv = base_dir / "machine_learning/data/fase10/auditoria_etapa31/AUDITORIA_DEV10_ORIGINAL_SEEN.csv"
df_res.to_csv(out_csv, index=False)
# Also save at workspace root for convenience
df_res.to_csv(base_dir / "AUDITORIA_DEV10_ORIGINAL_SEEN.csv", index=False)

n_total = len(dev_orig)
print(f"\n--- AUDITORIA DEV10 ORIGINAL (n={n_total}) ---")
print(f"Exact Seen by F8.3 Train:       {n_exact:4d} ({n_exact/n_total*100:6.2f}%)")
print(f"Normalized Seen (not exact):    {n_norm:4d} ({n_norm/n_total*100:6.2f}%)")
print(f"Near Duplicate Seen (sim>=0.85):{n_near:4d} ({n_near/n_total*100:6.2f}%)")
print(f"Truly Unseen:                   {n_unseen:4d} ({n_unseen/n_total*100:6.2f}%)")

# Check source_row_id match
source_ids_valid = dev_orig['source_row_id'].astype(int).isin(range(len(df_orig_all))).all()
print(f"All 1237 source_row_id point directly to F8.3 training rows? {source_ids_valid}")
