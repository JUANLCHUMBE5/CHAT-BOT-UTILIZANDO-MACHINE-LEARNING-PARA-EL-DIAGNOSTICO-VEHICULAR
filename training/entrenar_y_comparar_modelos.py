"""
Entrenamiento y comparación rigurosa de clasificadores supervisados con validación cruzada estratificada,
calibración de probabilidades con CalibratedClassifierCV y hashing criptográfico de artefactos.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.naive_bayes import ComplementNB
from sklearn.svm import LinearSVC

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from src.core.taxonomy.catalogo_fallas import CATALOGO_TAXONOMIA


def calcular_sha256(ruta_archivo: Path) -> str:
    """Calcula el hash SHA-256 de un artefacto para trazabilidad de auditoría."""
    hasher = hashlib.sha256()
    with open(ruta_archivo, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def entrenar_y_comparar():
    print("=" * 80)
    print("FASE 3: COMPARACION Y CALIBRACION DE MODELOS DE MACHINE LEARNING")
    print("=" * 80)

    dataset_path = Path("data/dataset_sintomas_limpio.csv")
    if not dataset_path.exists():
        dataset_path = Path("data/dataset_sintomas.csv")

    df = pd.read_csv(dataset_path, encoding="utf-8")
    print(f"Dataset cargado: {len(df)} registros | {df['falla'].nunique()} clases unificadas.")

    X = df["sintoma"].astype(str)
    y = df["falla"].astype(str)

    # 1. Separación rigurosa antes de TF-IDF para impedir fuga de datos
    X_train_text, X_test_text, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    vectorizador = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
    )
    X_train = vectorizador.fit_transform(X_train_text)
    X_test = vectorizador.transform(X_test_text)

    # 2. Definición de algoritmos candidatos para clasificación de texto
    candidatos = {
        "Random_Forest": RandomForestClassifier(
            n_estimators=100, random_state=42, class_weight="balanced", n_jobs=1
        ),
        "Logistic_Regression": LogisticRegression(
            C=10.0, max_iter=1000, random_state=42, class_weight="balanced"
        ),
        "Linear_SVM_Calibrado": CalibratedClassifierCV(
            LinearSVC(C=1.0, random_state=42, dual=False, max_iter=2000), cv=3
        ),
        "Complement_Naive_Bayes": ComplementNB(alpha=0.5),
    }

    # 3. Validación cruzada estratificada 5-Fold sobre el set de entrenamiento
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    resultados_cv = {}

    print("\n--- VALIDACION CRUZADA ESTRATIFICADA (5-FOLD CROSS VALIDATION) ---")
    for nombre, clf in candidatos.items():
        scores_f1 = cross_val_score(clf, X_train, y_train, cv=cv, scoring="f1_macro", n_jobs=1)
        media_f1 = float(np.mean(scores_f1))
        std_f1 = float(np.std(scores_f1))
        resultados_cv[nombre] = {"media_f1_macro": media_f1, "desviacion_std": std_f1}
        print(f"• {nombre:25s}: F1-Macro CV = {media_f1*100:.2f}% (±{std_f1*100:.2f}%)")

    # 4. Evaluación en Test Set
    print("\n--- EVALUACION EN TEST SET INDEPENDIENTE (HOLDOUT 20%) ---")
    mejor_modelo = None
    mejor_f1 = -1.0
    mejor_nombre = ""

    for nombre, clf in candidatos.items():
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        acc = accuracy_score(y_test, preds)
        f1_m = f1_score(y_test, preds, average="macro", zero_division=0)
        f1_w = f1_score(y_test, preds, average="weighted", zero_division=0)

        print(f"[{nombre}] Accuracy: {acc*100:.2f}% | F1-Macro: {f1_m*100:.2f}% | F1-Weighted: {f1_w*100:.2f}%")

        if f1_m > mejor_f1:
            mejor_f1 = f1_m
            mejor_modelo = clf
            mejor_nombre = nombre

    print(f"\n=> Algoritmo seleccionado: {mejor_nombre} con F1-Macro = {mejor_f1*100:.2f}%")

    # 5. Ajuste final con 100% de datos con vectorizador y calibrador
    vectorizador_final = TfidfVectorizer(
        lowercase=True, strip_accents="unicode", ngram_range=(1, 2), sublinear_tf=True
    )
    X_completo = vectorizador_final.fit_transform(X)

    # Entrenar clasificador calibrado final
    if mejor_nombre == "Linear_SVM_Calibrado":
        modelo_produccion = CalibratedClassifierCV(
            LinearSVC(C=1.0, random_state=42, dual=False, max_iter=2000), cv=3
        )
    elif mejor_nombre == "Logistic_Regression":
        modelo_produccion = LogisticRegression(C=10.0, max_iter=1000, random_state=42, class_weight="balanced")
    elif mejor_nombre == "Complement_Naive_Bayes":
        modelo_produccion = CalibratedClassifierCV(ComplementNB(alpha=0.5), cv=3)
    else:
        modelo_produccion = RandomForestClassifier(
            n_estimators=100, random_state=42, class_weight="balanced", n_jobs=1
        )

    modelo_produccion.fit(X_completo, y)

    # 6. Exportar artefactos en models/
    os.makedirs("models", exist_ok=True)
    ruta_modelo = Path("models/modelo_diagnostico.pkl")
    ruta_vectorizador = Path("models/vectorizador_tfidf.pkl")
    ruta_metricas = Path("models/metricas_modelo.json")

    joblib.dump(modelo_produccion, ruta_modelo, compress=3)
    joblib.dump(vectorizador_final, ruta_vectorizador, compress=3)

    hash_modelo = calcular_sha256(ruta_modelo)
    hash_vectorizador = calcular_sha256(ruta_vectorizador)

    metadatos_completos = {
        "version": "2.0.0-calibrated",
        "algoritmo_ganador": mejor_nombre,
        "exactitud_test": float(accuracy_score(y_test, mejor_modelo.predict(X_test))),
        "f1_macro_test": float(mejor_f1),
        "f1_weighted_test": float(f1_score(y_test, mejor_modelo.predict(X_test), average="weighted", zero_division=0)),
        "cv_5fold": resultados_cv,
        "registros_entrenamiento": int(len(df)),
        "clases_totales": int(df["falla"].nunique()),
        "sha256_modelo": hash_modelo,
        "sha256_vectorizador": hash_vectorizador,
        "umbral_baja_confianza": 0.35,
    }

    ruta_metricas.write_text(json.dumps(metadatos_completos, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 80)
    print("ARTEFACTOS DE PRODUCCION GENERADOS CON EXITO:")
    print(f"  - {ruta_modelo} (SHA-256: {hash_modelo[:16]}...)")
    print(f"  - {ruta_vectorizador} (SHA-256: {hash_vectorizador[:16]}...)")
    print(f"  - {ruta_metricas}")
    print("=" * 80)


if __name__ == "__main__":
    entrenar_y_comparar()
