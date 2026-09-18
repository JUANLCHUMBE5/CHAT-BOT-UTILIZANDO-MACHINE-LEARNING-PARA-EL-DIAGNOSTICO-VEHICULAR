import asyncio
import json
import sys

sys.path.insert(0, "backend")
from sqlalchemy import text
from src.infrastructure.database.connection import obtener_sesion_db


async def inspect_diag():
    async for s in obtener_sesion_db():
        res = await s.execute(
            text("""
            SELECT id, falla_predicha, confianza, sintoma_original, sintoma_normalizado, creado_en, trazabilidad 
            FROM diagnosticos 
            WHERE conversacion_id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094' 
            ORDER BY creado_en DESC
            LIMIT 5
        """)
        )
        rows = res.fetchall()
        for r in rows:
            print("==================================================")
            print(f"ID: {r[0]} | Creado: {r[5]}")
            print(f"Falla: {r[1]} | Confianza: {r[2]}")
            print(f"Sintoma original: {repr(r[3])}")
            print(f"Sintoma normalizado: {repr(r[4])}")
            print("Trazabilidad:")
            traza = r[6] if isinstance(r[6], dict) else {}
            for k, v in traza.items():
                if k != "prompt_enviado":
                    print(f"  {k}: {repr(v)[:200]}")


asyncio.run(inspect_diag())
