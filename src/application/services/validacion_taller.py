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

CAMPS_FICHA2 = (
    ("campo_1", "Código de registro"),
    ("campo_2", "Fecha de atención"),
    ("campo_3", "Datos generales del vehículo"),
    ("campo_4", "Síntomas reportados"),
    ("campo_5", "Descripción del síntoma"),
    ("campo_6", "Sistema afectado probable"),
    ("campo_7", "Diagnóstico confirmado por el mecánico"),
    ("campo_8", "Tiempo de atención registrado"),
)


def _valor_presente(valor: Any) -> bool:
    if valor is None:
        return False
    if isinstance(valor, str):
        limpio = valor.strip().lower()
        return bool(limpio) and limpio not in {"-", "n/a", "na", "sin registrar", "pendiente"}
    if isinstance(valor, (int, float)):
        return valor > 0
    return bool(valor)


def construir_datos_generales_vehiculo(
    *,
    marca_modelo: Any,
    anio: Any = None,
    kilometraje: Any = None,
    combustible: Any = None,
    transmision: Any = None,
) -> dict[str, Any]:
    """Representa el bloque B del Anexo 2 sin reducirlo solo a marca/modelo."""
    return {
        "marca_modelo": marca_modelo,
        "anio": anio,
        "kilometraje": kilometraje,
        "combustible": combustible,
        "transmision": transmision,
    }


def _datos_generales_completos(valor: Any) -> bool:
    if not isinstance(valor, dict):
        return _valor_presente(valor)
    requeridos = ("marca_modelo", "anio", "kilometraje", "combustible", "transmision")
    return all(_valor_presente(valor.get(campo)) for campo in requeridos)


def _resumir_valor_ficha2(valor: Any) -> str:
    if isinstance(valor, dict):
        partes = [f"{clave}={valor.get(clave) or ''}" for clave in valor]
        return "; ".join(partes)[:160]
    return str(valor)[:160] if valor is not None else ""


def calcular_detalles_campos_ficha2(
    *,
    codigo_registro: Any,
    fecha_atencion: Any,
    datos_generales_vehiculo: Any,
    sintomas_reportados: Any,
    descripcion_sintoma: Any,
    sistema_afectado_probable: Any,
    diagnostico_confirmado: Any,
    tiempo_atencion_minutos: Any,
) -> tuple[int, int, dict[str, dict[str, Any]]]:
    """Calcula trazabilidad auditable del indicador RDC según Anexo 2, Ficha 2."""
    valores = {
        "campo_1": codigo_registro,
        "campo_2": fecha_atencion,
        "campo_3": datos_generales_vehiculo,
        "campo_4": sintomas_reportados,
        "campo_5": descripcion_sintoma,
        "campo_6": sistema_afectado_probable,
        "campo_7": diagnostico_confirmado,
        "campo_8": tiempo_atencion_minutos,
    }
    detalles: dict[str, dict[str, Any]] = {}
    cantidad = 0
    for clave, nombre in CAMPS_FICHA2:
        completo = _datos_generales_completos(valores[clave]) if clave == "campo_3" else _valor_presente(valores[clave])
        cantidad += int(completo)
        detalles[clave] = {
            "nombre": nombre,
            "completo": completo,
            "valor_resumen": _resumir_valor_ficha2(valores[clave]),
        }
    return (1 if cantidad == 8 else 0), cantidad, detalles


def resumir_fases(grupos: list[dict[str, Any]]) -> dict[str, Any]:
    """Resumen descriptivo sobre casos verificados; no presume mejora ni significancia estadística."""
    fases = {str(g["fase"]).strip().lower(): g for g in grupos}
    pre = fases.get("pre-test") or fases.get("pretest") or {}
    post = fases.get("post-test") or fases.get("posttest") or {}

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
        "descripcion_sintoma": caso.descripcion_sintoma,
        "vehiculo_anio": caso.vehiculo_anio,
        "vehiculo_kilometraje": caso.vehiculo_kilometraje,
        "vehiculo_combustible": caso.vehiculo_combustible,
        "vehiculo_transmision": caso.vehiculo_transmision,
        "falla_real": caso.falla_real,
        "chatbot_prediccion": caso.chatbot_prediccion,
        "sistema_afectado_probable": caso.sistema_afectado_probable,
        "campos_completos": caso.campos_completos,
        "cantidad_campos_completos": caso.cantidad_campos_completos,
        "detalles_campos": caso.detalles_campos,
        "tiempo_diagnostico_minutos": caso.tiempo_diagnostico_minutos,
        "prediccion_correcta": caso.prediccion_correcta,
        "taller_id": str(caso.taller_id),
        "mecanico_id": str(caso.mecanico_id) if caso.mecanico_id else None,
        "metodo_confirmacion": caso.metodo_confirmacion,
        "evidencia_ref": caso.evidencia_ref,
        "estado_registro": caso.estado_registro,
        "tipo_registro": getattr(caso, "tipo_registro", "THESIS_POSTTEST"),
        "conversacion_id": str(caso.conversacion_id) if getattr(caso, "conversacion_id", None) else None,
        "diagnostico_id": str(caso.diagnostico_id) if getattr(caso, "diagnostico_id", None) else None,
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

        # Resolución de tipo de registro para separación estricta
        if dto.tipo_registro:
            tipo_reg = dto.tipo_registro
        else:
            fase_lower = dto.fase.strip().lower()
            if "pre" in fase_lower:
                tipo_reg = "THESIS_PRETEST"
            elif "post" in fase_lower:
                tipo_reg = "THESIS_POSTTEST"
            elif "pilo" in fase_lower or "dev" in fase_lower:
                tipo_reg = "DEVELOPMENT"
            else:
                tipo_reg = "THESIS_POSTTEST"

        conv_id = None
        if dto.conversacion_id:
            try:
                conv_id = uuid.UUID(dto.conversacion_id)
            except (ValueError, TypeError):
                conv_id = None

        diag_id = None
        if dto.diagnostico_id:
            try:
                diag_id = uuid.UUID(dto.diagnostico_id)
            except (ValueError, TypeError):
                diag_id = None

        fecha_val = datetime.now(timezone.utc) if estado == "verificado" else None
        validado_por = usuario_id if estado == "verificado" else None
        sistema_probable = (dto.sistema_afectado_probable or dto.chatbot_prediccion).strip()
        descripcion_sintoma = (dto.descripcion_sintoma or "").strip()
        datos_generales_vehiculo = construir_datos_generales_vehiculo(
            marca_modelo=dto.marca_modelo,
            anio=dto.vehiculo_anio,
            kilometraje=dto.vehiculo_kilometraje,
            combustible=dto.vehiculo_combustible,
            transmision=dto.vehiculo_transmision,
        )
        campos_completos, cantidad_campos, detalles_campos = calcular_detalles_campos_ficha2(
            codigo_registro="pendiente_item",
            fecha_atencion=fecha_caso,
            datos_generales_vehiculo=datos_generales_vehiculo,
            sintomas_reportados=dto.sintoma,
            descripcion_sintoma=descripcion_sintoma,
            sistema_afectado_probable=sistema_probable,
            diagnostico_confirmado=dto.falla_real,
            tiempo_atencion_minutos=dto.tiempo_diagnostico_minutos,
        )

        caso = await self.repo.crear(
            taller_id=taller_id,
            mecanico_id=usuario_id,
            fase=dto.fase,
            fecha=fecha_caso,
            placa_enmascarada=placa_enmascarada,
            placa_hash=placa_hash,
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
            metodo_confirmacion=dto.metodo_confirmacion or "Inspección Visual",
            evidencia_ref=dto.evidencia_ref,
            estado_registro=estado,
            tipo_registro=tipo_reg,
            conversacion_id=conv_id,
            diagnostico_id=diag_id,
            sintoma_registrado_correctamente=dto.sintoma_registrado_correctamente,
            validado_por_id=validado_por,
            fecha_validacion=fecha_val,
            normalizacion_correcta=dto.normalizacion_correcta,
            extraccion_correcta=dto.extraccion_correcta,
            clasificacion_procesada=dto.clasificacion_procesada,
            procesamiento_validado=proc_val,
            tiempo_inferencia_ml_ms=dto.tiempo_inferencia_ml_ms,
        )
        detalles_actualizados = dict(caso.detalles_campos or {})
        if "campo_1" in detalles_actualizados:
            detalles_actualizados["campo_1"] = {
                **detalles_actualizados["campo_1"],
                "valor_resumen": str(caso.item),
            }
            caso.detalles_campos = detalles_actualizados
            await self.session.flush()
        await OperacionesRepository(self.session).registrar_auditoria(
            accion="crear_validacion_taller",
            entidad="validacion_taller",
            taller_id=taller_id,
            usuario_id=usuario_id,
            detalles={"item": caso.item, "fase": caso.fase, "estado_registro": caso.estado_registro, "tipo_registro": caso.tipo_registro},
        )
        return caso

    async def metricas(
        self, taller_id: uuid.UUID, fecha_desde: date | None = None, fecha_hasta: date | None = None
    ) -> dict[str, Any]:
        grupos = await self.repo.resumen_por_fase(taller_id, fecha_desde, fecha_hasta)
        metricas_vi = await self.repo.metricas_variable_independiente(taller_id, fecha_desde, fecha_hasta)
        distribuciones = await self.repo.distribuciones(taller_id, fecha_desde, fecha_hasta)
        total_v = int(metricas_vi.get("casos_verificados") or 0)
        return {
            **resumir_fases(grupos),
            **metricas_vi,
            "total_casos_verificados": total_v,
            **distribuciones,
        }
