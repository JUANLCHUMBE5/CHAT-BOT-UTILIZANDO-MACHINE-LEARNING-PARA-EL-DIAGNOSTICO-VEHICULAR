import asyncio
import json
import sys

sys.path.insert(0, "backend")
from sqlalchemy import text
from src.core.conversacion.models import ConversationState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.infrastructure.container import ServiceContainer
from src.infrastructure.database.connection import obtener_sesion_db


async def test_orquestador_reproduce():
    # Obtener el contexto exacto guardado en traza 7
    async for s in obtener_sesion_db():
        res = await s.execute(
            text("""
            SELECT contexto FROM conversaciones WHERE id = 'f7a37e2d-efe8-4c26-9b62-9f4103e7b094'
        """)
        )
        ctx = res.scalar()
        st_dict = ctx.get("conversation_state", {})
        trazas = st_dict.get("trazabilidad", [])

        # Tomar el contexto previo de la traza 8 (que es el estado después de la traza 7)
        traza8 = trazas[7]
        ctx_previo = traza8.get("contexto_previo")

        repo = InMemoryConversationRepository()
        st_init = ConversationState.from_dict(ctx_previo)
        await repo.save_session("test_sess", st_init)

        from src.core.gestor_diagnostico import GestorDiagnostico
        gestor = GestorDiagnostico()
        orquestador = OrquestadorConversacion(repositorio=repo)

        msg = '"Buenas, mi carro estaba normal hasta ayer. Hoy salí a la carretera y a los 20 minutos de manejar empecé a sentir que perdía fuerza, como que se ahogaba. Bajé la velocidad y se recuperó. Pero a los 5 minutos otra vez. Ya no puedo pasar de 80. ¿Qué será?'

        res = await orquestador.procesar_turno(
            session_id="test_sess",
            texto_usuario=msg,
            gestor_diagnostico=gestor,
        )

        print("=== RESULTADO REPRODUCCION ===")
        print("Decision:", res.get("decision"))
        print("Motivo:", res.get("motivo_decision"))
        print("Consulta consolidada:", repr(res.get("consulta_consolidada")))
        print("Diagnostico ML:", res.get("diagnostico_ml"))
        print("Confianza ML:", res.get("confianza_ml"))
        st_final = res.get("estado")
        if st_final and st_final.trazabilidad:
            ultima_traza = st_final.trazabilidad[-1]
            print("Hechos nuevos en ultima traza:", ultima_traza.get("hechos_nuevos_extraidos"))
            print("Hechos actualizados en ultima traza:", [h.get("campo") for h in ultima_traza.get("hechos_actualizados", [])])
            print("Top 3 en estado:", st_final.top3_actual)
            print("Respuesta texto enviada:\n", res.get("respuesta_texto"))


asyncio.run(test_orquestador_reproduce())
