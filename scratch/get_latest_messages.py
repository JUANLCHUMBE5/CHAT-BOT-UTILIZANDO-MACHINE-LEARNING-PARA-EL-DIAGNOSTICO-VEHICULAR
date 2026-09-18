import asyncio
import json
import sys
sys.path.insert(0, 'backend')
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import text
from src.infrastructure.database.connection import obtener_engine

async def main():
    engine = obtener_engine()
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT id, conversacion_id, meta_message_id, direccion, tipo, texto, creado_en 
            FROM mensajes 
            ORDER BY creado_en DESC 
            LIMIT 30;
        """))
        msgs = res.fetchall()
        print(f"Últimos {len(msgs)} mensajes en la base de datos:")
        for m in reversed(msgs):
            print(f"[{m.creado_en}] ({m.direccion}) Conv: {m.conversacion_id} ID: {m.id}")
            print(f"  TEXTO: {m.texto}\n")

if __name__ == "__main__":
    asyncio.run(main())
