"""Pruebas de compatibilidad clínica de preguntas y aislamiento de casos (Fase 11.4.1).

Verifica que nunca se seleccionen preguntas incompatibles con el síntoma activo,
que las negaciones epistemológicas no descarten sistemas, y que las transiciones
entre dominios aíslen limpiamente el contexto.
"""


import pytest

from src.core.conversacion.compatibilidad_preguntas import CompatibilidadPreguntas
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import (
    ConversationState,
    EstadoOperativo,
    FactState,
    QuestionIntent,
)
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.segmentador_casos import (
    SegmentadorCasos,
    SubsistemaVehicular,
)
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.fixture(scope="module")
def gestor_diag():
    return GestorDiagnostico()


@pytest.fixture
def orquestador():
    return OrquestadorConversacion()


import asyncio


# ==============================================================================
# SECCIÓN 15: TEST EXACTO DEL MENSAJE REAL DE WHATSAPP
# ==============================================================================
def test_seccion_15_mensaje_real_tras_suspension(gestor_diag, orquestador):
    async def _run():
        session_id = "test_fase11_4_1_real_exact"
        
        # Turno 1: Suspensión previa
        msg1 = (
            "Hola, ahora quisiera revisar otro problema. Cuando paso por pistas irregulares "
            "o baches escucho un golpeteo en la parte delantera del carro. En pista lisa casi no se escucha. "
            "Al frenar no vibra el volante y el motor funciona normal. Todavía no he revisado la suspensión."
        )
        res1 = await orquestador.procesar_mensaje(session_id=session_id, texto_usuario=msg1, gestor_diagnostico=gestor_diag)
        assert res1["estado"].dominio_probable == "SUSPENSION"

        # Turno 2: Mensaje real de WhatsApp reportado en Fase 11.4.1
        msg2 = (
            "Hola, tengo un vehículo en el taller. El cliente comenta que demora bastante en encender por las mañanas. "
            "Una vez que logra encender, el motor funciona normal y no se prende ninguna luz de advertencia. "
            "Todavía no he revisado batería, arranque ni sistema de combustible. ¿Qué debería revisar primero?"
        )
        res2 = await orquestador.procesar_mensaje(session_id=session_id, texto_usuario=msg2, gestor_diagnostico=gestor_diag)
        
        estado2 = res2["estado"]
        assert estado2.estado_operativo == EstadoOperativo.ARRANQUE
        assert estado2.dominio_probable == "ARRANQUE"
        assert "sintoma_demora_arranque" in estado2.hechos
        assert estado2.hechos["sintoma_demora_arranque"].estado == FactState.CONFIRMADO

        # Hechos de suspensión no deben existir en el caso activo
        for k in estado2.hechos:
            assert "suspension" not in k.lower() or estado2.hechos[k].estado == FactState.NO_REVISADO
            assert "bache" not in k.lower()
            assert "golpeteo" not in k.lower()

        # La pregunta seleccionada JAMÁS debe ser de suspensión
        resp_texto = res2["respuesta_texto"]
        assert "bujes" not in resp_texto.lower()
        assert "rótulas" not in resp_texto.lower()
        assert "rotulas" not in resp_texto.lower()
        assert "trapecios" not in resp_texto.lower()

        # Debe ser una pregunta pertinente de arranque
        assert any(w in resp_texto.lower() for w in ("arrancar", "arranque", "llave", "girar", "tablero", "batería", "bateria", "luces"))

    asyncio.run(_run())


# ==============================================================================
# SECCIÓN 16: VARIANTES DE ARRANQUE EN FRÍO
# ==============================================================================
@pytest.mark.parametrize(
    "frase",
    [
        "Le cuesta prender en frío.",
        "En las mañanas demora varios segundos en encender.",
        "Da marcha bastante rato y luego prende.",
        "Solo tarda en arrancar cuando está frío.",
        "Después de encender funciona normal.",
        "Cliente dice que demora en prender, aún no revisé batería.",
        "Arranca mal en la mañana y luego trabaja normal.",
    ],
)
def test_seccion_16_variantes_arranque_dominio(frase):
    sub = SegmentadorCasos.detectar_subsistema_texto(frase)
    assert sub in (SubsistemaVehicular.ARRANQUE, SubsistemaVehicular.DESCONOCIDO)
    # Ninguna variante debe clasificarse como suspensión, frenos o climatización
    assert sub not in (
        SubsistemaVehicular.SUSPENSION,
        SubsistemaVehicular.FRENOS,
        SubsistemaVehicular.CLIMATIZACION,
    )


# ==============================================================================
# SECCIÓN 17: TEST DE NEGACIÓN EPISTEMOLÓGICA (NO CONFUNDIR NO REVISADO CON AUSENCIA)
# ==============================================================================
def test_seccion_17_negaciones_epistemologicas():
    frase = (
        "Todavía no he revisado batería, arranque ni sistema de combustible. "
        "No he medido presión de combustible. No tengo scanner. No sé si tiene códigos."
    )
    estado = ConversationState(session_id="test_epist")
    ExtractorHechos.extraer_y_actualizar(estado, frase)

    # Componentes no revisados deben registrarse como NO_REVISADO, NO como AUSENTE_NEGADO
    assert estado.obtener_hecho("revision_bateria") is not None
    assert estado.obtener_hecho("revision_bateria").estado == FactState.NO_REVISADO

    assert estado.obtener_hecho("revision_arranque") is not None
    assert estado.obtener_hecho("revision_arranque").estado == FactState.NO_REVISADO

    assert estado.obtener_hecho("revision_sistema_combustible") is not None
    assert estado.obtener_hecho("revision_sistema_combustible").estado == FactState.NO_REVISADO

    assert estado.obtener_hecho("revision_presion") is not None
    assert estado.obtener_hecho("revision_presion").estado == FactState.NO_REVISADO

    # Scanner no disponible debe ser NO_APLICA
    assert estado.obtener_hecho("escaner_disponible") is not None
    assert estado.obtener_hecho("escaner_disponible").valor == "NO"

    # Códigos desconocidos
    assert estado.obtener_hecho("codigos_dtc_observados") is not None
    assert estado.obtener_hecho("codigos_dtc_observados").estado == FactState.DESCONOCIDO


# ==============================================================================
# SECCIÓN 18: TEST DE RECHAZO DE PREGUNTAS INCOMPATIBLES EN CASO DE ARRANQUE
# ==============================================================================
def test_seccion_18_rechazo_preguntas_incompatibles():
    estado = ConversationState(session_id="test_incompat")
    estado.estado_operativo = EstadoOperativo.ARRANQUE
    estado.dominio_probable = "ARRANQUE"
    estado.registrar_hecho("sintoma_demora_arranque", "demora en arrancar", categoria="sintoma", estado=FactState.CONFIRMADO)

    preguntas_prohibidas = [
        (QuestionIntent.COMPONENTE_REVISADO, "¿Has podido revisar si los bujes de trapecios o las rótulas tienen holgura visible?"),
        (QuestionIntent.PRESENCIA_RUIDO, "Al frenar, ¿la vibración se siente principalmente en el volante, en el pedal o en todo el vehículo?"),
        (QuestionIntent.COMPONENTE_REVISADO, "Al encender el botón A/C: ¿se escucha un 'clic' metálico claro en el compresor?"),
        (QuestionIntent.COMPONENTE_REVISADO, "¿Has revisado el nivel y estado del aceite ATF de la transmisión?"),
    ]

    for intent, txt in preguntas_prohibidas:
        compat, motivo = CompatibilidadPreguntas.validar(intent, txt, estado)
        assert not compat, f"Pregunta '{txt}' debió ser rechazada en caso de arranque, motivo recibido: {motivo}"
        assert "INCOMPATIBLE" in motivo or "SIN_EVIDENCIA_SUBSISTEMA" in motivo


# ==============================================================================
# SECCIÓN 19: TEST INVERSO (BUJES/RÓTULAS SÍ ES VÁLIDA CON EVIDENCIA DE SUSPENSIÓN)
# ==============================================================================
def test_seccion_19_test_inverso_suspension_valida():
    estado = ConversationState(session_id="test_inverso")
    estado.estado_operativo = EstadoOperativo.MARCHA
    estado.dominio_probable = "SUSPENSION"
    estado.registrar_hecho("sintoma_golpeteo_suspension", "golpea la suspensión delantera", categoria="sintoma", estado=FactState.CONFIRMADO)
    estado.registrar_hecho("condicion_operacion", "en pistas irregulares o baches", categoria="condicion", estado=FactState.CONFIRMADO)

    txt_bujes = "¿Has podido revisar si los bujes de trapecios o las rótulas tienen holgura visible?"
    compat, motivo = CompatibilidadPreguntas.validar(QuestionIntent.COMPONENTE_REVISADO, txt_bujes, estado)
    assert compat, f"Pregunta de bujes debió ser aceptada con evidencia de suspensión, motivo: {motivo}"


# ==============================================================================
# SECCIÓN 20: CRUCE DE OTROS DOMINIOS (RECHAZO BIDIRECCIONAL)
# ==============================================================================
def test_seccion_20_cruce_otros_dominios():
    # 1. A/C no enfría -> no preguntar bujes
    estado_ac = ConversationState(session_id="test_ac")
    estado_ac.dominio_probable = "CLIMATIZACION"
    estado_ac.registrar_hecho("sintoma_climatizacion", "aire acondicionado no enfría", categoria="sintoma", estado=FactState.CONFIRMADO)
    c, m = CompatibilidadPreguntas.validar(
        QuestionIntent.COMPONENTE_REVISADO,
        "¿Has podido revisar si los bujes de trapecios o las rótulas tienen holgura visible?",
        estado_ac,
    )
    assert not c

    # 2. Fuga refrigerante -> no preguntar embrague/caja
    estado_ref = ConversationState(session_id="test_ref")
    estado_ref.dominio_probable = "MARCHA_MOTOR"
    estado_ref.registrar_hecho("sintoma_fuga_refrigerante", "fuga de refrigerante", categoria="sintoma", estado=FactState.CONFIRMADO)
    c, m = CompatibilidadPreguntas.validar(
        QuestionIntent.COMPONENTE_REVISADO,
        "¿Has revisado el nivel y estado del aceite ATF de la transmisión o si patina el embrague?",
        estado_ref,
    )
    assert not c

    # 3. Vibración al frenar -> no preguntar compresor A/C
    estado_fr = ConversationState(session_id="test_frenos")
    estado_fr.estado_operativo = EstadoOperativo.FRENADO
    estado_fr.dominio_probable = "FRENOS"
    estado_fr.registrar_hecho("sintoma_frenos", "vibración al frenar", categoria="sintoma", estado=FactState.CONFIRMADO)
    c, m = CompatibilidadPreguntas.validar(
        QuestionIntent.COMPONENTE_REVISADO,
        "Al encender el botón A/C: ¿se escucha un 'clic' metálico claro en el compresor?",
        estado_fr,
    )
    assert not c

    # 4. Arranque -> no preguntar suspensión
    estado_arr = ConversationState(session_id="test_arranque")
    estado_arr.estado_operativo = EstadoOperativo.ARRANQUE
    estado_arr.dominio_probable = "ARRANQUE"
    estado_arr.registrar_hecho("sintoma_demora_arranque", "demora en arrancar", categoria="sintoma", estado=FactState.CONFIRMADO)
    c, m = CompatibilidadPreguntas.validar(
        QuestionIntent.COMPONENTE_REVISADO,
        "¿Has podido revisar si los bujes de trapecios o las rótulas tienen holgura visible?",
        estado_arr,
    )
    assert not c


# ==============================================================================
# SECCIÓN 21: AUDITORÍA DE CONTAMINACIÓN DE ESTADO (SESIÓN LIMPIA VS CONTAMINADA)
# ==============================================================================
def test_seccion_21_aislamiento_sesion_limpia_vs_previa(gestor_diag, orquestador):
    async def _run():
        msg_arranque = (
            "Hola, tengo un vehículo en el taller. El cliente comenta que demora bastante en encender por las mañanas. "
            "Una vez que logra encender, el motor funciona normal y no se prende ninguna luz de advertencia. "
            "Todavía no he revisado batería, arranque ni sistema de combustible. ¿Qué debería revisar primero?"
        )

        # Caso 1: Sesión completamente limpia
        res_limpia = await orquestador.procesar_mensaje(
            session_id="test_sesion_pura_limpia",
            texto_usuario=msg_arranque,
            gestor_diagnostico=gestor_diag,
        )
        assert res_limpia["estado"].dominio_probable == "ARRANQUE"
        assert "bujes" not in res_limpia["respuesta_texto"].lower()

        # Caso 2: Sesión con suspensión previa
        sess_contaminada = "test_sesion_con_suspension_previa"
        await orquestador.procesar_mensaje(
            session_id=sess_contaminada,
            texto_usuario="Siento golpeteo al pasar por baches y pistas irregulares en la suspensión.",
            gestor_diagnostico=gestor_diag,
        )
        res_aislada = await orquestador.procesar_mensaje(
            session_id=sess_contaminada,
            texto_usuario=msg_arranque,
            gestor_diagnostico=gestor_diag,
        )
        assert res_aislada["estado"].dominio_probable == "ARRANQUE"
        assert "bujes" not in res_aislada["respuesta_texto"].lower()

    asyncio.run(_run())
