import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import joblib
from scipy import stats
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix
)

base_dir = Path('.').resolve()
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from machine_learning.models.taxonomia_sistemas import FALLA_A_SISTEMA, obtener_macro_sistema

# 1. Load TEST10
test10_path = base_dir / "machine_learning/data/fase10/test10_fase10_blind_v1.csv"
df_test = pd.read_csv(test10_path)
print(f"TEST10 cargado: {len(df_test)} filas, {df_test['clase_objetivo'].nunique()} clases")

# Verify constraints
assert len(df_test) == 366, f"Esperadas 366 filas, encontradas {len(df_test)}"
assert df_test['clase_objetivo'].nunique() == 61, f"Esperadas 61 clases"
assert df_test['id'].nunique() == 366, "IDs duplicados"
assert df_test['texto_usuario'].isna().sum() == 0, "Textos nulos"
assert (df_test['texto_usuario'].str.strip() == '').sum() == 0, "Textos vacíos"

textos_test = df_test["texto_usuario"].astype(str).tolist()
y_test_real = df_test["clase_objetivo"].tolist()
y_macro_real = [obtener_macro_sistema(c) for c in y_test_real]
df_test["macro_sistema_canonico"] = y_macro_real

# 2. Load Models
# F8.3 Frozen Baseline
vec_f83 = joblib.load(base_dir / "machine_learning/models/vectorizador_tfidf.pkl")
cal_f_f83 = joblib.load(base_dir / "machine_learning/models/modelo_diagnostico.pkl")
cal_s_f83 = joblib.load(base_dir / "machine_learning/models/modelo_sistema.pkl")

# C1 Frozen Final Candidate
dir_c1_final = base_dir / "machine_learning/training/fase10/final_candidate/C1"
vec_c1 = joblib.load(dir_c1_final / "vectorizador_c1.pkl")
cal_f_c1 = joblib.load(dir_c1_final / "modelo_diagnostico_c1.pkl")
cal_s_c1 = joblib.load(dir_c1_final / "modelo_sistema_c1_macrofix.pkl")

# 3. Canonical Hierarchical Inference Function
def inferir_jerarquico(cal_falla, cal_sist, vec, textos: List[str], temp: float = 0.80, exp_sist: float = 0.65):
    X_vec = vec.transform(textos)
    p_f = cal_falla.predict_proba(X_vec)
    p_s = cal_sist.predict_proba(X_vec)

    clases_f = list(cal_falla.classes_)
    clases_s = list(cal_sist.classes_)
    sist_map = [{clases_s[j]: p_s[i, j] for j in range(len(clases_s))} for i in range(len(textos))]

    p_comb = np.zeros_like(p_f)
    for i in range(len(textos)):
        for j, f in enumerate(clases_f):
            m = obtener_macro_sistema(f)
            p_comb[i, j] = p_f[i, j] * (sist_map[i].get(m, 0.05) ** exp_sist)
        suma_i = np.sum(p_comb[i])
        if suma_i > 0:
            p_comb[i] /= suma_i

    if temp > 0 and temp != 1.0:
        for i in range(len(textos)):
            p_comb[i] = p_comb[i] ** (1.0 / temp)
            suma_t = np.sum(p_comb[i])
            if suma_t > 0:
                p_comb[i] /= suma_t

    pred_top1_idx = np.argmax(p_comb, axis=1)
    pred_top1 = [clases_f[idx] for idx in pred_top1_idx]
    conf_top1 = np.max(p_comb, axis=1)

    top3_idx = np.argsort(p_comb, axis=1)[:, -3:][:, ::-1]
    pred_top3 = [[clases_f[idx] for idx in row] for row in top3_idx]

    pred_sistema = cal_sist.predict(X_vec)

    return {
        "pred_top1": pred_top1,
        "conf_top1": conf_top1,
        "pred_top3": pred_top3,
        "pred_sistema": pred_sistema,
        "probs_falla": p_comb,
        "clases_falla": clases_f
    }

print("\nEjecutando inferencia F8.3 sobre TEST10 (n=366)...")
t0 = time.time()
inf_f83 = inferir_jerarquico(cal_f_f83, cal_s_f83, vec_f83, textos_test, temp=0.80, exp_sist=0.65)
t_f83 = round(time.time() - t0, 2)
print(f"Inferencia F8.3 completada en {t_f83}s")

print("Ejecutando inferencia C1 sobre TEST10 (n=366)...")
t0 = time.time()
inf_c1 = inferir_jerarquico(cal_f_c1, cal_s_c1, vec_c1, textos_test, temp=0.80, exp_sist=0.65)
t_c1 = round(time.time() - t0, 2)
print(f"Inferencia C1 completada en {t_c1}s")

# 4. Global Metrics Calculation
top1_f83 = [1 if inf_f83["pred_top1"][i] == y_test_real[i] else 0 for i in range(len(y_test_real))]
top1_c1 = [1 if inf_c1["pred_top1"][i] == y_test_real[i] else 0 for i in range(len(y_test_real))]

acc1_f83 = np.mean(top1_f83)
acc1_c1 = np.mean(top1_c1)

top3_f83 = [1 if y_test_real[i] in inf_f83["pred_top3"][i] else 0 for i in range(len(y_test_real))]
top3_c1 = [1 if y_test_real[i] in inf_c1["pred_top3"][i] else 0 for i in range(len(y_test_real))]

acc3_f83 = np.mean(top3_f83)
acc3_c1 = np.mean(top3_c1)

# Top3 recovery among errors
rec_top3_f83 = sum(top3_f83[i] for i in range(len(y_test_real)) if top1_f83[i] == 0) / sum(1 - t for t in top1_f83)
rec_top3_c1 = sum(top3_c1[i] for i in range(len(y_test_real)) if top1_c1[i] == 0) / sum(1 - t for t in top1_c1)

clases_unicas = sorted(list(FALLA_A_SISTEMA.keys()))

p_m_f83, r_m_f83, f1_m_f83, _ = precision_recall_fscore_support(y_test_real, inf_f83["pred_top1"], labels=clases_unicas, average="macro", zero_division=0)
p_m_c1, r_m_c1, f1_m_c1, _ = precision_recall_fscore_support(y_test_real, inf_c1["pred_top1"], labels=clases_unicas, average="macro", zero_division=0)

p_w_f83, r_w_f83, f1_w_f83, _ = precision_recall_fscore_support(y_test_real, inf_f83["pred_top1"], labels=clases_unicas, average="weighted", zero_division=0)
p_w_c1, r_w_c1, f1_w_c1, _ = precision_recall_fscore_support(y_test_real, inf_c1["pred_top1"], labels=clases_unicas, average="weighted", zero_division=0)

print("\n" + "="*80)
print("RESULTADOS GLOBALES EN TEST10 CIEGO (n=366, 61 clases)")
print("="*80)
print(f"Métrica                 F8.3       C1        DELTA")
print(f"Top-1 Accuracy:       {acc1_f83*100:6.2f}%   {acc1_c1*100:6.2f}%   {(acc1_c1-acc1_f83)*100:+6.2f} pp")
print(f"Top-3 Accuracy:       {acc3_f83*100:6.2f}%   {acc3_c1*100:6.2f}%   {(acc3_c1-acc3_f83)*100:+6.2f} pp")
print(f"Macro Precision:      {p_m_f83*100:6.2f}%   {p_m_c1*100:6.2f}%   {(p_m_c1-p_m_f83)*100:+6.2f} pp")
print(f"Macro Recall:         {r_m_f83*100:6.2f}%   {r_m_c1*100:6.2f}%   {(r_m_c1-r_m_f83)*100:+6.2f} pp")
print(f"Macro F1-Score:       {f1_m_f83*100:6.2f}%   {f1_m_c1*100:6.2f}%   {(f1_m_c1-f1_m_f83)*100:+6.2f} pp")
print(f"Weighted F1-Score:    {f1_w_f83*100:6.2f}%   {f1_w_c1*100:6.2f}%   {(f1_w_c1-f1_w_f83)*100:+6.2f} pp")
print(f"Top-3 Recovery (err): {rec_top3_f83*100:6.2f}%   {rec_top3_c1*100:6.2f}%   {(rec_top3_c1-rec_top3_f83)*100:+6.2f} pp")

# 5. Predictions DataFrames and Export
df_pred_f83 = df_test.copy()
df_pred_f83["pred_top1"] = inf_f83["pred_top1"]
df_pred_f83["top3"] = [" | ".join(t) for t in inf_f83["pred_top3"]]
df_pred_f83["confidence"] = [round(float(c), 4) for c in inf_f83["conf_top1"]]
df_pred_f83["correct_top1"] = top1_f83
df_pred_f83["in_top3"] = top3_f83
df_pred_f83["pred_macro"] = inf_f83["pred_sistema"]
df_pred_f83["macro_correct"] = (df_pred_f83["pred_macro"] == df_test["macro_sistema_canonico"]).astype(int)

df_pred_c1 = df_test.copy()
df_pred_c1["pred_top1"] = inf_c1["pred_top1"]
df_pred_c1["top3"] = [" | ".join(t) for t in inf_c1["pred_top3"]]
df_pred_c1["confidence"] = [round(float(c), 4) for c in inf_c1["conf_top1"]]
df_pred_c1["correct_top1"] = top1_c1
df_pred_c1["in_top3"] = top3_c1
df_pred_c1["pred_macro"] = inf_c1["pred_sistema"]
df_pred_c1["macro_correct"] = (df_pred_c1["pred_macro"] == df_test["macro_sistema_canonico"]).astype(int)

df_pred_f83.to_csv(base_dir / "test10_f83_predictions.csv", index=False, encoding="utf-8")
df_pred_f83.to_csv(base_dir / "machine_learning/data/fase10/test10_f83_predictions.csv", index=False, encoding="utf-8")

df_pred_c1.to_csv(base_dir / "test10_c1_predictions.csv", index=False, encoding="utf-8")
df_pred_c1.to_csv(base_dir / "machine_learning/data/fase10/test10_c1_predictions.csv", index=False, encoding="utf-8")

# 6. Evaluation by Level (L1, L2, L3)
level_rows = []
for lvl in ["L1", "L2", "L3"]:
    sub_f = df_pred_f83[df_pred_f83["nivel_informacion"] == lvl]
    sub_c = df_pred_c1[df_pred_c1["nivel_informacion"] == lvl]
    nl = len(sub_f)
    
    t1_f = sub_f["correct_top1"].mean()
    t1_c = sub_c["correct_top1"].mean()
    t3_f = sub_f["in_top3"].mean()
    t3_c = sub_c["in_top3"].mean()
    
    _, _, f1_f, _ = precision_recall_fscore_support(sub_f["clase_objetivo"], sub_f["pred_top1"], average="macro", zero_division=0)
    _, _, f1_c, _ = precision_recall_fscore_support(sub_c["clase_objetivo"], sub_c["pred_top1"], average="macro", zero_division=0)
    
    mac_acc_f = sub_f["macro_correct"].mean()
    mac_acc_c = sub_c["macro_correct"].mean()
    
    conf_f = sub_f["confidence"].mean()
    conf_c = sub_c["confidence"].mean()
    
    rec_err_c = sub_c[sub_c["correct_top1"] == 0]["in_top3"].sum()
    total_err_c = len(sub_c[sub_c["correct_top1"] == 0])
    
    level_rows.append({
        "nivel": lvl,
        "n": nl,
        "f83_top1": round(t1_f, 4),
        "c1_top1": round(t1_c, 4),
        "delta_top1": round(t1_c - t1_f, 4),
        "f83_top3": round(t3_f, 4),
        "c1_top3": round(t3_c, 4),
        "delta_top3": round(t3_c - t3_f, 4),
        "f83_macro_f1": round(f1_f, 4),
        "c1_macro_f1": round(f1_c, 4),
        "delta_macro_f1": round(f1_c - f1_f, 4),
        "f83_macro_acc": round(mac_acc_f, 4),
        "c1_macro_acc": round(mac_acc_c, 4),
        "c1_conf_mean": round(conf_c, 4),
        "c1_top3_rec_err": f"{rec_err_c}/{total_err_c}"
    })

df_levels = pd.DataFrame(level_rows)
df_levels.to_csv(base_dir / "test10_metrics_by_level.csv", index=False, encoding="utf-8")
df_levels.to_csv(base_dir / "machine_learning/data/fase10/test10_metrics_by_level.csv", index=False, encoding="utf-8")

print("\n" + "="*80)
print("EVALUACIÓN POR NIVEL DE INFORMACIÓN (L1, L2, L3)")
print("="*80)
print(df_levels[["nivel", "n", "f83_top1", "c1_top1", "delta_top1", "f83_top3", "c1_top3", "c1_macro_acc"]].to_string(index=False))

# 7. Macro-System Evaluation
expected_macros = sorted([
    "CARROCERIA_NEUMATICA", "CLIMATIZACION", "ELECTRICO",
    "FRENOS", "MOTOR", "SUSPENSION_CHASIS", "TRANSMISION"
])

mac_acc_f83 = accuracy_score(df_test["macro_sistema_canonico"], inf_f83["pred_sistema"])
mac_acc_c1 = accuracy_score(df_test["macro_sistema_canonico"], inf_c1["pred_sistema"])

p_mac_f83, r_mac_f83, f1_mac_f83, _ = precision_recall_fscore_support(df_test["macro_sistema_canonico"], inf_f83["pred_sistema"], labels=expected_macros, average="macro", zero_division=0)
p_mac_c1, r_mac_c1, f1_mac_c1, _ = precision_recall_fscore_support(df_test["macro_sistema_canonico"], inf_c1["pred_sistema"], labels=expected_macros, average="macro", zero_division=0)

p_mac_w_f83, r_mac_w_f83, f1_mac_w_f83, _ = precision_recall_fscore_support(df_test["macro_sistema_canonico"], inf_f83["pred_sistema"], labels=expected_macros, average="weighted", zero_division=0)
p_mac_w_c1, r_mac_w_c1, f1_mac_w_c1, _ = precision_recall_fscore_support(df_test["macro_sistema_canonico"], inf_c1["pred_sistema"], labels=expected_macros, average="weighted", zero_division=0)

print("\n" + "="*80)
print("EVALUACIÓN MACRO-SISTEMA (7 MACROS CANÓNICAS)")
print("="*80)
print(f"Macro Accuracy:    F8.3 = {mac_acc_f83*100:6.2f}% | C1 = {mac_acc_c1*100:6.2f}% | Delta = {(mac_acc_c1-mac_acc_f83)*100:+6.2f} pp")
print(f"Macro Precision:   F8.3 = {p_mac_f83*100:6.2f}% | C1 = {p_mac_c1*100:6.2f}% | Delta = {(p_mac_c1-p_mac_f83)*100:+6.2f} pp")
print(f"Macro Recall:      F8.3 = {r_mac_f83*100:6.2f}% | C1 = {r_mac_c1*100:6.2f}% | Delta = {(r_mac_c1-r_mac_f83)*100:+6.2f} pp")
print(f"Macro F1-Score:    F8.3 = {f1_mac_f83*100:6.2f}% | C1 = {f1_mac_c1*100:6.2f}% | Delta = {(f1_mac_c1-f1_mac_f83)*100:+6.2f} pp")
print(f"Weighted F1-Score: F8.3 = {f1_mac_w_f83*100:6.2f}% | C1 = {f1_mac_w_c1*100:6.2f}% | Delta = {(f1_mac_w_c1-f1_mac_w_f83)*100:+6.2f} pp")

# Metrics per macro
p_by_m_f, r_by_m_f, f1_by_m_f, s_by_m = precision_recall_fscore_support(df_test["macro_sistema_canonico"], inf_f83["pred_sistema"], labels=expected_macros, zero_division=0)
p_by_m_c, r_by_m_c, f1_by_m_c, _ = precision_recall_fscore_support(df_test["macro_sistema_canonico"], inf_c1["pred_sistema"], labels=expected_macros, zero_division=0)

macro_detail_rows = []
for idx, m in enumerate(expected_macros):
    macro_detail_rows.append({
        "macro_sistema": m,
        "support": int(s_by_m[idx]),
        "f83_precision": round(float(p_by_m_f[idx]), 4),
        "f83_recall": round(float(r_by_m_f[idx]), 4),
        "f83_f1": round(float(f1_by_m_f[idx]), 4),
        "c1_precision": round(float(p_by_m_c[idx]), 4),
        "c1_recall": round(float(r_by_m_c[idx]), 4),
        "c1_f1": round(float(f1_by_m_c[idx]), 4),
        "delta_f1": round(float(f1_by_m_c[idx] - f1_by_m_f[idx]), 4)
    })
df_macro_detail = pd.DataFrame(macro_detail_rows)
df_macro_detail.to_csv(base_dir / "test10_metrics_by_macro.csv", index=False, encoding="utf-8")
df_macro_detail.to_csv(base_dir / "machine_learning/data/fase10/test10_metrics_by_macro.csv", index=False, encoding="utf-8")
print("\nDetalle por Macro-Sistema en TEST10:")
print(df_macro_detail[["macro_sistema", "support", "f83_f1", "c1_f1", "delta_f1"]].to_string(index=False))

# Confusion Matrix 7x7
cm_c1_macro = confusion_matrix(df_test["macro_sistema_canonico"], inf_c1["pred_sistema"], labels=expected_macros)
df_cm_c1_macro = pd.DataFrame(cm_c1_macro, index=expected_macros, columns=expected_macros)
print("\nMatriz de Confusión 7x7 Macro C1 en TEST10:")
print(df_cm_c1_macro)

# 8. By-Class Metrics (61 Classes, support=6)
p_cls_f, r_cls_f, f1_cls_f, s_cls = precision_recall_fscore_support(y_test_real, inf_f83["pred_top1"], labels=clases_unicas, zero_division=0)
p_cls_c, r_cls_c, f1_cls_c, _ = precision_recall_fscore_support(y_test_real, inf_c1["pred_top1"], labels=clases_unicas, zero_division=0)

cls_rows = []
for idx, c in enumerate(clases_unicas):
    hits_f = sum(1 for i in range(len(y_test_real)) if y_test_real[i] == c and inf_f83["pred_top1"][i] == c)
    hits_c = sum(1 for i in range(len(y_test_real)) if y_test_real[i] == c and inf_c1["pred_top1"][i] == c)
    top3_h_f = sum(1 for i in range(len(y_test_real)) if y_test_real[i] == c and c in inf_f83["pred_top3"][i])
    top3_h_c = sum(1 for i in range(len(y_test_real)) if y_test_real[i] == c and c in inf_c1["pred_top3"][i])
    
    cls_rows.append({
        "clase": c,
        "macro_sistema": obtener_macro_sistema(c),
        "support": int(s_cls[idx]),
        "f83_correct_top1": hits_f,
        "c1_correct_top1": hits_c,
        "f83_top3_hits": top3_h_f,
        "c1_top3_hits": top3_h_c,
        "f83_precision": round(float(p_cls_f[idx]), 4),
        "f83_recall": round(float(r_cls_f[idx]), 4),
        "f83_f1": round(float(f1_cls_f[idx]), 4),
        "c1_precision": round(float(p_cls_c[idx]), 4),
        "c1_recall": round(float(r_cls_c[idx]), 4),
        "c1_f1": round(float(f1_cls_c[idx]), 4),
        "delta_recall": round(float(r_cls_c[idx] - r_cls_f[idx]), 4),
        "delta_f1": round(float(f1_cls_c[idx] - f1_cls_f[idx]), 4)
    })

df_by_class = pd.DataFrame(cls_rows)
df_by_class.to_csv(base_dir / "test10_f83_vs_c1_by_class.csv", index=False, encoding="utf-8")
df_by_class.to_csv(base_dir / "machine_learning/data/fase10/test10_f83_vs_c1_by_class.csv", index=False, encoding="utf-8")

# Individual files
df_by_class[["clase", "macro_sistema", "support", "f83_correct_top1", "f83_top3_hits", "f83_precision", "f83_recall", "f83_f1"]].rename(
    columns={"f83_correct_top1": "correct_top1", "f83_top3_hits": "top3_hits", "f83_precision": "precision", "f83_recall": "recall", "f83_f1": "f1_score"}
).to_csv(base_dir / "test10_f83_metrics_by_class.csv", index=False, encoding="utf-8")

df_by_class[["clase", "macro_sistema", "support", "c1_correct_top1", "c1_top3_hits", "c1_precision", "c1_recall", "c1_f1"]].rename(
    columns={"c1_correct_top1": "correct_top1", "c1_top3_hits": "top3_hits", "c1_precision": "precision", "c1_recall": "recall", "c1_f1": "f1_score"}
).to_csv(base_dir / "test10_c1_metrics_by_class.csv", index=False, encoding="utf-8")

# 9. Confusion Matrices 61x61
cm_f83 = confusion_matrix(y_test_real, inf_f83["pred_top1"], labels=clases_unicas)
df_cm_f83 = pd.DataFrame(cm_f83, index=clases_unicas, columns=clases_unicas)
df_cm_f83.to_csv(base_dir / "test10_f83_confusion_matrix.csv", encoding="utf-8")
df_cm_f83.to_csv(base_dir / "machine_learning/data/fase10/test10_f83_confusion_matrix.csv", encoding="utf-8")

cm_c1 = confusion_matrix(y_test_real, inf_c1["pred_top1"], labels=clases_unicas)
df_cm_c1 = pd.DataFrame(cm_c1, index=clases_unicas, columns=clases_unicas)
df_cm_c1.to_csv(base_dir / "test10_c1_confusion_matrix.csv", encoding="utf-8")
df_cm_c1.to_csv(base_dir / "machine_learning/data/fase10/test10_c1_confusion_matrix.csv", encoding="utf-8")

# 10. Paired Comparison & McNemar
ambos_correctos = sum(1 for i in range(len(y_test_real)) if top1_f83[i] == 1 and top1_c1[i] == 1)
solo_f83 = sum(1 for i in range(len(y_test_real)) if top1_f83[i] == 1 and top1_c1[i] == 0)
solo_c1 = sum(1 for i in range(len(y_test_real)) if top1_f83[i] == 0 and top1_c1[i] == 1)
ambos_incorrectos = sum(1 for i in range(len(y_test_real)) if top1_f83[i] == 0 and top1_c1[i] == 0)

b = solo_f83  # F8.3 correcto / C1 incorrecto
c = solo_c1   # F8.3 incorrecto / C1 correcto
if b + c > 0:
    mcnemar_stat = float((abs(b - c) - 1.0) ** 2 / (b + c))
    mcnemar_p = float(1.0 - stats.chi2.cdf(mcnemar_stat, df=1))
else:
    mcnemar_stat = 0.0
    mcnemar_p = 1.0

print("\n" + "="*80)
print("COMPARACIÓN PAREADA Y TEST DE MCNEMAR")
print("="*80)
print(f"Ambos correctos:    {ambos_correctos}")
print(f"Solo F8.3 correcto: {solo_f83} (b)")
print(f"Solo C1 correcto:   {solo_c1} (c)")
print(f"Ambos incorrectos:  {ambos_incorrectos}")
print(f"McNemar Chi2:       {mcnemar_stat:.4f} | p-value: {mcnemar_p:.6e}")

# Paired CSV
df_paired = df_test[["id", "nivel_informacion", "clase_objetivo"]].rename(columns={"nivel_informacion": "nivel", "clase_objetivo": "real"}).copy()
df_paired["pred_f83"] = inf_f83["pred_top1"]
df_paired["pred_c1"] = inf_c1["pred_top1"]
df_paired["correct_f83"] = top1_f83
df_paired["correct_c1"] = top1_c1
df_paired["top3_f83"] = [" | ".join(t) for t in inf_f83["pred_top3"]]
df_paired["top3_c1"] = [" | ".join(t) for t in inf_c1["pred_top3"]]
df_paired["confidence_f83"] = [round(float(conf), 4) for conf in inf_f83["conf_top1"]]
df_paired["confidence_c1"] = [round(float(conf), 4) for conf in inf_c1["conf_top1"]]

df_paired.to_csv(base_dir / "test10_f83_vs_c1_paired.csv", index=False, encoding="utf-8")
df_paired.to_csv(base_dir / "machine_learning/data/fase10/test10_f83_vs_c1_paired.csv", index=False, encoding="utf-8")

# 11. Bootstrap 95% Confidence Intervals (5000 iterations, seed 42)
print("\nCalculando Bootstrap 95% CI (5000 iteraciones, seed=42)...")
np.random.seed(42)
n_boot = 5000
boot_d_t1 = []
boot_d_t3 = []
boot_d_mf1 = []

n_total = len(y_test_real)
idx_range = np.arange(n_total)

for _ in range(n_boot):
    s_idx = np.random.choice(idx_range, size=n_total, replace=True)
    b_y = [y_test_real[i] for i in s_idx]
    
    b_t1_f = [top1_f83[i] for i in s_idx]
    b_t1_c = [top1_c1[i] for i in s_idx]
    boot_d_t1.append(np.mean(b_t1_c) - np.mean(b_t1_f))
    
    b_t3_f = [top3_f83[i] for i in s_idx]
    b_t3_c = [top3_c1[i] for i in s_idx]
    boot_d_t3.append(np.mean(b_t3_c) - np.mean(b_t3_f))
    
    b_p_f = [inf_f83["pred_top1"][i] for i in s_idx]
    b_p_c = [inf_c1["pred_top1"][i] for i in s_idx]
    _, _, f1_bf, _ = precision_recall_fscore_support(b_y, b_p_f, labels=clases_unicas, average="macro", zero_division=0)
    _, _, f1_bc, _ = precision_recall_fscore_support(b_y, b_p_c, labels=clases_unicas, average="macro", zero_division=0)
    boot_d_mf1.append(f1_bc - f1_bf)

ci_t1 = [round(float(np.percentile(boot_d_t1, 2.5)), 4), round(float(np.percentile(boot_d_t1, 97.5)), 4)]
ci_t3 = [round(float(np.percentile(boot_d_t3, 2.5)), 4), round(float(np.percentile(boot_d_t3, 97.5)), 4)]
ci_mf1 = [round(float(np.percentile(boot_d_mf1, 2.5)), 4), round(float(np.percentile(boot_d_mf1, 97.5)), 4)]

print(f"Delta Top-1 CI 95%:   [{ci_t1[0]*100:+.2f}%, {ci_t1[1]*100:+.2f}%]")
print(f"Delta Top-3 CI 95%:   [{ci_t3[0]*100:+.2f}%, {ci_t3[1]*100:+.2f}%]")
print(f"Delta Macro F1 CI 95%: [{ci_mf1[0]*100:+.2f}%, {ci_mf1[1]*100:+.2f}%]")

# 12. Contrastive Cases
if "es_contrastivo" in df_test.columns and (df_test["es_contrastivo"] == "SI").sum() > 0:
    sub_ct = df_test[df_test["es_contrastivo"] == "SI"]
    n_ct = len(sub_ct)
    indices_ct = sub_ct.index.tolist()
    
    ct_t1_f = np.mean([top1_f83[i] for i in indices_ct])
    ct_t1_c = np.mean([top1_c1[i] for i in indices_ct])
    ct_t3_f = np.mean([top3_f83[i] for i in indices_ct])
    ct_t3_c = np.mean([top3_c1[i] for i in indices_ct])
    
    trap_f = sum(1 for i in indices_ct if inf_f83["pred_top1"][i] == df_test.loc[i, "clase_contrastiva"])
    trap_c = sum(1 for i in indices_ct if inf_c1["pred_top1"][i] == df_test.loc[i, "clase_contrastiva"])
    print(f"\nCONTRASTIVOS EN TEST10 (n={n_ct}):")
    print(f"  F8.3: Top-1 = {ct_t1_f*100:.2f}% | Top-3 = {ct_t3_f*100:.2f}% | Trampa = {trap_f}")
    print(f"  C1:   Top-1 = {ct_t1_c*100:.2f}% | Top-3 = {ct_t3_c*100:.2f}% | Trampa = {trap_c}")
else:
    n_ct, ct_t1_f, ct_t1_c, ct_t3_f, ct_t3_c, trap_f, trap_c = 0, 0, 0, 0, 0, 0, 0

# 13. DTC Cases
def tiene_dtc(row):
    d = str(row['dtc']).strip()
    return bool(d != '' and d != 'nan' and d != 'None' and pd.notna(row['dtc']))

df_test['has_dtc'] = df_test.apply(tiene_dtc, axis=1)

dtc_table = []
for flag in [True, False]:
    sub_idx = df_test[df_test['has_dtc'] == flag].index.tolist()
    n_dtc = len(sub_idx)
    t1_f = np.mean([top1_f83[i] for i in sub_idx])
    t1_c = np.mean([top1_c1[i] for i in sub_idx])
    t3_f = np.mean([top3_f83[i] for i in sub_idx])
    t3_c = np.mean([top3_c1[i] for i in sub_idx])
    
    y_sub = [y_test_real[i] for i in sub_idx]
    p_f = [inf_f83["pred_top1"][i] for i in sub_idx]
    p_c = [inf_c1["pred_top1"][i] for i in sub_idx]
    _, _, f1_f, _ = precision_recall_fscore_support(y_sub, p_f, average="macro", zero_division=0)
    _, _, f1_c, _ = precision_recall_fscore_support(y_sub, p_c, average="macro", zero_division=0)
    
    dtc_table.append({
        "grupo": "CON_DTC" if flag else "SIN_DTC",
        "n": n_dtc,
        "f83_top1": round(t1_f, 4),
        "c1_top1": round(t1_c, 4),
        "delta_top1": round(t1_c - t1_f, 4),
        "f83_top3": round(t3_f, 4),
        "c1_top3": round(t3_c, 4),
        "delta_top3": round(t3_c - t3_f, 4),
        "f83_macro_f1": round(f1_f, 4),
        "c1_macro_f1": round(f1_c, 4),
        "delta_macro_f1": round(f1_c - f1_f, 4)
    })

df_dtc_exp = pd.DataFrame(dtc_table)
df_dtc_exp.to_csv(base_dir / "test10_metrics_dtc.csv", index=False, encoding="utf-8")
df_dtc_exp.to_csv(base_dir / "machine_learning/data/fase10/test10_metrics_dtc.csv", index=False, encoding="utf-8")
print("\nEVALUACIÓN DTC:")
print(df_dtc_exp.to_string(index=False))

# 14. Language Types
lang_table = []
for lang, grp in df_test.groupby("tipo_lenguaje"):
    sub_idx = grp.index.tolist()
    n_lg = len(sub_idx)
    t1_f = np.mean([top1_f83[i] for i in sub_idx])
    t1_c = np.mean([top1_c1[i] for i in sub_idx])
    t3_f = np.mean([top3_f83[i] for i in sub_idx])
    t3_c = np.mean([top3_c1[i] for i in sub_idx])
    lang_table.append({
        "tipo_lenguaje": lang,
        "n": n_lg,
        "f83_top1": round(t1_f, 4),
        "c1_top1": round(t1_c, 4),
        "delta_top1": round(t1_c - t1_f, 4),
        "f83_top3": round(t3_f, 4),
        "c1_top3": round(t3_c, 4),
        "delta_top3": round(t3_c - t3_f, 4)
    })
df_lang_exp = pd.DataFrame(lang_table).sort_values(by="n", ascending=False)
df_lang_exp.to_csv(base_dir / "test10_metrics_by_language.csv", index=False, encoding="utf-8")
df_lang_exp.to_csv(base_dir / "machine_learning/data/fase10/test10_metrics_by_language.csv", index=False, encoding="utf-8")
print("\nEVALUACIÓN POR LENGUAJE:")
print(df_lang_exp.to_string(index=False))

# 15. Climatización Class 54 (6 cases)
clase_ac = "Falla en compresor de aire acondicionado o fuga de gas R134a"
ac_indices = df_test[df_test["clase_objetivo"] == clase_ac].index.tolist()
ac_cases = []
for i in ac_indices:
    ac_cases.append({
        "id": df_test.loc[i, "id"],
        "nivel": df_test.loc[i, "nivel_informacion"],
        "real": clase_ac,
        "pred_f83": inf_f83["pred_top1"][i],
        "top3_f83": " | ".join(inf_f83["pred_top3"][i]),
        "pred_c1": inf_c1["pred_top1"][i],
        "top3_c1": " | ".join(inf_c1["pred_top3"][i]),
        "macro_f83": inf_f83["pred_sistema"][i],
        "macro_c1": inf_c1["pred_sistema"][i],
        "confidence": round(float(inf_c1["conf_top1"][i]), 4),
        "c1_correct": top1_c1[i]
    })
print(f"\nCLIMATIZACIÓN CLASE 54 (n={len(ac_cases)}):")
for ac in ac_cases:
    print(f"  ID: {ac['id']} ({ac['nivel']}) | C1 Pred: {ac['pred_c1']} (Correct: {ac['c1_correct']}) | Macro C1: {ac['macro_c1']} | Conf: {ac['confidence']}")

# 16. Calibration for C1
brier_c1 = float(np.mean((np.array(inf_c1["conf_top1"]) - np.array(top1_c1)) ** 2))
bin_bounds = np.linspace(0, 1, 11)
ece_c1 = 0.0
bins_info = []
for b_idx in range(10):
    b_low = bin_bounds[b_idx]
    b_high = bin_bounds[b_idx + 1]
    mask = (np.array(inf_c1["conf_top1"]) > b_low) & (np.array(inf_c1["conf_top1"]) <= b_high)
    if np.any(mask):
        b_acc = float(np.mean(np.array(top1_c1)[mask]))
        b_conf = float(np.mean(np.array(inf_c1["conf_top1"])[mask]))
        b_size = int(np.sum(mask))
        ece_c1 += (b_size / len(top1_c1)) * abs(b_acc - b_conf)
        bins_info.append({"bin": f"({b_low:.1f}, {b_high:.1f}]", "count": b_size, "acc": round(b_acc, 4), "conf": round(b_conf, 4)})

cal_thresholds = {}
for th in [0.60, 0.70, 0.80, 0.90]:
    mask_th = np.array(inf_c1["conf_top1"]) >= th
    acc_th = float(np.mean(np.array(top1_c1)[mask_th])) if np.any(mask_th) else 0.0
    cov_th = float(np.mean(mask_th))
    cal_thresholds[f"acc_gte_{int(th*100)}"] = round(acc_th, 4)
    cal_thresholds[f"cov_gte_{int(th*100)}"] = round(cov_th, 4)

print(f"\nCALIBRACIÓN C1 EN TEST10:")
print(f"  Brier Score: {brier_c1:.4f} | ECE: {ece_c1:.4f}")
for th in [0.60, 0.70, 0.80, 0.90]:
    print(f"  Conf >= {th:.2f}: Accuracy = {cal_thresholds[f'acc_gte_{int(th*100)}']*100:.2f}% | Coverage = {cal_thresholds[f'cov_gte_{int(th*100)}']*100:.2f}%")

# 17. High Confidence Wrong in C1
hcw_rows = []
for i in range(len(y_test_real)):
    if top1_c1[i] == 0 and inf_c1["conf_top1"][i] >= 0.80:
        hcw_rows.append({
            "id": df_test.loc[i, "id"],
            "nivel": df_test.loc[i, "nivel_informacion"],
            "texto": df_test.loc[i, "texto_usuario"],
            "real": y_test_real[i],
            "pred_c1": inf_c1["pred_top1"][i],
            "top3_c1": " | ".join(inf_c1["pred_top3"][i]),
            "confidence": round(float(inf_c1["conf_top1"][i]), 4),
            "dtc": df_test.loc[i, "dtc"]
        })
df_hcw = pd.DataFrame(hcw_rows)
df_hcw.to_csv(base_dir / "test10_c1_high_conf_wrong.csv", index=False, encoding="utf-8")
df_hcw.to_csv(base_dir / "machine_learning/data/fase10/test10_c1_high_conf_wrong.csv", index=False, encoding="utf-8")

print(f"\nHIGH CONFIDENCE WRONG (>=0.80) EN TEST10: {len(df_hcw)} casos")
print(f"  L1: {len(df_hcw[df_hcw['nivel'] == 'L1'])} | L2: {len(df_hcw[df_hcw['nivel'] == 'L2'])} | L3: {len(df_hcw[df_hcw['nivel'] == 'L3'])}")
print(f"  Casos con Conf >= 0.90 erróneos: {len(df_hcw[df_hcw['confidence'] >= 0.90])}")

# 18. Save JSON metrics
test10_f83_metrics = {
    "top1_accuracy": round(acc1_f83, 4),
    "top3_accuracy": round(acc3_f83, 4),
    "macro_precision": round(p_m_f83, 4),
    "macro_recall": round(r_m_f83, 4),
    "macro_f1": round(f1_m_f83, 4),
    "weighted_f1": round(f1_w_f83, 4),
    "macro_system_accuracy": round(mac_acc_f83, 4),
    "macro_system_f1": round(f1_mac_f83, 4)
}
with open(base_dir / "test10_f83_metrics.json", "w", encoding="utf-8") as f:
    json.dump(test10_f83_metrics, f, indent=2)
with open(base_dir / "machine_learning/data/fase10/test10_f83_metrics.json", "w", encoding="utf-8") as f:
    json.dump(test10_f83_metrics, f, indent=2)

test10_c1_metrics = {
    "top1_accuracy": round(acc1_c1, 4),
    "top3_accuracy": round(acc3_c1, 4),
    "macro_precision": round(p_m_c1, 4),
    "macro_recall": round(r_m_c1, 4),
    "macro_f1": round(f1_m_c1, 4),
    "weighted_f1": round(f1_w_c1, 4),
    "macro_system_accuracy": round(mac_acc_c1, 4),
    "macro_system_f1": round(f1_mac_c1, 4),
    "brier_score": round(brier_c1, 4),
    "ece": round(ece_c1, 4),
    "umbrales_calibracion": cal_thresholds
}
with open(base_dir / "test10_c1_metrics.json", "w", encoding="utf-8") as f:
    json.dump(test10_c1_metrics, f, indent=2)
with open(base_dir / "machine_learning/data/fase10/test10_c1_metrics.json", "w", encoding="utf-8") as f:
    json.dump(test10_c1_metrics, f, indent=2)

stat_comparison = {
    "paired": {
        "ambos_correctos": int(ambos_correctos),
        "solo_f83": int(solo_f83),
        "solo_c1": int(solo_c1),
        "ambos_incorrectos": int(ambos_incorrectos)
    },
    "mcnemar": {
        "statistic": round(mcnemar_stat, 4),
        "p_value": float(mcnemar_p)
    },
    "bootstrap_95ci": {
        "iterations": 5000,
        "seed": 42,
        "delta_top1": {"mean": round(float(acc1_c1 - acc1_f83), 4), "ci_95": ci_t1},
        "delta_top3": {"mean": round(float(acc3_c1 - acc3_f83), 4), "ci_95": ci_t3},
        "delta_macro_f1": {"mean": round(float(f1_m_c1 - f1_m_f83), 4), "ci_95": ci_mf1}
    }
}
with open(base_dir / "test10_statistical_comparison.json", "w", encoding="utf-8") as f:
    json.dump(stat_comparison, f, indent=2)
with open(base_dir / "machine_learning/data/fase10/test10_statistical_comparison.json", "w", encoding="utf-8") as f:
    json.dump(stat_comparison, f, indent=2)

print("\nEvaluación completada y todos los artefactos guardados exitosamente!")
