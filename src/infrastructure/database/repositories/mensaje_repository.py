"""Repositorio para mensajes de WhatsApp con deduplicación por meta_message_id."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.messaging import Mensaje


class MensajeRepository:
    """Acceso a datos asíncrono para mensajes y deduplicación de webhooks."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def existe_meta_message_id(self, meta_message_id: str) -> bool:
        """Verifica de forma rápida e indexada si el mensaje de Meta ya fue registrado."""
        if not meta_message_id:
            return False
        stmt = select(Mensaje.id).where(Mensaje.meta_message_id == meta_message_id)
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    async def obtener_por_meta_message_id(self, meta_message_id: str) -> Optional[Mensaje]:
        """Obtiene un mensaje por su ID único asignado por Meta."""
        stmt = select(Mensaje).where(Mensaje.meta_message_id == meta_message_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def crear_mensaje(
        self,
        conversacion_id: uuid.UUID,
        taller_id: uuid.UUID,
        meta_message_id: str,
        direccion: str = "entrada",
        tipo: str = "texto",
        texto: Optional[str] = None,
        usuario_id: Optional[uuid.UUID] = None,
        categoria_cobro: str = "servicio",
        estado_entrega: str = "recibido",
        costo_estimado: Decimal = Decimal("0"),
        moneda: str = "PEN",
        ocurrido_en: Optional[datetime] = None,
        mensaje_id: Optional[uuid.UUID] = None,
        proveedor: Optional[str] = None,
        destinatario_cifrado: Optional[str] = None,
        disponible_entrega_en: Optional[datetime] = None,
    ) -> Mensaje:
        """Crea y persiste un mensaje recibido o enviado."""
        ahora = ocurrido_en or datetime.now(timezone.utc)
        mensaje = Mensaje(
            id=mensaje_id or uuid.uuid4(),
            conversacion_id=conversacion_id,
            taller_id=taller_id,
            usuario_id=usuario_id,
            meta_message_id=meta_message_id,
            direccion=direccion,
            tipo=tipo,
            categoria_cobro=categoria_cobro,
            texto=texto,
            estado_entrega=estado_entrega,
            costo_estimado=costo_estimado,
            moneda=moneda,
            ocurrido_en=ahora,
            proveedor=proveedor,
            destinatario_cifrado=destinatario_cifrado,
            disponible_entrega_en=disponible_entrega_en,
        )
        self.session.add(mensaje)
        await self.session.flush()
        return mensaje

    async def obtener_siguiente_salida_bloqueada(
        self, bloqueo_segundos: int = 60
    ) -> Optional[Mensaje]:
        """Reclama atómicamente un mensaje pendiente mediante SKIP LOCKED."""
        ahora = datetime.now(timezone.utc)
        stmt = (
            select(Mensaje)
            .where(
                Mensaje.direccion == "salida",
                Mensaje.estado_entrega.in_(("pendiente", "pendiente_reintento")),
                Mensaje.destinatario_cifrado.is_not(None),
                or_(Mensaje.disponible_entrega_en.is_(None), Mensaje.disponible_entrega_en <= ahora),
                or_(Mensaje.bloqueado_entrega_hasta.is_(None), Mensaje.bloqueado_entrega_hasta < ahora),
            )
            .order_by(Mensaje.ocurrido_en.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        mensaje = result.scalar_one_or_none()
        if mensaje:
            mensaje.bloqueado_entrega_hasta = ahora + timedelta(seconds=bloqueo_segundos)
            mensaje.intentos_entrega += 1
            await self.session.flush()
        return mensaje

    async def registrar_resultado_entrega(
        self,
        mensaje_id: uuid.UUID,
        *,
        estado: str,
        id_externo: Optional[str] = None,
        error: Optional[str] = None,
        reintentar_en_segundos: int = 30,
    ) -> Optional[Mensaje]:
        mensaje = await self.session.get(Mensaje, mensaje_id, with_for_update=True)
        if not mensaje:
            return None
        mensaje.estado_entrega = estado
        mensaje.id_externo = id_externo or mensaje.id_externo
        mensaje.error_entrega = error[:1000] if error else None
        mensaje.bloqueado_entrega_hasta = None
        mensaje.disponible_entrega_en = (
            datetime.now(timezone.utc) + timedelta(seconds=reintentar_en_segundos)
            if estado == "pendiente_reintento"
            else None
        )
        await self.session.flush()
        return mensaje

    async def actualizar_estado_por_id_externo(self, id_externo: str, estado: str) -> Optional[Mensaje]:
        stmt = select(Mensaje).where(Mensaje.id_externo == id_externo).with_for_update()
        result = await self.session.execute(stmt)
        mensaje = result.scalar_one_or_none()
        if mensaje:
            mensaje.estado_entrega = estado
            await self.session.flush()
        return mensaje

    async def listar_por_conversacion(
        self, conversacion_id: uuid.UUID, limite: int = 50
    ) -> Sequence[Mensaje]:
        """Lista el historial de mensajes de una conversación en orden cronológico."""
        stmt = (
            select(Mensaje)
            .where(Mensaje.conversacion_id == conversacion_id)
            .order_by(Mensaje.ocurrido_en.asc())
            .limit(limite)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def actualizar_estado_entrega(
        self, meta_message_id: str, estado: str
    ) -> Optional[Mensaje]:
        """Actualiza el estado de un mensaje saliente ya persistido."""
        mensaje = await self.obtener_por_meta_message_id(meta_message_id)
        if mensaje:
            mensaje.estado_entrega = estado
            await self.session.flush()
        return mensaje
