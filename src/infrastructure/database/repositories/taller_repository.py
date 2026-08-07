"""Repositorio para la gestión de talleres en PostgreSQL."""

from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.catalogs import Taller


class TallerRepository:
    """Acceso a datos asíncrono para la entidad Taller."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def crear_taller(
        self,
        nombre: str,
        ruc: Optional[str] = None,
        telefono: Optional[str] = None,
        direccion: Optional[str] = None,
        activo: bool = True,
        taller_id: Optional[uuid.UUID] = None,
    ) -> Taller:
        """Crea y persiste un nuevo taller mecánico."""
        taller = Taller(
            id=taller_id or uuid.uuid4(),
            nombre=nombre,
            ruc=ruc,
            telefono=telefono,
            direccion=direccion,
            activo=activo,
        )
        self.session.add(taller)
        await self.session.flush()
        return taller

    async def obtener_por_id(self, taller_id: uuid.UUID) -> Optional[Taller]:
        """Obtiene un taller por su UUID."""
        stmt = select(Taller).where(Taller.id == taller_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def obtener_por_ruc(self, ruc: str) -> Optional[Taller]:
        """Obtiene un taller por su RUC único de 11 dígitos."""
        stmt = select(Taller).where(Taller.ruc == ruc)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def obtener_primer_taller_activo(self) -> Optional[Taller]:
        """Obtiene el primer taller activo registrado en el sistema."""
        stmt = select(Taller).where(Taller.activo.is_(True)).order_by(Taller.creado_en.asc())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def listar_talleres(self, solo_activos: bool = True) -> Sequence[Taller]:
        """Lista todos los talleres mecánicos."""
        stmt = select(Taller)
        if solo_activos:
            stmt = stmt.where(Taller.activo.is_(True))
        result = await self.session.execute(stmt.order_by(Taller.nombre.asc()))
        return result.scalars().all()
