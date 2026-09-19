"""Enrutador canónico del canal WhatsApp.

El endpoint existente se conserva durante la transición para mantener sus
rutas, pruebas y contratos externos sin cambios.
"""

from src.interfaces.api.v1.endpoints.webhook import router

__all__ = ["router"]
