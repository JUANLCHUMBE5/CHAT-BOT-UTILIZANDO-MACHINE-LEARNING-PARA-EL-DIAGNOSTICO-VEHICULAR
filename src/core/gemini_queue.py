"""
Fachada de compatibilidad hacia atrás para el gestor de tasa y cola de Gemini.
El código modularizado reside en el paquete src.core.gemini_queue.
"""

from __future__ import annotations

from src.core.gemini_queue import (
    COSTO_META_MENSAJE_SERVICIO_USD,
    GeminiRateLimiter,
    SolicitudGeminiEncolada,
    crear_resumen_whatsapp,
    gemini_rate_limiter,
)

__all__ = [
    "SolicitudGeminiEncolada",
    "GeminiRateLimiter",
    "gemini_rate_limiter",
    "COSTO_META_MENSAJE_SERVICIO_USD",
    "crear_resumen_whatsapp",
]
