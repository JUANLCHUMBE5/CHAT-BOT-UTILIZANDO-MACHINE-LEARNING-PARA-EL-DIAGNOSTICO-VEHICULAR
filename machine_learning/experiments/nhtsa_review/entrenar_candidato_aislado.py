"""Entrena y evalúa un candidato NHTSA sin modificar artefactos oficiales.

El candidato conserva Linear SVM + TF-IDF calibrado. Los casos NHTSA revisados
se separan por vehículo antes de entrar al entrenamiento para impedir fuga entre
entrenamiento y evaluación. Este script nunca escribe en machine_learning/models.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = Path(__file__).resolve().parent
REVIEWED = EXPERIMENT / "output" / "dataset_nhtsa_revisado.csv"
BASE = ROOT / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"
OFFICIAL_DIR = ROOT / "machine_learning" / "models"
OUTPUT = EXPERIMENT / "candidate_artifacts"
FROZEN = [
    OFFICIAL_DIR / "modelo_diagnostico.pkl",
    OFFICIAL_DIR / "modelo_sistema.pkl",
    OFFICIAL_DIR / "vectorizador_tfidf.pkl",
]
MINIMUM_REVIEWED = 30


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def group_split(record: dict[str, str]) -> str:
    group = "|".join(record.get(key, "").strip().casefold() for key in ("make", "model", "model_year"))
    value = int(hashlib.sha256(group.encode("utf-8")).hexdigest()[:8], 16) % 100
    return "train" if value < 70 else "validation" if value < 85 else "test"


def top3_accuracy(model: CalibratedClassifierCV, features, labels: list[str]) -> float:
    probabilities = model.predict_proba(features)
    classes = list(model.classes_)
    hits = 0
    for row, label in zip(probabilities, labels):
        top = np.argsort(row)[::-1][:3]
        hits += label in {classes[index] for index in top}
    return hits / len(labels) if labels else 0.0


def per_class_precision(model: CalibratedClassifierCV, features, labels: list[str]) -> dict[str, dict[str, float]]:
    predicted = model.predict(features)
    classes = sorted(set(labels) | set(predicted))
    precision, recall, f1, support = precision_recall_fscore_support(
        labels, predicted, labels=classes, zero_division=0
    )
    return {
        label: {
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "f1": round(float(score), 4),
            "support": int(count),
        }
        for label, p, r, score, count in zip(classes, precision, recall, f1, support)
    }


def evaluate(model: CalibratedClassifierCV, vectorizer: TfidfVectorizer, records: list[dict[str, str]]) -> dict[str, object]:
    texts = [row["sintoma"] for row in records]
    labels = [row["falla"] for row in records]
    started = time.perf_counter()
    features = vectorizer.transform(texts)
    predicted = model.predict(features)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        "samples": len(records),
        "accuracy": round(float(accuracy_score(labels, predicted)), 4),
        "f1_macro": round(float(f1_score(labels, predicted, average="macro", zero_division=0)), 4),
        "f1_weighted": round(float(f1_score(labels, predicted, average="weighted", zero_division=0)), 4),
        "top3_accuracy": round(float(top3_accuracy(model, features, labels)), 4),
        "mean_ml_latency_ms": round(elapsed_ms / len(records), 3),
        "per_class": per_class_precision(model, features, labels),
        "confusion_matrix": {
            "labels": sorted(set(labels) | set(predicted)),
            "values": confusion_matrix(labels, predicted, labels=sorted(set(labels) | set(predicted))).tolist(),
        },
    }


def check_ready() -> dict[str, object]:
    if not REVIEWED.exists():
        return {"state": "blocked", "reason": "dataset_nhtsa_revisado.csv no existe; falta revisión mecánica."}
    reviewed = read_csv(REVIEWED)
    splits = Counter(group_split(row) for row in reviewed)
    return {
        "state": "ready" if len(reviewed) >= MINIMUM_REVIEWED and splits["test"] else "blocked",
        "reviewed_cases": len(reviewed),
        "split_counts": dict(splits),
        "minimum_reviewed_cases": MINIMUM_REVIEWED,
        "reason": "" if len(reviewed) >= MINIMUM_REVIEWED and splits["test"] else "Faltan casos revisados o casos de prueba por vehículo.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Solo informa si el experimento puede ejecutarse.")
    args = parser.parse_args()
    readiness = check_ready()
    if args.check:
        print(json.dumps(readiness, ensure_ascii=False, indent=2))
        return
    if readiness["state"] != "ready":
        raise RuntimeError(json.dumps(readiness, ensure_ascii=False))

    reviewed = read_csv(REVIEWED)
    split_rows = {name: [row for row in reviewed if group_split(row) == name] for name in ("train", "validation", "test")}
    if not split_rows["test"] or not split_rows["validation"]:
        raise RuntimeError("La división por vehículo no produjo validación y prueba independientes.")

    frozen_before = {str(path): sha256(path) for path in FROZEN if path.exists()}
    base = read_csv(BASE)
    train_rows = base + split_rows["train"]
    texts = [row["sintoma"].strip() for row in train_rows]
    labels = [row["falla"].strip() for row in train_rows]
    counts = Counter(labels)
    insufficient = sorted(label for label, count in counts.items() if count < 3)
    if insufficient:
        raise RuntimeError(f"Clases con menos de tres muestras para calibración: {insufficient}")

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode", min_df=1, max_features=25000)
    train_features = vectorizer.fit_transform(texts)
    estimator = CalibratedClassifierCV(LinearSVC(C=1.2, random_state=42, max_iter=3000), method="sigmoid", cv=3)
    estimator.fit(train_features, labels)

    validation = evaluate(estimator, vectorizer, split_rows["validation"])
    test = evaluate(estimator, vectorizer, split_rows["test"])
    OUTPUT.mkdir(parents=True, exist_ok=True)
    model_path = OUTPUT / "modelo_diagnostico_candidato.pkl"
    vectorizer_path = OUTPUT / "vectorizador_tfidf_candidato.pkl"
    joblib.dump(estimator, model_path)
    joblib.dump(vectorizer, vectorizer_path)
    frozen_after = {str(path): sha256(path) for path in FROZEN if path.exists()}
    report = {
        "experiment": "NHTSA_REVIEWED_LINEAR_SVM_TFIDF",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "architecture": "TF-IDF + Linear SVM calibrado",
        "reviewed_split_by_vehicle": {key: len(value) for key, value in split_rows.items()},
        "base_training_records": len(base),
        "candidate_training_records": len(train_rows),
        "validation": validation,
        "blind_test": test,
        "frozen_hashes_before": frozen_before,
        "frozen_hashes_after": frozen_after,
        "official_artifacts_unchanged": frozen_before == frozen_after,
        "promotion": "PENDIENTE: comparar con modelo actual y revisar métricas por sistemas críticos.",
    }
    report_path = OUTPUT / "reporte_candidato.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
