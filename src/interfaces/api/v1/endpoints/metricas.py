"""Endpoints de métricas ejecutivas para el taller calculadas en PostgreSQL."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import verificar_jwt_token
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.models.diagnostics import Diagnostico

router = APIRouter()
LIMA_TZ = ZoneInfo("America/Lima")


class ResumenMetricasResponseDTO(BaseModel):
    diagnosticos_hoy: int
    diagnosticos_semana: int
    diagnosticos_mes: int
    porcentaje_confirmados: int
    tiempo_promedio_ms: int
    distribucion_modos: List[Dict[str, Any]]
    actividad_diaria: List[Dict[str, Any]]
    fallas_frecuentes: List[Dict[str, Any]]


@router.get("/resumen", response_model=ResumenMetricasResponseDTO, summary="Obtener resumen ejecutivo de métricas del taller")
async def obtener_resumen_metricas(payload: dict = Depends(verificar_jwt_token)):
    """Ejecuta consultas agregadas SQL en PostgreSQL usando la zona horaria America/Lima."""
    taller_id_str = payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)

    if database_configurada():
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            ahora = datetime.now(LIMA_TZ)
            inicio_hoy = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
            inicio_semana = inicio_hoy - timedelta(days=ahora.weekday())  # Lunes de esta semana
            inicio_mes = inicio_hoy.replace(day=1)  # Día 1 del mes calendario actual

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

            # 3. Diagnósticos este mes calendario
            res_mes = await session.execute(
                select(func.count(Diagnostico.id)).where(
                    Diagnostico.taller_id == taller_uuid,
                    Diagnostico.creado_en >= inicio_mes,
                )
            )
            mes_count = res_mes.scalar() or 0

            # 4. Porcentaje confirmados DEL MES CALENDARIO ACTUAL (0% a 100%)
            res_conf = await session.execute(
                select(func.count(Diagnostico.id)).where(
                    Diagnostico.taller_id == taller_uuid,
                    Diagnostico.creado_en >= inicio_mes,
                    Diagnostico.estado == "confirmado",
                )
            )
            confirmados_mes = res_conf.scalar() or 0
            pct_confirmados = min(100, int((confirmados_mes / mes_count * 100))) if mes_count > 0 else 0

            # 5. Tiempo promedio de respuesta en ms
            res_dur = await session.execute(
                select(func.avg(Diagnostico.duracion_ms)).where(
                    Diagnostico.taller_id == taller_uuid,
                    Diagnostico.duracion_ms.isnot(None),
                )
            )
            avg_dur = res_dur.scalar()
            tiempo_promedio = int(avg_dur) if avg_dur is not None else 0

            # 6. Distribución de modos
            res_modos = await session.execute(
                select(Diagnostico.modo_diagnostico, func.count(Diagnostico.id))
                .where(Diagnostico.taller_id == taller_uuid)
                .group_by(Diagnostico.modo_diagnostico)
            )
            distribucion = [
                {"modo": modo or "completo_ml_rag_llm", "cantidad": cant}
                for modo, cant in res_modos.all()
            ]

            # 7. Actividad diaria completando los 7 días de la semana con 0
            res_actividad = await session.execute(
                select(
                    func.date(Diagnostico.creado_en).label("fecha"),
                    func.count(Diagnostico.id).label("cantidad"),
                )
                .where(
                    Diagnostico.taller_id == taller_uuid,
                    Diagnostico.creado_en >= (inicio_hoy - timedelta(days=6)),
                )
                .group_by(func.date(Diagnostico.creado_en))
            )
            actividad_map = {str(row.fecha): row.cantidad for row in res_actividad.all()}

            actividad_list = []
            for i in range(6, -1, -1):
                dia = (inicio_hoy - timedelta(days=i)).date()
                dia_str = str(dia)
                actividad_list.append({
                    "fecha": dia.strftime("%a %d"),
                    "cantidad": actividad_map.get(dia_str, 0),
                })

            # 8. Fallas más frecuentes
            res_fallas = await session.execute(
                select(
                    Diagnostico.falla_predicha,
                    func.count(Diagnostico.id).label("cantidad"),
                )
                .where(
                    Diagnostico.taller_id == taller_uuid,
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
                porcentaje_confirmados=pct_confirmados,
                tiempo_promedio_ms=tiempo_promedio,
                distribucion_modos=distribucion,
                actividad_diaria=actividad_list,
                fallas_frecuentes=fallas_list,
            )

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
