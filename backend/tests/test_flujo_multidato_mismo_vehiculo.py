"""Tests para ingesta multidato en un solo mensaje y transferencia de vehículo en nuevo caso."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import src.core.services.webhook_service as modulo
from src.application.services.confirmacion_diagnostico import (
    interpretar_seleccion_top3,
)
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


def test_extractor_hechos_detecta_mismo_vehiculo_con_placa():
    sol = ExtractorHechos.clasificar_solicitud_caso(
        "Es una falla diferente. Quiero iniciar un nuevo diagnóstico para el mismo vehículo de placa ABC1234."
    )
    assert sol is not None
    assert sol.get("preservar_vehiculo") is True


def test_extractor_interpretar_seleccion_top3_variantes():
    sel1 = interpretar_seleccion_top3("la opcion 1")
    assert sel1 is not None
    assert sel1.accion == "CONFIRMAR"
    assert sel1.orden == 1

    sel2 = interpretar_seleccion_top3("opcion 2")
    assert sel2 is not None
    assert sel2.accion == "CONFIRMAR"
    assert sel2.orden == 2

    sel3 = interpretar_seleccion_top3("fue la 3")
    assert sel3 is not None
    assert sel3.accion == "CONFIRMAR"
    assert sel3.orden == 3


@pytest.mark.anyio
async def test_flujo_un_solo_mensaje_placa_modelo_sintoma(monkeypatch):
    """Si el mecánico envía placa + modelo + síntoma en un solo mensaje, no debe repreguntar."""
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    gestor.conversation_repo = InMemoryConversationRepository()
    monkeypatch.setattr(modulo.settings, "groq_api_key", "")
    usuario = SimpleNamespace(
        id=uuid.uuid4(), taller_id=uuid.uuid4(), nombres="Mecánico Prueba",
        rol=SimpleNamespace(codigo="mecanico"),
    )
    conversacion = SimpleNamespace(id=uuid.uuid4(), contexto={})
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.begin_nested.return_value.__aenter__ = AsyncMock()
    session.begin_nested.return_value.__aexit__ = AsyncMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock()
    monkeypatch.setattr(modulo, "database_configurada", lambda: True)
    monkeypatch.setattr(modulo, "obtener_engine", lambda: None)
    monkeypatch.setattr(modulo, "AsyncSession", lambda *a, **k: context)
    mensaje_repo = MagicMock()
    mensaje_repo.existe_meta_message_id = AsyncMock(return_value=False)
    mensaje_repo.crear_mensaje = AsyncMock(return_value=SimpleNamespace(id=uuid.uuid4()))
    monkeypatch.setattr(modulo, "MensajeRepository", lambda *a: mensaje_repo)
    conv_repo = SimpleNamespace(obtener_o_crear_activa=AsyncMock(return_value=conversacion))
    monkeypatch.setattr(modulo, "ConversacionRepository", lambda *a: conv_repo)
    monkeypatch.setattr(modulo, "OperacionesRepository", lambda *a: SimpleNamespace(registrar_uso_api=AsyncMock()))
    monkeypatch.setattr(
        modulo.IdentityResolver, "resolver_o_registrar",
        AsyncMock(return_value=SimpleNamespace(status="ok", usuario=usuario)),
    )
    monkeypatch.setattr(modulo.ValidationWorkflow, "manejar_flujo_validacion", AsyncMock(return_value=None))

    async def persistir_mock(**kwargs):
        dto = kwargs["dto"]
        return {"status": "completado", "respuesta": dto.respuesta_texto}, 0

    monkeypatch.setattr(modulo.DiagnosticPersister, "persistir_y_responder", persistir_mock)
    service = modulo.WebhookService(gestor)

    # Mensaje completo con placa, modelo y síntoma
    res = await service.procesar_mensaje(
        remitente="51999111222",
        meta_message_id=f"msg-{uuid.uuid4()}",
        texto_cliente="Placa ABC-123, Toyota Yaris 2018, el motor cascabelea al acelerar en subida",
        proveedor="api",
        marca_modelo="",
    )

    # Debe diagnosticar de inmediato sin frenar en compuerta esperando placa o perfil
    assert res is not None
    assert res.get("status") != "esperando_placa"
    assert res.get("status") != "esperando_perfil_vehiculo"
    assert conversacion.contexto.get("placa") == "ABC123"
    assert "Toyota" in str(conversacion.contexto.get("perfil_vehiculo", {}))


@pytest.mark.anyio
async def test_flujo_nuevo_caso_mismo_vehiculo_conserva_placa(monkeypatch):
    """Al indicar nuevo caso para el mismo vehículo, conserva placa y no la vuelve a pedir."""
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    gestor.conversation_repo = InMemoryConversationRepository()
    monkeypatch.setattr(modulo.settings, "groq_api_key", "")
    usuario = SimpleNamespace(
        id=uuid.uuid4(), taller_id=uuid.uuid4(), nombres="Mecánico Prueba",
        rol=SimpleNamespace(codigo="mecanico"),
    )
    # Conversación activa previa con placa y perfil
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={
            "placa": "ABC123",
            "placa_posttest": "ABC123",
            "perfil_vehiculo": {"marca": "Toyota", "modelo": "Yaris", "anio": "2018"},
        },
    )
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.begin_nested.return_value.__aenter__ = AsyncMock()
    session.begin_nested.return_value.__aexit__ = AsyncMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock()
    monkeypatch.setattr(modulo, "database_configurada", lambda: True)
    monkeypatch.setattr(modulo, "obtener_engine", lambda: None)
    monkeypatch.setattr(modulo, "AsyncSession", lambda *a, **k: context)
    mensaje_repo = MagicMock()
    mensaje_repo.existe_meta_message_id = AsyncMock(return_value=False)
    mensaje_repo.crear_mensaje = AsyncMock(return_value=SimpleNamespace(id=uuid.uuid4()))
    monkeypatch.setattr(modulo, "MensajeRepository", lambda *a: mensaje_repo)
    conv_repo = SimpleNamespace(obtener_o_crear_activa=AsyncMock(return_value=conversacion))
    monkeypatch.setattr(modulo, "ConversacionRepository", lambda *a: conv_repo)
    monkeypatch.setattr(modulo, "OperacionesRepository", lambda *a: SimpleNamespace(registrar_uso_api=AsyncMock()))
    monkeypatch.setattr(
        modulo.IdentityResolver, "resolver_o_registrar",
        AsyncMock(return_value=SimpleNamespace(status="ok", usuario=usuario)),
    )
    monkeypatch.setattr(modulo.ValidationWorkflow, "manejar_flujo_validacion", AsyncMock(return_value=None))

    async def persistir_mock(**kwargs):
        dto = kwargs["dto"]
        return {"status": "completado", "respuesta": dto.respuesta_texto}, 0

    monkeypatch.setattr(modulo.DiagnosticPersister, "persistir_y_responder", persistir_mock)
    service = modulo.WebhookService(gestor)

    # Solicitar nuevo caso para el mismo vehículo
    res_nuevo = await service.procesar_mensaje(
        remitente="51999111222",
        meta_message_id=f"msg-{uuid.uuid4()}",
        texto_cliente="Es una falla diferente. Quiero iniciar un nuevo diagnóstico para el mismo vehículo de placa ABC-123",
        proveedor="api",
        marca_modelo="Toyota Yaris",
    )

    # Debe confirmar cierre del caso previo y que conserva los datos del vehículo
    assert res_nuevo is not None
    assert "Conservo los datos del vehículo" in res_nuevo["respuesta"]
    assert "ABC123" in res_nuevo["respuesta"]
    # La placa debe seguir guardada en contexto
    assert conversacion.contexto.get("placa") == "ABC123"
