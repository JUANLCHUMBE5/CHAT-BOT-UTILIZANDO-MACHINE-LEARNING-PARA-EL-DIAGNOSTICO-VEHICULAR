"""Endpoints de registro experimental y seguimiento de diagnósticos en taller automotriz."""

from __future__ import annotations

import asyncio
import csv
import hashlib
import hmac
import io
import re
import uuid
from datetime import date, datetime
from typing import Optional
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
from src.infrastructure.database.repositories.tracker_csv import (
    _bloqueo_archivo_interproceso as _bloqueo_archivo_interproceso,
)
from src.infrastructure.database.repositories.tracker_csv import (
    _guardar_df_tracker_atomico as _guardar_df_tracker_atomico,
)
from src.infrastructure.database.repositories.validacion_taller_repository import ValidacionTallerRepository
from src.interfaces.api.v1.dtos.validacion import (
    CasoValidacionDTO,
    CrearCasoValidacionDTO,
    MetricasValidacionResponseDTO,
)
from src.interfaces.api.v1.presenters.casos_csv import presentar_casos_csv
from src.interfaces.api.v1.presenters.fichas_csv import (
    _sanitizar_campo_csv as _sanitizar_campo_csv,
)
from src.interfaces.api.v1.presenters.fichas_csv import (
    construir_fichas_csv,
)
from src.interfaces.api.v1.presenters.metricas_csv import (
    _filtrar_df_oficial_verificado as _filtrar_df_oficial_verificado,
)
from src.interfaces.api.v1.presenters.metricas_csv import (
    _serie_binaria as _serie_binaria,
)
from src.interfaces.api.v1.presenters.metricas_csv import (
    _serie_predicciones_evaluables as _serie_predicciones_evaluables,
)
from src.interfaces.api.v1.presenters.metricas_csv import (
    presentar_metricas_csv,
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

    return presentar_casos_csv(
        df,
        taller_id_auth,
        _pseudonimizar_placa,
        fase=fase,
        tipo_registro=tipo_registro,
        estado_registro=estado_registro,
        marca=marca,
        acierto=acierto,
        busqueda=busqueda,
        skip=skip,
        limit=limit,
    )


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
    return presentar_metricas_csv(df_taller)


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
                    "metodo_confirmacion": (dto.metodo_confirmacion or "").strip() or None,
                    "evidencia_ref": dto.evidencia_ref or "",
                    "estado_registro": estado_final,
                    "tipo_registro": dto.tipo_registro or "DEVELOPMENT",
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

    output = construir_fichas_csv(registros, fecha_desde, fecha_hasta)
    filename = f"anexo2_fichas_oficiales_taller_{datetime.now(LIMA_TZ).strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
