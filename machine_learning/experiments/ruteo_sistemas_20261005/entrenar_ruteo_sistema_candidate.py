"""Entrena y evalúa un candidato aislado de frase -> sistema CarBot.

No reemplaza el clasificador principal de fallas. Lee solo filas tipo sintoma
de los CSV de desarrollo y guarda el artefacto bajo machine_learning/experiments.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC


ROOT = Path(__file__).resolve().parents[3]
DOWNLOADS = Path.home() / "Downloads"
BIG_CSV = DOWNLOADS / "CarBot_clasificacion_3000.csv"
FOCUS_CSV = DOWNLOADS / "CarBot_train_ruteo_focus.csv"
OUT = ROOT / "machine_learning" / "experiments" / "ruteo_sistemas_20261005"
sys.path.insert(0, str(ROOT / "backend"))
from src.core.diagnostico.enrutador_sistema import detectar_sistema_ruteo  # noqa: E402
LABELS = {
    "refrigeracion", "combustible_admision", "encendido", "frenos",
    "transmision", "suspension_direccion", "electrico_ecu",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with path.open(encoding=encoding, newline="") as source:
                return list(csv.DictReader(source))
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"No se pudo decodificar {path.name}")


def normalize(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.casefold())
    return " ".join("".join(c for c in folded if not unicodedata.combining(c)).split())


def source_rows(path: Path, phrase_keys: tuple[str, ...]) -> list[dict[str, str]]:
    selected = []
    for row in read_csv(path):
        if row.get("tipo", "").strip().lower() != "sintoma":
            continue
        phrase = next((row.get(key, "").strip() for key in phrase_keys if row.get(key, "").strip()), "")
        label = normalize(row.get("sistema_id", "")).replace(" ", "_")
        if phrase and label in LABELS:
            selected.append({"text": phrase, "label": label, "source": path.name})
    return selected


def make_pipeline() -> Pipeline:
    features = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode")),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
    ])
    return Pipeline([
        ("features", features),
        ("classifier", LinearSVC(C=1.0, class_weight="balanced", random_state=42)),
    ])


def stable_group(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


def main() -> None:
    rows = source_rows(BIG_CSV, ("frase", "frase_sintoma"))
    rows.extend(source_rows(FOCUS_CSV, ("frase", "frase_sintoma")))
    raw_selected_counts = dict(Counter(row["source"] for row in rows))
    by_phrase: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        by_phrase[normalize(row["text"])].add(row["label"])
    conflicts = {phrase: sorted(labels) for phrase, labels in by_phrase.items() if len(labels) > 1}
    unique = {}
    for row in rows:
        key = normalize(row["text"])
        if key not in conflicts:
            unique.setdefault(key, row)
    rows = list(unique.values())
    texts = [row["text"] for row in rows]
    labels = [row["label"] for row in rows]
    groups = [stable_group(text) for text in texts]

    splitter = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=42)
    train_idx, test_idx = next(splitter.split(texts, labels, groups))
    evaluator = make_pipeline()
    evaluator.fit([texts[i] for i in train_idx], [labels[i] for i in train_idx])
    predicted = evaluator.predict([texts[i] for i in test_idx])
    decision_values = evaluator.decision_function([texts[i] for i in test_idx])
    sorted_scores = __import__("numpy").sort(decision_values, axis=1)
    margins = sorted_scores[:, -1] - sorted_scores[:, -2]
    overlap = set(groups[i] for i in train_idx) & set(groups[i] for i in test_idx)

    model = make_pipeline()
    model.fit(texts, labels)
    OUT.mkdir(parents=True, exist_ok=True)
    model_path = OUT / "modelo_ruteo_candidato.joblib"
    joblib.dump(model, model_path)

    fixtures = {
        "está recalentando": "refrigeracion",
        "es refrigeración no de mezcla": "refrigeracion",
        "tiembla y 500 rpm": "encendido",
        "500 rpm": "ambiguo",
        "patina embrague": "transmision",
        "ruido al frenar": "frenos",
    }
    fixture_results = []
    for phrase, expected in fixtures.items():
        svm_label = str(model.predict([phrase])[0])
        runtime_label = detectar_sistema_ruteo(phrase) or svm_label
        fixture_results.append({
            "frase": phrase,
            "esperado": expected,
            "modelo_svm": svm_label,
            "ruta_runtime": runtime_label,
            "pass": runtime_label == expected,
        })
    report = {
        "candidate_only": True,
        "main_fault_classifier_modified": False,
        "source_files": [str(BIG_CSV), str(FOCUS_CSV)],
        "symptom_rows_selected_before_deduplication": raw_selected_counts,
        "source_rows_used": dict(Counter(row["source"] for row in rows)),
        "unique_symptoms": len(rows),
        "conflicting_phrase_groups_excluded": len(conflicts),
        "labels": dict(Counter(labels)),
        "group_holdout_train": len(train_idx),
        "group_holdout_test": len(test_idx),
        "group_overlap": len(overlap),
        "holdout_accuracy": accuracy_score([labels[i] for i in test_idx], predicted),
        "holdout_margin_p10": float(__import__("numpy").percentile(margins, 10)),
        "holdout_margin_median": float(__import__("numpy").median(margins)),
        "holdout_report": classification_report(
            [labels[i] for i in test_idx], predicted, output_dict=True, zero_division=0
        ),
        "holdout_confusion_matrix": confusion_matrix(
            [labels[i] for i in test_idx], predicted, labels=sorted(set(labels))
        ).tolist(),
        "label_order": sorted(set(labels)),
        "six_fixture_svm_only": fixture_results,
        "six_fixture_runtime_pass_count": sum(result["pass"] for result in fixture_results),
        "model_path": str(model_path),
    }
    (OUT / "evaluacion.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "candidate_path": str(model_path),
        "unique_symptoms": len(rows),
        "holdout_train": len(train_idx),
        "holdout_test": len(test_idx),
        "group_overlap": len(overlap),
        "holdout_accuracy": report["holdout_accuracy"],
        "fixtures": fixture_results,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
