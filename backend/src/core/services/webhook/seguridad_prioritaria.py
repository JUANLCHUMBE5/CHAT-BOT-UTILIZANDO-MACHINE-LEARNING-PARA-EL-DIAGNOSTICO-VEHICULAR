"""Peligro físico antes de gates, consultas informativas y validación técnica."""

from datetime import datetime, timezone

from src.core.conversacion.models import ConversationState
from src.core.conversacion.session_persistence import guardar_contexto_sesion_redis
from src.core.diagnostico.politica_seguridad import PoliticaSeguridad, SeveridadSeguridad
from src.core.security import cifrar_texto_reversible
from src.core.services.webhook.diagnostic_workflow import TechnicalDiagnosticWorkflow
from src.infrastructure.database.repositories.mensaje_repository import MensajeRepository


async def responder_peligro_activo(
    gestor, session, usuario, conversacion, texto, meta_message_id, remitente, proveedor, placa, marca_modelo
):
    contexto = dict(conversacion.contexto or {})
    raw = contexto.get("conversation_state") or contexto.get("estado_conversacion")
    estado = ConversationState.from_dict(raw) if isinstance(raw, dict) else None
    severidad, _ = PoliticaSeguridad.evaluar_severidad(texto, "", estado=estado)
    if severidad != SeveridadSeguridad.CRITICAL_STOP:
        return None
    dto = await TechnicalDiagnosticWorkflow._procesar_texto(
        gestor, texto, placa, marca_modelo, str(conversacion.id), remitente, proveedor, usuario, conversacion
    )
    # La respuesta ha pasado por la misma política documental final del orquestador.
    contexto = dict(conversacion.contexto or {})
    case_id = contexto.get("case_id")
    await MensajeRepository(session).crear_mensaje(
        conversacion_id=conversacion.id,
        taller_id=usuario.taller_id,
        usuario_id=usuario.id,
        meta_message_id=f"out_{meta_message_id}",
        direccion="salida",
        tipo="texto",
        texto=dto.respuesta_texto,
        categoria_cobro="servicio",
        estado_entrega="pendiente",
        moneda="USD",
        proveedor=proveedor,
        destinatario_cifrado=cifrar_texto_reversible(remitente),
        disponible_entrega_en=datetime.now(timezone.utc),
        case_id=case_id,
    )
    await session.commit()
    await guardar_contexto_sesion_redis(str(conversacion.id), contexto)
    return {
        "status": "seguridad_critica",
        "decision": "SEGURIDAD_CRITICA",
        "respuesta_texto": dto.respuesta_texto,
        "case_id": case_id,
        "conversacion_id": str(conversacion.id),
    }
