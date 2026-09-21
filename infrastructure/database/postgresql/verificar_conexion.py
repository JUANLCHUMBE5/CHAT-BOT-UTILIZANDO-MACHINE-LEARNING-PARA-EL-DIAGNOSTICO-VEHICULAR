"""Comprueba la conexión configurada sin imprimir credenciales."""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
BACKEND_ROOT = RAIZ_PROYECTO / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(RAIZ_PROYECTO / ".env")

from src.config import settings  # noqa: E402 - requiere configurar sys.path y cargar .env
from src.infrastructure.database.connection import (  # noqa: E402
    cerrar_conexion,
    comprobar_conexion,
)


async def main() -> None:
    if not settings.database.enabled:
        raise SystemExit("PostgreSQL está desactivado. Configure DATABASE_ENABLED=true en .env.")

    try:
        await comprobar_conexion()
        print(
            "Conexión PostgreSQL correcta: "
            f"{settings.database.host}:{settings.database.port}/{settings.database.database}"
        )
    finally:
        await cerrar_conexion()


if __name__ == "__main__":
    asyncio.run(main())
