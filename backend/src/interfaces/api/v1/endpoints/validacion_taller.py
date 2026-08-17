"""Endpoints de validación real de diagnósticos en taller automotriz."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.config import settings
from src.core.security import verificar_jwt_administrador

router = APIRouter()
LIMA_TZ = ZoneInfo("America/Lima")

TRACKER_CSV_PATH = settings.paths.tracker_csv


class CasoValidacionDTO(BaseModel):
    item: int
    fase: str
    fecha: str
    placa: str
    marca_modelo: str
    sintoma: str
    falla_real: str
    chatbot_prediccion: str
    campos_completos: int
    tiempo_diagnostico_minutos: int
    prediccion_correcta: int


class CrearCasoValidacionDTO(BaseModel):
    fase: str = Field(default="Post-test", description="Fase de evaluación: Pre-test o Post-test")
    fecha: Optional[str] = Field(default=None, description="Fecha de atención (YYYY-MM-DD)")
    placa: str = Field(min_length=3, max_length=15, description="Placa del vehículo")
    marca_modelo: str = Field(min_length=2, max_length=100, description="Marca y modelo (ej. Toyota Yaris)")
    sintoma: str = Field(min_length=5, description="Síntoma reportado por el cliente o detectado")
    falla_real: str = Field(min_length=3, description="Diagnóstico real confirmado por el mecánico")
    chatbot_prediccion: str = Field(min_length=3, description="Predicción generada por CarBot")
    campos_completos: int = Field(default=1, ge=0, le=1, description="1 si tiene datos completos, 0 si incompleto")
    tiempo_diagnostico_minutos: int = Field(ge=1, le=600, description="Tiempo total en minutos del proceso")
    prediccion_correcta: int = Field(ge=0, le=1, description="1 si el chatbot acertó con la falla real, 0 si no")


class MetricasValidacionResponseDTO(BaseModel):
    total_casos: int
    total_aciertos: int
    total_desaciertos: int
    tasa_acierto_global_porcentaje: float
    casos_pretest: int
    tasa_acierto_pretest_porcentaje: float
    tiempo_promedio_pretest_min: float
    casos_posttest: int
    tasa_acierto_posttest_porcentaje: float
    tiempo_promedio_posttest_min: float
    reduccion_tiempo_porcentaje: float
    distribucion_marcas: List[Dict[str, Any]]
    top_fallas_reales: List[Dict[str, Any]]


def _cargar_df_tracker() -> pd.DataFrame:
    if not TRACKER_CSV_PATH.exists():
        return pd.DataFrame(
            columns=[
                "item", "fase", "fecha", "placa", "marca_modelo", "sintoma",
                "falla_real", "chatbot_prediccion", "campos_completos",
                "tiempo_diagnostico_minutos", "prediccion_correcta"
            ]
        )
    return pd.read_csv(TRACKER_CSV_PATH, encoding="utf-8")


@router.get("", summary="Listar casos de validación real en taller")
async def listar_casos_validacion(
    fase: Optional[str] = Query(None, description="Filtrar por fase: Pre-test o Post-test"),
    marca: Optional[str] = Query(None, description="Filtrar por marca/modelo"),
    acierto: Optional[int] = Query(None, ge=0, le=1, description="1 acertados, 0 desacertados"),
    busqueda: Optional[str] = Query(None, description="Término de búsqueda libre"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    payload: dict = Depends(verificar_jwt_administrador),
):
    df = _cargar_df_tracker()
    if df.empty:
        return {"total": 0, "casos": []}

    # Aplicar filtros
    if fase:
        df = df[df["fase"].astype(str).str.lower() == fase.strip().lower()]
    if marca:
        df = df[df["marca_modelo"].astype(str).str.contains(marca.strip(), case=False, na=False)]
    if acierto is not None:
        df = df[df["prediccion_correcta"] == acierto]
    if busqueda:
        term = busqueda.strip()
        mask = (
            df["sintoma"].astype(str).str.contains(term, case=False, na=False)
            | df["falla_real"].astype(str).str.contains(term, case=False, na=False)
            | df["chatbot_prediccion"].astype(str).str.contains(term, case=False, na=False)
            | df["placa"].astype(str).str.contains(term, case=False, na=False)
            | df["marca_modelo"].astype(str).str.contains(term, case=False, na=False)
        )
        df = df[mask]

    total_filtrado = len(df)
    df_pagina = df.iloc[::-1].iloc[skip : skip + limit]  # Orden descendente por item

    casos_lista = df_pagina.to_dict(orient="records")
    return {
        "total": total_filtrado,
        "skip": skip,
        "limit": limit,
        "casos": casos_lista,
    }


@router.get("/metricas", response_model=MetricasValidacionResponseDTO, summary="Obtener KPIs y métricas de validación en taller")
async def obtener_metricas_validacion(
    payload: dict = Depends(verificar_jwt_administrador),
):
    df = _cargar_df_tracker()
    if df.empty:
        return MetricasValidacionResponseDTO(
            total_casos=0,
            total_aciertos=0,
            total_desaciertos=0,
            tasa_acierto_global_porcentaje=0.0,
            casos_pretest=0,
            tasa_acierto_pretest_porcentaje=0.0,
            tiempo_promedio_pretest_min=0.0,
            casos_posttest=0,
            tasa_acierto_posttest_porcentaje=0.0,
            tiempo_promedio_posttest_min=0.0,
            reduccion_tiempo_porcentaje=0.0,
            distribucion_marcas=[],
            top_fallas_reales=[],
        )

    total_casos = len(df)
    total_aciertos = int(df["prediccion_correcta"].sum())
    total_desaciertos = total_casos - total_aciertos
    tasa_global = round((total_aciertos / total_casos) * 100, 2) if total_casos > 0 else 0.0

    # Pre-test
    df_pre = df[df["fase"].astype(str).str.lower().str.contains("pre")]
    casos_pre = len(df_pre)
    tasa_pre = round((df_pre["prediccion_correcta"].sum() / casos_pre) * 100, 2) if casos_pre > 0 else 0.0
    t_pre = round(float(df_pre["tiempo_diagnostico_minutos"].mean()), 1) if casos_pre > 0 else 0.0

    # Post-test
    df_post = df[df["fase"].astype(str).str.lower().str.contains("post")]
    casos_post = len(df_post)
    tasa_post = round((df_post["prediccion_correcta"].sum() / casos_post) * 100, 2) if casos_post > 0 else 0.0
    t_post = round(float(df_post["tiempo_diagnostico_minutos"].mean()), 1) if casos_post > 0 else 0.0

    # Reducción de tiempo
    reduccion_tiempo = round(((t_pre - t_post) / t_pre) * 100, 2) if t_pre > 0 and t_post > 0 else 0.0

    # Distribución por marca
    dist_marcas = [
        {"marca": str(k), "conteo": int(v)}
        for k, v in df["marca_modelo"].value_counts().head(8).items()
    ]

    # Top fallas reales
    top_fallas = [
        {"falla": str(k), "conteo": int(v)}
        for k, v in df["falla_real"].value_counts().head(8).items()
    ]

    return MetricasValidacionResponseDTO(
        total_casos=total_casos,
        total_aciertos=total_aciertos,
        total_desaciertos=total_desaciertos,
        tasa_acierto_global_porcentaje=tasa_global,
        casos_pretest=casos_pre,
        tasa_acierto_pretest_porcentaje=tasa_pre,
        tiempo_promedio_pretest_min=t_pre,
        casos_posttest=casos_post,
        tasa_acierto_posttest_porcentaje=tasa_post,
        tiempo_promedio_posttest_min=t_post,
        reduccion_tiempo_porcentaje=reduccion_tiempo,
        distribucion_marcas=dist_marcas,
        top_fallas_reales=top_fallas,
    )


@router.post("", response_model=CasoValidacionDTO, status_code=201, summary="Registrar nuevo caso de validación real en taller")
async def registrar_caso_validacion(
    dto: CrearCasoValidacionDTO,
    payload: dict = Depends(verificar_jwt_administrador),
):
    df = _cargar_df_tracker()
    siguiente_item = int(df["item"].max()) + 1 if not df.empty and "item" in df.columns else 1
    fecha_hoy = dto.fecha or datetime.now(LIMA_TZ).strftime("%Y-%m-%d")

    nuevo_registro = {
        "item": siguiente_item,
        "fase": dto.fase.strip(),
        "fecha": fecha_hoy,
        "placa": dto.placa.strip().upper(),
        "marca_modelo": dto.marca_modelo.strip(),
        "sintoma": dto.sintoma.strip(),
        "falla_real": dto.falla_real.strip(),
        "chatbot_prediccion": dto.chatbot_prediccion.strip(),
        "campos_completos": dto.campos_completos,
        "tiempo_diagnostico_minutos": dto.tiempo_diagnostico_minutos,
        "prediccion_correcta": dto.prediccion_correcta,
    }

    df_nuevo = pd.DataFrame([nuevo_registro])
    if df.empty:
        df_nuevo.to_csv(TRACKER_CSV_PATH, index=False, encoding="utf-8")
    else:
        df_actualizado = pd.concat([df, df_nuevo], ignore_index=True)
        df_actualizado.to_csv(TRACKER_CSV_PATH, index=False, encoding="utf-8")

    return CasoValidacionDTO(**nuevo_registro)


@router.get("/exportar-csv", summary="Descargar CSV del tracker de diagnósticos para anexos de tesis")
async def exportar_tracker_csv(
    payload: dict = Depends(verificar_jwt_administrador),
):
    df = _cargar_df_tracker()
    stream = io.StringIO()
    df.to_csv(stream, index=False, encoding="utf-8")
    stream.seek(0)

    filename = f"tracker_diagnosticos_taller_{datetime.now(LIMA_TZ).strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        io.BytesIO(stream.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
