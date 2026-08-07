"""Crea la base de datos carbot_test para aislamiento de pruebas si no existe."""

import asyncio
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
    pwd = settings.database.password.get_secret_value() if hasattr(settings.database.password, "get_secret_value") else str(settings.database.password)
    conn = await asyncpg.connect(
        host=settings.database.host,
        port=settings.database.port,
        user=settings.database.user,
        password=pwd,
        database="carbot_db",
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
