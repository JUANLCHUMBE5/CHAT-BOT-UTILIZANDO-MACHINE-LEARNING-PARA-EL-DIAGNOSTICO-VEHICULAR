"""Pruebas de destinatarios tradicionales y BSUID en Meta Cloud API v25."""

import pytest

from src.config import settings
from src.core.services.whatsapp_provider import WhatsAppProviderService


class _RespuestaMeta:
    status_code = 200
    content = b'{"messages":[{"id":"wamid.prueba"}]}'

    def json(self):
        return {"messages": [{"id": "wamid.prueba"}]}


@pytest.mark.anyio
async def test_meta_envia_numero_tradicional_en_campo_to(monkeypatch):
    payload_capturado = {}

    def post_simulado(*args, **kwargs):
        payload_capturado.update(kwargs["json"])
        return _RespuestaMeta()

    monkeypatch.setattr(settings, "meta_access_token", "token-prueba")
    monkeypatch.setattr(settings, "meta_phone_number_id", "phone-id-prueba")
    monkeypatch.setattr("src.core.services.whatsapp_provider.requests.post", post_simulado)

    resultado = await WhatsAppProviderService().enviar("meta", "+51955095147", "Hola")

    assert resultado.exitoso is True
    assert payload_capturado["to"] == "51955095147"
    assert "recipient" not in payload_capturado
    assert payload_capturado["recipient_type"] == "individual"


@pytest.mark.anyio
async def test_meta_envia_bsuid_en_campo_recipient(monkeypatch):
    payload_capturado = {}

    def post_simulado(*args, **kwargs):
        payload_capturado.update(kwargs["json"])
        return _RespuestaMeta()

    monkeypatch.setattr(settings, "meta_access_token", "token-prueba")
    monkeypatch.setattr(settings, "meta_phone_number_id", "phone-id-prueba")
    monkeypatch.setattr("src.core.services.whatsapp_provider.requests.post", post_simulado)

    resultado = await WhatsAppProviderService().enviar(
        "meta", "PE.1012375744961169", "Hola"
    )

    assert resultado.exitoso is True
    assert payload_capturado["recipient"] == "PE.1012375744961169"
    assert "to" not in payload_capturado
    assert payload_capturado["recipient_type"] == "individual"

