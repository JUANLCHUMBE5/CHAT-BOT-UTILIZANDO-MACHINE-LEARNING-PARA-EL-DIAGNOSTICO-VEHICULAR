"""Endpoints de registro experimental y seguimiento de diagnósticos en taller automotriz."""

from __future__ import annotations

import asyncio
import csv
import hashlib
import hmac
import io
import os
import re
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.validacion_taller import (
    ServicioValidacionTaller,
    calcular_detalles_campos_ficha2,
    construir_datos_generales_vehiculo,
    serializar_caso,
)
from src.config import settings
from src.core.authorization import exigir_gestion_validacion, exigir_lectura_validacion
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.validacion_taller_repository import ValidacionTallerRepository
from src.interfaces.api.v1.dtos.validacion import (
    CasoValidacionDTO,
    CrearCasoValidacionDTO,
    MetricasValidacionResponseDTO,
    MetricasVariableIndependienteDTO,
)

router = APIRouter()
LIMA_TZ = ZoneInfo("America/Lima")
TRACKER_CSV_PATH = settings.paths.tracker_csv
_ASYNC_CSV_LOCK = asyncio.Lock()
DEFAULT_SEED_TALLER_ID = "00000000-0000-0000-0000-000000000001"


def _uuid_claim(payload: dict, nombre: str, *, obligatorio: bool = True) -> uuid.UUID | None:
    valor = payload.get(nombre)
    if not valor and not obligatorio:
        return None
    try:
        return uuid.UUID(str(valor))
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(status_code=401, detail=f"El token contiene un {nombre} inválido.") from exc


def _pseudonimizar_placa(placa_raw: str, secret_key: Optional[str] = None) -> tuple[str, str]:
    """Genera hash HMAC-SHA-256 completo de 64 caracteres con clave secreta y máscara visual."""
    clave_str = secret_key or settings.privacy_secret_key or settings.jwt_secret_key
    if not clave_str:
        raise RuntimeError("PRIVACY_SECRET_KEY es obligatoria para pseudonimizar placas.")
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


def _es_proceso_vivo(pid: int) -> bool:
    """Comprueba si un proceso sigue en ejecución en el sistema operativo."""
    if pid <= 0:
        return False

    if sys.platform == "win32":
        try:
            import ctypes

            synchronize = 0x00100000
            wait_timeout = 0x00000102
            handle = ctypes.windll.kernel32.OpenProcess(synchronize, False, pid)
            if not handle:
                return False
            try:
                return ctypes.windll.kernel32.WaitForSingleObject(handle, 0) == wait_timeout
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return False

    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except (OSError, SystemError):
        return False


@contextmanager
def _bloqueo_archivo_interproceso(lock_path: Path, timeout: float = 6.0, max_stale_seconds: float = 12.0):
    """Garantiza exclusividad de archivo entre múltiples procesos/workers con auto-recuperación de locks huérfanos."""
    lock_file = lock_path.with_suffix(".lock")
    start = time.time()
    adquirido = False
    while time.time() - start < timeout:
        try:
            # os.O_CREAT | os.O_EXCL garantiza exclusividad atómica en el kernel
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            try:
                lock_info = f"{os.getpid()}:{time.time():.4f}\n".encode("utf-8")
                os.write(fd, lock_info)
            finally:
                os.close(fd)
            adquirido = True
            break
        except FileExistsError:
            # Comprobar si el lock existente es huérfano / abandonado tras un crash forzado
            try:
                st = lock_file.stat()
                edad_lock = time.time() - st.st_mtime
                if edad_lock > max_stale_seconds:
                    try:
                        lock_file.unlink()
                        continue
                    except Exception:
                        pass
                else:
                    # Comprobar si el PID que tomó el lock sigue existiendo en el sistema
                    try:
                        contenido = lock_file.read_text(encoding="utf-8").strip()
                        if contenido and ":" in contenido:
                            pid_str, _ = contenido.split(":", 1)
                            pid = int(pid_str)
                            if not _es_proceso_vivo(pid):
                                lock_file.unlink()
                                continue
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(0.02)
        except Exception:
            break

    if not adquirido:
        raise TimeoutError(
            f"No se pudo adquirir el bloqueo de archivo exclusivo en {lock_file} tras {timeout}s"
        )

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
                "item",
                "fase",
                "fecha",
                "placa",
                "placa_hash",
                "marca_modelo",
                "sintoma",
                "descripcion_sintoma",
                "vehiculo_anio",
                "vehiculo_kilometraje",
                "vehiculo_combustible",
                "vehiculo_transmision",
                "falla_real",
                "chatbot_prediccion",
                "sistema_afectado_probable",
                "campos_completos",
                "cantidad_campos_completos",
                "detalles_campos",
                "tiempo_diagnostico_minutos",
                "prediccion_correcta",
                "taller_id",
                "mecanico_id",
                "metodo_confirmacion",
                "evidencia_ref",
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


def periodo_validacion(
    fecha_desde: date | None = Query(None), fecha_hasta: date | None = Query(None)
) -> tuple[date | None, date | None]:
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise HTTPException(status_code=422, detail="La fecha inicial debe ser anterior a la final.")
    return fecha_desde, fecha_hasta


def _filtrar_periodo(df: pd.DataFrame, periodo: tuple[date | None, date | None]) -> pd.DataFrame:
    if df.empty:
        return df
    fechas = pd.to_datetime(df["fecha"], errors="coerce").dt.date
    desde, hasta = periodo
    if desde:
        df = df[fechas >= desde]
    if hasta:
        df = df[fechas.loc[df.index] <= hasta]
    return df


def _filtrar_df_oficial_verificado(df: pd.DataFrame) -> pd.DataFrame:
    """Falla cerrada: solo muestra filas oficiales con estado y auditoría humana explícitos."""
    if df.empty:
        return df.iloc[0:0].copy()

    df = df.copy()
    if "validado_por_id" not in df.columns and "mecanico_id" in df.columns:
        df["validado_por_id"] = df["mecanico_id"]
    if "fecha_validacion" not in df.columns and "fecha" in df.columns:
        df["fecha_validacion"] = df["fecha"]
    if "tipo_registro" not in df.columns and "fase" in df.columns:
        df["tipo_registro"] = df["fase"].apply(
            lambda f: "THESIS_PRETEST" if str(f).strip().lower().startswith("pre")
            else ("THESIS_POSTTEST" if str(f).strip().lower().startswith("post") else "DEVELOPMENT")
        )
    if "estado_registro" not in df.columns:
        df["estado_registro"] = "verificado"

    requeridas = {
        "tipo_registro",
        "estado_registro",
        "fase",
        "falla_real",
        "metodo_confirmacion",
        "evidencia_ref",
        "validado_por_id",
        "fecha_validacion",
    }
    if not requeridas.issubset(df.columns):
        return df.iloc[0:0].copy()

    tipo = df["tipo_registro"].fillna("").astype(str).str.strip()
    fase = df["fase"].fillna("").astype(str).str.strip().str.casefold()
    estado = df["estado_registro"].fillna("").astype(str).str.strip().str.casefold()
    tipo_fase_valido = (
        (tipo == "THESIS_PRETEST") & (fase.isin({"pre-test", "pretest"}) | fase.str.startswith("pre"))
    ) | (
        (tipo == "THESIS_POSTTEST") & (fase.isin({"post-test", "posttest", "postest"}) | fase.str.startswith("post"))
    )
    mask = (
        tipo_fase_valido
        & estado.eq("verificado")
        & df["falla_real"].fillna("").astype(str).str.strip().ne("")
        & df["metodo_confirmacion"].fillna("").astype(str).str.strip().ne("")
        & df["evidencia_ref"].fillna("").astype(str).str.strip().ne("")
        & df["validado_por_id"].fillna("").astype(str).str.strip().ne("")
        & pd.to_datetime(df["fecha_validacion"], errors="coerce").notna()
    )
    return df.loc[mask].copy()


def _serie_binaria(df: pd.DataFrame, columna: str) -> pd.Series:
    if columna not in df.columns:
        return pd.Series(index=df.index, dtype="float64")
    valores = pd.to_numeric(df[columna], errors="coerce")
    return valores.where(valores.isin((0, 1)))


def _serie_predicciones_evaluables(df: pd.DataFrame) -> pd.Series:
    """Solo cuenta resultado cuando existen predicción y falla real en una fila verificada."""
    valores = _serie_binaria(df, "prediccion_correcta")
    if "chatbot_prediccion" not in df.columns:
        return valores.where(False)
    tiene_prediccion = df["chatbot_prediccion"].fillna("").astype(str).str.strip().ne("")
    tiene_falla_real = df.get("falla_real", pd.Series(index=df.index, dtype="string"))
    tiene_falla_real = tiene_falla_real.fillna("").astype(str).str.strip().ne("")
    return valores.where(tiene_prediccion & tiene_falla_real)


@router.get("", summary="Listar registros del tracker experimental en taller (Aislamiento Multitenant)")
async def listar_casos_validacion(
    fase: Optional[str] = Query(None, description="Filtrar por fase: Pre-test o Post-test"),
    tipo_registro: Optional[str] = Query(
        None, description="Filtrar por tipo: DEVELOPMENT, REGRESSION, THESIS_PRETEST, THESIS_POSTTEST"
    ),
    estado_registro: Optional[str] = Query(None, description="Filtrar por estado: verificado o borrador"),
    marca: Optional[str] = Query(None, description="Filtrar por marca/modelo"),
    acierto: Optional[int] = Query(None, ge=0, le=1, description="1 acertados, 0 desacertados"),
    busqueda: Optional[str] = Query(None, description="Término de búsqueda libre"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=200),
    periodo: tuple = Depends(periodo_validacion),
    payload: dict = Depends(exigir_lectura_validacion),
):
    taller_id_auth = payload.get("taller_id", DEFAULT_SEED_TALLER_ID)
    if database_configurada():
        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            return await ServicioValidacionTaller(session).listar(
                _uuid_claim(payload, "taller_id"),
                fase=fase,
                tipo_registro=tipo_registro,
                estado_registro=estado_registro,
                marca=marca,
                acierto=acierto,
                busqueda=busqueda,
                skip=skip,
                limit=limit,
                fecha_desde=periodo[0],
                fecha_hasta=periodo[1],
            )
    df_global = _cargar_df_tracker()
    df = _filtrar_periodo(_filtrar_df_por_taller(df_global, taller_id_auth), periodo)

    if df.empty:
        return {"total": 0, "skip": skip, "limit": limit, "casos": []}

    # Aplicar filtros
    if fase:
        df = df[df["fase"].astype(str).str.lower() == fase.strip().lower()]
    if tipo_registro:
        df = df[df["tipo_registro"] == tipo_registro] if "tipo_registro" in df.columns else df.iloc[0:0]
    if estado_registro:
        df = df[df["estado_registro"] == estado_registro] if "estado_registro" in df.columns else df.iloc[0:0]
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
    df_pagina = df.sort_values(["fecha", "item"], ascending=False, kind="stable").iloc[skip : skip + limit]

    casos_lista = []
    for r in df_pagina.to_dict(orient="records"):
        placa_raw = str(r.get("placa", ""))

        # Recuperar placa_hash persistido si ya existe en el registro
        p_hash_existente = str(r.get("placa_hash", "")).strip() if pd.notna(r.get("placa_hash")) else ""
        if p_hash_existente:
            p_hash = p_hash_existente
            enmascarada = (
                placa_raw if ("-" in placa_raw and "***" in placa_raw) else _pseudonimizar_placa(placa_raw)[0]
            )
        else:
            enmascarada, p_hash = _pseudonimizar_placa(placa_raw)

        fase_registro = str(r.get("fase", ""))
        diagnostico_registrado = (
            str(r.get("chatbot_prediccion")) if pd.notna(r.get("chatbot_prediccion")) else ""
        )
        es_pretest = fase_registro.strip().casefold() in {"pre-test", "pretest"}
        casos_lista.append(
            CasoValidacionDTO(
                item=int(r.get("item", 0)),
                fase=fase_registro,
                fecha=str(r.get("fecha", "")),
                placa_enmascarada=enmascarada,
                placa_hash=p_hash,
                marca_modelo=str(r.get("marca_modelo", "")),
                sintoma=str(r.get("sintoma", "")),
                descripcion_sintoma=str(r.get("descripcion_sintoma", ""))
                if pd.notna(r.get("descripcion_sintoma"))
                else None,
                vehiculo_anio=int(r.get("vehiculo_anio")) if pd.notna(r.get("vehiculo_anio")) else None,
                vehiculo_kilometraje=int(r.get("vehiculo_kilometraje"))
                if pd.notna(r.get("vehiculo_kilometraje"))
                else None,
                vehiculo_combustible=str(r.get("vehiculo_combustible", ""))
                if pd.notna(r.get("vehiculo_combustible"))
                else None,
                vehiculo_transmision=str(r.get("vehiculo_transmision", ""))
                if pd.notna(r.get("vehiculo_transmision"))
                else None,
                falla_real=str(r.get("falla_real")) if pd.notna(r.get("falla_real")) else None,
                chatbot_prediccion=diagnostico_registrado,
                diagnostico_preliminar_sin_chatbot=diagnostico_registrado if es_pretest else None,
                falla_sugerida_chatbot=None if es_pretest else diagnostico_registrado,
                campos_completos=(
                    int(r.get("campos_completos"))
                    if pd.notna(r.get("campos_completos")) and int(r.get("campos_completos")) in (0, 1)
                    else 0
                ),
                cantidad_campos_completos=(
                    int(r.get("cantidad_campos_completos"))
                    if pd.notna(r.get("cantidad_campos_completos"))
                    else 0
                ),
                detalles_campos=r.get("detalles_campos")
                if isinstance(r.get("detalles_campos"), dict)
                else None,
                tiempo_diagnostico_minutos=(
                    int(r.get("tiempo_diagnostico_minutos"))
                    if pd.notna(r.get("tiempo_diagnostico_minutos"))
                    else None
                ),
                prediccion_correcta=(
                    int(r.get("prediccion_correcta"))
                    if pd.notna(r.get("prediccion_correcta")) and int(r.get("prediccion_correcta")) in (0, 1)
                    else None
                ),
                taller_id=str(r.get("taller_id", taller_id_auth)),
                mecanico_id=str(r.get("mecanico_id")) if pd.notna(r.get("mecanico_id")) else None,
                metodo_confirmacion=str(r.get("metodo_confirmacion"))
                if pd.notna(r.get("metodo_confirmacion"))
                else None,
                evidencia_ref=str(r.get("evidencia_ref", "")) if pd.notna(r.get("evidencia_ref")) else None,
                estado_registro=str(r.get("estado_registro"))
                if pd.notna(r.get("estado_registro"))
                else "borrador",
                tipo_registro=str(r.get("tipo_registro"))
                if pd.notna(r.get("tipo_registro"))
                else "DEVELOPMENT",
                conversacion_id=str(r.get("conversacion_id", ""))
                if pd.notna(r.get("conversacion_id"))
                else None,
                diagnostico_id=str(r.get("diagnostico_id", ""))
                if pd.notna(r.get("diagnostico_id"))
                else None,
                validado_por_id=str(r.get("validado_por_id")) if pd.notna(r.get("validado_por_id")) else None,
                fecha_validacion=str(r.get("fecha_validacion"))
                if pd.notna(r.get("fecha_validacion"))
                else None,
            )
        )

    return {
        "total": total_filtrado,
        "skip": skip,
        "limit": limit,
        "casos": [c.model_dump() for c in casos_lista],
    }


@router.get(
    "/metricas",
    response_model=MetricasValidacionResponseDTO,
    summary="Obtener KPIs del seguimiento experimental por taller",
)
async def obtener_metricas_validacion(
    periodo: tuple = Depends(periodo_validacion),
    payload: dict = Depends(exigir_lectura_validacion),
):
    taller_id_auth = payload.get("taller_id", DEFAULT_SEED_TALLER_ID)
    if database_configurada():
        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            metricas = await ServicioValidacionTaller(session).metricas(
                _uuid_claim(payload, "taller_id"), *periodo
            )
        return MetricasValidacionResponseDTO(**metricas)
    df_global = _cargar_df_tracker()
    df_taller = _filtrar_periodo(_filtrar_df_por_taller(df_global, taller_id_auth), periodo)
    df = _filtrar_df_oficial_verificado(df_taller)
    fases = (
        df["fase"].astype(str).str.casefold()
        if "fase" in df.columns
        else pd.Series(index=df.index, dtype="string")
    )
    df_pre = df[fases.isin({"pre-test", "pretest"})]
    df_post = df[fases.isin({"post-test", "posttest"})]

    def binaria(filas: pd.DataFrame, columna: str) -> pd.Series:
        return _serie_binaria(filas, columna)

    def porcentaje(valores: pd.Series) -> float | None:
        observados = valores.dropna()
        return round(float(observados.mean()) * 100, 2) if not observados.empty else None

    def tiempo_medido(filas: pd.DataFrame) -> tuple[float | None, int]:
        if "tiempo_diagnostico_minutos" not in filas.columns:
            return None, 0
        valores = pd.to_numeric(filas["tiempo_diagnostico_minutos"], errors="coerce")
        validos = valores[valores > 0]
        return (round(float(validos.mean()), 1), int(validos.count())) if not validos.empty else (None, 0)

    aciertos_pre = _serie_predicciones_evaluables(df_pre)
    aciertos_post = _serie_predicciones_evaluables(df_post)
    todos_aciertos = pd.concat([aciertos_pre, aciertos_post])
    evaluados_pre = int(aciertos_pre.count())
    evaluados_post = int(aciertos_post.count())
    aciertos = int(todos_aciertos.fillna(0).sum())
    predicciones_evaluadas = evaluados_pre + evaluados_post
    tiempo_pre, tiempos_pre = tiempo_medido(df_pre)
    tiempo_post, tiempos_post = tiempo_medido(df_post)
    reduccion_tiempo = (
        round((tiempo_pre - tiempo_post) / tiempo_pre * 100, 2)
        if tiempo_pre is not None and tiempo_post is not None and tiempo_pre > 0
        else None
    )

    def porcentaje_completitud(filas: pd.DataFrame) -> float | None:
        if filas.empty:
            return None
        return porcentaje(binaria(filas, "campos_completos"))

    campos_pre_evaluados = int(binaria(df_pre, "campos_completos").count())
    campos_post_evaluados = int(binaria(df_post, "campos_completos").count())

    # Los indicadores de CarBot se reportan solo en POST-TEST; el PRE-TEST es línea base manual.
    sintomas = binaria(df_post, "sintoma_registrado_correctamente")
    if "procesamiento_validado" in df_post.columns:
        procesamiento = binaria(df_post, "procesamiento_validado")
    elif {"normalizacion_correcta", "extraccion_correcta", "clasificacion_procesada"}.issubset(
        df_post.columns
    ):
        normalizacion = binaria(df_post, "normalizacion_correcta")
        extraccion = binaria(df_post, "extraccion_correcta")
        clasificacion = binaria(df_post, "clasificacion_procesada")
        validos = normalizacion.notna() & extraccion.notna() & clasificacion.notna()
        procesamiento = pd.Series(index=df_post.index, dtype="float64")
        procesamiento.loc[validos] = (
            (normalizacion.loc[validos] == 1)
            & (extraccion.loc[validos] == 1)
            & (clasificacion.loc[validos] == 1)
        ).astype(int)
    else:
        procesamiento = pd.Series(index=df_post.index, dtype="float64")
    predicciones_post = aciertos_post
    vi_metricas = MetricasVariableIndependienteDTO(
        indicador1_sintomas_correctos_pct=porcentaje(sintomas),
        indicador2_procesamiento_correcto_pct=porcentaje(procesamiento),
        indicador3_exactitud_ml_pct=porcentaje(predicciones_post),
        casos_verificados_evaluados=len(df_post),
        casos_sintomas_evaluados=int(sintomas.count()),
        casos_procesamiento_evaluados=int(procesamiento.count()),
        casos_modelo_evaluados=evaluados_post,
        nota_metodologica=(
            "Indicadores de CarBot calculados solo sobre casos POST-TEST oficiales con "
            "revisión humana trazable; no incluyen el diagnóstico manual PRE-TEST."
            if not df_post.empty
            else "Pendiente de registros POST-TEST oficiales con revisión humana trazable."
        ),
    )

    candidatos_oficiales = df_taller
    if "tipo_registro" in candidatos_oficiales.columns and "estado_registro" in candidatos_oficiales.columns:
        candidatos_oficiales = candidatos_oficiales[
            candidatos_oficiales["tipo_registro"].isin(("THESIS_PRETEST", "THESIS_POSTTEST"))
        ]
        borradores = int(
            candidatos_oficiales["estado_registro"].fillna("").astype(str).str.casefold().eq("borrador").sum()
        )
    else:
        borradores = 0
    casos_piloto = (
        int(df_taller["tipo_registro"].eq("PILOT").sum()) if "tipo_registro" in df_taller.columns else 0
    )
    dist_marcas = (
        [{"marca": str(k), "conteo": int(v)} for k, v in df["marca_modelo"].value_counts().head(8).items()]
        if "marca_modelo" in df.columns
        else []
    )
    top_fallas = (
        [{"falla": str(k), "conteo": int(v)} for k, v in df["falla_real"].value_counts().head(8).items()]
        if "falla_real" in df.columns
        else []
    )
    return MetricasValidacionResponseDTO(
        total_casos=len(df),
        total_aciertos=aciertos,
        total_desaciertos=predicciones_evaluadas - aciertos,
        tasa_acierto_global_porcentaje=porcentaje(todos_aciertos),
        casos_pretest=len(df_pre),
        predicciones_evaluadas_pretest=evaluados_pre,
        tasa_acierto_pretest_porcentaje=porcentaje(aciertos_pre),
        tiempos_evaluados_pretest=tiempos_pre,
        tiempo_promedio_pretest_min=tiempo_pre,
        registros_completos_pretest_porcentaje=porcentaje_completitud(df_pre),
        registros_prdc_evaluados_pretest=campos_pre_evaluados,
        casos_posttest=len(df_post),
        predicciones_evaluadas_posttest=evaluados_post,
        tasa_acierto_posttest_porcentaje=porcentaje(aciertos_post),
        tiempos_evaluados_posttest=tiempos_post,
        tiempo_promedio_posttest_min=tiempo_post,
        registros_completos_posttest_porcentaje=porcentaje_completitud(df_post),
        registros_prdc_evaluados_posttest=campos_post_evaluados,
        reduccion_tiempo_porcentaje=reduccion_tiempo,
        casos_piloto=casos_piloto,
        casos_verificados=len(df_post),
        total_casos_verificados=len(df),
        total_casos_borrador=borradores,
        porcentaje_sintomas_correctos=vi_metricas.indicador1_sintomas_correctos_pct,
        porcentaje_datos_procesados_correctos=vi_metricas.indicador2_procesamiento_correcto_pct,
        exactitud_modelo_validada=vi_metricas.indicador3_exactitud_ml_pct,
        variable_independiente=vi_metricas,
        distribucion_marcas=dist_marcas,
        top_fallas_reales=top_fallas,
        nota_metodologica=(
            "Se incluyen solo registros THESIS_PRETEST/THESIS_POSTTEST verificados con autor, fecha, "
            "método y referencia de evidencia explícitos. La referencia no acredita por sí sola una "
            "prueba física; la revisión corresponde a la persona autorizada."
        ),
    )


@router.post(
    "",
    response_model=CasoValidacionDTO,
    status_code=201,
    summary="Registrar nuevo caso en el tracker con escritura atómica",
)
async def registrar_caso_validacion(
    dto: CrearCasoValidacionDTO,
    payload: dict = Depends(exigir_gestion_validacion),
):
    if database_configurada():
        enmascarada, p_hash = _pseudonimizar_placa(dto.placa)
        try:
            async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
                async with session.begin():
                    caso = await ServicioValidacionTaller(session).crear(
                        _uuid_claim(payload, "taller_id"),
                        _uuid_claim(payload, "usuario_id", obligatorio=False),
                        dto,
                        enmascarada,
                        p_hash,
                    )
                return CasoValidacionDTO(**serializar_caso(caso))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if dto.tipo_registro in {"THESIS_PRETEST", "THESIS_POSTTEST", "PILOT"}:
        raise HTTPException(
            status_code=503,
            detail="Los registros PILOT y oficiales requieren PostgreSQL y su trazabilidad transaccional.",
        )

    async with _ASYNC_CSV_LOCK:
        try:
            with _bloqueo_archivo_interproceso(TRACKER_CSV_PATH):
                df = _cargar_df_tracker()
                siguiente_item = int(df["item"].max()) + 1 if not df.empty and "item" in df.columns else 1
                fecha_hoy = dto.fecha or datetime.now(LIMA_TZ).strftime("%Y-%m-%d")
                taller_id = payload.get("taller_id", DEFAULT_SEED_TALLER_ID)
                mecanico_id = payload.get("usuario_id", payload.get("sub", ""))

                enmascarada, p_hash = _pseudonimizar_placa(dto.placa)
                sistema_probable = (dto.sistema_afectado_probable or "").strip() or None
                descripcion_sintoma = (dto.descripcion_sintoma or "").strip()
                datos_generales_vehiculo = construir_datos_generales_vehiculo(
                    marca_modelo=dto.marca_modelo,
                    anio=dto.vehiculo_anio,
                    kilometraje=dto.vehiculo_kilometraje,
                    combustible=dto.vehiculo_combustible,
                    transmision=dto.vehiculo_transmision,
                )
                campos_completos, cantidad_campos, detalles_campos = calcular_detalles_campos_ficha2(
                    codigo_registro=siguiente_item,
                    fecha_atencion=fecha_hoy,
                    datos_generales_vehiculo=datos_generales_vehiculo,
                    sintomas_reportados=dto.sintoma,
                    descripcion_sintoma=descripcion_sintoma,
                    sistema_afectado_probable=sistema_probable,
                    diagnostico_confirmado=dto.falla_real,
                    tiempo_atencion_minutos=dto.tiempo_diagnostico_minutos,
                )

                estado_solicitado = dto.estado_registro
                tiene_revision_humana = bool(
                    mecanico_id
                    and dto.falla_real.strip()
                    and dto.prediccion_correcta in (0, 1)
                    and dto.tiempo_diagnostico_minutos > 0
                    and dto.metodo_confirmacion
                    and dto.metodo_confirmacion.strip()
                    and dto.evidencia_ref
                    and dto.evidencia_ref.strip()
                )
                estado_final = (
                    "verificado"
                    if estado_solicitado == "verificado" and tiene_revision_humana
                    else "borrador"
                )
                nuevo_registro = {
                    "item": siguiente_item,
                    "fase": dto.fase,
                    "fecha": fecha_hoy,
                    "placa": enmascarada,
                    "placa_hash": p_hash,
                    "marca_modelo": dto.marca_modelo.strip(),
                    "sintoma": dto.sintoma.strip(),
                    "descripcion_sintoma": descripcion_sintoma,
                    "vehiculo_anio": dto.vehiculo_anio,
                    "vehiculo_kilometraje": dto.vehiculo_kilometraje,
                    "vehiculo_combustible": (dto.vehiculo_combustible or "").strip(),
                    "vehiculo_transmision": (dto.vehiculo_transmision or "").strip(),
                    "falla_real": dto.falla_real.strip(),
                    "chatbot_prediccion": dto.chatbot_prediccion.strip(),
                    "sistema_afectado_probable": sistema_probable,
                    "campos_completos": campos_completos,
                    "cantidad_campos_completos": cantidad_campos,
                    "detalles_campos": detalles_campos,
                    "tiempo_diagnostico_minutos": dto.tiempo_diagnostico_minutos,
                    "prediccion_correcta": dto.prediccion_correcta,
                    "taller_id": taller_id,
                    "mecanico_id": mecanico_id,
                    "metodo_confirmacion": (dto.metodo_confirmacion or "").strip(),
                    "evidencia_ref": dto.evidencia_ref or "",
                    "estado_registro": estado_final,
                    "tipo_registro": (
                        dto.tipo_registro
                        or (
                            "THESIS_POSTTEST"
                            if estado_final == "verificado" and "post" in dto.fase.lower()
                            else (
                                "THESIS_PRETEST"
                                if estado_final == "verificado" and "pre" in dto.fase.lower()
                                else "DEVELOPMENT"
                            )
                        )
                    ),
                    "validado_por_id": mecanico_id if estado_final == "verificado" else None,
                    "fecha_validacion": datetime.now(LIMA_TZ).isoformat()
                    if estado_final == "verificado"
                    else None,
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
                detail="El tracker se encuentra ocupado procesando otra escritura. Intente nuevamente en unos segundos.",
            ) from exc

        return CasoValidacionDTO(
            item=siguiente_item,
            fase=dto.fase,
            fecha=fecha_hoy,
            placa_enmascarada=enmascarada,
            placa_hash=p_hash,
            marca_modelo=dto.marca_modelo.strip(),
            sintoma=dto.sintoma.strip(),
            descripcion_sintoma=descripcion_sintoma or None,
            vehiculo_anio=dto.vehiculo_anio,
            vehiculo_kilometraje=dto.vehiculo_kilometraje,
            vehiculo_combustible=(dto.vehiculo_combustible or "").strip() or None,
            vehiculo_transmision=(dto.vehiculo_transmision or "").strip() or None,
            falla_real=dto.falla_real.strip(),
            chatbot_prediccion=dto.chatbot_prediccion.strip(),
            sistema_afectado_probable=sistema_probable,
            campos_completos=campos_completos,
            cantidad_campos_completos=cantidad_campos,
            detalles_campos=detalles_campos,
            tiempo_diagnostico_minutos=dto.tiempo_diagnostico_minutos,
            prediccion_correcta=dto.prediccion_correcta,
            taller_id=taller_id,
            mecanico_id=mecanico_id,
            metodo_confirmacion=(dto.metodo_confirmacion or "").strip() or None,
            evidencia_ref=(dto.evidencia_ref or "").strip() or None,
            estado_registro=nuevo_registro["estado_registro"],
            tipo_registro=nuevo_registro["tipo_registro"],
            validado_por_id=nuevo_registro["validado_por_id"],
            fecha_validacion=nuevo_registro["fecha_validacion"],
        )


@router.get(
    "/exportar-csv",
    summary="Descargar CSV sanitizado contra inyecciones de fórmulas (Aislamiento Multitenant)",
)
async def exportar_tracker_csv(
    periodo: tuple = Depends(periodo_validacion),
    payload: dict = Depends(exigir_lectura_validacion),
):
    taller_id_auth = payload.get("taller_id", DEFAULT_SEED_TALLER_ID)
    if database_configurada():
        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            casos = await ValidacionTallerRepository(session).listar_todos(
                _uuid_claim(payload, "taller_id"), *periodo
            )
        filas = [serializar_caso(caso) for caso in casos]
        df = pd.DataFrame(filas)
    else:
        df_global = _cargar_df_tracker()
        df = _filtrar_periodo(_filtrar_df_por_taller(df_global, taller_id_auth), periodo)
        df = df.sort_values(["fecha", "item"], kind="stable")

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


@router.get(
    "/exportar-fichas-anexo2-csv",
    summary="Descargar CSV oficial de Anexo 2 con todos los casos reales verificados (sin paginación)",
)
async def exportar_fichas_anexo2_csv(
    periodo: tuple = Depends(periodo_validacion),
    payload: dict = Depends(exigir_lectura_validacion),
):
    fecha_desde, fecha_hasta = periodo
    taller_id_auth = payload.get("taller_id", DEFAULT_SEED_TALLER_ID)

    if database_configurada():
        taller_uuid = _uuid_claim(payload, "taller_id")
        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            casos = await ValidacionTallerRepository(session).listar_todos(
                taller_uuid, *periodo, solo_verificados=True
            )
        registros = [serializar_caso(c) for c in casos]
    else:
        df_global = _cargar_df_tracker()
        df = _filtrar_periodo(_filtrar_df_por_taller(df_global, taller_id_auth), periodo)
        df = _filtrar_df_oficial_verificado(df)
        registros = df.to_dict(orient="records")

    if not registros:
        raise HTTPException(
            status_code=400,
            detail="No existen registros verificados para exportar en el periodo seleccionado.",
        )

    total_casos = len(registros)
    pre_count = sum(1 for r in registros if str(r.get("tipo_registro")) == "THESIS_PRETEST")
    post_count = sum(1 for r in registros if str(r.get("tipo_registro")) == "THESIS_POSTTEST")
    estado_muestra = (
        "MUESTRA OBJETIVO COMPLETA (30/30 PRE-TEST y 30/30 POST-TEST)"
        if pre_count == 30 and post_count == 30
        else f"TRABAJO DE CAMPO PENDIENTE ({pre_count}/30 PRE-TEST; {post_count}/30 POST-TEST)"
    )

    output = io.StringIO()
    output.write(
        "# =================================================================================================\n"
    )
    output.write("# UNIVERSIDAD CÉSAR VALLEJO - ESCUELA DE INGENIERÍA DE SISTEMAS\n")
    output.write(
        "# TESIS: CHATBOT UTILIZANDO MACHINE LEARNING PARA EL DIAGNÓSTICO VEHICULAR (CARTER MOTOR'S E.I.R.L.)\n"
    )
    output.write("# ANEXO 2: MATRIZ DE RECOLECCIÓN DE DATOS EXPERIMENTALES (PRETEST Y POSTEST)\n")
    output.write(
        "# =================================================================================================\n"
    )
    output.write(f"# Total casos verificados exportados: {total_casos}\n")
    output.write(f"# Registros oficiales PRE-TEST: {pre_count}/30; POST-TEST: {post_count}/30\n")
    output.write(f"# Periodo evaluado: {fecha_desde or 'Histórico'} a {fecha_hasta or 'Actualidad'}\n")
    output.write(f"# Estado de la muestra oficial: {estado_muestra}\n")
    output.write(
        "# NOTA METODOLÓGICA: El contraste de hipótesis inferencial (pretest vs. postest) queda estrictamente\n"
    )
    output.write(
        "# pendiente de definición con el asesor estadístico según la distribución y naturaleza de la muestra.\n"
    )
    output.write(
        "# Se prohíbe el uso de datos sintéticos o valores simulados para conclusiones formales de la tesis.\n"
    )
    output.write(
        "# =================================================================================================\n"
    )

    columnas_export = [
        "Item",
        "Fase",
        "Tipo_Registro",
        "Fecha",
        "Placa_Enmascarada",
        "Marca_Modelo",
        "Sintoma_Reportado",
        "Descripcion_Sintoma",
        "Vehiculo_Anio",
        "Vehiculo_Kilometraje",
        "Vehiculo_Combustible",
        "Vehiculo_Transmision",
        "Falla_Confirmada_Fisica",
        "Diagnostico_Preliminar_Sin_Chatbot",
        "Falla_Sugerida_Chatbot",
        "Prediccion_Linear_SVM",
        "PPCF_Ficha1_Prediccion_Correcta",
        "PRDC_Ficha2_Campos_Completos",
        "Ficha2_Cantidad_Campos_Completos",
        "Ficha2_Campo1_Codigo_Registro",
        "Ficha2_Campo2_Fecha_Atencion",
        "Ficha2_Campo3_Datos_Generales_Vehiculo",
        "Ficha2_Campo4_Sintomas_Reportados",
        "Ficha2_Campo5_Descripcion_Sintoma",
        "Ficha2_Campo6_Sistema_Afectado_Probable",
        "Ficha2_Campo7_Diagnostico_Confirmado",
        "Ficha2_Campo8_Tiempo_Atencion_Registrado",
        "TPRD_Ficha3_Tiempo_Minutos",
        "Ind1_Sintoma_Validado",
        "Ind2_Procesamiento_Validado",
        "Metodo_Confirmacion",
        "Evidencia_Referencia",
        "Validador_ID",
        "Fecha_Validacion",
        "Estado_Registro",
    ]

    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(columnas_export)

    for r in registros:
        detalles = r.get("detalles_campos") if isinstance(r.get("detalles_campos"), dict) else {}

        def campo_completo(clave: str) -> str:
            campo = detalles.get(clave) if isinstance(detalles.get(clave), dict) else {}
            if not campo or "completo" not in campo:
                return ""
            return "1" if campo.get("completo") else "0"

        es_pretest = str(r.get("fase", "")).strip().casefold() in {"pre-test", "pretest"}
        diagnostico_preliminar = r.get("chatbot_prediccion", "") if es_pretest else ""
        falla_sugerida = r.get("chatbot_prediccion", "") if not es_pretest else ""

        fila = [
            _sanitizar_campo_csv(r.get("item", "")),
            _sanitizar_campo_csv(r.get("fase", "")),
            _sanitizar_campo_csv(r.get("tipo_registro", "")),
            _sanitizar_campo_csv(r.get("fecha", "")),
            _sanitizar_campo_csv(r.get("placa_enmascarada", "")),
            _sanitizar_campo_csv(r.get("marca_modelo", "")),
            _sanitizar_campo_csv(r.get("sintoma", "")),
            _sanitizar_campo_csv(r.get("descripcion_sintoma", "")),
            _sanitizar_campo_csv(r.get("vehiculo_anio", "")),
            _sanitizar_campo_csv(r.get("vehiculo_kilometraje", "")),
            _sanitizar_campo_csv(r.get("vehiculo_combustible", "")),
            _sanitizar_campo_csv(r.get("vehiculo_transmision", "")),
            _sanitizar_campo_csv(r.get("falla_real", "")),
            _sanitizar_campo_csv(diagnostico_preliminar),
            _sanitizar_campo_csv(falla_sugerida),
            _sanitizar_campo_csv(falla_sugerida if not es_pretest else ""),
            _sanitizar_campo_csv(r.get("prediccion_correcta", "")),
            _sanitizar_campo_csv(r.get("campos_completos", "")),
            _sanitizar_campo_csv(r.get("cantidad_campos_completos", 0)),
            _sanitizar_campo_csv(campo_completo("campo_1")),
            _sanitizar_campo_csv(campo_completo("campo_2")),
            _sanitizar_campo_csv(campo_completo("campo_3")),
            _sanitizar_campo_csv(campo_completo("campo_4")),
            _sanitizar_campo_csv(campo_completo("campo_5")),
            _sanitizar_campo_csv(campo_completo("campo_6")),
            _sanitizar_campo_csv(campo_completo("campo_7")),
            _sanitizar_campo_csv(campo_completo("campo_8")),
            _sanitizar_campo_csv(r.get("tiempo_diagnostico_minutos", "")),
            _sanitizar_campo_csv(r.get("sintoma_registrado_correctamente", "")),
            _sanitizar_campo_csv(r.get("procesamiento_validado", "")),
            _sanitizar_campo_csv(r.get("metodo_confirmacion", "")),
            _sanitizar_campo_csv(r.get("evidencia_ref", "")),
            _sanitizar_campo_csv(r.get("validado_por_id", "") or r.get("mecanico_id", "")),
            _sanitizar_campo_csv(r.get("fecha_validacion", "")),
            _sanitizar_campo_csv(r.get("estado_registro", "")),
        ]
        writer.writerow(fila)

    output.seek(0)
    filename = f"anexo2_fichas_oficiales_taller_{datetime.now(LIMA_TZ).strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
