"""Pruebas para los 20 escenarios de información escasa, ambigua y 'no sé' (Adenda 9.1)."""

from __future__ import annotations

import pytest

from src.core.conversacion.models import EvidenceLevel, FactState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico
from tests.fase9.casos_adenda_escasa_20 import ESCENARIOS_20_ADENDA_ESCASOS


@pytest.fixture
def orquestador():
    repo = InMemoryConversationRepository()
    return OrquestadorConversacion(repositorio=repo)


@pytest.fixture
def gestor():
    return GestorDiagnostico()


@pytest.mark.anyio
async def test_20_escenarios_adenda_informacion_escasa(orquestador, gestor):
    """Ejecuta los 20 escenarios de la Adenda 9.1 y valida comportamiento robusto."""
    casos_exitosos = 0

    for caso in ESCENARIOS_20_ADENDA_ESCASOS:
        sid = f"adenda_{caso['id']}"
        res_final = None

        for turno_txt in caso["turnos"]:
            res_final = await orquestador.procesar_turno(
                session_id=sid,
                texto_usuario=turno_txt,
                gestor_diagnostico=gestor,
            )

        estado = await orquestador.repositorio.get_session(sid)
        assert estado is not None

        # 1. Validación de mensaje escaso: debe pedir aclaración
        if caso.get("espera_pregunta"):
            assert res_final.get("es_pregunta") is True
            assert estado.conversation_evidence_level == EvidenceLevel.BAJA

        # 2. Validación de nivel de evidencia
        if "evidence_level_esperado" in caso:
            assert estado.conversation_evidence_level.value == caso["evidence_level_esperado"]

        # 3. Validación de síntomas esperados
        if "sintoma_esperado" in caso:
            sintomas = [h.valor for h in estado.hechos.values() if h.categoria == "sintoma"]
            assert any(caso["sintoma_esperado"] in s for s in sintomas)

        # 4. Validación de 'no sé' y hechos desconocidos
        if "debe_registrar_desconocido" in caso:
            campo = caso["debe_registrar_desconocido"]
            hecho = estado.obtener_hecho(campo)
            assert hecho is not None
            assert hecho.estado == FactState.DESCONOCIDO

        # 5. Validación de no repetición de preguntas
        if caso.get("no_debe_repetir"):
            intents = [p.get("intent") for p in estado.preguntas_realizadas]
            assert len(intents) == len(set(intents)), "No deben existir preguntas con misma intención repetida"

        # 6. Validación de estados ambiguos
        if caso.get("debe_tener_estado_ambiguo"):
            estados_hechos = [h.estado for h in estado.hechos.values()]
            assert FactState.AMBIGUO in estados_hechos, "Debe registrarse al menos un hecho en estado AMBIGUO"

        # 7. Validación de límite de repreguntas y escape de loop
        if caso.get("debe_alcanzar_limite_escape"):
            assert estado.turnos_repregunta >= estado.max_repreguntas
            assert res_final.get("decision") in ("DIFERENCIAL", "DIAGNOSTICAR")
            assert "Diagnóstico diferencial" in res_final.get("respuesta_texto", "") or "Límite" in res_final.get("motivo_decision", "")

        # 8. Validación de DTC observado vs sin DTC
        if "dtc_status_esperado" in caso:
            assert estado.dtc_status.value == caso["dtc_status_esperado"]

        casos_exitosos += 1

    assert casos_exitosos == len(ESCENARIOS_20_ADENDA_ESCASOS)
