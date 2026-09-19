"""Batería de pruebas Fase 11.3: Verificación T01 a T16 del Estado Conversacional y Evidencia Técnica."""

from __future__ import annotations

import re

import pytest

from src.application.services import GestorDiagnostico
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.gestor_plan_b import GestorPlanB
from src.core.conversacion.models import (
    ConversationState,
    DtcStatus,
    EstadoOperativo,
    FactState,
    QuestionIntent,
)
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository


@pytest.fixture
def gestor_real() -> GestorDiagnostico:
    return GestorDiagnostico()


@pytest.fixture
def orquestador_inmem() -> OrquestadorConversacion:
    repo = InMemoryConversationRepository()
    return OrquestadorConversacion(repositorio=repo)


# =============================================================================
# T01 — AFFIRMATIVE + FOLLOW-UP
# =============================================================================
@pytest.mark.anyio
async def test_t01_affirmative_follow_up(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    Pregunta: "¿Cuentas con manómetro para medir la presión de combustible?"
    Respuesta: "Sí, tengo un manómetro. ¿Qué tengo que revisar?"
    PASS: Reconoce SI, registra disponibilidad y no vuelve a preguntar si tiene manómetro.
    """
    session_id = "test_t01_session"
    estado = ConversationState(session_id=session_id)
    estado.registrar_pregunta(
        intent=QuestionIntent.DISPONIBILIDAD_HERRAMIENTA,
        texto="¿Cuentas con manómetro para medir la presión de combustible?",
        opciones=["Sí", "No"],
    )
    await orquestador_inmem.repositorio.save_session(session_id, estado)

    respuesta = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="Sí, tengo un manómetro. ¿Qué tengo que revisar?",
        gestor_diagnostico=gestor_real,
    )

    estado_actual = respuesta["estado"]
    assert estado_actual.es_herramienta_disponible("manometro") is True
    # La respuesta no debe volver a preguntar si cuenta con manómetro
    txt_resp = respuesta["respuesta_texto"].lower()
    assert "cuentas con manómetro" not in txt_resp
    assert "tienes manómetro" not in txt_resp
    assert "con el manómetro conectado" in txt_resp or "psi" in txt_resp or "presión" in txt_resp


# =============================================================================
# T02 — PSI PRESERVATION
# =============================================================================
@pytest.mark.anyio
async def test_t02_psi_preservation(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    Pregunta previa: "¿Cuántos PSI marca con la llave en ON?"
    Respuesta: "Marca 52 PSI con la llave en ON y se mantiene casi igual cuando doy marcha."
    PASS: valor=52.0, unidad=PSI, contexto=presión, NUNCA voltios ni batería.
    """
    session_id = "test_t02_session"
    estado = ConversationState(session_id=session_id)
    estado.establecer_pregunta_pendiente(
        intent="MEASURE_FUEL_PRESSURE",
        expected_quantity="pressure",
        expected_units=["PSI", "bar", "kPa"],
        related_system="COMBUSTIBLE",
    )
    estado.registrar_pregunta(
        intent=QuestionIntent.MEDICION_PRESION,
        texto="Con el manómetro conectado al riel: ¿cuántos PSI marca con la llave en ON y al dar marcha?",
        opciones=[],
    )
    await orquestador_inmem.repositorio.save_session(session_id, estado)

    respuesta = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="Marca 52 PSI con la llave en ON y se mantiene casi igual cuando doy marcha.",
        gestor_diagnostico=gestor_real,
    )

    estado_actual = respuesta["estado"]
    assert "presion_combustible" in estado_actual.measurements
    med = estado_actual.measurements["presion_combustible"]
    assert med["valor"] == 52.0
    assert med["unidad"] == "PSI"
    assert med["contexto"] == "riel_inyeccion"

    # Verificación crítica: NINGUNA conversión a Voltios
    txt_resp = respuesta["respuesta_texto"]
    assert "52.0 V" not in txt_resp
    assert "52 V" not in txt_resp
    assert "52.0 psi" in txt_resp.lower() or "52 psi" in txt_resp.lower()
    assert "batería" not in txt_resp.lower() or "chispa" in txt_resp.lower()


# =============================================================================
# T03 — A/C TEST CONSUMPTION
# =============================================================================
@pytest.mark.anyio
async def test_t03_ac_test_consumption(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    Pregunta: "¿Se escucha un 'clic' metálico claro en el compresor y bajan un instante las revoluciones?"
    Respuesta: "Sí, se escucha el clic cuando enciendo el A/C y las revoluciones bajan un poquito, pero el aire sigue saliendo casi a temperatura ambiente."
    PASS: Registra resultado, completed_tests['acople_compresor'] == 'SI' y NO repite la pregunta del clic.
    """
    session_id = "test_t03_session"
    estado = ConversationState(session_id=session_id)
    estado.dominio_probable = "CLIMATIZACION"
    estado.registrar_hecho(
        "sintoma_climatizacion",
        "aire acondicionado no enfría / sale aire caliente",
        categoria="sintoma",
        estado=FactState.CONFIRMADO,
    )
    estado.registrar_pregunta(
        intent=QuestionIntent.COMPONENTE_REVISADO,
        texto="Al encender el botón A/C con motor encendido: ¿se escucha un 'clic' metálico en el compresor?",
        opciones=["Sí, acopla", "No acopla"],
    )
    await orquestador_inmem.repositorio.save_session(session_id, estado)

    respuesta = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="Sí, se escucha el clic cuando enciendo el A/C y las revoluciones bajan un poquito, pero el aire sigue saliendo casi a temperatura ambiente.",
        gestor_diagnostico=gestor_real,
    )

    estado_actual = respuesta["estado"]
    assert estado_actual.ya_comprobado_o_respondido("acople_compresor") is True
    assert estado_actual.completed_tests.get("acople_compresor") == "SI"

    # NO volver a preguntar por el clic del compresor
    txt_resp = respuesta["respuesta_texto"].lower()
    assert "¿se escucha un 'clic' metálico en el compresor" not in txt_resp
    assert "electroventilador" in txt_resp or "ventilador" in txt_resp or "tubería" in txt_resp or "tuberia" in txt_resp or "presión" in txt_resp or "acopla" in txt_resp


# =============================================================================
# T04 — DUPLICATE EVIDENCE
# =============================================================================
@pytest.mark.anyio
async def test_t04_duplicate_evidence(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    Repetir una observación ya registrada.
    PASS: no cuenta como nueva evidencia independiente, la confianza NO escala artificialmente a 100%.
    """
    session_id = "test_t04_session"
    # Turno 1: consulta inicial
    r1 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="A/C expulsa aire pero no enfría nada en carretera ni detenido.",
        gestor_diagnostico=gestor_real,
    )
    conf_t1 = r1["confianza_ml"]
    assert conf_t1 >= 0.0

    # Turno 2: responde comprobación de acople
    r2 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="El compresor sí acopla y bajan un poco las revoluciones.",
        gestor_diagnostico=gestor_real,
    )
    conf_t2 = r2["confianza_ml"]

    # Turno 3: repite la misma observación
    r3 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="El compresor sí acopla.",
        gestor_diagnostico=gestor_real,
    )
    conf_t3 = r3["confianza_ml"]

    # La repetición de la misma observación no debe inflar la confianza a 100%
    assert conf_t3 <= 0.95 or conf_t3 == conf_t2
    assert r3["confianza_ml"] < 1.0


# =============================================================================
# T05 — STARTING PROBLEM
# =============================================================================
@pytest.mark.anyio
async def test_t05_starting_problem(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    Entrada: "El cliente dice que demora en arrancar por las mañanas. No he revisado la batería y no tengo escáner."
    PASS: Pregunta pertinente a arranque (velocidad de giro, luces, clic).
    FAIL: Preguntas de ralentí / aceleración / frenado / A-C sin relación.
    """
    session_id = "test_t05_session"
    respuesta = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="El cliente dice que demora en arrancar por las mañanas. No he revisado la batería y no tengo escáner.",
        gestor_diagnostico=gestor_real,
    )

    txt_resp = respuesta["respuesta_texto"].lower()
    # Debe estar orientada a arranque
    assert any(term in txt_resp for term in ("arrancar", "arranque", "gira", "pesado", "batería", "luces"))
    # PROHIBIDO: preguntar si falla al acelerar en carretera o al pisar el freno
    assert "al acelerar con fuerza en carretera" not in txt_resp
    assert "al pisar el pedal de freno" not in txt_resp


# =============================================================================
# T06 — UNKNOWN BATTERY
# =============================================================================
def test_t06_unknown_battery() -> None:
    """
    'No he revisado la batería.'
    PASS: FactState.NO_REVISADO / DESCONOCIDO.
    FAIL: NORMAL / OK.
    """
    estado = ConversationState(session_id="test_t06")
    ExtractorHechos.extraer_y_actualizar(estado, "El auto tiembla. No he revisado la batería.")

    hecho_bat = estado.obtener_hecho("revision_bateria") or estado.obtener_hecho("revision_batería")
    assert hecho_bat is not None
    assert hecho_bat.estado == FactState.NO_REVISADO
    # No debe considerarse batería normal
    hecho_norm = estado.obtener_hecho("sistema_normal_batería") or estado.obtener_hecho("sistema_normal_bateria")
    assert hecho_norm is None


# =============================================================================
# T07 — NO SCANNER
# =============================================================================
def test_t07_no_scanner() -> None:
    """
    'No tengo escáner.'
    PASS: scanner_available=false, dtc_status=DtcStatus.DTC_DESCONOCIDO.
    FAIL: SIN_DTC.
    """
    estado = ConversationState(session_id="test_t07")
    ExtractorHechos.extraer_y_actualizar(estado, "No tengo escáner para ver códigos.")

    assert estado.es_herramienta_disponible("escaner") is False
    assert "escaner" in estado.tools_unavailable
    assert estado.dtc_status == DtcStatus.DTC_DESCONOCIDO
    assert estado.dtc_status != DtcStatus.SIN_DTC


# =============================================================================
# T08 — USER CORRECTION
# =============================================================================
@pytest.mark.anyio
async def test_t08_user_correction(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    'Ninguna de esas opciones. El problema es que demora en arrancar por las mañanas.'
    PASS: Actualiza síntoma activo a ARRANQUE y remueve síntomas contradictorios.
    """
    session_id = "test_t08_session"
    estado = ConversationState(session_id=session_id)
    estado.registrar_hecho("sintoma_climatizacion", "aire acondicionado no enfría", categoria="sintoma")
    await orquestador_inmem.repositorio.save_session(session_id, estado)

    respuesta = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="Ninguna de esas opciones. El problema en realidad es que demora en arrancar por las mañanas.",
        gestor_diagnostico=gestor_real,
    )

    estado_actual = respuesta["estado"]
    assert estado_actual.estado_operativo == EstadoOperativo.ARRANQUE
    assert estado_actual.obtener_hecho("sintoma_climatizacion") is None
    assert estado_actual.last_user_correction is not None


# =============================================================================
# T09 — NEW WORKSHOP CASE
# =============================================================================
@pytest.mark.anyio
async def test_t09_new_workshop_case(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    Caso anterior: A/C.
    Caso nuevo: 'El cliente dejó su vehículo porque presenta una fuga de líquido en la parte delantera y la temperatura está subiendo.'
    PASS: No aparecen preguntas de A/C por contaminación residual.
    """
    session_id = "test_t09_session"
    # Turno 1: A/C
    await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="El aire acondicionado no enfría, sopla aire tibio.",
        gestor_diagnostico=gestor_real,
    )

    # Turno 2: Nuevo caso de taller con fuga y calentamiento
    r2 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="El cliente dejó su vehículo porque presenta una fuga de líquido en la parte delantera y la temperatura está subiendo.",
        gestor_diagnostico=gestor_real,
    )

    txt_r2 = r2["respuesta_texto"].lower()
    assert re.search(r"(?<!turbo)compresor", txt_r2) is None
    assert "r134a" not in txt_r2
    assert any(term in txt_r2 for term in ("refrigerante", "radiador", "temperatura", "fuga", "manguera"))


# =============================================================================
# T10 — SAME VEHICLE NEW PROBLEM
# =============================================================================
@pytest.mark.anyio
async def test_t10_same_vehicle_new_problem(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    'Ya revisaré eso después. Ahora el problema es que el aire acondicionado no enfría.'
    PASS: Cambia problema activo a climatización sin arrastrar hipótesis motor irrelevantes.
    """
    session_id = "test_t10_session"
    # Turno 1: Falla de motor
    await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="El motor tironea al acelerar en subida.",
        gestor_diagnostico=gestor_real,
    )

    # Turno 2: Transición explícita a A/C
    r2 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="Ya revisaré eso después. Ahora el problema es que el aire acondicionado no enfría.",
        gestor_diagnostico=gestor_real,
    )

    estado_actual = r2["estado"]
    assert estado_actual.dominio_probable == "CLIMATIZACION"
    txt_r2 = r2["respuesta_texto"].lower()
    assert "bujía" not in txt_r2 and "bobina" not in txt_r2


# =============================================================================
# T11 — MECHANIC REPORT
# =============================================================================
def test_t11_mechanic_report() -> None:
    """
    'Ya revisé el compresor. Sí acopla.'
    PASS: Guardado como comprobación realizada.
    """
    estado = ConversationState(session_id="test_t11")
    ExtractorHechos.extraer_y_actualizar(estado, "Ya revisé el compresor. Sí acopla.")

    assert estado.ya_comprobado_o_respondido("acople_compresor") is True
    assert estado.completed_tests.get("acople_compresor") == "SI"


# =============================================================================
# T12 — NEGATIVE RESULT
# =============================================================================
def test_t12_negative_result() -> None:
    """
    'Lo revisé y no acopla.'
    PASS: Registra resultado negativo.
    """
    estado = ConversationState(session_id="test_t12")
    ExtractorHechos.extraer_y_actualizar(estado, "Lo revisé y el compresor no acopla.")

    assert estado.ya_comprobado_o_respondido("acople_compresor") is True
    assert estado.completed_tests.get("acople_compresor") == "NO"


# =============================================================================
# T13 — UNKNOWN RESULT
# =============================================================================
def test_t13_unknown_result() -> None:
    """
    'No sé si acopla.'
    PASS: UNKNOWN / DESCONOCIDO.
    """
    estado = ConversationState(session_id="test_t13")
    ExtractorHechos.extraer_y_actualizar(estado, "No sé si acopla el compresor.")

    hecho = estado.obtener_hecho("compresor_acopla")
    assert hecho is not None
    assert hecho.estado == FactState.DESCONOCIDO


# =============================================================================
# T14 — DTC
# =============================================================================
def test_t14_dtc_extraction() -> None:
    """
    'Escaneé el carro y salió P0301.'
    PASS: DTC P0301 registrado correctamente, dtc_status=DTC_OBSERVADO.
    """
    estado = ConversationState(session_id="test_t14")
    ExtractorHechos.extraer_y_actualizar(estado, "Escaneé el carro y salió P0301.")

    assert estado.dtc_status == DtcStatus.DTC_OBSERVADO
    assert estado.obtener_hecho("dtc_P0301") is not None
    assert estado.obtener_hecho("dtc_P0301").valor == "P0301"


# =============================================================================
# T15 — TOOL UNAVAILABLE
# =============================================================================
def test_t15_tool_unavailable() -> None:
    """
    'No tengo osciloscopio.'
    PASS: No vuelve a pedir inmediatamente osciloscopio; cataloga la indisponibilidad.
    """
    estado = ConversationState(session_id="test_t15")
    ExtractorHechos.extraer_y_actualizar(estado, "No tengo osciloscopio en el taller.")

    assert "osciloscopio" in estado.tools_unavailable
    assert estado.es_herramienta_disponible("osciloscopio") is False
    indisp = GestorPlanB.detectar_indisponibilidad_en_texto("No tengo osciloscopio")
    assert "osciloscopio" in indisp


# =============================================================================
# T16 — VEHICLE SPECIFICATION
# =============================================================================
@pytest.mark.anyio
async def test_t16_vehicle_specification(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    Si una prueba necesita un rango específico dependiente del vehículo:
    PASS: Recomienda comparar con la especificación del fabricante, sin inventar un rango universal.
    """
    session_id = "test_t16_session"
    estado = ConversationState(session_id=session_id)
    estado.establecer_pregunta_pendiente(
        intent="MEASURE_FUEL_PRESSURE",
        expected_quantity="pressure",
        expected_units=["PSI", "bar", "kPa"],
        related_system="COMBUSTIBLE",
    )
    estado.registrar_pregunta(
        intent=QuestionIntent.MEDICION_PRESION,
        texto="Con el manómetro conectado al riel: ¿cuántos PSI marca?",
        opciones=[],
    )
    await orquestador_inmem.repositorio.save_session(session_id, estado)

    respuesta = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="Me marca 52 PSI.",
        gestor_diagnostico=gestor_real,
    )

    txt_resp = respuesta["respuesta_texto"]
    # Debe referenciar la especificación del fabricante
    assert "especificación de servicio del fabricante" in txt_resp or "especificación del fabricante" in txt_resp
    # No debe afirmar que 45 a 55 PSI es universal para todo vehículo
    assert "debe mantener entre 45 y 55 psi" not in txt_resp.lower()
