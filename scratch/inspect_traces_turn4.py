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
        res_c = await conn.execute(text("SELECT id, contexto FROM conversaciones WHERE id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094'"))
        conv = res_c.fetchone()
        if conv and conv.contexto:
            cs = conv.contexto.get("conversation_state", {})
            print("HECHOS ACTUALES EN ESTADO:")
            print(json.dumps(cs.get("hechos", {}), indent=2, ensure_ascii=False))
            print("\nTRAZAS:")
            for t in cs.get("trazabilidad", []):
                print(f"--- Turno {t.get('turno')} ---")
                print(f"Mensaje: {t.get('mensaje_original')}")
                print(f"Decision: {t.get('decision')}, Intent: {t.get('question_intent')}")
                print(f"Top 3 RAW: {t.get('top3_ml_raw')}")
                print(f"Top 3 Presentado: {t.get('hipotesis_final_presentada')}")
                print(f"Falla forzada: {t.get('falla_forzada_alternativa')}")
                print(f"Motivo: {t.get('motivo_decision')}")
    await cerrar_conexion()


if __name__ == "__main__":
    asyncio.run(main())
