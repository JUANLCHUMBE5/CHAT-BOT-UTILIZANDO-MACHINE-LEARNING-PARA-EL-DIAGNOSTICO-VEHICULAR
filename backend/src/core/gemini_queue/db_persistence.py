"""Persistencia en PostgreSQL para la cola de Gemini, outbox de WhatsApp y cuota compartida."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.gemini_queue.models import (
    COSTO_META_MENSAJE_SERVICIO_USD,
    SolicitudGeminiEncolada,
)
from src.core.logger import logger
from src.core.security import cifrar_texto_reversible, descifrar_texto_reversible
from src.core.services.whatsapp_provider import whatsapp_provider_service
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.conversacion_repository import ConversacionRepository
from src.infrastructure.database.repositories.cuota_gemini_repository import CuotaGeminiRepository
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.mensaje_repository import MensajeRepository
from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository
from src.infrastructure.database.repositories.trabajo_gemini_repository import TrabajoGeminiRepository


async def persistir_estado_local_db(estado: dict[str, Any]) -> None:
    """Replica el estado local en PostgreSQL para coordinar todos los workers."""
    if not database_configurada():
        return
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        async with session.begin():
            await CuotaGeminiRepository(session).registrar_resultado_externo(
                exitoso=estado["estado"] == "disponible",
                codigo_http=estado["ultimo_codigo_http"],
                error=estado["ultimo_error"],
                retry_after_segundos=estado["cooldown_segundos"],
            )


async def obtener_estado_gemini_compartido(local_state: dict[str, Any], api_key_valida: bool) -> dict[str, Any]:
    """Prioriza el último estado persistido para que todos los workers informen lo mismo."""
    if not api_key_valida or not database_configurada():
        return local_state
    try:
        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            compartido = await CuotaGeminiRepository(session).obtener_estado_externo()
    except Exception as exc:
        logger.debug(f"[Gemini Health DB] No se pudo leer estado compartido: {exc}")
        return local_state
    if not compartido or compartido["ultima_verificacion"] is None:
        return local_state

    codigo = compartido["ultimo_codigo_http"]
    error = compartido["ultimo_error"]
    cooldown = compartido["cooldown_segundos"]
    if codigo == 429 or cooldown > 0:
        estado = "degradado_sin_cuota"
    elif error:
        estado = "degradado"
    else:
        estado = "disponible"
    return {
        "estado": estado,
        "disponible": estado == "disponible",
        "ultima_verificacion": compartido["ultima_verificacion"].isoformat(),
        "ultimo_exito": (
            compartido["ultimo_exito"].isoformat()
            if compartido["ultimo_exito"]
            else None
        ),
        "ultimo_codigo_http": codigo,
        "ultimo_error": error,
        "cooldown_segundos": cooldown,
    }


async def marcar_trabajo_reintento_db(
    solicitud_id: str,
    error: str,
    espera_segundos: int = 15,
) -> None:
    """Marca el trabajo en base de datos para reintento con backoff."""
    try:
        trabajo_id = uuid.UUID(solicitud_id)
    except (ValueError, TypeError):
        return
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        async with session.begin():
            await TrabajoGeminiRepository(session).marcar_reintento(
                trabajo_id,
                espera_segundos=espera_segundos,
                error_mensaje=error,
            )


async def posponer_trabajo_por_cuota_db(solicitud_id: str, motivo: str) -> None:
    """Libera el lease sin contar un intento porque Gemini no fue invocado."""
    try:
        trabajo_id = uuid.UUID(solicitud_id)
    except (ValueError, TypeError):
        return
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        async with session.begin():
            await TrabajoGeminiRepository(session).posponer_por_cuota(
                trabajo_id, espera_segundos=5, motivo=motivo
            )


async def marcar_trabajo_fallido_db(solicitud_id: str, error: str) -> None:
    """Marca el trabajo como fallido definitivamente tras exceder reintentos."""
    try:
        trabajo_id = uuid.UUID(solicitud_id)
    except (ValueError, TypeError):
        return
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        async with session.begin():
            await TrabajoGeminiRepository(session).marcar_fallido(trabajo_id, error)


async def persistir_solicitud_en_sesion_db(
    session: AsyncSession,
    *,
    solicitud_id: str,
    sintoma: str,
    diagnostico_ml: str,
    confianza_ml: float,
    contexto_manual: str,
    titulo_manual: str,
    requiere_revision_humana: bool,
    remitente: Optional[str] = None,
    proveedor: str = "meta",
    taller_id: Optional[str] = None,
    usuario_id: Optional[str] = None,
    conversacion_id: Optional[str] = None,
    diagnostico_id: Optional[str] = None,
    tipo_consulta: str = "diagnostico",
) -> None:
    """Persiste el trabajo de Gemini en la misma transacción del webhook."""
    proveedor_normalizado = "meta" if (proveedor or "").lower() in ("meta", "whatsapp") else (proveedor or "meta").lower()
    if proveedor_normalizado not in {"meta", "twilio", "api"}:
        raise ValueError(f"Proveedor de cola no soportado: {proveedor}")

    repo = TrabajoGeminiRepository(session)
    await repo.crear_trabajo(
        trabajo_id=uuid.UUID(solicitud_id),
        sintoma=sintoma,
        diagnostico_ml=diagnostico_ml,
        confianza_ml=confianza_ml,
        contexto_manual=contexto_manual,
        titulo_manual=titulo_manual,
        requiere_revision_humana=requiere_revision_humana,
        remitente=remitente,
        proveedor=proveedor_normalizado,
        tipo_consulta=tipo_consulta,
        taller_id=uuid.UUID(taller_id) if taller_id else None,
        usuario_id=uuid.UUID(usuario_id) if usuario_id else None,
        conversacion_id=uuid.UUID(conversacion_id) if conversacion_id else None,
        diagnostico_id=uuid.UUID(diagnostico_id) if diagnostico_id else None,
    )


async def procesar_siguiente_entrega_whatsapp() -> bool:
    """Reclama, envía y actualiza un mensaje del outbox."""
    mensaje = None
    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        async with session.begin():
            mensaje = await MensajeRepository(session).obtener_siguiente_salida_bloqueada()
    if not mensaje:
        return False

    try:
        destino = descifrar_texto_reversible(mensaje.destinatario_cifrado)
    except ValueError as exc:
        resultado_estado, externo, error = "fallido", None, str(exc)
    else:
        resultado = await whatsapp_provider_service.enviar(
            mensaje.proveedor or "meta", destino, mensaje.texto or ""
        )
        externo = resultado.id_externo
        error = resultado.error
        if resultado.exitoso:
            resultado_estado = "enviado"
        elif resultado.reintentable and mensaje.intentos_entrega < 3:
            resultado_estado = "pendiente_reintento"
        else:
            resultado_estado = "fallido"

    async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
        async with session.begin():
            await MensajeRepository(session).registrar_resultado_entrega(
                mensaje.id,
                estado=resultado_estado,
                id_externo=externo,
                error=error,
                reintentar_en_segundos=min(300, 15 * (2 ** max(0, mensaje.intentos_entrega - 1))),
            )
    return True


async def actualizar_diagnostico_y_trabajo_db(
    solicitud: SolicitudGeminiEncolada, texto_respuesta: str, metadatos: dict
) -> None:
    """Actualiza el estado de la fila en PostgreSQL y marca el trabajo como completado."""
    try:
        db_engine = obtener_engine()
        modo_final = metadatos.get("modo", "completo_ml_rag_llm")
        fuente_final = "gemini" if metadatos.get("usado") else "hibrido"
        conclusion_final = (
            f"[{modo_final.upper()}] Síntesis Gemini ({metadatos.get('modelo') or settings.gemini_model})"
            if metadatos.get("usado")
            else f"[{modo_final.upper()}] Fallback tras salida de cola"
        )

        async with AsyncSession(db_engine, expire_on_commit=False) as session:
            async with session.begin():
                # 1. Actualizar trabajo_gemini
                trabajo_repo = TrabajoGeminiRepository(session)
                trabajo_id = None
                try:
                    trabajo_id = uuid.UUID(solicitud.id)
                except ValueError:
                    pass

                if trabajo_id:
                    await trabajo_repo.marcar_completado(trabajo_id)

                # 2. Actualizar diagnostico
                if solicitud.diagnostico_id:
                    diag_repo = DiagnosticoRepository(session)
                    diag = await diag_repo.obtener_por_id(uuid.UUID(solicitud.diagnostico_id))
                    if diag:
                        diag.modo_diagnostico = modo_final
                        diag.fuente = fuente_final
                        diag.sintesis_llm = texto_respuesta
                        trazabilidad = dict(diag.trazabilidad or {})
                        if not trazabilidad.get("validacion_tecnica"):
                            diag.conclusion_mecanico = conclusion_final
                        trazabilidad["gemini"] = {
                            "usado": bool(metadatos.get("usado")),
                            "modelo": metadatos.get("modelo") or settings.gemini_model,
                            "tokens_entrada": int(metadatos.get("tokens_entrada", 0)),
                            "tokens_salida": int(metadatos.get("tokens_salida", 0)),
                            "posicion_cola": 0,
                        }
                        etapas = list(trazabilidad.get("etapas") or [])
                        for etapa in etapas:
                            if etapa.get("clave") == "llm":
                                etapa["estado"] = "completado" if metadatos.get("usado") else "degradado"
                                etapa["detalle"] = metadatos.get("modelo") or settings.gemini_model
                                etapa["duracion_ms"] = int(metadatos.get("tiempo_llm_ms", 0))
                        trazabilidad["etapas"] = etapas
                        trazabilidad["tiempo_total_ms"] = int(
                            trazabilidad.get("tiempo_total_ms", 0)
                        ) + int(metadatos.get("tiempo_llm_ms", 0))
                        diag.trazabilidad = trazabilidad
                        diag.duracion_ms = int(trazabilidad["tiempo_total_ms"])

                        if not solicitud.predicciones_ml and diag.hipotesis:
                            solicitud.predicciones_ml = [
                                {"falla": h.falla_probable, "probabilidad": float(h.confianza)}
                                for h in sorted(diag.hipotesis, key=lambda x: x.orden)
                            ]

                        if metadatos.get("usado"):
                            operaciones_repo = OperacionesRepository(session)
                            tokens_in = metadatos.get("tokens_entrada", 0)
                            tokens_out = metadatos.get("tokens_salida", 0)

                            if settings.gemini_use_free_tier:
                                costo = Decimal("0.000000")
                            else:
                                p_in = Decimal(str(settings.gemini_input_price_per_million / 1_000_000))
                                p_out = Decimal(str(settings.gemini_output_price_per_million / 1_000_000))
                                costo = Decimal(tokens_in) * p_in + Decimal(tokens_out) * p_out

                            await operaciones_repo.registrar_uso_api(
                                taller_id=diag.taller_id,
                                proveedor="google",
                                operacion="gemini_generacion_diagnostico_cola",
                                modelo=metadatos.get("modelo") or settings.gemini_model,
                                tokens_entrada=tokens_in,
                                tokens_salida=tokens_out,
                                unidades=Decimal(str(tokens_in + tokens_out)),
                                costo_estimado=costo,
                                moneda="USD",
                                diagnostico_id=diag.id,
                            )
                elif metadatos.get("usado") and solicitud.taller_id:
                    tokens_in = int(metadatos.get("tokens_entrada", 0))
                    tokens_out = int(metadatos.get("tokens_salida", 0))
                    if settings.gemini_use_free_tier:
                        costo = Decimal("0.000000")
                    else:
                        p_in = Decimal(str(settings.gemini_input_price_per_million / 1_000_000))
                        p_out = Decimal(str(settings.gemini_output_price_per_million / 1_000_000))
                        costo = Decimal(tokens_in) * p_in + Decimal(tokens_out) * p_out
                    await OperacionesRepository(session).registrar_uso_api(
                        taller_id=uuid.UUID(solicitud.taller_id),
                        proveedor="google",
                        operacion="gemini_consulta_tecnica_cola",
                        modelo=metadatos.get("modelo") or settings.gemini_model,
                        tokens_entrada=tokens_in,
                        tokens_salida=tokens_out,
                        unidades=Decimal(str(tokens_in + tokens_out)),
                        costo_estimado=costo,
                        moneda="USD",
                        diagnostico_id=None,
                    )
                logger.info(
                    f"[Gemini Worker DB] Diagnóstico {solicitud.diagnostico_id or solicitud.id[:8]} actualizado en DB -> {modo_final}."
                )
    except Exception as e:
        logger.error(f"[Gemini Worker DB Update Error] {e}")
        raise


async def persistir_mensaje_saliente_db(
    solicitud: SolicitudGeminiEncolada, texto_respuesta: str, estado_entrega: str
) -> None:
    """Persiste el segundo mensaje de salida (síntesis de Gemini) en la tabla `mensajes` de PostgreSQL."""
    try:
        db_engine = obtener_engine()
        out_msg_id = f"out_gemini_{uuid.uuid4()}"
        texto_completo = texto_respuesta
        costo_msg = (
            Decimal(str(getattr(settings, "twilio_message_price_usd", 0.0)))
            if solicitud.proveedor == "twilio"
            else COSTO_META_MENSAJE_SERVICIO_USD
        )

        async with AsyncSession(db_engine, expire_on_commit=False) as session:
            async with session.begin():
                msg_repo = MensajeRepository(session)
                await msg_repo.crear_mensaje(
                    conversacion_id=uuid.UUID(solicitud.conversacion_id),
                    taller_id=uuid.UUID(solicitud.taller_id) if solicitud.taller_id else None,
                    usuario_id=uuid.UUID(solicitud.usuario_id) if solicitud.usuario_id else None,
                    meta_message_id=out_msg_id,
                    direccion="salida",
                    tipo="texto",
                    texto=texto_completo,
                    categoria_cobro="servicio",
                    estado_entrega="pendiente",
                    costo_estimado=costo_msg,
                    moneda="USD",
                    proveedor=("meta" if solicitud.proveedor == "whatsapp" else solicitud.proveedor),
                    destinatario_cifrado=(
                        cifrar_texto_reversible(solicitud.remitente)
                        if solicitud.remitente else None
                    ),
                    disponible_entrega_en=datetime.now(timezone.utc),
                )
                if solicitud.diagnostico_id:
                    conversacion = await ConversacionRepository(session).obtener_por_id(
                        uuid.UUID(solicitud.conversacion_id)
                    )
                    if conversacion:
                        contexto = dict(conversacion.contexto or {})
                        contexto["validacion_diagnostico"] = {
                            "diagnostico_id": solicitud.diagnostico_id,
                            "etapa": "esperando_confirmacion",
                        }
                        conversacion.contexto = contexto
            logger.info(
                f"[Gemini Worker DB] Segundo mensaje de síntesis guardado en DB para conv {solicitud.conversacion_id[:8]}."
            )
    except Exception as e:
        logger.error(f"[Gemini Worker DB Message Save Error] {e}")
        raise
