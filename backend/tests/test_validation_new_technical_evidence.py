"""Regresiones para no perder evidencia detrás de una validación pendiente."""

from src.core.services.webhook.validation_workflow import (
    _es_evidencia_diagnostica_nueva,
    _registrar_turno_consumido_por_validacion,
)


def test_evidencia_tecnica_no_se_confunde_con_confirmacion_pendiente():
    assert _es_evidencia_diagnostica_nueva(
        "La bobina 1 fue intercambiada con la 2 y el P0301 no se movió."
    )
    assert _es_evidencia_diagnostica_nueva("El termostato abre a 82 grados Celsius.")
    assert _es_evidencia_diagnostica_nueva("La presión real llega solo a 1.05 bar absolutos.")


def test_confirmaciones_cortas_siguen_en_el_flujo_de_validacion():
    assert not _es_evidencia_diagnostica_nueva("sí")
    assert not _es_evidencia_diagnostica_nueva("no")
    assert not _es_evidencia_diagnostica_nueva("incorrecto")


def test_validacion_persiste_el_turno_tecnico_que_consumio():
    contexto = {"conversation_state": {"session_id": "regresion-validacion"}}
    texto = "Puedo aislar inyectores con tapones certificados mañana."

    _registrar_turno_consumido_por_validacion(contexto, texto, "regresion-validacion")

    estado = contexto["conversation_state"]
    assert estado["turno_actual"] == 1
    assert estado["historial_mensajes_usuario"] == [texto]
