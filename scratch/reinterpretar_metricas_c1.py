import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import f1_score

base_dir = Path('.').resolve()
df_dev = pd.read_csv(base_dir / "machine_learning/data/fase10/fase10_f83_vs_c1_dev10.csv")
print(f"Loaded paired dev predictions: {len(df_dev)} rows")
print(df_dev.columns)

# Also load leakage info to flag near-duplicates
df_leak = pd.read_csv(base_dir / "machine_learning/data/fase10/fase10_leakage_train_dev.csv")
leak_ids = set(df_leak['dev_id'])

# Define subsets:
# 1. Todo DEV10 (n=1725)
# 2. SINTETICO FASE 10 (n=488) -> Truly unseen by both F8.3 and C1 train
# 3. ORIGINAL TOTAL (n=1237) -> 100% Seen by F8.3 train, unseen by C1 train
#    3a. ORIGINAL con near-duplicate en TRAIN10 (n=327)
#    3b. ORIGINAL sin near-duplicate en TRAIN10 (n=910)

def evaluate_subset(name, subset_df):
    n = len(subset_df)
    if n == 0:
        print(f"Subset {name}: n=0")
        return {}
    
    top1_f83 = subset_df['correct_f83'].mean()
    top1_c1  = subset_df['correct_c1'].mean()
    
    # Macro F1 (only on classes present in subset)
    present_classes = sorted(subset_df['real'].unique())
    mf1_f83 = f1_score(subset_df['real'], subset_df['pred_f83'], labels=present_classes, average='macro', zero_division=0)
    mf1_c1  = f1_score(subset_df['real'], subset_df['pred_c1'], labels=present_classes, average='macro', zero_division=0)
    
    print(f"\n--- {name} (n={n}) ---")
    print(f"  Clases presentes: {len(present_classes)}")
    print(f"  F8.3 Top-1: {top1_f83*100:6.2f}% | C1 Top-1: {top1_c1*100:6.2f}% | DELTA: {(top1_c1 - top1_f83)*100:+6.2f}%")
    print(f"  F8.3 MF1:   {mf1_f83*100:6.2f}% | C1 MF1:   {mf1_c1*100:6.2f}% | DELTA: {(mf1_c1 - mf1_f83)*100:+6.2f}%")
    
    return {
        "subset": name,
        "n": n,
        "top1_f83": round(float(top1_f83), 4),
        "top1_c1": round(float(top1_c1), 4),
        "delta_top1": round(float(top1_c1 - top1_f83), 4),
        "mf1_f83": round(float(mf1_f83), 4),
        "mf1_c1": round(float(mf1_c1), 4),
        "delta_mf1": round(float(mf1_c1 - mf1_f83), 4),
    }

subsets = {
    "DEV10 GLOBAL": df_dev,
    "ORIGINAL VISTO POR F8.3 (TOTAL ORIGINAL)": df_dev[df_dev['source'] == 'ORIGINAL'],
    "ORIGINAL REALMENTE NO VISTO POR F8.3": df_dev[(df_dev['source'] == 'ORIGINAL') & False], # empty: n=0
    "ORIGINAL CON NEAR-DUPLICATE EN TRAIN10": df_dev[df_dev['id'].isin(leak_ids)],
    "ORIGINAL SIN NEAR-DUPLICATE EN TRAIN10 (STRICT CLEAN ORIGINAL)": df_dev[(df_dev['source'] == 'ORIGINAL') & (~df_dev['id'].isin(leak_ids))],
    "SINTETICO FASE 10 (NO VISTO POR F8.3 NI C1 TRAIN)": df_dev[df_dev['source'] == 'SINTETICO'],
    "SINTETICO L1": df_dev[(df_dev['source'] == 'SINTETICO') & (df_dev['nivel'] == 'L1')],
    "SINTETICO L2": df_dev[(df_dev['source'] == 'SINTETICO') & (df_dev['nivel'] == 'L2')],
    "SINTETICO L3": df_dev[(df_dev['source'] == 'SINTETICO') & (df_dev['nivel'] == 'L3')],
}

results = []
for name, sub in subsets.items():
    if len(sub) > 0:
        results.append(evaluate_subset(name, sub))

df_sub_res = pd.DataFrame(results)
print("\n" + "="*80)
print("TABLA COMPARATIVA REINTERPRETADA:")
print("="*80)
print(df_sub_res.to_string(index=False))
