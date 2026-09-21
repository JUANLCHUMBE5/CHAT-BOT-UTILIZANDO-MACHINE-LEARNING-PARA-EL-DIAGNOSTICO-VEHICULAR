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
        # Search for recent messages containing keywords
        res = await conn.execute(text("""
            SELECT id, conversacion_id, meta_message_id, direccion, tipo, texto, creado_en 
            FROM mensajes 
            WHERE texto ILIKE '%herramienta%' 
               OR texto ILIKE '%tironear%' 
               OR texto ILIKE '%chispa%'
               OR texto ILIKE '%gasolina%'
            ORDER BY creado_en DESC 
            LIMIT 20;
        """))
        msgs = res.fetchall()
        print(f"Encontrados {len(msgs)} mensajes coincidentes:")
        conv_ids = set()
        for m in msgs:
            conv_ids.add(m.conversacion_id)
            print(f"[{m.creado_en}] Conv: {m.conversacion_id} ({m.direccion}): {m.texto[:100]}...")

        print("\n" + "="*50)
        for cid in conv_ids:
            print(f"\n--- REVISANDO CONVERSACION: {cid} ---")
            res_c = await conn.execute(text("SELECT id, taller_id, contexto, creado_en, actualizado_en FROM conversaciones WHERE id = :cid"), {"cid": cid})
            conv = res_c.fetchone()
            if conv:
                print("Contexto keys:", list(conv.contexto.keys()) if isinstance(conv.contexto, dict) else type(conv.contexto))
                # print context
                print("Contexto:\n", json.dumps(conv.contexto, indent=2, ensure_ascii=False, default=str))

            res_all_m = await conn.execute(text("""
                SELECT id, meta_message_id, direccion, tipo, texto, creado_en 
                FROM mensajes 
                WHERE conversacion_id = :cid 
                ORDER BY creado_en ASC
            """), {"cid": cid})
            for m in res_all_m.fetchall():
                print(f"\n[{m.creado_en}] ({m.direccion}) ID={m.id}:")
                print(f"  TEXTO: {m.texto}")

            # Check diagnosticos
            res_d = await conn.execute(text("""
                SELECT id, conversacion_id, sintoma_original, falla_predicha, confianza, trazabilidad, creado_en
                FROM diagnosticos
                WHERE conversacion_id = :cid
                ORDER BY creado_en ASC
            """), {"cid": cid})
            diags = res_d.fetchall()
            print(f"\nDiagnósticos asociados: {len(diags)}")
            for d in diags:
                print(f"  Diag {d.id} | falla={d.falla_predicha} | conf={d.confianza}")
                print(f"  sintoma: {d.sintoma_original}")
                if d.trazabilidad:
                    print(f"  trazabilidad keys: {list(d.trazabilidad.keys())}")
                    # print relevant trace
                    print(f"  trazabilidad snippet: {json.dumps(d.trazabilidad, ensure_ascii=False, default=str)[:300]}")

if __name__ == "__main__":
    asyncio.run(main())
