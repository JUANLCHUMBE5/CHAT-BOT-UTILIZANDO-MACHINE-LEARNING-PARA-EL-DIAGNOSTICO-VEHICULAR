"""Pruebas de regresión y seguridad mecánica: preguntas contextuales de refrigeración vs frenos (Fase 3)."""

import pytest

from src.core.conversacion.compatibilidad_preguntas import CompatibilidadPreguntas
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.models import ConversationState, FactState, QuestionIntent


def test_recalentamiento_no_genera_pregunta_pedal_de_freno():
    """Verifica que 'el auto recalienta' jamás genere preguntas sobre el pedal de freno."""
    estado = ConversationState(session_id="test-recalentamiento-1")
    texto_usuario = "el auto recalienta"

    ExtractorHechos.extraer_y_actualizar(estado, texto_usuario)

    # El hecho de sobrecalentamiento debe estar confirmado y el dominio debe ser REFRIGERACION
    hecho_sobre = estado.obtener_hecho("sintoma_sobrecalentamiento")
    assert hecho_sobre is not None, "Debe extraer hecho sintoma_sobrecalentamiento"
    assert hecho_sobre.estado == FactState.CONFIRMADO

    dominio = CompatibilidadPreguntas.dominio_actual(estado)
    assert dominio == "REFRIGERACION"

    resultado = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    assert resultado is not None, "Debe seleccionar una pregunta contextual"
    pregunta, opciones, intent, candidatas, descartadas = resultado

    texto_p = pregunta.lower()
    assert "pedal de freno" not in texto_p, f"Pregunta contiene 'pedal de freno': {pregunta}"
    assert "pisar el pedal" not in texto_p
    assert "al frenar" not in texto_p
    assert any(
        w in texto_p
        for w in ("temperatura", "recalentamiento", "electroventilador", "refrigerante", "ralentí", "tráfico")
    ), f"Pregunta no es pertinente a refrigeración: {pregunta}"


@pytest.mark.parametrize(
    "expresion_peruana",
    [
        "mi caña se calienta en tráfico",
        "la aguja de temperatura se va al tope",
        "el auto hierve el agua",
        "está botando vapor por el capó",
        "calienta en subida y en pista plana baja",
        "se le sube la temperatura al motor",
        "la manguera inferior está fría y la superior hirviendo",
        "el motoventilador no arranca y recalienta",
    ],
)
def test_expresiones_coloquiales_peruanas_recalentamiento(expresion_peruana: str):
    """Prueba que múltiples expresiones coloquiales de taller reconozcan sobrecalentamiento sin sesgos."""
    estado = ConversationState(session_id="test-coloquial")
    ExtractorHechos.extraer_y_actualizar(estado, expresion_peruana)

    dominio = CompatibilidadPreguntas.dominio_actual(estado)
    assert dominio in ("REFRIGERACION", "MARCHA_MOTOR")

    resultado = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    if resultado:
        pregunta, _, _, _, _ = resultado
        assert "pedal de freno" not in pregunta.lower()
        assert "al frenar" not in pregunta.lower()


def test_multisistema_temperatura_y_frenos_genera_aclaracion():
    """Verifica que ante síntomas mixtos (recalentamiento + frenos), pregunte cuál ocurrió primero."""
    estado = ConversationState(session_id="test-multisistema")
    texto = "el auto recalienta y además los frenos están largos con pedal esponjoso"
    ExtractorHechos.extraer_y_actualizar(estado, texto)

    resultado = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    assert resultado is not None
    pregunta, opciones, intent, _, _ = resultado

    assert intent == QuestionIntent.ACLARACION_CONTRADICCION
    assert "cuál de estas dos anomalías se presentó primero" in pregunta.lower()


def test_seguridad_mecanica_refrigeracion_y_frenos():
    """Verifica que las comprobaciones técnicas incluyan advertencias de seguridad física."""
    estado = ConversationState(session_id="test-seguridad")
    texto = "el auto recalienta en subidas"
    ExtractorHechos.extraer_y_actualizar(estado, texto)

    # Forzar pregunta Plan B para validar advertencia
    estado.preguntas_realizadas.append({"intent": QuestionIntent.CONDICION_OPERACION.value})
    estado.preguntas_realizadas.append({"intent": QuestionIntent.COMPONENTE_REVISADO.value})

    resultado = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    if resultado:
        pregunta, _, intent, _, _ = resultado
        if intent == QuestionIntent.PLAN_B_SIN_HERRAMIENTAS:
            assert "nunca abras la tapa del radiador caliente" in pregunta.lower()
