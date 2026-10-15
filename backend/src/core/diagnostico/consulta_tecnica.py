"""Módulo de procesamiento y orquestación de consultas técnicas informativas."""

from __future__ import annotations

import time
from typing import Any, Optional

from src.core.diagnostico.models import ResultadoDiagnostico
from src.core.vehicle_profile import extraer_datos_vehiculo
from src.core.whatsapp_response import formatear_consulta_tecnica_whatsapp


def procesar_consulta_tecnica(
    gestor: Any,
    pregunta: str,
    *,
    inicio_total: float,
    remitente: Optional[str],
    proveedor: str,
    taller_id: Optional[str],
    usuario_id: Optional[str],
    conversacion_id: Optional[str],
    slot_gemini_preconcedido: Optional[bool],
    diferir_encolado_persistente: bool,
) -> ResultadoDiagnostico:
    """Responde información automotriz sin forzar una clase de avería ML."""
    inicio_rag = time.perf_counter()
    if hasattr(gestor.motor_rag, "recuperar_contexto_con_similitud"):
        contexto, titulo, similitud = gestor.motor_rag.recuperar_contexto_con_similitud(pregunta)
    else:
        contexto, titulo = gestor.motor_rag.recuperar_contexto(pregunta)
        similitud = 0.0
    tiempo_rag_ms = max(0, int((time.perf_counter() - inicio_rag) * 1000))

    inicio_llm = time.perf_counter()
    respuesta, uso_llm = gestor._generar_respuesta_con_metadatos(
        pregunta=pregunta,
        diagnostico_ml="Consulta técnica informativa",
        confianza_ml=0.0,
        contexto_manual=contexto,
        titulo_manual=titulo,
        requiere_revision_humana=False,
        remitente=remitente,
        proveedor=proveedor,
        taller_id=taller_id,
        usuario_id=usuario_id,
        conversacion_id=conversacion_id,
        slot_gemini_preconcedido=slot_gemini_preconcedido,
        diferir_encolado_persistente=diferir_encolado_persistente,
        tipo_consulta="consulta_tecnica",
    )
    tiempo_llm_ms = max(0, int((time.perf_counter() - inicio_llm) * 1000))
    modo = uso_llm.get(
        "modo",
        "consulta_tecnica" if uso_llm.get("usado") else "consulta_tecnica_degradada",
    )
    if proveedor.lower() in {"meta", "twilio", "whatsapp"} and modo != "consulta_tecnica_en_cola":
        respuesta = formatear_consulta_tecnica_whatsapp(
            respuesta,
            modelo_informado=bool(extraer_datos_vehiculo(pregunta).get("modelo")),
        )
    return ResultadoDiagnostico(
        respuesta_texto=respuesta,
        diagnostico_ml="Consulta técnica informativa",
        confianza_ml=0.0,
        contexto_manual=contexto,
        titulo_manual=titulo,
        similitud_rag=similitud,
        requiere_revision_humana=False,
        modo_diagnostico=modo,
        solicitud_id=uso_llm.get("solicitud_id"),
        llm_usado=uso_llm.get("usado", False),
        llm_modelo=uso_llm.get("modelo"),
        tokens_entrada=uso_llm.get("tokens_entrada", 0),
        tokens_salida=uso_llm.get("tokens_salida", 0),
        posicion_cola=uso_llm.get("posicion_cola", 0),
        tiempo_espera_cola=uso_llm.get("tiempo_espera_cola", 0.0),
        sintoma_evaluado=pregunta,
        tiempo_rag_ms=tiempo_rag_ms,
        tiempo_llm_ms=tiempo_llm_ms,
        tiempo_total_ms=max(0, int((time.perf_counter() - inicio_total) * 1000)),
        tipo_consulta="consulta_tecnica",
    )
