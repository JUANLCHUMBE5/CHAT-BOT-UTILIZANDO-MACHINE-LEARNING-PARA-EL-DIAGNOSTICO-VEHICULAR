"""Pruebas de paridad Test <-> WhatsApp y Selección Contextual de Preguntas (Fase 9.7)."""

from unittest.mock import MagicMock

import pytest

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.models import (
    ConversationState,
    EstadoOperativo,
    QuestionIntent,
)
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.services.webhook.diagnostic_workflow import TechnicalDiagnosticWorkflow
from src.core.version import ORCHESTRATOR_VERSION


@pytest.fixture(scope="module")
def gestor_fixture():
    return GestorDiagnostico()


@pytest.mark.anyio
async def test_paridad_caso_exacto_webhook_vs_test(gestor_fixture):
    """
    Verifica que el caso exacto de Fase 9.6/9.7 procesado por TechnicalDiagnosticWorkflow (entrypoint de WhatsApp)
    genere exactamente la pregunta de comportamiento de arranque y caída de tensión.
    """
    texto = (
        "Buenas, mi carro tiene un problema. Ayer lo dejé estacionado en la calle y cuando "
        "volví en la noche ya no quiso arrancar. Le doy a la llave y hace como un clic seco, "
        "una sola vez, y nada más. Las luces del tablero sí prenden bien, y el radio también."
    )

    conv = MagicMock()
    conv.id = "parity-test-001"
    conv.contexto = {}

    usuario = MagicMock()
    usuario.id = "mecanico-001"
    usuario.taller_id = "taller-001"
    usuario.nombres = "Mecánico Prueba"

    res = await TechnicalDiagnosticWorkflow.preparar(
        gestor=gestor_fixture,
        conversacion=conv,
        usuario=usuario,
        remitente="51955095147",
        proveedor="meta",
        tipo_mensaje="text",
        texto_cliente=texto,
        audio_id="",
        placa="WAPP-01",
        marca_modelo="Vehiculo Generico",
    )

    # 1. Validación de respuesta técnica
    assert "¿las luces del tablero se atenúan" in res.dto.respuesta_texto
    assert "brillo normal" in res.dto.respuesta_texto
    assert res.dto.modo_diagnostico == "esperando_clarificacion"

    # 2. Validación de estado persistido en contexto
    cs = conv.contexto.get("conversation_state", {})
    assert cs.get("estado_operativo") == EstadoOperativo.ARRANQUE.value
    assert "motor_arranca" in cs.get("hechos", {})
    assert cs["hechos"]["motor_arranca"]["valor"] == "NO"
    assert "ruido_arranque" in cs.get("hechos", {})
    assert cs["hechos"]["ruido_arranque"]["valor"] == "clic_unico"

    # 3. Validación de traza y versión
    assert cs.get("trazabilidad")
    traza = cs["trazabilidad"][-1]
    assert traza.get("version_orquestador") == ORCHESTRATOR_VERSION
    assert traza.get("question_intent") == QuestionIntent.COMPORTAMIENTO_ARRANQUE.value

    # 4. Auditoría de candidatas y descartadas (demostrar rechazo de temperatura de trabajo)
    descartadas = traza.get("preguntas_descartadas", [])
    motivos_descarte = [d.get("motivo") for d in descartadas]
    assert any("PRECONDICION_NO_CUMPLIDA: REQUIERE_MOTOR_EN_MARCHA" in m for m in motivos_descarte)


def test_principio_presuposiciones_temperatura_motor_en_marcha():
    """Demuestra que una pregunta que presupone temperatura de trabajo es incompatible si motor_arranca=NO."""
    estado = ConversationState(session_id="test_presuposicion_1")
    estado.estado_operativo = EstadoOperativo.ARRANQUE
    estado.registrar_hecho("motor_arranca", "NO")

    # Pregunta con presuposición de motor en marcha
    txt_marcha = (
        "¿El problema aparece en frío o únicamente después de que el motor "
        "alcanza su temperatura de trabajo normal?"
    )
    compatible, motivo = GeneradorPreguntas.es_pregunta_compatible(
        QuestionIntent.TEMPERATURA_APARICION, txt_marcha, estado
    )
    assert not compatible
    assert motivo == "PRECONDICION_NO_CUMPLIDA: REQUIERE_MOTOR_EN_MARCHA"

    # En cambio, pregunta ambiental de arranque NO presupone régimen
    txt_ambiental = (
        "¿La dificultad para arrancar ocurrió con el motor totalmente frío "
        "o intentaste encenderlo poco después de haber apagado el motor?"
    )
    compatible_amb, motivo_amb = GeneradorPreguntas.es_pregunta_compatible(
        QuestionIntent.TEMPERATURA_APARICION, txt_ambiental, estado
    )
    assert compatible_amb
    assert motivo_amb is None


def test_temperatura_permitida_cuando_hay_antecedente_de_marcha():
    """Si el usuario indica que venía conduciendo, la pregunta térmica en caliente SÍ es compatible."""
    estado = ConversationState(session_id="test_presuposicion_2")
    msg = "Venía manejando en carretera y tras 20 minutos el motor se apagó y ya no quiso arrancar."
    ExtractorHechos.extraer_y_actualizar(estado, msg)

    txt_marcha = (
        "¿El problema aparece con el motor aún frío "
        "o únicamente después de que el motor alcanza su temperatura de trabajo normal tras circular?"
    )
    compatible, motivo = GeneradorPreguntas.es_pregunta_compatible(
        QuestionIntent.TEMPERATURA_APARICION, txt_marcha, estado
    )
    assert compatible
    assert motivo is None


def test_priorizacion_por_ganancia_de_informacion_en_arranque():
    """Demuestra que COMPORTAMIENTO_ARRANQUE (score 85) gana sobre temperatura ambiental (65) y DTC (40)."""
    estado = ConversationState(session_id="test_ganancia_info")
    msg = "Ayer lo dejé estacionado y hoy no arranca, hace clic seco."
    ExtractorHechos.extraer_y_actualizar(estado, msg)

    seleccion = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    assert seleccion is not None
    txt, opc, intent, candidatas, descartadas = seleccion

    assert intent == QuestionIntent.COMPORTAMIENTO_ARRANQUE
    assert "luces del tablero se atenúan" in txt


# === BATERÍA DE REGRESIÓN DE 11 ESCENARIOS ===

def test_regresion_1_no_arranque_clic_unico():
    st = ConversationState(session_id="reg_1")
    ExtractorHechos.extraer_y_actualizar(st, "No arranca. Hace un solo clic seco al girar la llave.")
    sel = GeneradorPreguntas.seleccionar_pregunta_con_filtro(st)
    assert sel is not None
    assert sel[2] == QuestionIntent.COMPORTAMIENTO_ARRANQUE
    assert "luces" in sel[0].lower()


def test_regresion_2_clac_clac_luces_tenues():
    st = ConversationState(session_id="reg_2")
    ExtractorHechos.extraer_y_actualizar(
        st, "No arranca, hace clac clac clac y las luces del tablero se ponen tenues al dar arranque."
    )
    # Luces ya conocidas y ruido ya conocido -> suficiencia o no repreguntar luces
    sel = GeneradorPreguntas.seleccionar_pregunta_con_filtro(st)
    if sel:
        assert "luces del tablero se atenúan" not in sel[0]


def test_regresion_3_falla_unicamente_en_caliente():
    st = ConversationState(session_id="reg_3")
    ExtractorHechos.extraer_y_actualizar(
        st, "El carro anda bien al inicio, pero cuando calienta después de 30 minutos empieza a fallar."
    )
    assert st.estado_operativo == EstadoOperativo.MARCHA
    # Temperatura ya conocida lingüísticamente
    assert st.obtener_hecho("temperatura") is not None


def test_regresion_4_falla_unicamente_en_frio():
    st = ConversationState(session_id="reg_4")
    ExtractorHechos.extraer_y_actualizar(
        st, "Falla solo en frío en la mañana al encender, luego de 5 minutos ya empareja."
    )
    assert st.obtener_hecho("temperatura") is not None


def test_regresion_5_perdida_potencia_en_marcha():
    st = ConversationState(session_id="reg_5")
    ExtractorHechos.extraer_y_actualizar(
        st, "El auto pierde fuerza al subir pendientes en carretera, no pasa de 80 km/h."
    )
    assert st.estado_operativo == EstadoOperativo.MARCHA
    sel = GeneradorPreguntas.seleccionar_pregunta_con_filtro(st)
    if sel:
        assert sel[2] != QuestionIntent.COMPORTAMIENTO_ARRANQUE


def test_regresion_6_ralenti():
    st = ConversationState(session_id="reg_6")
    ExtractorHechos.extraer_y_actualizar(
        st, "El motor tiembla mucho cuando estoy detenido en el semáforo en ralentí."
    )
    assert st.estado_operativo == EstadoOperativo.RALENTI
    sel = GeneradorPreguntas.seleccionar_pregunta_con_filtro(st)
    if sel:
        assert sel[2] != QuestionIntent.COMPORTAMIENTO_ARRANQUE


def test_regresion_7_frenado():
    st = ConversationState(session_id="reg_7")
    ExtractorHechos.extraer_y_actualizar(
        st, "Siento una vibración muy fuerte en el pedal al frenar a alta velocidad."
    )
    assert st.estado_operativo == EstadoOperativo.FRENADO
    sel = GeneradorPreguntas.seleccionar_pregunta_con_filtro(st)
    if sel:
        assert sel[2] != QuestionIntent.COMPORTAMIENTO_ARRANQUE
        assert sel[2] != QuestionIntent.CODIGO_DTC  # Avería puramente mecánica


def test_regresion_8_estado_desconocido():
    st = ConversationState(session_id="reg_8")
    ExtractorHechos.extraer_y_actualizar(st, "Tengo una falla en mi carro, me preocupa.")
    assert st.estado_operativo == EstadoOperativo.DESCONOCIDO
    sel = GeneradorPreguntas.seleccionar_pregunta_con_filtro(st)
    assert sel is not None
    assert sel[2] == QuestionIntent.CONDICION_OPERACION


def test_regresion_9_contradiccion():
    st = ConversationState(session_id="reg_9")
    ExtractorHechos.extraer_y_actualizar(
        st, "No arranca nada pero cuando voy a 100 km/h en carretera se chupa."
    )
    assert st.obtener_hecho("conflicto_operativo") is not None
    sel = GeneradorPreguntas.seleccionar_pregunta_con_filtro(st)
    assert sel is not None
    assert sel[2] == QuestionIntent.ACLARACION_CONTRADICCION


def test_regresion_10_caso_nuevo_reinicio():
    st = ConversationState(session_id="reg_10")
    st.registrar_hecho("falla", "batería")
    assert ExtractorHechos.es_reinicio_solicitado("Hola, quiero consultar por otro carro")


def test_regresion_11_flujo_no_descarte_alternativa():
    """Verifica que responder NO tras una pregunta registre el descarte sin bucles."""
    st = ConversationState(session_id="reg_11")
    st.top3_actual = [
        {"falla": "Bateria descargada", "probabilidad": 0.8},
        {"falla": "Motor de arranque", "probabilidad": 0.15},
    ]
    st.registrar_pregunta(QuestionIntent.DISCRIMINACION_TOP3, "¿Es la batería?")
    from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas
    res_no = InterpreteRespuestasCortas.interpretar(st, "no")
    assert res_no["campo"] == "confirmacion"
    assert res_no["valor"] == "no"
