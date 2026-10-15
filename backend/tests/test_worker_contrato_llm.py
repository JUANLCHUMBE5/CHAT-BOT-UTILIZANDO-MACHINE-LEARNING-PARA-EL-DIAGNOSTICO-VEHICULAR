"""El worker aplica el mismo contrato cerrado que la ruta síncrona."""

import json

import pytest

from src.core.gemini_queue.models import SolicitudGeminiEncolada
from src.core.gemini_queue.worker_processor import _validar_diagnostico_llm


@pytest.fixture
def solicitud():
    return SolicitudGeminiEncolada(
        diagnostico_ml="Batería descargada",
        predicciones_ml=[{"falla": "Motor de arranque defectuoso", "probabilidad": 0.2}],
    )


@pytest.mark.parametrize(
    "respuesta",
    [
        "Cambie la SCV inmediatamente.",
        '{"hipotesis":"Incendio","explicacion":"confirmado","siguiente_prueba":"ninguna","pregunta":"¿ok?"}',
        '{"hipotesis":"Batería descargada","explicacion":"posible"}',
        '{"hipotesis":"Batería descargada","explicacion":"confirmado: midió 8 V",'
        '"siguiente_prueba":"cambiar batería","pregunta":"¿ok?"}',
        '{"hipotesis":"Batería descargada","explicacion":"posible",'
        '"siguiente_prueba":"destapa el radiador caliente","pregunta":"¿ok?"}',
    ],
)
def test_rechaza_json_invalido_peligroso_o_contradictorio(solicitud, respuesta):
    with pytest.raises(ValueError):
        _validar_diagnostico_llm(respuesta, solicitud)


def test_acepta_hipotesis_permitida_sin_convertirla_en_confirmacion(solicitud):
    respuesta = json.dumps(
        {
            "hipotesis": "Batería descargada",
            "explicacion": "Es una hipótesis; falta medir voltaje bajo carga.",
            "siguiente_prueba": "Mida voltaje durante el arranque.",
            "pregunta": "¿Qué voltaje obtiene?",
        }
    )
    salida = _validar_diagnostico_llm(respuesta, solicitud)
    assert "Hipótesis: Batería descargada" in salida
    assert "falta medir" in salida
