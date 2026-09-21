import sys
import hashlib
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)

base_dir = Path('.').resolve()
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

dir_c1 = base_dir / "machine_learning/training/fase10/candidates/C1"
ruta_vec_c1 = dir_c1 / "vectorizador_c1.pkl"
ruta_diag_c1 = dir_c1 / "modelo_diagnostico_c1.pkl"
ruta_sist_c1_old = dir_c1 / "modelo_sistema_c1.pkl"

# 1. Hashes BEFORE
h_vec_before = hashlib.sha256(ruta_vec_c1.read_bytes()).hexdigest()
h_diag_before = hashlib.sha256(ruta_diag_c1.read_bytes()).hexdigest()
h_sist_old = hashlib.sha256(ruta_sist_c1_old.read_bytes()).hexdigest()

print(f"Vectorizador C1 hash BEFORE: {h_vec_before}")
print(f"Diagnostico C1 hash BEFORE:  {h_diag_before}")

# 2. Load data
ruta_tr10_fix = base_dir / "machine_learning/data/fase10/train10_v1_1_macrofix.csv"
ruta_dev10_fix = base_dir / "machine_learning/data/fase10/dev10_v1_1_macrofix.csv"

df_tr = pd.read_csv(ruta_tr10_fix)
df_dev = pd.read_csv(ruta_dev10_fix)

X_train_text = df_tr["texto_usuario"].astype(str).tolist()
y_train_sist = df_tr["macro_sistema"].tolist()
groups_train = df_tr["id_grupo"].tolist()

X_dev_text = df_dev["texto_usuario"].astype(str).tolist()
y_dev_sist = df_dev["macro_sistema"].tolist()

# Load frozen vectorizer
vec_c1 = joblib.load(ruta_vec_c1)
print(f"Vectorizador C1 cargado: {len(vec_c1.vocabulary_)} términos")

# Vectorize X_train using existing frozen vectorizer
print("Transformando texto_usuario con vectorizador_c1...")
X_train_vec = vec_c1.transform(X_train_text)
X_dev_vec = vec_c1.transform(X_dev_text)

# 3. Train new macro-model
print("\nConfigurando StratifiedGroupKFold (n_splits=5, seed=42) para Macro-Sistemas con 7 clases...")
sgkf_s = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
cv_splits_s = list(sgkf_s.split(X_train_vec, y_train_sist, groups_train))

print("Entrenando Modelo Macro-Sistema C1 Macrofix (LinearSVC C=1.0 + Isotonic cv=5)...")
t0 = time.time()
svc_s_fix = LinearSVC(C=1.0, class_weight="balanced", random_state=42, max_iter=3000)
cal_s_fix = CalibratedClassifierCV(estimator=svc_s_fix, method="isotonic", cv=cv_splits_s)
cal_s_fix.fit(X_train_vec, y_train_sist)
t_train = round(time.time() - t0, 2)
print(f"Entrenamiento completado en {t_train}s")

# 4. Validate classes of new model
classes_fix = list(cal_s_fix.classes_)
print(f"\nClases del nuevo macro-model ({len(classes_fix)}): {classes_fix}")
expected_macros = sorted([
    "CARROCERIA_NEUMATICA", "CLIMATIZACION", "ELECTRICO",
    "FRENOS", "MOTOR", "SUSPENSION_CHASIS", "TRANSMISION"
])
assert sorted(classes_fix) == expected_macros, f"ERROR: Clases inesperadas en macrofix: {classes_fix}"
assert len(classes_fix) == 7, f"ERROR: Se esperaban 7 clases, encontradas {len(classes_fix)}"

# 5. Save as modelo_sistema_c1_macrofix.pkl (DO NOT overwrite old model)
ruta_sist_fix = dir_c1 / "modelo_sistema_c1_macrofix.pkl"
joblib.dump(cal_s_fix, ruta_sist_fix, compress=3)
# Also copy to root
joblib.dump(cal_s_fix, base_dir / "modelo_sistema_c1_macrofix.pkl", compress=3)
h_sist_fix = hashlib.sha256(ruta_sist_fix.read_bytes()).hexdigest()
print(f"Guardado {ruta_sist_fix} | SHA-256: {h_sist_fix}")

# Check old model unchanged
assert hashlib.sha256(ruta_sist_c1_old.read_bytes()).hexdigest() == h_sist_old, "ERROR: modelo_sistema_c1.pkl fue alterado!"

# 6. Verify C1 falla and vectorizer hashes AFTER
h_vec_after = hashlib.sha256(ruta_vec_c1.read_bytes()).hexdigest()
h_diag_after = hashlib.sha256(ruta_diag_c1.read_bytes()).hexdigest()
assert h_vec_before == h_vec_after, "ERROR: vectorizador_c1.pkl fue alterado!"
assert h_diag_before == h_diag_after, "ERROR: modelo_diagnostico_c1.pkl fue alterado!"
print("Verificación de inmutabilidad: vectorizador_c1 y modelo_diagnostico_c1 son 100% INTACTOS.")

# 7. Evaluate on DEV10 Macrofix
print("\n" + "="*80)
print("EVALUACIÓN DE MODELO_SISTEMA_C1_MACROFIX SOBRE DEV10 CORREGIDO (n=1725)")
print("="*80)

pred_dev_fix = cal_s_fix.predict(X_dev_vec)
probs_dev_fix = cal_s_fix.predict_proba(X_dev_vec)

acc_fix = accuracy_score(y_dev_sist, pred_dev_fix)
p_macro_fix, r_macro_fix, f1_macro_fix, _ = precision_recall_fscore_support(y_dev_sist, pred_dev_fix, average="macro", zero_division=0)
p_wt_fix, r_wt_fix, f1_wt_fix, _ = precision_recall_fscore_support(y_dev_sist, pred_dev_fix, average="weighted", zero_division=0)

print(f"Accuracy Macrofix:         {acc_fix*100:.2f}%")
print(f"Macro Precision:           {p_macro_fix*100:.2f}%")
print(f"Macro Recall:              {r_macro_fix*100:.2f}%")
print(f"Macro F1:                  {f1_macro_fix*100:.2f}%")
print(f"Weighted F1:               {f1_wt_fix*100:.2f}%")

# Metrics by class
p_cls, r_cls, f1_cls, s_cls = precision_recall_fscore_support(y_dev_sist, pred_dev_fix, labels=classes_fix, zero_division=0)
rows_cls = []
for idx, m in enumerate(classes_fix):
    rows_cls.append({
        "macro_sistema": m,
        "support": int(s_cls[idx]),
        "precision": round(float(p_cls[idx]), 4),
        "recall": round(float(r_cls[idx]), 4),
        "f1_score": round(float(f1_cls[idx]), 4)
    })
df_metrics_macro = pd.DataFrame(rows_cls)
df_metrics_macro.to_csv(base_dir / "fase10_c1_macrofix_metrics.csv", index=False, encoding="utf-8")
df_metrics_macro.to_csv(base_dir / "machine_learning/data/fase10/fase10_c1_macrofix_metrics.csv", index=False, encoding="utf-8")
print("\nMétricas por Macro-Sistema (Guardado fase10_c1_macrofix_metrics.csv):")
print(df_metrics_macro.to_string(index=False))

# Confusion Matrix 7x7
cm_fix = confusion_matrix(y_dev_sist, pred_dev_fix, labels=classes_fix)
df_cm = pd.DataFrame(cm_fix, index=classes_fix, columns=classes_fix)
df_cm.to_csv(base_dir / "fase10_c1_macrofix_confusion_matrix.csv", encoding="utf-8")
df_cm.to_csv(base_dir / "machine_learning/data/fase10/fase10_c1_macrofix_confusion_matrix.csv", encoding="utf-8")
print("\nMatriz de Confusión 7x7 (Guardado fase10_c1_macrofix_confusion_matrix.csv):")
print(df_cm)

# 8. Evaluation by Source (ORIGINAL vs SINTETICO)
print("\n" + "="*80)
print("EVALUACIÓN POR SOURCE (ORIGINAL VS SINTETICO):")
print("="*80)
df_dev["pred_macro_fix"] = pred_dev_fix
df_dev["correct_macro_fix"] = (df_dev["macro_sistema"] == pred_dev_fix).astype(int)

for src in ["ORIGINAL", "SINTETICO"]:
    sub = df_dev[df_dev["synthetic_or_original"] == src]
    n_s = len(sub)
    acc_s = accuracy_score(sub["macro_sistema"], sub["pred_macro_fix"])
    p_s, r_s, f1_s, _ = precision_recall_fscore_support(sub["macro_sistema"], sub["pred_macro_fix"], average="macro", zero_division=0)
    print(f"[{src}] n={n_s:4d} | Accuracy: {acc_s*100:6.2f}% | Macro F1: {f1_s*100:6.2f}%")

# 9. Evaluation by Level (L1, L2, L3 for synthetic)
print("\n" + "="*80)
print("EVALUACIÓN POR NIVEL SINTÉTICO (L1, L2, L3):")
print("="*80)
for lvl in ["L1", "L2", "L3"]:
    sub = df_dev[(df_dev["synthetic_or_original"] == "SINTETICO") & (df_dev["nivel_informacion"] == lvl)]
    n_l = len(sub)
    acc_l = accuracy_score(sub["macro_sistema"], sub["pred_macro_fix"])
    p_l, r_l, f1_l, _ = precision_recall_fscore_support(sub["macro_sistema"], sub["pred_macro_fix"], average="macro", zero_division=0)
    print(f"[{lvl}] n={n_l:4d} | Accuracy: {acc_l*100:6.2f}% | Macro F1: {f1_l*100:6.2f}%")

# 10. CLIMATIZACION focus
print("\n" + "="*80)
print("EVALUACIÓN CLIMATIZACION EN DEV10 (n=28):")
print("="*80)
sub_clima = df_dev[df_dev["macro_sistema"] == "CLIMATIZACION"]
n_clima = len(sub_clima)
acc_clima = accuracy_score(sub_clima["macro_sistema"], sub_clima["pred_macro_fix"])
confusiones_clima = sub_clima[sub_clima["pred_macro_fix"] != "CLIMATIZACION"]["pred_macro_fix"].value_counts().to_dict()
print(f"n={n_clima} | Accuracy: {acc_clima*100:6.2f}%")
print(f"Confusiones: {confusiones_clima if confusiones_clima else 'Ninguna (100% aciertos)'}")

# 11. Comparison: Old Macro C1 vs Macrofix on Canonical DEV10
print("\n" + "="*80)
print("COMPARACIÓN: MACRO C1 ANTIGUO VS MACROFIX SOBRE DEV10 CANÓNICO:")
print("="*80)
cal_s_old = joblib.load(ruta_sist_c1_old)
pred_old = cal_s_old.predict(X_dev_vec)
acc_old = accuracy_score(y_dev_sist, pred_old)
_, _, f1_old, _ = precision_recall_fscore_support(y_dev_sist, pred_old, average="macro", zero_division=0)
n_targets_old = len(cal_s_old.classes_)
nan_targets_old = "nan" in cal_s_old.classes_
errores_old = int(np.sum(pred_old != y_dev_sist))
errores_fix = int(np.sum(pred_dev_fix != y_dev_sist))

comp_table = pd.DataFrame([
    {"Métrica": "Accuracy", "MACRO C1 ANTIGUO": f"{acc_old*100:.2f}%", "MACROFIX": f"{acc_fix*100:.2f}%"},
    {"Métrica": "Macro F1", "MACRO C1 ANTIGUO": f"{f1_old*100:.2f}%", "MACROFIX": f"{f1_macro_fix*100:.2f}%"},
    {"Métrica": "n targets modelo", "MACRO C1 ANTIGUO": str(n_targets_old), "MACROFIX": str(len(classes_fix))},
    {"Métrica": "NaN en targets", "MACRO C1 ANTIGUO": "SÍ ('nan' class)" if nan_targets_old else "NO", "MACROFIX": "NO (0 NaN)"},
    {"Métrica": "Errores en DEV10", "MACRO C1 ANTIGUO": f"{errores_old} / 1725", "MACROFIX": f"{errores_fix} / 1725"}
])
print(comp_table.to_string(index=False))

# 12. Save metadata_c1_macrofix.json
metadata = {
    "modelo": "modelo_sistema_c1_macrofix.pkl",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "arquitectura": "LinearSVC(C=1.0, class_weight='balanced') + CalibratedClassifierCV(method='isotonic', cv=5)",
    "vectorizador_utilizado": "vectorizador_c1.pkl",
    "vectorizador_hash": h_vec_before,
    "sha256": h_sist_fix,
    "train_dataset": "train10_v1_1_macrofix.csv",
    "train_dataset_hash": hashlib.sha256(ruta_tr10_fix.read_bytes()).hexdigest(),
    "n_train": len(df_tr),
    "n_dev": len(df_dev),
    "classes": classes_fix,
    "n_classes": len(classes_fix),
    "metricas_dev10": {
        "accuracy": round(float(acc_fix), 4),
        "macro_precision": round(float(p_macro_fix), 4),
        "macro_recall": round(float(r_macro_fix), 4),
        "macro_f1": round(float(f1_macro_fix), 4),
        "weighted_f1": round(float(f1_wt_fix), 4)
    },
    "metricas_por_source": {
        "original": {
            "n": int(len(df_dev[df_dev['synthetic_or_original'] == 'ORIGINAL'])),
            "accuracy": round(float(accuracy_score(df_dev[df_dev['synthetic_or_original'] == 'ORIGINAL']['macro_sistema'], df_dev[df_dev['synthetic_or_original'] == 'ORIGINAL']['pred_macro_fix'])), 4)
        },
        "sintetico": {
            "n": int(len(df_dev[df_dev['synthetic_or_original'] == 'SINTETICO'])),
            "accuracy": round(float(accuracy_score(df_dev[df_dev['synthetic_or_original'] == 'SINTETICO']['macro_sistema'], df_dev[df_dev['synthetic_or_original'] == 'SINTETICO']['pred_macro_fix'])), 4)
        }
    }
}

with open(dir_c1 / "metadata_c1_macrofix.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

with open(base_dir / "metadata_c1_macrofix.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

print("\nGuardado metadata_c1_macrofix.json exitosamente.")
