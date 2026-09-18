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
        cid = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094'
        res_c = await conn.execute(text("SELECT id, taller_id, contexto, creado_en, actualizado_en FROM conversaciones WHERE id = :cid"), {"cid": cid})
        conv = res_c.fetchone()
        print("=== CONTEXTO DE CONVERSACION ===")
        print(json.dumps(conv.contexto, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    asyncio.run(main())
