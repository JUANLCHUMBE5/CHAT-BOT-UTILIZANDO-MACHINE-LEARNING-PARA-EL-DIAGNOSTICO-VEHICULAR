import asyncio
import sys

sys.path.insert(0, "backend")
from sqlalchemy import text
from src.infrastructure.database.connection import obtener_sesion_db


async def print_messages():
    async for s in obtener_sesion_db():
        res = await s.execute(
            text("""
            SELECT id, direccion, texto, creado_en 
            FROM mensajes 
            WHERE conversacion_id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094' 
            ORDER BY creado_en ASC
        """)
        )
        for r in res.fetchall():
            txt = (r[2] or "").encode("ascii", errors="replace").decode("ascii")
            print(f"[{r[3]}] ({r[1]}): {txt}\n---")


asyncio.run(print_messages())
