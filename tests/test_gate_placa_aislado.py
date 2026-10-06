"""Gate del webhook real con identidad, persistencia y envío sustituidos en memoria."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.services import webhook_service as modulo


@pytest.mark.anyio
@pytest.mark.parametrize("sintoma", ["El auto recalienta", "El motor se calienta y pierde refrigerante"])
async def test_placa_sintoma_cancelar_nueva_placa_sin_bd_ni_envio(monkeypatch, sintoma):
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    gestor.conversation_repo = InMemoryConversationRepository()
    monkeypatch.setattr(modulo.settings, "groq_api_key", "")
    usuario = SimpleNamespace(
        id=uuid.uuid4(), taller_id=uuid.uuid4(), nombres="Prueba aislada",
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
    enviar = AsyncMock()
    monkeypatch.setattr(modulo.whatsapp_provider_service, "enviar", enviar)

    async def persistir_mock(**kwargs):
        dto = kwargs["dto"]
        return {"status": "completado", "respuesta": dto.respuesta_texto}, 0

    monkeypatch.setattr(modulo.DiagnosticPersister, "persistir_y_responder", persistir_mock)
    preparar = AsyncMock(wraps=modulo.TechnicalDiagnosticWorkflow.preparar)
    monkeypatch.setattr(modulo.TechnicalDiagnosticWorkflow, "preparar", preparar)
    service = modulo.WebhookService(gestor)

    async def turno(texto):
        return await service.procesar_mensaje(
            remitente="local-ficticio", meta_message_id=f"local-{uuid.uuid4()}",
            texto_cliente=texto, proveedor="api", marca_modelo="Vehiculo Generico",
        )

    inicio = await turno(sintoma)
    assert inicio["status"] == "esperando_placa"
    assert conversacion.contexto["preplate_pending_input"] == sintoma
    invalida = await turno("!")
    assert invalida["status"] == "esperando_placa"
    assert "válida" in invalida["respuesta"]
    assert preparar.await_count == 0
    valida = await turno("ABC123")
    assert valida["status"] == "completado"
    assert preparar.await_count == 1
    assert preparar.call_args.args[6] == sintoma
    assert "preplate_pending_input" not in conversacion.contexto
    assert conversacion.contexto["conversation_state"]["active_system"] == "refrigeracion"
    await turno("Cancelar")
    assert "conversation_state" not in conversacion.contexto
    assert "preplate_pending_input" not in conversacion.contexto
    assert "placa" not in conversacion.contexto
    await turno("XYZ789")
    assert conversacion.contexto["placa"] == "XYZ789"
    perfil = await turno("Toyota Yaris 2020")
    assert perfil["status"] == "esperando_sintoma"
    nuevo = await turno("El motor tiembla en ralentí")
    assert nuevo["status"] == "completado"
    assert conversacion.contexto["conversation_state"]["active_system"] == "encendido"
    # Todos los envíos y commits anteriores fueron exclusivamente AsyncMocks.
    assert enviar.await_count >= 3
    assert not session.rollback.await_count
