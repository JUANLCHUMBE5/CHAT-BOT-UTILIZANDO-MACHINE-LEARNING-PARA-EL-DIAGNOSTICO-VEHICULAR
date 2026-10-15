"""Casos de uso del tracker de validación persistido en PostgreSQL."""

from __future__ import annotations

import math
import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
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
        return math.isfinite(valor) and valor >= 0
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
        partes = [f"{clave}={valor[clave] if valor[clave] is not None else ''}" for clave in valor]
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
        if clave == "campo_3":
            completo = _datos_generales_completos(valores[clave])
        elif clave == "campo_8":
            try:
                tiempo = float(valores[clave])
                completo = math.isfinite(tiempo) and tiempo > 0
            except (TypeError, ValueError):
                completo = False
        elif clave == "campo_2":
            try:
                date.fromisoformat(str(valores[clave]))
                completo = True
            except (TypeError, ValueError):
                completo = isinstance(valores[clave], date)
        else:
            completo = _valor_presente(valores[clave])
        cantidad += int(completo)
        detalles[clave] = {
            "nombre": nombre,
            "completo": completo,
            "valor_resumen": _resumir_valor_ficha2(valores[clave]),
        }
    return (1 if cantidad == 8 else 0), cantidad, detalles


def resumir_fases(grupos: list[dict[str, Any]]) -> dict[str, Any]:
    """Resumen descriptivo sobre casos verificados; no presume mejora ni significancia estadística."""
    grupos_oficiales = [
        g
        for g in grupos
        if str(g.get("fase", "")).strip().casefold() in {"pre-test", "pretest", "post-test", "posttest"}
    ]
    fases = {str(g["fase"]).strip().casefold(): g for g in grupos_oficiales}
    pre = fases.get("pre-test") or fases.get("pretest") or {}
    post = fases.get("post-test") or fases.get("posttest") or {}

    def valor(grupo: dict, campo: str) -> float:
        return float(grupo.get(campo) or 0)

    def promedio(grupo: dict, campo: str, denominador: str, factor: int = 1) -> float | None:
        cantidad = valor(grupo, denominador)
        return round(valor(grupo, campo) / cantidad * factor, 2) if cantidad > 0 else None

    total = sum(int(valor(g, "total")) for g in grupos_oficiales)
    aciertos = sum(int(valor(g, "aciertos")) for g in grupos_oficiales)
    predicciones_evaluadas = sum(int(valor(g, "predicciones_evaluadas")) for g in grupos_oficiales)
    pred_pre = int(valor(pre, "predicciones_evaluadas"))
    pred_post = int(valor(post, "predicciones_evaluadas"))
    campos_pre = int(valor(pre, "campos_evaluados"))
    campos_post = int(valor(post, "campos_evaluados"))
    tiempos_pre = int(valor(pre, "tiempos_evaluados"))
    tiempos_post = int(valor(post, "tiempos_evaluados"))
    # El instrumento divide por diagnósticos evaluados: no reducir ese denominador
    # silenciosamente cuando falta una medición. La fase permanece pendiente.
    tiempo_pre = promedio(pre, "minutos", "total") if tiempos_pre == valor(pre, "total") else None
    tiempo_post = promedio(post, "minutos", "total") if tiempos_post == valor(post, "total") else None
    tasa_global = round(aciertos / predicciones_evaluadas * 100, 2) if predicciones_evaluadas else None
    tasa_pre = promedio(pre, "aciertos", "predicciones_evaluadas", 100)
    tasa_post = promedio(post, "aciertos", "predicciones_evaluadas", 100)
    completos_pre = promedio(pre, "completos", "total", 100) if campos_pre == valor(pre, "total") else None
    completos_post = (
        promedio(post, "completos", "total", 100) if campos_post == valor(post, "total") else None
    )
    reduccion_tiempo = (
        round((tiempo_pre - tiempo_post) / tiempo_pre * 100, 2)
        if tiempo_pre is not None and tiempo_post is not None and tiempo_pre > 0
        else None
    )
    return {
        "total_casos": total,
        "total_aciertos": aciertos,
        "total_desaciertos": predicciones_evaluadas - aciertos,
        "tasa_acierto_global_porcentaje": tasa_global,
        "casos_pretest": int(valor(pre, "total")),
        "casos_posttest": int(valor(post, "total")),
        "predicciones_evaluadas_pretest": pred_pre,
        "predicciones_evaluadas_posttest": pred_post,
        "registros_prdc_evaluados_pretest": campos_pre,
        "registros_prdc_evaluados_posttest": campos_post,
        "tasa_acierto_pretest_porcentaje": tasa_pre,
        "tasa_acierto_posttest_porcentaje": tasa_post,
        "registros_completos_pretest_porcentaje": completos_pre,
        "registros_completos_posttest_porcentaje": completos_post,
        "tiempos_evaluados_pretest": tiempos_pre,
        "tiempos_evaluados_posttest": tiempos_post,
        "tiempo_promedio_pretest_min": tiempo_pre,
        "tiempo_promedio_posttest_min": tiempo_post,
        "reduccion_tiempo_porcentaje": reduccion_tiempo,
        "distribucion_marcas": [],
        "top_fallas_reales": [],
    }


def serializar_caso(caso: ValidacionTaller) -> dict[str, Any]:
    es_pretest = str(caso.fase).strip().lower() == "pre-test"
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
        "diagnostico_preliminar_sin_chatbot": caso.chatbot_prediccion if es_pretest else None,
        "falla_sugerida_chatbot": None if es_pretest else caso.chatbot_prediccion,
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
        "tipo_registro": getattr(caso, "tipo_registro", "DEVELOPMENT") or "DEVELOPMENT",
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
        "inicio_sistema_at": caso.inicio_sistema_at.isoformat()
        if getattr(caso, "inicio_sistema_at", None)
        else None,
        "fin_sistema_at": caso.fin_sistema_at.isoformat() if getattr(caso, "fin_sistema_at", None) else None,
        "duracion_sistema_segundos": float(caso.duracion_sistema_segundos)
        if getattr(caso, "duracion_sistema_segundos", None) is not None
        else None,
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
            tiene_revision_humana = bool(
                usuario_id
                and dto.falla_real
                and dto.falla_real.strip()
                and dto.prediccion_correcta in (0, 1)
                and dto.tiempo_diagnostico_minutos
                and dto.metodo_confirmacion
                and dto.metodo_confirmacion.strip()
                and dto.evidencia_ref
                and dto.evidencia_ref.strip()
            )
            if not tiene_revision_humana:
                estado = "borrador"

        # Procesamiento validado requiere cumplimiento de las 3 fases si están registradas
        proc_val = dto.procesamiento_validado
        if proc_val is None and (
            dto.normalizacion_correcta is not None
            and dto.extraccion_correcta is not None
            and dto.clasificacion_procesada is not None
        ):
            proc_val = (
                1
                if (
                    dto.normalizacion_correcta == 1
                    and dto.extraccion_correcta == 1
                    and dto.clasificacion_procesada == 1
                )
                else 0
            )

        # Blindaje contra contaminación de muestra:
        # Requiere intención explícita; NUNCA inferir THESIS_* automáticamente.
        if dto.tipo_registro:
            tipo_reg = dto.tipo_registro
        else:
            tipo_reg = "DEVELOPMENT"

        if tipo_reg == "THESIS_PRETEST" and dto.fase != "Pre-test":
            raise ValueError("Un registro de tesis THESIS_PRETEST debe pertenecer a la fase Pre-test.")
        if tipo_reg == "THESIS_POSTTEST" and dto.fase != "Post-test":
            raise ValueError("Un registro de tesis THESIS_POSTTEST debe pertenecer a la fase Post-test.")
        if tipo_reg == "THESIS_POSTTEST" and not dto.diagnostico_id:
            raise ValueError("Un POST-TEST oficial debe vincularse al diagnóstico original de CarBot.")
        if tipo_reg == "THESIS_PRETEST" and dto.diagnostico_id:
            raise ValueError(
                "Un PRE-TEST sin CarBot no puede vincularse a un diagnóstico generado por el sistema."
            )

        conv_id = None
        if dto.conversacion_id:
            try:
                conv_id = uuid.UUID(dto.conversacion_id)
            except (ValueError, TypeError):
                conv_id = None

        diag_id = None
        chatbot_prediccion_final = dto.chatbot_prediccion.strip()
        tiempo_ml = dto.tiempo_inferencia_ml_ms

        if dto.diagnostico_id:
            try:
                diag_id = uuid.UUID(dto.diagnostico_id)
            except (ValueError, TypeError):
                raise ValueError("El diagnostico_id proporcionado no es un UUID válido.")

            from src.infrastructure.database.models.diagnostics import Diagnostico

            stmt_diag = select(Diagnostico).where(
                Diagnostico.id == diag_id,
                Diagnostico.taller_id == taller_id,
            )
            diag_real = (await self.session.execute(stmt_diag)).scalar_one_or_none()
            if not diag_real:
                raise ValueError("El diagnóstico vinculado no existe o no pertenece al taller.")

            if tipo_reg == "THESIS_POSTTEST" and not diag_real.falla_predicha:
                raise ValueError(
                    "El POST-TEST requiere la predicción original de CarBot para poder evaluarla."
                )

            # INMUTABILIDAD ABSOLUTA: La predicción del modelo no puede alterarse
            if diag_real.falla_predicha:
                chatbot_prediccion_final = diag_real.falla_predicha

            if not conv_id and diag_real.conversacion_id:
                conv_id = diag_real.conversacion_id

            if tiempo_ml is None and diag_real.tiempo_inferencia_ml_ms is not None:
                tiempo_ml = diag_real.tiempo_inferencia_ml_ms

        # Telemetría técnica
        inicio_sis = None
        if dto.inicio_sistema_at:
            try:
                inicio_sis = datetime.fromisoformat(dto.inicio_sistema_at)
            except (ValueError, TypeError):
                inicio_sis = None

        fin_sis = None
        if dto.fin_sistema_at:
            try:
                fin_sis = datetime.fromisoformat(dto.fin_sistema_at)
            except (ValueError, TypeError):
                fin_sis = None

        duracion_sis = dto.duracion_sistema_segundos
        if duracion_sis is None and inicio_sis and fin_sis:
            duracion_sis = round((fin_sis - inicio_sis).total_seconds(), 2)

        fecha_val = datetime.now(timezone.utc) if estado == "verificado" else None
        validado_por = usuario_id if estado == "verificado" else None
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
            chatbot_prediccion=chatbot_prediccion_final,
            sistema_afectado_probable=sistema_probable,
            campos_completos=campos_completos,
            cantidad_campos_completos=cantidad_campos,
            detalles_campos=detalles_campos,
            tiempo_diagnostico_minutos=dto.tiempo_diagnostico_minutos,
            prediccion_correcta=dto.prediccion_correcta,
            metodo_confirmacion=(dto.metodo_confirmacion or "").strip() or None,
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
            tiempo_inferencia_ml_ms=tiempo_ml,
            inicio_sistema_at=inicio_sis,
            fin_sistema_at=fin_sis,
            duracion_sistema_segundos=duracion_sis,
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
            detalles={
                "item": caso.item,
                "fase": caso.fase,
                "estado_registro": caso.estado_registro,
                "tipo_registro": caso.tipo_registro,
            },
        )
        return caso

    async def metricas(
        self, taller_id: uuid.UUID, fecha_desde: date | None = None, fecha_hasta: date | None = None
    ) -> dict[str, Any]:
        grupos = await self.repo.resumen_por_fase(taller_id, fecha_desde, fecha_hasta)
        metricas_vi = await self.repo.metricas_variable_independiente(taller_id, fecha_desde, fecha_hasta)
        distribuciones = await self.repo.distribuciones(taller_id, fecha_desde, fecha_hasta)
        casos_piloto = await self.repo.contar_piloto(taller_id)
        total_v = int(metricas_vi.get("casos_verificados") or 0)
        resumen = resumir_fases(grupos)
        variable_independiente = {
            "indicador1_sintomas_correctos_pct": metricas_vi.get("porcentaje_sintomas_correctos"),
            "indicador2_procesamiento_correcto_pct": metricas_vi.get("porcentaje_datos_procesados_correctos"),
            "indicador3_exactitud_ml_pct": metricas_vi.get("exactitud_modelo_validada"),
            "casos_verificados_evaluados": total_v,
            "casos_sintomas_evaluados": metricas_vi.get("casos_sintomas_evaluados", 0),
            "casos_procesamiento_evaluados": metricas_vi.get("casos_procesamiento_evaluados", 0),
            "casos_modelo_evaluados": metricas_vi.get("casos_modelo_evaluados", 0),
            "nota_metodologica": (
                "Indicadores de CarBot calculados solo sobre casos POST-TEST oficiales "
                "con revisión humana trazable; no incluyen el diagnóstico manual PRE-TEST."
            ),
        }
        return {
            **resumen,
            **metricas_vi,
            "variable_independiente": variable_independiente,
            "casos_verificados": total_v,
            "casos_piloto": casos_piloto,
            "total_casos_verificados": resumen["total_casos"],
            **distribuciones,
        }
