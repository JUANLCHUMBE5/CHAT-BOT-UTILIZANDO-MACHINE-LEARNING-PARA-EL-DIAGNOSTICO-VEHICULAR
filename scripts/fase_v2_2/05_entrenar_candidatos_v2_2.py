"""
05_entrenar_candidatos_v2_2.py
FASE EXPERIMENTAL CARBOT V2.2 — FASES 8 Y 15
Entrenamiento controlado en sandbox de:
- SVM_V2_2_A (dataset_v2_2_a.csv, 7,119 filas)
- SVM_V2_2_B (dataset_v2_2_b.csv, 7,189 filas)
- SVM_V2_2_C (dataset_v2_2_c.csv, 7,259 filas)

Aplica la arquitectura de features ganadora en la Fase 9:
FeatureUnion(Word n-grams 1-2 [22,000] + Char_wb 3-5 [8,000])
+ LinearSVC(C=1.2, class_weight='balanced') calibrado con Sigmoid cv=3.
Guarda modelos, vectorizadores y manifiestos con SHA-256 en models/.
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
from sklearn.pipeline import FeatureUnion
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
V2_2_DIR = PROJECT_ROOT / "machine_learning" / "experimentos" / "carbot_v2_2"
DATA_DIR = V2_2_DIR / "data"
MODELS_DIR = V2_2_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def calcular_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def entrenar_candidato(nombre: str, dataset_csv: Path):
    print(f"\n{'='*70}")
    print(f"ENTRENANDO CANDIDATO {nombre} ({dataset_csv.name})")
    print(f"{'='*70}")

    t0 = time.time()
    df = pd.read_csv(dataset_csv)
    X = df["texto_usuario"].astype(str).tolist()
    y = df["clase_objetivo"].astype(str).tolist()
    n_clases = df["clase_objetivo"].nunique()
    print(f"Muestras de entrenamiento: {len(df):,} | Clases: {n_clases}")
    assert n_clases == 61, f"Error: Se esperaban 61 clases, se encontraron {n_clases}"

    # 1. Feature Union Tfidf (Ganador Fase 9)
    print("Ajustando FeatureUnion (Word 1-2 + Char_wb 3-5)...")
    t_vec_0 = time.time()
    vectorizer = FeatureUnion([
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

    X_vec = vectorizer.fit_transform(X)
    t_vec = time.time() - t_vec_0
    print(f"TF-IDF ajustado en {t_vec:.2f} s. Matriz de características: {X_vec.shape}")

    # 2. Linear SVM con Calibración Sigmoide
    print("Entrenando LinearSVC Calibrado (C=1.2, balanced, 3-fold CV)...")
    t_svm_0 = time.time()
    base_svc = LinearSVC(
        C=1.2,
        class_weight="balanced",
        max_iter=3500,
        random_state=42
    )
    model = CalibratedClassifierCV(estimator=base_svc, method="sigmoid", cv=3)
    model.fit(X_vec, y)
    t_svm = time.time() - t_svm_0
    print(f"Modelo ajustado y calibrado en {t_svm:.2f} s.")

    # 3. Guardar artefactos
    tfidf_file = MODELS_DIR / f"tfidf_{nombre.lower()}.joblib"
    svm_file = MODELS_DIR / f"linear_svm_{nombre.lower()}.joblib"
    manifest_file = MODELS_DIR / f"manifest_{nombre.lower()}.json"

    joblib.dump(vectorizer, tfidf_file, compress=3)
    joblib.dump(model, svm_file, compress=3)

    hash_tfidf = calcular_sha256(tfidf_file)
    hash_svm = calcular_sha256(svm_file)

    manifest = {
        "candidate_name": nombre,
        "date_trained": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_used": dataset_csv.name,
        "total_samples": len(df),
        "total_classes": n_clases,
        "feature_dimensions": X_vec.shape[1],
        "training_time_seconds": round(time.time() - t0, 2),
        "vectorizer_file": tfidf_file.name,
        "vectorizer_sha256": hash_tfidf,
        "model_file": svm_file.name,
        "model_sha256": hash_svm,
        "classes_list": list(model.classes_)
    }

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Artefactos guardados exitosamente:")
    print(f"  - TF-IDF : {tfidf_file.name} (SHA-256: {hash_tfidf[:16]}...)")
    print(f"  - SVM    : {svm_file.name} (SHA-256: {hash_svm[:16]}...)")
    print(f"  - Manifest: {manifest_file.name}")


def main():
    print("INICIANDO ENTRENAMIENTO DE LOS 3 CANDIDATOS V2.2...")
    entrenar_candidato("V2_2_A", DATA_DIR / "dataset_v2_2_a.csv")
    entrenar_candidato("V2_2_B", DATA_DIR / "dataset_v2_2_b.csv")
    entrenar_candidato("V2_2_C", DATA_DIR / "dataset_v2_2_c.csv")
    print("\nEntrenamiento de todos los candidatos V2.2 finalizado.")


if __name__ == "__main__":
    main()
