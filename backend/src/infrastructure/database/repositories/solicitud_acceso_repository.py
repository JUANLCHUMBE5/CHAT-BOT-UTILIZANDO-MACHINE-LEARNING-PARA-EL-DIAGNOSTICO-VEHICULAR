"""Repositorio para la gestión de solicitudes de acceso de clientes a mecánicos."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.database.models.access_requests import SolicitudAcceso
from src.infrastructure.database.models.catalogs import Usuario


class SolicitudAccesoRepository:
    """Acceso a datos asíncrono para solicitudes de acceso."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def obtener_por_id(self, solicitud_id: uuid.UUID) -> Optional[SolicitudAcceso]:
        """Obtiene una solicitud por su UUID cargando usuario y taller."""
        stmt = (
            select(SolicitudAcceso)
            .options(
                selectinload(SolicitudAcceso.usuario).selectinload(Usuario.rol),
                selectinload(SolicitudAcceso.usuario).selectinload(Usuario.identidades_whatsapp),
                selectinload(SolicitudAcceso.taller),
                selectinload(SolicitudAcceso.revisado_por),
            )
            .where(SolicitudAcceso.id == solicitud_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def obtener_pendiente_por_usuario(
        self, usuario_id: uuid.UUID, taller_id: uuid.UUID
    ) -> Optional[SolicitudAcceso]:
        """Verifica si el usuario ya tiene una solicitud pendiente en el taller."""
        stmt = (
            select(SolicitudAcceso)
            .where(
                SolicitudAcceso.usuario_id == usuario_id,
                SolicitudAcceso.taller_id == taller_id,
                SolicitudAcceso.estado == "pendiente",
            )
            .order_by(SolicitudAcceso.solicitado_en.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def crear_solicitud(
        self,
        usuario_id: uuid.UUID,
        taller_id: uuid.UUID,
        rol_solicitado: str = "mecanico",
        observaciones: Optional[str] = None,
    ) -> SolicitudAcceso:
        """Crea una nueva solicitud de acceso pendiente."""
        solicitud = SolicitudAcceso(
            id=uuid.uuid4(),
            usuario_id=usuario_id,
            taller_id=taller_id,
            rol_solicitado=rol_solicitado,
            estado="pendiente",
            solicitado_en=datetime.now(timezone.utc),
            observaciones=observaciones,
        )
        self.session.add(solicitud)
        await self.session.flush()
        return solicitud

    async def listar_por_taller(
        self,
        taller_id: uuid.UUID,
        estado: Optional[str] = None,
    ) -> Sequence[SolicitudAcceso]:
        """Lista todas las solicitudes de acceso de un taller con filtro opcional por estado."""
        stmt = (
            select(SolicitudAcceso)
            .options(
                selectinload(SolicitudAcceso.usuario).selectinload(Usuario.identidades_whatsapp),
                selectinload(SolicitudAcceso.usuario).selectinload(Usuario.rol),
                selectinload(SolicitudAcceso.revisado_por),
            )
            .where(SolicitudAcceso.taller_id == taller_id)
        )
        if estado:
            stmt = stmt.where(SolicitudAcceso.estado == estado)

        stmt = stmt.order_by(SolicitudAcceso.solicitado_en.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def responder_solicitud(
        self,
        solicitud_id: uuid.UUID,
        nuevo_estado: str,
        revisado_por_id: Optional[uuid.UUID],
        observaciones: Optional[str] = None,
    ) -> Optional[SolicitudAcceso]:
        """Actualiza el estado de una solicitud a aprobada o rechazada."""
        if nuevo_estado not in ("aprobada", "rechazada"):
            raise ValueError(f"Estado de solicitud inválido: {nuevo_estado}")

        solicitud = await self.obtener_por_id(solicitud_id)
        if not solicitud:
            return None

        solicitud.estado = nuevo_estado
        solicitud.revisado_por_id = revisado_por_id
        solicitud.revisado_en = datetime.now(timezone.utc)
        if observaciones is not None:
            solicitud.observaciones = observaciones

        await self.session.flush()
        return solicitud
