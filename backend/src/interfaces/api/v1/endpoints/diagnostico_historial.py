"""Lectura y actualización autorizadas del historial diagnóstico."""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.authorization import (
    exigir_confirmacion_diagnosticos,
    exigir_lectura_diagnosticos,
)
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.mensaje_repository import MensajeRepository
from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository
from src.infrastructure.database.repositories.vehiculo_repository import VehiculoRepository, normalizar_placa
from src.interfaces.api.v1.dtos.diagnosticos import (
    ActualizarEstadoDTO,
    ItemDiagnosticoDTO,
    MensajeConversacionDTO,
)
from src.interfaces.api.v1.dtos.fechas import fecha_hora_peru
from src.interfaces.api.v1.dtos.historial_diagnostico import (
    _es_procedimiento_rag_real as _es_procedimiento_rag_real,
)
from src.interfaces.api.v1.dtos.historial_diagnostico import (
    presentar_historial,
)

router = APIRouter()


@router.get("/historial", response_model=List[ItemDiagnosticoDTO], summary="Consultar historial de diagnósticos del taller")
async def consultar_historial(
    response: Response,
    busqueda: Optional[str] = None,
    estado: Optional[str] = None,
    modo: Optional[str] = None,
    mecanico_id: Optional[uuid.UUID] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    limite: Optional[int] = Query(10, ge=1, le=1000, description="Límite de registros a retornar"),
    offset: Optional[int] = Query(0, ge=0, description="Desplazamiento para paginación"),
    token_payload: dict = Depends(exigir_lectura_diagnosticos),
):
    """Retorna la lista de diagnósticos registrados en PostgreSQL filtrando por taller_id y query params."""
    taller_id_str = token_payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)

    if database_configurada():
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            diag_repo = DiagnosticoRepository(session)
            diag_db_list = await diag_repo.listar_por_taller(
                taller_id=taller_uuid,
                busqueda=busqueda,
                estado=estado,
                modo=modo,
                mecanico_id=mecanico_id,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                limite=limite,
                offset=offset or 0,
            )
            total = await diag_repo.contar_por_taller(
                taller_id=taller_uuid,
                busqueda=busqueda,
                estado=estado,
                modo=modo,
                mecanico_id=mecanico_id,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
            )
            response.headers["X-Total-Count"] = str(total)
            return presentar_historial(diag_db_list)

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")


@router.get("/vehiculos/{placa}/historial", summary="Historial exacto por placa")
async def consultar_historial_por_placa(
    placa: str,
    token_payload: dict = Depends(exigir_lectura_diagnosticos),
):
    """Busca por HMAC normalizado, sin devolver ni persistir la placa completa."""
    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
    try:
        placa_normalizada = normalizar_placa(placa)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    taller_id = uuid.UUID(token_payload["taller_id"])
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        vehiculo = await VehiculoRepository(session).buscar_por_placa(taller_id, placa_normalizada)
        if vehiculo is None:
            return {"placa": "no_encontrada", "diagnosticos": []}
        diagnosticos = await DiagnosticoRepository(session).listar_por_vehiculo(taller_id, vehiculo.id)
        return {
            "placa": f"***-{vehiculo.placa_ultimos4}", "vehiculo_id": str(vehiculo.id),
            "diagnosticos": [
                {"id": str(diag.id), "fecha": diag.creado_en.isoformat(), "sintoma": diag.sintoma_original,
                 "prediccion": diag.falla_predicha, "estado": diag.estado, "tipo_registro": diag.tipo_registro,
                 "duracion_ms": diag.duracion_ms}
                for diag in diagnosticos
            ],
        }


@router.patch("/{diagnostico_id}/confirmar", summary="Confirmar o modificar estado de diagnóstico")
async def confirmar_diagnostico(
    diagnostico_id: str,
    dto: ActualizarEstadoDTO,
    token_payload: dict = Depends(exigir_confirmacion_diagnosticos),
):
    """Actualiza el estado de validación mecánica en PostgreSQL verificando taller_id y restricciones de enum."""
    taller_id_str = token_payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)

    if database_configurada():
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            diag_repo = DiagnosticoRepository(session)
            diag = await diag_repo.obtener_por_id(uuid.UUID(diagnostico_id))
            if not diag or diag.taller_id != taller_uuid:
                raise HTTPException(status_code=404, detail="Diagnóstico no encontrado en este taller.")

            diag.estado = dto.nuevo_estado
            if dto.notas_mecanico:
                diag.conclusion_mecanico = dto.notas_mecanico

            usuario_id = token_payload.get("usuario_id")
            await OperacionesRepository(session).registrar_auditoria(
                accion="confirmar_diagnostico",
                entidad="diagnostico",
                entidad_id=diag.id,
                taller_id=taller_uuid,
                usuario_id=uuid.UUID(str(usuario_id)) if usuario_id else None,
                detalles={"estado_nuevo": dto.nuevo_estado},
            )

            await session.commit()
            return {"mensaje": f"Diagnóstico {diagnostico_id} actualizado a {dto.nuevo_estado} en PostgreSQL."}

    raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")


@router.get(
    "/{diagnostico_id}/conversacion",
    response_model=List[MensajeConversacionDTO],
    summary="Obtener trazabilidad cronológica de mensajes de la conversación del diagnóstico",
)
async def obtener_conversacion_diagnostico(
    diagnostico_id: str,
    token_payload: dict = Depends(exigir_lectura_diagnosticos),
):
    """Retorna los mensajes cronológicos reales asociados a la conversación de un diagnóstico."""
    try:
        diag_uuid = uuid.UUID(diagnostico_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de diagnóstico inválido.")

    taller_id_str = token_payload.get("taller_id", "00000000-0000-0000-0000-000000000001")
    taller_uuid = uuid.UUID(taller_id_str)

    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")

    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        diag_repo = DiagnosticoRepository(session)
        diag = await diag_repo.obtener_por_id(diag_uuid)
        if not diag or diag.taller_id != taller_uuid:
            raise HTTPException(status_code=404, detail="Diagnóstico no encontrado en este taller.")

        if not diag.conversacion_id:
            return []

        msg_repo = MensajeRepository(session)
        mensajes = await msg_repo.listar_por_conversacion(diag.conversacion_id, limite=50)
        return [
            MensajeConversacionDTO(
                id=str(m.id),
                direccion=m.direccion,
                texto=m.texto,
                tipo=m.tipo,
                fecha_hora=fecha_hora_peru(m.ocurrido_en) if m.ocurrido_en else "Reciente",
            )
            for m in mensajes
        ]
