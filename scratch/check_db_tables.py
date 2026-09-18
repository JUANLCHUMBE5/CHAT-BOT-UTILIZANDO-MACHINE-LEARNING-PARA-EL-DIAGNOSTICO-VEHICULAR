import asyncio
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("backend"))

from src.infrastructure.database.connection import obtener_sesion_db
from sqlalchemy import text

async def main():
    async for db in obtener_sesion_db():
        res = await db.execute(text("SELECT id, direccion, texto, estado_entrega, creado_en FROM mensajes ORDER BY creado_en DESC LIMIT 10"))
        print("\n=== ULTIMOS MENSAJES (POR FECHA DESC) ===")
        for r in res.fetchall():
            print(f"[{r[4]}] DIR={r[1]} ESTADO={r[3]}: {str(r[2])[:120]}")
            
        res_tg = await db.execute(text("SELECT id, estado, sintoma, creado_en, actualizado_en, intentos, error_ultimo FROM trabajos_gemini ORDER BY creado_en DESC LIMIT 5"))
        print("\n=== ULTIMOS TRABAJOS GEMINI (POR FECHA DESC) ===")
        for r in res_tg.fetchall():
            print(f"[{r[3]}] ESTADO={r[1]} INTENTOS={r[5]} ERR={r[6]}: {str(r[2])[:80]}")

asyncio.run(main())
