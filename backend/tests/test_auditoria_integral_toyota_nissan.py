"""Pruebas integrales de auditoría funcional para las conversaciones Toyota Yaris 2020 y Nissan Sentra 2021.

Verifica:
- Extracción y persistencia de múltiples datos en un solo mensaje.
- Ausencia de secuestro de respuestas libres como selección de hipótesis Top-3.
- Registro fiel de memoria: placa, síntomas específicos, duración, negaciones y limitaciones.
- Cambio de vehículo y nuevo caso sin pérdida de datos ni preguntas redundantes.
- Diferenciación de confianza estadística y advertencias de seguridad física.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.application.services.confirmacion_diagnostico import (
    interpretar_confirmacion_whatsapp,
    interpretar_respuesta_validacion_whatsapp,
    interpretar_seleccion_top3,
)
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.formato_salidas.generador_diagnostico import formatear_respuesta_diagnostico
from src.core.conversacion.models import ConversationState
from src.core.conversacion.resumen_memoria import generar_resumen_memoria
from src.core.parser.message_parser import SinglePassMessageParser
from src.core.services.webhook.validation_workflow import (
    _es_evidencia_diagnostica_nueva,
)
from src.core.services.webhook.vehicle_workflow import preparar_flujo_vehiculo

# ==============================================================================
# CASO A: Toyota Yaris 2020 (ABC-123)
# ==============================================================================

def test_caso_a_turno_1_extraccion_multidato_completa():
    """Turno 1: el usuario aporta vehículo, placa, síntomas con ubicación y duración juntos."""
    msg = (
        "Mi vehículo es un Toyota Yaris 2020, placa ABC123. Cuando freno escucho "
        "un chirrido en las ruedas delanteras y siento que el pedal vibra. "
        "El problema empezó hace tres días. ¿Qué podría estar fallando?"
    )
    parsed = SinglePassMessageParser.parse(msg)

    # 1. Vehículo y placa
    assert parsed.vehiculo.marca == "Toyota"
    assert parsed.vehiculo.modelo == "Yaris"
    assert parsed.vehiculo.anio == 2020
    assert parsed.vehiculo.placa == "ABC-123"

    # 2. Hechos afirmados específicos
    campos_afirmados = {h.campo for h in parsed.hechos_afirmados}
    assert "sintoma_chirrido_frenos" in campos_afirmados
    assert "sintoma_vibracion_pedal" in campos_afirmados

    # 3. Estado de conversación acumulativo
    estado = ConversationState(session_id="test_toyota_a")
    ExtractorHechos.extraer_y_actualizar(estado, msg)

    assert estado.placa == "ABC-123"
    assert estado.marca == "Toyota"
    assert estado.modelo == "Yaris"
    assert estado.anio == "2020"
    assert estado.obtener_hecho("duracion_problema") is not None
    assert "tres días" in estado.obtener_hecho("duracion_problema").valor


def test_caso_a_turno_2_no_secuestra_texto_libre_como_seleccion_top3():
    """Turno 2: retroalimentación libre NO debe interpretarse como selección de la hipótesis 1."""
    hipotesis = [
        {"falla": "Discos de freno alabeados o desgastados"},
        {"falla": "Desbalanceo en ruedas delanteras"},
        {"falla": "Holgura en rótulas de suspensión"},
    ]
    msg2 = (
        "El pedal no está esponjoso ni se va al fondo, pero sí siento vibraciones "
        "en el volante cuando freno. No tengo un reloj comparador ni puedo desmontar las ruedas."
    )

    # 1. No debe interpretarse como selección de hipótesis
    sel = interpretar_seleccion_top3(msg2, hipotesis)
    assert sel is None, "Una explicación libre no debe seleccionar hipótesis 1 ni 2"

    # 2. No debe tomarse como respuesta binaria afirmativa o negativa
    assert interpretar_respuesta_validacion_whatsapp(msg2) is None
    assert interpretar_confirmacion_whatsapp(msg2) is None

    # 3. Debe ser reconocido como evidencia técnica nueva para el orquestador
    assert _es_evidencia_diagnostica_nueva(msg2) is True


def test_caso_a_turno_2_captura_negaciones_y_limitaciones():
    """Turno 2: registra síntomas negados y limitaciones de herramientas/procedimientos."""
    msg2 = (
        "El pedal no está esponjoso ni se va al fondo, pero sí siento vibraciones "
        "en el volante cuando freno. No tengo un reloj comparador ni puedo desmontar las ruedas."
    )
    estado = ConversationState(session_id="test_toyota_a2")
    ExtractorHechos.extraer_y_actualizar(estado, msg2)

    # Negaciones registradas
    assert estado.es_hecho_negado("sintoma_pedal_esponjoso")
    assert estado.es_hecho_negado("sintoma_pedal_se_va_al_fondo")

    # Limitaciones registradas
    assert "reloj_comparador" in estado.herramientas_no_disponibles
    assert estado.es_prueba_bloqueada("desmontar_ruedas")


def test_caso_a_turno_3_memoria_fiel_y_detallada():
    """Turno 3: la memoria técnica muestra placa, síntomas detallados, duración, negaciones y limitaciones."""
    estado = ConversationState(session_id="test_toyota_a_mem")
    msg1 = (
        "Mi vehículo es un Toyota Yaris 2020, placa ABC123. Cuando freno escucho "
        "un chirrido en las ruedas delanteras y siento que el pedal vibra. "
        "El problema empezó hace tres días. ¿Qué podría estar fallando?"
    )
    msg2 = (
        "El pedal no está esponjoso ni se va al fondo, pero sí siento vibraciones "
        "en el volante cuando freno. No tengo un reloj comparador ni puedo desmontar las ruedas."
    )
    ExtractorHechos.extraer_y_actualizar(estado, msg1)
    ExtractorHechos.extraer_y_actualizar(estado, msg2)

    resumen = generar_resumen_memoria(estado)

    # 1. Muestra la placa ABC-123
    assert "ABC-123" in resumen or "ABC123" in resumen

    # 2. Refleja el vehículo
    assert "Toyota Yaris 2020" in resumen

    # 3. Refleja síntomas detallados (chirrido, pedal vibra, volante vibra)
    assert "chirrido" in resumen
    assert "pedal" in resumen
    assert "volante" in resumen

    # 4. Refleja la duración
    assert "tres días" in resumen

    # 5. Refleja síntomas negados
    assert "esponjoso" in resumen or "al fondo" in resumen

    # 6. Refleja limitaciones de herramientas y comprobaciones físicas
    assert "reloj comparador" in resumen
    assert "desmontar ruedas" in resumen


# ==============================================================================
# CASO B: Nissan Sentra 2021 (XYZ-789)
# ==============================================================================

def test_caso_b_turno_1_cambio_caso_con_datos_completos():
    """Turno 1: reconoce cambio de caso, placa, modelo y síntomas sin requerir repeticiones."""
    msg = (
        "Quiero iniciar un diagnóstico nuevo para otro vehículo. Es un Nissan Sentra 2021, "
        "placa XYZ789. No presenta problemas de frenos. Escucho golpes metálicos en la suspensión "
        "delantera cuando paso por baches. ¿Qué podría estar fallando?"
    )
    parsed = SinglePassMessageParser.parse(msg)

    # 1. Marcador de nuevo caso
    assert parsed.es_cambio_caso is True

    # 2. Entidades vehiculares
    assert parsed.vehiculo.marca == "Nissan"
    assert parsed.vehiculo.modelo == "Sentra"
    assert parsed.vehiculo.anio == 2021
    assert parsed.vehiculo.placa == "XYZ-789"

    # 3. Síntomas afirmados y negados
    campos_afirmados = {h.campo for h in parsed.hechos_afirmados}
    assert "sintoma_golpes_suspension" in campos_afirmados

    campos_negados = {h.campo for h in parsed.hechos_negados}
    assert "sintoma_frenos" in campos_negados or "funcionamiento_frenos" in campos_negados

    # 4. No debe reportar datos faltantes que obliguen a bucles
    assert "placa" not in parsed.datos_faltantes
    assert "sintoma" not in parsed.datos_faltantes


@pytest.mark.anyio
async def test_caso_b_workflow_transicion_inmediata_sin_compuertas_redundantes():
    """El workflow vehicular debe avanzar de inmediato a diagnóstico cuando los datos requeridos existen."""
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={
            # Caso previo de otro vehículo
            "placa": "ABC-123",
            "placa_posttest": "ABC-123",
            "perfil_vehiculo": {"marca": "Toyota", "modelo": "Yaris", "anio": 2020},
            "conversation_state": {"session_id": "prev"},
        },
    )
    session = AsyncMock()

    class GestorFalso:
        class SessionManagerFalso:
            def finalizar_caso(self, *args, **kwargs):
                pass
        session_manager = SessionManagerFalso()

    mock_self = SimpleNamespace(gestor=GestorFalso())

    msg = (
        "Quiero iniciar un diagnóstico nuevo para otro vehículo. Es un Nissan Sentra 2021, "
        "placa XYZ789. No presenta problemas de frenos. Escucho golpes metálicos en la suspensión "
        "delantera cuando paso por baches. ¿Qué podría estar fallando?"
    )

    resultado, placa_out, marca_modelo_out, _ = await preparar_flujo_vehiculo(
        self=mock_self,
        session=session,
        conversacion=conversacion,
        texto_cliente=msg,
        tipo_mensaje="text",
        proveedor="meta",
        remitente="+51999999999",
        placa="",
        marca_modelo="",
    )

    # Debe retornar None para resultado (no debe bloquear con 'esperando_placa' ni 'esperando_sintoma')
    assert resultado is None, f"Se esperaba pase directo a diagnóstico, pero retornó: {resultado}"
    assert placa_out in ("XYZ-789", "XYZ789")
    assert "nissan sentra 2021" in marca_modelo_out.lower()


def test_caso_b_advertencia_seguridad_suspension():
    """El diagnóstico de suspensión incluye advertencias de elevador/caballetes certificados."""
    top_hipotesis = [
        {"falla": "Amortiguadores reventados o bujes de suspensión gastados", "probabilidad": 0.85, "origen_probabilidad": "SVM"},
        {"falla": "Holgura en rótulas de suspensión", "probabilidad": 0.10, "origen_probabilidad": "SVM"},
    ]
    estado = ConversationState(session_id="test_nissan_seg")
    estado.active_symptoms = ["golpes metálicos en la suspensión delantera al pasar por baches"]

    respuesta = formatear_respuesta_diagnostico(
        top_hipotesis=top_hipotesis,
        sintoma_original="golpes metálicos en la suspensión delantera",
        estado=estado,
    )

    # 1. Contiene causas
    assert "Amortiguadores" in respuesta or "suspensión" in respuesta

    # 2. Contiene advertencia física de seguridad
    assert "Seguridad" in respuesta
    assert "elevador" in respuesta.lower() or "caballetes" in respuesta.lower()
