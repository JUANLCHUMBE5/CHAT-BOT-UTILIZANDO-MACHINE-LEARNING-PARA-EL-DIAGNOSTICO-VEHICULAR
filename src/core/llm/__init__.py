"""Adaptadores LLM externos con fallback seguro."""

from src.core.llm.groq_client import (
    GroqClientError,
    generar_respuesta_groq,
    transcribir_audio_groq,
)

__all__ = [
    "GroqClientError",
    "generar_respuesta_groq",
    "transcribir_audio_groq",
]
