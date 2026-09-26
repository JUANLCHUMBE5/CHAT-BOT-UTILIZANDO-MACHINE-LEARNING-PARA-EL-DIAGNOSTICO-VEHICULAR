"""Repositorio para vehículos y placas anonimizadas mediante HMAC-SHA256."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_identificador_persistencia
from src.infrastructure.database.models.diagnostics import Vehiculo


def normalizar_placa(placa: str) -> str:
    """Normaliza una placa antes de calcular su identificador pseudónimo."""
    normalizada = "".join(caracter for caracter in placa.upper() if caracter.isalnum())
    if len(normalizada) < 3:
        raise ValueError("La placa debe contener al menos 3 caracteres alfanuméricos.")
    return normalizada


class VehiculoRepository:
    """Acceso a datos asíncrono para vehículos del taller."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def buscar_por_placa(
        self, taller_id: uuid.UUID, placa_str: str
    ) -> Optional[Vehiculo]:
        """Busca un vehículo por su hash HMAC de placa en el taller."""
        if not placa_str or placa_str in ("WAPP-01", "REST-API", "SIN-PLACA"):
            return None
        try:
            placa_hash = hash_identificador_persistencia(normalizar_placa(placa_str), "placa")
        except Exception:
            return None

        stmt = select(Vehiculo).where(
            Vehiculo.taller_id == taller_id,
            Vehiculo.placa_hash == placa_hash,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def obtener_o_crear(
        self,
        taller_id: uuid.UUID,
        registrado_por_id: uuid.UUID,
        placa_str: Optional[str] = None,
        marca: str = "Generico",
        modelo: str = "Generico",
        anio: Optional[int] = None,
        motor: Optional[str] = None,
        combustible: Optional[str] = None,
        kilometraje: Optional[int] = None,
    ) -> Optional[Vehiculo]:
        """Obtiene un vehículo existente por placa o registra uno nuevo."""
        if placa_str and placa_str not in ("WAPP-01", "REST-API", "SIN-PLACA"):
            existente = await self.buscar_por_placa(taller_id, placa_str)
            if existente:
                return existente

            # Extraer los últimos 4 caracteres alfanuméricos de la placa
            placa_limpia = normalizar_placa(placa_str)
            ultimos4 = placa_limpia[-4:] if len(placa_limpia) >= 4 else placa_limpia.rjust(4, "0")
            placa_hash = hash_identificador_persistencia(placa_limpia, "placa")
        else:
            placa_hash = None
            ultimos4 = None

        vehiculo = Vehiculo(
            id=uuid.uuid4(),
            taller_id=taller_id,
            registrado_por_id=registrado_por_id,
            placa_hash=placa_hash,
            placa_ultimos4=ultimos4,
            marca=marca or "Generico",
            modelo=modelo or "Generico",
            anio=anio,
            motor=motor,
            combustible=combustible,
            kilometraje=kilometraje,
        )
        self.session.add(vehiculo)
        await self.session.flush()
        return vehiculo
