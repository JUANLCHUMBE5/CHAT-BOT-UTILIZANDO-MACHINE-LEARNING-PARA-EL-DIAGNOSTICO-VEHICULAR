"""
05_entrenar_candidatos_v2_1.py
FASE EXPERIMENTAL CARBOT V2.1 — FASE 8
Entrena de forma controlada y reproducible los 3 modelos candidatos:
- SVM_V2_1_A (Dataset V2.1-A)
- SVM_V2_1_B (Dataset V2.1-B)
- SVM_V2_1_C (Dataset V2.1-C)

Arquitectura estandarizada idéntica al baseline:
- TfidfVectorizer(ngram_range=(1, 2), max_features=25000, sublinear_tf=True, strip_accents='unicode', lowercase=True)
- LinearSVC(C=1.2, class_weight='balanced', max_iter=3500, random_state=42)
- CalibratedClassifierCV(method='isotonic', cv=5)
"""
import sys
import os
import json
import time
import hashlib
from pathlib import Path
import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
V2_1_DIR = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2_1"
DATA_DIR = V2_1_DIR / "data"
MODELS_DIR = V2_1_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def calcular_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def entrenar_candidato(nombre_candidato: str, dataset_path: Path):
    t0 = time.time()
    print(f"\n--- Entrenando Candidato {nombre_candidato} ({dataset_path.name}) ---")
    df = pd.read_csv(dataset_path)
    X = df["texto_usuario"].astype(str).tolist()
    y = df["clase_objetivo"].astype(str).tolist()
    n_clases = df["clase_objetivo"].nunique()
    print(f"Muestras: {len(df):,} | Clases: {n_clases}")

    # 1. TF-IDF
    t_tf_0 = time.time()
    vec = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=25000,
        sublinear_tf=True,
        strip_accents="unicode",
        lowercase=True
    )
    X_vec = vec.fit_transform(X)
    t_tfidf = time.time() - t_tf_0
    print(f"TF-IDF ajustado en {t_tfidf:.2f} s. Dimension: {X_vec.shape}")

    # 2. Linear SVM Calibrado
    t_svm_0 = time.time()
    base_svc = LinearSVC(
        C=1.2,
        class_weight="balanced",
        max_iter=3500,
        random_state=42
    )
    calibrated = CalibratedClassifierCV(
        estimator=base_svc,
        method="isotonic",
        cv=5
    )
    calibrated.fit(X_vec, y)
    t_svm = time.time() - t_svm_0
    print(f"Linear SVM calibrado en {t_svm:.2f} s.")

    # 3. Guardar artefactos
    prefix = nombre_candidato.lower()
    tfidf_file = MODELS_DIR / f"tfidf_{prefix}.joblib"
    svm_file = MODELS_DIR / f"linear_svm_{prefix}.joblib"
    manifest_file = MODELS_DIR / f"manifest_{prefix}.json"

    joblib.dump(vec, tfidf_file, compress=3)
    joblib.dump(calibrated, svm_file, compress=3)

    hash_tf = calcular_sha256(tfidf_file)
    hash_svm = calcular_sha256(svm_file)
    hash_data = calcular_sha256(dataset_path)

    manifest = {
        "candidato": nombre_candidato,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset": {
            "archivo": dataset_path.name,
            "sha256": hash_data,
            "total_registros": len(df),
            "originales_c1": int((df["data_origin"] == "ORIGINAL").sum()),
            "externos": int((df["data_origin"] != "ORIGINAL").sum())
        },
        "vectorizador": {
            "archivo": tfidf_file.name,
            "sha256": hash_tf,
            "tamano_bytes": tfidf_file.stat().st_size
        },
        "clasificador": {
            "archivo": svm_file.name,
            "sha256": hash_svm,
            "tamano_bytes": svm_file.stat().st_size,
            "n_classes": len(calibrated.classes_),
            "classes": list(calibrated.classes_)
        },
        "tiempos_segundos": {
            "tfidf": round(t_tfidf, 2),
            "svm_calibracion": round(t_svm, 2),
            "total": round(time.time() - t0, 2)
        }
    }

    with open(manifest_file, "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2, ensure_ascii=False)

    print(f"Artefactos guardados:")
    print(f"  - TF-IDF: {tfidf_file.name} (SHA-256: {hash_tf[:16]}...)")
    print(f"  - SVM:    {svm_file.name} (SHA-256: {hash_svm[:16]}...)")
    print(f"  - Manifest: {manifest_file.name}")


def main():
    t_global = time.time()
    print("Iniciando Fase 8: Entrenamiento de Candidatos V2.1-A, V2.1-B, V2.1-C...")

    candidatos = [
        ("V2_1_A", DATA_DIR / "dataset_v2_1_a.csv"),
        ("V2_1_B", DATA_DIR / "dataset_v2_1_b.csv"),
        ("V2_1_C", DATA_DIR / "dataset_v2_1_c.csv")
    ]

    for nombre, ruta in candidatos:
        entrenar_candidato(nombre, ruta)

    print(f"\nEntrenamiento de los 3 candidatos completado en {time.time() - t_global:.2f} s.")


if __name__ == "__main__":
    main()
