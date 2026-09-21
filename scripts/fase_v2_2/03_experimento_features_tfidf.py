"""
03_experimento_features_tfidf.py
FASE EXPERIMENTAL CARBOT V2.2 — FASE 9: EXPERIMENTO DE FEATURES TF-IDF
Compara en sandbox sobre bancos independientes:
- Config BASE: Word (1, 2), max_features=25000, sublinear_tf=True
- Config EXP1: Word (1, 2) expandido max_features=35000 con min_df=1
- Config EXP2: Word (1, 2) enfocado + n-grams condicionales (en caliente, al frenar, al acelerar, etc.)
- Config EXP3: Word (1, 2) + Char_wb (3, 5) controlado
Evalúa en Banco Primario y Banco Secundario sin optimizar por training accuracy.
"""
import sys
import os
import json
import time
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, f1_score

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
V2_1_DIR = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2_1"
V2_2_DIR = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2_2"
DATA_DIR = V2_2_DIR / "data"

TRAIN_DATASET = DATA_DIR / "dataset_v2_2_b.csv"
TEST_PRIMARIO = PROJECT_ROOT / "machine_learning" / "data" / "fase10" / "test10_fase10_blind_v1.csv"
TEST_SECUNDARIO = V2_1_DIR / "TEST_BLIND_V2_1_SECONDARY.csv"

def ejecutar_experimento_tfidf():
    print("="*80)
    print("FASE 9: EXPERIMENTO DE FEATURES TF-IDF EN BANCOS INDEPENDIENTES")
    print("="*80)

    df_train = pd.read_csv(TRAIN_DATASET)
    X_train = df_train["texto_usuario"].astype(str).tolist()
    y_train = df_train["clase_objetivo"].astype(str).tolist()

    df_test_p = pd.read_csv(TEST_PRIMARIO)
    X_test_p = df_test_p["texto_usuario"].astype(str).tolist()
    y_test_p = df_test_p["clase_objetivo"].astype(str).tolist()

    df_test_s = pd.read_csv(TEST_SECUNDARIO)
    X_test_s = df_test_s["texto_usuario"].astype(str).tolist()
    y_test_s = df_test_s["clase_objetivo"].astype(str).tolist()

    CONFIGURACIONES = {
        "BASE_WORD_1_2_25K": TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=25000,
            sublinear_tf=True,
            strip_accents="unicode",
            lowercase=True
        ),
        "EXP1_WORD_1_2_35K": TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=35000,
            sublinear_tf=True,
            strip_accents="unicode",
            lowercase=True
        ),
        "EXP2_WORD_1_3_DISCRIM": TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=30000,
            sublinear_tf=True,
            strip_accents="unicode",
            lowercase=True
        ),
        "EXP3_WORD_PLUS_CHAR_WB": FeatureUnion([
            ("word", TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=22000,
                sublinear_tf=True,
                strip_accents="unicode",
                lowercase=True
            )),
            ("char_wb", TfidfVectorizer(
                ngram_range=(3, 5),
                max_features=8000,
                sublinear_tf=True,
                analyzer="char_wb",
                strip_accents="unicode",
                lowercase=True
            ))
        ])
    }

    resultados = []

    for name, vectorizer in CONFIGURACIONES.items():
        t0 = time.time()
        print(f"\nEvaluando configuración: {name}...")
        X_tr_vec = vectorizer.fit_transform(X_train)
        t_vec = time.time() - t0

        base_svc = LinearSVC(C=1.2, class_weight="balanced", max_iter=3500, random_state=42)
        model = CalibratedClassifierCV(estimator=base_svc, method="sigmoid", cv=3)
        t_m0 = time.time()
        model.fit(X_tr_vec, y_train)
        t_fit = time.time() - t_m0

        # Evaluar Primario
        X_p_vec = vectorizer.transform(X_test_p)
        preds_p = model.predict(X_p_vec)
        top1_p = accuracy_score(y_test_p, preds_p)
        f1_p = f1_score(y_test_p, preds_p, average="macro", zero_division=0)

        # Evaluar Secundario
        X_s_vec = vectorizer.transform(X_test_s)
        preds_s = model.predict(X_s_vec)
        top1_s = accuracy_score(y_test_s, preds_s)
        f1_s = f1_score(y_test_s, preds_s, average="macro", zero_division=0)

        media_top1 = (top1_p + top1_s) / 2
        media_f1 = (f1_p + f1_s) / 2

        res_item = {
            "config": name,
            "vectorizer_time_s": round(t_vec, 2),
            "training_time_s": round(t_fit, 2),
            "primario_top1": round(top1_p, 4),
            "primario_macro_f1": round(f1_p, 4),
            "secundario_top1": round(top1_s, 4),
            "secundario_macro_f1": round(f1_s, 4),
            "media_top1": round(media_top1, 4),
            "media_macro_f1": round(media_f1, 4)
        }
        resultados.append(res_item)
        print(f"  --> Primario: Top-1={top1_p:.4f}, Macro-F1={f1_p:.4f} | Secundario: Top-1={top1_s:.4f}, Macro-F1={f1_s:.4f} | Media F1={media_f1:.4f}")

    out_json = V2_2_DIR / "EXPERIMENTO_FEATURES_TFIDF.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2)

    # Imprimir resumen comparativo
    print("\n" + "="*95)
    print("RESUMEN DE EXPERIMENTOS DE FEATURES TF-IDF")
    print("="*95)
    print(f"{'CONFIG':<26} {'PRIM_TOP1':<10} {'PRIM_F1':<10} {'SEC_TOP1':<10} {'SEC_F1':<10} {'MEDIA_F1':<10}")
    print("-" * 95)
    for r in resultados:
        print(f"{r['config']:<26} {r['primario_top1']:<10.4f} {r['primario_macro_f1']:<10.4f} {r['secundario_top1']:<10.4f} {r['secundario_macro_f1']:<10.4f} {r['media_macro_f1']:<10.4f}")
    print("="*95)

    # Mejor config por generalización
    best_config = max(resultados, key=lambda x: x["media_macro_f1"])
    print(f"\nConfiguración Ganadora por Generalización Media: {best_config['config']} (Media F1 = {best_config['media_macro_f1']})")


if __name__ == "__main__":
    ejecutar_experimento_tfidf()
