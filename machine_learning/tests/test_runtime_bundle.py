"""Contrato del paquete ML congelado; datos sintéticos, sin métricas clínicas."""
import hashlib
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pytest

ROOT = Path(os.environ['ML_ROOT'])
MODELS = ROOT / 'models/c1_fase10_final'


@pytest.fixture(scope='module')
def model():
    return joblib.load(MODELS / 'modelo_diagnostico_c1.pkl')


@pytest.fixture(scope='module')
def raw(model):
    vectorizer = joblib.load(MODELS / 'vectorizador_c1.pkl')
    return model.predict_proba(vectorizer.transform(['demora cinco segundos en arrancar en frío']))[0]


def test_c1_has_61_unique_labels(model):
    assert len(model.classes_) == len(set(model.classes_)) == 61


def test_raw_probabilities_are_normalized(raw):
    assert np.all((raw >= 0) & (raw <= 1))
    assert np.isclose(raw.sum(), 1)


def test_raw_top3_preserves_model_probabilities(model, raw):
    indices = raw.argsort()[::-1][:3]
    top3 = [(str(model.classes_[i]), float(raw[i])) for i in indices]
    assert len(top3) == 3 and len({label for label, _ in top3}) == 3
    assert top3[0][1] >= top3[1][1] >= top3[2][1]


def test_frozen_model_hashes():
    manifest = json.loads((MODELS / 'C1_FINAL_HASH_MANIFEST.json').read_text(encoding='utf-8'))
    for entry in manifest['archivos']:
        if entry['archivo'].endswith('.pkl'):
            assert hashlib.sha256((MODELS / Path(entry['archivo']).name).read_bytes()).hexdigest() == entry['sha256']


def test_rag_loads_original_vectors_and_current_documents():
    from src.infrastructure.motor_rag import MotorRAG
    rag = MotorRAG(manual_path=str(ROOT / 'manuals'), rag_version='candidate_v1')
    assert rag.faiss_index is not None
    assert (rag.faiss_index.d, rag.faiss_index.ntotal) == (32708, 239)
    assert len(rag.documentos) == 239
    assert not rag.corpus_validado  # No convertir corpus referencial en validación OEM.
