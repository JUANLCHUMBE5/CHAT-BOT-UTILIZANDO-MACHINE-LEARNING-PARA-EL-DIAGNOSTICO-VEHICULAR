import json
import logging
import re
import sys
import time
import unicodedata
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.svm import LinearSVC

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s"
)
logger = logging.getLogger("SVMOptimizer")

ROOT = Path(".").resolve()
train_path = ROOT / "machine_learning/data/fase10/train10_v1_1_macrofix.csv"
dev_path = ROOT / "machine_learning/data/fase10/dev10_v1_1_macrofix.csv"

df_train = pd.read_csv(train_path)
df_dev = pd.read_csv(dev_path)

X_train_raw = df_train["texto_usuario"].astype(str).tolist()
y_train_falla = df_train["clase_objetivo"].astype(str).tolist()
y_train_sist = df_train["macro_sistema"].astype(str).tolist()
groups_train = df_train["id_grupo"].tolist()

X_dev_raw = df_dev["texto_usuario"].astype(str).tolist()
y_dev_falla = df_dev["clase_objetivo"].astype(str).tolist()
y_dev_sist = df_dev["macro_sistema"].astype(str).tolist()

# Preprocesador con manejo explícito de negaciones automotrices
def preprocesar_texto_automotriz(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    # Unificar negaciones clave automotrices con guion bajo para capturar el token compuesto
    t = re.sub(r"\bno\s+arranca\b", "no_arranca", t)
    t = re.sub(r"\bno\s+enciende\b", "no_enciende", t)
    t = re.sub(r"\bno\s+prende\b", "no_prende", t)
    t = re.sub(r"\bno\s+frena\b", "no_frena", t)
    t = re.sub(r"\bno\s+entra\b", "no_entra", t)
    t = re.sub(r"\bno\s+sube\b", "no_sube", t)
    t = re.sub(r"\bno\s+baja\b", "no_baja", t)
    t = re.sub(r"\bno\s+carga\b", "no_carga", t)
    t = re.sub(r"\bno\s+retiene\b", "no_retiene", t)
    t = re.sub(r"\bsin\s+fuerza\b", "sin_fuerza", t)
    t = re.sub(r"\bsin\s+chispa\b", "sin_chispa", t)
    t = re.sub(r"\bsin\s+presion\b", "sin_presion", t)
    t = re.sub(r"\bcheck\s+engine\b", "check_engine", t)
    t = re.sub(r"[^\w\s_]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def evaluar_modelo(clf, vec, X_dev_texts, y_dev_falla, y_dev_sist=None, clf_sist=None):
    X_dev_v = vec.transform(X_dev_texts)
    probs = clf.predict_proba(X_dev_v)
    classes = list(clf.classes_)
    
    top1 = 0
    top3 = 0
    preds_top1 = []
    
    for i, true_y in enumerate(y_dev_falla):
        row_p = probs[i]
        top_idx = np.argsort(row_p)[::-1][:3]
        top_c = [classes[idx] for idx in top_idx]
        preds_top1.append(top_c[0])
        if true_y == top_c[0]:
            top1 += 1
        if true_y in top_c:
            top3 += 1
            
    n = len(y_dev_falla)
    top1_pct = (top1 / n) * 100.0
    top3_pct = (top3 / n) * 100.0
    p_m, r_m, f1_m, _ = precision_recall_fscore_support(
        y_dev_falla, preds_top1, average="macro", zero_division=0
    )
    
    res = {
        "top1": top1_pct,
        "top3": top3_pct,
        "f1_macro": f1_m * 100.0,
        "top1_count": top1,
        "n": n
    }
    return res

sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
cv_splits = list(sgkf.split(X_train_raw, y_train_falla, groups_train))

experimentos = [
    {
        "nombre": "EXP_0_BASELINE_REPRODUCIDO",
        "prep": False,
        "ngram": (1, 2),
        "max_features": 25000,
        "C": 1.2,
        "method": "isotonic"
    },
    {
        "nombre": "EXP_1_PREP_NEGACIONES_C1.2",
        "prep": True,
        "ngram": (1, 2),
        "max_features": 25000,
        "C": 1.2,
        "method": "isotonic"
    },
    {
        "nombre": "EXP_2_PREP_NEGACIONES_C1.0",
        "prep": True,
        "ngram": (1, 2),
        "max_features": 25000,
        "C": 1.0,
        "method": "isotonic"
    },
    {
        "nombre": "EXP_3_PREP_NEGACIONES_C1.5",
        "prep": True,
        "ngram": (1, 2),
        "max_features": 25000,
        "C": 1.5,
        "method": "isotonic"
    },
    {
        "nombre": "EXP_4_PREP_NGRAM1_3_C1.2",
        "prep": True,
        "ngram": (1, 3),
        "max_features": 35000,
        "C": 1.2,
        "method": "isotonic"
    },
    {
        "nombre": "EXP_5_PREP_SIGMOID_C1.2",
        "prep": True,
        "ngram": (1, 2),
        "max_features": 25000,
        "C": 1.2,
        "method": "sigmoid"
    }
]

resultados = []

for exp in experimentos:
    logger.info(f"\n=======================================================")
    logger.info(f"EJECUTANDO: {exp['nombre']}")
    logger.info(f"Config: {exp}")
    t0 = time.time()
    
    if exp["prep"]:
        X_train_proc = [preprocesar_texto_automotriz(t) for t in X_train_raw]
        X_dev_proc = [preprocesar_texto_automotriz(t) for t in X_dev_raw]
    else:
        X_train_proc = X_train_raw
        X_dev_proc = X_dev_raw
        
    vec = TfidfVectorizer(
        ngram_range=exp["ngram"],
        sublinear_tf=True,
        strip_accents="unicode",
        min_df=1,
        max_features=exp["max_features"]
    )
    X_train_v = vec.fit_transform(X_train_proc)
    
    svc = LinearSVC(
        C=exp["C"],
        class_weight="balanced",
        random_state=42,
        max_iter=3500
    )
    cal_clf = CalibratedClassifierCV(
        estimator=svc,
        method=exp["method"],
        cv=cv_splits,
        n_jobs=4
    )
    cal_clf.fit(X_train_v, y_train_falla)
    
    t_train = time.time() - t0
    logger.info(f"Entrenamiento completado en {t_train:.2f}s")
    
    eval_res = evaluar_modelo(cal_clf, vec, X_dev_proc, y_dev_falla)
    logger.info(f"RESULTADOS DEV10: Top-1={eval_res['top1']:.2f}% | Top-3={eval_res['top3']:.2f}% | F1-Macro={eval_res['f1_macro']:.2f}%")
    
    exp_record = {
        **exp,
        "t_train_s": round(t_train, 2),
        **eval_res
    }
    resultados.append(exp_record)

out_file = ROOT / "machine_learning/models/resultados_experimentos_svm_dev10.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(resultados, f, indent=2)

logger.info(f"\nTodos los experimentos completados. Guardados en: {out_file}")
