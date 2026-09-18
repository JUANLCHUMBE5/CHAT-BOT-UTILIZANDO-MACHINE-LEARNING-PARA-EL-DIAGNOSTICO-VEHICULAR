import sys
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

base_dir = Path('.').resolve()
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

# 1. Load data
dev_fix_path = base_dir / "machine_learning/data/fase10/dev10_v1_1_macrofix.csv"
df_dev = pd.read_csv(dev_fix_path)

# Load existing error and comparison files from Stage 3
err_path = base_dir / "machine_learning/data/fase10/fase10_c1_dev10_errors.csv"
df_errors = pd.read_csv(err_path)

vs_path = base_dir / "machine_learning/data/fase10/fase10_f83_vs_c1_dev10.csv"
df_vs = pd.read_csv(vs_path)

# Load macrofix model to get macro predictions on DEV10
dir_c1 = base_dir / "machine_learning/training/fase10/candidates/C1"
vec_c1 = joblib.load(dir_c1 / "vectorizador_c1.pkl")
cal_sist_fix = joblib.load(dir_c1 / "modelo_sistema_c1_macrofix.pkl")

X_dev_vec = vec_c1.transform(df_dev["texto_usuario"].astype(str))
macro_preds_dev = cal_sist_fix.predict(X_dev_vec)
df_dev["pred_macro_fix"] = macro_preds_dev
df_dev["macro_correct"] = (df_dev["macro_sistema"] == macro_preds_dev).astype(int)

# Map dev predictions and top3 into df_dev
# Notice df_errors has id, pred, top3, confidence
err_dict = {}
for idx, r in df_errors.iterrows():
    parts = [p.strip() for p in str(r['top3']).split('|')]
    top1 = parts[0] if len(parts) > 0 else r['pred']
    top2 = parts[1] if len(parts) > 1 else ""
    top3 = parts[2] if len(parts) > 2 else ""
    err_dict[r['id']] = {
        'pred_top1': top1,
        'top2': top2,
        'top3': top3,
        'top3_full': str(r['top3']),
        'confidence': float(r['confidence']),
        'in_top3': bool(r['real'] in [top1, top2, top3])
    }

# Also from df_vs we know correct_c1, correct_f83, pred_c1, pred_f83
vs_dict = {}
for idx, r in df_vs.iterrows():
    vs_dict[r['id']] = {
        'correct_c1': int(r['correct_c1']),
        'correct_f83': int(r['correct_f83']),
        'pred_c1': r['pred_c1'],
        'pred_f83': r['pred_f83'],
        'conf_c1': float(r['confidence_c1']),
        'conf_f83': float(r['confidence_f83'])
    }

# Merge into df_dev
df_dev['correct_c1'] = df_dev['id'].map(lambda x: vs_dict[x]['correct_c1'] if x in vs_dict else 0)
df_dev['correct_f83'] = df_dev['id'].map(lambda x: vs_dict[x]['correct_f83'] if x in vs_dict else 0)
df_dev['pred_c1'] = df_dev['id'].map(lambda x: vs_dict[x]['pred_c1'] if x in vs_dict else "")
df_dev['pred_f83'] = df_dev['id'].map(lambda x: vs_dict[x]['pred_f83'] if x in vs_dict else "")
df_dev['conf_c1'] = df_dev['id'].map(lambda x: vs_dict[x]['conf_c1'] if x in vs_dict else 0.0)
df_dev['conf_f83'] = df_dev['id'].map(lambda x: vs_dict[x]['conf_f83'] if x in vs_dict else 0.0)

# For top3 in df_dev: if correct_c1 == 1, in_top3 is True, top2/top3 can be retrieved if needed
# If error, in_top3 from err_dict
def get_in_top3(row):
    if row['correct_c1'] == 1:
        return True
    if row['id'] in err_dict:
        return err_dict[row['id']]['in_top3']
    return False

df_dev['in_top3_c1'] = df_dev.apply(get_in_top3, axis=1)

def get_top2(row):
    if row['id'] in err_dict:
        return err_dict[row['id']]['top2']
    return ""

def get_top3_str(row):
    if row['id'] in err_dict:
        return err_dict[row['id']]['top3']
    return ""

df_dev['top2_c1'] = df_dev.apply(get_top2, axis=1)
df_dev['top3_c1'] = df_dev.apply(get_top3_str, axis=1)

print("Datos DEV10 cargados y cruzados:")
print(f"Total DEV10: {len(df_dev)}")
print(f"Sintético: {len(df_dev[df_dev['synthetic_or_original'] == 'SINTETICO'])}")
print(f"Original:  {len(df_dev[df_dev['synthetic_or_original'] == 'ORIGINAL'])}")

# ==============================================================================
# 5. ERROR TAXONOMY DEV SYNTHETIC (144 errors)
# ==============================================================================
df_synth_err = df_dev[(df_dev['synthetic_or_original'] == 'SINTETICO') & (df_dev['correct_c1'] == 0)].copy()
print(f"\nErrores sintéticos a clasificar: {len(df_synth_err)} (esperado: 144)")

def clasificar_error(row):
    # Hierarchy for single primary category:
    # 1. AMBIGUO_L1: Level is L1
    if row['nivel_informacion'] == 'L1':
        return 'AMBIGUO_L1'
    # 2. ERROR_MACRO: The macro-model predicted the wrong macro system
    if row['macro_sistema'] != row['pred_macro_fix']:
        return 'ERROR_MACRO'
    # 3. HIGH_CONF_WRONG: Confidence >= 0.80 and wrong
    if row['conf_c1'] >= 0.80:
        return 'HIGH_CONF_WRONG'
    # 4. TOP3_COMPATIBLE: Real class is present in top 3
    if row['in_top3_c1']:
        return 'TOP3_COMPATIBLE'
    # 5. SHORTCUT: DTC or brand specific misleading term
    txt = str(row['texto_usuario']).lower()
    if pd.notna(row['dtc']) and str(row['dtc']).strip() != '' and str(row['dtc']).strip() != 'nan':
        return 'SHORTCUT'
    # 6. Default: ERROR_MODELO_CLARO
    return 'ERROR_MODELO_CLARO'

df_synth_err['categoria_error'] = df_synth_err.apply(clasificar_error, axis=1)

# Format for fase10_c1_error_taxonomy_dev_synthetic.csv
cols_err_tax = [
    'id', 'id_grupo', 'texto_usuario', 'nivel_informacion', 'clase_objetivo',
    'pred_c1', 'top2_c1', 'top3_c1', 'conf_c1', 'macro_sistema', 'pred_macro_fix',
    'es_contrastivo', 'clase_contrastiva', 'dtc', 'categoria_error'
]
df_err_export = df_synth_err[cols_err_tax].rename(columns={
    'nivel_informacion': 'nivel',
    'clase_objetivo': 'clase_real',
    'pred_c1': 'pred_top1',
    'top2_c1': 'top2',
    'top3_c1': 'top3',
    'conf_c1': 'confidence',
    'macro_sistema': 'macro_real',
    'pred_macro_fix': 'macro_pred'
})

df_err_export.to_csv(base_dir / "fase10_c1_error_taxonomy_dev_synthetic.csv", index=False, encoding="utf-8")
df_err_export.to_csv(base_dir / "machine_learning/data/fase10/fase10_c1_error_taxonomy_dev_synthetic.csv", index=False, encoding="utf-8")
print(f"Exportado fase10_c1_error_taxonomy_dev_synthetic.csv ({len(df_err_export)} filas)")
print("Distribución de categorías primarias de error:")
print(df_err_export['categoria_error'].value_counts())

# ==============================================================================
# 6. L1 ANALYSIS (n=122)
# ==============================================================================
df_l1 = df_dev[(df_dev['synthetic_or_original'] == 'SINTETICO') & (df_dev['nivel_informacion'] == 'L1')].copy()
n_l1 = len(df_l1)
top1_l1_acc = df_l1['correct_c1'].mean()
top3_l1_acc = df_l1['in_top3_c1'].mean()
macro_l1_acc = df_l1['macro_correct'].mean()

# Macro F1 for L1
_, _, macro_f1_l1, _ = precision_recall_fscore_support(
    df_l1['macro_sistema'], df_l1['pred_macro_fix'], average='macro', zero_division=0
)

mean_conf_l1 = df_l1['conf_c1'].mean()
median_conf_l1 = df_l1['conf_c1'].median()
pct_conf_lt_60 = (df_l1['conf_c1'] < 0.60).mean()
pct_conf_lt_70 = (df_l1['conf_c1'] < 0.70).mean()
pct_conf_ge_80 = (df_l1['conf_c1'] >= 0.80).mean()

l1_correct = df_l1['correct_c1'].sum()
l1_wrong = n_l1 - l1_correct
l1_top3_rec = df_l1[df_l1['correct_c1'] == 0]['in_top3_c1'].sum()
l1_macro_corr = df_l1['macro_correct'].sum()

# Export L1 table
cols_l1 = [
    'id', 'id_grupo', 'texto_usuario', 'clase_objetivo', 'pred_c1',
    'correct_c1', 'in_top3_c1', 'conf_c1', 'macro_sistema', 'pred_macro_fix', 'macro_correct'
]
df_l1[cols_l1].to_csv(base_dir / "fase10_c1_l1_analysis.csv", index=False, encoding="utf-8")
df_l1[cols_l1].to_csv(base_dir / "machine_learning/data/fase10/fase10_c1_l1_analysis.csv", index=False, encoding="utf-8")

print(f"\nANÁLISIS L1 (n={n_l1}):")
print(f"  Top-1 Accuracy: {top1_l1_acc*100:.2f}% ({l1_correct}/{n_l1})")
print(f"  Top-3 Accuracy: {top3_l1_acc*100:.2f}% ({df_l1['in_top3_c1'].sum()}/{n_l1})")
print(f"  Top-3 Recuperados en errores: {l1_top3_rec}/{l1_wrong} ({l1_top3_rec/l1_wrong*100:.1f}%)")
print(f"  Macro Accuracy: {macro_l1_acc*100:.2f}% ({l1_macro_corr}/{n_l1})")
print(f"  Macro F1: {macro_f1_l1*100:.2f}%")
print(f"  Confianza media: {mean_conf_l1:.4f} | Mediana: {median_conf_l1:.4f}")
print(f"  % Conf < 0.60: {pct_conf_lt_60*100:.1f}% | < 0.70: {pct_conf_lt_70*100:.1f}% | >= 0.80: {pct_conf_ge_80*100:.1f}%")

# ==============================================================================
# 7. L2 ANALYSIS (n=183)
# ==============================================================================
df_l2 = df_dev[(df_dev['synthetic_or_original'] == 'SINTETICO') & (df_dev['nivel_informacion'] == 'L2')].copy()
n_l2 = len(df_l2)
top1_l2_acc = df_l2['correct_c1'].mean()
top3_l2_acc = df_l2['in_top3_c1'].mean()
macro_l2_acc = df_l2['macro_correct'].mean()
_, _, macro_f1_l2, _ = precision_recall_fscore_support(
    df_l2['macro_sistema'], df_l2['pred_macro_fix'], average='macro', zero_division=0
)
l2_correct = df_l2['correct_c1'].sum()
l2_wrong = n_l2 - l2_correct
l2_top3_rec = df_l2[df_l2['correct_c1'] == 0]['in_top3_c1'].sum()
l2_clear_err = l2_wrong - l2_top3_rec

cols_l2 = [
    'id', 'id_grupo', 'texto_usuario', 'clase_objetivo', 'pred_c1',
    'correct_c1', 'in_top3_c1', 'conf_c1', 'macro_sistema', 'pred_macro_fix', 'macro_correct'
]
df_l2[cols_l2].to_csv(base_dir / "fase10_c1_l2_analysis.csv", index=False, encoding="utf-8")
df_l2[cols_l2].to_csv(base_dir / "machine_learning/data/fase10/fase10_c1_l2_analysis.csv", index=False, encoding="utf-8")

print(f"\nANÁLISIS L2 (n={n_l2}):")
print(f"  Top-1 Accuracy: {top1_l2_acc*100:.2f}% ({l2_correct}/{n_l2})")
print(f"  Top-3 Accuracy: {top3_l2_acc*100:.2f}% ({df_l2['in_top3_c1'].sum()}/{n_l2})")
print(f"  Top-3 Recuperados en errores: {l2_top3_rec}/{l2_wrong} ({l2_top3_rec/l2_wrong*100:.1f}%)")
print(f"  Errores claros (no en top3): {l2_clear_err}/{l2_wrong}")
print(f"  Macro Accuracy: {macro_l2_acc*100:.2f}% | Macro F1: {macro_f1_l2*100:.2f}%")

# ==============================================================================
# 8. L3 ANALYSIS (n=183) & HIGH CONF WRONG
# ==============================================================================
df_l3 = df_dev[(df_dev['synthetic_or_original'] == 'SINTETICO') & (df_dev['nivel_informacion'] == 'L3')].copy()
n_l3 = len(df_l3)
top1_l3_acc = df_l3['correct_c1'].mean()
top3_l3_acc = df_l3['in_top3_c1'].mean()
macro_l3_acc = df_l3['macro_correct'].mean()
_, _, macro_f1_l3, _ = precision_recall_fscore_support(
    df_l3['macro_sistema'], df_l3['pred_macro_fix'], average='macro', zero_division=0
)
l3_correct = df_l3['correct_c1'].sum()
l3_wrong = n_l3 - l3_correct
l3_top3_rec = df_l3[df_l3['correct_c1'] == 0]['in_top3_c1'].sum()
l3_clear_err = l3_wrong - l3_top3_rec

cols_l3 = [
    'id', 'id_grupo', 'texto_usuario', 'clase_objetivo', 'pred_c1',
    'correct_c1', 'in_top3_c1', 'conf_c1', 'macro_sistema', 'pred_macro_fix', 'macro_correct'
]
df_l3[cols_l3].to_csv(base_dir / "fase10_c1_l3_analysis.csv", index=False, encoding="utf-8")
df_l3[cols_l3].to_csv(base_dir / "machine_learning/data/fase10/fase10_c1_l3_analysis.csv", index=False, encoding="utf-8")

print(f"\nANÁLISIS L3 (n={n_l3}):")
print(f"  Top-1 Accuracy: {top1_l3_acc*100:.2f}% ({l3_correct}/{n_l3})")
print(f"  Top-3 Accuracy: {top3_l3_acc*100:.2f}% ({df_l3['in_top3_c1'].sum()}/{n_l3})")
print(f"  Top-3 Recuperados en errores: {l3_top3_rec}/{l3_wrong}")
print(f"  Errores claros (no en top3): {l3_clear_err}")

# High confidence wrong in all DEV10 (confidence >= 0.80 and correct_c1 == 0)
df_high_conf = df_dev[(df_dev['correct_c1'] == 0) & (df_dev['conf_c1'] >= 0.80)].copy()
cols_hc = [
    'id', 'synthetic_or_original', 'nivel_informacion', 'texto_usuario',
    'clase_objetivo', 'pred_c1', 'in_top3_c1', 'conf_c1', 'dtc', 'macro_sistema', 'pred_macro_fix'
]
df_high_conf[cols_hc].to_csv(base_dir / "fase10_c1_high_conf_wrong.csv", index=False, encoding="utf-8")
df_high_conf[cols_hc].to_csv(base_dir / "machine_learning/data/fase10/fase10_c1_high_conf_wrong.csv", index=False, encoding="utf-8")
print(f"\nHigh confidence wrong (>=0.80) en todo DEV10: {len(df_high_conf)} casos")
print(f"  En sintéticos: {len(df_high_conf[df_high_conf['synthetic_or_original'] == 'SINTETICO'])}")
print(f"  En originales: {len(df_high_conf[df_high_conf['synthetic_or_original'] == 'ORIGINAL'])}")
print(f"  L3 sintéticos con conf >= 0.80 erróneos: {len(df_high_conf[(df_high_conf['synthetic_or_original'] == 'SINTETICO') & (df_high_conf['nivel_informacion'] == 'L3')])}")
print(f"  Casos con conf >= 0.90 erróneos en todo DEV10: {len(df_dev[(df_dev['correct_c1'] == 0) & (df_dev['conf_c1'] >= 0.90)])}")

# ==============================================================================
# 9. TOP 3 RECOVERY SUMMARY
# ==============================================================================
# In synthetic: Top1 = 70.49% (344), Top3 = 89.34% (436). Total errors = 144.
# Recovered in top3 = 436 - 344 = 92 cases!
rec_l1 = df_l1[df_l1['correct_c1'] == 0]['in_top3_c1'].sum()
rec_l2 = df_l2[df_l2['correct_c1'] == 0]['in_top3_c1'].sum()
rec_l3 = df_l3[df_l3['correct_c1'] == 0]['in_top3_c1'].sum()
print(f"\nTOP-3 RECUPERACIÓN EN SINTÉTICOS:")
print(f"  Total recuperados en Top3: {rec_l1 + rec_l2 + rec_l3} / 144 ({((rec_l1 + rec_l2 + rec_l3)/144)*100:.1f}%)")
print(f"  En L1: {rec_l1} / {l1_wrong} ({rec_l1/l1_wrong*100:.1f}%)")
print(f"  En L2: {rec_l2} / {l2_wrong} ({rec_l2/l2_wrong*100:.1f}%)")
print(f"  En L3: {rec_l3} / {l3_wrong} ({rec_l3/l3_wrong*100:.1f}%)")

# ==============================================================================
# 10. CONTRASTIVE ANALYSIS (n=257 in DEV10)
# ==============================================================================
df_cont = df_dev[df_dev['es_contrastivo'] == 'SI'].copy()
n_cont = len(df_cont)
cont_top1_acc = df_cont['correct_c1'].mean()
cont_top3_acc = df_cont['in_top3_c1'].mean()

# Cases where pred_c1 == clase_contrastiva
df_cont_trap = df_cont[df_cont['pred_c1'] == df_cont['clase_contrastiva']].copy()
print(f"\nCONTRASTIVOS EN DEV10 (n={n_cont}):")
print(f"  Top-1: {cont_top1_acc*100:.2f}% | Top-3: {cont_top3_acc*100:.2f}%")
print(f"  Caídas en trampa contrastiva (pred == contrastiva): {len(df_cont_trap)} / {n_cont} ({len(df_cont_trap)/n_cont*100:.1f}%)")

# Group by real, contrastive pair
pair_counts = []
for (real, cont), grp in df_cont_trap.groupby(['clase_objetivo', 'clase_contrastiva']):
    pair_counts.append({
        'clase_real': real,
        'clase_contrastiva': cont,
        'cantidad_errores': len(grp),
        'niveles': ', '.join(grp['nivel_informacion'].value_counts().index.tolist()),
        'confianza_promedio': round(grp['conf_c1'].mean(), 4),
        'es_sintetico': (grp['synthetic_or_original'] == 'SINTETICO').sum(),
        'es_original': (grp['synthetic_or_original'] == 'ORIGINAL').sum()
    })
df_pairs = pd.DataFrame(pair_counts).sort_values(by='cantidad_errores', ascending=False)
df_pairs.to_csv(base_dir / "fase10_c1_contrastive_errors.csv", index=False, encoding="utf-8")
df_pairs.to_csv(base_dir / "machine_learning/data/fase10/fase10_c1_contrastive_errors.csv", index=False, encoding="utf-8")
print("\nTop pares contrastivos con confusión directa:")
print(df_pairs.head(8).to_string(index=False))

# ==============================================================================
# 12 & 13. CLASES DEGRADADAS / MEJORADAS EN UNSEEN SINTETICO (n=488)
# ==============================================================================
df_synth = df_dev[df_dev['synthetic_or_original'] == 'SINTETICO'].copy()
all_classes = sorted(df_dev['clase_objetivo'].unique())

class_stats = []
for c in all_classes:
    sub = df_synth[df_synth['clase_objetivo'] == c]
    supp = len(sub)
    if supp == 0:
        continue
    # recall
    rec_f83 = sub['correct_f83'].mean()
    rec_c1 = sub['correct_c1'].mean()
    delta_rec = rec_c1 - rec_f83
    
    # f1 calculation for this class in synthetic sub
    # True positives, False positives, False negatives
    tp_f83 = ((df_synth['clase_objetivo'] == c) & (df_synth['pred_f83'] == c)).sum()
    fp_f83 = ((df_synth['clase_objetivo'] != c) & (df_synth['pred_f83'] == c)).sum()
    fn_f83 = ((df_synth['clase_objetivo'] == c) & (df_synth['pred_f83'] != c)).sum()
    p_f83 = tp_f83 / (tp_f83 + fp_f83) if (tp_f83 + fp_f83) > 0 else 0.0
    r_f83 = tp_f83 / (tp_f83 + fn_f83) if (tp_f83 + fn_f83) > 0 else 0.0
    f1_f83 = (2 * p_f83 * r_f83) / (p_f83 + r_f83) if (p_f83 + r_f83) > 0 else 0.0
    
    tp_c1 = ((df_synth['clase_objetivo'] == c) & (df_synth['pred_c1'] == c)).sum()
    fp_c1 = ((df_synth['clase_objetivo'] != c) & (df_synth['pred_c1'] == c)).sum()
    fn_c1 = ((df_synth['clase_objetivo'] == c) & (df_synth['pred_c1'] != c)).sum()
    p_c1 = tp_c1 / (tp_c1 + fp_c1) if (tp_c1 + fp_c1) > 0 else 0.0
    r_c1 = tp_c1 / (tp_c1 + fn_c1) if (tp_c1 + fn_c1) > 0 else 0.0
    f1_c1 = (2 * p_c1 * r_c1) / (p_c1 + r_c1) if (p_c1 + r_c1) > 0 else 0.0
    
    delta_f1 = f1_c1 - f1_f83
    
    class_stats.append({
        'clase': c,
        'support_unseen': supp,
        'rec_f83': round(rec_f83, 4),
        'rec_c1': round(rec_c1, 4),
        'delta_recall': round(delta_rec, 4),
        'f1_f83': round(f1_f83, 4),
        'f1_c1': round(f1_c1, 4),
        'delta_f1': round(delta_f1, 4),
        'degradacion_relevante': 'SI' if (delta_f1 <= -0.15 and supp >= 8) else 'NO'
    })

df_unseen_cls = pd.DataFrame(class_stats)
df_unseen_cls.to_csv(base_dir / "fase10_c1_vs_f83_unseen_by_class.csv", index=False, encoding="utf-8")
df_unseen_cls.to_csv(base_dir / "machine_learning/data/fase10/fase10_c1_vs_f83_unseen_by_class.csv", index=False, encoding="utf-8")

mejora_unseen = df_unseen_cls[df_unseen_cls['delta_f1'] > 0.05].sort_values(by='delta_f1', ascending=False)
empeora_unseen = df_unseen_cls[df_unseen_cls['delta_f1'] < -0.05].sort_values(by='delta_f1', ascending=True)

print(f"\nCLASES EN UNSEEN SINTÉTICO (n={len(df_unseen_cls)}):")
print(f"  Clases donde C1 mejora (delta F1 > +5%): {len(mejora_unseen)}")
print(f"  Clases donde C1 empeora (delta F1 < -5%): {len(empeora_unseen)}")
print(f"  Clases con DEGRADACION_RELEVANTE (delta F1 <= -15% y support >= 8): {len(df_unseen_cls[df_unseen_cls['degradacion_relevante'] == 'SI'])}")
print("\nTop 5 Mejoras en Unseen:")
print(mejora_unseen[['clase', 'support_unseen', 'f1_f83', 'f1_c1', 'delta_f1']].head(5).to_string(index=False))
print("\nTop 5 Empeoras en Unseen:")
print(empeora_unseen[['clase', 'support_unseen', 'f1_f83', 'f1_c1', 'delta_f1']].head(5).to_string(index=False))

# ==============================================================================
# 15 & 16. CLIMATIZACIÓN (Clase 54 y Macro)
# ==============================================================================
clase_ac = "Falla en compresor de aire acondicionado o fuga de gas R134a"
df_ac = df_dev[df_dev['clase_objetivo'] == clase_ac].copy()

rows_ac = []
for idx, r in df_ac.iterrows():
    rows_ac.append({
        'id': r['id'],
        'source': r['synthetic_or_original'],
        'nivel': r['nivel_informacion'],
        'texto': r['texto_usuario'],
        'correct_top1': r['correct_c1'],
        'in_top3': r['in_top3_c1'],
        'pred_top1': r['pred_c1'],
        'conf': round(r['conf_c1'], 4),
        'macro_real': r['macro_sistema'],
        'macro_pred': r['pred_macro_fix'],
        'macro_correct': r['macro_correct']
    })
df_ac_export = pd.DataFrame(rows_ac)
df_ac_export.to_csv(base_dir / "fase10_c1_climate_analysis.csv", index=False, encoding="utf-8")
df_ac_export.to_csv(base_dir / "machine_learning/data/fase10/fase10_c1_climate_analysis.csv", index=False, encoding="utf-8")

print(f"\nCLIMATIZACIÓN CLASE 54 (n={len(df_ac)}):")
print(f"  Top-1: {df_ac['correct_c1'].mean()*100:.2f}% ({df_ac['correct_c1'].sum()}/{len(df_ac)})")
print(f"  Top-3: {df_ac['in_top3_c1'].mean()*100:.2f}% ({df_ac['in_top3_c1'].sum()}/{len(df_ac)})")
print(f"  Macro Accuracy: {df_ac['macro_correct'].mean()*100:.2f}%")

# The 5 macro errors in CLIMATIZACION
sub_macro_clima = df_dev[df_dev['macro_sistema'] == 'CLIMATIZACION']
errs_macro_clima = sub_macro_clima[sub_macro_clima['pred_macro_fix'] != 'CLIMATIZACION']
print(f"\n5 Errores en Macro CLIMATIZACION (n={len(errs_macro_clima)}):")
for idx, r in errs_macro_clima.iterrows():
    print(f"  ID: {r['id']} | Nivel: {r['nivel_informacion']} | Pred Macro: {r['pred_macro_fix']} | Pred Falla: {r['pred_c1']} | Conf: {r['conf_c1']:.4f}")
    print(f"    Texto: {r['texto_usuario']}")

# ==============================================================================
# 21. DTC SHORTCUT ANALYSIS
# ==============================================================================
# Check if dtc is present in synthetic rows
def has_dtc(row):
    d = str(row['dtc']).strip()
    return bool(d != '' and d != 'nan' and d != 'None' and pd.notna(row['dtc']))

df_synth['has_dtc'] = df_synth.apply(has_dtc, axis=1)

dtc_rows = []
for flag in [True, False]:
    sub = df_synth[df_synth['has_dtc'] == flag]
    acc1 = sub['correct_c1'].mean()
    acc3 = sub['in_top3_c1'].mean()
    _, _, mf1, _ = precision_recall_fscore_support(sub['clase_objetivo'], sub['pred_c1'], average='macro', zero_division=0)
    dtc_rows.append({
        'grupo': 'CON_DTC' if flag else 'SIN_DTC',
        'n': len(sub),
        'top1_accuracy': round(acc1, 4),
        'top3_accuracy': round(acc3, 4),
        'macro_f1': round(mf1, 4)
    })
df_dtc_export = pd.DataFrame(dtc_rows)
df_dtc_export.to_csv(base_dir / "fase10_c1_dtc_analysis.csv", index=False, encoding="utf-8")
df_dtc_export.to_csv(base_dir / "machine_learning/data/fase10/fase10_c1_dtc_analysis.csv", index=False, encoding="utf-8")
print("\nANÁLISIS DE SHORTCUT DTC (Sintéticos):")
print(df_dtc_export.to_string(index=False))

# ==============================================================================
# 22. LANGUAGE SHORTCUT ANALYSIS
# ==============================================================================
lang_rows = []
for lang, grp in df_synth.groupby('tipo_lenguaje'):
    acc1 = grp['correct_c1'].mean()
    acc3 = grp['in_top3_c1'].mean()
    _, _, mf1, _ = precision_recall_fscore_support(grp['clase_objetivo'], grp['pred_c1'], average='macro', zero_division=0)
    lang_rows.append({
        'tipo_lenguaje': lang,
        'n': len(grp),
        'top1_accuracy': round(acc1, 4),
        'top3_accuracy': round(acc3, 4),
        'macro_f1': round(mf1, 4)
    })
df_lang_export = pd.DataFrame(lang_rows).sort_values(by='n', ascending=False)
df_lang_export.to_csv(base_dir / "fase10_c1_language_analysis.csv", index=False, encoding="utf-8")
df_lang_export.to_csv(base_dir / "machine_learning/data/fase10/fase10_c1_language_analysis.csv", index=False, encoding="utf-8")
print("\nANÁLISIS POR TIPO DE LENGUAJE (Sintéticos):")
print(df_lang_export.to_string(index=False))

# ==============================================================================
# 23. BRAND SHORTCUT ANALYSIS
# ==============================================================================
brands = [
    'toyota', 'chevrolet', 'chevy', 'ford', 'volkswagen', 'vw', 'audi',
    'bmw', 'mercedes', 'nissan', 'hyundai', 'kia', 'fiat', 'suzuki',
    'renault', 'peugeot', 'mazda', 'honda', 'mitsubishi', 'volvo'
]
brand_pattern = r'\b(' + '|'.join(brands) + r')\b'

def mentions_brand(txt):
    return bool(re.search(brand_pattern, str(txt).lower()))

df_synth['has_brand'] = df_synth['texto_usuario'].apply(mentions_brand)
for flag in [True, False]:
    sub = df_synth[df_synth['has_brand'] == flag]
    acc1 = sub['correct_c1'].mean()
    acc3 = sub['in_top3_c1'].mean()
    print(f"  {'CON_MARCA' if flag else 'SIN_MARCA'}: n={len(sub):3d} | Top-1: {acc1*100:.2f}% | Top-3: {acc3*100:.2f}%")

# ==============================================================================
# 24. CONFIDENCE AND AUTO-INTERROGATOR
# ==============================================================================
print("\nCONFIANZA POR NIVEL Y ACIERTO:")
for lvl in ['L1', 'L2', 'L3']:
    sub = df_synth[df_synth['nivel_informacion'] == lvl]
    sub_corr = sub[sub['correct_c1'] == 1]
    sub_wrong = sub[sub['correct_c1'] == 0]
    print(f"  {lvl} Correctos:   n={len(sub_corr):3d} | Confianza media = {sub_corr['conf_c1'].mean():.4f}")
    print(f"  {lvl} Incorrectos: n={len(sub_wrong):3d} | Confianza media = {sub_wrong['conf_c1'].mean():.4f}")

print("\nAnálisis completado exitosamente.")
