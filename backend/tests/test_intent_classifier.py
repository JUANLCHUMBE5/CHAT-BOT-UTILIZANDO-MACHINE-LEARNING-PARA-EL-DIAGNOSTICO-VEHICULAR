"""Regresiones de clasificación para síntomas escritos informalmente."""

import pytest

from src.core.intent_classifier import clasificar_intencion_consulta
from src.core.traductor_jerga import normalizar_jerga_peruana


@pytest.mark.parametrize(
    "mensaje",
    [
        "El cliente indica que tiene vibraciones al manejar",
        "Vibraciones al manejar",
        "Vibración al menjar",
    ],
)
def test_vibraciones_al_manejar_es_un_diagnostico(mensaje):
    normalizado = normalizar_jerga_peruana(mensaje)

    assert "vibracion" in normalizado
    assert "manejar" in normalizado
    assert clasificar_intencion_consulta(normalizado) == "diagnostico"
