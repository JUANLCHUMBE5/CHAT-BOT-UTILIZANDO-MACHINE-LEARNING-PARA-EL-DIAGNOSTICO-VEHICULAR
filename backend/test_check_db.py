import asyncio
import sys
from src.infrastructure.database.connection import obtener_sesion_db
from sqlalchemy import text

sys.stdout.reconfigure(encoding="utf-8")

async def main():
    async for session in obtener_sesion_db():
        res = await session.execute(text("SELECT id, direccion, estado_entrega, error_entrega, creado_en, texto FROM mensajes ORDER BY creado_en DESC LIMIT 5"))
        for r in res.fetchall():
            print(f"[{r[4]}] {r[1]} -> Estado: {r[2]} | Error: {r[3]}\nTexto: {r[5][:80]}...\n")
        break

asyncio.run(main())
