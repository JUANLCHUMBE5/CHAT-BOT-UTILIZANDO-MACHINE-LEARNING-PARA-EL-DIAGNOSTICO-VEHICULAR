"""Contrafactuales para reglas de coherencia posteriores al SVM congelado."""

import pytest

from src.core.diagnostico.models import PrediccionML
from src.core.diagnostico.reglas_coherencia_ml import (
    CADENA,
    COMMON_RAIL,
    RESTRICCION,
    aplicar_reglas_coherencia,
)


def _predicciones():
    return [
        PrediccionML(falla="Bateria descargada o bornes sulfatados", probabilidad=0.46),
        PrediccionML(falla=CADENA, probabilidad=0.17),
        PrediccionML(falla=COMMON_RAIL, probabilidad=0.12),
        PrediccionML(falla=RESTRICCION, probabilidad=0.08),
    ]


def _evaluar(texto):
    originales = _predicciones()
    return aplicar_reglas_coherencia(texto, originales[0].falla, 0.46, originales[:3], originales)


@pytest.mark.parametrize(
    "texto",
    [
        "El sensor CMP es nuevo pero salió defectuoso; todavía no medí sincronización.",
        "La SCV está sospechosa, sin medir presión del riel.",
        "Parece que falta petróleo, pero no se inspeccionó el filtro ni el tanque.",
        "Hilux gasolina 2.7: demora en arrancar en caliente.",
        "D-Max gasolina: el cebador que mencioné pertenece a otro vehículo.",
    ],
)
def test_afirmaciones_no_confirmadas_no_fuerzan_diagnostico(texto):
    diagnostico, confianza, _, motivo = _evaluar(texto)
    assert diagnostico == "Bateria descargada o bornes sulfatados"
    assert confianza == pytest.approx(0.46)
    assert motivo == ""


@pytest.mark.parametrize(
    "texto",
    [
        "No hay desfase; correlación medida 0 grados.",
        "Isuzu 4JJ1 diésel arranca en caliente; presión del riel 310 bar.",
        "Diésel con filtro nuevo y cebador firme; falta medir restricción.",
    ],
)
def test_contrafactuales_no_conservan_el_rescate(texto):
    assert _evaluar(texto)[0] == "Bateria descargada o bornes sulfatados"


@pytest.mark.parametrize(
    ("texto", "esperada", "probabilidad"),
    [
        ("Osciloscopio: correlación CMP CKP medida en 12 grados.", CADENA, 0.17),
        ("Isuzu 4JJ1 diésel falla caliente; presión del riel medida 140 bar.", COMMON_RAIL, 0.12),
        ("Diésel: se desmontó el pescador y la malla estaba obstruida con sedimento.", RESTRICCION, 0.08),
    ],
)
def test_evidencia_medida_reordena_y_conserva_score_svm(texto, esperada, probabilidad):
    diagnostico, confianza, predicciones, motivo = _evaluar(texto)
    assert diagnostico == esperada
    assert confianza == pytest.approx(probabilidad)
    assert predicciones[0].probabilidad == pytest.approx(probabilidad)
    assert predicciones[0].origen_probabilidad == "SVM_ORIGINAL_REORDENADO_REGLA"
    assert "score SVM original conservado" in motivo
    assert confianza not in (0.80, 0.82)
