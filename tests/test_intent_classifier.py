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


def test_pedal_de_freno_hundiendose_es_diagnostico_y_no_consulta_tecnica():
    mensaje = (
        "tengo un susto tremendo con los frenos: cuando voy manejando y freno normal o de golpe, "
        "el carro se detiene bien. El problema es cuando me quedo parado esperando la luz verde... "
        "siento clarito cómo el pedal se va hundiendo despacito, despacito, hasta que llega al fondo... "
        "el tachito del líquido de frenos tiene el nivel completo"
    )
    normalizado = normalizar_jerga_peruana(mensaje)
    assert clasificar_intencion_consulta(normalizado) == "diagnostico"


@pytest.mark.parametrize(
    ("pregunta", "intencion_esperada"),
    [
        ("¿A cuántas libras se calibra la bujía?", "consulta_tecnica"),
        ("como calibrar las bujias de mi auto", "consulta_tecnica"),
        ("que presion de inflado llevan las llantas?", "consulta_tecnica"),
        ("receta para cocinar lomo saltado", "fuera_de_alcance"),
    ],
)
def test_consultas_tecnicas_vs_fuera_de_alcance(pregunta, intencion_esperada):
    normalizado = normalizar_jerga_peruana(pregunta)
    assert clasificar_intencion_consulta(normalizado) == intencion_esperada

