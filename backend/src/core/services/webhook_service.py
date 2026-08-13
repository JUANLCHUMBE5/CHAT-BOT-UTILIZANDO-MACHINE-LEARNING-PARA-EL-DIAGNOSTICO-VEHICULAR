"""
Servicio de orquestación para el procesamiento del Webhook de WhatsApp con PostgreSQL.

Flujo de ejecución:
1. Deduplicación por meta_message_id.
2. Identificación del mecánico mediante HMAC-SHA256 del número de WhatsApp.
3. Rechazo automático de números no registrados/inactivos.
4. Obtención o apertura de conversación con ventana de 24 horas.
5. Persistencia del mensaje recibido y registro de costo Meta.
6. Ejecución del diagnóstico ML + RAG + Gemini / Audio.
7. Persistencia del diagnóstico, hipótesis técnicas, confianza y latencia.
8. Registro de consumo de tokens y costo estimado de Gemini.
9. Persistencia del mensaje saliente y envío a WhatsApp Graph API.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import requests
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.gemini_queue import gemini_rate_limiter
from src.core.gestor_diagnostico import GestorDiagnostico, ResultadoDiagnostico
from src.core.logger import logger
from src.core.sanitizer import sanitizar_prompt_usuario
from src.core.security import (
    anonimizar_identificador,
    cifrar_texto_reversible,
    hash_identificador_persistencia,
)
from src.core.services.cliente_service import ClienteService
from src.core.services.whatsapp_provider import whatsapp_provider_service
from src.core.traductor_jerga import normalizar_jerga_peruana
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.conversacion_repository import ConversacionRepository
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.identidad_whatsapp_repository import IdentidadWhatsAppRepository
from src.infrastructure.database.repositories.mensaje_repository import MensajeRepository
from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository
from src.infrastructure.database.repositories.vehiculo_repository import VehiculoRepository

# Tarifas de costo estimado
COSTO_META_MENSAJE_SERVICIO_USD = Decimal(str(settings.meta_message_price_usd))
PRECIO_GEMINI_INPUT_POR_TOKEN_USD = Decimal("0.000000075")  # ~$0.075 / 1M tokens
PRECIO_GEMINI_OUTPUT_POR_TOKEN_USD = Decimal("0.000000300")  # ~$0.300 / 1M tokens


class WebhookService:
    """Orquestador thread-safe de la lógica de negocio y persistencia del Webhook."""

    def __init__(self, gestor_diagnostico: Optional[GestorDiagnostico] = None):
        self.gestor = gestor_diagnostico or GestorDiagnostico()

    async def actualizar_estado_entrega_externo(self, id_externo: str, estado: str) -> bool:
        """Relaciona callbacks Meta/Twilio con el ID externo guardado en el outbox."""
        mapa = {
            "queued": "enviado", "sent": "enviado", "delivered": "entregado",
            "read": "leido", "failed": "fallido", "undelivered": "fallido",
        }
        estado_db = mapa.get(estado.lower())
        if not id_externo or not estado_db or not database_configurada():
            return False
        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            async with session.begin():
                mensaje = await MensajeRepository(session).actualizar_estado_por_id_externo(
                    id_externo, estado_db
                )
                return mensaje is not None

    def enviar_mensaje_whatsapp(self, numero_destino: str, texto: str) -> bool:
        """Envía el mensaje de respuesta mediante la API Graph de Meta WhatsApp."""
        token_activo = settings.meta_access_token
        telefono_id_activo = settings.meta_phone_number_id

        if not token_activo or not telefono_id_activo:
            logger.info("Envío WhatsApp omitido (falta META_ACCESS_TOKEN o META_PHONE_NUMBER_ID).")
            return False

        if not numero_destino or numero_destino.startswith("test"):
            return False

        version = settings.meta_graph_api_version.strip("/")
        url = f"https://graph.facebook.com/{version}/{telefono_id_activo}/messages"
        headers = {
            "Authorization": f"Bearer {token_activo}",
            "Content-Type": "application/json",
        }
        data = {
            "messaging_product": "whatsapp",
            "to": numero_destino,
            "type": "text",
            "text": {"body": texto},
        }
        try:
            res = requests.post(url, headers=headers, json=data, timeout=8)
            rem_anon = anonimizar_identificador(numero_destino)
            logger.info(f"Respuesta enviada a {rem_anon}. Status HTTP: {res.status_code}")
            return res.status_code in (200, 201)
        except Exception as exc:
            logger.error(f"Error al enviar mensaje vía Meta Graph API: {exc}")
            return False

    async def procesar_mensaje(
        self,
        remitente: str,
        meta_message_id: str,
        tipo_mensaje: str = "text",
        texto_cliente: str = "",
        audio_id: str = "",
        placa: str = "WAPP-01",
        marca_modelo: str = "Vehiculo Generico",
        proveedor: str = "meta",
        session_id: Optional[str] = None,
        tipo_identificador: str = "telefono",
        telefono_id_meta: Optional[str] = None,
        nombre_contacto: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Ejecuta el ciclo de vida completo del webhook con PostgreSQL y soporte multi-rol.
        """
        inicio = time.perf_counter()
        rem_anon = anonimizar_identificador(remitente)
        proveedor = "meta" if proveedor.lower() in ("meta", "whatsapp") else proveedor.lower()
        if proveedor not in {"meta", "twilio", "api"}:
            raise ValueError(f"Proveedor de webhook no soportado: {proveedor}")

        # Si PostgreSQL no está habilitado, procesar en modo desacoplado / offline
        if not database_configurada():
            logger.info(f"[Webhook Modo Sin BD] Procesando para usuario {rem_anon}")
            return await self._procesar_sin_base_datos(
                remitente=remitente,
                tipo_mensaje=tipo_mensaje,
                texto_cliente=texto_cliente,
                audio_id=audio_id,
                placa=placa,
                marca_modelo=marca_modelo,
                session_id=session_id,
                proveedor=proveedor,
            )

        # Modo persistente con PostgreSQL
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            try:
                usuario_repo = UsuarioRepository(session)
                identidad_repo = IdentidadWhatsAppRepository(session)
                taller_repo = TallerRepository(session)
                conv_repo = ConversacionRepository(session)
                msg_repo = MensajeRepository(session)
                diag_repo = DiagnosticoRepository(session)
                vehiculo_repo = VehiculoRepository(session)
                operaciones_repo = OperacionesRepository(session)

                # =========================================================
                # 1. DEDUPLICACIÓN DE MENSAJES (IDEMPOTENCIA)
                # =========================================================
                if meta_message_id and await msg_repo.existe_meta_message_id(meta_message_id):
                    logger.info(
                        f"[Webhook Deduplicación] Mensaje {meta_message_id} ya procesado. Descartando duplicado."
                    )
                    return {
                        "status": "duplicado_ignorado",
                        "meta_message_id": meta_message_id,
                        "tiempo_ms": round((time.perf_counter() - inicio) * 1000, 2),
                    }

                # =========================================================
                # 2. IDENTIFICACIÓN / AUTO-REGISTRO DEL CONTACTO
                # =========================================================
                # Normalizar tipo de identificador
                tipo_id_norm = tipo_identificador if tipo_identificador in ("telefono", "wa_id", "user_id") else "telefono"
                id_hash = hash_identificador_persistencia(remitente, tipo_id_norm)

                # Extraer ultimos 4 dígitos si aplica
                digits = "".join(c for c in remitente if c.isdigit())
                ultimos4 = digits[-4:] if len(digits) >= 4 else (digits.zfill(4) if digits else "0000")
                dest_cifrado = cifrar_texto_reversible(remitente)

                # Buscar en identidades_whatsapp
                identidad = await identidad_repo.buscar_por_hash(id_hash)
                usuario = identidad.usuario if identidad else None

                # Fallback a búsqueda directa en usuarios
                if usuario is None:
                    usuario = await usuario_repo.buscar_por_whatsapp_hash(id_hash)
                    if usuario and not identidad:
                        # Crear registro en identidades_whatsapp para este usuario preexistente
                        identidad = await identidad_repo.registrar_identidad(
                            usuario_id=usuario.id,
                            identificador_hash=id_hash,
                            tipo_identificador=tipo_id_norm,
                            ultimos4=ultimos4,
                            proveedor=proveedor,
                            destinatario_cifrado=dest_cifrado,
                        )

                # Si no existe usuario -> Auto-registro como Cliente
                if usuario is None:
                    # 2.1 Asociar al taller correcto sin inventar datos
                    taller_asociado = await taller_repo.obtener_taller_para_webhook(telefono_id_meta)

                    if taller_asociado is None:
                        logger.error(
                            f"[Webhook Error] No se encontró taller activo para telefono_id_meta='{telefono_id_meta}'. "
                            "Se rechaza auto-registro para evitar cruce de datos."
                        )
                        return {
                            "status": "taller_no_encontrado",
                            "remitente": rem_anon,
                            "tiempo_ms": round((time.perf_counter() - inicio) * 1000, 2),
                        }

                    nombre_nuevo = (nombre_contacto.strip() if nombre_contacto and nombre_contacto.strip() else f"Cliente {ultimos4}")
                    usuario = await usuario_repo.crear_cliente_automatico(
                        taller_id=taller_asociado.id,
                        nombres=nombre_nuevo,
                        whatsapp_hash=id_hash,
                        whatsapp_ultimos4=ultimos4,
                    )
                    identidad = await identidad_repo.registrar_identidad(
                        usuario_id=usuario.id,
                        identificador_hash=id_hash,
                        tipo_identificador=tipo_id_norm,
                        ultimos4=ultimos4,
                        proveedor=proveedor,
                        destinatario_cifrado=dest_cifrado,
                    )
                    logger.info(
                        f"[Webhook Auto-Registro] Contacto {rem_anon} registrado automáticamente con rol cliente en taller {taller_asociado.nombre}."
                    )
                else:
                    if identidad:
                        await identidad_repo.actualizar_destinatario(
                            identidad.id,
                            destinatario_cifrado=dest_cifrado,
                            proveedor=proveedor,
                        )

                # =========================================================
                # 3. VERIFICACIÓN DE BLOQUEO, ESTADO ACTIVO Y TALLER ACTIVO
                # =========================================================
                if getattr(usuario, "bloqueado", False) or not getattr(usuario, "activo", True):
                    logger.warning(f"[Webhook Acceso Denegado] Contacto {rem_anon} bloqueado={getattr(usuario, 'bloqueado', False)} o activo={getattr(usuario, 'activo', True)}.")
                    mensaje_bloqueo = (
                        "🚫 *Acceso Restringido*\n\n"
                        "Tu número o usuario se encuentra temporalmente inactivo o bloqueado para interactuar con este servicio."
                    )
                    await whatsapp_provider_service.enviar(proveedor, remitente, mensaje_bloqueo)
                    return {
                        "status": "bloqueado",
                        "remitente": rem_anon,
                        "tiempo_ms": round((time.perf_counter() - inicio) * 1000, 2),
                    }

                if not usuario.taller or not usuario.taller.activo:
                    logger.warning(f"[Webhook Taller Inactivo] Taller inactivo para usuario {rem_anon}.")
                    mensaje_inactivo = (
                        "🔒 *Taller Temporalmente Fuera de Servicio*\n\n"
                        "El taller asociado a tu cuenta se encuentra en mantenimiento o inactivo."
                    )
                    await whatsapp_provider_service.enviar(proveedor, remitente, mensaje_inactivo)
                    return {
                        "status": "taller_inactivo",
                        "remitente": rem_anon,
                        "tiempo_ms": round((time.perf_counter() - inicio) * 1000, 2),
                    }

                # =========================================================
                # 4. RECUPERAR O CREAR CONVERSACIÓN (VENTANA DE 24 HORAS)
                # =========================================================
                conversacion = await conv_repo.obtener_o_crear_activa(
                    taller_id=usuario.taller_id,
                    usuario_id=usuario.id,
                    canal="whatsapp" if proveedor in {"meta", "twilio"} else "api",
                    ventana_horas=24,
                )

                # =========================================================
                # 5. PERSISTIR MENSAJE ENTRANTE
                # =========================================================
                msg_in_id = uuid.uuid4()
                try:
                    async with session.begin_nested():
                        mensaje_in = await msg_repo.crear_mensaje(
                            conversacion_id=conversacion.id,
                            taller_id=usuario.taller_id,
                            usuario_id=usuario.id,
                            meta_message_id=meta_message_id or f"in_{msg_in_id}",
                            direccion="entrada",
                            tipo="texto" if tipo_mensaje == "text" else "audio",
                            texto=texto_cliente if tipo_mensaje == "text" else f"[Audio Meta: {audio_id}]",
                            categoria_cobro="servicio",
                            estado_entrega="recibido",
                            costo_estimado=COSTO_META_MENSAJE_SERVICIO_USD,
                            moneda="USD",
                            mensaje_id=msg_in_id,
                        )
                except IntegrityError:
                    logger.info(
                        f"[Webhook Deduplicación] Carrera concurrente resuelta para {meta_message_id}."
                    )
                    return {
                        "status": "duplicado_ignorado",
                        "meta_message_id": meta_message_id,
                        "tiempo_ms": round((time.perf_counter() - inicio) * 1000, 2),
                    }

                # Registrar costo operativo
                await operaciones_repo.registrar_uso_api(
                    taller_id=usuario.taller_id,
                    proveedor=proveedor,
                    operacion="webhook_mensaje_recibido",
                    solicitud_externa_id=meta_message_id,
                    tokens_entrada=0,
                    tokens_salida=0,
                    unidades=Decimal("1.0"),
                    costo_estimado=(
                        Decimal(str(settings.twilio_message_price_usd))
                        if proveedor == "twilio" else COSTO_META_MENSAJE_SERVICIO_USD
                    ),
                    moneda="USD",
                    mensaje_id=mensaje_in.id,
                )

                # =========================================================
                # 6. ENRUTAMIENTO POR ROL: CLIENTE vs MECÁNICO/ADMIN
                # =========================================================
                codigo_rol = usuario.rol.codigo if usuario.rol else "cliente"

                if codigo_rol == "cliente":
                    # =========================================================
                    # FLUJO CLIENTE (CERO ML / CERO RAG / CERO GEMINI)
                    # =========================================================
                    cliente_svc = ClienteService(session)
                    respuesta_texto = await cliente_svc.procesar_mensaje_cliente(
                        usuario=usuario,
                        taller=usuario.taller,
                        texto_usuario=texto_cliente,
                    )

                    # Guardar mensaje saliente en outbox
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
                    total_ms = (time.perf_counter() - inicio) * 1000
                    logger.info(
                        f"[Webhook Cliente] Respuesta enviada a cliente {usuario.nombres} ({rem_anon}) en {total_ms:.2f}ms"
                    )
                    return {
                        "status": "completado_cliente",
                        "conversacion_id": str(conversacion.id),
                        "respuesta": respuesta_texto,
                        "tiempo_total_ms": round(total_ms, 2),
                    }

                # =========================================================
                # 7. EJECUTAR DIAGNÓSTICO ML + RAG + GEMINI (MECÁNICOS / ADMIN)
                # =========================================================
                t_ml_inicio = time.perf_counter()
                id_sesion_str = str(conversacion.id)

                if tipo_mensaje == "audio":
                    try:
                        audio_bytes, mime_type = await whatsapp_provider_service.descargar_audio(
                            proveedor, audio_id
                        )
                        slot_audio, motivo_audio = await gemini_rate_limiter.intentar_adquirir_slot_db()
                        if not slot_audio:
                            raise RuntimeError(f"Transcripción temporalmente no disponible: {motivo_audio}")
                        texto_cliente = await asyncio.to_thread(
                            self.gestor.procesador_audio.transcribir_nota_de_voz,
                            audio_id,
                            audio_bytes,
                            mime_type,
                            self.gestor.api_key,
                        )
                    except Exception as exc:
                        logger.warning(f"[Audio WhatsApp] No se pudo transcribir: {exc}")
                        dto = ResultadoDiagnostico(
                            respuesta_texto=(
                                "🎤 No pude transcribir la nota de voz de forma segura. "
                                "Por favor, escribe el síntoma del vehículo en texto."
                            ),
                            diagnostico_ml="Audio pendiente de transcripción",
                            confianza_ml=0.0,
                            contexto_manual="",
                            titulo_manual="",
                            requiere_revision_humana=True,
                            estado_sesion="esperando_clarificacion",
                            modo_diagnostico="esperando_clarificacion",
                        )
                    else:
                        dto = await asyncio.to_thread(
                            self.gestor.procesar_consulta_texto,
                            texto_usuario=texto_cliente,
                            placa=placa,
                            marca_modelo=marca_modelo,
                            session_id=id_sesion_str,
                            remitente=remitente,
                            proveedor=proveedor,
                            taller_id=str(usuario.taller_id),
                            usuario_id=str(usuario.id),
                            conversacion_id=str(conversacion.id),
                            slot_gemini_preconcedido=False,
                            diferir_encolado_persistente=True,
                        )
                else:
                    dto = await asyncio.to_thread(
                        self.gestor.procesar_consulta_texto,
                        texto_usuario=texto_cliente,
                        placa=placa,
                        marca_modelo=marca_modelo,
                        session_id=id_sesion_str,
                        remitente=remitente,
                        proveedor=proveedor,
                        taller_id=str(usuario.taller_id),
                        usuario_id=str(usuario.id),
                        conversacion_id=str(conversacion.id),
                        # El webhook siempre deja la llamada a Gemini al worker.
                        # Así toda invocación usa la cuota global PostgreSQL y
                        # queda recuperable ante reinicios.
                        slot_gemini_preconcedido=False,
                        diferir_encolado_persistente=True,
                    )
                respuesta_texto = dto.respuesta_texto
                diagnostico_ml = dto.diagnostico_ml
                confianza_ml = dto.confianza_ml
                similitud_rag = dto.similitud_rag
                contexto_manual = dto.contexto_manual
                titulo_manual = dto.titulo_manual

                duracion_ms = int((time.perf_counter() - t_ml_inicio) * 1000)

                # =========================================================
                # 6. ASOCIAR VEHÍCULO (SI APLICA)
                # =========================================================
                vehiculo = None
                if placa and placa not in ("WAPP-01", "REST-API", "SIN-PLACA"):
                    vehiculo = await vehiculo_repo.obtener_o_crear(
                        taller_id=usuario.taller_id,
                        registrado_por_id=usuario.id,
                        placa_str=placa,
                        marca=marca_modelo.split()[0] if marca_modelo else "Generico",
                    )

                # =========================================================
                # 7. GUARDAR DIAGNÓSTICO E HIPÓTESIS TÉCNICAS
                # =========================================================
                sintoma_diagnostico = dto.sintoma_evaluado or texto_cliente
                sintoma_norm = normalizar_jerga_peruana(sanitizar_prompt_usuario(sintoma_diagnostico))
                
                modo_diag = dto.modo_diagnostico
                if modo_diag == "saludo":
                        fuente_diag = "regla"
                        conclusion_diag = "[SALUDO] Contacto inicial o saludo conversacional"
                elif modo_diag == "esperando_clarificacion":
                        fuente_diag = "regla"
                        conclusion_diag = "[ESPERANDO_CLARIFICACION] Consulta ambigua, se requiere especificación de síntomas"
                elif modo_diag == "baja_confianza":
                        fuente_diag = "ml"
                        conclusion_diag = f"[BAJA_CONFIANZA] Confianza ML inferior al umbral ({int(confianza_ml * 100)}%)"
                elif modo_diag == "en_cola_gemini":
                        fuente_diag = "hibrido"
                        conclusion_diag = f"[EN_COLA_GEMINI] Solicitud encolada en posición #{dto.posicion_cola}"
                elif dto.llm_usado or modo_diag == "completo_ml_rag_llm":
                        fuente_diag = "gemini"
                        conclusion_diag = f"[COMPLETO_ML_RAG_LLM] Síntesis Gemini ({dto.llm_modelo or settings.gemini_model})"
                else:
                        fuente_diag = "hibrido"
                        conclusion_diag = "[DIAGNOSTICO_DEGRADADO_ML_RAG] Fallback por indisponibilidad o límite de tasa"

                diag = await diag_repo.crear_diagnostico(
                    taller_id=usuario.taller_id,
                    mecanico_id=usuario.id,
                    conversacion_id=conversacion.id,
                    vehiculo_id=vehiculo.id if vehiculo else None,
                    sintoma_original=sintoma_diagnostico or "[Nota de Audio]",
                    sintoma_normalizado=sintoma_norm,
                    falla_predicha=diagnostico_ml,
                    confianza=confianza_ml,
                    similitud_rag=similitud_rag,
                    fuente=fuente_diag,
                    modo_diagnostico=modo_diag,
                    estado="generado",
                    duracion_ms=duracion_ms,
                    conclusion_mecanico=conclusion_diag,
                    version_modelo_ml=settings.model_version,
                    version_corpus_rag=getattr(self.gestor.motor_rag, "corpus_version", "desconocido"),
                )

                if dto.modo_diagnostico == "en_cola_gemini" and dto.solicitud_id:
                    await gemini_rate_limiter.persistir_solicitud_en_sesion(
                        session,
                        solicitud_id=dto.solicitud_id,
                        sintoma=sintoma_diagnostico,
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

                # Guardar hipótesis diagnóstica priorizada con procedimiento RAG real
                fuente_documental = "Corpus local preliminar no validado como OEM"
                titulo_procedimiento = titulo_manual.strip() if titulo_manual else "Sin título recuperado"
                evidencia = (
                    f"Fuente: {fuente_documental}. "
                    f"Procedimiento: {titulo_procedimiento}. "
                    f"Corpus: {getattr(self.gestor.motor_rag, 'corpus_version', 'v1.0')}. "
                    f"Clasificador ML TF-IDF: {int(confianza_ml * 100)}% de confianza"
                )
                proc_recomendado = (
                    contexto_manual.strip()
                    if contexto_manual and contexto_manual.strip()
                    else "Sin procedimiento RAG registrado"
                )
                await diag_repo.agregar_hipotesis(
                    diagnostico_id=diag.id,
                    orden=1,
                    falla_probable=diagnostico_ml,
                    confianza=confianza_ml,
                    evidencia=evidencia,
                    prueba_recomendada=proc_recomendado,
                    resultado="pendiente",
                )

                # =========================================================
                # 8. REGISTRAR CONSUMO Y COSTO DE GEMINI LLM
                # =========================================================
                costo_gemini = Decimal("0")
                if dto.llm_usado:
                    tokens_in = dto.tokens_entrada
                    tokens_out = dto.tokens_salida
                    
                    if settings.gemini_use_free_tier:
                        costo_gemini = Decimal("0.000000")
                    else:
                        precio_in = Decimal(str(settings.gemini_input_price_per_million / 1_000_000))
                        precio_out = Decimal(str(settings.gemini_output_price_per_million / 1_000_000))
                        costo_gemini = (Decimal(tokens_in) * precio_in + Decimal(tokens_out) * precio_out)

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

                # =========================================================
                # 9. GUARDAR MENSAJE SALIENTE Y ENVIAR RESPUESTA
                # =========================================================
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

                # Confirmar transacción en PostgreSQL
                await session.commit()

                # El outbox durable será enviado/reintentado por el worker.
                total_ms = (time.perf_counter() - inicio) * 1000
                logger.info(
                    f"[Webhook Procesado] Diagnóstico '{diagnostico_ml}' guardado en DB para mecánico {usuario.nombres} en {total_ms:.2f}ms"
                )

                return {
                    "status": "completado",
                    "diagnostico_id": str(diag.id),
                    "conversacion_id": str(conversacion.id),
                    "falla_predicha": diagnostico_ml,
                    "confianza": float(confianza_ml),
                    "similitud_rag": float(similitud_rag),
                    "tiempo_total_ms": round(total_ms, 2),
                    "tiempo_ml_ms": duracion_ms,
                    "costo_estimado_usd": float(costo_gemini),
                    "envio_whatsapp": "pendiente",
                }

            except Exception as exc:
                await session.rollback()
                logger.error(f"[Webhook Error] Fallo al procesar y persistir: {exc}")
                raise

    async def _procesar_sin_base_datos(
        self,
        remitente: str,
        tipo_mensaje: str,
        texto_cliente: str,
        audio_id: str,
        placa: str,
        marca_modelo: str,
        session_id: Optional[str],
        proveedor: str = "meta",
    ) -> dict[str, Any]:
        """Fallback seguro cuando PostgreSQL no está activado."""
        t0 = time.perf_counter()
        if tipo_mensaje == "audio":
            respuesta = (
                "No puedo procesar audios sin persistencia y control de cuota activos. "
                "Envia el sintoma por texto para continuar de forma segura."
            )
            diag_ml = "Análisis Acústico Espectral"
            conf = 0.0
            diag_ml = "Audio no procesado"
        else:
            dto = self.gestor.procesar_consulta_texto(
                texto_usuario=texto_cliente,
                placa=placa,
                marca_modelo=marca_modelo,
                session_id=session_id or remitente,
                proveedor=proveedor,
            )
            respuesta = dto.respuesta_texto
            diag_ml = dto.diagnostico_ml
            conf = dto.confianza_ml

        await whatsapp_provider_service.enviar(proveedor, remitente, respuesta)
        elapsed = (time.perf_counter() - t0) * 1000
        return {
            "status": "completado_offline",
            "diagnostico_ml": diag_ml,
            "confianza": conf,
            "tiempo_ms": round(elapsed, 2),
        }
