"""Registro humano y aislado de los casos oficiales POST-TEST."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.validacion_taller import (
    calcular_detalles_campos_ficha2,
    construir_datos_generales_vehiculo,
    serializar_caso,
)
from src.core.authorization import exigir_gestion_validacion
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.models.validation import ValidacionTaller
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.validacion_taller_repository import ValidacionTallerRepository

router = APIRouter()


class ConfirmacionHumanaPostTestDTO(BaseModel):
    falla_real: str = Field(min_length=3, max_length=1000)
    tiempo_diagnostico_minutos: int = Field(ge=1, le=600)
    prediccion_correcta: int = Field(ge=0, le=1)
    metodo_confirmacion: str = Field(min_length=3, max_length=500)
    evidencia_ref: str | None = Field(default=None, max_length=500)


def _claims(payload: dict) -> tuple[uuid.UUID, uuid.UUID | None]:
    try:
        taller = uuid.UUID(str(payload["taller_id"]))
        usuario = uuid.UUID(str(payload["usuario_id"])) if payload.get("usuario_id") else None
        return taller, usuario
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Token sin identidad de taller válida.") from exc


@router.post("/desde-diagnostico/{diagnostico_id}", status_code=201)
async def crear_borrador_posttest(diagnostico_id: uuid.UUID, payload: dict = Depends(exigir_gestion_validacion)):
    """Autollenado desde CarBot. No rellena confirmación ni métricas humanas."""
    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
    taller_id, usuario_id = _claims(payload)
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        async with session.begin():
            diagnostico = await DiagnosticoRepository(session).obtener_por_id(diagnostico_id)
            if not diagnostico or diagnostico.taller_id != taller_id or not diagnostico.vehiculo:
                raise HTTPException(status_code=404, detail="Diagnóstico con vehículo identificado no encontrado.")
            existente = await session.execute(select(ValidacionTaller).where(ValidacionTaller.diagnostico_id == diagnostico_id))
            if existente.scalar_one_or_none():
                raise HTTPException(status_code=409, detail="El diagnóstico ya tiene un borrador POST-TEST.")
            v = diagnostico.vehiculo
            datos = construir_datos_generales_vehiculo(
                marca_modelo=f"{v.marca} {v.modelo}", anio=v.anio, kilometraje=v.kilometraje,
                combustible=v.combustible, transmision=None,
            )
            completo, cantidad, detalles = calcular_detalles_campos_ficha2(
                codigo_registro="pendiente", fecha_atencion=date.today(), datos_generales_vehiculo=datos,
                sintomas_reportados=diagnostico.sintoma_original, descripcion_sintoma=diagnostico.sintoma_normalizado,
                sistema_afectado_probable=diagnostico.falla_predicha, diagnostico_confirmado=None,
                tiempo_atencion_minutos=None,
            )
            caso = await ValidacionTallerRepository(session).crear(
                taller_id=taller_id, mecanico_id=usuario_id, fase="Post-test", fecha=date.today(),
                placa_enmascarada=f"***-{v.placa_ultimos4}", placa_hash=v.placa_hash,
                marca_modelo=f"{v.marca} {v.modelo}", sintoma=diagnostico.sintoma_original,
                descripcion_sintoma=diagnostico.sintoma_normalizado, vehiculo_anio=v.anio,
                vehiculo_kilometraje=v.kilometraje, vehiculo_combustible=v.combustible,
                vehiculo_transmision=None, falla_real=None,
                chatbot_prediccion=diagnostico.falla_predicha or "Sin predicción registrada",
                sistema_afectado_probable=diagnostico.falla_predicha, campos_completos=completo,
                cantidad_campos_completos=cantidad, detalles_campos=detalles, tiempo_diagnostico_minutos=None,
                prediccion_correcta=None, metodo_confirmacion=None, evidencia_ref=None,
                estado_registro="borrador", tipo_registro="THESIS_POSTTEST",
                conversacion_id=diagnostico.conversacion_id, diagnostico_id=diagnostico.id,
                tiempo_inferencia_ml_ms=diagnostico.tiempo_inferencia_ml_ms,
                inicio_sistema_at=diagnostico.creado_en,
                duracion_sistema_segundos=(diagnostico.duracion_ms or 0) / 1000,
            )
            diagnostico.tipo_registro = "THESIS_POSTTEST"
        return {"id": str(caso.id), **serializar_caso(caso)}


@router.patch("/{caso_id}/confirmacion-humana")
async def confirmar_posttest(caso_id: uuid.UUID, dto: ConfirmacionHumanaPostTestDTO, payload: dict = Depends(exigir_gestion_validacion)):
    """Solo una persona registra falla real, tiempo diagnóstico y acierto SI/NO."""
    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
    taller_id, usuario_id = _claims(payload)
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        async with session.begin():
            caso = await session.get(ValidacionTaller, caso_id, with_for_update=True)
            if not caso or caso.taller_id != taller_id or caso.tipo_registro != "THESIS_POSTTEST":
                raise HTTPException(status_code=404, detail="Borrador POST-TEST no encontrado.")
            datos = construir_datos_generales_vehiculo(marca_modelo=caso.marca_modelo, anio=caso.vehiculo_anio,
                kilometraje=caso.vehiculo_kilometraje, combustible=caso.vehiculo_combustible, transmision=caso.vehiculo_transmision)
            completo, cantidad, detalles = calcular_detalles_campos_ficha2(
                codigo_registro=caso.item, fecha_atencion=caso.fecha, datos_generales_vehiculo=datos,
                sintomas_reportados=caso.sintoma, descripcion_sintoma=caso.descripcion_sintoma,
                sistema_afectado_probable=caso.sistema_afectado_probable, diagnostico_confirmado=dto.falla_real,
                tiempo_atencion_minutos=dto.tiempo_diagnostico_minutos,
            )
            caso.falla_real = dto.falla_real.strip()
            caso.tiempo_diagnostico_minutos = dto.tiempo_diagnostico_minutos
            caso.prediccion_correcta = dto.prediccion_correcta
            caso.metodo_confirmacion = dto.metodo_confirmacion.strip()
            caso.evidencia_ref = dto.evidencia_ref
            caso.campos_completos, caso.cantidad_campos_completos, caso.detalles_campos = completo, cantidad, detalles
            caso.estado_registro, caso.validado_por_id, caso.fecha_validacion = "verificado", usuario_id, datetime.now(timezone.utc)
        return {"id": str(caso.id), **serializar_caso(caso)}
