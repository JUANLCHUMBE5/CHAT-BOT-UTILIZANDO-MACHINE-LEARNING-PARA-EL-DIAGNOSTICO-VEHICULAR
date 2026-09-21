"""Endpoints de métricas ejecutivas para el taller calculadas en PostgreSQL."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.trabajos_sistema import ServicioTrabajosSistema
from src.core.authorization import exigir_gestion_trabajos, exigir_lectura_metricas
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.models.diagnostics import Diagnostico
from src.infrastructure.database.repositories.trabajo_sistema_repository import TrabajoSistemaRepository
from src.interfaces.api.v1.dtos.metricas import (
    MetricasColaResponseDTO,
    ResumenMetricasResponseDTO,
    TrabajoFallidoDTO,
)

router = APIRouter()
LIMA_TZ = ZoneInfo("America/Lima")


@router.get("/colas", response_model=MetricasColaResponseDTO, summary="Monitorear colas y worker")
async def obtener_metricas_colas(payload: dict = Depends(exigir_lectura_metricas)):
    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
    taller_uuid = uuid.UUID(payload.get("taller_id", "00000000-0000-0000-0000-000000000001"))
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        metricas = await ServicioTrabajosSistema(session).metricas(taller_uuid)
    return MetricasColaResponseDTO(**metricas)


@router.post("/trabajos/{trabajo_id}/reintentar", summary="Reintentar un trabajo fallido")
async def reintentar_trabajo_fallido(
    trabajo_id: uuid.UUID,
    payload: dict = Depends(exigir_gestion_trabajos),
):
    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
    taller_uuid = uuid.UUID(payload.get("taller_id", "00000000-0000-0000-0000-000000000001"))
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        async with session.begin():
            actualizado = await ServicioTrabajosSistema(session).reintentar(
                trabajo_id,
                taller_uuid,
                payload.get("usuario_id"),
            )
    if not actualizado:
        raise HTTPException(status_code=404, detail="Trabajo fallido no encontrado en este taller.")
    return {"status": "pendiente", "trabajo_id": str(trabajo_id)}


@router.get("/trabajos/fallidos", response_model=List[TrabajoFallidoDTO], summary="Listar trabajos fallidos")
async def listar_trabajos_fallidos(
    limite: int = Query(50, ge=1, le=100),
    payload: dict = Depends(exigir_lectura_metricas),
):
    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
    taller_uuid = uuid.UUID(payload.get("taller_id", "00000000-0000-0000-0000-000000000001"))
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        trabajos = await TrabajoSistemaRepository(session).listar_fallidos(taller_uuid, limite)
        return [
            TrabajoFallidoDTO(
                id=trabajo.id,
                tipo=trabajo.tipo,
                cola=trabajo.cola,
                intentos=trabajo.intentos,
                max_intentos=trabajo.max_intentos,
                error=trabajo.error_ultimo,
                creado_en=trabajo.creado_en,
                actualizado_en=trabajo.actualizado_en,
            )
            for trabajo in trabajos
        ]


@router.post("/trabajos/reentrenar-modelo", status_code=202, summary="Encolar reentrenamiento controlado")
async def encolar_reentrenamiento_modelo(payload: dict = Depends(exigir_gestion_trabajos)):
    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
    taller_uuid = uuid.UUID(payload.get("taller_id", "00000000-0000-0000-0000-000000000001"))
    try:
        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            async with session.begin():
                trabajo, creado = await ServicioTrabajosSistema(session).encolar_reentrenamiento(
                    taller_uuid,
                    payload.get("usuario_id"),
                    payload.get("sub"),
                )
    except OverflowError as exc:
        raise HTTPException(status_code=503, detail=str(exc), headers={"Retry-After": "60"}) from exc
    return {
        "status": "encolado" if creado else "ya_programado",
        "trabajo_id": str(trabajo.id),
    }


@router.get("/resumen", response_model=ResumenMetricasResponseDTO, summary="Obtener resumen ejecutivo de métricas del taller")
async def obtener_resumen_metricas(
    todo: bool = Query(False, description="Incluir todo el historial cuando no hay fecha inicial"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    payload: dict = Depends(exigir_lectura_metricas),
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
                    dt_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").replace(tzinfo=LIMA_TZ) + timedelta(days=1)
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
            elif not todo:
                filtros_base.append(Diagnostico.creado_en >= inicio_mes)
            if dt_fin:
                filtros_base.append(Diagnostico.creado_en < dt_fin)

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

            # 6. Tiempo promedio de respuesta en ms y tiempo de inferencia ML
            res_dur = await session.execute(
                select(func.avg(Diagnostico.duracion_ms)).where(
                    *filtros_base,
                    Diagnostico.duracion_ms.isnot(None),
                )
            )
            avg_dur = res_dur.scalar()
            tiempo_promedio = int(avg_dur) if avg_dur is not None else 0

            res_ml_dur = await session.execute(
                select(func.avg(Diagnostico.tiempo_inferencia_ml_ms)).where(
                    *filtros_base,
                    Diagnostico.tiempo_inferencia_ml_ms.isnot(None),
                )
            )
            avg_ml_dur = res_ml_dur.scalar()
            tiempo_promedio_ml = int(avg_ml_dur) if avg_ml_dur is not None else None

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
            end_range = ((dt_fin - timedelta(days=1)).date() if dt_fin else inicio_hoy.date())

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
                tiempo_inferencia_ml_ms=tiempo_promedio_ml,
                distribucion_modos=distribucion,
                actividad_diaria=actividad_list,
                fallas_frecuentes=fallas_list,
            )

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
