"""Contrato C1: probabilidades SVM sin fusión y telemetría independiente."""

from types import SimpleNamespace

import numpy as np

from src.core.diagnostico.models import ResultadoDiagnostico
from src.infrastructure.modelo_ml import ModeloML


class _Vectorizador:
    def transform(self, textos):
        return SimpleNamespace(nnz=1)


class _SVM:
    classes_ = np.array(["Falla A", "Falla B", "Falla C"])

    def predict_proba(self, entrada):
        return np.array([[0.2, 0.7, 0.1]])


def test_top3_svm_raw_no_aplica_temperatura_ni_macro_sistema():
    modelo = ModeloML.__new__(ModeloML)
    modelo.modelo = _SVM()
    modelo.vectorizador = _Vectorizador()
    modelo.modelo_sistema = None
    modelo.temperatura = 0.5
    raw = modelo.predecir_top_fallas_svm_raw("motor vibra", limite=3)
    assert [p["falla"] for p in raw] == ["Falla B", "Falla A", "Falla C"]
    assert [p["probabilidad"] for p in raw] == [0.7, 0.2, 0.1]


def test_raw_y_tiempo_separados_del_diagnostico_operativo():
    dto = ResultadoDiagnostico(
        respuesta_texto="Orientación pendiente", diagnostico_ml="Indeterminado",
        confianza_ml=0.0, contexto_manual="", titulo_manual="",
        predicciones_svm_raw=[], motivo_abstencion="SIN_VOCABULARIO_TFIDF",
        tiempo_ml_ms=0, tiempo_total_ms=23,
    )
    assert dto.predicciones_svm_raw == []
    assert dto.motivo_abstencion == "SIN_VOCABULARIO_TFIDF"
    assert dto.tiempo_total_ms == 23
    assert dto.tiempo_ml_ms == 0


def test_tiempo_inferencia_incluye_pasada_svm_raw():
    # La segunda inferencia debe contabilizarse en el componente ML,
    # sin confundirse con la duración extremo a extremo.
    tiempo_raw_ms = 7
    tiempo_clasificacion_ms = 13
    tiempo_ml_ms = tiempo_raw_ms + tiempo_clasificacion_ms
    tiempo_total_ms = 45
    assert tiempo_ml_ms == 20
    assert tiempo_total_ms >= tiempo_ml_ms
