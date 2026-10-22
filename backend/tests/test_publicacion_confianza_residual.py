"""Regresiones de publicación: rechazo íntegro, procedencia y aislamiento de casos."""
import pytest

from src.core.conversacion.models import FactState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico
from src.infrastructure.rag.contrato_documental import verificar_presencia_cifra_y_trazabilidad
from src.infrastructure.rag_checks.metadata_contract import adaptar_metadata_historica


@pytest.mark.parametrize('marca', ['Universal / Multimarca', 'Toyota', ''])
def test_alias_metadata_no_inventa_modelo_ni_validacion(marca):
    original = {'id_procedimiento': 'TEST_1', 'marca': marca}
    meta = adaptar_metadata_historica(original)
    assert meta['doc_id'] == 'TEST_1'
    assert 'modelo' not in meta
    assert 'estado_validacion' not in meta
    assert original == {'id_procedimiento': 'TEST_1', 'marca': marca}
    if marca != 'Universal / Multimarca':
        assert meta.get('vehicle_scope') != 'UNIVERSAL'


def test_pagina_cifra_separa_alcance_del_documento():
    candidate = {
        'manual_oem': 'manual-sintetico-solo-pruebas.pdf', 'pagina': '2-8',
        'texto': 'Perno superior de columna (Pag. 7): 42.0 N.m.',
    }
    ok, trace, _ = verificar_presencia_cifra_y_trazabilidad(
        'Torque del perno superior de columna', candidate,
    )
    assert ok
    assert trace.pagina_cifra == '7'
    assert trace.paginas == list(range(2, 9))


@pytest.mark.anyio
async def test_reinicio_no_reutiliza_pregunta_peligro_anterior():
    repo = InMemoryConversationRepository()
    orch = OrquestadorConversacion(repo)
    gestor = GestorDiagnostico(gemini_api_key='')
    first = await orch.procesar_turno('aislar-publicacion',
        'Tengo una Hilux diésel: voy a aflojar el inyector con el motor funcionando.', gestor)
    old_case = first['case_id']
    await orch.procesar_turno('aislar-publicacion', 'nuevo caso', gestor)
    result = await orch.procesar_turno('aislar-publicacion',
        'Toyota Yaris 2014: la puerta trasera no abre con el control remoto.', gestor)
    state = result['estado']
    assert state.case_id != old_case
    assert all('aflojar' not in x.lower() for x in state.active_symptoms)
    assert 'common rail' not in result['respuesta_texto'].lower()


@pytest.mark.anyio
async def test_respuesta_tentativa_no_confirma_falla_durante_bloqueo():
    repo = InMemoryConversationRepository()
    orch = OrquestadorConversacion(repo)
    gestor = GestorDiagnostico(gemini_api_key='')
    await orch.procesar_turno('tentativa-publicacion', 'El pedal de freno se hunde hasta el fondo.', gestor)
    result = await orch.procesar_turno('tentativa-publicacion', 'puede ser', gestor)
    state = result['estado']
    assert result['decision'] == 'SEGURIDAD_CRITICA'
    assert any(f.estado == FactState.AMBIGUO for f in state.hechos.values())
    assert not result['confianza']['diagnostico_confirmado_fisicamente']
