"""Repositorio para la gestión y búsqueda de identidades externas de WhatsApp."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.database.models.access_requests import IdentidadWhatsApp
from src.infrastructure.database.models.catalogs import Usuario


class IdentidadWhatsAppRepository:
    """Acceso a datos asíncrono para identidades externas de WhatsApp."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def buscar_por_hash(self, identificador_hash: str) -> Optional[IdentidadWhatsApp]:
        """Busca una identidad por su hash HMAC-SHA256, cargando usuario, taller y rol."""
        stmt = (
            select(IdentidadWhatsApp)
            .options(
                selectinload(IdentidadWhatsApp.usuario).selectinload(Usuario.taller),
                selectinload(IdentidadWhatsApp.usuario).selectinload(Usuario.rol),
                selectinload(IdentidadWhatsApp.usuario).selectinload(Usuario.identidades_whatsapp),
            )
            .where(IdentidadWhatsApp.identificador_hash == identificador_hash)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def buscar_por_usuario(self, usuario_id: uuid.UUID) -> Sequence[IdentidadWhatsApp]:
        """Obtiene todas las identidades asociadas a un usuario."""
        stmt = select(IdentidadWhatsApp).where(IdentidadWhatsApp.usuario_id == usuario_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def registrar_identidad(
        self,
        usuario_id: uuid.UUID,
        identificador_hash: str,
        tipo_identificador: str = "telefono",
        ultimos4: Optional[str] = None,
        proveedor: str = "meta",
        destinatario_cifrado: Optional[str] = None,
    ) -> IdentidadWhatsApp:
        """Crea y persiste una nueva identidad externa para un usuario."""
        identidad = IdentidadWhatsApp(
            id=uuid.uuid4(),
            usuario_id=usuario_id,
            proveedor=proveedor,
            identificador_hash=identificador_hash,
            destinatario_cifrado=destinatario_cifrado,
            tipo_identificador=tipo_identificador,
            ultimos4=ultimos4,
            ultima_interaccion=datetime.now(timezone.utc),
        )
        self.session.add(identidad)
        await self.session.flush()
        return identidad

    async def actualizar_ultima_interaccion(self, identidad_id: uuid.UUID) -> None:
        """Actualiza la fecha y hora de la última interacción del contacto."""
        await self.session.execute(
            update(IdentidadWhatsApp)
            .where(IdentidadWhatsApp.id == identidad_id)
            .values(
                ultima_interaccion=datetime.now(timezone.utc),
                actualizado_en=datetime.now(timezone.utc),
            )
        )

    async def actualizar_destinatario(
        self,
        identidad_id: uuid.UUID,
        destinatario_cifrado: str,
        proveedor: str,
    ) -> None:
        """Renueva el destino reversible después de una interacción válida."""
        await self.session.execute(
            update(IdentidadWhatsApp)
            .where(IdentidadWhatsApp.id == identidad_id)
            .values(
                destinatario_cifrado=destinatario_cifrado,
                proveedor=proveedor,
                ultima_interaccion=datetime.now(timezone.utc),
                actualizado_en=datetime.now(timezone.utc),
            )
        )
