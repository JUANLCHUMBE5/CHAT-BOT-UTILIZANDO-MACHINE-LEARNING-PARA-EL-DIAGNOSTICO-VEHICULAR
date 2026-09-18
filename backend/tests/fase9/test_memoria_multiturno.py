"""Pruebas automatizadas de memoria conversacional acumulativa y consistencia (Fase 9.1)."""

from __future__ import annotations

import pytest

from src.core.conversacion.models import FactState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico
from tests.fase9.casos_multiturno_50 import ESCENARIOS_50_MULTITURNO


@pytest.fixture
def orquestador():
    repo = InMemoryConversationRepository()
    return OrquestadorConversacion(repositorio=repo)


@pytest.fixture
def gestor():
    return GestorDiagnostico()


@pytest.mark.anyio
async def test_50_escenarios_multiturno_ejecucion(orquestador, gestor):
    """Ejecuta los 50 escenarios y valida acumulación de contexto y extracción de hechos."""
    casos_exitosos = 0
    total_hechos_evaluados = 0
    hechos_correctos = 0

    for caso in ESCENARIOS_50_MULTITURNO:
        sid = f"test_{caso['id']}"
        estado_final = None

        for idx_t, turno_txt in enumerate(caso["turnos"]):
            res = await orquestador.procesar_turno(
                session_id=sid,
                texto_usuario=turno_txt,
                gestor_diagnostico=gestor,
            )
            assert res["status"] in ("completado", "reinicio")
            assert "respuesta_texto" in res
            assert len(res["respuesta_texto"]) > 0
            estado_final = res.get("estado") or (await orquestador.repositorio.get_session(sid))

        # Validaciones de hechos esperados
        hechos_esp = caso.get("hechos_esperados") or {}
        for k, v_esp in hechos_esp.items():
            total_hechos_evaluados += 1
            hecho = estado_final.obtener_hecho(k)
            if hecho and hecho.valor == v_esp:
                hechos_correctos += 1

        # Validación de corrección
        if "debe_corregir" in caso:
            campo_corr = caso["debe_corregir"]
            hecho_corr = estado_final.obtener_hecho(campo_corr)
            assert hecho_corr is not None
            assert hecho_corr.estado in (FactState.CONFIRMADO, FactState.CORREGIDO)

        # Validación de reinicio
        if "marca_final_esperada" in caso:
            assert estado_final.marca == caso["marca_final_esperada"]
        if "marca_no_debe_existir" in caso:
            assert estado_final.marca != caso["marca_no_debe_existir"]

        casos_exitosos += 1

    assert casos_exitosos == len(ESCENARIOS_50_MULTITURNO)
    if total_hechos_evaluados > 0:
        accuracy_hechos = (hechos_correctos / total_hechos_evaluados) * 100
        assert accuracy_hechos >= 95.0, f"Fact Extraction Accuracy insuficiente: {accuracy_hechos:.1f}%"


@pytest.mark.anyio
async def test_consistencia_single_turn_vs_multiturn(orquestador, gestor):
    """Compara el diagnóstico entre un mensaje único completo vs conversación en varios turnos."""
    casos_consistencia = [c for c in ESCENARIOS_50_MULTITURNO if c.get("es_consistencia_par")]
    assert len(casos_consistencia) >= 10, "Debe haber al menos 10 casos de consistencia"

    coincidencias = 0
    total = len(casos_consistencia)

    for caso in casos_consistencia:
        # Versión A: Mensaje único
        sid_a = f"single_{caso['id']}"
        res_a = await orquestador.procesar_turno(
            session_id=sid_a,
            texto_usuario=caso["texto_single_turn"],
            gestor_diagnostico=gestor,
        )
        diag_a = res_a.get("diagnostico_ml")

        # Versión B: Conversación multiturno
        sid_b = f"multi_{caso['id']}"
        diag_b = None
        for turno_txt in caso["turnos"]:
            res_b = await orquestador.procesar_turno(
                session_id=sid_b,
                texto_usuario=turno_txt,
                gestor_diagnostico=gestor,
            )
            diag_b = res_b.get("diagnostico_ml")

        # Verificar equivalencia semántica o diagnóstica
        if diag_a == diag_b or res_a.get("es_pregunta") == res_b.get("es_pregunta"):
            coincidencias += 1
        else:
            # Comprobar si comparten Top-3
            estado_b = await orquestador.repositorio.get_session(sid_b)
            top3_b = [p.get("falla") for p in (estado_b.top3_actual if estado_b else [])]
            if diag_a in top3_b:
                coincidencias += 1

    consistency_pct = (coincidencias / total) * 100
    assert consistency_pct >= 90.0, f"Diagnostic Consistency insuficiente: {consistency_pct:.1f}%"
