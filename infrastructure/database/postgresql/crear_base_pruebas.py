"""Crea la base de datos carbot_test para aislamiento de pruebas si no existe."""

import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
BACKEND_ROOT = RAIZ_PROYECTO / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(RAIZ_PROYECTO / ".env")
from src.config import settings  # noqa: E402 - requiere configurar sys.path y cargar .env


async def main():
    admin_user = os.getenv("POSTGRES_ADMIN_USER", "postgres")
    admin_password = os.getenv("POSTGRES_ADMIN_PASSWORD", "")
    if not admin_password:
        raise SystemExit(
            "Defina POSTGRES_ADMIN_PASSWORD temporalmente para crear carbot_test; "
            "no conceda CREATEDB al usuario carbot_app."
        )
    conn = await asyncpg.connect(
        host=settings.database.host,
        port=settings.database.port,
        user=admin_user,
        password=admin_password,
        database="postgres",
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'carbot_test'")
        if not exists:
            await conn.execute("CREATE DATABASE carbot_test OWNER carbot_app")
            print("Base de datos 'carbot_test' creada exitosamente.")
        else:
            print("Base de datos 'carbot_test' ya existe.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
