"""Crea y migra la base de datos carbot_test."""

import asyncio
import os
import re
import subprocess
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


async def main():
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = int(os.getenv("POSTGRES_PORT", 5433))
    user = os.getenv("POSTGRES_USER", "carbot_app")
    password = os.getenv("POSTGRES_PASSWORD", "").strip()
    if not password:
        raise RuntimeError("POSTGRES_PASSWORD es obligatorio; no se permiten credenciales predeterminadas.")

    admin_user = os.getenv("POSTGRES_ADMIN_USER", "postgres").strip()
    admin_password = os.getenv("POSTGRES_ADMIN_PASSWORD", password).strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", user):
        raise RuntimeError("POSTGRES_USER contiene caracteres no permitidos.")

    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=admin_user,
        password=admin_password,
        database="postgres",
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'carbot_test'")
        if not exists:
            await conn.execute(f'CREATE DATABASE carbot_test OWNER "{user}"')
            print("Base de datos 'carbot_test' creada exitosamente.")
        else:
            print("Base de datos 'carbot_test' ya existe.")
    finally:
        await conn.close()

    # Ejecutar alembic upgrade head sobre carbot_test
    test_db_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/carbot_test"
    env = os.environ.copy()
    env["DATABASE_URL"] = test_db_url
    env["POSTGRES_DB"] = "carbot_test"
    env["DATABASE_ENABLED"] = "true"
    res = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    print("Alembic upgrade output:\n", res.stdout, res.stderr)
    if res.returncode != 0:
        raise RuntimeError("No se pudo migrar carbot_test.")


if __name__ == "__main__":
    asyncio.run(main())
