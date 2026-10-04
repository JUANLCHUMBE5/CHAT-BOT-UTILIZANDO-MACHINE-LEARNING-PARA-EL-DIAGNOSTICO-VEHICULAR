"""Interpretación visual acotada para aportar observaciones al diagnóstico CarBot."""

from __future__ import annotations

import base64

import requests

from src.config import settings

_FIRMAS_IMAGEN = {
    "image/jpeg": (lambda data: data.startswith(b"\xff\xd8\xff")),
    "image/png": (lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": (lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"),
}

_INSTRUCCION = """Analiza esta foto como evidencia auxiliar para un mecánico automotriz.
Describe únicamente elementos visibles y legibles relevantes (componentes, conectores,
fugas, daños, testigos del tablero o valores mostrados). Si algo no se distingue, dilo.
No concluyas una avería interna ni inventes mediciones, códigos o especificaciones.
No transcribas placas, rostros ni otros identificadores personales. Responde en español,
breve y estructurado: 'Observaciones visibles' y 'Qué conviene verificar físicamente'."""


class ImageProcessor:
    """Usa Gemini Vision y, si falla, Groq Vision cuando ambos estén habilitados."""

    def interpretar_imagen(
        self, image_bytes: bytes, mime_type: str, *, permitir_gemini: bool = True
    ) -> tuple[str, str]:
        if not settings.image_vision_enabled:
            raise RuntimeError("La interpretación de imágenes está deshabilitada.")
        if not image_bytes or len(image_bytes) > settings.image_max_bytes:
            raise ValueError("La imagen está vacía o supera el tamaño permitido.")
        mime = (mime_type or "").split(";")[0].lower()
        validar_imagen(image_bytes, mime)

        errores: list[str] = []
        if permitir_gemini and settings.gemini_api_key:
            try:
                observaciones = self._interpretar_con_gemini(image_bytes, mime)
                return observaciones, "gemini"
            except Exception as exc:
                errores.append(f"Gemini:{type(exc).__name__}")

        if settings.groq_vision_enabled and settings.groq_api_key:
            try:
                observaciones = self._interpretar_con_groq(image_bytes, mime)
                return observaciones, "groq"
            except Exception as exc:
                errores.append(f"Groq:{type(exc).__name__}")

        if not errores:
            errores.append("No hay proveedor visual habilitado y configurado")
        raise RuntimeError("No se pudo interpretar la imagen (" + ", ".join(errores) + ").")

    def _interpretar_con_gemini(self, image_bytes: bytes, mime: str) -> str:
        modelo = settings.gemini_model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
        payload = {
            "contents": [{"parts": [
                {"text": _INSTRUCCION},
                {"inline_data": {"mime_type": mime, "data": base64.b64encode(image_bytes).decode("ascii")}},
            ]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 350},
        }
        response = None
        from src.core.gemini_queue import gemini_rate_limiter

        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json", "x-goog-api-key": settings.gemini_api_key},
                json=payload,
                timeout=settings.gemini_timeout_seconds,
            )
            if response.status_code >= 400:
                retry_after = (
                    gemini_rate_limiter.extraer_retry_after_segundos(response)
                    if response.status_code == 429
                    else 0
                )
                gemini_rate_limiter.registrar_estado_gemini(
                    exitoso=False,
                    codigo_http=response.status_code,
                    error=f"Gemini imagen HTTP {response.status_code}",
                    retry_after_segundos=retry_after,
                )
                response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            if response is None:
                gemini_rate_limiter.registrar_estado_gemini(
                    exitoso=False, error=f"Gemini imagen red: {type(exc).__name__}"
                )
            raise
        gemini_rate_limiter.registrar_estado_gemini(exitoso=True, codigo_http=200)
        try:
            observaciones = "\n".join(
                parte["text"].strip()
                for parte in data["candidates"][0]["content"]["parts"]
                if parte.get("text", "").strip()
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("El proveedor no devolvió observaciones visuales utilizables.") from exc
        if not observaciones:
            raise RuntimeError("El análisis visual no produjo observaciones.")
        return observaciones[:2000]

    def _interpretar_con_groq(self, image_bytes: bytes, mime: str) -> str:
        clave = settings.groq_api_key.strip()
        if not clave:
            raise RuntimeError("GROQ_API_KEY no configurada.")
        image_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {clave}", "Content-Type": "application/json"},
            json={
                "model": settings.groq_vision_model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _INSTRUCCION},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }],
                "temperature": 0.1,
                "max_tokens": 350,
            },
            timeout=settings.groq_timeout_seconds,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Groq Vision HTTP {response.status_code}")
        data = response.json()
        try:
            contenido = data["choices"][0]["message"]["content"]
            if isinstance(contenido, list):
                texto = "\n".join(
                    str(parte.get("text", "")).strip()
                    for parte in contenido
                    if isinstance(parte, dict) and parte.get("text")
                )
            else:
                texto = str(contenido or "").strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Groq Vision no devolvió observaciones utilizables.") from exc
        if not texto:
            raise RuntimeError("Groq Vision devolvió una respuesta vacía.")
        return texto[:2000]


def validar_imagen(image_bytes: bytes, mime_type: str) -> None:
    """Verifica MIME y firma binaria para no tratar archivos arbitrarios como imágenes."""
    es_valida = _FIRMAS_IMAGEN.get(mime_type)
    if es_valida is None or not es_valida(image_bytes):
        raise ValueError("La imagen debe ser JPEG, PNG o WEBP válida.")
