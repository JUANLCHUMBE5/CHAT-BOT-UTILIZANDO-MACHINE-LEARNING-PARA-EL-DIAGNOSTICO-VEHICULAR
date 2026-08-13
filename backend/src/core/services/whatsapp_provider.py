"""Adaptador único para entrega y descarga de medios de Meta/Twilio."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import requests

from src.config import settings


@dataclass(frozen=True)
class ResultadoEnvioWhatsApp:
    exitoso: bool
    reintentable: bool
    id_externo: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None


class WhatsAppProviderService:
    """Encapsula diferencias de autenticación y payload entre proveedores."""

    async def enviar(self, proveedor: str, destino: str, texto: str) -> ResultadoEnvioWhatsApp:
        proveedor = proveedor.lower()
        if proveedor == "meta":
            return await self._enviar_meta(destino, texto)
        if proveedor == "twilio":
            return await self._enviar_twilio(destino, texto)
        return ResultadoEnvioWhatsApp(False, False, error=f"Proveedor no soportado: {proveedor}")

    async def _enviar_meta(self, destino: str, texto: str) -> ResultadoEnvioWhatsApp:
        if not settings.meta_access_token or not settings.meta_phone_number_id:
            return ResultadoEnvioWhatsApp(False, False, error="Credenciales Meta incompletas")
        version = settings.meta_graph_api_version.strip("/")
        url = f"https://graph.facebook.com/{version}/{settings.meta_phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {settings.meta_access_token}",
            "Content-Type": "application/json",
        }
        destino_limpio = destino.replace("whatsapp:", "").replace("+", "").strip()
        es_bsuid = "." in destino_limpio and not destino_limpio.isdigit()
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "type": "text",
            "text": {"body": texto},
        }
        # Meta v25 usa ``recipient`` para Business-Scoped User IDs (BSUID).
        # Los números/wa_id tradicionales continúan utilizando ``to``.
        payload["recipient" if es_bsuid else "to"] = destino_limpio
        try:
            response = await asyncio.to_thread(
                requests.post, url, headers=headers, json=payload, timeout=10
            )
            data = response.json() if response.content else {}
            if response.status_code in (200, 201):
                mensajes = data.get("messages", [])
                externo = mensajes[0].get("id") if mensajes else None
                return ResultadoEnvioWhatsApp(True, False, externo, status_code=response.status_code)
            return ResultadoEnvioWhatsApp(
                False,
                response.status_code == 429 or response.status_code >= 500,
                error=f"Meta HTTP {response.status_code}",
                status_code=response.status_code,
            )
        except requests.RequestException as exc:
            return ResultadoEnvioWhatsApp(False, True, error=f"Meta red: {type(exc).__name__}")

    async def _enviar_twilio(self, destino: str, texto: str) -> ResultadoEnvioWhatsApp:
        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            return ResultadoEnvioWhatsApp(False, False, error="Credenciales Twilio incompletas")
        url = (
            "https://api.twilio.com/2010-04-01/Accounts/"
            f"{settings.twilio_account_sid}/Messages.json"
        )
        data = {
            "From": settings.twilio_whatsapp_from,
            "To": destino if destino.startswith("whatsapp:") else f"whatsapp:{destino}",
            "Body": texto,
        }
        try:
            response = await asyncio.to_thread(
                requests.post,
                url,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
                data=data,
                timeout=10,
            )
            body = response.json() if response.content else {}
            if response.status_code in (200, 201):
                return ResultadoEnvioWhatsApp(
                    True, False, body.get("sid"), status_code=response.status_code
                )
            return ResultadoEnvioWhatsApp(
                False,
                response.status_code == 429 or response.status_code >= 500,
                error=f"Twilio HTTP {response.status_code}",
                status_code=response.status_code,
            )
        except requests.RequestException as exc:
            return ResultadoEnvioWhatsApp(False, True, error=f"Twilio red: {type(exc).__name__}")

    async def descargar_audio(self, proveedor: str, referencia: str) -> tuple[bytes, str]:
        if not settings.audio_enabled:
            raise RuntimeError("El procesamiento de audio está deshabilitado por configuración.")
        if proveedor == "meta":
            return await self._descargar_audio_meta(referencia)
        if proveedor == "twilio":
            return await self._descargar_audio_twilio(referencia)
        raise ValueError("Proveedor de audio no soportado.")

    async def _descargar_audio_meta(self, media_id: str) -> tuple[bytes, str]:
        version = settings.meta_graph_api_version.strip("/")
        headers = {"Authorization": f"Bearer {settings.meta_access_token}"}
        metadata = await asyncio.to_thread(
            requests.get,
            f"https://graph.facebook.com/{version}/{media_id}",
            headers=headers,
            timeout=10,
        )
        metadata.raise_for_status()
        media_url = metadata.json().get("url")
        if not media_url or urlparse(media_url).scheme != "https":
            raise ValueError("Meta no devolvió una URL HTTPS de audio válida.")
        return await self._descargar_limitado(media_url, headers=headers)

    async def _descargar_audio_twilio(self, media_url: str) -> tuple[bytes, str]:
        parsed = urlparse(media_url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not (
            host.endswith(".twilio.com") or host.endswith(".twiliocdn.com") or host == "api.twilio.com"
        ):
            raise ValueError("URL de audio Twilio no autorizada.")
        auth = (settings.twilio_account_sid, settings.twilio_auth_token)
        return await self._descargar_limitado(media_url, auth=auth)

    async def _descargar_limitado(self, url: str, **kwargs) -> tuple[bytes, str]:
        def descargar() -> tuple[bytes, str]:
            with requests.get(url, stream=True, timeout=15, **kwargs) as response:
                response.raise_for_status()
                limite = settings.audio_max_bytes
                contenido = bytearray()
                for bloque in response.iter_content(chunk_size=64 * 1024):
                    contenido.extend(bloque)
                    if len(contenido) > limite:
                        raise ValueError("El audio supera el límite permitido.")
                mime = response.headers.get("content-type", "audio/ogg").split(";")[0]
                return bytes(contenido), mime

        return await asyncio.to_thread(descargar)


whatsapp_provider_service = WhatsAppProviderService()

