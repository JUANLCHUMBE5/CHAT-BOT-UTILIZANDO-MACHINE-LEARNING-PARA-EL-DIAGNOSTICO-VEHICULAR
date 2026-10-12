"""Pruebas de regresión automatizadas para Calidad de Preguntas, Embrague y Procedimientos RAG (PR 4).

Cubre:
- ESC-03: Jerga peruana de zapateo de embrague (falla mecánica pura sin escáner DTC).
- ESC-22: Solicitud de detalle técnico y procedimiento de comprobación RAG.
- ESC-29: Embrague patinando en pendiente (revoluciones suben sin avance y olor a quemado).
- ESC-31: Respuestas monosilábicas cortas ('no') y alias historial_respuestas.
"""

import asyncio

import pytest

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.fixture
def test_setup():
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    gestor = GestorDiagnostico()
    return repo, orquestador, gestor


def test_esc03_zapateo_embrague_falla_mecanica_pura(test_setup):
    """ESC-03: Jerga Peruana: Zapateo de Embrague (Falla Mecánica Pura sin escáner DTC)."""
    repo, orquestador, gestor = test_setup
    sesion = "test_esc03_sesion"

    async def _run():
        res = await orquestador.procesar_turno(
            sesion,
            "Maestro, el carro zapatea feo al arrancar en primera y el pedal vibra cuando lo suelto en un Kia Rio 2014",
            gestor,
        )
        est = await repo.get_session(sesion)
        resp_lower = res["respuesta_texto"].lower()

        # Debe reconocer embrague y no sugerir escaneo DTC en avería mecánica pura
        assert "dtc" not in resp_lower, "No debe sugerir código DTC en avería mecánica pura de embrague"
        assert "escaner" not in resp_lower, "No debe sugerir escáner en avería mecánica pura de embrague"
        assert (
            "embrague" in resp_lower
            or any("embrague" in h["falla"].lower() for h in (est.top3_actual or []))
        ), "Debe identificar embrague en la respuesta o en las hipótesis"

    asyncio.run(_run())


def test_esc22_solicitud_detalle_tecnico_procedimiento_rag(test_setup):
    """ESC-22: Solicitud de Detalle Técnico / Procedimiento RAG."""
    repo, orquestador, gestor = test_setup
    sesion = "test_esc22_sesion"

    async def _run():
        # Turno 1: Reporte de sobrecalentamiento
        await orquestador.procesar_turno(
            sesion,
            "El motor recalienta al poco rato en un Toyota Corolla 2012",
            gestor,
        )
        # Turno 2: Solicitud explícita de cómo revisar termostato y bomba
        res2 = await orquestador.procesar_turno(
            sesion,
            "Dame más detalles de cómo revisar el termostato y la bomba",
            gestor,
        )
        resp2_lower = res2["respuesta_texto"].lower()

        assert res2["decision"] == "DETALLE", "La decisión debe ser DETALLE ante solicitud técnica"
        assert (
            "procedimiento" in resp2_lower
            or "termostato" in resp2_lower
            or "revisar" in resp2_lower
        ), "Debe proporcionar el procedimiento técnico de comprobación"

    asyncio.run(_run())


def test_esc29_embrague_patinando_en_pendiente(test_setup):
    """ESC-29: Embrague Patinando en Pendiente (Revoluciones suben sin avance)."""
    repo, orquestador, gestor = test_setup
    sesion = "test_esc29_sesion"

    async def _run():
        res = await orquestador.procesar_turno(
            sesion,
            "En subida las revoluciones suben hasta 4500 RPM pero el carro no avanza casi nada y huele a quemado en un Toyota Yaris 2012",
            gestor,
        )
        est = await repo.get_session(sesion)
        resp_lower = res["respuesta_texto"].lower()

        assert (
            any("embrague" in h["falla"].lower() for h in (est.top3_actual or []))
            or "embrague" in resp_lower
        ), "Debe orientar el diagnóstico a embrague patinando"

    asyncio.run(_run())


def test_esc31_interpretacion_respuestas_monosilabicas(test_setup):
    """ESC-31: Interpretación de Respuestas Monosilábicas ('no')."""
    repo, orquestador, gestor = test_setup
    sesion = "test_esc31_sesion"

    async def _run():
        await orquestador.procesar_turno(
            sesion,
            "El carro no enciende en un Toyota Yaris 2015",
            gestor,
        )
        res2 = await orquestador.procesar_turno(
            sesion,
            "No",
            gestor,
        )
        est = await repo.get_session(sesion)

        # Debe registrar la respuesta en historial_respuestas y completar el ciclo
        assert len(est.historial_respuestas) >= 1
        assert res2["status"] == "completado"

    asyncio.run(_run())
