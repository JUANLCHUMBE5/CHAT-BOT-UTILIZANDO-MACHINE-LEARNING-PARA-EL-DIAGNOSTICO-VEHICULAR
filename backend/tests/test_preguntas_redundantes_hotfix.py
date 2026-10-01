"""Pruebas obligatorias para el hotfix de preguntas redundantes sobre hechos confirmados."""

import pytest
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.filtro_preguntas_discriminantes import FiltroPreguntasDiscriminantes
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.models import (
    ConversationState,
    DtcStatus,
    EstadoOperativo,
    FactState,
    FactType,
    QuestionIntent,
)


def test_1_caso_sdf_516_evita_ralenti_y_check_engine():
    """
    TEST 1 — CASO SDF-516
    Estado acumulado:
      ralentí = CONFIRMADO
      motor caliente = CONFIRMADO
      Check Engine = CONFIRMADO
      escáner OBD-II = NO REALIZADO
    Al responder 'NO' y descartar Top-1:
      NO debe preguntar nuevamente:
      - si ocurre en ralentí
      - si Check Engine está encendido
    """
    estado = ConversationState(session_id="test_sdf516")
    estado.placa = "SDF-516"
    estado.case_id = "case_sdf516_001"

    # Turno 1: Síntoma en ralentí
    msg1 = "cuando estoy parado en el semaforo el motor tiembla bastante y las revoluciones suben y bajan, a veces parece que se quiere apagar"
    ExtractorHechos.extraer_y_actualizar(estado, msg1)

    # Turno 2: Condición de temperatura normal de trabajo (caliente)
    msg2 = "Únicamente después de que el motor alcanza su temperatura normal de trabajo."
    ExtractorHechos.extraer_y_actualizar(estado, msg2)

    # Turno 3: Check Engine encendido sin escáner conectado
    msg3 = "Sí, el testigo Check Engine está encendido, pero todavía no se ha conectado un escáner OBD-II."
    ExtractorHechos.extraer_y_actualizar(estado, msg3)

    # Verificación de hechos acumulados antes del descarte
    assert estado.estado_operativo == EstadoOperativo.RALENTI
    assert estado.obtener_hecho("condicion_operacion") is not None
    assert estado.obtener_hecho("sintoma_testigo_check_engine") is not None
    assert estado.obtener_hecho("sintoma_testigo_check_engine").estado == FactState.CONFIRMADO

    # Formular pregunta discriminante tras descarte de Top-1
    falla_descartada = "Cuerpo de aceleracion o valvula IAC sucia"
    pregunta, intent = GeneradorPreguntas.formular_pregunta_discriminante_post_descarte(estado, falla_descartada)

    preg_l = pregunta.lower()

    # NO debe preguntar si ocurre en ralentí ni en marcha
    assert "ralentí" not in preg_l and "ralenti" not in preg_l, f"Pregunta repitió ralentí: {pregunta}"
    assert "bajo aceleración en marcha" not in preg_l, f"Pregunta repitió aceleración en marcha: {pregunta}"

    # NO debe preguntar si el Check Engine o testigo está encendido
    assert "check engine" not in preg_l, f"Pregunta repitió Check Engine: {pregunta}"
    assert "testigo encendido" not in preg_l, f"Pregunta repitió testigo encendido: {pregunta}"

    # Debe preguntar por dimensión desconocida útil (sonido o humo)
    assert any(w in preg_l for w in ("sonido", "cascabeleo", "silbido", "humo")), f"Pregunta no incluye dimensión desconocida: {pregunta}"


def test_2_informacion_parcial_ralenti_confirmado_check_desconocido():
    """
    TEST 2 — INFORMACIÓN PARCIAL
    Si ralentí está confirmado pero Check Engine es desconocido:
    puede preguntar por Check Engine, pero NO por ralentí.
    """
    estado = ConversationState(session_id="test_parcial")
    estado.estado_operativo = EstadoOperativo.RALENTI
    estado.registrar_hecho(
        "condicion_operacion", "detenido en ralentí", categoria="condicion",
        estado=FactState.CONFIRMADO, tipo=FactType.CONDICION,
    )
    # Check Engine y DTC son desconocidos
    assert estado.dtc_status == DtcStatus.SIN_DTC
    assert estado.obtener_hecho("sintoma_testigo_check_engine") is None

    pregunta, intent = GeneradorPreguntas.formular_pregunta_discriminante_post_descarte(
        estado, "Cuerpo de aceleracion o valvula IAC sucia"
    )
    preg_l = pregunta.lower()

    # NO debe preguntar por ralentí
    assert "ralentí" not in preg_l and "ralenti" not in preg_l, f"Preguntó por ralentí: {pregunta}"
    assert "aceleración en marcha" not in preg_l

    # PUEDE preguntar por Check Engine / testigo
    assert "testigo" in preg_l or "check" in preg_l, f"Debió poder preguntar por testigo/Check: {pregunta}"


def test_3_contradiccion_y_correccion_explicita():
    """
    TEST 3 — CONTRADICCIÓN
    Si el usuario posteriormente corrige:
    'No, me equivoqué, también ocurre acelerando'
    debe permitir actualizar/corregir el hecho anterior.
    NO bloquear correcciones explícitas.
    """
    estado = ConversationState(session_id="test_correc")
    estado.estado_operativo = EstadoOperativo.RALENTI
    estado.registrar_hecho(
        "condicion_operacion", "detenido en ralentí", categoria="condicion",
        estado=FactState.CONFIRMADO, tipo=FactType.CONDICION,
    )

    # Usuario introduce corrección explícita
    msg_corr = "No, me equivoqué, también ocurre acelerando"
    ExtractorHechos.extraer_y_actualizar(estado, msg_corr)

    # Debe haber actualizado estado operativo y condición
    assert estado.estado_operativo == EstadoOperativo.MARCHA
    hecho_cond = estado.obtener_hecho("condicion_operacion")
    assert hecho_cond is not None
    assert "acelerar" in hecho_cond.valor.lower()
    assert estado.last_user_correction == msg_corr

    # Debe haberse preservado en hechos_historicos
    assert any(h.get("campo") == "condicion_operacion" for h in estado.hechos_historicos)


def test_4_preguntas_realizadas_dedup_semantico():
    """
    TEST 4 — PREGUNTAS REALIZADAS
    Una pregunta ya contestada no debe repetirse literalmente ni
    semánticamente si la respuesta continúa vigente.
    """
    estado = ConversationState(session_id="test_dedup")
    estado.registrar_pregunta(
        intent=QuestionIntent.CONDICION_OPERACION,
        texto="¿La falla se manifiesta con el motor en ralentí o bajo aceleración en marcha?",
    )
    estado.registrar_respuesta("detenido en ralentí")
    estado.estado_operativo = EstadoOperativo.RALENTI
    estado.registrar_hecho("condicion_operacion", "detenido en ralentí", categoria="condicion", estado=FactState.CONFIRMADO)

    # Comprobar already_known y es_pregunta_compatible
    assert GeneradorPreguntas.already_known(QuestionIntent.CONDICION_OPERACION, estado) is True
    es_comp, motivo = GeneradorPreguntas.es_pregunta_compatible(
        QuestionIntent.CONDICION_OPERACION,
        "¿La falla se manifiesta con el motor en ralentí o bajo aceleración en marcha?",
        estado,
    )
    assert es_comp is False
    assert motivo in ("PREGUNTA_REPETIDA", "INTENT_YA_RESUELTO", "HECHO_YA_CONOCIDO")


def test_5_persistencia_memoria_completa():
    """
    TEST 5 — MEMORIA
    Después de múltiples preguntas y respuestas:
      PLATE_PERSISTED = TRUE
      CASE_ID_PERSISTED = TRUE
      SYMPTOMS_PERSISTED = TRUE
      DISCARDED_HYPOTHESES_PERSISTED = TRUE
    """
    estado = ConversationState(session_id="test_memoria")
    estado.placa = "SDF-516"
    estado.case_id = "case_sdf516_full"
    estado.active_symptoms = ["el motor tiembla bastante en semáforo"]
    estado.hipotesis_descartadas = ["Cuerpo de aceleracion o valvula IAC sucia"]

    # Simular preguntas y respuestas adicionales
    estado.registrar_pregunta(QuestionIntent.PRESENCIA_RUIDO, "¿Se detecta algún sonido anómalo o humo?")
    estado.registrar_respuesta("ningún ruido")
    estado.registrar_hecho("presencia_ruido", "ningun_ruido", categoria="polaridad", estado=FactState.AUSENTE_NEGADO)

    # Exportar e importar para emular persistencia de sesión
    dict_exportado = estado.exportar_dict()
    estado_recuperado = ConversationState.from_dict(dict_exportado)

    assert estado_recuperado.placa == "SDF-516"
    assert estado_recuperado.case_id == "case_sdf516_full"
    assert "el motor tiembla bastante en semáforo" in estado_recuperado.active_symptoms
    assert "Cuerpo de aceleracion o valvula IAC sucia" in estado_recuperado.hipotesis_descartadas
    assert len(estado_recuperado.preguntas_realizadas) == 1
    assert len(estado_recuperado.respuestas_obtenidas) == 1
    assert estado_recuperado.obtener_hecho("presencia_ruido").estado == FactState.AUSENTE_NEGADO


def test_6_regresion_arranque_chispa_y_top3():
    """
    TEST 6 — REGRESIÓN
    Verificar que siga funcionando:
    - En caso de arranque con giro ya conocido: pregunta por luces o chispa
    - Prueba de chispa ya completada no se repite
    - Selección de pregunta compatible de GeneradorPreguntas
    """
    estado = ConversationState(session_id="test_arranque")
    estado.estado_operativo = EstadoOperativo.ARRANQUE
    estado.registrar_hecho("giro_motor", "gira_lento", categoria="condicion", estado=FactState.CONFIRMADO)

    # Giro ya conocido: debe preguntar por luces o caída de tensión
    pregunta, intent = GeneradorPreguntas.formular_pregunta_discriminante_post_descarte(
        estado, "Bateria descargada o bornes sulfatados"
    )
    assert intent == QuestionIntent.CAIDA_TENSION_ARRANQUE
    assert "luces del tablero" in pregunta.lower()

    # Si luces también se conoce y prueba de chispa completada
    estado.registrar_hecho("luces_se_atenuan", "NO", categoria="condicion", estado=FactState.CONFIRMADO)
    estado.registrar_prueba_completada("prueba_chispa", "CHISPA_PRESENTE")

    pregunta2, intent2 = GeneradorPreguntas.formular_pregunta_discriminante_post_descarte(
        estado, "Falla en motor de arranque o solenoide defectuoso"
    )
    # Debe pasar a bomba de combustible o inspección
    assert "chispa" not in pregunta2.lower()
    assert "bomba" in pregunta2.lower() or "inspección" in pregunta2.lower() or "inspeccion" in pregunta2.lower()


@pytest.mark.anyio
async def test_7_e2e_validation_workflow_sdf516_respuesta_discriminante():
    """
    TEST 7 — INTEGRACIÓN WORKFLOW SDF-516
    Simula el ciclo completo a través de ValidationWorkflow.manejar_flujo_validacion.
    """
    import uuid
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, MagicMock
    from src.core.services.webhook.validation_workflow import ValidationWorkflow

    # 1. Preparar estado acumulado previo
    estado = ConversationState(session_id="conv_sdf516")
    estado.placa = "SDF-516"
    estado.case_id = "case_sdf516_real"
    ExtractorHechos.extraer_y_actualizar(
        estado,
        "cuando estoy parado en el semaforo el motor tiembla bastante y las revoluciones suben y bajan, a veces parece que se quiere apagar",
    )
    ExtractorHechos.extraer_y_actualizar(
        estado,
        "Únicamente después de que el motor alcanza su temperatura normal de trabajo.",
    )
    ExtractorHechos.extraer_y_actualizar(
        estado,
        "Sí, el testigo Check Engine está encendido, pero todavía no se ha conectado un escáner OBD-II.",
    )

    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        placa="SDF-516",
        contexto={
            "conversation_state": estado.exportar_dict(),
            "estado_conversacion": estado.exportar_dict(),
            "placa": "SDF-516",
            "placa_posttest": "SDF-516",
            "case_id": "case_sdf516_real",
            "validacion_diagnostico": {
                "etapa": "esperando_confirmacion",
                "diagnostico_id": str(uuid.uuid4()),
            },
        },
    )

    diagnostico_obj = SimpleNamespace(
        id=uuid.uuid4(),
        falla_predicha="Cuerpo de aceleracion o valvula IAC sucia",
        sintoma_original="cuando estoy parado en el semaforo el motor tiembla bastante",
    )

    diag_repo_mock = MagicMock()
    diag_repo_mock.obtener_pendiente_mecanico_por_id = AsyncMock(return_value=diagnostico_obj)
    diag_repo_mock.obtener_ultimo_pendiente_mecanico = AsyncMock(return_value=diagnostico_obj)

    msg_repo_mock = MagicMock()
    msg_repo_mock.crear_mensaje = AsyncMock()

    session_mock = MagicMock()
    session_mock.commit = AsyncMock()

    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4(), nombres="Mecánico Test")

    # Mock de repositorios en ValidationWorkflow
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.core.services.webhook.validation_workflow.DiagnosticoRepository", lambda s: diag_repo_mock)
        mp.setattr("src.core.services.webhook.validation_workflow.MensajeRepository", lambda s: msg_repo_mock)

        # Paso 1: Usuario responde "NO"
        resultado_no = await ValidationWorkflow.manejar_flujo_validacion(
            session=session_mock,
            conversacion=conversacion,
            usuario=usuario,
            texto_cliente="NO",
            tipo_mensaje="text",
            meta_message_id="wamid_sdf516_01",
            proveedor="meta",
            remitente="+51999111222",
            t_inicio=0.0,
        )

        assert resultado_no is not None
        assert resultado_no["status"] == "esperando_falla_real"
        resp_texto = resultado_no["respuesta"]
        resp_l = resp_texto.lower()

        # Debe descartar la hipótesis principal
        assert "se descarta *cuerpo de aceleracion o valvula iac sucia*" in resp_l
        assert "pregunta técnica discriminante" in resp_l

        # NO debe preguntar por ralentí
        assert "ralentí" not in resp_l and "ralenti" not in resp_l
        assert "bajo aceleración en marcha" not in resp_l

        # NO debe preguntar por Check Engine
        assert "check engine" not in resp_l
        assert "testigo encendido" not in resp_l

        # Debe haber preguntado por dimensión desconocida (sonido/humo)
        assert any(w in resp_l for w in ("sonido", "cascabeleo", "silbido", "humo"))

        # Paso 2: Usuario responde aportando nueva evidencia o corrección
        resultado_evidencia = await ValidationWorkflow.manejar_flujo_validacion(
            session=session_mock,
            conversacion=conversacion,
            usuario=usuario,
            texto_cliente="No se detecta ningún sonido extraño ni humo, solo la vibración",
            tipo_mensaje="text",
            meta_message_id="wamid_sdf516_02",
            proveedor="meta",
            remitente="+51999111222",
            t_inicio=0.0,
        )

        assert resultado_evidencia is not None
        assert resultado_evidencia["status"] == "evaluar_alternativa"
        assert "No se detecta ningún sonido" in resultado_evidencia["texto_evaluar"]

