"""Casos de uso del tracker de validación persistido en PostgreSQL."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.validation import ValidacionTaller
from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository
from src.infrastructure.database.repositories.validacion_taller_repository import ValidacionTallerRepository
from src.interfaces.api.v1.dtos.validacion import CrearCasoValidacionDTO


def resumir_fases(grupos: list[dict[str, Any]]) -> dict[str, Any]:
    """Resumen descriptivo sobre casos verificados; no presume mejora ni significancia estadística."""
    fases = {g["fase"]: g for g in grupos}
    pre = fases.get("Pre-test", {})
    post = fases.get("Post-test", {})

    def valor(grupo: dict, campo: str) -> float:
        return float(grupo.get(campo) or 0)

    def promedio(grupo: dict, campo: str, factor: int = 1) -> float:
        total = valor(grupo, "total")
        return round(valor(grupo, campo) / total * factor, 2) if total else 0.0

    total = sum(int(valor(g, "total")) for g in grupos)
    aciertos = sum(int(valor(g, "aciertos")) for g in grupos)
    tiempo_pre, tiempo_post = promedio(pre, "minutos"), promedio(post, "minutos")
    return {
        "total_casos": total, "total_aciertos": aciertos, "total_desaciertos": total - aciertos,
        "tasa_acierto_global_porcentaje": round(aciertos / total * 100, 2) if total else 0.0,
        "casos_pretest": int(valor(pre, "total")), "casos_posttest": int(valor(post, "total")),
        "tasa_acierto_pretest_porcentaje": promedio(pre, "aciertos", 100),
        "tasa_acierto_posttest_porcentaje": promedio(post, "aciertos", 100),
        "registros_completos_pretest_porcentaje": promedio(pre, "completos", 100),
        "registros_completos_posttest_porcentaje": promedio(post, "completos", 100),
        "tiempo_promedio_pretest_min": tiempo_pre, "tiempo_promedio_posttest_min": tiempo_post,
        "reduccion_tiempo_porcentaje": (
            round((tiempo_pre - tiempo_post) / tiempo_pre * 100, 2)
            if tiempo_pre and valor(post, "total") else 0.0
        ),
        "distribucion_marcas": [], "top_fallas_reales": [],
    }


def serializar_caso(caso: ValidacionTaller) -> dict[str, Any]:
    return {
        "item": caso.item,
        "fase": caso.fase,
        "fecha": caso.fecha.isoformat(),
        "placa_enmascarada": caso.placa_enmascarada,
        "placa_hash": caso.placa_hash,
        "marca_modelo": caso.marca_modelo,
        "sintoma": caso.sintoma,
        "falla_real": caso.falla_real,
        "chatbot_prediccion": caso.chatbot_prediccion,
        "campos_completos": caso.campos_completos,
        "tiempo_diagnostico_minutos": caso.tiempo_diagnostico_minutos,
        "prediccion_correcta": caso.prediccion_correcta,
        "taller_id": str(caso.taller_id),
        "mecanico_id": str(caso.mecanico_id) if caso.mecanico_id else None,
        "metodo_confirmacion": caso.metodo_confirmacion,
        "evidencia_ref": caso.evidencia_ref,
        "estado_registro": caso.estado_registro,
        "sintoma_registrado_correctamente": caso.sintoma_registrado_correctamente,
        "validado_por_id": str(caso.validado_por_id) if caso.validado_por_id else None,
        "fecha_validacion": caso.fecha_validacion.isoformat() if caso.fecha_validacion else None,
        "normalizacion_correcta": caso.normalizacion_correcta,
        "extraccion_correcta": caso.extraccion_correcta,
        "clasificacion_procesada": caso.clasificacion_procesada,
        "procesamiento_validado": caso.procesamiento_validado,
        "tiempo_inferencia_ml_ms": caso.tiempo_inferencia_ml_ms,
    }


class ServicioValidacionTaller:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ValidacionTallerRepository(session)

    async def listar(self, taller_id: uuid.UUID, **filtros: Any) -> dict[str, Any]:
        total, casos = await self.repo.listar(taller_id, **filtros)
        return {
            "total": total,
            "skip": filtros.get("skip", 0),
            "limit": filtros.get("limit", 50),
            "casos": [serializar_caso(caso) for caso in casos],
        }

    async def crear(
        self,
        taller_id: uuid.UUID,
        usuario_id: uuid.UUID | None,
        dto: CrearCasoValidacionDTO,
        placa_enmascarada: str,
        placa_hash: str,
    ) -> ValidacionTaller:
        fecha_caso = date.fromisoformat(dto.fecha) if dto.fecha else date.today()
        
        # Validación de reglas de negocio para estado verificado
        estado = dto.estado_registro
        if estado == "verificado":
            if not dto.metodo_confirmacion or not dto.evidencia_ref:
                estado = "borrador"

        # Procesamiento validado requiere cumplimiento de las 3 fases si están registradas
        proc_val = dto.procesamiento_validado
        if proc_val is None and (
            dto.normalizacion_correcta is not None
            and dto.extraccion_correcta is not None
            and dto.clasificacion_procesada is not None
        ):
            proc_val = 1 if (
                dto.normalizacion_correcta == 1
                and dto.extraccion_correcta == 1
                and dto.clasificacion_procesada == 1
            ) else 0

        fecha_val = datetime.now(timezone.utc) if estado == "verificado" else None
        validado_por = usuario_id if estado == "verificado" else None

        caso = await self.repo.crear(
            taller_id=taller_id,
            mecanico_id=usuario_id,
            fase=dto.fase,
            fecha=fecha_caso,
            placa_enmascarada=placa_enmascarada,
            placa_hash=placa_hash,
            marca_modelo=dto.marca_modelo.strip(),
            sintoma=dto.sintoma.strip(),
            falla_real=dto.falla_real.strip(),
            chatbot_prediccion=dto.chatbot_prediccion.strip(),
            campos_completos=dto.campos_completos,
            tiempo_diagnostico_minutos=dto.tiempo_diagnostico_minutos,
            prediccion_correcta=dto.prediccion_correcta,
            metodo_confirmacion=dto.metodo_confirmacion or "Inspección Visual",
            evidencia_ref=dto.evidencia_ref,
            estado_registro=estado,
            sintoma_registrado_correctamente=dto.sintoma_registrado_correctamente,
            validado_por_id=validado_por,
            fecha_validacion=fecha_val,
            normalizacion_correcta=dto.normalizacion_correcta,
            extraccion_correcta=dto.extraccion_correcta,
            clasificacion_procesada=dto.clasificacion_procesada,
            procesamiento_validado=proc_val,
            tiempo_inferencia_ml_ms=dto.tiempo_inferencia_ml_ms,
        )
        await OperacionesRepository(self.session).registrar_auditoria(
            accion="crear_validacion_taller",
            entidad="validacion_taller",
            taller_id=taller_id,
            usuario_id=usuario_id,
            detalles={"item": caso.item, "fase": caso.fase, "estado_registro": caso.estado_registro},
        )
        return caso

    async def metricas(
        self, taller_id: uuid.UUID, fecha_desde: date | None = None, fecha_hasta: date | None = None
    ) -> dict[str, Any]:
        grupos = await self.repo.resumen_por_fase(taller_id, fecha_desde, fecha_hasta)
        metricas_vi = await self.repo.metricas_variable_independiente(taller_id, fecha_desde, fecha_hasta)
        distribuciones = await self.repo.distribuciones(taller_id, fecha_desde, fecha_hasta)
        return {
            **resumir_fases(grupos),
            **metricas_vi,
            **distribuciones,
        }
