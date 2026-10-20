import json
import logging
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

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("SigmoidGrid")

ROOT = Path(".").resolve()
train_path = ROOT / "machine_learning/data/fase10/train10_v1_1_macrofix.csv"
dev_path = ROOT / "machine_learning/data/fase10/dev10_v1_1_macrofix.csv"

df_train = pd.read_csv(train_path)
df_dev = pd.read_csv(dev_path)

X_train_raw = df_train["texto_usuario"].astype(str).tolist()
y_train_falla = df_train["clase_objetivo"].astype(str).tolist()
groups_train = df_train["id_grupo"].tolist()

X_dev_raw = df_dev["texto_usuario"].astype(str).tolist()
y_dev_falla = df_dev["clase_objetivo"].astype(str).tolist()

sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
cv_splits = list(sgkf.split(X_train_raw, y_train_falla, groups_train))

# Probar C con Sigmoid tanto con prep=False (vocabulario puro) como prep=True
grid = [
    {"nombre": "SIGMOID_NOPREP_C1.0", "prep": False, "C": 1.0},
    {"nombre": "SIGMOID_NOPREP_C1.2", "prep": False, "C": 1.2},
    {"nombre": "SIGMOID_NOPREP_C1.5", "prep": False, "C": 1.5},
    {"nombre": "SIGMOID_NOPREP_C2.0", "prep": False, "C": 2.0},
    {"nombre": "SIGMOID_PREP_C1.0", "prep": True, "C": 1.0},
    {"nombre": "SIGMOID_PREP_C1.2", "prep": True, "C": 1.2},
    {"nombre": "SIGMOID_PREP_C1.5", "prep": True, "C": 1.5},
    {"nombre": "SIGMOID_PREP_C2.0", "prep": True, "C": 2.0},
]

resultados = []

for item in grid:
    t0 = time.time()
    if item["prep"]:
        X_tr = [preprocesar_texto_automotriz(t) for t in X_train_raw]
        X_de = [preprocesar_texto_automotriz(t) for t in X_dev_raw]
    else:
        X_tr = X_train_raw
        X_de = X_dev_raw
        
    vec = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        strip_accents="unicode",
        min_df=1,
        max_features=25000
    )
    X_tr_v = vec.fit_transform(X_tr)
    
    svc = LinearSVC(
        C=item["C"],
        class_weight="balanced",
        random_state=42,
        max_iter=3500
    )
    cal_clf = CalibratedClassifierCV(
        estimator=svc,
        method="sigmoid",
        cv=cv_splits,
        n_jobs=4
    )
    cal_clf.fit(X_tr_v, y_train_falla)
    t_train = time.time() - t0
    
    eval_res = evaluar_modelo(cal_clf, vec, X_de, y_dev_falla)
    logger.info(f"[{item['nombre']}] ({t_train:.1f}s) -> Top-1: {eval_res['top1']:.2f}% | Top-3: {eval_res['top3']:.2f}% | F1-Macro: {eval_res['f1_macro']:.2f}%")
    resultados.append({**item, **eval_res, "t_train": round(t_train, 2)})

with open("machine_learning/models/resultados_sigmoid_grid_dev10.json", "w") as f:
    json.dump(resultados, f, indent=2)

best = max(resultados, key=lambda x: (x["top1"], x["f1_macro"]))
logger.info(f"\nMEJOR MODELO EN DEV10: {best['nombre']} con Top-1={best['top1']:.2f}%, F1-Macro={best['f1_macro']:.2f}%")
