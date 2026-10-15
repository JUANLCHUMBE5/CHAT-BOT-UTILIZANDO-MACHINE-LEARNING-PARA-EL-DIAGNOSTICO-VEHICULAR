"""Consulta informativa autorizada sin crear vehículo ni alterar el caso activo."""
import asyncio
import time

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.intent_classifier import clasificar_intencion_consulta
from src.core.services.webhook.diagnostic_persister import DiagnosticPersister


async def responder_consulta_informativa(
    gestor, session, usuario, conversacion, texto, meta_message_id, remitente, proveedor
):
    if ExtractorHechos.es_consulta_memoria(texto) or clasificar_intencion_consulta(texto) != "consulta_tecnica":
        return None
    inicio = time.perf_counter()
    dto = await asyncio.to_thread(
        gestor._procesar_consulta_tecnica,
        texto, inicio_total=inicio, remitente=remitente, proveedor=proveedor,
        taller_id=str(usuario.taller_id), usuario_id=str(usuario.id),
        conversacion_id=str(conversacion.id), slot_gemini_preconcedido=None,
        diferir_encolado_persistente=True,
    )
    resultado, _ = await DiagnosticPersister.persistir_y_responder(
        session=session, dto=dto, usuario=usuario, conversacion=conversacion,
        texto_cliente=texto, meta_message_id=meta_message_id, remitente=remitente,
        proveedor=proveedor, placa="", marca_modelo="",
        duracion_ms=int((time.perf_counter()-inicio)*1000),
        corpus_version=getattr(gestor.motor_rag, "corpus_version", "desconocido"),
    )
    return resultado
