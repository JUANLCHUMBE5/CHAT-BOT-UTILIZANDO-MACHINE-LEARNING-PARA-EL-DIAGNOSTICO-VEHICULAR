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
            assert res["status"] in ("completado", "reinicio", "abstencion_ood")
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
        estado_a = res_a.get("estado") or (await orquestador.repositorio.get_session(sid_a))
        top3_a = [h.falla if hasattr(h, "falla") else h.get("falla", "") for h in (estado_a.top3_actual or [])]
        falla_a = estado_a.falla_principal or (top3_a[0] if top3_a else None)

        # Versión B: Conversación multiturno
        sid_b = f"multi_{caso['id']}"
        res_b = None
        for turno_txt in caso["turnos"]:
            res_b = await orquestador.procesar_turno(
                session_id=sid_b,
                texto_usuario=turno_txt,
                gestor_diagnostico=gestor,
            )
        estado_b = res_b.get("estado") or (await orquestador.repositorio.get_session(sid_b))
        top3_b = [h.falla if hasattr(h, "falla") else h.get("falla", "") for h in (estado_b.top3_actual or [])]
        falla_b = estado_b.falla_principal or (top3_b[0] if top3_b else None)

        # Comparación de consistencia
        if falla_a and falla_b and (falla_a == falla_b or falla_a in top3_b or falla_b in top3_a):
            coincidencias += 1
        elif res_a.get("decision") == res_b.get("decision"):
            coincidencias += 1
        elif res_a.get("diagnostico_ml") == res_b.get("diagnostico_ml"):
            coincidencias += 1

    consistencia = (coincidencias / total) * 100
    assert consistencia >= 80.0, f"Consistencia single vs multi insuficiente: {consistencia:.1f}%"
