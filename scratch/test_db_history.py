import asyncio
import sys

sys.path.insert(0, "backend")
from sqlalchemy import text
from src.infrastructure.database.connection import obtener_sesion_db


async def test_audit():
    async for s in obtener_sesion_db():
        res = await s.execute(
            text("""
            SELECT id, accion, entidad, entidad_id, detalles, creado_en 
            FROM operaciones_auditoria 
            ORDER BY creado_en DESC 
            LIMIT 10
        """)
        )
        for r in res.fetchall():
            print(r[5], "| Accion:", r[1], "| Entidad:", r[2], r[3])
            print("  Detalles:", r[4])


asyncio.run(test_audit())
