"""
12_entrenar_svm_v2.py
FASE EXPERIMENTAL — CARBOT ML + RAG V2
Reentrenamiento controlado y reproducible del clasificador Linear SVM V2 + TF-IDF V2
utilizando la arquitectura exacta de referencia (CalibratedClassifierCV + LinearSVC).

Entrada:
- machine_learning/experimentos/carbot_v2/data/dataset_c1_v2_experimental.csv

Salidas:
- machine_learning/experimentos/carbot_v2/models/tfidf_diagnostico_v2_experimental.joblib
- machine_learning/experimentos/carbot_v2/models/linear_svm_diagnostico_v2_experimental.joblib
- machine_learning/experimentos/carbot_v2/models/model_manifest_v2_experimental.json
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
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
BASE_V2 = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2"
DATA_V2 = BASE_V2 / "data"
MODELS_V2 = BASE_V2 / "models"
MODELS_V2.mkdir(parents=True, exist_ok=True)

DATASET_V2_CSV = DATA_V2 / "dataset_c1_v2_experimental.csv"
TEST_BLIND_CSV = PROJECT_ROOT / "machine_learning" / "data" / "fase10" / "test10_fase10_blind_v1.csv"


def calcular_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def entrenar():
    t0 = time.time()
    print("Iniciando Entrenamiento Experimental de Linear SVM V2 + TF-IDF V2...")

    if not DATASET_V2_CSV.exists():
        raise FileNotFoundError(f"No se encontro {DATASET_V2_CSV}. Ejecute 11_ensamblar_dataset_v2.py primero.")

    df_train = pd.read_csv(DATASET_V2_CSV)
    print(f"Cargados {len(df_train):,} registros para entrenamiento C1-V2.")
    print(f"Clases unicas en entrenamiento: {df_train['clase_objetivo'].nunique()}")

    X_train = df_train["texto_usuario"].astype(str).tolist()
    y_train = df_train["clase_objetivo"].astype(str).tolist()

    # 1. Configurar TF-IDF V2 identico a produccion
    print("\n1. Ajustando vectorizador TF-IDF V2...")
    t_tfidf_start = time.time()
    vectorizador_v2 = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=25000,
        sublinear_tf=True,
        strip_accents="unicode",
        lowercase=True
    )
    X_train_vec = vectorizador_v2.fit_transform(X_train)
    t_tfidf = time.time() - t_tfidf_start
    print(f"TF-IDF V2 ajustado en {t_tfidf:.2f} s. Dimension matriz: {X_train_vec.shape}")

    # 2. Configurar LinearSVC base + CalibratedClassifierCV
    print("\n2. Entrenando CalibratedClassifierCV con LinearSVC(C=1.2, class_weight='balanced')...")
    t_svm_start = time.time()
    base_svc = LinearSVC(
        C=1.2,
        class_weight="balanced",
        max_iter=3500,
        random_state=42
    )
    calibrated_svm_v2 = CalibratedClassifierCV(
        estimator=base_svc,
        method="isotonic",
        cv=5
    )
    calibrated_svm_v2.fit(X_train_vec, y_train)
    t_svm = time.time() - t_svm_start
    print(f"Linear SVM V2 entrenado y calibrado en {t_svm:.2f} s.")

    # 3. Guardar artefactos en machine_learning/experimentos/carbot_v2/models/
    out_tfidf_path = MODELS_V2 / "tfidf_diagnostico_v2_experimental.joblib"
    out_svm_path = MODELS_V2 / "linear_svm_diagnostico_v2_experimental.joblib"

    print("\n3. Guardando artefactos experimentales...")
    joblib.dump(vectorizador_v2, out_tfidf_path, compress=3)
    joblib.dump(calibrated_svm_v2, out_svm_path, compress=3)

    hash_tfidf = calcular_sha256(out_tfidf_path)
    hash_svm = calcular_sha256(out_svm_path)
    hash_dataset = calcular_sha256(DATASET_V2_CSV)

    # 4. Generar manifiesto experimental
    manifest_data = {
        "nombre_modelo": "Linear SVM V2 Experimental",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "estado": "EXPERIMENTAL_NO_PRODUCTIVO",
        "arquitectura": "LinearSVC(C=1.2, class_weight='balanced') + CalibratedClassifierCV(method='isotonic', cv=5)",
        "vectorizador": {
            "archivo": out_tfidf_path.name,
            "sha256": hash_tfidf,
            "tamano_bytes": out_tfidf_path.stat().st_size,
            "ngram_range": [1, 2],
            "max_features": 25000,
            "sublinear_tf": True
        },
        "clasificador": {
            "archivo": out_svm_path.name,
            "sha256": hash_svm,
            "tamano_bytes": out_svm_path.stat().st_size,
            "n_classes": len(calibrated_svm_v2.classes_),
            "classes": list(calibrated_svm_v2.classes_)
        },
        "dataset_entrenamiento": {
            "archivo": DATASET_V2_CSV.name,
            "sha256": hash_dataset,
            "total_muestras": len(df_train),
            "original_c1": int((df_train["data_origin"] == "ORIGINAL").sum()),
            "external_verified": int((df_train["data_origin"] == "EXTERNAL_VERIFIED").sum())
        },
        "tiempos_entrenamiento_segundos": {
            "tfidf": round(t_tfidf, 2),
            "svm_calibracion": round(t_svm, 2),
            "total": round(time.time() - t0, 2)
        }
    }

    manifest_path = MODELS_V2 / "model_manifest_v2_experimental.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    print(f"Artefactos guardados exitosamente:")
    print(f"  - TF-IDF: {out_tfidf_path} (SHA-256: {hash_tfidf[:16]}...)")
    print(f"  - SVM V2: {out_svm_path} (SHA-256: {hash_svm[:16]}...)")
    print(f"  - Manifiesto: {manifest_path}")
    print(f"Tiempo total: {time.time() - t0:.2f} s")


if __name__ == "__main__":
    entrenar()
