"""Borrador automático de consulta; nunca incorpora casos a la muestra oficial."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import UUID

from sqlalchemy import case, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.validacion_taller import (
    calcular_detalles_campos_ficha2,
    construir_datos_generales_vehiculo,
)
from src.infrastructure.database.models.validation import ValidacionTaller


def case_id_sesion_activa(gestor: Any, session_id: str | None) -> str | None:
    """Lee el case_id real de la sesión; nunca interpreta session_id como case_id."""
    if not session_id:
        return None
    session_manager = getattr(gestor, "session_manager", None)
    if session_manager is None:
        return None
    sesion = session_manager.obtener_sesion(session_id)
    case_id = getattr(sesion, "case_id", None)
    if not case_id:
        return None
    try:
        return str(UUID(str(case_id)))
    except (TypeError, ValueError, AttributeError):
        return None


def clave_borrador(diagnostico: Any, vehiculo: Any, case_id: str | None = None) -> str:
    """Identifica un caso por taller, conversación, vehículo y case_id."""
    if not case_id:
        return f"auto:{diagnostico.id}"
    identidad = "|".join((str(diagnostico.taller_id), str(diagnostico.conversacion_id), case_id, vehiculo.placa_hash))
    return "caso:" + sha256(identidad.encode("utf-8")).hexdigest()[:59]


def construir_statement_borrador_consulta(
    diagnostico: Any, vehiculo: Any, *, case_id: str | None = None
) -> Any | None:
    """Construye el insert idempotente del borrador sin realizar I/O.

    La clave única evita duplicados aun con reintentos concurrentes. Si faltan
    datos obligatorios (placa identificada), se conserva el diagnóstico normal.
    """
    if vehiculo is None or not getattr(vehiculo, "placa_hash", None):
        return None
    if len(vehiculo.placa_hash) != 64:
        return None
    clave = clave_borrador(diagnostico, vehiculo, case_id)
    fecha = datetime.now(timezone.utc).date()
    marca_modelo = f"{vehiculo.marca or 'Generico'} {vehiculo.modelo or 'Generico'}"[:100]
    datos = construir_datos_generales_vehiculo(
        marca_modelo=marca_modelo, anio=vehiculo.anio,
        kilometraje=vehiculo.kilometraje, combustible=vehiculo.combustible,
        transmision=None,
    )
    completo, cantidad, detalles = calcular_detalles_campos_ficha2(
        codigo_registro="pendiente", fecha_atencion=fecha,
        datos_generales_vehiculo=datos,
        sintomas_reportados=diagnostico.sintoma_original,
        descripcion_sintoma=diagnostico.sintoma_normalizado,
        sistema_afectado_probable=diagnostico.falla_predicha or None,
        diagnostico_confirmado=None, tiempo_atencion_minutos=None,
    )
    stmt = insert(ValidacionTaller).values(
        origen_clave=clave, taller_id=diagnostico.taller_id,
        mecanico_id=diagnostico.mecanico_id, fase="Post-test", fecha=fecha,
        placa_enmascarada=f"***-{vehiculo.placa_ultimos4 or '****'}",
        placa_hash=vehiculo.placa_hash, marca_modelo=marca_modelo,
        sintoma=diagnostico.sintoma_original,
        descripcion_sintoma=diagnostico.sintoma_normalizado,
        vehiculo_anio=vehiculo.anio, vehiculo_kilometraje=vehiculo.kilometraje,
        vehiculo_combustible=vehiculo.combustible, vehiculo_transmision=None,
        falla_real=None, chatbot_prediccion=diagnostico.falla_predicha or "Sin predicción registrada",
        sistema_afectado_probable=diagnostico.falla_predicha,
        campos_completos=completo, cantidad_campos_completos=cantidad,
        detalles_campos=detalles, tiempo_diagnostico_minutos=None,
        prediccion_correcta=None, metodo_confirmacion=None, evidencia_ref=None,
        estado_registro="borrador", tipo_registro="DEVELOPMENT",
        conversacion_id=diagnostico.conversacion_id, diagnostico_id=diagnostico.id,
        tiempo_inferencia_ml_ms=diagnostico.tiempo_inferencia_ml_ms,
        inicio_sistema_at=None, fin_sistema_at=None,
        duracion_sistema_segundos=(
            round(diagnostico.duracion_ms / 1000)
            if diagnostico.duracion_ms is not None else None
        ),
    )
    if case_id:
        stmt = stmt.on_conflict_do_update(
            index_elements=["origen_clave"],
            set_={
                "diagnostico_id": func.coalesce(stmt.excluded.diagnostico_id, ValidacionTaller.diagnostico_id),
                "sintoma": func.coalesce(
                    func.nullif(stmt.excluded.sintoma, ""), ValidacionTaller.sintoma
                ),
                "descripcion_sintoma": func.coalesce(
                    func.nullif(stmt.excluded.descripcion_sintoma, ""),
                    ValidacionTaller.descripcion_sintoma,
                ),
                "chatbot_prediccion": func.coalesce(
                    func.nullif(stmt.excluded.chatbot_prediccion, "Sin predicción registrada"),
                    ValidacionTaller.chatbot_prediccion,
                ),
                "sistema_afectado_probable": func.coalesce(
                    func.nullif(stmt.excluded.sistema_afectado_probable, ""),
                    ValidacionTaller.sistema_afectado_probable,
                ),
                "marca_modelo": case(
                    (
                        stmt.excluded.marca_modelo != "Generico Generico",
                        stmt.excluded.marca_modelo,
                    ),
                    else_=ValidacionTaller.marca_modelo,
                ),
                "vehiculo_anio": func.coalesce(
                    stmt.excluded.vehiculo_anio, ValidacionTaller.vehiculo_anio
                ),
                "vehiculo_kilometraje": func.coalesce(
                    stmt.excluded.vehiculo_kilometraje, ValidacionTaller.vehiculo_kilometraje
                ),
                "vehiculo_combustible": func.coalesce(
                    func.nullif(stmt.excluded.vehiculo_combustible, ""),
                    ValidacionTaller.vehiculo_combustible,
                ),
                "tiempo_inferencia_ml_ms": func.coalesce(
                    stmt.excluded.tiempo_inferencia_ml_ms,
                    ValidacionTaller.tiempo_inferencia_ml_ms,
                ),
                "campos_completos": case(
                    (
                        stmt.excluded.cantidad_campos_completos
                        >= ValidacionTaller.cantidad_campos_completos,
                        stmt.excluded.campos_completos,
                    ),
                    else_=ValidacionTaller.campos_completos,
                ),
                "cantidad_campos_completos": func.greatest(
                    stmt.excluded.cantidad_campos_completos,
                    ValidacionTaller.cantidad_campos_completos,
                ),
                "detalles_campos": case(
                    (
                        stmt.excluded.cantidad_campos_completos
                        >= ValidacionTaller.cantidad_campos_completos,
                        stmt.excluded.detalles_campos,
                    ),
                    else_=ValidacionTaller.detalles_campos,
                ),
            },
            where=(ValidacionTaller.estado_registro == "borrador")
            & (ValidacionTaller.tipo_registro == "DEVELOPMENT")
            & (ValidacionTaller.placa_hash == vehiculo.placa_hash),
        )
    else:
        stmt = stmt.on_conflict_do_nothing(index_elements=["origen_clave"])
    return stmt


async def registrar_borrador_consulta(
    session: AsyncSession, diagnostico: Any, vehiculo: Any, *, case_id: str | None = None
) -> None:
    """Persiste un borrador DEVELOPMENT idempotente, sin datos humanos inventados."""
    stmt = construir_statement_borrador_consulta(diagnostico, vehiculo, case_id=case_id)
    if stmt is not None:
        await session.execute(stmt)

