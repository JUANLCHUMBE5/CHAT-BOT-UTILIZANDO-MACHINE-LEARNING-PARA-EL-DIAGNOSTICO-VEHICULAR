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
    async with engine.connect() as c:
        res = await c.execute(text("SELECT contexto FROM conversaciones WHERE id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094'"))
        row = res.fetchone()
        ctx = row[0]
        cs = ctx.get("conversation_state", {})
        print("cs estado_operativo:", cs.get("estado_operativo"))
        print("cs hechos keys:", list(cs.get("hechos", {}).keys()))
        for k, v in cs.get("hechos", {}).items():
            print(f"  hecho [{k}]: {v}")
        print("cs preguntas_realizadas:", cs.get("preguntas_realizadas"))
        print("cs respuestas_obtenidas:", cs.get("respuestas_obtenidas"))
        for i, tr in enumerate(ctx.get("trazas", [])):
            print(f"--- TRAZA {i+1} ---")
            print("  turno:", tr.get("turno"))
            print("  decision:", tr.get("decision"))
            print("  motivo_decision:", tr.get("motivo_decision"))
            print("  respuesta_enviada:", tr.get("respuesta_enviada"))
            print("  hechos_nuevos:", [h.get("campo") for h in tr.get("hechos_nuevos_extraidos", [])])
            print("  hechos_actualizados:", [h.get("campo") for h in tr.get("hechos_actualizados", [])])

if __name__ == "__main__":
    asyncio.run(main())
