"""Regresiones locales de interacción, sin llamadas a proveedores ni persistencia."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.conversacion.avance_preguntas import asegurar_pregunta_util
from src.core.conversacion.formateador_compacto import _extraer_accion_prioritaria
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.models import ConversationState, QuestionIntent
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.mark.parametrize("sistema", ["refrigeracion", "encendido", "frenos", "electrico_ecu"])
def test_salida_final_no_repite_pregunta_y_registra_la_real(sistema):
    estado = ConversationState(session_id="pregunta-final", active_system=sistema)
    original = "¿Has revisado este punto?"
    estado.registrar_pregunta(QuestionIntent.MEDICION_TECNICA, original)
    previas = list(estado.preguntas_realizadas)
    estado.turno_actual += 1
    respuesta, pregunta = asegurar_pregunta_util(estado, "Mismo bloque. " + original, previas)
    assert original not in respuesta
    assert pregunta == estado.ultima_pregunta()["texto"]
    assert estado.ultima_pregunta()["metadata"]["origen"] == "salida_final"


def test_codificacion_respuesta_parcial_pide_solo_error_exacto():
    estado = ConversationState(session_id="ecu-parcial", active_system="electrico_ecu")
    estado.historial_mensajes_usuario = [
        "No arranca después de cambiar la computadora", "El escáner se comunica pero da error de codificación",
    ]
    estado.registrar_pregunta(
        QuestionIntent.MEDICION_TECNICA,
        "¿El número de parte coincide con el vehículo y qué mensaje/código exacto aparece al codificar?",
    )
    texto, _ = GeneradorPreguntas.pregunta_por_area(estado)
    assert "código o texto exacto" in texto
    assert "número de parte" not in texto


def test_medicion_map_no_equivale_a_maf_ni_carga_calculada():
    estado = ConversationState(session_id="map-unidades", active_system="combustible_admision")
    estado.historial_mensajes_usuario = ["carga absoluta fuera de rango"]
    texto, _ = GeneradorPreguntas.pregunta_por_area(estado)
    assert "presión MAP (kPa)" in texto
    assert "carga calculada (%)" in texto
    assert "flujo MAF (g/s)" in texto
    assert "condición del motor" in texto
    assert "no equivalentes" in texto


def test_ventilador_no_repite_la_misma_pregunta_con_otras_palabras():
    estado = ConversationState(session_id="fan", active_system="refrigeracion")
    previas = [{"texto": "¿El electroventilador se activa cuando aumenta la temperatura?"}]
    texto, pregunta = asegurar_pregunta_util(
        estado, "¿Funciona el ventilador cuando el motor se calienta?", previas,
    )
    assert "fuga visible" in pregunta
    assert "Funciona el ventilador" not in texto


def test_temperatura_en_marcha_no_se_segmenta_como_transmision():
    from src.core.conversacion.segmentador_casos import SegmentadorCasos, SubsistemaVehicular

    assert SegmentadorCasos.detectar_subsistema_texto(
        "Temperatura sube en marcha y en ralentí",
    ) == SubsistemaVehicular.MARCHA_MOTOR
    assert SegmentadorCasos.detectar_subsistema_texto("No entra segunda marcha") == SubsistemaVehicular.TRANSMISION


def test_frenos_no_presenta_tolerancia_universal_sin_fuente():
    texto = _extraer_accion_prioritaria("Discos de freno alabeados o desgastados")
    assert "0.05" not in texto and "0,05" not in texto
    assert "especificación del fabricante" in texto
    assert "reloj comparador" in texto


@pytest.mark.anyio
@pytest.mark.parametrize("respuesta", ["Sí", "No"])
async def test_rio_resultado_de_hallazgo_no_confirma_ni_descarta_o2(monkeypatch, respuesta):
    from src.config import settings

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    flujo = OrquestadorConversacion(InMemoryConversationRepository())
    sid = "rio-hallazgo-" + respuesta
    await flujo.procesar_turno(sid, "Kia Rio mezcla pobre en el scaner", gestor, proveedor="web")
    hallazgo = await flujo.procesar_turno(
        sid, "Encontré que los injectores no inyectan lo suficiente", gestor, proveedor="web",
    )
    prediccion_original = hallazgo["dto"].diagnostico_ml
    assert hallazgo["estado"].obtener_hecho("hipotesis_en_evaluacion") is not None
    assert "inyector" in hallazgo["estado"].falla_principal.lower()
    assert hallazgo["estado"].top3_actual == []  # Hallazgo sin probabilidad inventada.
    assert hallazgo["estado"].ultima_pregunta()["intent"] == QuestionIntent.MEDICION_TECNICA.value
    final = await flujo.procesar_turno(sid, respuesta, gestor, proveedor="web")
    assert final["decision"] != "CONFIRMACION"
    assert final["estado"].obtener_hecho("confirmacion_diagnostico_usuario") is None
    assert prediccion_original not in final["estado"].hipotesis_descartadas


@pytest.mark.anyio
@pytest.mark.parametrize("texto", ["Sí", "No"])
async def test_webhook_no_valida_top1_oculto_con_respuesta_al_hallazgo(monkeypatch, texto):
    from src.core.services.webhook.validation_workflow import ValidationWorkflow

    estado = ConversationState(session_id="validacion-aislada")
    estado.registrar_hecho("hipotesis_en_evaluacion", "Caudal de inyectores", categoria="flujo")
    estado.registrar_pregunta(QuestionIntent.MEDICION_TECNICA, "¿Tienes resultados de balance de inyectores?")
    conversacion = SimpleNamespace(contexto={
        "conversation_state": estado.exportar_dict(),
        "validacion_diagnostico": {"etapa": "esperando_confirmacion"},
    })
    confirmar = AsyncMock()
    monkeypatch.setattr(ValidationWorkflow, "procesar_confirmacion_tecnica", confirmar)
    resultado = await ValidationWorkflow.manejar_flujo_validacion(
        session=MagicMock(), conversacion=conversacion, usuario=None,
        texto_cliente=texto, tipo_mensaje="text", meta_message_id="local-fake",
        proveedor="api", remitente="local-fake", t_inicio=0,
    )
    assert resultado is None
    confirmar.assert_not_awaited()
    assert "validacion_diagnostico" not in conversacion.contexto
