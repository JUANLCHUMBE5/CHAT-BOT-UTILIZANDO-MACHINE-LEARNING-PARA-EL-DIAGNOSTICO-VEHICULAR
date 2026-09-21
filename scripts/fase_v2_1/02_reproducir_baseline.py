"""
02_reproducir_baseline.py
FASE EXPERIMENTAL CARBOT V2.1 — FASE 2
Reproducción formal e independiente del Baseline Actual (Fase 10) sobre el test blind.
Genera:
- machine_learning/experimentos/carbot_v2_1/REPRODUCCION_BASELINE_V2_1.json
"""
import sys
import os
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
V2_1_DIR = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2_1"

TFIDF_ACTUAL = PROJECT_ROOT / "machine_learning" / "models" / "c1_fase10_final" / "vectorizador_c1.pkl"
SVM_ACTUAL = PROJECT_ROOT / "machine_learning" / "models" / "c1_fase10_final" / "modelo_diagnostico_c1.pkl"
TEST_BLIND = PROJECT_ROOT / "machine_learning" / "data" / "fase10" / "test10_fase10_blind_v1.csv"


def reproducir():
    print("Iniciando Fase 2: Reproduccion del Baseline Actual...")
    t0 = time.time()

    df_test = pd.read_csv(TEST_BLIND)
    X_test = df_test["texto_usuario"].astype(str).tolist()
    y_test = df_test["clase_objetivo"].astype(str).tolist()

    tfidf = joblib.load(TFIDF_ACTUAL)
    svm = joblib.load(SVM_ACTUAL)

    t_inf_0 = time.time()
    X_vec = tfidf.transform(X_test)
    probs = svm.predict_proba(X_vec)
    preds = svm.predict(X_vec)
    lat_ms = (time.time() - t_inf_0) / len(X_test) * 1000

    # Top-3
    classes = list(svm.classes_)
    top3_hits = 0
    for i, true_y in enumerate(y_test):
        top3_idx = np.argsort(probs[i])[-3:][::-1]
        top3_names = [classes[idx] for idx in top3_idx]
        if true_y in top3_names:
            top3_hits += 1

    top1 = accuracy_score(y_test, preds)
    top3 = top3_hits / len(y_test)
    macro_p = precision_score(y_test, preds, average="macro", zero_division=0)
    macro_r = recall_score(y_test, preds, average="macro", zero_division=0)
    macro_f1 = f1_score(y_test, preds, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_test, preds, average="weighted", zero_division=0)

    # Per-class F1
    f1_classes = f1_score(y_test, preds, average=None, labels=classes, zero_division=0)
    f1_por_clase = {classes[i]: round(float(f1_classes[i]), 4) for i in range(len(classes))}

    # Verificación estricta de tolerancia
    esperado_top1 = 0.8169
    esperado_top3 = 0.9317
    esperado_macro_f1 = 0.8095

    diff_top1 = abs(top1 - esperado_top1)
    diff_top3 = abs(top3 - esperado_top3)
    diff_f1 = abs(macro_f1 - esperado_macro_f1)

    tolerancia = 0.0005
    reproducido_ok = (diff_top1 < tolerancia and diff_top3 < tolerancia and diff_f1 < tolerancia)

    print(f"\nResultados de Reproduccion:")
    print(f"  Top-1 Accuracy:  {top1:.4f} (Esperado: {esperado_top1:.4f}, Delta: {diff_top1:.5f})")
    print(f"  Top-3 Accuracy:  {top3:.4f} (Esperado: {esperado_top3:.4f}, Delta: {diff_top3:.5f})")
    print(f"  Macro-F1:        {macro_f1:.4f} (Esperado: {esperado_macro_f1:.4f}, Delta: {diff_f1:.5f})")
    print(f"  Weighted-F1:     {weighted_f1:.4f}")
    print(f"  Macro Precision: {macro_p:.4f}")
    print(f"  Macro Recall:    {macro_r:.4f}")
    print(f"  Latencia:        {lat_ms:.2f} ms")
    print(f"  Dictamen:        {'REPRODUCIBLE CONFORME' if reproducido_ok else 'DIVERGENCIA'}")

    res_out = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dictamen": "REPRODUCIBLE_CONFORME" if reproducido_ok else "DIVERGENCIA",
        "tolerancia_maxima": tolerancia,
        "metricas": {
            "top_1": round(top1, 4),
            "top_3": round(top3, 4),
            "macro_precision": round(macro_p, 4),
            "macro_recall": round(macro_r, 4),
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
            "latencia_ms": round(lat_ms, 2)
        },
        "metricas_esperadas": {
            "top_1": esperado_top1,
            "top_3": esperado_top3,
            "macro_f1": esperado_macro_f1
        },
        "f1_por_clase": f1_por_clase,
        "n_muestras_test": len(X_test),
        "n_clases": len(classes)
    }

    out_file = V2_1_DIR / "REPRODUCCION_BASELINE_V2_1.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(res_out, f, indent=2, ensure_ascii=False)

    print(f"Archivo guardado: {out_file.name}")
    print(f"Tiempo total: {time.time() - t0:.2f} s")


if __name__ == "__main__":
    reproducir()
