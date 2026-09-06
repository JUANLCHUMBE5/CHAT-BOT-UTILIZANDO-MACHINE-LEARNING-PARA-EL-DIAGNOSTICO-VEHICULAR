"""Persistencia SQL del tracker de validación por taller."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.validation import ValidacionTaller


class ValidacionTallerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def listar(
        self,
        taller_id: uuid.UUID,
        *,
        fase: str | None = None,
        marca: str | None = None,
        acierto: int | None = None,
        busqueda: str | None = None,
        skip: int = 0,
        limit: int = 10,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> tuple[int, list[ValidacionTaller]]:
        filtros: list[Any] = [ValidacionTaller.taller_id == taller_id]
        if fecha_desde:
            filtros.append(ValidacionTaller.fecha >= fecha_desde)
        if fecha_hasta:
            filtros.append(ValidacionTaller.fecha <= fecha_hasta)
        if fase:
            filtros.append(func.lower(ValidacionTaller.fase) == fase.strip().lower())
        if marca:
            filtros.append(ValidacionTaller.marca_modelo.ilike(f"%{marca.strip()}%"))
        if acierto is not None:
            filtros.append(ValidacionTaller.prediccion_correcta == acierto)
        if busqueda:
            patron = f"%{busqueda.strip()}%"
            filtros.append(
                or_(
                    ValidacionTaller.sintoma.ilike(patron),
                    ValidacionTaller.falla_real.ilike(patron),
                    ValidacionTaller.chatbot_prediccion.ilike(patron),
                    ValidacionTaller.placa_enmascarada.ilike(patron),
                    ValidacionTaller.marca_modelo.ilike(patron),
                )
            )
        total = int(
            (await self.session.execute(select(func.count()).select_from(ValidacionTaller).where(*filtros)))
            .scalar_one()
        )
        stmt = (
            select(ValidacionTaller)
            .where(*filtros)
            .order_by(ValidacionTaller.fecha.asc(), ValidacionTaller.item.asc(), ValidacionTaller.id.asc())
            .offset(skip)
            .limit(limit)
        )
        return total, list((await self.session.execute(stmt)).scalars().all())

    async def resumen_por_fase(
        self, taller_id: uuid.UUID, fecha_desde: date | None = None, fecha_hasta: date | None = None
    ) -> list[dict[str, Any]]:
        filtros = [ValidacionTaller.taller_id == taller_id]
        if fecha_desde:
            filtros.append(ValidacionTaller.fecha >= fecha_desde)
        if fecha_hasta:
            filtros.append(ValidacionTaller.fecha <= fecha_hasta)
        stmt = select(
            ValidacionTaller.fase,
            func.count().label("total"),
            func.sum(ValidacionTaller.prediccion_correcta).label("aciertos"),
            func.sum(ValidacionTaller.campos_completos).label("completos"),
            func.sum(ValidacionTaller.tiempo_diagnostico_minutos).label("minutos"),
        ).where(*filtros).group_by(ValidacionTaller.fase)
        return [dict(row) for row in (await self.session.execute(stmt)).mappings().all()]

    async def listar_todos(
        self, taller_id: uuid.UUID, fecha_desde: date | None = None, fecha_hasta: date | None = None
    ) -> list[ValidacionTaller]:
        stmt = (
            select(ValidacionTaller)
            .where(ValidacionTaller.taller_id == taller_id)
            .order_by(ValidacionTaller.fecha, ValidacionTaller.item, ValidacionTaller.id)
        )
        if fecha_desde:
            stmt = stmt.where(ValidacionTaller.fecha >= fecha_desde)
        if fecha_hasta:
            stmt = stmt.where(ValidacionTaller.fecha <= fecha_hasta)
        return list((await self.session.execute(stmt)).scalars().all())

    async def distribuciones(
        self, taller_id: uuid.UUID, fecha_desde: date | None = None, fecha_hasta: date | None = None
    ) -> dict[str, list[dict[str, Any]]]:
        filtros = [ValidacionTaller.taller_id == taller_id]
        if fecha_desde:
            filtros.append(ValidacionTaller.fecha >= fecha_desde)
        if fecha_hasta:
            filtros.append(ValidacionTaller.fecha <= fecha_hasta)
        resultado = {}
        for campo, clave, etiqueta in (
            (ValidacionTaller.marca_modelo, "distribucion_marcas", "marca"),
            (ValidacionTaller.falla_real, "top_fallas_reales", "falla"),
        ):
            conteo = func.count().label("conteo")
            stmt = select(campo.label(etiqueta), conteo).where(*filtros).group_by(campo)
            stmt = stmt.order_by(conteo.desc(), campo.asc()).limit(8)
            resultado[clave] = [dict(r) for r in (await self.session.execute(stmt)).mappings().all()]
        return resultado

    async def crear(
        self,
        *,
        taller_id: uuid.UUID,
        mecanico_id: uuid.UUID | None,
        fase: str,
        fecha: date,
        placa_enmascarada: str,
        placa_hash: str,
        marca_modelo: str,
        sintoma: str,
        falla_real: str,
        chatbot_prediccion: str,
        campos_completos: int,
        tiempo_diagnostico_minutos: int,
        prediccion_correcta: int,
        metodo_confirmacion: str | None,
        evidencia_ref: str | None,
    ) -> ValidacionTaller:
        caso = ValidacionTaller(
            taller_id=taller_id,
            mecanico_id=mecanico_id,
            fase=fase,
            fecha=fecha,
            placa_enmascarada=placa_enmascarada,
            placa_hash=placa_hash,
            marca_modelo=marca_modelo,
            sintoma=sintoma,
            falla_real=falla_real,
            chatbot_prediccion=chatbot_prediccion,
            campos_completos=campos_completos,
            tiempo_diagnostico_minutos=tiempo_diagnostico_minutos,
            prediccion_correcta=prediccion_correcta,
            metodo_confirmacion=metodo_confirmacion,
            evidencia_ref=evidencia_ref,
        )
        self.session.add(caso)
        await self.session.flush()
        await self.session.refresh(caso)
        return caso
