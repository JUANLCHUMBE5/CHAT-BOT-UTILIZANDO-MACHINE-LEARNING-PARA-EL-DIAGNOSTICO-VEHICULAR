import asyncio
import json
import sys

sys.path.insert(0, "backend")
from sqlalchemy import text
from src.core.security import descifrar_texto_reversible
from src.infrastructure.database.connection import obtener_sesion_db


async def check_jobs():
    async for s in obtener_sesion_db():
        res = await s.execute(
            text("""
            SELECT id, tipo, cola, estado, payload_cifrado, resultado_resumen, creado_en 
            FROM trabajos_sistema 
            ORDER BY creado_en DESC 
            LIMIT 5
        """)
        )
        for r in res.fetchall():
            print("==================================================")
            print(f"ID: {r[0]} | Tipo: {r[1]} | Cola: {r[2]} | Estado: {r[3]}")
            print(f"Creado: {r[6]}")
            try:
                pld = descifrar_texto_reversible(r[4])
                print(f"Payload descifrado (repr): {repr(pld)[:300]}")
            except Exception as e:
                print(f"Error descifrando: {e}")
            print(f"Resultado resumen: {r[5]}")


asyncio.run(check_jobs())
