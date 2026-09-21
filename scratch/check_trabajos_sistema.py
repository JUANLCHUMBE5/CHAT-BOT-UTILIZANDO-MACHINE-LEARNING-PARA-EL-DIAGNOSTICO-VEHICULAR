import asyncio
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("backend"))

from src.infrastructure.database.connection import obtener_sesion_db
from sqlalchemy import text

async def main():
    async for db in obtener_sesion_db():
        cols = await db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'trabajos_sistema'"))
        cnames = [c[0] for c in cols.fetchall()]
        print("COLS IN trabajos_sistema:", cnames)

        res = await db.execute(text("SELECT * FROM trabajos_sistema ORDER BY creado_en DESC LIMIT 10"))
        print("\n=== ULTIMOS TRABAJOS SISTEMA ===")
        for r in res.fetchall():
            d = dict(zip(cnames, r))
            print(f"ID={d.get('id')} TIPO={d.get('tipo')} ESTADO={d.get('estado')} COLA={d.get('cola')} INTENTOS={d.get('intentos')} ERR={d.get('ultimo_error') or d.get('error_ultimo')} CREADO={d.get('creado_en')}")
            print(f"  PAYLOAD: {str(d.get('payload'))[:120]}")

asyncio.run(main())
