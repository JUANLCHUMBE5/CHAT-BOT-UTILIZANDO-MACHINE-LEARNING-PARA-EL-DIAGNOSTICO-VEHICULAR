import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.svm import LinearSVC

from optimizar_svm_candidato import preprocesar_texto_automotriz, evaluar_modelo

ROOT = Path(".").resolve()
train_path = ROOT / "machine_learning/data/fase10/train10_v1_1_macrofix.csv"
test_path = ROOT / "machine_learning/data/fase10/test10_fase10_blind_v1.csv"

df_train = pd.read_csv(train_path)
df_test = pd.read_csv(test_path)

X_train_raw = df_train["texto_usuario"].astype(str).tolist()
y_train_falla = df_train["clase_objetivo"].astype(str).tolist()
y_train_sist = df_train["macro_sistema"].astype(str).tolist()
groups_train = df_train["id_grupo"].tolist()

X_test_raw = df_test["texto_usuario"].astype(str).tolist()
y_test_falla = df_test["clase_objetivo"].astype(str).tolist()
y_test_sist = df_test["macro_sistema"].astype(str).tolist()

sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
cv_splits = list(sgkf.split(X_train_raw, y_train_falla, groups_train))

sgkf_s = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
cv_splits_s = list(sgkf_s.split(X_train_raw, y_train_sist, groups_train))

print("=== EVALUACIÓN FINAL DE CANDIDATOS SVM SOBRE TEST10 CIEGO (N=366) ===")

# 1. EVALUAR BASELINE CONGELADO OFICIAL
vec_base = joblib.load(ROOT / "machine_learning/models/c1_fase10_final/vectorizador_c1.pkl")
clf_base = joblib.load(ROOT / "machine_learning/models/c1_fase10_final/modelo_diagnostico_c1.pkl")
clf_sist_base = joblib.load(ROOT / "machine_learning/models/c1_fase10_final/modelo_sistema_c1_macrofix.pkl")

res_base_n2 = evaluar_modelo(clf_base, vec_base, X_test_raw, y_test_falla)
preds_sist_b = clf_sist_base.predict(vec_base.transform(X_test_raw))
acc_sist_b = accuracy_score(y_test_sist, preds_sist_b) * 100.0

print(f"\n[BASELINE OFICIAL C1]")
print(f"  N2 Top-1:   {res_base_n2['top1']:.2f}% ({res_base_n2['top1_count']}/366)")
print(f"  N2 Top-3:   {res_base_n2['top3']:.2f}%")
print(f"  N2 F1-Macro:{res_base_n2['f1_macro']:.2f}%")
print(f"  N1 Acc:     {acc_sist_b:.2f}%")

# 2. ENTRENAR Y EVALUAR CANDIDATO V2 (Sigmoid C=2.0 + preprocesamiento automotriz)
X_train_v2 = [preprocesar_texto_automotriz(t) for t in X_train_raw]
X_test_v2 = [preprocesar_texto_automotriz(t) for t in X_test_raw]

vec_v2 = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode", min_df=1, max_features=25000)
X_tr_v2 = vec_v2.fit_transform(X_train_v2)

svc_v2 = LinearSVC(C=2.0, class_weight="balanced", random_state=42, max_iter=3500)
cal_v2 = CalibratedClassifierCV(estimator=svc_v2, method="sigmoid", cv=cv_splits, n_jobs=4)
cal_v2.fit(X_tr_v2, y_train_falla)

svc_sist_v2 = LinearSVC(C=1.5, class_weight="balanced", random_state=42, max_iter=3000)
cal_sist_v2 = CalibratedClassifierCV(estimator=svc_sist_v2, method="sigmoid", cv=cv_splits_s, n_jobs=4)
cal_sist_v2.fit(X_tr_v2, y_train_sist)

res_v2_n2 = evaluar_modelo(cal_v2, vec_v2, X_test_v2, y_test_falla)
preds_sist_v2 = cal_sist_v2.predict(vec_v2.transform(X_test_v2))
acc_sist_v2 = accuracy_score(y_test_sist, preds_sist_v2) * 100.0

print(f"\n[CANDIDATO C1-V2 (Sigmoid C=2.0 + Prep Automotriz)]")
print(f"  N2 Top-1:   {res_v2_n2['top1']:.2f}% ({res_v2_n2['top1_count']}/366)")
print(f"  N2 Top-3:   {res_v2_n2['top3']:.2f}%")
print(f"  N2 F1-Macro:{res_v2_n2['f1_macro']:.2f}%")
print(f"  N1 Acc:     {acc_sist_v2:.2f}%")

# 3. ENTRENAR Y EVALUAR CANDIDATO V3 (Sigmoid C=1.5 vocabulario puro)
vec_v3 = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode", min_df=1, max_features=25000)
X_tr_v3 = vec_v3.fit_transform(X_train_raw)

svc_v3 = LinearSVC(C=1.5, class_weight="balanced", random_state=42, max_iter=3500)
cal_v3 = CalibratedClassifierCV(estimator=svc_v3, method="sigmoid", cv=cv_splits, n_jobs=4)
cal_v3.fit(X_tr_v3, y_train_falla)

svc_sist_v3 = LinearSVC(C=1.5, class_weight="balanced", random_state=42, max_iter=3000)
cal_sist_v3 = CalibratedClassifierCV(estimator=svc_sist_v3, method="sigmoid", cv=cv_splits_s, n_jobs=4)
cal_sist_v3.fit(X_tr_v3, y_train_sist)

res_v3_n2 = evaluar_modelo(cal_v3, vec_v3, X_test_raw, y_test_falla)
preds_sist_v3 = cal_sist_v3.predict(vec_v3.transform(X_test_raw))
acc_sist_v3 = accuracy_score(y_test_sist, preds_sist_v3) * 100.0

print(f"\n[CANDIDATO C1-V3 (Sigmoid C=1.5 Vocabulario Puro)]")
print(f"  N2 Top-1:   {res_v3_n2['top1']:.2f}% ({res_v3_n2['top1_count']}/366)")
print(f"  N2 Top-3:   {res_v3_n2['top3']:.2f}%")
print(f"  N2 F1-Macro:{res_v3_n2['f1_macro']:.2f}%")
print(f"  N1 Acc:     {acc_sist_v3:.2f}%")

# Guardar informe
reporte = {
    "baseline_c1": {
        "n2_top1": res_base_n2["top1"],
        "n2_top3": res_base_n2["top3"],
        "n2_f1_macro": res_base_n2["f1_macro"],
        "n1_acc": acc_sist_b
    },
    "candidato_v2_prep": {
        "n2_top1": res_v2_n2["top1"],
        "n2_top3": res_v2_n2["top3"],
        "n2_f1_macro": res_v2_n2["f1_macro"],
        "n1_acc": acc_sist_v2
    },
    "candidato_v3_puro": {
        "n2_top1": res_v3_n2["top1"],
        "n2_top3": res_v3_n2["top3"],
        "n2_f1_macro": res_v3_n2["f1_macro"],
        "n1_acc": acc_sist_v3
    }
}
with open("machine_learning/models/comparativa_final_test10.json", "w") as f:
    json.dump(reporte, f, indent=2)
