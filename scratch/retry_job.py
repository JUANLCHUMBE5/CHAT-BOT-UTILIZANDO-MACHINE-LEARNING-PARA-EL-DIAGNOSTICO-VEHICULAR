import asyncio
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("backend"))

from src.infrastructure.database.connection import obtener_sesion_db
from sqlalchemy import text

async def main():
    async for db in obtener_sesion_db():
        # Reset the latest failed job so the worker picks it up
        res = await db.execute(text("""
            UPDATE trabajos_sistema 
            SET estado = 'pendiente', intentos = 0, error_ultimo = NULL, bloqueado_hasta = NULL
            WHERE id = '920218f1-9d31-408b-a53f-d7646f44aee4'
            RETURNING id, estado
        """))
        print("RETRY JOB:", res.fetchall())
        await db.commit()

asyncio.run(main())
