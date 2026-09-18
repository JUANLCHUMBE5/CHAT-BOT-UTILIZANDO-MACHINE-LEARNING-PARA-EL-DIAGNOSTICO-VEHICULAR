import asyncio
import json
from src.infrastructure.database.connection import obtener_engine, _session_factory
from sqlalchemy import text

async def main():
    obtener_engine()
    from src.infrastructure.database.connection import _session_factory
    async with _session_factory() as s:
        sql = """
            SELECT c.contexto->'conversation_state'->'trazabilidad', c.contexto->'conversation_state'
            FROM conversaciones c
            WHERE c.id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094'
        """
        res = await s.execute(text(sql))
        row = res.fetchone()
        trazas = row[0] or []
        cs = row[1] or {}
        
        print(f"Total trazas almacenadas: {len(trazas)}")
        print(f"Hechos activos actuales en conversation_state:")
        for k, v in cs.get("hechos", {}).items():
            print(f"  {k} -> {v.get('valor')} ({v.get('estado')}) cat={v.get('categoria')}")
        print(f"Preguntas realizadas en conversation_state: {len(cs.get('preguntas_realizadas', []))}")
        for p in cs.get("preguntas_realizadas", []):
            print(f"  - Intent: {p.get('intent')} | Texto: {p.get('texto')}")
        print(f"Respuestas obtenidas en conversation_state: {len(cs.get('respuestas_obtenidas', []))}")
        for r in cs.get("respuestas_obtenidas", []):
            print(f"  - Turno: {r.get('turno')} | Texto: {r.get('texto')} | Interp: {r.get('interpretacion')}")
            
        print("\n================ TRAZAS DE TURNOS ================")
        for i, t in enumerate(trazas[-5:]):
            print(f"\n--- TRAZA #{i+1} (Turno {t.get('turno')}) ---")
            print("  Mensaje original:", t.get("mensaje_original"))
            print("  Decision:", t.get("decision"), "| Motivo:", t.get("motivo_decision"))
            print("  Question intent:", t.get("question_intent"))
            print("  Pregunta final:", t.get("pregunta_final"))
            print("  Respuesta enviada:", t.get("respuesta_enviada"))
            print("  Estado operativo:", t.get("estado_operativo"))
            print("  Dominio actual:", t.get("dominio_actual"))
            print("  Hechos nuevos:", t.get("hechos_nuevos_extraidos"))
            print("  Hechos actualizados:", [h.get("campo") for h in t.get("hechos_actualizados", [])])
            print("  Candidatas:")
            for c in t.get("preguntas_candidatas", []):
                print(f"    * {c.get('intent')} (score: {c.get('score')}): {c.get('pregunta')}")
            print("  Descartadas:")
            for d in t.get("preguntas_descartadas", []):
                print(f"    * {d.get('intent')} (motivo: {d.get('motivo')}): {d.get('pregunta')}")
            print("  Top3:", t.get("top3"))
            print("  Plan B activado:", t.get("plan_b_activado"))
            print("  Herramientas bloqueadas:", t.get("herramientas_bloqueadas"))

if __name__ == '__main__':
    asyncio.run(main())
