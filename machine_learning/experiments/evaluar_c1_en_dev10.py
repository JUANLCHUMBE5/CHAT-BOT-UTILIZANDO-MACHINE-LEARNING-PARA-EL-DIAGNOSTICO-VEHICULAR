import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

ROOT = Path(".").resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

dev_path = ROOT / "machine_learning/data/fase10/dev10_v1_1_macrofix.csv"
df_dev = pd.read_csv(dev_path)

vec = joblib.load(ROOT / "machine_learning/models/c1_fase10_final/vectorizador_c1.pkl")
clf_falla = joblib.load(ROOT / "machine_learning/models/c1_fase10_final/modelo_diagnostico_c1.pkl")
clf_sist = joblib.load(ROOT / "machine_learning/models/c1_fase10_final/modelo_sistema_c1_macrofix.pkl")

X_dev = df_dev["texto_usuario"].astype(str).tolist()
y_dev_falla = df_dev["clase_objetivo"].astype(str).tolist()
y_dev_sist = df_dev["macro_sistema"].astype(str).tolist()

X_dev_vec = vec.transform(X_dev)

# Evaluacion N2 (Falla)
probs_falla = clf_falla.predict_proba(X_dev_vec)
classes_falla = list(clf_falla.classes_)
class_to_idx = {c: i for i, c in enumerate(classes_falla)}

top1_count = 0
top3_count = 0
preds_top1 = []

for i, y_true in enumerate(y_dev_falla):
    row_probs = probs_falla[i]
    top_indices = np.argsort(row_probs)[::-1][:3]
    top_classes = [classes_falla[idx] for idx in top_indices]
    preds_top1.append(top_classes[0])
    if y_true == top_classes[0]:
        top1_count += 1
    if y_true in top_classes:
        top3_count += 1

n = len(y_dev_falla)
top1_acc = (top1_count / n) * 100.0
top3_acc = (top3_count / n) * 100.0
p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
    y_dev_falla, preds_top1, average="macro", zero_division=0
)

# Evaluacion N1 (Macro-sistema)
preds_sist = clf_sist.predict(X_dev_vec)
acc_sist = accuracy_score(y_dev_sist, preds_sist) * 100.0
p_sist, r_sist, f1_sist, _ = precision_recall_fscore_support(
    y_dev_sist, preds_sist, average="macro", zero_division=0
)

print("=== BASELINE C1 EVALUADO SOBRE DEV10 (N=1725) ===")
print(f"SVM N2 (61 Clases):")
print(f"  Top-1 Accuracy: {top1_acc:.2f}% ({top1_count}/{n})")
print(f"  Top-3 Accuracy: {top3_acc:.2f}% ({top3_count}/{n})")
print(f"  Macro F1:       {f1_macro*100.0:.2f}%")
print(f"SVM N1 (7 Macros):")
print(f"  Accuracy:       {acc_sist:.2f}%")
print(f"  Macro F1:       {f1_sist*100.0:.2f}%")

res = {
    "dev_n": n,
    "top1_acc": top1_acc,
    "top3_acc": top3_acc,
    "f1_macro": f1_macro * 100.0,
    "n1_acc": acc_sist,
    "n1_f1_macro": f1_sist * 100.0
}
with open("machine_learning/models/c1_dev10_baseline_metrics.json", "w") as f:
    json.dump(res, f, indent=2)
