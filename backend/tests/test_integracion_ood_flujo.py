import asyncio

import pytest

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.fixture(scope="module")
def gestor_real():
    return GestorDiagnostico()


def test_flujo_orquestador_ood_airbag(gestor_real):
    async def _test():
        repo = InMemoryConversationRepository()
        orq = OrquestadorConversacion(repositorio=repo)

        # 1. Turno con síntoma fuera de catálogo (Airbag)
        res = await orq.procesar_turno(
            session_id="session_test_ood_1",
            texto_usuario="Testigo del airbag encendido tras desmontar el volante, posible cinta reloj rota",
            gestor_diagnostico=gestor_real,
        )
        assert res["status"] == "abstencion_ood"
        assert res["decision"] == "ABSTENCION_OOD"
        assert "Airbag" in res["respuesta_texto"]
        assert res["confianza_ml"] == 0.0
        assert len(res["top3_actual"]) == 0

    asyncio.run(_test())


def test_flujo_orquestador_ood_glp(gestor_real):
    async def _test():
        repo = InMemoryConversationRepository()
        orq = OrquestadorConversacion(repositorio=repo)

        res = await orq.procesar_turno(
            session_id="session_test_ood_2",
            texto_usuario="El conmutador de gas pita seguido y se regresa solo a gasolina aunque el tanque de GLP está lleno",
            gestor_diagnostico=gestor_real,
        )
        assert res["status"] == "abstencion_ood"
        assert res["decision"] == "ABSTENCION_OOD"
        assert "GLP/GNV" in res["respuesta_texto"]
        assert res["confianza_ml"] == 0.0

    asyncio.run(_test())


def test_flujo_orquestador_transicion_ood_a_indomain(gestor_real):
    async def _test():
        repo = InMemoryConversationRepository()
        orq = OrquestadorConversacion(repositorio=repo)

        # Turno 1: OOD
        res1 = await orq.procesar_turno(
            session_id="session_test_ood_3",
            texto_usuario="El timón eléctrico EPS está durísimo y parpadea el testigo EPS",
            gestor_diagnostico=gestor_real,
        )
        assert res1["decision"] == "ABSTENCION_OOD"
        assert res1["confianza_ml"] == 0.0

        # Turno 2: Usuario aclara que también falla el motor in-domain (Bujías)
        res2 = await orq.procesar_turno(
            session_id="session_test_ood_3",
            texto_usuario="Bueno, pero aparte el motor tiembla en mínimo y se chupa al acelerar",
            gestor_diagnostico=gestor_real,
        )
        # El flujo debe diagnosticar o repreguntar in-domain, NO abstenerse ciegamente de nuevo
        assert res2["decision"] in ("DIAGNOSTICAR", "PREGUNTAR")
        assert res2["status"] == "completado"

    asyncio.run(_test())
