"""Contrato del paquete ML congelado; datos sintéticos, sin métricas clínicas."""
import hashlib
import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pytest

ROOT = Path(os.environ.get("ML_ROOT", str(Path(__file__).resolve().parents[1])))
MODELS = ROOT / "models/c1_fase10_final"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.taxonomia_sistemas import (
    CLASES_ENTRENADAS_61,
    CLASS_ID_POR_FALLA,
    FALLA_A_SISTEMA,
    MODEL_VERSION,
    SUBAREAS_POR_CLASE,
    TAXONOMY_VERSION,
    construir_contrato_prediccion,
    es_clase_entrenada_svm,
)


@pytest.fixture(scope="module")
def model():
    return joblib.load(MODELS / "modelo_diagnostico_c1.pkl")


@pytest.fixture(scope="module")
def raw(model):
    vectorizer = joblib.load(MODELS / "vectorizador_c1.pkl")
    return model.predict_proba(vectorizer.transform(["demora cinco segundos en arrancar en frío"]))[0]


def test_c1_has_61_unique_labels(model):
    assert len(model.classes_) == len(set(model.classes_)) == 61


def test_taxonomy_matches_exact_61_trained_classes(model):
    trained_set = {str(c) for c in model.classes_}
    taxonomy_set = set(CLASES_ENTRENADAS_61)
    assert trained_set == taxonomy_set
    assert len(CLASS_ID_POR_FALLA) == 61
    assert set(SUBAREAS_POR_CLASE.keys()) == taxonomy_set
    for clase, subareas in SUBAREAS_POR_CLASE.items():
        assert len(subareas) >= 1, f"Clase sin subárea asignada: {clase}"
        assert es_clase_entrenada_svm(clase)


def test_inference_contract_distinguishes_svm_from_rule():
    contrato_svm = construir_contrato_prediccion(
        class_label="Bomba de gasolina quemada o con baja presion",
        raw_svm_score=0.6123,
        calibrated_probability=0.7345,
        prediction_source="SVM",
        top_k=[{"falla": "Bomba de gasolina quemada o con baja presion", "probabilidad": 0.7345}],
    )
    assert contrato_svm.model_version == MODEL_VERSION
    assert contrato_svm.taxonomy_version == TAXONOMY_VERSION
    assert contrato_svm.class_id == "C02"
    assert contrato_svm.subsystem == "MOTOR"
    assert contrato_svm.raw_svm_score == 0.6123
    assert contrato_svm.calibrated_probability == 0.7345
    assert contrato_svm.prediction_source == "SVM"

    contrato_regla = construir_contrato_prediccion(
        class_label="Falla en conector, alimentacion o red CAN de comunicacion con ECU",
        raw_svm_score=0.18,
        calibrated_probability=0.85,
        prediction_source="REGLA",
        top_k=[],
    )
    assert contrato_regla.class_id == "HIPOTESIS_REGLA"
    assert contrato_regla.calibrated_probability is None
    assert contrato_regla.prediction_source == "REGLA"


def test_raw_probabilities_are_normalized(raw):
    assert np.all((raw >= 0) & (raw <= 1))
    assert np.isclose(raw.sum(), 1)


def test_raw_top3_preserves_model_probabilities(model, raw):
    indices = raw.argsort()[::-1][:3]
    top3 = [(str(model.classes_[i]), float(raw[i])) for i in indices]
    assert len(top3) == 3 and len({label for label, _ in top3}) == 3
    assert top3[0][1] >= top3[1][1] >= top3[2][1]


def test_frozen_model_hashes():
    manifest = json.loads((MODELS / "C1_FINAL_HASH_MANIFEST.json").read_text(encoding="utf-8"))
    for entry in manifest["archivos"]:
        if entry["archivo"].endswith(".pkl"):
            assert hashlib.sha256((MODELS / Path(entry["archivo"]).name).read_bytes()).hexdigest() == entry["sha256"]


def test_rag_loads_original_vectors_and_current_documents():
    from src.infrastructure.motor_rag import MotorRAG
    rag = MotorRAG(manual_path=str(ROOT / "manuals"), rag_version="candidate_v1")
    assert rag.faiss_index is not None
    assert (rag.faiss_index.d, rag.faiss_index.ntotal) == (32708, 239)
    assert len(rag.documentos) == 239
    assert not rag.corpus_validado  # No convertir corpus referencial en validación OEM.
