import asyncio
import json
import sys

sys.path.insert(0, "backend")
from sqlalchemy import text
from src.infrastructure.database.connection import obtener_sesion_db


async def inspect_turns():
    async for s in obtener_sesion_db():
        res = await s.execute(
            text("""
            SELECT contexto FROM conversaciones WHERE id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094'
        """)
        )
        ctx = res.scalar()
        st = ctx.get("conversation_state", {})
        trazas = st.get("trazabilidad", [])
        print(f"Total trazas: {len(trazas)}")
        for idx, t in enumerate(trazas):
            print(f"\n================ TRAZA {idx+1} (Turno {t.get('turno')}) ================")
            print("Mensaje original:", repr(t.get("mensaje_original")))
            print("Decision:", t.get("decision"))
            print("Motivo decision:", t.get("motivo_decision"))
            print("Consulta consolidada:", repr(t.get("consulta_consolidada")))
            print("Top 3:", t.get("top3"))
            print("Hechos nuevos:", t.get("hechos_nuevos_extraidos"))
            resp = (t.get("respuesta_enviada") or "")[:120].encode('ascii', errors='replace').decode('ascii')
            print("Respuesta enviada:", repr(resp))


asyncio.run(inspect_turns())
