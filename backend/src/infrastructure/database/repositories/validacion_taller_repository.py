"""Persistencia SQL del tracker de validación por taller."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
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
        tipo_registro: str | None = None,
        marca: str | None = None,
        acierto: int | None = None,
        busqueda: str | None = None,
        skip: int = 0,
        limit: int = 10,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        estado_registro: str | None = None,
    ) -> tuple[int, list[ValidacionTaller]]:
        filtros: list[Any] = [ValidacionTaller.taller_id == taller_id]
        if fecha_desde:
            filtros.append(ValidacionTaller.fecha >= fecha_desde)
        if fecha_hasta:
            filtros.append(ValidacionTaller.fecha <= fecha_hasta)
        if fase:
            filtros.append(func.lower(ValidacionTaller.fase) == fase.strip().lower())
        if tipo_registro:
            filtros.append(ValidacionTaller.tipo_registro == tipo_registro)
        if estado_registro:
            filtros.append(ValidacionTaller.estado_registro == estado_registro)
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
            .order_by(ValidacionTaller.fecha.desc(), ValidacionTaller.item.desc(), ValidacionTaller.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return total, list((await self.session.execute(stmt)).scalars().all())

    async def resumen_por_fase(
        self, taller_id: uuid.UUID, fecha_desde: date | None = None, fecha_hasta: date | None = None
    ) -> list[dict[str, Any]]:
        filtros = [
            ValidacionTaller.taller_id == taller_id,
            ValidacionTaller.estado_registro == "verificado",
            ValidacionTaller.tipo_registro.in_(("THESIS_PRETEST", "THESIS_POSTTEST")),
        ]
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

    async def metricas_variable_independiente(
        self, taller_id: uuid.UUID, fecha_desde: date | None = None, fecha_hasta: date | None = None
    ) -> dict[str, Any]:
        """Cálculo riguroso de los 3 indicadores de la Variable Independiente sobre registros verificados."""
        filtros = [
            ValidacionTaller.taller_id == taller_id,
            ValidacionTaller.estado_registro == "verificado",
            ValidacionTaller.tipo_registro.in_(("THESIS_PRETEST", "THESIS_POSTTEST")),
        ]
        if fecha_desde:
            filtros.append(ValidacionTaller.fecha >= fecha_desde)
        if fecha_hasta:
            filtros.append(ValidacionTaller.fecha <= fecha_hasta)

        stmt = select(
            func.count().label("total_verificados"),
            func.count(ValidacionTaller.sintoma_registrado_correctamente).label("sintomas_evaluados"),
            func.sum(ValidacionTaller.sintoma_registrado_correctamente).label("sintomas_correctos"),
            func.count(ValidacionTaller.procesamiento_validado).label("proc_evaluados"),
            func.sum(ValidacionTaller.procesamiento_validado).label("proc_correctos"),
            func.count(ValidacionTaller.prediccion_correcta).label("predicciones_evaluadas"),
            func.sum(ValidacionTaller.prediccion_correcta).label("predicciones_correctas"),
        ).where(*filtros)

        row = (await self.session.execute(stmt)).mappings().one_or_none()
        if not row or not row["total_verificados"]:
            return {
                "casos_verificados": 0,
                "porcentaje_sintomas_correctos": None,
                "porcentaje_datos_procesados_correctos": None,
                "exactitud_modelo_validada": None,
            }

        s_eval = int(row["sintomas_evaluados"] or 0)
        s_corr = int(row["sintomas_correctos"] or 0)
        pct_sintomas = round((s_corr / s_eval) * 100, 2) if s_eval > 0 else None

        p_eval = int(row["proc_evaluados"] or 0)
        p_corr = int(row["proc_correctos"] or 0)
        pct_proc = round((p_corr / p_eval) * 100, 2) if p_eval > 0 else None

        pred_eval = int(row["predicciones_evaluadas"] or 0)
        pred_corr = int(row["predicciones_correctas"] or 0)
        exactitud = round((pred_corr / pred_eval) * 100, 2) if pred_eval > 0 else None

        return {
            "casos_verificados": int(row["total_verificados"]),
            "porcentaje_sintomas_correctos": pct_sintomas,
            "porcentaje_datos_procesados_correctos": pct_proc,
            "exactitud_modelo_validada": exactitud,
        }

    async def listar_todos(
        self,
        taller_id: uuid.UUID,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        solo_verificados: bool = False,
        tipo_registro: str | None = None,
    ) -> list[ValidacionTaller]:
        stmt = (
            select(ValidacionTaller)
            .where(ValidacionTaller.taller_id == taller_id)
            .order_by(ValidacionTaller.fecha.desc(), ValidacionTaller.item.desc(), ValidacionTaller.id.desc())
        )
        if fecha_desde:
            stmt = stmt.where(ValidacionTaller.fecha >= fecha_desde)
        if fecha_hasta:
            stmt = stmt.where(ValidacionTaller.fecha <= fecha_hasta)
        if tipo_registro:
            stmt = stmt.where(ValidacionTaller.tipo_registro == tipo_registro)
        if solo_verificados:
            stmt = stmt.where(
                ValidacionTaller.estado_registro == "verificado",
                ValidacionTaller.tipo_registro.in_(("THESIS_PRETEST", "THESIS_POSTTEST")),
                ValidacionTaller.fase != "Piloto",
            )
        return list((await self.session.execute(stmt)).scalars().all())

    async def distribuciones(
        self, taller_id: uuid.UUID, fecha_desde: date | None = None, fecha_hasta: date | None = None
    ) -> dict[str, list[dict[str, Any]]]:
        filtros = [
            ValidacionTaller.taller_id == taller_id,
            ValidacionTaller.estado_registro == "verificado",
            ValidacionTaller.tipo_registro.in_(("THESIS_PRETEST", "THESIS_POSTTEST")),
        ]
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

    async def contar_piloto(self, taller_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(ValidacionTaller).where(
            ValidacionTaller.taller_id == taller_id,
            ValidacionTaller.tipo_registro == "PILOT",
        )
        return int((await self.session.execute(stmt)).scalar_one() or 0)

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
        descripcion_sintoma: str | None,
        vehiculo_anio: int | None,
        vehiculo_kilometraje: int | None,
        vehiculo_combustible: str | None,
        vehiculo_transmision: str | None,
        falla_real: str | None,
        chatbot_prediccion: str,
        sistema_afectado_probable: str | None,
        campos_completos: int,
        cantidad_campos_completos: int,
        detalles_campos: dict[str, Any],
        tiempo_diagnostico_minutos: int | None,
        prediccion_correcta: int | None,
        metodo_confirmacion: str | None,
        evidencia_ref: str | None,
        estado_registro: str = "borrador",
        tipo_registro: str = "DEVELOPMENT",
        conversacion_id: uuid.UUID | None = None,
        diagnostico_id: uuid.UUID | None = None,
        sintoma_registrado_correctamente: int | None = None,
        validado_por_id: uuid.UUID | None = None,
        fecha_validacion: datetime | None = None,
        normalizacion_correcta: int | None = None,
        extraccion_correcta: int | None = None,
        clasificacion_procesada: int | None = None,
        procesamiento_validado: int | None = None,
        tiempo_inferencia_ml_ms: int | None = None,
        inicio_sistema_at: datetime | None = None,
        fin_sistema_at: datetime | None = None,
        duracion_sistema_segundos: Decimal | float | None = None,
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
            descripcion_sintoma=descripcion_sintoma,
            vehiculo_anio=vehiculo_anio,
            vehiculo_kilometraje=vehiculo_kilometraje,
            vehiculo_combustible=vehiculo_combustible,
            vehiculo_transmision=vehiculo_transmision,
            falla_real=falla_real,
            chatbot_prediccion=chatbot_prediccion,
            sistema_afectado_probable=sistema_afectado_probable,
            campos_completos=campos_completos,
            cantidad_campos_completos=cantidad_campos_completos,
            detalles_campos=detalles_campos,
            tiempo_diagnostico_minutos=tiempo_diagnostico_minutos,
            prediccion_correcta=prediccion_correcta,
            metodo_confirmacion=metodo_confirmacion,
            evidencia_ref=evidencia_ref,
            estado_registro=estado_registro,
            tipo_registro=tipo_registro,
            conversacion_id=conversacion_id,
            diagnostico_id=diagnostico_id,
            sintoma_registrado_correctamente=sintoma_registrado_correctamente,
            validado_por_id=validado_por_id,
            fecha_validacion=fecha_validacion,
            normalizacion_correcta=normalizacion_correcta,
            extraccion_correcta=extraccion_correcta,
            clasificacion_procesada=clasificacion_procesada,
            procesamiento_validado=procesamiento_validado,
            tiempo_inferencia_ml_ms=tiempo_inferencia_ml_ms,
            inicio_sistema_at=inicio_sistema_at,
            fin_sistema_at=fin_sistema_at,
            duracion_sistema_segundos=duracion_sistema_segundos,
        )
        self.session.add(caso)
        await self.session.flush()
        await self.session.refresh(caso)
        return caso
