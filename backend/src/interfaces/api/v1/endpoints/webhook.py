import time
from urllib.parse import parse_qs

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services import GestorDiagnostico
from src.application.services.whatsapp import WebhookService
from src.config import settings
from src.core.logger import logger
from src.core.security import anonimizar_identificador, verificar_firma_meta, verificar_firma_twilio
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.trabajo_sistema_repository import TrabajoSistemaRepository

router = APIRouter()


def obtener_gestor_diagnostico(request: Request) -> GestorDiagnostico:
    if hasattr(request.app.state, "gestor_diagnostico"):
        return request.app.state.gestor_diagnostico
    return GestorDiagnostico()


def obtener_webhook_service(request: Request) -> WebhookService:
    gestor = obtener_gestor_diagnostico(request)
    return WebhookService(gestor)


async def _encolar_mensaje_whatsapp(payload: dict, proveedor: str, mensaje_id: str) -> tuple[str, bool]:
    """Persiste el mensaje antes de confirmar su recepción al proveedor."""
    try:
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            async with session.begin():
                taller = await TallerRepository(session).obtener_taller_para_webhook(
                    payload.get("telefono_id_meta")
                )
                if taller is None:
                    raise HTTPException(status_code=503, detail="No existe un taller activo para este canal.")
                trabajo, creado = await TrabajoSistemaRepository(session).crear_trabajo(
                    tipo="webhook_mensaje",
                    cola="audio" if payload.get("tipo_mensaje") == "audio" else "diagnosticos",
                    payload=payload,
                    prioridad=80 if payload.get("tipo_mensaje") == "text" else 60,
                    clave_idempotencia=f"{proveedor}:{mensaje_id}",
                    taller_id=taller.id,
                )
                return str(trabajo.id), creado
    except OverflowError as exc:
        raise HTTPException(status_code=503, detail=str(exc), headers={"Retry-After": "30"}) from exc


async def _procesar_y_responder_whatsapp(
    gestor: GestorDiagnostico,
    remitente: str,
    tipo_mensaje: str,
    texto_cliente: str = "",
    audio_id: str = "",
    placa: str = "WAPP-01",
    marca_modelo: str = "Vehiculo Generico",
    session_id: str = None,
    meta_message_id: str = None,
    proveedor: str = "whatsapp",
    tipo_identificador: str = "telefono",
    telefono_id_meta: str = None,
    nombre_contacto: str = None,
):
    """Procesa en segundo plano la consulta mediante WebhookService y responde vía WhatsApp."""
    start_t = time.time()
    try:
        service = WebhookService(gestor)
        resultado = await service.procesar_mensaje(
            remitente=remitente,
            meta_message_id=meta_message_id or f"msg_{time.time_ns()}",
            tipo_mensaje=tipo_mensaje,
            texto_cliente=texto_cliente,
            audio_id=audio_id,
            placa=placa,
            marca_modelo=marca_modelo,
            proveedor=proveedor,
            session_id=session_id,
            tipo_identificador=tipo_identificador,
            telefono_id_meta=telefono_id_meta,
            nombre_contacto=nombre_contacto,
        )
        elapsed = (time.time() - start_t) * 1000
        rem_anon = anonimizar_identificador(remitente)
        logger.info(f"[Background Task Webhook] Procesado con éxito en {elapsed:.2f} ms para usuario {rem_anon}")
        return resultado
    except Exception as e:
        logger.error(f"[Background Task Webhook] Error en segundo plano: {e}")
        raise


# ==========================================
# ENDPOINTS META WHATSAPP CLOUD API
# ==========================================

@router.get("/meta", summary="Verificación Webhook Meta Cloud API")
@router.get("", summary="Verificación Webhook Meta (Compatibilidad)")
def verificar_webhook_meta(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge"),
):
    """Verificación obligatoria del Webhook requerida por Meta Cloud API."""
    expected_token = settings.meta_verify_token
    if mode == "subscribe" and bool(expected_token) and token == expected_token:
        logger.info("Webhook de WhatsApp verificado con éxito por Meta.")
        return PlainTextResponse(content=challenge or "")
    logger.warning("Intento de verificación de Webhook fallido por token incorrecto.")
    raise HTTPException(status_code=403, detail="Token de verificación inválido (Verify token incorrecto).")


@router.post("/meta", summary="Recepción de Mensajes Meta Cloud API")
async def recibir_mensaje_meta(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
):
    """
    Webhook dedicado para Meta Cloud API (WhatsApp).
    Requiere obligatoriamente firma criptográfica X-Hub-Signature-256 válida. Falla cerrado si el secret falta o no coincide.
    """
    t_inicio = time.time()
    raw_body = await request.body()
    if len(raw_body) > settings.webhook_max_body_bytes:
        raise HTTPException(status_code=413, detail="Payload de webhook demasiado grande.")

    if not x_hub_signature_256 or not verificar_firma_meta(raw_body, x_hub_signature_256):
        logger.warning("[Webhook Meta] Firma criptográfica X-Hub-Signature-256 inválida o ausente.")
        raise HTTPException(status_code=401, detail="Firma de webhook inválida (Unauthorized Meta Payload).")

    try:
        payload = await request.json()
        remitente = "desconocido"
        tipo_identificador = "telefono"
        nombre_contacto = None
        tipo_mensaje = "text"
        texto_cliente = ""
        audio_id = ""
        meta_message_id = f"meta_{time.time_ns()}"
        telefono_id_meta = None

        if "entry" in payload:
            entry = payload.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])

            metadata = value.get("metadata", {})
            telefono_id_meta = metadata.get("phone_number_id")

            # Meta también envía estados (enviado/entregado/leído). No son
            # consultas y no deben generar diagnósticos ficticios.
            if not messages:
                statuses = value.get("statuses", [])
                if statuses:
                    estado = statuses[0]
                    await obtener_webhook_service(request).actualizar_estado_entrega_externo(
                        estado.get("id", ""), estado.get("status", "")
                    )
                return JSONResponse(
                    status_code=200,
                    content={"status": "evento_ignorado", "proveedor": "Meta Cloud API"},
                )

            msg = messages[0]
            meta_message_id = msg.get("id", meta_message_id)

            # Prioridad de identificación: messages.from -> contacts.wa_id -> contacts.user_id
            msg_from = msg.get("from")
            msg_from_user_id = msg.get("from_user_id")
            contact_wa_id = contacts[0].get("wa_id") if contacts else None
            contact_user_id = contacts[0].get("user_id") if contacts else None

            if contacts and contacts[0].get("profile"):
                nombre_contacto = contacts[0].get("profile", {}).get("name")

            if msg_from and str(msg_from).strip():
                remitente = str(msg_from).strip()
                tipo_identificador = "telefono"
            elif contact_wa_id and str(contact_wa_id).strip():
                remitente = str(contact_wa_id).strip()
                tipo_identificador = "wa_id"
            elif msg_from_user_id and str(msg_from_user_id).strip():
                remitente = str(msg_from_user_id).strip()
                tipo_identificador = "user_id"
            elif contact_user_id and str(contact_user_id).strip():
                remitente = str(contact_user_id).strip()
                tipo_identificador = "user_id"
            else:
                remitente = f"user_{meta_message_id}"
                tipo_identificador = "user_id"

            tipo_mensaje = msg.get("type", "text")
            if tipo_mensaje == "text":
                texto_cliente = msg.get("text", {}).get("body", "")
                if len(texto_cliente) > settings.user_text_max_chars:
                    raise HTTPException(status_code=413, detail="Mensaje de texto demasiado largo.")
            elif tipo_mensaje == "audio":
                audio_id = msg.get("audio", {}).get("id", "")
            else:
                logger.info(f"[Webhook Meta] Tipo de mensaje no soportado: {tipo_mensaje}")
                return JSONResponse(
                    status_code=200,
                    content={"status": "tipo_no_soportado", "tipo": tipo_mensaje},
                )
        else:
            raise HTTPException(status_code=400, detail="Formato de payload Meta inválido.")

        rem_anon = anonimizar_identificador(remitente)
        logger.info(f"[Webhook Meta API] Mensaje válido de usuario {rem_anon} (Tipo: {tipo_mensaje}, MsgID: {meta_message_id})")

        datos_trabajo = {
            "remitente": remitente,
            "tipo_mensaje": tipo_mensaje,
            "texto_cliente": texto_cliente,
            "audio_id": audio_id,
            "placa": "WAPP-01",
            "marca_modelo": "Vehiculo Generico",
            "session_id": remitente,
            "meta_message_id": meta_message_id,
            "proveedor": "meta",
            "tipo_identificador": tipo_identificador,
            "telefono_id_meta": telefono_id_meta,
            "nombre_contacto": nombre_contacto,
        }
        if database_configurada():
            trabajo_id, creado = await _encolar_mensaje_whatsapp(datos_trabajo, "meta", meta_message_id)
        else:
            background_tasks.add_task(
                _procesar_y_responder_whatsapp,
                obtener_gestor_diagnostico(request),
                **datos_trabajo,
            )
            trabajo_id, creado = "background-local", True
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Webhook Meta] Error al procesar payload: {e}")
        raise HTTPException(status_code=400, detail="Formato de payload Meta inválido.")

    elapsed_ms = (time.time() - t_inicio) * 1000
    return JSONResponse(
        status_code=200,
        content={
            "status": "procesado",
            "estado_interno": "encolado" if creado else "duplicado",
            "trabajo_id": trabajo_id,
            "proveedor": "Meta Cloud API",
            "tiempo_respuesta_ms": round(elapsed_ms, 2),
        },
    )


# ==========================================
# ENDPOINT TWILIO WHATSAPP
# ==========================================

@router.post("/twilio", summary="Recepción de Mensajes Twilio Form")
async def recibir_mensaje_twilio(
    request: Request,
    background_tasks: BackgroundTasks,
    x_twilio_signature: str = Header(None, alias="X-Twilio-Signature"),
):
    """
    Webhook dedicado para Twilio (Form-urlencoded).
    Valida la firma criptográfica X-Twilio-Signature. Falla cerrado si el token o la firma no coinciden.
    """
    t_inicio = time.time()
    raw_body = await request.body()
    if len(raw_body) > settings.webhook_max_body_bytes:
        raise HTTPException(status_code=413, detail="Payload de webhook demasiado grande.")
    body_str = raw_body.decode("utf-8", errors="ignore")
    parsed_qs = parse_qs(body_str)

    # Convertir dict de listas de parse_qs a valores simples
    params_dict = {k: v[0] for k, v in parsed_qs.items() if v}

    url_solicitud = str(request.url)
    if not x_twilio_signature or not verificar_firma_twilio(url_solicitud, params_dict, x_twilio_signature):
        logger.warning("[Webhook Twilio] Firma criptográfica X-Twilio-Signature inválida o ausente.")
        raise HTTPException(status_code=401, detail="Firma de webhook inválida (Unauthorized Twilio Payload).")

    if params_dict.get("MessageStatus") and not params_dict.get("Body") and not params_dict.get("MediaUrl0"):
        await obtener_webhook_service(request).actualizar_estado_entrega_externo(
            params_dict.get("MessageSid", ""), params_dict.get("MessageStatus", "")
        )
        return JSONResponse(status_code=200, content={"status": "estado_actualizado", "proveedor": "Twilio"})

    remitente = params_dict.get("From", "whatsapp:+51000000000")
    texto_cliente = params_dict.get("Body", "")
    if len(texto_cliente) > settings.user_text_max_chars:
        raise HTTPException(status_code=413, detail="Mensaje de texto demasiado largo.")
    media_url = params_dict.get("MediaUrl0", "")
    tipo_mensaje = "audio" if media_url else "text"
    audio_id = media_url if media_url else ""
    twilio_message_sid = params_dict.get("MessageSid", f"twilio_{time.time_ns()}")

    rem_anon = anonimizar_identificador(remitente)
    logger.info(f"[Webhook Twilio] Mensaje verificado recibido de {rem_anon}")

    datos_trabajo = {
        "remitente": remitente,
        "tipo_mensaje": tipo_mensaje,
        "texto_cliente": texto_cliente,
        "audio_id": audio_id,
        "placa": "WAPP-01",
        "marca_modelo": "Vehiculo Generico",
        "session_id": remitente,
        "meta_message_id": twilio_message_sid,
        "proveedor": "twilio",
    }
    if database_configurada():
        trabajo_id, creado = await _encolar_mensaje_whatsapp(datos_trabajo, "twilio", twilio_message_sid)
    else:
        background_tasks.add_task(
            _procesar_y_responder_whatsapp,
            obtener_gestor_diagnostico(request),
            **datos_trabajo,
        )
        trabajo_id, creado = "background-local", True

    elapsed_ms = (time.time() - t_inicio) * 1000
    return JSONResponse(
        status_code=200,
        content={
            "status": "procesado",
            "estado_interno": "encolado" if creado else "duplicado",
            "trabajo_id": trabajo_id,
            "proveedor": "Twilio",
            "tiempo_respuesta_ms": round(elapsed_ms, 2),
        },
    )


# ==========================================
# ENDPOINT RAÍZ COMPATIBILIDAD
# ==========================================

@router.post("", summary="Recepción Webhook Raíz (Enrutamiento Criptográfico)")
async def recibir_mensaje(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    x_twilio_signature: str = Header(None, alias="X-Twilio-Signature"),
):
    """
    Punto de entrada general con enrutamiento automático hacia /meta o /twilio según firmas e inspección del payload.
    Exige firma criptográfica válida de alguno de los proveedores.
    """
    content_type = request.headers.get("content-type", "").lower()

    if "application/x-www-form-urlencoded" in content_type or x_twilio_signature:
        return await recibir_mensaje_twilio(request, background_tasks, x_twilio_signature)

    return await recibir_mensaje_meta(request, background_tasks, x_hub_signature_256)


def enviar_mensaje_whatsapp(numero_destino: str, texto: str):
    """Realiza la llamada HTTP POST a la Graph API de Meta para enviar la respuesta."""
    return WebhookService().enviar_mensaje_whatsapp(numero_destino, texto)
