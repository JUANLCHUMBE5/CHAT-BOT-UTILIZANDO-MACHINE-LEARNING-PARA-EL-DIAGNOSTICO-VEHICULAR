"""Pruebas End-to-End (E2E) obligatorias Fase 11.3: Conversaciones completas de taller."""

from __future__ import annotations

import pytest

from src.application.services import GestorDiagnostico
from src.core.conversacion.models import DtcStatus, EstadoOperativo
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
# E2E-01 — COMBUSTIBLE
# =============================================================================
@pytest.mark.anyio
async def test_e2e_01_combustible(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    Mecánico: "El cliente indica que el carro tiembla al acelerar, especialmente en subida."
    CarBot: orienta diagnóstico / pregunta.
    Mecánico: "Sí tengo manómetro. ¿Qué reviso?"
    CarBot: consume afirmación y solicita medición.
    Mecánico: "Me marca 52 PSI."
    CarBot: conserva 52 PSI y avanza.
    PROHIBIDO: convertir a 52 V.
    """
    session_id = "e2e_01_combustible_session"

    # Turno 1: Reporte del síntoma por el mecánico
    r1 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="El cliente indica que el carro tiembla al acelerar, especialmente en subida.",
        gestor_diagnostico=gestor_real,
    )
    assert r1["respuesta_texto"] != ""

    # Turno 2: Confirmación afirmativa con pregunta
    r2 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="Sí tengo manómetro. ¿Qué reviso?",
        gestor_diagnostico=gestor_real,
    )
    txt_r2 = r2["respuesta_texto"].lower()
    assert "cuentas con manómetro" not in txt_r2
    assert "tienes manómetro" not in txt_r2
    assert any(k in txt_r2 for k in ("psi", "presión", "riel", "manómetro", "conectar"))

    # Turno 3: Registro de la medición
    r3 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="Me marca 52 PSI.",
        gestor_diagnostico=gestor_real,
    )
    txt_r3 = r3["respuesta_texto"]

    # INVARIANTE: 52 PSI conservado, 0 conversiones a V
    assert "52.0 V" not in txt_r3
    assert "52 V" not in txt_r3
    assert "52" in txt_r3 and "psi" in txt_r3.lower()

    estado_final = r3["estado"]
    assert "presion_combustible" in estado_final.measurements
    assert estado_final.measurements["presion_combustible"]["unidad"] == "PSI"
    assert estado_final.measurements["presion_combustible"]["valor"] == 52.0


# =============================================================================
# E2E-02 — A/C
# =============================================================================
@pytest.mark.anyio
async def test_e2e_02_aire_acondicionado(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    Mecánico: "El cliente indica que el A/C expulsa aire pero no enfría. En movimiento enfría un poco más."
    CarBot: pregunta comprobación.
    Mecánico: "El compresor sí acopla y las RPM bajan un poco."
    CarBot: registra resultado y avanza sin repetir la misma pregunta.
    PROHIBIDO: volver a preguntar si acopla.
    """
    session_id = "e2e_02_ac_session"

    # Turno 1
    r1 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="El cliente indica que el A/C expulsa aire pero no enfría. En movimiento enfría un poco más.",
        gestor_diagnostico=gestor_real,
    )
    assert r1["respuesta_texto"] != ""

    # Turno 2: Mecánico reporta acople
    r2 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="El compresor sí acopla y las RPM bajan un poco.",
        gestor_diagnostico=gestor_real,
    )
    txt_r2 = r2["respuesta_texto"].lower()

    # PROHIBIDO: volver a preguntar si acopla
    assert "¿se escucha un 'clic' metálico claro en el compresor" not in txt_r2
    assert "electroventilador" in txt_r2 or "ventilador" in txt_r2 or "tubería" in txt_r2 or "tuberia" in txt_r2 or "gas" in txt_r2 or "presión" in txt_r2

    estado_final = r2["estado"]
    assert estado_final.ya_comprobado_o_respondido("acople_compresor") is True
    assert estado_final.completed_tests.get("acople_compresor") == "SI"


# =============================================================================
# E2E-03 — ARRANQUE
# =============================================================================
@pytest.mark.anyio
async def test_e2e_03_dificultad_arranque(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    Mecánico: "El cliente dice que demora en arrancar por las mañanas. No he revisado la batería y no tengo escáner."
    CarBot: mantiene contexto ARRANQUE.
    PROHIBIDO: preguntas de freno / A-C / aceleración sin relación.
    """
    session_id = "e2e_03_arranque_session"

    r1 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="El cliente dice que demora en arrancar por las mañanas. No he revisado la batería y no tengo escáner.",
        gestor_diagnostico=gestor_real,
    )
    txt_r1 = r1["respuesta_texto"].lower()

    # Contexto ARRANQUE preservado
    assert any(term in txt_r1 for term in ("arrancar", "arranque", "gira", "pesado", "batería", "luces"))
    assert "al acelerar con fuerza en carretera" not in txt_r1
    assert "al pisar el pedal de freno" not in txt_r1
    assert "botón a/c" not in txt_r1

    estado_final = r1["estado"]
    assert estado_final.estado_operativo == EstadoOperativo.ARRANQUE
    assert estado_final.dtc_status in (DtcStatus.DTC_DESCONOCIDO, DtcStatus.SIN_DTC)


# =============================================================================
# E2E-04 — CAMBIO DE CASO
# =============================================================================
@pytest.mark.anyio
async def test_e2e_04_cambio_de_caso(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    Caso A: A/C no enfría.
    Cerrar / cambiar caso.
    Caso B: "El cliente dejó el carro porque tiene fuga de líquido adelante y está subiendo la temperatura."
    PASS: Caso B no contiene síntomas, pruebas, preguntas ni hipótesis residuales de A/C.
    """
    session_id = "e2e_04_cambio_caso_session"

    # Caso A: A/C
    r1 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="El cliente indica que el A/C no enfría nada y sale aire tibio.",
        gestor_diagnostico=gestor_real,
    )
    assert "aire acondicionado" in r1["respuesta_texto"].lower() or "climatización" in r1["respuesta_texto"].lower() or "a/c" in r1["respuesta_texto"].lower()

    # Caso B: Fuga de refrigerante y temperatura
    r2 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="El cliente dejó su vehículo porque tiene fuga de líquido en la parte delantera y está subiendo la temperatura del motor.",
        gestor_diagnostico=gestor_real,
    )
    txt_r2 = r2["respuesta_texto"].lower()

    # CERO contaminación de A/C
    assert "compresor" not in txt_r2
    assert "r134a" not in txt_r2
    assert "botón a/c" not in txt_r2
    assert any(term in txt_r2 for term in ("refrigerante", "radiador", "temperatura", "fuga", "manguera", "termostato"))


# =============================================================================
# E2E-05 — CORRECCIÓN
# =============================================================================
@pytest.mark.anyio
async def test_e2e_05_correccion_usuario(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    CarBot interpreta o formula una pregunta incompatible.
    Mecánico: "No, eso no ocurre. El problema realmente es que demora en arrancar por las mañanas."
    PASS: CarBot corrige el estado y continúa desde arranque.
    """
    session_id = "e2e_05_correccion_session"

    # Turno 1: Consulta inicial que podría ser ambigua
    await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="El vehículo presenta un comportamiento extraño al encender el clima.",
        gestor_diagnostico=gestor_real,
    )

    # Turno 2: Corrección directa del mecánico
    r2 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="No, eso no ocurre. El problema realmente es que demora en arrancar por las mañanas.",
        gestor_diagnostico=gestor_real,
    )

    estado_actual = r2["estado"]
    assert estado_actual.estado_operativo == EstadoOperativo.ARRANQUE
    assert estado_actual.last_user_correction is not None
    txt_r2 = r2["respuesta_texto"].lower()
    assert any(term in txt_r2 for term in ("arrancar", "arranque", "gira", "pesado", "batería", "motor"))
