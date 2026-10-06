"""Regresiones aisladas de recepción y análisis de imágenes, sin Meta ni llamadas externas."""

from __future__ import annotations

import asyncio
import json

import pytest
import requests
from fastapi import BackgroundTasks
from starlette.requests import Request

from src.config import settings
from src.core.image_processor import ImageProcessor, validar_imagen
from src.core.services.whatsapp_provider import WhatsAppProviderService, _host_permitido
from src.interfaces.api.v1.endpoints import webhook

JPEG_MINIMO = b"\xff\xd8\xff\xe0contenido-de-prueba"
PNG_MINIMO = b"\x89PNG\r\n\x1a\ncontenido-de-prueba"
WEBP_MINIMO = b"RIFF\x08\x00\x00\x00WEBPcontenido"


@pytest.mark.parametrize(
    ("contenido", "mime"),
    [(JPEG_MINIMO, "image/jpeg"), (PNG_MINIMO, "image/png"), (WEBP_MINIMO, "image/webp")],
)
def test_acepta_solo_firmas_de_imagen_permitidas(contenido, mime):
    validar_imagen(contenido, mime)


def test_rechaza_mime_o_firma_no_coincidente():
    with pytest.raises(ValueError, match="JPEG, PNG o WEBP"):
        validar_imagen(b"no-es-una-imagen", "image/jpeg")
    with pytest.raises(ValueError, match="JPEG, PNG o WEBP"):
        validar_imagen(JPEG_MINIMO, "application/pdf")


def test_vision_desactivada_no_hace_llamada_externa(monkeypatch):
    monkeypatch.setattr(settings, "image_vision_enabled", False)
    monkeypatch.setattr(settings, "gemini_api_key", "clave-falsa-de-prueba")
    monkeypatch.setattr(
        "src.core.image_processor.requests.post",
        lambda *_args, **_kwargs: pytest.fail("No debe llamar a un proveedor"),
    )
    with pytest.raises(RuntimeError, match="deshabilitada"):
        ImageProcessor().interpretar_imagen(JPEG_MINIMO, "image/jpeg")


def test_gemini_vision_usa_inline_image_y_devuelve_observaciones(monkeypatch):
    monkeypatch.setattr(settings, "image_vision_enabled", True)
    monkeypatch.setattr(settings, "gemini_api_key", "clave-falsa-de-prueba")
    monkeypatch.setattr(settings, "gemini_model", "modelo-test")
    capturado = {}

    class Respuesta:
        status_code = 200

        def raise_for_status(self):
            return None

        @staticmethod
        def json():
            return {"candidates": [{"content": {"parts": [{"text": "Observaciones visibles: conector suelto."}]}}]}

    def post_mock(url, **kwargs):
        capturado["url"] = url
        capturado.update(kwargs)
        return Respuesta()

    monkeypatch.setattr("src.core.image_processor.requests.post", post_mock)
    result, proveedor = ImageProcessor().interpretar_imagen(JPEG_MINIMO, "image/jpeg")

    assert result == "Observaciones visibles: conector suelto."
    assert proveedor == "gemini"
    assert capturado["url"].endswith("/models/modelo-test:generateContent")
    assert capturado["json"]["contents"][0]["parts"][1]["inline_data"]["mime_type"] == "image/jpeg"
    assert "No concluyas una avería interna" in capturado["json"]["contents"][0]["parts"][0]["text"]


def test_gemini_saturado_activa_groq_vision_sin_llamada_real(monkeypatch):
    monkeypatch.setattr(settings, "image_vision_enabled", True)
    monkeypatch.setattr(settings, "gemini_api_key", "gemini-key-falsa")
    monkeypatch.setattr(settings, "gemini_model", "modelo-test")
    monkeypatch.setattr(settings, "groq_api_key", "groq-key-falsa")
    monkeypatch.setattr(settings, "groq_vision_enabled", True)
    monkeypatch.setattr(settings, "groq_vision_model", "qwen/qwen3.6-27b")
    llamadas = []

    class Respuesta:
        def __init__(self, status_code, payload, headers=None):
            self.status_code = status_code
            self._payload = payload
            self.headers = headers or {}

        def json(self):
            return self._payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"HTTP {self.status_code}")

    def post_mock(url, **kwargs):
        llamadas.append((url, kwargs))
        if "generativelanguage.googleapis.com" in url:
            return Respuesta(429, {"error": {}}, {"Retry-After": "20"})
        return Respuesta(200, {"choices": [{"message": {"content": "Se observa un conector desconectado."}}]})

    monkeypatch.setattr("src.core.image_processor.requests.post", post_mock)
    result, proveedor = ImageProcessor().interpretar_imagen(JPEG_MINIMO, "image/jpeg")

    assert result == "Se observa un conector desconectado."
    assert proveedor == "groq"
    assert len(llamadas) == 2
    assert llamadas[1][1]["json"]["model"] == "qwen/qwen3.6-27b"
    contenido = llamadas[1][1]["json"]["messages"][0]["content"]
    assert contenido[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_groq_vision_puede_usarse_si_gemini_esta_en_cooldown(monkeypatch):
    monkeypatch.setattr(settings, "image_vision_enabled", True)
    monkeypatch.setattr(settings, "gemini_api_key", "gemini-key-falsa")
    monkeypatch.setattr(settings, "groq_api_key", "groq-key-falsa")
    monkeypatch.setattr(settings, "groq_vision_enabled", True)
    llamadas = []

    class Respuesta:
        status_code = 200

        @staticmethod
        def json():
            return {"choices": [{"message": {"content": "Observación visual de prueba."}}]}

    monkeypatch.setattr(
        "src.core.image_processor.requests.post",
        lambda url, **kwargs: (llamadas.append(url) or Respuesta()),
    )
    resultado, proveedor = ImageProcessor().interpretar_imagen(
        JPEG_MINIMO, "image/jpeg", permitir_gemini=False
    )

    assert resultado == "Observación visual de prueba."
    assert proveedor == "groq"
    assert llamadas == ["https://api.groq.com/openai/v1/chat/completions"]


def test_media_host_allowlist_rechaza_hosts_arbitrarios():
    assert _host_permitido("graph.facebook.com", meta=True)
    assert _host_permitido("lookaside.fbsbx.com", meta=True)
    assert _host_permitido("cdn.example.fbcdn.net", meta=True)
    assert not _host_permitido("evil.example", meta=True)
    assert not _host_permitido("api.twilio.com.evil.example", twilio=True)


def test_descarga_imagen_rechaza_url_twilion_no_autorizada(monkeypatch):
    monkeypatch.setattr(settings, "image_vision_enabled", True)
    with pytest.raises(ValueError, match="no autorizada"):
        asyncio.run(WhatsAppProviderService()._descargar_imagen_twilio("https://evil.example/image.jpg"))


@pytest.mark.anyio
async def test_webhook_meta_encola_imagen_con_id_y_caption_sin_descartarla(monkeypatch):
    raw_body = json.dumps({
        "entry": [{"changes": [{"value": {
            "metadata": {"phone_number_id": "phone-test"},
            "contacts": [{"wa_id": "51900000000", "profile": {"name": "Mecánico test"}}],
            "messages": [{
                "id": "wamid.test-image",
                "from": "51900000000",
                "type": "image",
                "image": {"id": "media-test-1", "mime_type": "image/jpeg", "caption": "Conector sulfatado"},
            }],
        }}]}],
    }).encode()

    async def receive():
        return {"type": "http.request", "body": raw_body, "more_body": False}

    request = Request({
        "type": "http", "method": "POST", "path": "/meta", "raw_path": b"/meta",
        "query_string": b"", "headers": [(b"content-type", b"application/json")],
        "scheme": "https", "server": ("localhost", 443), "client": ("localhost", 1),
    }, receive)
    captured = {}

    monkeypatch.setattr(webhook, "verificar_firma_meta", lambda *_args: True)
    monkeypatch.setattr(webhook, "database_configurada", lambda: True)

    async def enqueue(payload, provider, message_id):
        captured.update(payload=payload, provider=provider, message_id=message_id)
        return "job-test", True

    monkeypatch.setattr(webhook, "_encolar_mensaje_whatsapp", enqueue)
    response = await webhook.recibir_mensaje_meta(request, BackgroundTasks(), "sha256=test")

    assert response.status_code == 200
    assert captured["payload"]["tipo_mensaje"] == "image"
    assert captured["payload"]["image_id"] == "media-test-1"
    assert captured["payload"]["texto_cliente"] == "Conector sulfatado"
    assert captured["message_id"] == "wamid.test-image"
