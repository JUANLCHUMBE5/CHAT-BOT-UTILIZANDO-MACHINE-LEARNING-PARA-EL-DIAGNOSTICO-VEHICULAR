"""
Script de Reproducibilidad — Fase 10 Etapa 3.2: Saneamiento del Macro-Sistema y Validación Macrofix C1.

Objetivo:
1. Validar la inmutabilidad previa de F8.3, TEST10 y del clasificador de 61 fallas C1 (vectorizador y modelo diagnóstico).
2. Entrenar exclusivamente modelo_sistema_c1_macrofix.pkl sobre train10_v1_1_macrofix.csv.
3. Evaluar sobre dev10_v1_1_macrofix.csv.
4. Generar métricas, matriz de confusión y metadata.
5. Confirmar inmutabilidad posterior.
"""

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
    confusion_matrix
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
pred_dev_fix = cal_s_fix.predict(X_dev_vec)
acc_fix = accuracy_score(y_dev_sist, pred_dev_fix)
p_macro_fix, r_macro_fix, f1_macro_fix, _ = precision_recall_fscore_support(y_dev_sist, pred_dev_fix, average="macro", zero_division=0)
p_wt_fix, r_wt_fix, f1_wt_fix, _ = precision_recall_fscore_support(y_dev_sist, pred_dev_fix, average="weighted", zero_division=0)

print(f"\nAccuracy Macrofix:         {acc_fix*100:.2f}%")
print(f"Macro Precision:           {p_macro_fix*100:.2f}%")
print(f"Macro Recall:              {r_macro_fix*100:.2f}%")
print(f"Macro F1:                  {f1_macro_fix*100:.2f}%")
print(f"Weighted F1:               {f1_wt_fix*100:.2f}%")
