"""Punto de entrada del proceso worker: python -m src.application.jobs.worker."""

from __future__ import annotations

import asyncio

from src.application.jobs.gemini import gemini_rate_limiter
from src.application.jobs.system_worker import SystemWorker
from src.infrastructure.database.connection import cerrar_conexion, comprobar_conexion


async def main() -> None:
    await comprobar_conexion()
    worker = SystemWorker()
    gemini_rate_limiter.iniciar_worker()
    try:
        await worker.run()
    finally:
        await worker.detener()
        await gemini_rate_limiter.detener_worker()
        await cerrar_conexion()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
