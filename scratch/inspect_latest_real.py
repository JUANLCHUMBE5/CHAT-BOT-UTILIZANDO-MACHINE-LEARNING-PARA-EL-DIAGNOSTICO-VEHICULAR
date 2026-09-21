import asyncio
import json
import sys
from pathlib import Path
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "backend"))
sys.stdout.reconfigure(encoding="utf-8")

from src.infrastructure.database.connection import obtener_engine, cerrar_conexion


async def main():
    engine = obtener_engine()
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT id, conversacion_id, direccion, tipo, texto, creado_en 
            FROM mensajes 
            WHERE conversacion_id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094'
            ORDER BY creado_en DESC
            LIMIT 10;
        """))
        rows = res.fetchall()
        print("ÚLTIMOS MENSAJES DE WHATSAPP REAL (f7a37e2d-efe8-4c26-9b62-9f4103e7b094):")
        print("=" * 80)
        for r in reversed(rows):
            print(f"[{r.creado_en}] {r.direccion.upper()}:")
            print(f"  {r.texto}")
            print("-" * 80)

        # Contexto de la conversación
        res_c = await conn.execute(text("SELECT id, contexto FROM conversaciones WHERE id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094'"))
        conv = res_c.fetchone()
        if conv and conv.contexto:
            cs = conv.contexto.get("conversation_state", {})
            print("ESTADO CONVERSACIONAL EN POSTGRESQL:")
            print(f"  Case ID:                     {cs.get('case_id')}")
            print(f"  Herramientas No Disponibles: {cs.get('herramientas_no_disponibles')}")
            print(f"  Pruebas No Disponibles:      {cs.get('pruebas_no_disponibles')}")
            print(f"  Hipótesis descartadas:       {cs.get('hipotesis_descartadas')}")
            if cs.get("trazabilidad"):
                ult_traza = cs["trazabilidad"][-1]
                print(f"  Última traza:")
                print(f"    Turno:               {ult_traza.get('turno')}")
                print(f"    Decisión:            {ult_traza.get('decision')}")
                print(f"    Intent:              {ult_traza.get('question_intent')}")
                print(f"    Versión orquestador: {ult_traza.get('version_orquestador')}")
                print(f"    Plan B activado:     {ult_traza.get('plan_b_activado')}")
                print(f"    Herramientas bloq:   {ult_traza.get('herramientas_bloqueadas')}")
    await cerrar_conexion()


if __name__ == "__main__":
    asyncio.run(main())
