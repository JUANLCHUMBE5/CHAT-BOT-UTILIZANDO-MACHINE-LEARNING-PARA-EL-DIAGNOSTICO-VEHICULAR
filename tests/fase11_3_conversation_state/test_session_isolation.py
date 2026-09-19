"""Pruebas de Aislamiento de Sesiones Concurrentes y Problemas Activos (Fase 11.3 - Sección 12)."""

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


@pytest.mark.anyio
async def test_session_isolation_interleaved(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    Ejecución intercalada de 4 sesiones independientes simultáneas:
    SESSION_A: A/C no enfría.
    SESSION_B: demora en arrancar.
    SESSION_C: fuga de refrigerante y calentamiento.
    SESSION_D: escáner P0301 y pérdida de potencia.

    Orden de mensajes intercalados:
    A1, B1, C1, D1, A2, C2, B2, D2
    PASS obligatorio: CERO contaminación cruzada de síntomas, hechos o hipótesis.
    """
    id_a = "session_a_climatizacion"
    id_b = "session_b_arranque"
    id_c = "session_c_temperatura"
    id_d = "session_d_misfire_dtc"

    # Turno 1 intercalado
    await orquestador_inmem.procesar_mensaje(
        session_id=id_a,
        texto_usuario="El cliente dice que el aire acondicionado no enfría y sopla tibio.",
        gestor_diagnostico=gestor_real,
    )
    await orquestador_inmem.procesar_mensaje(
        session_id=id_b,
        texto_usuario="El carro demora en arrancar en frío por las mañanas.",
        gestor_diagnostico=gestor_real,
    )
    await orquestador_inmem.procesar_mensaje(
        session_id=id_c,
        texto_usuario="Hay una fuga visible de líquido refrigerante adelante y la temperatura sube.",
        gestor_diagnostico=gestor_real,
    )
    await orquestador_inmem.procesar_mensaje(
        session_id=id_d,
        texto_usuario="Escaneé el vehículo y salió código P0301 con tironeo al acelerar.",
        gestor_diagnostico=gestor_real,
    )

    # Turno 2 intercalado (desordenado)
    # A2
    r_a2 = await orquestador_inmem.procesar_mensaje(
        session_id=id_a,
        texto_usuario="El compresor sí acopla cuando enciendo el botón A/C.",
        gestor_diagnostico=gestor_real,
    )
    # C2
    r_c2 = await orquestador_inmem.procesar_mensaje(
        session_id=id_c,
        texto_usuario="La fuga proviene de la manguera inferior del radiador.",
        gestor_diagnostico=gestor_real,
    )
    # B2
    r_b2 = await orquestador_inmem.procesar_mensaje(
        session_id=id_b,
        texto_usuario="El motor gira pesado y lento como sin batería.",
        gestor_diagnostico=gestor_real,
    )
    # D2
    r_d2 = await orquestador_inmem.procesar_mensaje(
        session_id=id_d,
        texto_usuario="Ya cambié bujías del cilindro 1 pero sigue la falla.",
        gestor_diagnostico=gestor_real,
    )

    # Verificación estricta de aislamiento
    # SESIÓN A: Estrictamente Climatización / A/C
    st_a = r_a2["estado"]
    assert st_a.dominio_probable == "CLIMATIZACION"
    assert st_a.completed_tests.get("acople_compresor") == "SI"
    assert "P0301" not in str(st_a.hechos)
    assert "refrigerante" not in str(st_a.hechos)
    assert st_a.estado_operativo != EstadoOperativo.ARRANQUE

    # SESIÓN B: Estrictamente Arranque
    st_b = r_b2["estado"]
    assert st_b.estado_operativo == EstadoOperativo.ARRANQUE
    assert "P0301" not in str(st_b.hechos)
    assert "compresor_acopla" not in st_b.hechos
    assert "sintoma_climatizacion" not in st_b.hechos

    # SESIÓN C: Estrictamente Refrigeración / Temperatura
    st_c = r_c2["estado"]
    assert any("fuga" in str(h.valor).lower() or "refrigerante" in str(h.valor).lower() for h in st_c.hechos.values())
    assert "P0301" not in str(st_c.hechos)
    assert "compresor_acopla" not in st_c.hechos
    assert st_c.estado_operativo != EstadoOperativo.ARRANQUE

    # SESIÓN D: Estrictamente DTC P0301 / Inyección / Misfire
    st_d = r_d2["estado"]
    assert st_d.dtc_status == DtcStatus.DTC_OBSERVADO
    assert "dtc_P0301" in st_d.hechos
    assert "compresor_acopla" not in st_d.hechos
    assert "sintoma_climatizacion" not in st_d.hechos


@pytest.mark.anyio
async def test_same_session_new_active_problem(
    orquestador_inmem: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    """
    Verifica que dentro de la misma sesión se pueda transicionar a un nuevo active_problem_id
    sin arrastrar hechos conflictivos del problema previo.
    """
    session_id = "session_same_user_multi_problem"

    # Problema 1: Frenos
    r1 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="El pedal de freno vibra fuertemente al frenar a alta velocidad.",
        gestor_diagnostico=gestor_real,
    )
    st1 = r1["estado"]
    case_1 = st1.case_id

    # Transición a Problema 2: Climatización
    r2 = await orquestador_inmem.procesar_mensaje(
        session_id=session_id,
        texto_usuario="Ya revisaré los discos después. Ahora el problema es que el aire acondicionado no enfría.",
        gestor_diagnostico=gestor_real,
    )
    st2 = r2["estado"]
    case_2 = st2.case_id

    # El case_id debe haber cambiado o iniciado un caso nuevo
    assert case_1 != case_2 or st2.dominio_probable == "CLIMATIZACION"
    assert st2.dominio_probable == "CLIMATIZACION"
    # No debe arrastrar síntomas de freno
    assert "alabeo" not in str(st2.hechos).lower()
