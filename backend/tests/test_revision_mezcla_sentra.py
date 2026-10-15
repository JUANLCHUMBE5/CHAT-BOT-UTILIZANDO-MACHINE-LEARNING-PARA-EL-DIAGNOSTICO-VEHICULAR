"""Regresión aislada: una revisión concreta desbloquea el hilo de mezcla."""

from unittest.mock import MagicMock

import pytest

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.models import ConversationState, QuestionIntent
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.conversacion.revision_mezcla import registrar_revision_mezcla


@pytest.mark.anyio
async def test_sentra_revision_normal_avanza_a_maf_sin_repetir_trim():
    gestor = MagicMock()
    del gestor.session_manager
    flujo = OrquestadorConversacion(InMemoryConversationRepository())
    session_id = "sentra-local-aislado"
    primera = await flujo.procesar_turno(session_id, "Nissan Sentra con mezcla pobre", gestor)
    assert "STFT/LTFT" in primera["respuesta_texto"]
    segunda = await flujo.procesar_turno(
        session_id, "Ya revisé el cuerpo de aceleración y está bien", gestor,
    )
    assert "MAF" in segunda["respuesta_texto"]
    assert all(p not in segunda["respuesta_texto"].upper() for p in ("STFT", "LTFT", "DTC"))
    assert segunda["estado"].obtener_hecho("revision_normal_cuerpo_aceleracion") is not None
    assert any("IAC" in causa for causa in segunda["estado"].hipotesis_descartadas)
    tercera = await flujo.procesar_turno(session_id, "El MAF da lecturas raras", gestor)
    assert "MAF" in tercera["respuesta_texto"]
    assert all(p not in tercera["respuesta_texto"].upper() for p in ("STFT", "LTFT", "DTC"))
    assert tercera["estado"].active_system == "combustible_admision"
    gestor.procesar_consulta_texto.assert_not_called()


@pytest.mark.parametrize("texto", ["eso ya lo chequé", "esa parte está bien", "ya lo revisé y está bien"])
def test_revision_contextual_vinculada_a_un_punto(texto):
    estado = ConversationState(session_id="revision-contextual", active_system="combustible_admision")
    estado.registrar_pregunta(
        QuestionIntent.CONFIRMACION_ALTERNATIVA,
        "¿Revisaste el cuerpo de aceleración?",
        hipotesis=[{"falla": "Cuerpo de aceleración o válvula IAC sucia"}],
    )
    assert registrar_revision_mezcla(estado, texto) is not None
    assert not GeneradorPreguntas.falta_medicion_discriminante_por_area(estado)


@pytest.mark.parametrize("texto", [
    "El cuerpo de aceleración no está bien",
    "¿El cuerpo de aceleración está bien?",
    "No revisé el cuerpo de aceleración",
    "eso ya lo chequé",
])
def test_no_inventa_descarte_sin_resultado_o_referencia_inequivoca(texto):
    estado = ConversationState(session_id="revision-no-confirmada", active_system="combustible_admision")
    assert registrar_revision_mezcla(estado, texto) is None
    assert not estado.hipotesis_descartadas


def test_hallazgo_inyectores_conserva_prioridad_tras_revision():
    estado = ConversationState(session_id="revision-inyectores", active_system="combustible_admision")
    estado.historial_mensajes_usuario.append("Mezcla pobre")
    registrar_revision_mezcla(estado, "El cuerpo de aceleración está bien")
    ExtractorHechos.extraer_y_actualizar(estado, "Los injectores no inyectan lo suficiente")
    assert GeneradorPreguntas.pregunta_por_area(estado) is None
    assert not GeneradorPreguntas.falta_medicion_discriminante_por_area(estado)
