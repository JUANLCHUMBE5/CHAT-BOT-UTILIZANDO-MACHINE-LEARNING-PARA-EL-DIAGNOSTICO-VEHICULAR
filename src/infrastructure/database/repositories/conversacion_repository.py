"""Repositorio para la gestión de conversaciones y ventanas de servicio de 24 horas."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.messaging import Conversacion


class ConversacionRepository:
    """Acceso a datos asíncrono para conversaciones de WhatsApp y canales multimensajería."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def obtener_conversacion_activa(
        self,
        taller_id: uuid.UUID,
        usuario_id: uuid.UUID,
        canal: str = "whatsapp",
    ) -> Optional[Conversacion]:
        """
        Busca una conversación abierta vigente para el taller y usuario dentro de su ventana de servicio.
        """
        ahora = datetime.now(timezone.utc)
        stmt = (
            select(Conversacion)
            .where(
                Conversacion.taller_id == taller_id,
                Conversacion.usuario_id == usuario_id,
                Conversacion.canal == canal,
                Conversacion.estado == "abierta",
                Conversacion.ventana_servicio_hasta >= ahora,
            )
            .order_by(Conversacion.iniciada_en.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def crear_conversacion(
        self,
        taller_id: uuid.UUID,
        usuario_id: uuid.UUID,
        canal: str = "whatsapp",
        ventana_horas: int = 24,
        conversacion_id: Optional[uuid.UUID] = None,
    ) -> Conversacion:
        """Crea una nueva conversación abierta con ventana de atención de 24 horas."""
        ahora = datetime.now(timezone.utc)
        ventana = ahora + timedelta(hours=ventana_horas)
        conversacion = Conversacion(
            id=conversacion_id or uuid.uuid4(),
            taller_id=taller_id,
            usuario_id=usuario_id,
            canal=canal,
            estado="abierta",
            iniciada_en=ahora,
            ultimo_mensaje_en=ahora,
            ventana_servicio_hasta=ventana,
        )
        self.session.add(conversacion)
        await self.session.flush()
        return conversacion

    async def obtener_o_crear_activa(
        self,
        taller_id: uuid.UUID,
        usuario_id: uuid.UUID,
        canal: str = "whatsapp",
        ventana_horas: int = 24,
    ) -> Conversacion:
        """
        Obtiene la conversación activa vigente o crea una nueva si no existe o expiró la ventana de servicio.
        """
        conv = await self.obtener_conversacion_activa(taller_id, usuario_id, canal)
        ahora = datetime.now(timezone.utc)
        if conv:
            conv.ultimo_mensaje_en = ahora
            conv.ventana_servicio_hasta = ahora + timedelta(hours=ventana_horas)
            await self.session.flush()
            return conv

        # Si había conversaciones anteriores abiertas pero con ventana vencida, marcarlas como expiradas
        stmt_expiradas = select(Conversacion).where(
            Conversacion.taller_id == taller_id,
            Conversacion.usuario_id == usuario_id,
            Conversacion.canal == canal,
            Conversacion.estado == "abierta",
            Conversacion.ventana_servicio_hasta < ahora,
        )
        exp_res = await self.session.execute(stmt_expiradas)
        for exp_conv in exp_res.scalars().all():
            exp_conv.estado = "expirada"
            exp_conv.cerrada_en = ahora

        return await self.crear_conversacion(
            taller_id=taller_id,
            usuario_id=usuario_id,
            canal=canal,
            ventana_horas=ventana_horas,
        )

    async def cerrar_conversacion(self, conversacion_id: uuid.UUID) -> Optional[Conversacion]:
        """Cierra explícitamente una conversación."""
        stmt = select(Conversacion).where(Conversacion.id == conversacion_id)
        result = await self.session.execute(stmt)
        conv = result.scalars().first()
        if conv:
            conv.estado = "cerrada"
            conv.cerrada_en = datetime.now(timezone.utc)
            await self.session.flush()
        return conv

    async def obtener_por_id(self, conversacion_id: uuid.UUID) -> Optional[Conversacion]:
        """Obtiene una conversación por su identificador UUID."""
        stmt = select(Conversacion).where(Conversacion.id == conversacion_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
