"""Última barrera documental para salidas diferidas y fallback del worker."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.messaging import Conversacion, Mensaje
from src.infrastructure.rag.contrato_documental import proteger_salida_conversacional


async def proteger_mensaje_saliente(mensaje):
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        conversacion = await session.get(Conversacion, mensaje.conversacion_id)
        contexto = (conversacion.contexto or {}) if conversacion else {}
        state = contexto.get("conversation_state") or {}
        history = state.get("historial_mensajes_usuario") or []
        msg_id = str(mensaje.meta_message_id or "")
        entrada_id = msg_id.removeprefix("out_")
        entrada = await session.scalar(
            select(Mensaje.texto).where(
                Mensaje.meta_message_id == entrada_id, Mensaje.conversacion_id == mensaje.conversacion_id
            )
        )
        query = entrada or (history[-1] if history else "")
        vehiculo = " ".join(str(state.get(k) or "") for k in ("marca", "modelo", "anio", "motor", "mercado"))
        texto, _, changed = proteger_salida_conversacional(
            mensaje.texto or "", vehiculo, query, corpus_validado=False, mediciones_reportadas=history
        )
        if changed and texto != mensaje.texto:
            await session.execute(update(Mensaje).where(Mensaje.id == mensaje.id).values(texto=texto))
            await session.commit()
            mensaje.texto = texto
    return mensaje
