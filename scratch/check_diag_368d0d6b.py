import asyncio
import json
import os
import sys

# Ensure backend path
sys.path.insert(0, os.path.abspath("backend"))
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from src.infrastructure.database import obtener_sesion_db
from sqlalchemy import text

async def check():
    async for session in obtener_sesion_db():
        res = await session.execute(text("SELECT id, sintoma_original, sintoma_normalizado, falla_predicha, confianza, fuente, modo_diagnostico, conclusion_mecanico, trazabilidad, duracion_ms, tiempo_inferencia_ml_ms, creado_en, conversacion_id FROM diagnosticos WHERE id::text LIKE '%368d0d6b%'"))
        rows = res.fetchall()
        for r in rows:
            print("ID:", r[0])
            print("Sintoma orig:", r[1])
            print("Sintoma norm:", r[2])
            print("Falla pred:", r[3])
            print("Confianza:", r[4])
            print("Fuente:", r[5])
            print("Modo:", r[6])
            print("Conclusion:", r[7])
            print("Duracion ms:", r[9])
            print("Tiempo ML ms:", r[10])
            print("Creado en:", r[11])
            print("Trazabilidad:", json.dumps(r[8], indent=2, ensure_ascii=False) if r[8] else None)
            cid = r[12]
            print("\n--- MENSAJES DE LA CONVERSACION", cid, "---")
            m_res = await session.execute(text(f"SELECT texto, direccion, tipo, creado_en FROM mensajes WHERE conversacion_id = '{cid}' ORDER BY creado_en ASC"))
            for m in m_res.fetchall():
                print(f"[{m[3]}] {m[1]} ({m[2]}): {m[0]}")
            
            c_res = await session.execute(text(f"SELECT contexto FROM conversaciones WHERE id = '{cid}'"))
            c_row = c_res.fetchone()
            if c_row:
                print("\n--- CONTEXTO CONVERSACION ---")
                print(json.dumps(c_row[0], indent=2, ensure_ascii=False) if c_row[0] else None)

if __name__ == "__main__":
    asyncio.run(check())
