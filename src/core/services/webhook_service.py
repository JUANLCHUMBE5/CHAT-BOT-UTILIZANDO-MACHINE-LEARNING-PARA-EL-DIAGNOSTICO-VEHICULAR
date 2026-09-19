"""Servicio orquestador del Webhook de WhatsApp con PostgreSQL.

Coordina:
1. Deduplicación por meta_message_id (idempotencia).
2. Resolución y auto-registro de identidades (IdentityResolver).
3. Apertura o recuperación de conversación (ventana de 24h).
4. Persistencia del mensaje entrante y registro de auditoría de costos.
5. Enrutamiento por rol (Cliente vs Mecánico).
6. Flujo de validación técnica SÍ / NO por mecánicos (ValidationWorkflow).
7. Transcripción de audio y ejecución de diagnóstico ML + RAG + Gemini.
8. Persistencia de diagnósticos, hipótesis y outbox (DiagnosticPersister).
"""

from __future__ import annotations

import asyncio
import threading
import time
import uuid
from decimal import Decimal
from typing import Any, Optional

import requests
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.confirmacion_diagnostico import ConfirmacionDiagnosticoWhatsApp
from src.config import settings
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.logger import logger
from src.core.security import anonimizar_identificador
from src.core.services.webhook import (
    ClientWorkflow,
    DiagnosticPersister,
    IdentityResolver,
    OfflineProcessor,
    TechnicalDiagnosticWorkflow,
    ValidationWorkflow,
)
from src.core.services.whatsapp_provider import whatsapp_provider_service
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.conversacion_repository import ConversacionRepository
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.mensaje_repository import MensajeRepository
from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository

# Costos operativos estándar
COSTO_META_MENSAJE_SERVICIO_USD = Decimal(str(settings.meta_message_price_usd))

_LOCKS_CONVERSACION: dict[str, asyncio.Lock] = {}
_GLOBAL_LOCKS_LOCK = threading.Lock()


def _obtener_lock_conversacion(remitente: str) -> asyncio.Lock:
    """Devuelve un lock asíncrono serializado por remitente/conversación para evitar condiciones de carrera."""
    with _GLOBAL_LOCKS_LOCK:
        if remitente not in _LOCKS_CONVERSACION:
            _LOCKS_CONVERSACION[remitente] = asyncio.Lock()
        return _LOCKS_CONVERSACION[remitente]


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

    @staticmethod
    async def _procesar_confirmacion_tecnica(
        confirmacion: ConfirmacionDiagnosticoWhatsApp,
        usuario: Any,
        diag_repo: DiagnosticoRepository,
        operaciones_repo: OperacionesRepository,
        diagnostico_id: uuid.UUID | None = None,
    ) -> tuple[str, uuid.UUID | None]:
        """Delegación para compatibilidad de pruebas."""
        return await ValidationWorkflow.procesar_confirmacion_tecnica(
            confirmacion=confirmacion,
            usuario=usuario,
            diag_repo=diag_repo,
            operaciones_repo=operaciones_repo,
            diagnostico_id=diagnostico_id,
        )

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
        """Ejecuta el ciclo de vida completo del webhook con PostgreSQL y soporte multi-rol."""
        inicio = time.perf_counter()
        rem_anon = anonimizar_identificador(remitente)
        proveedor = "meta" if proveedor.lower() in ("meta", "whatsapp") else proveedor.lower()
        if proveedor not in {"meta", "twilio", "api"}:
            raise ValueError(f"Proveedor de webhook no soportado: {proveedor}")

        lock = _obtener_lock_conversacion(remitente)
        async with lock:
            # Si PostgreSQL no está habilitado, procesar en modo desacoplado / offline
            if not database_configurada():
                logger.info(f"[Webhook Modo Sin BD] Procesando para usuario {rem_anon}")
                return await OfflineProcessor.procesar_sin_base_datos(
                    gestor=self.gestor,
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
                    msg_repo = MensajeRepository(session)
                    conv_repo = ConversacionRepository(session)
                    operaciones_repo = OperacionesRepository(session)

                    # 1. Deduplicación de mensajes (idempotencia)
                    if meta_message_id and await msg_repo.existe_meta_message_id(meta_message_id):
                        logger.info(
                            f"[Webhook Deduplicación] Mensaje {meta_message_id} ya procesado. Descartando duplicado."
                        )
                        return {
                            "status": "duplicado_ignorado",
                            "meta_message_id": meta_message_id,
                            "tiempo_ms": round((time.perf_counter() - inicio) * 1000, 2),
                        }

                    # 2. Identificación / auto-registro del contacto
                    res_id = await IdentityResolver.resolver_o_registrar(
                        session=session,
                        remitente=remitente,
                        proveedor=proveedor,
                        tipo_identificador=tipo_identificador,
                        telefono_id_meta=telefono_id_meta,
                        nombre_contacto=nombre_contacto,
                    )
                    if res_id.status != "ok":
                        if res_id.mensaje_error:
                            await whatsapp_provider_service.enviar(proveedor, remitente, res_id.mensaje_error)
                        return {
                            "status": res_id.status,
                            "remitente": rem_anon,
                            "tiempo_ms": round((time.perf_counter() - inicio) * 1000, 2),
                        }
                    usuario = res_id.usuario

                    # 3. Recuperar o crear conversación activa (ventana 24 horas)
                    conversacion = await conv_repo.obtener_o_crear_activa(
                        taller_id=usuario.taller_id,
                        usuario_id=usuario.id,
                        canal="whatsapp" if proveedor in {"meta", "twilio"} else "api",
                        ventana_horas=24,
                    )

                    # 4. Persistir mensaje entrante
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
                        logger.info(f"[Webhook Deduplicación] Carrera concurrente resuelta para {meta_message_id}.")
                        return {
                            "status": "duplicado_ignorado",
                            "meta_message_id": meta_message_id,
                            "tiempo_ms": round((time.perf_counter() - inicio) * 1000, 2),
                        }

                    # Registrar costo operativo del mensaje entrante
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

                    # 5. Enrutamiento por rol: Cliente vs Personal Técnico
                    codigo_rol = usuario.rol.codigo if usuario.rol else "cliente"
                    roles_tecnicos = {"mecanico", "jefe_taller", "supervisor", "administrador", "admin"}

                    if codigo_rol not in roles_tecnicos:
                        resultado_cliente = await ClientWorkflow.procesar_y_persistir(
                            session, usuario, conversacion, texto_cliente, meta_message_id, proveedor, remitente
                        )
                        total_ms = (time.perf_counter() - inicio) * 1000
                        logger.info(
                            f"[Webhook Cliente] Respuesta enviada a cliente {usuario.nombres} ({rem_anon}) en {total_ms:.2f}ms"
                        )
                        resultado_cliente["tiempo_total_ms"] = round(total_ms, 2)
                        return resultado_cliente

                    # 6. Flujo de validación técnica conversacional (SÍ / NO / Falla real)
                    resultado_validacion = await ValidationWorkflow.manejar_flujo_validacion(
                        session=session,
                        conversacion=conversacion,
                        usuario=usuario,
                        texto_cliente=texto_cliente,
                        tipo_mensaje=tipo_mensaje,
                        meta_message_id=meta_message_id,
                        proveedor=proveedor,
                        remitente=remitente,
                        t_inicio=inicio,
                    )
                    diagnostico_forzado_alternativa = None
                    if resultado_validacion is not None:
                        if resultado_validacion.get("status") == "evaluar_alternativa":
                            texto_cliente = resultado_validacion["texto_evaluar"]
                            diagnostico_forzado_alternativa = resultado_validacion.get("diagnostico_forzado")
                        else:
                            if resultado_validacion.get("status") == "validacion_tecnica":
                                self.gestor.session_manager.finalizar_caso(str(conversacion.id))
                            return resultado_validacion

                    # 7. Diagnóstico Técnico ML + RAG + Gemini
                    flujo_diagnostico = await TechnicalDiagnosticWorkflow.preparar(
                        self.gestor, conversacion, usuario, remitente, proveedor, tipo_mensaje,
                        texto_cliente, audio_id, placa, marca_modelo,
                        diagnostico_forzado=diagnostico_forzado_alternativa,
                    )
                    dto = flujo_diagnostico.dto
                    texto_cliente = flujo_diagnostico.texto_cliente
                    duracion_ms = flujo_diagnostico.duracion_ms

                    # 8. Persistencia del diagnóstico, hipótesis, costos y encolado en outbox
                    resultado_diag, costo_gemini = await DiagnosticPersister.persistir_y_responder(
                        session=session,
                        dto=dto,
                        usuario=usuario,
                        conversacion=conversacion,
                        texto_cliente=texto_cliente,
                        meta_message_id=meta_message_id,
                        remitente=remitente,
                        proveedor=proveedor,
                        placa=placa,
                        marca_modelo=marca_modelo,
                        duracion_ms=duracion_ms,
                        corpus_version=getattr(self.gestor.motor_rag, "corpus_version", "desconocido"),
                    )

                    total_ms = (time.perf_counter() - inicio) * 1000
                    resultado_diag["tiempo_total_ms"] = round(total_ms, 2)
                    if "costo_estimado_usd" not in resultado_diag and dto.tipo_consulta == "diagnostico":
                        resultado_diag["costo_estimado_usd"] = float(costo_gemini)

                    logger.info(
                        f"[Webhook Procesado] Respuesta lista para mecánico {usuario.nombres} en {total_ms:.2f}ms"
                    )
                    return resultado_diag

                except Exception as exc:
                    await session.rollback()
                    logger.error(f"[Webhook Error] Fallo al procesar y persistir: {exc}")
                    raise
