"""Endpoints de registro experimental y seguimiento de diagnósticos en taller automotriz."""

from __future__ import annotations

import asyncio
import csv
import hashlib
import hmac
import io
import os
import re
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
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
_ASYNC_CSV_LOCK = asyncio.Lock()
DEFAULT_SEED_TALLER_ID = "00000000-0000-0000-0000-000000000001"

FaseEvaluacion = Literal["Pre-test", "Post-test", "Piloto"]


class CasoValidacionDTO(BaseModel):
    item: int
    fase: str
    fecha: str
    placa_enmascarada: str
    placa_hash: str
    marca_modelo: str
    sintoma: str
    falla_real: str
    chatbot_prediccion: str
    campos_completos: int
    tiempo_diagnostico_minutos: int
    prediccion_correcta: int
    taller_id: Optional[str] = None
    mecanico_id: Optional[str] = None
    metodo_confirmacion: Optional[str] = "Inspección Visual en Elevador"
    evidencia_ref: Optional[str] = None


class CrearCasoValidacionDTO(BaseModel):
    fase: FaseEvaluacion = Field(default="Post-test", description="Fase de evaluación: Pre-test, Post-test o Piloto")
    fecha: Optional[str] = Field(default=None, description="Fecha de atención (YYYY-MM-DD)")
    placa: str = Field(min_length=3, max_length=15, description="Placa vehicular (será pseudonimizada)")
    marca_modelo: str = Field(min_length=2, max_length=100, description="Marca y modelo (ej. Toyota Yaris 2020)")
    sintoma: str = Field(min_length=5, description="Síntoma reportado por el cliente o detectado")
    falla_real: str = Field(min_length=3, description="Diagnóstico final confirmado por el mecánico")
    chatbot_prediccion: str = Field(min_length=3, description="Predicción generada por CarBot")
    campos_completos: int = Field(default=1, ge=0, le=1, description="1 si tiene datos completos, 0 si incompleto")
    tiempo_diagnostico_minutos: int = Field(ge=1, le=600, description="Tiempo total en minutos del proceso")
    prediccion_correcta: int = Field(ge=0, le=1, description="1 si el chatbot acertó con la falla real, 0 si no")
    metodo_confirmacion: Optional[str] = Field(default="Inspección Visual + Escáner OBD", description="Método técnico de comprobación")
    evidencia_ref: Optional[str] = Field(default=None, description="Referencia a informe o foto de evidencia")


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
    nota_metodologica: str = (
        "Dataset experimental compuesto por simulación de campo (pre-test / post-test) "
        "y 33 casos de prueba externos de referencia taxonómica (Zenodo)."
    )


def _pseudonimizar_placa(placa_raw: str, secret_key: Optional[str] = None) -> tuple[str, str]:
    """Genera hash HMAC-SHA-256 completo de 64 caracteres con clave secreta y máscara visual."""
    clave_str = secret_key or settings.privacy_secret_key or settings.jwt_secret_key or "carbot-pseudonymization-secret-key-2026"
    clave = clave_str.encode("utf-8")
    placa_limpia = re.sub(r"[^A-Za-z0-9]", "", placa_raw).upper()
    placa_hash = hmac.new(clave, placa_limpia.encode("utf-8"), hashlib.sha256).hexdigest()
    if len(placa_limpia) >= 6:
        enmascarada = f"{placa_limpia[:3]}-***"
    else:
        enmascarada = f"{placa_limpia[:2]}***"
    return enmascarada, placa_hash


def _sanitizar_campo_csv(val: Any) -> str:
    """Neutraliza posibles fórmulas maliciosas de hojas de cálculo (=, +, -, @, tab, retorno)."""
    s = str(val) if val is not None else ""
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s


@contextmanager
def _bloqueo_archivo_interproceso(lock_path: Path, timeout: float = 6.0):
    """Garantiza exclusividad de archivo entre múltiples procesos/workers de uvicorn."""
    lock_file = lock_path.with_suffix(".lock")
    start = time.time()
    adquirido = False
    while time.time() - start < timeout:
        try:
            # os.O_CREAT | os.O_EXCL garantiza exclusividad atómica en el kernel
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            os.close(fd)
            adquirido = True
            break
        except FileExistsError:
            time.sleep(0.02)
        except Exception:
            break

    if not adquirido:
        raise TimeoutError(f"No se pudo adquirir el bloqueo de archivo exclusivo en {lock_file} tras {timeout}s")

    try:
        yield
    finally:
        try:
            if lock_file.exists():
                lock_file.unlink()
        except Exception:
            pass


def _guardar_df_tracker_atomico(df: pd.DataFrame, csv_path: Path) -> None:
    """Escribe a un archivo temporal en el mismo directorio y ejecuta reemplazo atómico en el SO."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = csv_path.parent
    with tempfile.NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding="utf-8", newline="") as tf:
        temp_name = tf.name
        df.to_csv(tf, index=False, encoding="utf-8")
        tf.flush()
        os.fsync(tf.fileno())
    os.replace(temp_name, str(csv_path))


def _cargar_df_tracker() -> pd.DataFrame:
    if not TRACKER_CSV_PATH.exists():
        return pd.DataFrame(
            columns=[
                "item", "fase", "fecha", "placa", "placa_hash", "marca_modelo", "sintoma",
                "falla_real", "chatbot_prediccion", "campos_completos",
                "tiempo_diagnostico_minutos", "prediccion_correcta",
                "taller_id", "mecanico_id", "metodo_confirmacion", "evidencia_ref"
            ]
        )
    return pd.read_csv(TRACKER_CSV_PATH, encoding="utf-8")


def _filtrar_df_por_taller(df: pd.DataFrame, taller_id_auth: str) -> pd.DataFrame:
    """Aplica aislamiento multitenant estricto por taller_id."""
    if df.empty:
        return df
    if "taller_id" not in df.columns:
        df["taller_id"] = DEFAULT_SEED_TALLER_ID
    # Filas sin taller_id pertenecen por defecto al taller seed inicial
    taller_serie = df["taller_id"].fillna(DEFAULT_SEED_TALLER_ID).astype(str)
    return df[taller_serie == str(taller_id_auth)]


@router.get("", summary="Listar registros del tracker experimental en taller (Aislamiento Multitenant)")
async def listar_casos_validacion(
    fase: Optional[str] = Query(None, description="Filtrar por fase: Pre-test o Post-test"),
    marca: Optional[str] = Query(None, description="Filtrar por marca/modelo"),
    acierto: Optional[int] = Query(None, ge=0, le=1, description="1 acertados, 0 desacertados"),
    busqueda: Optional[str] = Query(None, description="Término de búsqueda libre"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    payload: dict = Depends(verificar_jwt_administrador),
):
    taller_id_auth = payload.get("taller_id", DEFAULT_SEED_TALLER_ID)
    df_global = _cargar_df_tracker()
    df = _filtrar_df_por_taller(df_global, taller_id_auth)

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
    df_pagina = df.iloc[::-1].iloc[skip : skip + limit]

    casos_lista = []
    for r in df_pagina.to_dict(orient="records"):
        placa_raw = str(r.get("placa", ""))
        
        # Recuperar placa_hash persistido si ya existe en el registro
        p_hash_existente = str(r.get("placa_hash", "")).strip() if pd.notna(r.get("placa_hash")) else ""
        if p_hash_existente:
            p_hash = p_hash_existente
            enmascarada = placa_raw if ("-" in placa_raw and "***" in placa_raw) else _pseudonimizar_placa(placa_raw)[0]
        else:
            enmascarada, p_hash = _pseudonimizar_placa(placa_raw)

        casos_lista.append(
            CasoValidacionDTO(
                item=int(r.get("item", 0)),
                fase=str(r.get("fase", "")),
                fecha=str(r.get("fecha", "")),
                placa_enmascarada=enmascarada,
                placa_hash=p_hash,
                marca_modelo=str(r.get("marca_modelo", "")),
                sintoma=str(r.get("sintoma", "")),
                falla_real=str(r.get("falla_real", "")),
                chatbot_prediccion=str(r.get("chatbot_prediccion", "")),
                campos_completos=int(r.get("campos_completos", 1)),
                tiempo_diagnostico_minutos=int(r.get("tiempo_diagnostico_minutos", 0)),
                prediccion_correcta=int(r.get("prediccion_correcta", 0)),
                taller_id=str(r.get("taller_id", taller_id_auth)),
                mecanico_id=str(r.get("mecanico_id", payload.get("usuario_id", ""))),
                metodo_confirmacion=str(r.get("metodo_confirmacion", "Inspección Visual")),
                evidencia_ref=str(r.get("evidencia_ref", "")) if pd.notna(r.get("evidencia_ref")) else None,
            )
        )

    return {
        "total": total_filtrado,
        "skip": skip,
        "limit": limit,
        "casos": [c.model_dump() for c in casos_lista],
    }


@router.get("/metricas", response_model=MetricasValidacionResponseDTO, summary="Obtener KPIs del seguimiento experimental por taller")
async def obtener_metricas_validacion(
    payload: dict = Depends(verificar_jwt_administrador),
):
    taller_id_auth = payload.get("taller_id", DEFAULT_SEED_TALLER_ID)
    df_global = _cargar_df_tracker()
    df = _filtrar_df_por_taller(df_global, taller_id_auth)

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


@router.post("", response_model=CasoValidacionDTO, status_code=201, summary="Registrar nuevo caso en el tracker con escritura atómica")
async def registrar_caso_validacion(
    dto: CrearCasoValidacionDTO,
    payload: dict = Depends(verificar_jwt_administrador),
):
    async with _ASYNC_CSV_LOCK:
        try:
            with _bloqueo_archivo_interproceso(TRACKER_CSV_PATH):
                df = _cargar_df_tracker()
                siguiente_item = int(df["item"].max()) + 1 if not df.empty and "item" in df.columns else 1
                fecha_hoy = dto.fecha or datetime.now(LIMA_TZ).strftime("%Y-%m-%d")
                taller_id = payload.get("taller_id", DEFAULT_SEED_TALLER_ID)
                mecanico_id = payload.get("usuario_id", payload.get("sub", ""))

                enmascarada, p_hash = _pseudonimizar_placa(dto.placa)

                nuevo_registro = {
                    "item": siguiente_item,
                    "fase": dto.fase,
                    "fecha": fecha_hoy,
                    "placa": enmascarada,
                    "placa_hash": p_hash,
                    "marca_modelo": dto.marca_modelo.strip(),
                    "sintoma": dto.sintoma.strip(),
                    "falla_real": dto.falla_real.strip(),
                    "chatbot_prediccion": dto.chatbot_prediccion.strip(),
                    "campos_completos": dto.campos_completos,
                    "tiempo_diagnostico_minutos": dto.tiempo_diagnostico_minutos,
                    "prediccion_correcta": dto.prediccion_correcta,
                    "taller_id": taller_id,
                    "mecanico_id": mecanico_id,
                    "metodo_confirmacion": dto.metodo_confirmacion or "Inspección Visual",
                    "evidencia_ref": dto.evidencia_ref or "",
                }

                df_nuevo = pd.DataFrame([nuevo_registro])
                if df.empty:
                    df_actualizado = df_nuevo
                else:
                    df_actualizado = pd.concat([df, df_nuevo], ignore_index=True)

                _guardar_df_tracker_atomico(df_actualizado, TRACKER_CSV_PATH)
        except TimeoutError as exc:
            raise HTTPException(
                status_code=503,
                detail="El tracker se encuentra ocupado procesando otra escritura. Intente nuevamente en unos segundos."
            ) from exc

        return CasoValidacionDTO(
            item=siguiente_item,
            fase=dto.fase,
            fecha=fecha_hoy,
            placa_enmascarada=enmascarada,
            placa_hash=p_hash,
            marca_modelo=dto.marca_modelo.strip(),
            sintoma=dto.sintoma.strip(),
            falla_real=dto.falla_real.strip(),
            chatbot_prediccion=dto.chatbot_prediccion.strip(),
            campos_completos=dto.campos_completos,
            tiempo_diagnostico_minutos=dto.tiempo_diagnostico_minutos,
            prediccion_correcta=dto.prediccion_correcta,
            taller_id=taller_id,
            mecanico_id=mecanico_id,
            metodo_confirmacion=dto.metodo_confirmacion,
            evidencia_ref=dto.evidencia_ref,
        )


@router.get("/exportar-csv", summary="Descargar CSV sanitizado contra inyecciones de fórmulas (Aislamiento Multitenant)")
async def exportar_tracker_csv(
    payload: dict = Depends(verificar_jwt_administrador),
):
    taller_id_auth = payload.get("taller_id", DEFAULT_SEED_TALLER_ID)
    df_global = _cargar_df_tracker()
    df = _filtrar_df_por_taller(df_global, taller_id_auth)

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Escribir encabezados
    columnas = list(df.columns)
    writer.writerow(columnas)

    # Escribir filas sanitizadas contra CSV Formula Injection
    for _, row in df.iterrows():
        fila_sanitizada = [_sanitizar_campo_csv(row[col]) for col in columnas]
        writer.writerow(fila_sanitizada)

    output.seek(0)
    filename = f"tracker_diagnosticos_experimental_{datetime.now(LIMA_TZ).strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
