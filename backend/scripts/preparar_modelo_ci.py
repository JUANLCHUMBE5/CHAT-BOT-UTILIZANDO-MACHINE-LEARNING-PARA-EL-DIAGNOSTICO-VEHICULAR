"""Genera artefactos ML ligeros para la suite de CI.

No reemplaza los modelos C1 congelados de producción. Entrena un clasificador
Linear SVM + TF-IDF reproducible a partir del dataset versionado para que las
pruebas de código puedan ejecutarse en GitHub sin subir binarios `.pkl`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema

DATASET_PATH = PROJECT_ROOT / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"
OUTPUT_DIR = BACKEND_DIR / ".ci_ml_artifacts"


def cargar_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATASET_PATH, encoding="utf-8")
    df = df.dropna(subset=["sintoma", "falla"]).copy()
    df["sintoma"] = df["sintoma"].astype(str).str.strip()
    df["falla"] = df["falla"].astype(str).str.strip()
    df = df[df["sintoma"] != ""]
    df = df[df["falla"] != ""]
    df = df.drop_duplicates(subset=["sintoma", "falla"])
    df["macro_sistema"] = df["falla"].apply(obtener_macro_sistema)
    return df


def entrenar() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = cargar_dataset()

    vectorizador = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        strip_accents="unicode",
        min_df=1,
        max_features=25_000,
    )
    x_vec = vectorizador.fit_transform(df["sintoma"].tolist())

    falla_base = LinearSVC(C=1.2, random_state=42, max_iter=3000)
    modelo_falla = CalibratedClassifierCV(estimator=falla_base, method="sigmoid", cv=3)
    modelo_falla.fit(x_vec, df["falla"].tolist())

    sistema_base = LinearSVC(C=1.0, random_state=42, max_iter=2500)
    modelo_sistema = CalibratedClassifierCV(estimator=sistema_base, method="sigmoid", cv=3)
    modelo_sistema.fit(x_vec, df["macro_sistema"].tolist())

    joblib.dump(modelo_falla, OUTPUT_DIR / "modelo_diagnostico.pkl", compress=3)
    joblib.dump(modelo_sistema, OUTPUT_DIR / "modelo_sistema.pkl", compress=3)
    joblib.dump(vectorizador, OUTPUT_DIR / "vectorizador_tfidf.pkl", compress=3)
    print(f"Artefactos ML de CI generados en {OUTPUT_DIR}")


if __name__ == "__main__":
    entrenar()
