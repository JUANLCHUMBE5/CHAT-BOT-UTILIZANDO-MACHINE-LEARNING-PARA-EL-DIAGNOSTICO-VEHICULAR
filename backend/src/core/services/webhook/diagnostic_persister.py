"""Módulo para persistencia de diagnósticos, hipótesis técnicas, costos y outbox en PostgreSQL."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.confirmacion_diagnostico import instrucciones_confirmacion_whatsapp
from src.config import settings
from src.core.gemini_queue import gemini_rate_limiter
from src.core.gestor_diagnostico import ResultadoDiagnostico
from src.core.sanitizer import sanitizar_prompt_usuario
from src.core.security import cifrar_texto_reversible
from src.core.traductor_jerga import normalizar_jerga_peruana
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.mensaje_repository import MensajeRepository
from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository
from src.infrastructure.database.repositories.vehiculo_repository import VehiculoRepository

COSTO_META_MENSAJE_SERVICIO_USD = Decimal(str(settings.meta_message_price_usd))


class DiagnosticPersister:
    """Persiste los resultados del motor diagnóstico y genera mensajes de salida."""

    @staticmethod
    async def persistir_y_responder(
        session: AsyncSession,
        dto: ResultadoDiagnostico,
        usuario: Any,
        conversacion: Any,
        texto_cliente: str,
        meta_message_id: str,
        remitente: str,
        proveedor: str,
        placa: str,
        marca_modelo: str,
        duracion_ms: int,
        corpus_version: str,
    ) -> tuple[dict[str, Any], Decimal]:
        """
        Guarda vehículo, diagnóstico, hipótesis, costos y encola respuesta en el outbox.
        Retorna los datos del diagnóstico completado y el costo de Gemini estimado.
        """
        diag_repo = DiagnosticoRepository(session)
        vehiculo_repo = VehiculoRepository(session)
        msg_repo = MensajeRepository(session)
        operaciones_repo = OperacionesRepository(session)

        # 1. Manejo de consultas informativas
        if dto.tipo_consulta != "diagnostico":
            if dto.modo_diagnostico == "consulta_tecnica_en_cola" and dto.solicitud_id:
                await gemini_rate_limiter.persistir_solicitud_en_sesion(
                    session,
                    solicitud_id=dto.solicitud_id,
                    sintoma=dto.sintoma_evaluado or texto_cliente,
                    diagnostico_ml="Consulta técnica informativa",
                    confianza_ml=0.0,
                    contexto_manual=dto.contexto_manual,
                    titulo_manual=dto.titulo_manual,
                    requiere_revision_humana=False,
                    diagnostico_id=None,
                    remitente=remitente,
                    proveedor=proveedor,
                    taller_id=str(usuario.taller_id),
                    usuario_id=str(usuario.id),
                    conversacion_id=str(conversacion.id),
                    tipo_consulta="consulta_tecnica",
                )

            out_msg_id = f"out_{meta_message_id or uuid.uuid4()}"
            await msg_repo.crear_mensaje(
                conversacion_id=conversacion.id,
                taller_id=usuario.taller_id,
                usuario_id=usuario.id,
                meta_message_id=out_msg_id,
                direccion="salida",
                tipo="texto",
                texto=dto.respuesta_texto,
                categoria_cobro="servicio",
                estado_entrega="pendiente",
                costo_estimado=(
                    Decimal(str(settings.twilio_message_price_usd))
                    if proveedor == "twilio"
                    else COSTO_META_MENSAJE_SERVICIO_USD
                ),
                moneda="USD",
                proveedor=proveedor,
                destinatario_cifrado=cifrar_texto_reversible(remitente),
                disponible_entrega_en=datetime.now(timezone.utc),
            )
            await session.commit()
            return {
                "status": (
                    "consulta_tecnica"
                    if dto.tipo_consulta == "consulta_tecnica"
                    else dto.tipo_consulta
                ),
                "conversacion_id": str(conversacion.id),
                "respuesta": dto.respuesta_texto,
            }, Decimal("0")

        # 2. Agregar instrucciones de confirmación solo si no quedó en cola y no hay pregunta diagnóstica pendiente
        respuesta_texto = dto.respuesta_texto
        tiene_pregunta_activa = bool(
            respuesta_texto
            and (
                respuesta_texto.rstrip().endswith("?")
                or getattr(dto, "es_pregunta", False)
                or getattr(dto, "modo_diagnostico", "") == "esperando_clarificacion"
            )
        )
        if dto.modo_diagnostico != "en_cola_gemini" and not tiene_pregunta_activa:
            respuesta_texto = (
                respuesta_texto.rstrip()
                + instrucciones_confirmacion_whatsapp()
            )

        # 3. Asociar vehículo si aplica
        vehiculo = None
        if placa and placa not in ("WAPP-01", "REST-API", "SIN-PLACA"):
            vehiculo = await vehiculo_repo.obtener_o_crear(
                taller_id=usuario.taller_id,
                registrado_por_id=usuario.id,
                placa_str=placa,
                marca=marca_modelo.split()[0] if marca_modelo else "Generico",
            )

        # 4. Determinar fuente y conclusiones
        sintoma_original_cliente = texto_cliente or "[Nota de Audio]"
        sintoma_evaluado = dto.sintoma_evaluado or texto_cliente
        sintoma_norm = normalizar_jerga_peruana(sanitizar_prompt_usuario(sintoma_evaluado))

        # Sanitizar procedencia RAG documental si no está verificada como OEM oficial
        contexto_manual_limpio = re.sub(
            r"tolerancias\s+y\s+especificaciones\s+metrológicas\s+oem:?",
            "Valores del procedimiento técnico recuperado:",
            dto.contexto_manual or "",
            flags=re.IGNORECASE,
        )
        contexto_manual_limpio = re.sub(
            r"especificaciones\s+metrológicas\s+oem:?",
            "valores del procedimiento técnico recuperado:",
            contexto_manual_limpio,
            flags=re.IGNORECASE,
        )

        modo_diag = dto.modo_diagnostico
        if modo_diag == "saludo":
            fuente_diag = "regla"
            conclusion_diag = "[SALUDO] Contacto inicial o saludo conversacional"
        elif modo_diag == "esperando_clarificacion":
            fuente_diag = "regla"
            conclusion_diag = "[ESPERANDO_CLARIFICACION] Consulta ambigua, se requiere especificación de síntomas"
        elif modo_diag == "baja_confianza":
            fuente_diag = "ml"
            conclusion_diag = f"[BAJA_CONFIANZA] Confianza ML inferior al umbral ({int(dto.confianza_ml * 100)}%)"
        elif modo_diag == "en_cola_gemini":
            fuente_diag = "hibrido"
            conclusion_diag = f"[EN_COLA_GEMINI] Solicitud encolada en posición #{dto.posicion_cola}"
        elif dto.llm_usado or modo_diag == "completo_ml_rag_llm":
            fuente_diag = "gemini"
            conclusion_diag = f"[COMPLETO_ML_RAG_LLM] Síntesis Gemini ({dto.llm_modelo or settings.gemini_model})"
        else:
            fuente_diag = "hibrido"
            conclusion_diag = "[DIAGNOSTICO_DEGRADADO_ML_RAG] Fallback por indisponibilidad o límite de tasa"

        # 5. Persistir diagnóstico con trazabilidad completa
        diag = await diag_repo.crear_diagnostico(
            taller_id=usuario.taller_id,
            mecanico_id=usuario.id,
            conversacion_id=conversacion.id,
            vehiculo_id=vehiculo.id if vehiculo else None,
            sintoma_original=sintoma_original_cliente,
            sintoma_normalizado=sintoma_norm,
            falla_predicha=dto.diagnostico_ml,
            confianza=dto.confianza_ml,
            similitud_rag=dto.similitud_rag,
            fuente=fuente_diag,
            modo_diagnostico=modo_diag,
            estado="generado",
            duracion_ms=duracion_ms,
            tiempo_inferencia_ml_ms=dto.tiempo_ml_ms,
            conclusion_mecanico=conclusion_diag,
            version_modelo_ml=settings.model_version,
            version_corpus_rag=corpus_version,
            trazabilidad={
                "version": 1,
                "predicciones_ml": [pred.model_dump() for pred in dto.predicciones_ml],
                "top3_ml_raw": [pred.model_dump() for pred in dto.predicciones_ml[:3]],
                "hipotesis_final_presentada": [{"falla": dto.diagnostico_ml, "probabilidad": dto.confianza_ml}],
                "etapas": [
                    {
                        "clave": "normalizacion",
                        "nombre": "Normalización del síntoma",
                        "estado": "completado",
                        "duracion_ms": 0,
                        "detalle": sintoma_norm,
                    },
                    {
                        "clave": "ml",
                        "nombre": settings.model_algorithm,
                        "estado": "completado",
                        "duracion_ms": dto.tiempo_ml_ms,
                        "detalle": f"{len(dto.predicciones_ml)} clases comparadas en el resumen",
                    },
                    {
                        "clave": "rag",
                        "nombre": "Búsqueda RAG en manuales",
                        "estado": "completado" if dto.contexto_manual else "sin_resultado",
                        "duracion_ms": dto.tiempo_rag_ms,
                        "detalle": dto.titulo_manual or "Sin coincidencia documental",
                    },
                    {
                        "clave": "llm",
                        "nombre": "Síntesis técnica Gemini" if (dto.llm_usado or dto.modo_diagnostico == "en_cola_gemini") else "Síntesis técnica Gemini (Fallback ML+RAG)",
                        "estado": "en_cola" if dto.modo_diagnostico == "en_cola_gemini" else ("completado" if dto.llm_usado else "degradado"),
                        "duracion_ms": dto.tiempo_llm_ms,
                        "detalle": (dto.llm_modelo or settings.gemini_model) if dto.llm_usado else ("En cola de procesamiento" if dto.modo_diagnostico == "en_cola_gemini" else "Fallback determinista: cuota/indisponibilidad"),
                    },
                ],
                "gemini": {
                    "usado": dto.llm_usado,
                    "modelo": dto.llm_modelo,
                    "tokens_entrada": dto.tokens_entrada,
                    "tokens_salida": dto.tokens_salida,
                    "posicion_cola": dto.posicion_cola,
                },
                "desde_cache": dto.desde_cache,
                "tiempo_total_ms": dto.tiempo_total_ms or duracion_ms,
            },
        )

        # 6. Actualizar validación diagnóstica en conversación si no está en cola y no hay pregunta activa
        if dto.modo_diagnostico != "en_cola_gemini" and not tiene_pregunta_activa:
            contexto_conversacion = dict(conversacion.contexto or {})
            contexto_conversacion["validacion_diagnostico"] = {
                "diagnostico_id": str(diag.id),
                "etapa": "esperando_confirmacion",
            }
            conversacion.contexto = contexto_conversacion
        elif tiene_pregunta_activa and conversacion and getattr(conversacion, "contexto", None):
            contexto_conversacion = dict(conversacion.contexto or {})
            contexto_conversacion.pop("validacion_diagnostico", None)
            conversacion.contexto = contexto_conversacion

        # 7. Si quedó en cola, persistir en tabla de trabajos
        if dto.modo_diagnostico == "en_cola_gemini" and dto.solicitud_id:
            await gemini_rate_limiter.persistir_solicitud_en_sesion(
                session,
                solicitud_id=dto.solicitud_id,
                sintoma=sintoma_evaluado,
                diagnostico_ml=dto.diagnostico_ml,
                confianza_ml=dto.confianza_ml,
                contexto_manual=dto.contexto_manual,
                titulo_manual=dto.titulo_manual,
                requiere_revision_humana=dto.requiere_revision_humana,
                diagnostico_id=str(diag.id),
                remitente=remitente,
                proveedor=proveedor,
                taller_id=str(usuario.taller_id),
                usuario_id=str(usuario.id),
                conversacion_id=str(conversacion.id),
            )

        # 8. Guardar hipótesis diagnóstica priorizada
        fuente_documental = "Corpus local preliminar no validado como OEM"
        titulo_procedimiento = dto.titulo_manual.strip() if dto.titulo_manual else "Sin título recuperado"
        evidencia = (
            f"Fuente: {fuente_documental}. "
            f"Procedimiento: {titulo_procedimiento}. "
            f"Corpus: {corpus_version}. "
            f"Clasificador ML TF-IDF: {int(dto.confianza_ml * 100)}% de confianza"
        )
        proc_recomendado = (
            dto.contexto_manual.strip()
            if dto.contexto_manual and dto.contexto_manual.strip()
            else "Sin procedimiento RAG registrado"
        )
        predicciones_a_guardar = dto.predicciones_ml or []
        if not predicciones_a_guardar:
            predicciones_a_guardar = [
                {"falla": dto.diagnostico_ml, "probabilidad": dto.confianza_ml}
            ]
        for orden, prediccion in enumerate(predicciones_a_guardar[:3], start=1):
            falla = getattr(prediccion, "falla", None) or prediccion.get("falla", dto.diagnostico_ml)
            probabilidad = getattr(prediccion, "probabilidad", None)
            if probabilidad is None:
                probabilidad = prediccion.get("probabilidad", dto.confianza_ml)
            await diag_repo.agregar_hipotesis(
                diagnostico_id=diag.id,
                orden=orden,
                falla_probable=falla,
                confianza=probabilidad,
                evidencia=evidencia if orden == 1 else f"Alternativa calculada por {settings.model_algorithm}.",
                prueba_recomendada=proc_recomendado if orden == 1 else None,
                resultado="pendiente",
            )

        # 9. Costos de Gemini LLM
        costo_gemini = Decimal("0")
        if dto.llm_usado:
            tokens_in = dto.tokens_entrada
            tokens_out = dto.tokens_salida
            if settings.gemini_use_free_tier:
                costo_gemini = Decimal("0.000000")
            else:
                precio_in = Decimal(str(settings.gemini_input_price_per_million / 1_000_000))
                precio_out = Decimal(str(settings.gemini_output_price_per_million / 1_000_000))
                costo_gemini = Decimal(tokens_in) * precio_in + Decimal(tokens_out) * precio_out

            await operaciones_repo.registrar_uso_api(
                taller_id=usuario.taller_id,
                proveedor="google",
                operacion="gemini_generacion_diagnostico",
                modelo=dto.llm_modelo or settings.gemini_model,
                tokens_entrada=tokens_in,
                tokens_salida=tokens_out,
                unidades=Decimal(str(tokens_in + tokens_out)),
                costo_estimado=costo_gemini,
                moneda="USD",
                diagnostico_id=diag.id,
            )

        # 10. Persistir mensaje saliente en outbox
        out_msg_id = f"out_{meta_message_id or uuid.uuid4()}"
        await msg_repo.crear_mensaje(
            conversacion_id=conversacion.id,
            taller_id=usuario.taller_id,
            usuario_id=usuario.id,
            meta_message_id=out_msg_id,
            direccion="salida",
            tipo="texto",
            texto=respuesta_texto,
            categoria_cobro="servicio",
            estado_entrega="pendiente",
            costo_estimado=(
                Decimal(str(settings.twilio_message_price_usd))
                if proveedor == "twilio"
                else COSTO_META_MENSAJE_SERVICIO_USD
            ),
            moneda="USD",
            proveedor=proveedor,
            destinatario_cifrado=cifrar_texto_reversible(remitente),
            disponible_entrega_en=datetime.now(timezone.utc),
        )

        await session.commit()
        return {
            "status": "completado",
            "diagnostico_id": str(diag.id),
            "conversacion_id": str(conversacion.id),
            "falla_predicha": dto.diagnostico_ml,
            "confianza": float(dto.confianza_ml),
            "similitud_rag": float(dto.similitud_rag),
            "tiempo_ml_ms": duracion_ms,
            "envio_whatsapp": "pendiente",
        }, costo_gemini
