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
        res_c = await conn.execute(text("SELECT id, contexto FROM conversaciones WHERE id = :cid"), {"cid": cid})
        conv = res_c.fetchone()
        cstate = conv.contexto.get("conversation_state", {})
        print("case_id:", cstate.get("case_id"))
        print("turno_actual:", cstate.get("turno_actual"))
        print("estado_operativo:", cstate.get("estado_operativo"))
        print("\n--- HECHOS ACTIVOS ---")
        for k, v in cstate.get("hechos", {}).items():
            print(f"  {k}: {v}")
        print("\n--- ULTIMOS 3 TURN TRACES ---")
        for t in cstate.get("turn_traces", [])[-3:]:
            print(json.dumps(t, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    asyncio.run(main())
