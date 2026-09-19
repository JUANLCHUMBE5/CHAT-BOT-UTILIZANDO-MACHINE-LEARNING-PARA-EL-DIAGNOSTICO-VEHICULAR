"""Módulo core/gemini_queue: Gestor de tasa (Rate Limiter) y cola persistente para Google Gemini."""

from src.core.gemini_queue.models import (
    COSTO_META_MENSAJE_SERVICIO_USD,
    SolicitudGeminiEncolada,
)
from src.core.gemini_queue.rate_limiter import GeminiRateLimiter
from src.core.gemini_queue.summary_formatter import crear_resumen_whatsapp

# Instancia global del limitador y cola de Gemini
gemini_rate_limiter = GeminiRateLimiter()

__all__ = [
    "SolicitudGeminiEncolada",
    "GeminiRateLimiter",
    "gemini_rate_limiter",
    "COSTO_META_MENSAJE_SERVICIO_USD",
    "crear_resumen_whatsapp",
]
