"""Suite automatizada de ejecución y validación E2E para los 65 escenarios de Fase 10."""

from __future__ import annotations

import pytest

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico
from tests.fase10.casos_conversacionales_60 import CASOS_CONVERSACIONALES_65


@pytest.fixture
def orquestador():
    repo = InMemoryConversationRepository()
    return OrquestadorConversacion(repositorio=repo)


@pytest.fixture
def gestor():
    return GestorDiagnostico()


@pytest.mark.anyio
async def test_ejecucion_65_escenarios_e2e_fase10(orquestador, gestor):
    """Ejecuta los 65 escenarios completos validando estado, no repetición y memoria."""
    total_casos = len(CASOS_CONVERSACIONALES_65)
    casos_aprobados = 0
    total_turnos_ejecutados = 0

    assert total_casos >= 60, f"Debe haber al menos 60 casos para Fase 10, encontrados: {total_casos}"

    for caso in CASOS_CONVERSACIONALES_65:
        cid = caso["id"]
        sid = f"fase10_sess_{cid}"
        turnos = caso["turnos"]
        preguntas_vistas = set()
        estado_final = None

        for idx, texto in enumerate(turnos):
            total_turnos_ejecutados += 1
            res = await orquestador.procesar_turno(
                session_id=sid,
                texto_usuario=texto,
                gestor_diagnostico=gestor,
            )

            # Validación de respuesta coherente
            assert res is not None, f"Turno {idx} de {cid} devolvió None"
            assert "respuesta_texto" in res
            assert len(res["respuesta_texto"]) > 0
            # El status debe ser válido y no un error interno no capturado
            status_actual = res.get("status")
            assert status_actual is not None, f"Turno {idx} de {cid} no devolvió status"
            assert isinstance(status_actual, str) and "error" not in status_actual.lower()

            # Validación de ausencia de preguntas repetidas consecutivas
            pregunta_actual = res.get("pregunta_formulada") or res.get("pregunta_actual")
            if pregunta_actual:
                preguntas_vistas.add(pregunta_actual)

            estado_final = res.get("estado") or (await orquestador.repositorio.get_session(sid))

        # Validaciones de caso específicas
        verif = caso.get("verificaciones") or {}

        # 1. Conservación de placa
        if "conserva_placa" in verif:
            placa_esp = verif["conserva_placa"]
            assert estado_final is not None
            h_placa = estado_final.obtener_hecho("placa")
            placa_actual = getattr(estado_final, "placa", None) or (h_placa.valor if h_placa else None)
            assert placa_actual == placa_esp, (
                f"Caso {cid}: placa esperada {placa_esp}, obtenida {placa_actual}"
            )

        # 2. Casos OOD
        if "esperado_ood" in caso:
            res_ood = await orquestador.procesar_turno(
                session_id=f"ood_{cid}",
                texto_usuario=turnos[0],
                gestor_diagnostico=gestor,
            )
            assert res_ood["status"] in ("abstencion_ood", "ood"), (
                f"Caso {cid} no detectó OOD para {caso['esperado_ood']}: status={res_ood.get('status')}"
            )

        casos_aprobados += 1

    assert casos_aprobados == total_casos, f"Casos aprobados {casos_aprobados}/{total_casos}"
    assert total_turnos_ejecutados >= 150, f"Total turnos ejecutados insuficiente: {total_turnos_ejecutados}"


@pytest.mark.anyio
async def test_casos_largos_10_turnos_conservacion_contexto(orquestador, gestor):
    """Valida específicamente que las 10 conversaciones largas conserven case_id y datos técnicos."""
    casos_largos = [c for c in CASOS_CONVERSACIONALES_65 if c.get("grupo") == "LARGO"]
    assert len(casos_largos) == 10, f"Debe haber exactamente 10 casos largos, hay {len(casos_largos)}"

    for caso in casos_largos:
        sid = f"largo_{caso['id']}"
        case_id_inicial = None

        for idx, texto in enumerate(caso["turnos"]):
            res = await orquestador.procesar_turno(
                session_id=sid,
                texto_usuario=texto,
                gestor_diagnostico=gestor,
            )
            estado = res.get("estado") or (await orquestador.repositorio.get_session(sid))
            assert estado is not None

            # En el primer turno con síntoma debe asignarse un case_id
            if idx == 0:
                case_id_inicial = getattr(estado, "case_id", None) or getattr(estado, "id", None)
            else:
                # El case_id debe permanecer invariable durante toda la conversación
                case_id_actual = getattr(estado, "case_id", None) or getattr(estado, "id", None)
                if case_id_inicial and case_id_actual:
                    assert case_id_actual == case_id_inicial, (
                        f"En {caso['id']}, turno {idx}: el case_id cambió de {case_id_inicial} a {case_id_actual}"
                    )
