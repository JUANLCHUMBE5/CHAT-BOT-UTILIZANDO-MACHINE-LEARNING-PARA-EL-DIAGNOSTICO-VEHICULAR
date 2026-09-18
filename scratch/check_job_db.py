import asyncio
import sys
sys.path.insert(0, '.')
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.infrastructure.database.connection import obtener_engine

async def check_job():
    engine = obtener_engine()
    async with AsyncSession(engine) as session:
        res = await session.execute(text("SELECT * FROM trabajos_sistema WHERE id = '33d5651d-92e8-48b3-9a03-e1a0c7dfff8e'"))
        row = res.fetchone()
        if row:
            print("TRABAJO:")
            for k, v in row._mapping.items():
                print(f"  {k}: {v}")
        else:
            print("TRABAJO NO ENCONTRADO")

        print("\nULTIMOS MENSAJES CON DETALLES:")
        res_m = await session.execute(text("""
            SELECT m.id, m.conversacion_id, m.usuario_id, m.direccion, m.texto, m.creado_en, u.nombres, r.codigo as rol
            FROM mensajes m
            JOIN usuarios u ON u.id = m.usuario_id
            JOIN roles r ON r.id = u.rol_id
            ORDER BY m.creado_en DESC LIMIT 6
        """))
        for r in res_m.fetchall():
            txt_clean = r.texto.encode('ascii', errors='replace').decode('ascii')
            print(f"[{r.direccion}] {r.creado_en} | User: {r.nombres} ({r.rol}) | Conv: {r.conversacion_id}")
            print(f"   {txt_clean[:120]}...")

        print("\nCONTEXTO CONVERSACION:")
        res_c = await session.execute(text("SELECT id, contexto, cerrada_en FROM conversaciones WHERE id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094'"))
        row_c = res_c.fetchone()
        if row_c:
            import json
            ctx = row_c.contexto or {}
            cs = ctx.get("conversation_state", {})
            print(f"Estado Operativo en DB: {cs.get('estado_operativo')}")
            print(f"Fase en DB: {cs.get('fase')}")
            print(f"Hechos en DB: {list(cs.get('hechos', {}).keys())}")
            print(f"Turnos repregunta: {cs.get('turnos_repregunta')}")
            print(f"Version orquestador en traza: {[t.get('version_orquestador') for t in cs.get('trazabilidad', [])]}")

asyncio.run(check_job())
