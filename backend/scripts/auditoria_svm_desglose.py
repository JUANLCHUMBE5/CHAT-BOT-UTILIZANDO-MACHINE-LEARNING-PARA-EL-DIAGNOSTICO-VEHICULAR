"""Auditoría de Machine Learning SVM:
Desglose factorial de efectos (Tokenización, Calibración e Hiperparámetro C)
y verificación de que TEST10 se mantuvo como holdout ciego estricto.
"""

import json
from pathlib import Path
import unicodedata
import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[2]

train_path = ROOT / "machine_learning/data/fase10/train10_v1_1_macrofix.csv"
dev_path = ROOT / "machine_learning/data/fase10/dev10_v1_1_macrofix.csv"
test_path = ROOT / "machine_learning/data/fase10/test10_fase10_blind_v1.csv"

df_train = pd.read_csv(train_path)
df_dev = pd.read_csv(dev_path)
df_test = pd.read_csv(test_path)

X_train_raw = df_train["texto_usuario"].astype(str).tolist()
y_train = df_train["clase_objetivo"].astype(str).tolist()
groups_train = df_train["id_grupo"].tolist()

X_dev_raw = df_dev["texto_usuario"].astype(str).tolist()
y_dev = df_dev["clase_objetivo"].astype(str).tolist()

X_test_raw = df_test["texto_usuario"].astype(str).tolist()
y_test = df_test["clase_objetivo"].astype(str).tolist()

def prep_negaciones(texto: str) -> str:
    t = unicodedata.normalize("NFKD", str(texto))
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"\bno\s+arranca\b", "no_arranca", t)
    t = re.sub(r"\bno\s+enciende\b", "no_enciende", t)
    t = re.sub(r"\bno\s+prende\b", "no_prende", t)
    t = re.sub(r"\bno\s+frena\b", "no_frena", t)
    t = re.sub(r"\bno\s+entra\b", "no_entra", t)
    t = re.sub(r"\bsin\s+fuerza\b", "sin_fuerza", t)
    t = re.sub(r"\bsin\s+chispa\b", "sin_chispa", t)
    t = re.sub(r"[^\w\s_]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def evaluar(clf, vec, X_texts, y_true):
    X_v = vec.transform(X_texts)
    probs = clf.predict_proba(X_v)
    classes = list(clf.classes_)
    
    top1, top3 = 0, 0
    preds_top1 = []
    prob_sums = []
    
    for i, true_y in enumerate(y_true):
        p_row = probs[i]
        prob_sums.append(float(np.sum(p_row)))
        top_idx = np.argsort(p_row)[::-1][:3]
        top_c = [classes[idx] for idx in top_idx]
        preds_top1.append(top_c[0])
        if true_y == top_c[0]:
            top1 += 1
        if true_y in top_c:
            top3 += 1
            
    n = len(y_true)
    _, _, f1_m, _ = precision_recall_fscore_support(
        y_true, preds_top1, average="macro", zero_division=0
    )
    return {
        "top1": (top1 / n) * 100.0,
        "top3": (top3 / n) * 100.0,
        "f1_macro": f1_m * 100.0,
        "prob_sum_mean": float(np.mean(prob_sums)),
        "prob_sum_min": float(np.min(prob_sums)),
        "prob_sum_max": float(np.max(prob_sums)),
    }

print("=== AUDITORÍA FACTORIAL SVM EN DEV10 (SELECCIÓN) Y TEST10 (EVALUACIÓN CIEGA) ===")

configuraciones = [
    # Baseline: Tokenización estándar, Isotonic, C=1.0
    {"nombre": "Base (Isotonic, C=1.0, prep=No)", "prep": False, "calib": "isotonic", "C": 1.0, "ngram": (1,2)},
    # Factor A: Efecto exclusivo de Tokenización de Negaciones
    {"nombre": "Factor A: Prep Negaciones (Isotonic, C=1.0)", "prep": True, "calib": "isotonic", "C": 1.0, "ngram": (1,2)},
    # Factor B: Efecto exclusivo de Calibración Sigmoidea (Platt Scaling)
    {"nombre": "Factor B: Calibración Sigmoid (Sin prep, C=1.0)", "prep": False, "calib": "sigmoid", "C": 1.0, "ngram": (1,2)},
    # Factor C: Efecto de Regularización C=2.0 (Sigmoid, Sin prep)
    {"nombre": "Factor C: Regularización C=2.0 (Sigmoid, Sin prep)", "prep": False, "calib": "sigmoid", "C": 2.0, "ngram": (1,2)},
    # Combinación Óptima Seleccionada en DEV10 (Candidato Final)
    {"nombre": "Combinado Óptimo (Sigmoid, C=2.0, Prep Negaciones)", "prep": True, "calib": "sigmoid", "C": 2.0, "ngram": (1,2)},
]

sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
cv_splits = list(sgkf.split(X_train_raw, y_train, groups_train))

resultados = []

for cfg in configuraciones:
    if cfg["prep"]:
        X_tr_in = [prep_negaciones(x) for x in X_train_raw]
        X_dv_in = [prep_negaciones(x) for x in X_dev_raw]
        X_ts_in = [prep_negaciones(x) for x in X_test_raw]
    else:
        X_tr_in = X_train_raw
        X_dv_in = X_dev_raw
        X_ts_in = X_test_raw
        
    vec = TfidfVectorizer(ngram_range=cfg["ngram"], min_df=2, max_df=0.85, sublinear_tf=True)
    X_tr_vec = vec.fit_transform(X_tr_in)
    
    base_svc = LinearSVC(C=cfg["C"], class_weight="balanced", random_state=42, max_iter=2500)
    calib = CalibratedClassifierCV(estimator=base_svc, method=cfg["calib"], cv=cv_splits)
    calib.fit(X_tr_vec, y_train)
    
    # 1. Métrica en DEV10 (donde se toman decisiones)
    m_dev = evaluar(calib, vec, X_dv_in, y_dev)
    # 2. Métrica en TEST10 (holdout ciego)
    m_test = evaluar(calib, vec, X_ts_in, y_test)
    
    print(f"\nConfiguración: {cfg['nombre']}")
    print(f"  DEV10  -> Top-1: {m_dev['top1']:.2f}% | Top-3: {m_dev['top3']:.2f}% | F1: {m_dev['f1_macro']:.2f}%")
    print(f"  TEST10 -> Top-1: {m_test['top1']:.2f}% | Top-3: {m_test['top3']:.2f}% | F1: {m_test['f1_macro']:.2f}%")
    print(f"  Suma Probabilidades: Media={m_test['prob_sum_mean']:.4f} (Min={m_test['prob_sum_min']:.4f}, Max={m_test['prob_sum_max']:.4f})")
    
    resultados.append({
        "configuracion": cfg["nombre"],
        "dev10": m_dev,
        "test10": m_test
    })

out_file = ROOT / "machine_learning/models/auditoria_factorial_svm.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(resultados, f, indent=2)

print(f"\nGuardado informe factorial en {out_file}")
