"""Adaptador único para entrega y descarga de medios de Meta/Twilio e interactividad."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin, urlparse

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

    async def enviar(
        self,
        proveedor: str,
        destino: str,
        texto: str,
        interactivo: Optional[dict] = None,
    ) -> ResultadoEnvioWhatsApp:
        proveedor = proveedor.lower()
        if not getattr(settings, "whatsapp_interactive_buttons_enabled", False):
            interactivo = None
        if proveedor == "meta":
            return await self._enviar_meta(destino, texto, interactivo=interactivo)
        if proveedor == "twilio":
            return await self._enviar_twilio(destino, texto)
        return ResultadoEnvioWhatsApp(False, False, error=f"Proveedor no soportado: {proveedor}")

    async def _enviar_meta(
        self,
        destino: str,
        texto: str,
        interactivo: Optional[dict] = None,
    ) -> ResultadoEnvioWhatsApp:
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
        dest_field = "recipient" if es_bsuid else "to"

        payload_interactivo = None
        if interactivo and isinstance(interactivo, dict):
            tipo_interactivo = interactivo.get("tipo")
            if tipo_interactivo == "button":
                botones_in = interactivo.get("botones", [])
                botones_meta = []
                for b in botones_in[:3]:
                    b_id = str(b.get("id") or "")[:256]
                    b_title = str(b.get("title") or "")[:20]
                    if b_id and b_title:
                        botones_meta.append({
                            "type": "reply",
                            "reply": {
                                "id": b_id,
                                "title": b_title,
                            },
                        })
                if botones_meta:
                    payload_interactivo = {
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        dest_field: destino_limpio,
                        "type": "interactive",
                        "interactive": {
                            "type": "button",
                            "body": {"text": (texto or "")[:1024]},
                            "action": {"buttons": botones_meta},
                        },
                    }
                    if interactivo.get("header"):
                        payload_interactivo["interactive"]["header"] = {
                            "type": "text",
                            "text": str(interactivo["header"])[:60],
                        }
                    if interactivo.get("footer"):
                        payload_interactivo["interactive"]["footer"] = {
                            "text": str(interactivo["footer"])[:60],
                        }
            elif tipo_interactivo == "list":
                filas_in = interactivo.get("filas", [])
                filas_meta = []
                for f in filas_in[:10]:
                    f_id = str(f.get("id") or "")[:200]
                    f_title = str(f.get("title") or "")[:24]
                    if f_id and f_title:
                        fila_dict = {"id": f_id, "title": f_title}
                        if f.get("description"):
                            fila_dict["description"] = str(f["description"])[:72]
                        filas_meta.append(fila_dict)
                if filas_meta:
                    payload_interactivo = {
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        dest_field: destino_limpio,
                        "type": "interactive",
                        "interactive": {
                            "type": "list",
                            "body": {"text": (texto or "")[:1024]},
                            "action": {
                                "button": str(interactivo.get("boton_menu") or "Ver opciones")[:20],
                                "sections": [
                                    {
                                        "title": str(interactivo.get("titulo_seccion") or "Opciones")[:24],
                                        "rows": filas_meta,
                                    }
                                ],
                            },
                        },
                    }

        payload_texto = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            dest_field: destino_limpio,
            "type": "text",
            "text": {"body": texto},
        }

        # Intentar enviar interactivo si se construyó; si falla con 400 (política/límite Meta), fallback inmediato a texto plano
        payload_a_enviar = payload_interactivo if payload_interactivo else payload_texto
        try:
            response = await asyncio.to_thread(
                requests.post, url, headers=headers, json=payload_a_enviar, timeout=10
            )
            data = response.json() if response.content else {}
            if response.status_code in (200, 201):
                mensajes = data.get("messages", [])
                externo = mensajes[0].get("id") if mensajes else None
                return ResultadoEnvioWhatsApp(True, False, externo, status_code=response.status_code)

            # Si falló el envío interactivo por HTTP 400, intentar inmediatamente como texto
            if payload_interactivo and response.status_code == 400:
                resp_fallback = await asyncio.to_thread(
                    requests.post, url, headers=headers, json=payload_texto, timeout=10
                )
                if resp_fallback.status_code in (200, 201):
                    fb_data = resp_fallback.json() if resp_fallback.content else {}
                    mensajes = fb_data.get("messages", [])
                    externo = mensajes[0].get("id") if mensajes else None
                    return ResultadoEnvioWhatsApp(True, False, externo, status_code=resp_fallback.status_code)

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

    async def descargar_imagen(self, proveedor: str, referencia: str) -> tuple[bytes, str]:
        """Descarga una imagen WhatsApp con allowlist de hosts y límite estricto de bytes."""
        if not settings.image_vision_enabled:
            raise RuntimeError("La interpretación de imágenes está deshabilitada por configuración.")
        if proveedor == "meta":
            return await self._descargar_imagen_meta(referencia)
        if proveedor == "twilio":
            return await self._descargar_imagen_twilio(referencia)
        raise ValueError("Proveedor de imagen no soportado.")

    async def _descargar_imagen_meta(self, media_id: str) -> tuple[bytes, str]:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", media_id or ""):
            raise ValueError("ID de imagen Meta inválido.")
        if not settings.meta_access_token:
            raise RuntimeError("La descarga de imagen Meta no está configurada.")
        version = settings.meta_graph_api_version.strip("/")
        headers = {"Authorization": f"Bearer {settings.meta_access_token}"}
        metadata = await asyncio.to_thread(
            requests.get,
            f"https://graph.facebook.com/{version}/{media_id}",
            headers=headers,
            timeout=10,
            allow_redirects=False,
        )
        metadata.raise_for_status()
        media_url = metadata.json().get("url")
        mime = metadata.json().get("mime_type", "")
        parsed = urlparse(media_url or "")
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not _host_permitido(host, meta=True):
            raise ValueError("Meta no devolvió una URL HTTPS de imagen autorizada.")
        return await self._descargar_imagen_limitado(media_url, mime, headers=headers, meta=True)

    async def _descargar_imagen_twilio(self, media_url: str) -> tuple[bytes, str]:
        parsed = urlparse(media_url or "")
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not _host_permitido(host, twilio=True):
            raise ValueError("URL de imagen Twilio no autorizada.")
        auth = (settings.twilio_account_sid, settings.twilio_auth_token)
        return await self._descargar_imagen_limitado(media_url, "", auth=auth, twilio=True)

    async def _descargar_imagen_limitado(
        self, url: str, mime_declarado: str, *, meta: bool = False, twilio: bool = False, **kwargs
    ) -> tuple[bytes, str]:
        def descargar() -> tuple[bytes, str]:
            actual = url
            opciones = dict(kwargs)
            for _ in range(4):
                parsed = urlparse(actual)
                host = (parsed.hostname or "").lower()
                if parsed.scheme != "https" or not _host_permitido(host, meta=meta, twilio=twilio):
                    raise ValueError("Redirección de imagen a un host no autorizado.")
                with requests.get(
                    actual, stream=True, timeout=15, allow_redirects=False, **opciones
                ) as response:
                    if response.is_redirect:
                        destino = urljoin(actual, response.headers.get("Location", ""))
                        host_destino = (urlparse(destino).hostname or "").lower()
                        if not _host_permitido(host_destino, meta=meta, twilio=twilio):
                            raise ValueError("Redirección de imagen a un host no autorizado.")
                        if host_destino != host:
                            opciones.pop("headers", None)
                            opciones.pop("auth", None)
                        actual = destino
                        continue
                    response.raise_for_status()
                    mime = (mime_declarado or response.headers.get("content-type", "")).split(";")[0].lower()
                    if mime not in {"image/jpeg", "image/png", "image/webp"}:
                        raise ValueError("Formato no permitido; use JPEG, PNG o WEBP.")
                    contenido = bytearray()
                    for bloque in response.iter_content(chunk_size=64 * 1024):
                        contenido.extend(bloque)
                        if len(contenido) > settings.image_max_bytes:
                            raise ValueError("La imagen supera el tamaño máximo permitido.")
                    if not contenido:
                        raise ValueError("La imagen descargada está vacía.")
                    return bytes(contenido), mime
            raise ValueError("Demasiadas redirecciones al descargar la imagen.")

        return await asyncio.to_thread(descargar)

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


def _host_permitido(host: str, *, meta: bool = False, twilio: bool = False) -> bool:
    if meta:
        return (
            host == "graph.facebook.com"
            or host == "lookaside.fbsbx.com"
            or host.endswith(".fbcdn.net")
        )
    if twilio:
        return host == "api.twilio.com" or host.endswith(".twilio.com") or host.endswith(".twiliocdn.com")
    return False
