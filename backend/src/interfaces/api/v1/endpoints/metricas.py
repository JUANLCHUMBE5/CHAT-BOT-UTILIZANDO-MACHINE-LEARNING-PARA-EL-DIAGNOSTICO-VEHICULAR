"""Endpoints de métricas ejecutivas para el taller calculadas en PostgreSQL."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import verificar_jwt_administrador
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.models.diagnostics import Diagnostico

router = APIRouter()
LIMA_TZ = ZoneInfo("America/Lima")


class ResumenMetricasResponseDTO(BaseModel):
    diagnosticos_hoy: int
    diagnosticos_semana: int
    diagnosticos_mes: int
    diagnosticos_realizados: int = 0
    diagnosticos_pendientes: int = 0
    porcentaje_confirmados: int
    tiempo_promedio_ms: int
    distribucion_modos: List[Dict[str, Any]]
    actividad_diaria: List[Dict[str, Any]]
    fallas_frecuentes: List[Dict[str, Any]]


@router.get("/resumen", response_model=ResumenMetricasResponseDTO, summary="Obtener resumen ejecutivo de métricas del taller")
async def obtener_resumen_metricas(
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    payload: dict = Depends(verificar_jwt_administrador),
):
    """Ejecuta consultas agregadas SQL en PostgreSQL con filtro opcional de rango de fechas."""
    taller_id_str = payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)

    if database_configurada():
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            ahora = datetime.now(LIMA_TZ)
            inicio_hoy = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
            inicio_semana = inicio_hoy - timedelta(days=ahora.weekday())
            inicio_mes = inicio_hoy.replace(day=1)

            # Rango personalizado si se especifica
            dt_inicio = None
            dt_fin = None
            if fecha_inicio:
                try:
                    dt_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").replace(tzinfo=LIMA_TZ)
                except ValueError:
                    pass
            if fecha_fin:
                try:
                    dt_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=LIMA_TZ)
                except ValueError:
                    pass

            # 1. Diagnósticos hoy
            res_hoy = await session.execute(
                select(func.count(Diagnostico.id)).where(
                    Diagnostico.taller_id == taller_uuid,
                    Diagnostico.creado_en >= inicio_hoy,
                )
            )
            hoy_count = res_hoy.scalar() or 0

            # 2. Diagnósticos esta semana calendario
            res_sem = await session.execute(
                select(func.count(Diagnostico.id)).where(
                    Diagnostico.taller_id == taller_uuid,
                    Diagnostico.creado_en >= inicio_semana,
                )
            )
            sem_count = res_sem.scalar() or 0

            # 3. Diagnósticos este mes calendario (o dentro del rango seleccionado)
            filtros_base = [Diagnostico.taller_id == taller_uuid]
            if dt_inicio:
                filtros_base.append(Diagnostico.creado_en >= dt_inicio)
            else:
                filtros_base.append(Diagnostico.creado_en >= inicio_mes)
            if dt_fin:
                filtros_base.append(Diagnostico.creado_en <= dt_fin)

            res_mes = await session.execute(
                select(func.count(Diagnostico.id)).where(*filtros_base)
            )
            mes_count = res_mes.scalar() or 0

            # 4. Diagnósticos pendientes en el periodo seleccionado
            filtros_pend = list(filtros_base)
            filtros_pend.append(Diagnostico.estado.in_(["generado", "en_revision"]))
            res_pend = await session.execute(
                select(func.count(Diagnostico.id)).where(*filtros_pend)
            )
            pend_count = res_pend.scalar() or 0

            # 5. Porcentaje confirmados
            filtros_conf = list(filtros_base)
            filtros_conf.append(Diagnostico.estado == "confirmado")
            res_conf = await session.execute(
                select(func.count(Diagnostico.id)).where(*filtros_conf)
            )
            confirmados_mes = res_conf.scalar() or 0
            pct_confirmados = min(100, int((confirmados_mes / mes_count * 100))) if mes_count > 0 else 0

            # 6. Tiempo promedio de respuesta en ms
            res_dur = await session.execute(
                select(func.avg(Diagnostico.duracion_ms)).where(
                    *filtros_base,
                    Diagnostico.duracion_ms.isnot(None),
                )
            )
            avg_dur = res_dur.scalar()
            tiempo_promedio = int(avg_dur) if avg_dur is not None else 0

            # 7. Distribución de modos
            res_modos = await session.execute(
                select(Diagnostico.modo_diagnostico, func.count(Diagnostico.id))
                .where(*filtros_base)
                .group_by(Diagnostico.modo_diagnostico)
            )
            distribucion = [
                {"modo": modo or "completo_ml_rag_llm", "cantidad": cant}
                for modo, cant in res_modos.all()
            ]

            # 8. Actividad diaria completando días del rango o semana actual
            start_range = (dt_inicio.date() if dt_inicio else (inicio_hoy - timedelta(days=6)).date())
            end_range = (dt_fin.date() if dt_fin else inicio_hoy.date())

            res_actividad = await session.execute(
                select(
                    func.date(Diagnostico.creado_en).label("fecha"),
                    func.count(Diagnostico.id).label("cantidad"),
                )
                .where(*filtros_base)
                .group_by(func.date(Diagnostico.creado_en))
            )
            actividad_map = {str(row.fecha): row.cantidad for row in res_actividad.all()}

            actividad_list = []
            curr_date = start_range
            max_days = min((end_range - start_range).days + 1, 31)
            for _ in range(max_days):
                dia_str = str(curr_date)
                actividad_list.append({
                    "fecha": curr_date.strftime("%a %d"),
                    "cantidad": actividad_map.get(dia_str, 0),
                })
                curr_date += timedelta(days=1)

            # 9. Fallas más frecuentes
            res_fallas = await session.execute(
                select(
                    Diagnostico.falla_predicha,
                    func.count(Diagnostico.id).label("cantidad"),
                )
                .where(
                    *filtros_base,
                    Diagnostico.falla_predicha.isnot(None),
                )
                .group_by(Diagnostico.falla_predicha)
                .order_by(func.count(Diagnostico.id).desc())
                .limit(5)
            )
            fallas_list = [
                {"falla": row.falla_predicha, "cantidad": row.cantidad}
                for row in res_fallas.all()
            ]

            return ResumenMetricasResponseDTO(
                diagnosticos_hoy=hoy_count,
                diagnosticos_semana=sem_count,
                diagnosticos_mes=mes_count,
                diagnosticos_realizados=mes_count,
                diagnosticos_pendientes=pend_count,
                porcentaje_confirmados=pct_confirmados,
                tiempo_promedio_ms=tiempo_promedio,
                distribucion_modos=distribucion,
                actividad_diaria=actividad_list,
                fallas_frecuentes=fallas_list,
            )

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
