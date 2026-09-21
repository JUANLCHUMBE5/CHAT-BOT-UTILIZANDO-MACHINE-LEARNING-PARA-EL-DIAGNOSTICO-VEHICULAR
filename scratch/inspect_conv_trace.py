import asyncio
import json
import sys
sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.infrastructure.database.connection import obtener_engine

async def main():
    engine = obtener_engine()
    async with AsyncSession(engine) as session:
        res = await session.execute(text("SELECT id, contexto, creado_en, actualizado_en FROM conversaciones WHERE id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094'"))
        row = res.fetchone()
        ctx = row.contexto or {}
        print("=== CONTEXTO DE CONVERSACION f7a37e2d-efe8-4c26-9b62-9f4103e7b094 ===")
        print("Keys:", list(ctx.keys()))
        cs = ctx.get("conversation_state", {})
        print("\n--- CONVERSATION_STATE ---")
        print("case_id:", cs.get("case_id"))
        print("active_problem_id:", cs.get("active_problem_id"))
        print("fase:", cs.get("fase"))
        print("estado_operativo:", cs.get("estado_operativo"))
        print("turnos_repregunta:", cs.get("turnos_repregunta"))
        print("turno_actual:", cs.get("turno_actual"))
        print("top3_actual:", cs.get("top3_actual"))
        
        print("\nHECHOS EN ESTADO:")
        for k, v in cs.get("hechos", {}).items():
            val = str(v.get('valor')).encode('ascii', errors='replace').decode('ascii')
            print(f"  {k}: {val} (estado={v.get('estado')}, cat={v.get('categoria')}, turno={v.get('turno_origen')})")
        print("\nTOP3 ACTUAL:", cs.get("top3_actual"))

if __name__ == "__main__":
    asyncio.run(main())
