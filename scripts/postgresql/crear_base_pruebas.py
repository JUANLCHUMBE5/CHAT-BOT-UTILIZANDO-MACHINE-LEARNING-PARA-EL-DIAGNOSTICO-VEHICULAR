"""Crea la base de datos carbot_test para aislamiento de pruebas si no existe."""

import asyncio
import os
from pathlib import Path
import sys
import asyncpg
from dotenv import load_dotenv

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

load_dotenv()
from src.config import settings


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
