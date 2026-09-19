"""Repositorio para trazabilidad de costos, consumo de APIs (Meta/Gemini) y auditoría."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.operations import Auditoria, UsoApi


class OperacionesRepository:
    """Acceso a datos asíncrono para registro de consumo de APIs y auditoría."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def registrar_uso_api(
        self,
        taller_id: uuid.UUID,
        proveedor: str,
        operacion: str,
        modelo: Optional[str] = None,
        solicitud_externa_id: Optional[str] = None,
        tokens_entrada: int = 0,
        tokens_salida: int = 0,
        unidades: float | Decimal = Decimal("0"),
        costo_estimado: float | Decimal = Decimal("0"),
        moneda: str = "USD",
        diagnostico_id: Optional[uuid.UUID] = None,
        mensaje_id: Optional[uuid.UUID] = None,
        uso_id: Optional[uuid.UUID] = None,
    ) -> UsoApi:
        """Registra el consumo y costo estimado de un servicio externo (WhatsApp Meta, Google Gemini)."""
        unidades_dec = Decimal(str(round(float(unidades), 4)))
        costo_dec = Decimal(str(round(float(costo_estimado), 6)))
        uso = UsoApi(
            id=uso_id or uuid.uuid4(),
            taller_id=taller_id,
            diagnostico_id=diagnostico_id,
            mensaje_id=mensaje_id,
            proveedor=proveedor,
            operacion=operacion,
            modelo=modelo,
            solicitud_externa_id=solicitud_externa_id,
            tokens_entrada=max(0, tokens_entrada),
            tokens_salida=max(0, tokens_salida),
            unidades=unidades_dec,
            costo_estimado=costo_dec,
            moneda=moneda,
        )
        self.session.add(uso)
        await self.session.flush()
        return uso

    async def registrar_auditoria(
        self,
        accion: str,
        entidad: str,
        taller_id: Optional[uuid.UUID] = None,
        usuario_id: Optional[uuid.UUID] = None,
        entidad_id: Optional[uuid.UUID] = None,
        detalles: Optional[dict[str, Any]] = None,
        ip_hash: Optional[str] = None,
        auditoria_id: Optional[uuid.UUID] = None,
    ) -> Auditoria:
        """Registra un evento de seguridad o auditoría operativa."""
        auditoria = Auditoria(
            id=auditoria_id or uuid.uuid4(),
            taller_id=taller_id,
            usuario_id=usuario_id,
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            detalles=detalles or {},
            ip_hash=ip_hash,
        )
        self.session.add(auditoria)
        await self.session.flush()
        return auditoria

    async def obtener_costo_total_taller(
        self, taller_id: uuid.UUID, proveedor: Optional[str] = None
    ) -> Decimal:
        """Calcula el costo total acumulado por el taller en consumo de APIs."""
        stmt = select(func.coalesce(func.sum(UsoApi.costo_estimado), Decimal("0"))).where(
            UsoApi.taller_id == taller_id
        )
        if proveedor:
            stmt = stmt.where(UsoApi.proveedor == proveedor)
        result = await self.session.execute(stmt)
        return result.scalar_one()
