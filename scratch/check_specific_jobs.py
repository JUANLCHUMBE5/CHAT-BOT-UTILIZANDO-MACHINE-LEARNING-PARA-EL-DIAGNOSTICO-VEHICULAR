import asyncio
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("backend"))

from src.infrastructure.database.connection import obtener_sesion_db
from sqlalchemy import text

async def main():
    async for db in obtener_sesion_db():
        res = await db.execute(text("SELECT id, estado, intentos, error_ultimo, creado_en, actualizado_en, sintoma FROM trabajos_gemini WHERE id IN ('a05415bf-29ed-4e01-8c37-c0fed35972cb', '920218f1-9d31-408b-a53f-d7646f44aee4')"))
        print("\n=== JOBS STATUS ===")
        for r in res.fetchall():
            print("ID:", r[0])
            print("ESTADO:", r[1])
            print("INTENTOS:", r[2])
            print("ERROR:", r[3])
            print("CREADO:", r[4])
            print("ACTUALIZADO:", r[5])
            print("SINTOMA:", r[6])
            print("-" * 40)

asyncio.run(main())
