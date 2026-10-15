"""No repetir procedimientos imposibles ni preguntas que contradicen negaciones."""
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.formato_salidas.generador_diagnostico import (
    evitar_respuesta_repetida,
    formatear_respuesta_diagnostico,
)
from src.core.conversacion.models import ConversationState


def test_pregunta_personalizada_respeta_negacion_persistida():
    estado = ConversationState(session_id="pregunta-negada")
    ExtractorHechos.extraer_y_actualizar(estado, "No presenta pérdida de potencia.")
    respuesta = formatear_respuesta_diagnostico(
        [{"falla": "Falla en regulador de presion de combustible o diafragma roto", "probabilidad": 0.54}],
        estado=estado, pregunta_personalizada="¿La pérdida de fuerza empeora con el tanque vacío?",
    )
    assert "¿La pérdida de fuerza" not in respuesta
    assert "pendiente" in respuesta


def test_respuesta_repetida_sin_evidencia_nueva_se_detiene():
    estado = ConversationState(session_id="abstencion")
    anterior = "Sin hipótesis ML compatible. Realiza inspección de bujes rótulas y bieletas con seguridad."
    estado.trazabilidad = [{"respuesta_enviada": anterior}]
    actual = evitar_respuesta_repetida(anterior, estado, False, [])
    assert actual != anterior
    assert "sin confirmar" in actual
    assert "¿" not in actual


def test_prueba_no_disponible_no_se_insiste():
    estado = ConversationState(session_id="sin-herramienta")
    anterior = "Sin hipótesis ML priorizable. Comprueba físicamente las holguras de rótulas y bieletas con el vehículo correctamente elevado."
    estado.trazabilidad = [{"respuesta_enviada": anterior}]
    actual = evitar_respuesta_repetida(
        anterior, estado, False, [{"campo": "inspeccion_pendiente", "estado": "NO_REVISADO"}],
    )
    assert actual != anterior
    assert "No repetiré" in actual
