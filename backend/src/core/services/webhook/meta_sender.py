"""Adaptador de envío Meta preservado detrás del servicio público."""
from src.config import settings
from src.core.logger import logger
from src.core.security import anonimizar_identificador


def enviar_mensaje_meta(numero_destino, texto, requests, interactivo=None):
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
    
    payload_interactivo = None
    if interactivo and isinstance(interactivo, dict) and interactivo.get("tipo") == "button":
        botones = []
        for b in interactivo.get("botones", [])[:3]:
            b_id = str(b.get("id") or "")[:256]
            b_title = str(b.get("title") or "")[:20]
            if b_id and b_title:
                botones.append({"type": "reply", "reply": {"id": b_id, "title": b_title}})
        if botones:
            payload_interactivo = {
                "messaging_product": "whatsapp",
                "to": numero_destino,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": (texto or "")[:1024]},
                    "action": {"buttons": botones},
                },
            }

    data_texto = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {"body": texto},
    }
    payload_final = payload_interactivo if payload_interactivo else data_texto

    try:
        res = requests.post(url, headers=headers, json=payload_final, timeout=8)
        if payload_interactivo and res.status_code == 400:
            res = requests.post(url, headers=headers, json=data_texto, timeout=8)
        rem_anon = anonimizar_identificador(numero_destino)
        logger.info(f"Respuesta enviada a {rem_anon}. Status HTTP: {res.status_code}")
        return res.status_code in (200, 201)
    except Exception as exc:
        logger.error(f"Error al enviar mensaje vía Meta Graph API: {exc}")
        return False
