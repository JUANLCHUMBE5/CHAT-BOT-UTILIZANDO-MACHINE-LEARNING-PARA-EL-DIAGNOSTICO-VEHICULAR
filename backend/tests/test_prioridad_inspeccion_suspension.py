"""La prioridad de taller nunca se presenta como una nueva probabilidad del SVM."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from src.core.conversacion.prioridad_inspeccion import CRITERIO_REBOTE, ordenar_inspeccion

JOINT = {"falla": "Juntas homocineticas o palieres danados", "probabilidad": .41, "origen_probabilidad": "SVM"}
DAMPER = {"falla": "Amortiguadores reventados o bujes de suspension gastados", "probabilidad": .36,
          "origen_probabilidad": "SVM"}


@pytest.mark.parametrize("mensaje", [
    "Después de los desniveles la carrocería sigue rebotando varias veces.",
    "Presenta oscilación excesiva de la carrocería al superar irregularidades.",
    "El coche rebota en baches. No sé cuál pieza falla.",
])
def test_prioriza_inspeccion_sin_modificar_predicciones(mensaje):
    raw = [deepcopy(JOINT), deepcopy(DAMPER)]
    antes = deepcopy(raw)
    salida = ordenar_inspeccion(raw, SimpleNamespace(historial_mensajes_usuario=[mensaje]))
    assert raw == antes
    assert salida[0]["falla"] == DAMPER["falla"]
    assert salida[0]["criterio_presentacion"] == CRITERIO_REBOTE
    assert {p["falla"]: p["probabilidad"] for p in salida} == {
        p["falla"]: p["probabilidad"] for p in raw
    }
    assert salida[1] == JOINT


@pytest.mark.parametrize("mensaje", [
    "Golpe en baches, pero no rebota.",
    "Al pasar rompemuelles no se percibe oscilación excesiva.",
    "Golpeteo en desniveles sin rebote excesivo.",
    "¿Puede rebotar en los baches por un amortiguador?",
    "Rebota en baches y hace clac al girar y acelerar.",
    "Oscilación excesiva en irregularidades y pedal de freno esponjoso.",
    "Golpe al circular por baches.",
    "Cuando giro se escucha clac clac.",
])
def test_no_reordena_negaciones_hipotesis_o_casos_mixtos(mensaje):
    raw = [deepcopy(JOINT), deepcopy(DAMPER)]
    assert ordenar_inspeccion(raw, SimpleNamespace(historial_mensajes_usuario=[mensaje])) == raw


def test_no_inventa_candidata_ni_revive_descartada():
    estado = SimpleNamespace(historial_mensajes_usuario=["Rebota después de los baches."])
    assert ordenar_inspeccion([], estado) == []
    assert ordenar_inspeccion([JOINT], estado) == [JOINT]


def test_correccion_reciente_tiene_precedencia_sobre_rebote_antiguo():
    estado = SimpleNamespace(historial_mensajes_usuario=[
        "Rebota en los baches.", "Me corrijo: no rebota, solo hace un ruido.",
    ])
    assert ordenar_inspeccion([JOINT, DAMPER], estado) == [JOINT, DAMPER]


def test_llm_no_borra_prioridad_explicita():
    from src.core.conversacion.formato_salidas.generador_diagnostico import integrar_respuesta_llm

    assert integrar_respuesta_llm(
        "Cambia la homocinética.", "Orden de inspección; sin confirmar.", True, False,
        prioridad_inspeccion=True,
    ) == "Orden de inspección; sin confirmar."
