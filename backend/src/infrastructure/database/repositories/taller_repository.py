"""Repositorio para la gestión de talleres en PostgreSQL."""

from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
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
        horario_atencion: Optional[str] = None,
        servicios: Optional[str] = None,
        google_maps_url: Optional[str] = None,
        telefono_id_meta: Optional[str] = None,
        activo: bool = True,
        taller_id: Optional[uuid.UUID] = None,
    ) -> Taller:
        """Crea y persiste un nuevo taller mecánico con sus datos completos."""
        taller = Taller(
            id=taller_id or uuid.uuid4(),
            nombre=nombre,
            ruc=ruc,
            telefono=telefono,
            direccion=direccion,
            horario_atencion=horario_atencion,
            servicios=servicios,
            google_maps_url=google_maps_url,
            telefono_id_meta=telefono_id_meta,
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

    async def obtener_por_meta_phone_number_id(self, telefono_id_meta: str) -> Optional[Taller]:
        """Busca un taller asociado específicamente al ID de número de teléfono de Meta."""
        if not telefono_id_meta:
            return None
        stmt = select(Taller).where(
            Taller.telefono_id_meta == telefono_id_meta,
            Taller.activo.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def obtener_taller_para_webhook(self, telefono_id_meta: Optional[str] = None) -> Optional[Taller]:
        """
        Busca el taller correcto para el webhook:
        1. Busca por telefono_id_meta directo o por META_PHONE_NUMBER_ID.
        2. Si no coincide pero existe un ÚNICO taller activo en el sistema, lo asocia.
        3. Si existen múltiples talleres y ninguno coincide, retorna None para evitar cruce de datos.
        """
        target_id = telefono_id_meta or settings.meta_phone_number_id
        if target_id:
            taller = await self.obtener_por_meta_phone_number_id(target_id)
            if taller:
                return taller

        activos = await self.listar_talleres(solo_activos=True)
        if len(activos) == 1:
            return activos[0]

        return None

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

    async def actualizar_datos_taller(
        self,
        taller_id: uuid.UUID,
        nombre: Optional[str] = None,
        direccion: Optional[str] = None,
        telefono: Optional[str] = None,
        horario_atencion: Optional[str] = None,
        servicios: Optional[str] = None,
        google_maps_url: Optional[str] = None,
        telefono_id_meta: Optional[str] = None,
    ) -> Optional[Taller]:
        """Actualiza los datos informativos de un taller."""
        taller = await self.obtener_por_id(taller_id)
        if not taller:
            return None
        if nombre is not None:
            taller.nombre = nombre
        if direccion is not None:
            taller.direccion = direccion
        if telefono is not None:
            taller.telefono = telefono
        if horario_atencion is not None:
            taller.horario_atencion = horario_atencion
        if servicios is not None:
            taller.servicios = servicios
        if google_maps_url is not None:
            taller.google_maps_url = google_maps_url
        if telefono_id_meta is not None:
            taller.telefono_id_meta = telefono_id_meta
        await self.session.flush()
        return taller
