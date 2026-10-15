"""Garantía durable de que un webhook aceptado deja rastro conversacional."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState
from src.infrastructure.database.models.messaging import Conversacion, Mensaje

_CLAVE_TURNOS_REGISTRADOS = "turnos_registrados"
_MAX_TURNOS_REGISTRADOS = 200


def registrar_turno_en_contexto(
    contexto: dict[str, Any], *, message_id: str, texto: str, session_id: str
) -> tuple[dict[str, Any], bool]:
    """Registra una vez el turno en el contexto serializado de la conversación."""
    registrados = list(contexto.get(_CLAVE_TURNOS_REGISTRADOS) or [])
    if message_id in registrados:
        return contexto, False

    serializado = contexto.get("conversation_state") or contexto.get("estado_conversacion")
    estado = (
        ConversationState.from_dict(serializado)
        if isinstance(serializado, dict)
        else ConversationState(session_id=session_id)
    )
    if texto not in estado.historial_mensajes_usuario:
        ExtractorHechos.extraer_y_actualizar(estado, texto)
    else:
        # Algunas rutas terminales (por ejemplo, seguridad o abstención) guardan
        # el texto directamente para preservar el contexto.  No deben crear una
        # segunda entrada al reconciliar el trabajo, pero el contador sí debe
        # representar todos los mensajes ya conservados.
        estado.turno_actual = max(estado.turno_actual, len(estado.historial_mensajes_usuario))
    exportado = estado.exportar_dict()
    actualizado = dict(contexto)
    actualizado["conversation_state"] = exportado
    actualizado["estado_conversacion"] = exportado
    actualizado[_CLAVE_TURNOS_REGISTRADOS] = (registrados + [message_id])[-_MAX_TURNOS_REGISTRADOS:]
    return actualizado, True


async def asegurar_turno_webhook_registrado(session: AsyncSession, meta_message_id: str) -> bool:
    """Cierra el hueco entre recepción y retorno anticipado antes de completar el job."""
    mensaje = await session.scalar(
        select(Mensaje).where(Mensaje.meta_message_id == meta_message_id, Mensaje.direccion == "entrada")
    )
    if mensaje is None:
        return False
    conversacion = await session.get(Conversacion, mensaje.conversacion_id, with_for_update=True)
    if conversacion is None:
        return False
    contexto, registrado = registrar_turno_en_contexto(
        dict(conversacion.contexto or {}),
        message_id=meta_message_id,
        texto=str(mensaje.texto or ""),
        session_id=str(conversacion.id),
    )
    if registrado:
        conversacion.contexto = contexto
    return True
