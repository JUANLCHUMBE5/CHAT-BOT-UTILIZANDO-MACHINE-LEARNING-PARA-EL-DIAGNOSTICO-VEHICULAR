import asyncio
import json
import sys

sys.path.insert(0, "backend")
from sqlalchemy import text
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta
from src.infrastructure.container import ServiceContainer
from src.infrastructure.database.connection import obtener_sesion_db


async def debug_turn8():
    # Obtener el contexto de la base de datos justo antes del turno 8 (o el contexto previo guardado en traza 8)
    async for s in obtener_sesion_db():
        res = await s.execute(
            text("""
            SELECT contexto FROM conversaciones WHERE id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094'
        """)
        )
        ctx = res.scalar()
        st_dict = ctx.get("conversation_state", {})
        trazas = st_dict.get("trazabilidad", [])
        traza8 = trazas[-1] if trazas else {}
        ctx_previo_traza8 = traza8.get("contexto_previo", {})

        print("=== CONTEXTO PREVIO A TURNO 8 (desde traza 8) ===")
        print("Hechos previos:", list(ctx_previo_traza8.get("hechos", {}).keys()))
        print("Turnos repregunta:", ctx_previo_traza8.get("turnos_repregunta"))
        print("Turno actual:", ctx_previo_traza8.get("turno_actual"))
        print("Fase:", ctx_previo_traza8.get("fase"))

        # Reconstruir el estado previo a turno 8
        st_prev = ConversationState.from_dict(ctx_previo_traza8)

        msg = '"Buenas, mi carro estaba normal hasta ayer. Hoy salí a la carretera y a los 20 minutos de manejar empecé a sentir que perdía fuerza, como que se ahogaba. Bajé la velocidad y se recuperó. Pero a los 5 minutos otra vez. Ya no puedo pasar de 80. ¿Qué será?'

        print("\n=== PROBANDO EXTRACTOR CON EL ESTADO PREVIO ===")
        print("Antes de extraer hechos:")
        print("  hechos en st_prev:", list(st_prev.hechos.keys()))
        hechos_ext = ExtractorHechos.extraer_y_actualizar(st_prev, msg)
        print("  hechos extraidos retornados:", len(hechos_ext))
        for h in hechos_ext:
            print("   ->", h.get("campo"), "=", h.get("valor"))
        print("  hechos en st_prev despues:", list(st_prev.hechos.keys()))
        sint = SintetizadorConsulta.sintetizar(st_prev)
        print("  sintetizada resultante:", sint)


asyncio.run(debug_turn8())
