import json
import logging
import time
from pathlib import Path

import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.svm import LinearSVC

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("MacroOptimizer")

ROOT = Path(".").resolve()
train_path = ROOT / "machine_learning/data/fase10/train10_v1_1_macrofix.csv"
dev_path = ROOT / "machine_learning/data/fase10/dev10_v1_1_macrofix.csv"

df_train = pd.read_csv(train_path)
df_dev = pd.read_csv(dev_path)

X_train_raw = df_train["texto_usuario"].astype(str).tolist()
y_train_sist = df_train["macro_sistema"].astype(str).tolist()
groups_train = df_train["id_grupo"].tolist()

X_dev_raw = df_dev["texto_usuario"].astype(str).tolist()
y_dev_sist = df_dev["macro_sistema"].astype(str).tolist()

sgkf_s = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
cv_splits_s = list(sgkf_s.split(X_train_raw, y_train_sist, groups_train))

vec = TfidfVectorizer(
    ngram_range=(1, 2),
    sublinear_tf=True,
    strip_accents="unicode",
    min_df=1,
    max_features=25000
)
X_train_v = vec.fit_transform(X_train_raw)
X_dev_v = vec.transform(X_dev_raw)

experimentos = [
    {"nombre": "N1_ISOTONIC_C1.0 (BASELINE)", "C": 1.0, "method": "isotonic"},
    {"nombre": "N1_ISOTONIC_C1.2", "C": 1.2, "method": "isotonic"},
    {"nombre": "N1_SIGMOID_C1.0", "C": 1.0, "method": "sigmoid"},
    {"nombre": "N1_SIGMOID_C1.2", "C": 1.2, "method": "sigmoid"},
    {"nombre": "N1_SIGMOID_C1.5", "C": 1.5, "method": "sigmoid"},
]

resultados = []
for exp in experimentos:
    t0 = time.time()
    svc = LinearSVC(C=exp["C"], class_weight="balanced", random_state=42, max_iter=3000)
    cal = CalibratedClassifierCV(estimator=svc, method=exp["method"], cv=cv_splits_s, n_jobs=4)
    cal.fit(X_train_v, y_train_sist)
    t_train = time.time() - t0
    
    preds = cal.predict(X_dev_v)
    acc = accuracy_score(y_dev_sist, preds) * 100.0
    p_m, r_m, f1_m, _ = precision_recall_fscore_support(y_dev_sist, preds, average="macro", zero_division=0)
    
    logger.info(f"[{exp['nombre']}] Acc: {acc:.2f}% | F1-Macro: {f1_m*100.0:.2f}% (train: {t_train:.1f}s)")
    resultados.append({**exp, "acc": acc, "f1_macro": f1_m * 100.0, "t_train": round(t_train, 2)})

with open("machine_learning/models/resultados_macro_dev10.json", "w") as f:
    json.dump(resultados, f, indent=2)
