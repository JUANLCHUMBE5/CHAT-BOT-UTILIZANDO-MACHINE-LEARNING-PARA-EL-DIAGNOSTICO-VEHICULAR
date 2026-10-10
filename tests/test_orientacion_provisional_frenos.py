"""Regresiones para orientación segura cuando el mecánico no puede hacer pruebas físicas."""

from types import SimpleNamespace

import pytest

from src.core.conversacion.avance_preguntas import asegurar_pregunta_util
from src.core.conversacion.models import ConversationState, QuestionIntent
from src.core.conversacion.orientacion_provisional import es_imposibilidad_completa
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.diagnostico.models import ResultadoDiagnostico
from src.core.services.webhook.diagnostic_persister import DiagnosticPersister


class GestorFrenosMock:
    session_manager = None
    motor_rag = None

    def procesar_consulta_texto(self, **_kwargs):
        return SimpleNamespace(
            diagnostico_ml="Discos de freno bajo evaluación",
            confianza_ml=0.72,
            predicciones_ml=[{"falla": "Discos de freno bajo evaluación", "probabilidad": 0.72}],
        )


def _estado_frenos() -> ConversationState:
    estado = ConversationState(session_id="t16-frenos", case_id="case-frenos-t16")
    estado.placa = "T16-001"
    estado.active_system = "frenos"
    estado.active_symptoms = ["chirrido delantero al frenar", "vibración en el pedal"]
    estado.hipotesis_descartadas = ["Aire en el circuito hidráulico"]
    estado.registrar_pregunta(
        QuestionIntent.MEDICION_TECNICA,
        "¿Qué alabeo se midió en los discos y cuál es la especificación del vehículo?",
    )
    return estado


def test_imposibilidad_fisica_no_repite_prueba_ni_confirma_falla() -> None:
    estado = _estado_frenos()
    mensaje = "No puedo realizar comprobaciones físicas ni confirmar síntomas adicionales."

    assert es_imposibilidad_completa(mensaje)
    estado.historial_mensajes_usuario.append(mensaje)
    respuesta, pregunta = asegurar_pregunta_util(estado, "¿Qué alabeo se midió en los discos?", [])

    assert pregunta is None
    assert "provisional y no confirma una falla" in respuesta.lower()
    assert "revisión presencial" in respuesta.lower()
    assert "¿" not in respuesta
    assert estado.case_id == "case-frenos-t16"
    assert estado.placa == "T16-001"
    assert estado.active_symptoms == ["chirrido delantero al frenar", "vibración en el pedal"]
    assert estado.hipotesis_descartadas == ["Aire en el circuito hidráulico"]


@pytest.mark.anyio
async def test_orquestador_marca_orientacion_provisional_y_preserva_contexto() -> None:
    repositorio = InMemoryConversationRepository()
    estado = _estado_frenos()
    await repositorio.save_session(estado.session_id, estado)
    resultado = await OrquestadorConversacion(repositorio).procesar_turno(
        estado.session_id,
        "No puedo realizar comprobaciones físicas ni confirmar síntomas adicionales.",
        GestorFrenosMock(),
    )

    assert resultado["decision"] == "ORIENTACION_PROVISIONAL"
    assert resultado["es_pregunta"] is False
    assert "provisional y no confirma una falla" in resultado["respuesta_texto"].lower()
    assert "revisión presencial" in resultado["respuesta_texto"].lower()
    assert resultado["estado"].case_id == "case-frenos-t16"
    assert resultado["estado"].placa == "T16-001"
    assert resultado["estado"].hipotesis_descartadas == ["Aire en el circuito hidráulico"]


def test_orientacion_provisional_no_pide_feedback_binario() -> None:
    dto = ResultadoDiagnostico(
        respuesta_texto="Orientación provisional: solicita revisión presencial.",
        diagnostico_ml="Frenos en evaluación",
        confianza_ml=0.0,
        contexto_manual="",
        titulo_manual="",
        requiere_revision_humana=True,
        modo_diagnostico="orientacion_provisional",
        tipo_consulta="orientacion_provisional",
        es_orientacion_provisional=True,
    )

    assert DiagnosticPersister.debe_solicitar_feedback(dto) is False
