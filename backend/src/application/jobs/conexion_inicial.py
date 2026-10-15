"""Arranque del worker ante indisponibilidad transitoria; no reserva ningún trabajo."""
from __future__ import annotations

import asyncio

from sqlalchemy.exc import OperationalError

from src.infrastructure.database.connection import comprobar_conexion


async def esperar_base_disponible(intentos: int = 5) -> None:
    """Conexión comprobable, timeout por intento y límite explícito de reintentos."""
    if intentos < 1:
        raise ValueError("Se requiere al menos un intento.")
    for intento in range(intentos):
        try:
            await asyncio.wait_for(comprobar_conexion(), timeout=5)
            return
        except (OSError, OperationalError, TimeoutError):
            if intento + 1 == intentos:
                raise
            await asyncio.sleep(min(2 ** intento, 4))
