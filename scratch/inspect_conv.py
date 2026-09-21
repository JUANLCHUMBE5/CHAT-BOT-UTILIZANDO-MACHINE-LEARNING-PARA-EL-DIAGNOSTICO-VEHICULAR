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
        res = await conn.execute(text("SELECT id, taller_id, usuario_id, contexto, creado_en, actualizado_en FROM conversaciones WHERE id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094';"))
        conv = res.fetchone()
        if conv:
            print("=== CONVERSACION ===")
            print("ID:", conv.id)
            print("Creado en:", conv.creado_en)
            print("Actualizado en:", conv.actualizado_en)
            print("Contexto keys:", list(conv.contexto.keys()) if isinstance(conv.contexto, dict) else type(conv.contexto))
            print(json.dumps(conv.contexto, indent=2, ensure_ascii=False, default=str))

        res_msgs = await conn.execute(text("SELECT id, meta_message_id, direccion, tipo, texto, creado_en FROM mensajes WHERE conversacion_id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094' ORDER BY creado_en ASC;"))
        msgs = res_msgs.fetchall()
        print("\n=== MENSAJES DE ESTA CONVERSACION ===")
        for m in msgs:
            print(f"[{m.creado_en}] ({m.direccion}) meta_id={m.meta_message_id}")
            print(f"  texto: {m.texto}")

if __name__ == "__main__":
    asyncio.run(main())
