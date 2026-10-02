"""Cliente mínimo para Groq: transcripción Whisper y chat fallback.

Este módulo no persiste claves ni imprime secretos. Solo usa variables de entorno
ya cargadas en ``settings``.
"""

from __future__ import annotations

from typing import Any

import requests

from src.config import settings


class GroqClientError(RuntimeError):
    """Error controlado al invocar Groq."""


def _validar_clave() -> str:
    clave = settings.groq_api_key.strip()
    if not clave:
        raise GroqClientError("GROQ_API_KEY no configurada.")
    return clave


def transcribir_audio_groq(
    audio_bytes: bytes,
    mime_type: str = "audio/ogg",
    nombre_archivo: str = "nota_voz.ogg",
) -> str:
    """Transcribe audio con Groq Whisper y devuelve solo texto limpio."""
    if not settings.groq_audio_enabled:
        raise GroqClientError("Transcripción Groq deshabilitada por configuración.")
    if not audio_bytes:
        raise GroqClientError("Audio vacío.")
    if len(audio_bytes) > settings.audio_max_bytes:
        raise GroqClientError("El audio supera el tamaño máximo permitido.")

    clave = _validar_clave()
    files = {
        "file": (nombre_archivo, audio_bytes, mime_type or "application/octet-stream"),
    }
    data = {
        "model": settings.groq_audio_model,
        "language": "es",
        "response_format": "json",
        "temperature": "0",
        "prompt": "Transcribe literalmente en español. Devuelve solo lo dicho, sin diagnosticar.",
    }
    response = requests.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {clave}"},
        files=files,
        data=data,
        timeout=settings.groq_timeout_seconds,
    )
    if response.status_code >= 400:
        raise GroqClientError(f"Groq audio HTTP {response.status_code}")
    payload = response.json()
    texto = str(payload.get("text") or "").strip()
    if not texto:
        raise GroqClientError("Groq no devolvió transcripción utilizable.")
    return texto


def generar_respuesta_groq(
    prompt_sistema: str,
    *,
    tipo_consulta: str = "diagnostico",
) -> tuple[str, dict[str, Any]]:
    """Genera respuesta con Groq Chat como respaldo del LLM principal."""
    if not settings.groq_chat_enabled:
        raise GroqClientError("Chat Groq deshabilitado por configuración.")
    clave = _validar_clave()
    max_tokens = 140 if tipo_consulta == "consulta_tecnica" else 420
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {clave}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.groq_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Eres CarBot, asistente técnico automotriz. Responde en español, "
                        "con precisión de taller y sin inventar datos fuera del contexto."
                    ),
                },
                {"role": "user", "content": prompt_sistema},
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        },
        timeout=settings.groq_timeout_seconds,
    )
    if response.status_code >= 400:
        raise GroqClientError(f"Groq chat HTTP {response.status_code}")
    payload = response.json()
    try:
        texto = payload["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise GroqClientError("Groq no devolvió una respuesta utilizable.") from exc
    if not texto:
        raise GroqClientError("Groq devolvió una respuesta vacía.")

    usage = payload.get("usage") or {}
    return texto[: settings.gemini_output_max_chars], {
        "usado": True,
        "modelo": settings.groq_model,
        "proveedor": "groq",
        "modo": "consulta_tecnica" if tipo_consulta == "consulta_tecnica" else "completo_ml_rag_llm",
        "tokens_entrada": int(usage.get("prompt_tokens", max(1, len(prompt_sistema) // 4))),
        "tokens_salida": int(usage.get("completion_tokens", max(1, len(texto) // 4))),
    }
