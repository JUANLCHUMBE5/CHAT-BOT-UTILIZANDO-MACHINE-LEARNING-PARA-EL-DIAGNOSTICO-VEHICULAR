"""
Script de Congelamiento Oficial de Modelos para Iteración 8.3 de CarBot.
Entrena y serializa:
1. Clasificador Jerárquico Nivel 1 (Macro-Sistemas) con Isotonic cv=5 (LinearSVC C=1.0)
2. Clasificador Jerárquico Nivel 2 (Fallas - 61 clases) con Isotonic cv=5 (LinearSVC C=1.2)
3. Vectorizador TF-IDF canónico (ngram_range=(1,2), sublinear_tf=True, 25000 feats)
Guarda artefactos en:
- machine_learning/models/fase8_candidata/
- machine_learning/models/
"""

import sys
from pathlib import Path
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
import joblib

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema

DATA_TRAIN = BASE_DIR / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"
DIR_CANDIDATA = BASE_DIR / "machine_learning" / "models" / "fase8_candidata"
DIR_PROD = BASE_DIR / "machine_learning" / "models"

def main():
    print("Cargando dataset TRAIN 8.1...")
    df = pd.read_csv(DATA_TRAIN)
    X = df["sintoma"].values
    y_f = df["falla"].values
    y_s = [obtener_macro_sistema(f) for f in y_f]

    print(f"Total instancias: {len(X)} | Clases de falla: {len(set(y_f))} | Macro-Sistemas: {len(set(y_s))}")

    print("Ajustando vectorizador TF-IDF canónico...")
    vec = TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        strip_accents="unicode",
        min_df=1,
        max_features=25000,
    )
    X_vec = vec.fit_transform(X)

    print("Entrenando Nivel 1 (Macro-Sistemas) con Isotonic cv=5...")
    svc_s = LinearSVC(C=1.0, class_weight="balanced", random_state=42, max_iter=3000)
    cal_s = CalibratedClassifierCV(estimator=svc_s, method="isotonic", cv=5)
    cal_s.fit(X_vec, y_s)

    print("Entrenando Nivel 2 (Fallas - 61 clases) con Isotonic cv=5...")
    svc_f = LinearSVC(C=1.2, class_weight="balanced", random_state=42, max_iter=3500)
    cal_f = CalibratedClassifierCV(estimator=svc_f, method="isotonic", cv=5)
    cal_f.fit(X_vec, y_f)

    # Serializar en ambos directorios
    for destino in [DIR_CANDIDATA, DIR_PROD]:
        destino.mkdir(parents=True, exist_ok=True)
        joblib.dump(cal_f, destino / "modelo_diagnostico.pkl", compress=3)
        joblib.dump(cal_s, destino / "modelo_sistema.pkl", compress=3)
        joblib.dump(vec, destino / "vectorizador_tfidf.pkl", compress=3)
        print(f"Artefactos guardados con éxito en: {destino}")

    print("Congelamiento de modelos ML 8.3 completado exitosamente.")

if __name__ == "__main__":
    main()
