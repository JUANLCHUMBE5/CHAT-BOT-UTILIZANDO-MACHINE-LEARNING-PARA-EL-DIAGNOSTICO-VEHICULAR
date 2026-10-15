"""Registro humano y aislado de los casos oficiales POST-TEST."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
    prediccion_correcta: int | None = Field(default=None, ge=0, le=1)
    metodo_confirmacion: str = Field(min_length=3, max_length=500)
    evidencia_ref: str = Field(
        min_length=1,
        max_length=500,
        description=(
            "Referencia del soporte revisado por una persona autorizada; la referencia por sí sola "
            "no acredita una comprobación física."
        ),
    )
    sistema_afectado_probable: str | None = Field(default=None, min_length=2, max_length=80)
    vehiculo_anio: int | None = Field(default=None, ge=1950, le=2100)
    vehiculo_kilometraje: int | None = Field(default=None, ge=0)
    vehiculo_combustible: str | None = Field(default=None, max_length=30)
    vehiculo_transmision: str | None = Field(default=None, max_length=30)

    @field_validator("evidencia_ref", mode="before")
    @classmethod
    def limpiar_referencia_evidencia(cls, valor: Any) -> Any:
        return valor.strip() if isinstance(valor, str) else valor


def _claims(payload: dict, *, require_user: bool = False) -> tuple[uuid.UUID, uuid.UUID | None]:
    try:
        taller = uuid.UUID(str(payload["taller_id"]))
        usuario = uuid.UUID(str(payload["usuario_id"])) if payload.get("usuario_id") else None
        if require_user and usuario is None:
            raise HTTPException(status_code=401, detail="Token sin identidad de usuario validador.")
        return taller, usuario
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Token sin identidad de taller válida.") from exc


@router.post("/desde-diagnostico/{diagnostico_id}", status_code=201)
async def crear_borrador_posttest(
    diagnostico_id: uuid.UUID, payload: dict = Depends(exigir_gestion_validacion)
):
    """Autollenado desde CarBot. No rellena confirmación ni métricas humanas."""
    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
    taller_id, usuario_id = _claims(payload, require_user=True)
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        async with session.begin():
            diagnostico = await DiagnosticoRepository(session).obtener_por_id(diagnostico_id)
            if not diagnostico or diagnostico.taller_id != taller_id or not diagnostico.vehiculo:
                raise HTTPException(
                    status_code=404, detail="Diagnóstico con vehículo identificado no encontrado."
                )
            existente = await session.execute(
                select(ValidacionTaller).where(ValidacionTaller.diagnostico_id == diagnostico_id)
            )
            if existente.scalar_one_or_none():
                raise HTTPException(status_code=409, detail="El diagnóstico ya tiene un borrador POST-TEST.")
            v = diagnostico.vehiculo
            datos = construir_datos_generales_vehiculo(
                marca_modelo=f"{v.marca} {v.modelo}",
                anio=v.anio,
                kilometraje=v.kilometraje,
                combustible=v.combustible,
                transmision=None,
            )
            completo, cantidad, detalles = calcular_detalles_campos_ficha2(
                codigo_registro="pendiente",
                fecha_atencion=diagnostico.creado_en.date(),
                datos_generales_vehiculo=datos,
                sintomas_reportados=diagnostico.sintoma_original,
                descripcion_sintoma=diagnostico.sintoma_normalizado,
                sistema_afectado_probable=None,
                diagnostico_confirmado=None,
                tiempo_atencion_minutos=None,
            )
            try:
                caso = await ValidacionTallerRepository(session).crear(
                    origen_clave=f"posttest:{diagnostico_id}",
                    taller_id=taller_id,
                    mecanico_id=usuario_id,
                    fase="Post-test",
                    fecha=diagnostico.creado_en.date(),
                    placa_enmascarada=f"***-{v.placa_ultimos4}",
                    placa_hash=v.placa_hash,
                    marca_modelo=f"{v.marca} {v.modelo}",
                    sintoma=diagnostico.sintoma_original,
                    descripcion_sintoma=diagnostico.sintoma_normalizado,
                    vehiculo_anio=v.anio,
                    vehiculo_kilometraje=v.kilometraje,
                    vehiculo_combustible=v.combustible,
                    vehiculo_transmision=None,
                    falla_real=None,
                    chatbot_prediccion=diagnostico.falla_predicha or "",
                    sistema_afectado_probable=None,
                    campos_completos=completo,
                    cantidad_campos_completos=cantidad,
                    detalles_campos=detalles,
                    tiempo_diagnostico_minutos=None,
                    prediccion_correcta=None,
                    metodo_confirmacion=None,
                    evidencia_ref=None,
                    estado_registro="borrador",
                    tipo_registro="THESIS_POSTTEST",
                    conversacion_id=diagnostico.conversacion_id,
                    diagnostico_id=diagnostico.id,
                    tiempo_inferencia_ml_ms=diagnostico.tiempo_inferencia_ml_ms,
                    inicio_sistema_at=None,
                    duracion_sistema_segundos=(
                        diagnostico.duracion_ms / 1000 if diagnostico.duracion_ms is not None else None
                    ),
                )
            except IntegrityError as exc:
                raise HTTPException(
                    status_code=409,
                    detail="El diagnóstico ya tiene un borrador POST-TEST registrado.",
                ) from exc
            _, cantidad, detalles = calcular_detalles_campos_ficha2(
                codigo_registro=caso.item,
                fecha_atencion=caso.fecha,
                datos_generales_vehiculo=datos,
                sintomas_reportados=caso.sintoma,
                descripcion_sintoma=caso.descripcion_sintoma,
                sistema_afectado_probable=caso.sistema_afectado_probable,
                diagnostico_confirmado=caso.falla_real,
                tiempo_atencion_minutos=caso.tiempo_diagnostico_minutos,
            )
            caso.cantidad_campos_completos = cantidad
            caso.campos_completos = int(cantidad == 8)
            caso.detalles_campos = detalles
        return {"id": str(caso.id), **serializar_caso(caso)}


@router.patch("/{caso_id}/confirmacion-humana")
async def confirmar_posttest(
    caso_id: uuid.UUID, dto: ConfirmacionHumanaPostTestDTO, payload: dict = Depends(exigir_gestion_validacion)
):
    """Solo una persona registra falla real, tiempo diagnóstico y acierto SI/NO."""
    if not database_configurada():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado.")
    taller_id, usuario_id = _claims(payload, require_user=True)
    evidencia_ref = dto.evidencia_ref.strip()
    if not evidencia_ref:
        raise HTTPException(
            status_code=422, detail="evidencia_ref debe apuntar al soporte revisado por el validador."
        )
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        async with session.begin():
            caso = await session.get(ValidacionTaller, caso_id, with_for_update=True)
            if not caso or caso.taller_id != taller_id or caso.tipo_registro != "THESIS_POSTTEST":
                raise HTTPException(status_code=404, detail="Borrador POST-TEST no encontrado.")
            if caso.estado_registro == "verificado":
                raise HTTPException(
                    status_code=409, detail="El registro ya fue verificado y no admite reconfirmación."
                )
            tiene_prediccion = bool((caso.chatbot_prediccion or "").strip())
            if tiene_prediccion != (dto.prediccion_correcta is not None):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Registre el resultado solo cuando existe una predicción original; "
                        "los casos sin predicción quedan fuera del denominador PPCF."
                    ),
                )
            caso.sistema_afectado_probable = (
                dto.sistema_afectado_probable.strip()
                if dto.sistema_afectado_probable and dto.sistema_afectado_probable.strip()
                else caso.sistema_afectado_probable
            )
            for campo in ("vehiculo_anio", "vehiculo_kilometraje"):
                valor = getattr(dto, campo)
                if valor is not None:
                    setattr(caso, campo, valor)
            for campo in ("vehiculo_combustible", "vehiculo_transmision"):
                valor = getattr(dto, campo)
                if valor and valor.strip():
                    setattr(caso, campo, valor.strip())
            datos = construir_datos_generales_vehiculo(
                marca_modelo=caso.marca_modelo,
                anio=caso.vehiculo_anio,
                kilometraje=caso.vehiculo_kilometraje,
                combustible=caso.vehiculo_combustible,
                transmision=caso.vehiculo_transmision,
            )
            completo, cantidad, detalles = calcular_detalles_campos_ficha2(
                codigo_registro=caso.item,
                fecha_atencion=caso.fecha,
                datos_generales_vehiculo=datos,
                sintomas_reportados=caso.sintoma,
                descripcion_sintoma=caso.descripcion_sintoma,
                sistema_afectado_probable=caso.sistema_afectado_probable,
                diagnostico_confirmado=dto.falla_real,
                tiempo_atencion_minutos=dto.tiempo_diagnostico_minutos,
            )
            caso.falla_real = dto.falla_real.strip()
            caso.tiempo_diagnostico_minutos = dto.tiempo_diagnostico_minutos
            caso.prediccion_correcta = dto.prediccion_correcta
            caso.metodo_confirmacion = dto.metodo_confirmacion.strip()
            caso.evidencia_ref = evidencia_ref
            caso.campos_completos, caso.cantidad_campos_completos, caso.detalles_campos = (
                completo,
                cantidad,
                detalles,
            )
            caso.estado_registro, caso.validado_por_id, caso.fecha_validacion = (
                "verificado",
                usuario_id,
                datetime.now(timezone.utc),
            )
        return {"id": str(caso.id), **serializar_caso(caso)}
