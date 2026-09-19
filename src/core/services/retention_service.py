"""Política de minimización y retención de datos conversacionales."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.diagnostics import Diagnostico
from src.infrastructure.database.models.jobs import TrabajoGemini
from src.infrastructure.database.models.messaging import Conversacion


async def aplicar_retencion_datos() -> None:
    """Elimina contenido técnico vencido; conserva métricas financieras sin texto."""
    if not settings.database.enabled or settings.data_retention_days <= 0:
        return
    limite = datetime.now(timezone.utc) - timedelta(days=settings.data_retention_days)
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        async with session.begin():
            await session.execute(delete(TrabajoGemini).where(TrabajoGemini.creado_en < limite))
            await session.execute(delete(Diagnostico).where(Diagnostico.creado_en < limite))
            await session.execute(delete(Conversacion).where(Conversacion.creado_en < limite))
