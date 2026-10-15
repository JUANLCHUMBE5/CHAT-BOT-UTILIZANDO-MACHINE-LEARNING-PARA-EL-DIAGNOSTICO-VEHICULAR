"""Regresiones independientes de identidad, polaridad y control del caso."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.services.confirmacion_diagnostico import interpretar_respuesta_validacion_whatsapp
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState, FactState
from src.core.identidad_conversacional import (
    clave_sesion_rest,
    es_identificador_provisional,
    identificador_provisional,
)
from src.infrastructure.database.repositories.vehiculo_repository import VehiculoRepository, normalizar_placa


@pytest.mark.parametrize("texto", [
    "No probé la bobina porque no tengo herramienta.",
    "No revisé el filtro de combustible.",
    "No pude medir la presión de gasolina.",
    "Nunca cambié la bomba.",
])
def test_accion_no_realizada_no_descarta(texto):
    state = ConversationState(session_id="review")
    ExtractorHechos.extraer_y_actualizar(state, texto)
    assert not any(h.categoria == "componente_descartado" for h in state.hechos.values())
    assert not state.hipotesis_descartadas


@pytest.mark.parametrize("texto", [
    "no revisé los bornes", "no, no pude comprobarlo", "no, no medí la presión",
    "No, no tengo manómetro", "no probé con otra batería",
])
def test_limitacion_no_es_rechazo(texto):
    assert interpretar_respuesta_validacion_whatsapp(texto) is None


@pytest.mark.parametrize("texto", [
    "No generes un nuevo diagnóstico; consulta la memoria.",
    "¿Por qué propones otro caso? No cambies nada.",
    'El cliente dijo "nuevo caso", ¿qué significa?',
    "No cierres el caso; dime qué evidencia falta.",
])
def test_mencion_no_es_orden_de_cambio(texto):
    assert not ExtractorHechos.es_reinicio_solicitado(texto)


@pytest.mark.parametrize("texto", ["nuevo caso", "otro carro", "nuevo diagnóstico"])
def test_comando_explicito_sigue_funcionando(texto):
    assert ExtractorHechos.es_reinicio_solicitado(texto)


def test_sintomas_negados_no_son_positivos():
    state = ConversationState(session_id="review")
    ExtractorHechos.extraer_y_actualizar(state, "No pierde fuerza y no vibra al frenar.")
    symptoms = [h for h in state.hechos.values() if h.tipo.value == "SINTOMA"]
    assert symptoms
    assert not any(h.estado == FactState.CONFIRMADO for h in symptoms)


def test_pieza_nueva_no_es_descarte():
    state = ConversationState(session_id="review")
    ExtractorHechos.extraer_y_actualizar(state, "El filtro de combustible es nuevo, pero sigue fallando.")
    assert not any(h.categoria == "componente_descartado" for h in state.hechos.values())
    assert not state.hipotesis_descartadas


def test_inspeccion_no_implica_funcionamiento_normal():
    state = ConversationState(session_id="review")
    ExtractorHechos.extraer_y_actualizar(state, "Ya probé la bobina, pero falta interpretar el resultado.")
    assert any(h.categoria == "prueba_realizada" for h in state.hechos.values())
    assert not any(h.categoria == "componente_descartado" for h in state.hechos.values())


@pytest.mark.parametrize("valor", ["REST-API", "RESTAPI", "WAPP-01", "PROV_12345678", "SIN-PLACA"])
def test_placeholder_no_es_placa(valor):
    assert es_identificador_provisional(valor)
    with pytest.raises(ValueError):
        normalizar_placa(valor)


@pytest.mark.anyio
async def test_repositorio_no_persiste_provisional():
    session = MagicMock()
    session.flush = AsyncMock()
    repo = VehiculoRepository(session)
    for plate in (None, "RESTAPI", "PROV_12345678"):
        assert await repo.obtener_o_crear(uuid.uuid4(), uuid.uuid4(), placa_str=plate) is None
    session.add.assert_not_called()
    session.flush.assert_not_awaited()


def test_identidad_estable_y_aislada():
    a = clave_sesion_rest("taller-a", "mecanico", "sesion-cliente", None)
    assert a == clave_sesion_rest("taller-a", "mecanico", "sesion-cliente", None)
    assert a != clave_sesion_rest("taller-b", "mecanico", "sesion-cliente", None)
    assert a != clave_sesion_rest("taller-a", "otro-mecanico", "sesion-cliente", None)
    first = identificador_provisional("taller-a", a, "caso1")
    assert first == identificador_provisional("taller-a", a, "caso1")
    assert first != identificador_provisional("taller-a", a, "caso2")
    assert first != identificador_provisional("taller-b", a, "caso1")

@pytest.mark.parametrize("mensaje", ["No presenta pérdida de potencia.", "No vibra en marcha normal."])
def test_salida_del_extractor_no_reafirma_sintoma_negado(mensaje):
    state = ConversationState(session_id="negacion-final")
    hechos = ExtractorHechos.extraer_y_actualizar(state, mensaje)
    assert not any(h["categoria"] == "sintoma" and h["estado"] == "CONFIRMADO" for h in hechos)


def test_medicion_persistida_impide_declarar_ausencia_total_de_evidencia():
    from src.core.conversacion.control_aclaraciones import hay_evidencia_diagnostica
    state = ConversationState(session_id="evidencia-frenos")
    ExtractorHechos.extraer_y_actualizar(state, "Medí alabeo de disco 0.12 mm.")
    assert hay_evidencia_diagnostica(state)

@pytest.mark.anyio
async def test_cola_rest_rechaza_identidad_placeholder_antes_de_encolar():
    from fastapi import HTTPException

    from src.interfaces.api.v1.endpoints.diagnostico import analizar_sintoma_asincrono
    from src.interfaces.api.v1.schemas import ConsultaDiagnostico
    with pytest.raises(HTTPException) as error:
        await analizar_sintoma_asincrono(
            ConsultaDiagnostico(sintoma="No arranca", placa="REST-API"),
            {"taller_id": str(uuid.uuid4()), "usuario_id": str(uuid.uuid4())},
        )
    assert error.value.status_code == 400
