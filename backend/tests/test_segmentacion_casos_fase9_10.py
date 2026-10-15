"""Pruebas unitarias e integración de la Fase 9.10: Segmentación automática y aislamiento de contexto."""

from __future__ import annotations

import pytest

from src.application.services import GestorDiagnostico
from src.core.conversacion.formateador_compacto import FormateadorCompacto
from src.core.conversacion.models import (
    ConversationPhase,
    ConversationState,
    EstadoOperativo,
    FactState,
    QuestionIntent,
)
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.conversacion.segmentador_casos import (
    DecisionTransicion,
    SegmentadorCasos,
)
from src.core.version import (
    APP_VERSION,
    CODE_BUILD_ID,
    ORCHESTRATOR_VERSION,
    obtener_telemetria_proceso,
    verificar_paridad_runtime,
)


@pytest.fixture
def gestor_real() -> GestorDiagnostico:
    return GestorDiagnostico()


@pytest.fixture
def orquestador_inmem() -> OrquestadorConversacion:
    repo = InMemoryConversationRepository()
    return OrquestadorConversacion(repositorio=repo)


# =============================================================================
# 1. REPRODUCCIÓN EXACTA DEL INCIDENTE FASE 9.9
# =============================================================================
@pytest.mark.anyio
async def test_reproduccion_exacta_incidente_fase_9_9(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    Turno 1: No arranca + clic único (Batería / Solenoide).
    Turno 2 (mismo WhatsApp): Maneja y vibra al frenar a alta velocidad.
    DEBE aislar el contexto, generar nuevo case_id, inferir FRENADO,
    limpiar síntomas de arranque y diagnosticar Discos de freno alabeados.
    """
    session_id = "wapp_test_incidente_9_9"

    # Turno 1: Falla de arranque
    msg_arranque = (
        "Buenas, mi carro tiene un problema. Ayer lo dejé estacionado en la calle "
        "y cuando volví en la noche ya no quiso arrancar. Le doy a la llave y hace como "
        "un clic seco, una sola vez, y nada más. Las luces del tablero sí prenden bien, y el radio también."
    )
    res_t1 = await orquestador_inmem.procesar_turno(
        session_id=session_id,
        texto_usuario=msg_arranque,
        gestor_diagnostico=gestor_real,
    )
    estado_t1 = res_t1["estado"]
    case_id_t1 = estado_t1.case_id

    assert case_id_t1 is not None
    assert estado_t1.obtener_hecho("motor_arranca").valor == "NO"
    assert estado_t1.obtener_hecho("ruido_arranque").valor == "clic_unico"

    # Turno 2: Mensaje de frenado dentro de la misma conversación de WhatsApp
    msg_frenado = (
        "Buenas, tengo un problema con mi carro. Cuando manejo normalmente todo va bien, "
        "pero cuando freno desde una velocidad más o menos alta empiezo a sentir una vibración fuerte en el volante. "
        "A baja velocidad casi no se siente. No se prende ninguna luz en el tablero y el carro sí frena, "
        "pero la vibración me preocupa. ¿Qué podría ser?"
    )
    res_t2 = await orquestador_inmem.procesar_turno(
        session_id=session_id,
        texto_usuario=msg_frenado,
        gestor_diagnostico=gestor_real,
    )
    estado_t2 = res_t2["estado"]
    case_id_t2 = estado_t2.case_id

    # Contrato aprobado: una nueva queja no borra el caso sin consentimiento.
    assert case_id_t2 == case_id_t1
    assert res_t2["decision_transicion"] != DecisionTransicion.CAMBIO_DE_CASO.value
    assert estado_t2.obtener_hecho("motor_arranca") is not None
    assert msg_frenado in estado_t2.historial_mensajes_usuario


# =============================================================================
# 2. REGRESIONES CROSS-SYSTEM (REQUERIMIENTO 7)
# =============================================================================
def test_transicion_cross_system_frenado_a_marcha() -> None:
    estado = ConversationState(session_id="s1", case_id="c1")
    estado.estado_operativo = EstadoOperativo.FRENADO
    estado.fase = ConversationPhase.RESULTADO
    estado.registrar_hecho("sintoma_frenos", "vibración al frenar", categoria="sintoma", estado=FactState.CONFIRMADO)
    estado.top3_actual = [{"falla": "Discos de freno alabeados", "probabilidad": 0.85}]

    nuevo_texto = "Ahora el motor pierde potencia al acelerar a 80 km/h y tironea"
    res = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario=nuevo_texto,
        estado_detectado_mensaje=EstadoOperativo.MARCHA,
        seniales_mensaje={"senial_marcha": True},
        seniales_heredadas={"senial_frenado": True},
    )
    assert res.decision in (DecisionTransicion.MANTENER_CASO, DecisionTransicion.ACLARACION_REQUERIDA)
    assert res.nuevo_case_id is None
    assert estado.hechos  # La evaluación no descarta evidencia anterior.


def test_transicion_cross_system_marcha_a_arranque() -> None:
    estado = ConversationState(session_id="s2", case_id="c2")
    estado.estado_operativo = EstadoOperativo.MARCHA
    estado.fase = ConversationPhase.RESULTADO
    estado.registrar_hecho("sintoma_potencia", "pérdida de potencia", categoria="sintoma", estado=FactState.CONFIRMADO)
    estado.top3_actual = [{"falla": "Bujías en mal estado", "probabilidad": 0.80}]

    nuevo_texto = "Ayer lo dejé estacionado y hoy no quiso arrancar, da un clic seco"
    res = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario=nuevo_texto,
        estado_detectado_mensaje=EstadoOperativo.ARRANQUE,
        seniales_mensaje={"senial_arranque": True},
        seniales_heredadas={"senial_marcha": True},
    )
    assert res.decision in (DecisionTransicion.MANTENER_CASO, DecisionTransicion.ACLARACION_REQUERIDA)
    assert res.nuevo_case_id is None
    assert estado.hechos  # La evaluación no descarta evidencia anterior.


def test_transicion_cross_system_electrico_a_transmision() -> None:
    estado = ConversationState(session_id="s3", case_id="c3")
    estado.estado_operativo = EstadoOperativo.ESTACIONADO
    estado.fase = ConversationPhase.RESULTADO
    estado.registrar_hecho("sintoma_electrico", "batería descargada", categoria="sintoma", estado=FactState.CONFIRMADO)
    estado.top3_actual = [{"falla": "Batería descargada o bornes sulfatados", "probabilidad": 0.90}]

    nuevo_texto = "La caja de cambios patea fuerte al meter segunda y no entra reversa"
    res = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario=nuevo_texto,
        estado_detectado_mensaje=EstadoOperativo.DESCONOCIDO,
        seniales_mensaje={},
        seniales_heredadas={},
    )
    assert res.decision in (DecisionTransicion.MANTENER_CASO, DecisionTransicion.ACLARACION_REQUERIDA)
    assert res.nuevo_case_id is None
    assert estado.hechos  # La evaluación no descarta evidencia anterior.


def test_transicion_cross_system_motor_a_suspension() -> None:
    estado = ConversationState(session_id="s4", case_id="c4")
    estado.estado_operativo = EstadoOperativo.RALENTI
    estado.fase = ConversationPhase.RESULTADO
    estado.registrar_hecho("sintoma_temp", "sobrecalentamiento", categoria="sintoma", estado=FactState.CONFIRMADO)
    estado.top3_actual = [{"falla": "Termostato pegado", "probabilidad": 0.88}]

    nuevo_texto = "Siento un golpe seco al pasar baches o rompemuelles en la rueda derecha"
    res = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario=nuevo_texto,
        estado_detectado_mensaje=EstadoOperativo.MARCHA,
        seniales_mensaje={"senial_marcha": True},
        seniales_heredadas={},
    )
    assert res.decision in (DecisionTransicion.MANTENER_CASO, DecisionTransicion.ACLARACION_REQUERIDA)
    assert res.nuevo_case_id is None
    assert estado.hechos  # La evaluación no descarta evidencia anterior.


# =============================================================================
# 3. COEXISTENCIA DE SÍNTOMAS (NO CREA CASOS ESPURIOS)
# =============================================================================
def test_coexistencia_frenos_y_suspension() -> None:
    """Frenos y suspensión son compatibles y no deben forzar un cambio de caso."""
    estado = ConversationState(session_id="s5", case_id="c5")
    estado.estado_operativo = EstadoOperativo.MARCHA
    estado.registrar_hecho("sintoma_vib", "vibración en volante", categoria="sintoma", estado=FactState.CONFIRMADO)
    estado.top3_actual = [{"falla": "Llantas desbalanceadas", "probabilidad": 0.75}]

    nuevo_texto = "Cuando piso el pedal de freno la vibración se siente también en el pedal"
    res = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario=nuevo_texto,
        estado_detectado_mensaje=EstadoOperativo.FRENADO,
        seniales_mensaje={"senial_frenado": True},
        seniales_heredadas={"senial_marcha": True},
    )
    assert res.decision == DecisionTransicion.MANTENER_CASO
    assert "SINTOMAS_COEXISTENTES" in res.motivo


def test_coexistencia_conector_ademas() -> None:
    """Conectores como 'además' o 'también' indican síntomas del mismo vehículo."""
    estado = ConversationState(session_id="s6", case_id="c6")
    estado.estado_operativo = EstadoOperativo.MARCHA
    estado.registrar_hecho("sintoma_potencia", "pierde fuerza", categoria="sintoma", estado=FactState.CONFIRMADO)
    estado.top3_actual = [{"falla": "Bujías en mal estado", "probabilidad": 0.80}]

    nuevo_texto = "Y además cuando voy en carretera se prendió el foco de temperatura"
    res = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario=nuevo_texto,
        estado_detectado_mensaje=EstadoOperativo.MARCHA,
        seniales_mensaje={"senial_marcha": True},
        seniales_heredadas={"senial_marcha": True},
    )
    assert res.decision == DecisionTransicion.MANTENER_CASO


# =============================================================================
# 4. PREGUNTA DE ACLARACIÓN CANÓNICA ANTE AMBIGÜEDAD
# =============================================================================
def test_aclaracion_requerida_en_caso_abierto() -> None:
    """Caso no cerrado que recibe un síntoma no relacionado sin conectores."""
    estado = ConversationState(session_id="s7", case_id="c7")
    estado.estado_operativo = EstadoOperativo.FRENADO
    estado.fase = ConversationPhase.ACLARANDO
    estado.registrar_hecho("sintoma_freno", "pedal duro", categoria="sintoma", estado=FactState.CONFIRMADO)

    nuevo_texto = "El embrague patina y no entra reversa"
    res = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario=nuevo_texto,
        estado_detectado_mensaje=EstadoOperativo.DESCONOCIDO,
        seniales_mensaje={},
        seniales_heredadas={"senial_frenado": True},
    )
    assert res.decision == DecisionTransicion.ACLARACION_REQUERIDA
    assert res.pregunta_aclaracion == SegmentadorCasos.PREGUNTA_ACLARACION_CANONICA


def test_respuesta_usuario_a_pregunta_aclaracion() -> None:
    estado = ConversationState(session_id="s8", case_id="c8")
    estado.registrar_pregunta(
        intent=QuestionIntent.ACLARACION_ALCANCE,
        texto=SegmentadorCasos.PREGUNTA_ACLARACION_CANONICA,
    )
    estado.registrar_hecho("sintoma_freno", "pedal duro", categoria="sintoma", estado=FactState.CONFIRMADO)

    # Usuario confirma que es otra falla
    res_otra = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario="es una falla diferente",
        estado_detectado_mensaje=EstadoOperativo.DESCONOCIDO,
        seniales_mensaje={},
        seniales_heredadas={},
    )
    assert res_otra.decision == DecisionTransicion.CAMBIO_DE_CASO
    assert res_otra.motivo == "SOLICITUD_EXPLICITA_NUEVA_CONSULTA"

    # Usuario confirma que es el mismo vehículo
    res_mismo = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario="es el mismo carro",
        estado_detectado_mensaje=EstadoOperativo.DESCONOCIDO,
        seniales_mensaje={},
        seniales_heredadas={},
    )
    assert res_mismo.decision == DecisionTransicion.MANTENER_CASO
    assert "USUARIO_CONFIRMA_MISMO_CASO" in res_mismo.motivo


# =============================================================================
# 5. SCORES DE PRESENTACIÓN (REQUERIMIENTO 5)
# =============================================================================
def test_scores_presentacion_no_exceden_100_pct() -> None:
    """Las probabilidades RAW del modelo se conservan y los porcentajes mostrados nunca suman > 100%."""
    hipotesis_raw = [
        {"falla": "Batería descargada o bornes sulfatados", "probabilidad": 0.9766},
        {"falla": "Bujías o bobinas en mal estado", "probabilidad": 0.033},
        {"falla": "Discos de freno alabeados", "probabilidad": 0.018},
    ]
    scores_pres = FormateadorCompacto.calcular_scores_presentacion(hipotesis_raw)

    # Probabilidades RAW intactas
    assert scores_pres[0]["probabilidad_raw"] == 0.9766
    assert scores_pres[1]["probabilidad_raw"] == 0.033
    assert scores_pres[2]["probabilidad_raw"] == 0.018

    # Suma de porcentajes de presentación <= 100%
    suma_pct = sum(item["porcentaje_presentacion"] for item in scores_pres)
    assert suma_pct <= 100, f"Suma mostrada {suma_pct}% no debe exceder 100%"


# =============================================================================
# 6. VERSIONADO Y PARIDAD DE PROCESOS (REQUERIMIENTO 6)
# =============================================================================
def test_telemetria_y_paridad_runtime() -> None:
    api_telemetry = obtener_telemetria_proceso("api")
    worker_telemetry = obtener_telemetria_proceso("worker")

    assert api_telemetry["app_version"] == APP_VERSION
    assert api_telemetry["orchestrator_version"] == ORCHESTRATOR_VERSION
    assert api_telemetry["code_build_id"] == CODE_BUILD_ID
    assert api_telemetry["pid"] > 0

    # Paridad estricta entre API y Worker
    assert verificar_paridad_runtime(api_telemetry, worker_telemetry) is True
