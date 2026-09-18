import asyncio
import sys

sys.path.insert(0, "backend")
from sqlalchemy import text
from src.infrastructure.database.connection import obtener_sesion_db


async def test_check():
    async for s in obtener_sesion_db():
        res = await s.execute(
            text("SELECT contexto FROM conversaciones WHERE id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094'")
        )
        ctx = res.scalar() or {}
        print("Tiene conversation_state:", "conversation_state" in ctx)
        st = ctx.get("conversation_state", {})
        print("Turno actual:", st.get("turno_actual"))
        print("Hechos:", list(st.get("hechos", {}).keys()))
        print("Caso finalizado:", ctx.get("caso_finalizado"))


asyncio.run(test_check())
