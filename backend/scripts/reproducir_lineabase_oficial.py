import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from src.config import settings
from src.infrastructure.motor_rag import MotorRAG

print("=== 1. VERIFICANDO SVM EN TEST10 BLIND SET (N=366) ===")
test10_path = Path("machine_learning/data/fase10/test10_fase10_blind_v1.csv")
df_test = pd.read_csv(test10_path)
print(f"Muestras en test ciego: {len(df_test)}, clases unicas: {df_test['clase_objetivo'].nunique()}")

# Cargar SVM N2
vec_n2 = joblib.load(settings.paths.vectorizer_pkl)
svm_n2 = joblib.load(settings.paths.model_pkl)

# Cargar SVM N1
svm_n1 = joblib.load(settings.paths.modelo_sistema_pkl)

X_test_vec = vec_n2.transform(df_test["texto_usuario"].fillna(""))
y_test_true = df_test["clase_objetivo"]

# Inferencia N2
t0 = time.perf_counter()
y_pred_n2 = svm_n2.predict(X_test_vec)
lat_svm = (time.perf_counter() - t0) * 1000.0 / len(df_test)

# Probabilidades Top-3
probs_n2 = svm_n2.predict_proba(X_test_vec)
classes_n2 = svm_n2.classes_
top3_correct = 0
for i, true_label in enumerate(y_test_true):
    top3_idx = np.argsort(probs_n2[i])[-3:]
    top3_classes = classes_n2[top3_idx]
    if true_label in top3_classes:
        top3_correct += 1

top1_n2 = accuracy_score(y_test_true, y_pred_n2)
top3_n2 = top3_correct / len(df_test)
f1_macro_n2 = f1_score(y_test_true, y_pred_n2, average="macro", zero_division=0)
prec_macro_n2 = precision_score(y_test_true, y_pred_n2, average="macro", zero_division=0)
rec_macro_n2 = recall_score(y_test_true, y_pred_n2, average="macro", zero_division=0)

# Inferencia N1
y_macro_true = df_test["macro_sistema"].str.upper()
y_pred_n1 = svm_n1.predict(X_test_vec)
acc_n1 = accuracy_score(y_macro_true, pd.Series(y_pred_n1).str.upper())

print(f"SVM N2 Top-1: {top1_n2*100:.2f}% | Top-3: {top3_n2*100:.2f}% | F1 Macro: {f1_macro_n2*100:.2f}%")
print(f"SVM N1 Accuracy: {acc_n1*100:.2f}%")
print(f"Latencia promedio inferencia SVM: {lat_svm:.2f} ms")

print("\n=== 2. VERIFICANDO RAG ACTUAL EN BENCHMARK 122 ===")
rag = MotorRAG()
bench_path = Path("machine_learning/manuals/candidates/v1/benchmarks/benchmark_dataset.json")
with open(bench_path, "r", encoding="utf-8") as f:
    bench_data = json.load(f)
queries = bench_data["queries"]

latencias_rag = []
hit_at_1 = 0
contaminacion_macro = 0

for q_obj in queries:
    q = q_obj["query"]
    exp_falla = q_obj["expected_class_name"]
    exp_macro = q_obj.get("expected_macro", "").upper()
    top_fallas = [{"falla": exp_falla, "probabilidad": 0.85}]

    t0 = time.perf_counter()
    doc_text, nivel, sim, meta = rag.recuperar_procedimiento_con_metadatos(
        consulta=q, top_fallas=top_fallas, macro_sistema=exp_macro
    )
    lat = (time.perf_counter() - t0) * 1000.0
    latencias_rag.append(lat)

    falla_ret = (
        meta.get("primary_fault_class")
        or meta.get("falla")
        or meta.get("titulo")
        or ""
    ).strip().lower()
    macro_ret = (meta.get("system") or meta.get("sistema") or "").strip().upper()

    coincide_falla = (
        exp_falla.lower() in falla_ret or falla_ret in exp_falla.lower()
    ) if falla_ret else False
    if coincide_falla or (sim > 0.40 and exp_macro == macro_ret):
        hit_at_1 += 1

    if macro_ret and exp_macro and macro_ret != exp_macro and sim > 0.15:
        contaminacion_macro += 1

hit1_pct = (hit_at_1 / len(queries)) * 100.0
contam_pct = (contaminacion_macro / len(queries)) * 100.0
lat_p50 = float(np.percentile(latencias_rag, 50))
lat_p95 = float(np.percentile(latencias_rag, 95))

print(f"RAG Hit@1: {hit1_pct:.2f}% ({hit_at_1}/{len(queries)})")
print(f"RAG Contaminacion Macrosistema: {contam_pct:.2f}% ({contaminacion_macro}/{len(queries)})")
print(f"RAG Latencia p50: {lat_p50:.2f} ms | p95: {lat_p95:.2f} ms")

baseline_summary = {
    "svm_n2_top1": top1_n2,
    "svm_n2_top3": top3_n2,
    "svm_n2_f1_macro": f1_macro_n2,
    "svm_n1_accuracy": acc_n1,
    "rag_hit1": hit1_pct,
    "rag_contaminacion_macro": contam_pct,
    "rag_latencia_p50": lat_p50,
    "rag_latencia_p95": lat_p95,
}
with open("machine_learning/models/baseline_metricas_oficial.json", "w", encoding="utf-8") as f:
    json.dump(baseline_summary, f, indent=2)
print("\nLineabase guardada exitosamente en machine_learning/models/baseline_metricas_oficial.json")
