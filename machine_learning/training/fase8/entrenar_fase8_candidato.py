"""
Pipeline de Entrenamiento y Optimización de Hiperparámetros Fase 8 (Linear SVM + TF-IDF).
Cumple con la Regla 1 de Arquitectura de Tesis (Linear SVM estricto, sin Random Forest ni XGBoost).
Selecciona hiperparámetros evaluando exclusivamente en el conjunto DEV independiente.
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema
from machine_learning.training.fase8.evaluar_dev_60_casos import evaluar_modelo_en_dev

DATA_CANONICA = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"
MODEL_DIR = BASE_DIR / "machine_learning" / "models"

def calcular_sha256(ruta_archivo: Path) -> str:
    h = hashlib.sha256()
    with open(ruta_archivo, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def entrenar_fase8():
    print("=" * 80)
    print("INICIO DE ENTRENAMIENTO CANDIDATO FASE 8 (LINEAR SVM + TF-IDF)")
    print("=" * 80)

    print(f"Cargando dataset canónico: {DATA_CANONICA}")
    df = pd.read_csv(DATA_CANONICA, encoding="utf-8")
    df = df.dropna(subset=["sintoma", "falla"])
    df["sintoma"] = df["sintoma"].astype(str).str.strip()
    df["falla"] = df["falla"].astype(str).str.strip()
    df["macro_sistema"] = df["falla"].apply(obtener_macro_sistema)

    print(f"Registros totales: {len(df)} | Clases de falla: {df['falla'].nunique()} | Macro-Sistemas: {df['macro_sistema'].nunique()}")

    X = df["sintoma"].values
    y_falla = df["falla"].values
    y_sistema = df["macro_sistema"].values

    # Búsqueda en rejilla de hiperparámetros evaluada contra DEV
    c_valores = [1.0, 1.2, 1.5, 2.0]
    pesos_clase = ["balanced", None]
    max_feats = [25000, 30000]

    mejor_acc_dev = 0.0
    mejor_config = None
    mejor_modelo_f = None
    mejor_modelo_s = None
    mejor_vec = None
    mejor_dev_metricas = None

    print("\nIniciando optimización de hiperparámetros sobre DEV (60 casos)...")

    for mf in max_feats:
        vectorizador = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
            min_df=1,
            max_features=mf,
        )
        X_vec = vectorizador.fit_transform(X)

        for cw in pesos_clase:
            for c_val in c_valores:
                # Nivel 1: Macro-Sistemas
                svc_sist = LinearSVC(C=1.0, class_weight=cw, random_state=42, max_iter=3000)
                cal_sist = CalibratedClassifierCV(estimator=svc_sist, method="sigmoid", cv=3)
                cal_sist.fit(X_vec, y_sistema)

                # Nivel 2: Fallas Específicas
                svc_falla = LinearSVC(C=c_val, class_weight=cw, random_state=42, max_iter=3500)
                cal_falla = CalibratedClassifierCV(estimator=svc_falla, method="sigmoid", cv=3)
                cal_falla.fit(X_vec, y_falla)

                # Evaluar en DEV
                metricas_dev = evaluar_modelo_en_dev(cal_falla, cal_sist, vectorizador, exponente_jerarquico=0.65)
                acc_dev = metricas_dev["acc_top1"]
                top3_dev = metricas_dev["acc_top3"]

                print(f"Config: max_features={mf}, class_weight={cw}, C={c_val} -> Top-1 DEV: {acc_dev*100:.2f}% | Top-3 DEV: {top3_dev*100:.2f}% | ECE: {metricas_dev['ece']:.4f}")

                if acc_dev > mejor_acc_dev or (acc_dev == mejor_acc_dev and top3_dev > (mejor_dev_metricas.get("acc_top3", 0) if mejor_dev_metricas else 0)):
                    mejor_acc_dev = acc_dev
                    mejor_config = {"max_features": mf, "class_weight": cw, "C": c_val}
                    mejor_modelo_f = cal_falla
                    mejor_modelo_s = cal_sist
                    mejor_vec = vectorizador
                    mejor_dev_metricas = metricas_dev

    print("\n" + "=" * 80)
    print(f"MEJOR CONFIGURACION SELECCIONADA EN DEV:")
    print(f"  {mejor_config}")
    print(f"  Top-1 ML en DEV: {mejor_dev_metricas['acc_top1']*100:.2f}%")
    print(f"  Top-3 ML en DEV: {mejor_dev_metricas['acc_top3']*100:.2f}%")
    print(f"  Macro-Sistema en DEV: {mejor_dev_metricas['acc_macro']*100:.2f}%")
    print(f"  Brier Score en DEV: {mejor_dev_metricas['brier_score']:.4f}")
    print(f"  ECE en DEV: {mejor_dev_metricas['ece']:.4f}")
    print(f"  Accuracy (conf >= 80%): {mejor_dev_metricas['accuracy_alta_confianza_gte_80']*100:.2f}%")
    print("=" * 80)

    # Exportar los modelos candidatos Fase 8
    ruta_modelo = MODEL_DIR / "modelo_diagnostico.pkl"
    ruta_sistema = MODEL_DIR / "modelo_sistema.pkl"
    ruta_vec = MODEL_DIR / "vectorizador_tfidf.pkl"

    joblib.dump(mejor_modelo_f, ruta_modelo, compress=3)
    joblib.dump(mejor_modelo_s, ruta_sistema, compress=3)
    joblib.dump(mejor_vec, ruta_vec, compress=3)

    hash_dataset = calcular_sha256(DATA_CANONICA)
    hash_modelo = calcular_sha256(ruta_modelo)
    hash_sistema = calcular_sha256(ruta_sistema)
    hash_vec = calcular_sha256(ruta_vec)

    registro_fase8 = {
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
        "fase": "Fase 8 - Candidato",
        "dataset": {
            "archivo": str(DATA_CANONICA),
            "filas": len(df),
            "clases": int(df["falla"].nunique()),
            "macro_sistemas": int(df["macro_sistema"].nunique()),
            "sha256": hash_dataset,
        },
        "hiperparametros_seleccionados_en_dev": mejor_config,
        "desempeno_benchmark_dev_60_casos": mejor_dev_metricas,
        "hashes_modelos": {
            "modelo_diagnostico_pkl": hash_modelo,
            "modelo_sistema_pkl": hash_sistema,
            "vectorizador_tfidf_pkl": hash_vec,
        }
    }

    with open(MODEL_DIR / "metricas_fase8_candidato.json", "w", encoding="utf-8") as f:
        json.dump(registro_fase8, f, indent=2, ensure_ascii=False)

    print(f"\nModelos candidatos Fase 8 exportados exitosamente en: {MODEL_DIR}")
    print(f"Registro y hashes guardados en: {MODEL_DIR / 'metricas_fase8_candidato.json'}")

if __name__ == "__main__":
    entrenar_fase8()
