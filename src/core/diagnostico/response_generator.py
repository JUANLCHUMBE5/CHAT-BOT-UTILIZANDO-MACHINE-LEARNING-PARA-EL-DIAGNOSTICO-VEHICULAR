"""Generación de respuestas con metadatos usando Gemini LLM o fallback degradado."""

from __future__ import annotations

import uuid
from typing import Any, Optional, Tuple

from src.config import settings
from src.core.diagnostico.degraded_fallback import generar_respuesta_degradada
from src.core.diagnostico.prompt_builder import (
    construir_prompt_consulta_tecnica,
    construir_prompt_diagnostico,
)
from src.core.gemini_queue import SolicitudGeminiEncolada, gemini_rate_limiter
from src.core.logger import logger
from src.core.sanitizer import redactar_datos_sensibles_para_llm, sanitizar_prompt_usuario


def generar_respuesta_con_metadatos(
    gestor: Any,
    pregunta: str,
    diagnostico_ml: str,
    contexto_manual: str,
    confianza_ml: float = 0.85,
    titulo_manual: str = "",
    requiere_revision_humana: bool = False,
    remitente: Optional[str] = None,
    proveedor: str = "meta",
    taller_id: Optional[str] = None,
    usuario_id: Optional[str] = None,
    conversacion_id: Optional[str] = None,
    slot_gemini_preconcedido: Optional[bool] = None,
    diferir_encolado_persistente: bool = False,
    tipo_consulta: str = "diagnostico",
    predicciones_ml: Optional[list[Any]] = None,
    dtc_info: Optional[str] = None,
    perfil_vehiculo: Optional[str] = None,
    evidencia_confirmada: Optional[list[str]] = None,
    componentes_descartados: Optional[list[str]] = None,
    datos_faltantes: Optional[list[str]] = None,
) -> Tuple[str, dict]:
    """Sintetiza la respuesta final con Gemini LLM integrando Síntoma + ML + RAG."""
    confianza_pct = int(confianza_ml * 100)
    pregunta_llm = redactar_datos_sensibles_para_llm(
        sanitizar_prompt_usuario(pregunta, max_length=settings.user_text_max_chars)
    )
    contexto_llm = (contexto_manual or "")[: settings.rag_context_max_chars]
    alerta_revision = (
        "\n⚠️ *Nota:* Se requiere inspección física obligatoria: la confianza ML "
        "es insuficiente o el procedimiento RAG aún no tiene fuente OEM validada.\n"
        if requiere_revision_humana
        else ""
    )

    if tipo_consulta == "consulta_tecnica":
        prompt_sistema = construir_prompt_consulta_tecnica(
            pregunta_llm=pregunta_llm,
            titulo_manual=titulo_manual,
            contexto_llm=contexto_llm,
        )
    else:
        prompt_sistema = construir_prompt_diagnostico(
            pregunta_llm=pregunta_llm,
            diagnostico_ml=diagnostico_ml,
            confianza_pct=confianza_pct,
            titulo_manual=titulo_manual,
            contexto_llm=contexto_llm,
            alerta_revision=alerta_revision,
            predicciones_ml=predicciones_ml,
            dtc_info=dtc_info,
            perfil_vehiculo=perfil_vehiculo,
            evidencia_confirmada=evidencia_confirmada,
            componentes_descartados=componentes_descartados,
            datos_faltantes=datos_faltantes,
        )

    if gestor.api_key:
        slot_disponible = (
            gemini_rate_limiter.intentar_adquirir_slot()
            if slot_gemini_preconcedido is None
            else slot_gemini_preconcedido
        )
        if slot_disponible:
            try:
                modelo = settings.gemini_model
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": gestor.api_key,
                }
                payload = {
                    "contents": [{"parts": [{"text": prompt_sistema}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 140 if tipo_consulta == "consulta_tecnica" else 1200,
                    },
                }
                response = gestor._http_session.post(url, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    gemini_rate_limiter.registrar_estado_gemini(exitoso=True, codigo_http=200)
                    data = response.json()
                    metadata = data.get("usageMetadata", {})
                    texto_gemini = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    texto_gemini = texto_gemini[: settings.gemini_output_max_chars]
                    if not texto_gemini:
                        raise ValueError("Gemini devolvió una respuesta vacía.")
                    return texto_gemini, {
                        "usado": True,
                        "modelo": modelo,
                        "modo": "consulta_tecnica" if tipo_consulta == "consulta_tecnica" else "completo_ml_rag_llm",
                        "tokens_entrada": int(metadata.get("promptTokenCount", max(1, len(prompt_sistema) // 4))),
                        "tokens_salida": int(metadata.get("candidatesTokenCount", max(1, len(texto_gemini) // 4))),
                    }
                gemini_rate_limiter.registrar_estado_gemini(
                    exitoso=False,
                    codigo_http=response.status_code,
                    error=f"Gemini HTTP {response.status_code}",
                    retry_after_segundos=(
                        gemini_rate_limiter.extraer_retry_after_segundos(response)
                        if response.status_code == 429
                        else 0
                    ),
                )
                logger.warning(f"[Gemini API] Código HTTP {response.status_code}; activando fallback degradado.")
            except Exception as e:
                gemini_rate_limiter.registrar_estado_gemini(
                    exitoso=False,
                    error=f"{type(e).__name__}: {e}",
                )
                logger.error(f"[Gemini API Error] Fallo al consultar Gemini: {e}. Activando fallback degradado.")
        else:
            proveedor_normalizado = "meta" if proveedor.lower() in ("meta", "whatsapp") else proveedor.lower()
            predicciones_dicts = [
                p.model_dump() if hasattr(p, "model_dump") else (p if isinstance(p, dict) else {"falla": str(p)})
                for p in (predicciones_ml or [])
            ]
            if diferir_encolado_persistente:
                solicitud = SolicitudGeminiEncolada(
                    id=str(uuid.uuid4()),
                    sintoma=pregunta,
                    diagnostico_ml=diagnostico_ml,
                    confianza_ml=confianza_ml,
                    contexto_manual=contexto_manual,
                    titulo_manual=titulo_manual,
                    requiere_revision_humana=requiere_revision_humana,
                    remitente=remitente,
                    proveedor=proveedor_normalizado,
                    taller_id=taller_id,
                    usuario_id=usuario_id,
                    conversacion_id=conversacion_id,
                    tipo_consulta=tipo_consulta,
                    predicciones_ml=predicciones_dicts,
                )
                posicion = gemini_rate_limiter.tamaño_cola() + 1
                espera_segundos = gemini_rate_limiter.tiempo_espera_estimado()
            else:
                solicitud, posicion, espera_segundos = gemini_rate_limiter.encolar_solicitud(
                    sintoma=pregunta,
                    diagnostico_ml=diagnostico_ml,
                    confianza_ml=confianza_ml,
                    contexto_manual=contexto_manual,
                    titulo_manual=titulo_manual,
                    requiere_revision_humana=requiere_revision_humana,
                    remitente=remitente,
                    proveedor=proveedor_normalizado,
                    taller_id=taller_id,
                    usuario_id=usuario_id,
                    conversacion_id=conversacion_id,
                    tipo_consulta=tipo_consulta,
                    predicciones_ml=predicciones_dicts,
                )
            logger.info(
                f"[Gemini Queue] Solicitud {solicitud.id[:8]} colocada en cola de espera (Posición: {posicion}, Espera: ~{espera_segundos}s, Proveedor: {proveedor})."
            )
            es_prioridad_gas = diagnostico_ml.startswith("Sistema GNV/GLP")
            if es_prioridad_gas:
                mensaje_cola = (
                    f"⏳ *Analizando consulta (cola #{posicion})*\n"
                    "Como la falla ocurre solo en GNV/GLP, revisaré primero una posible "
                    "descalibración y la alimentación de gas bajo carga.\n"
                    f"Es una hipótesis por confirmar; la confianza ML es {confianza_pct}%."
                )
            elif confianza_pct < int(settings.diagnostic.confidence_threshold * 100):
                mensaje_cola = (
                    f"⏳ *Analizando consulta (cola #{posicion})*\n"
                    f"Hipótesis preliminar ML: *{diagnostico_ml}* ({confianza_pct}%).\n"
                    "Al ser confianza media (<70%), se contrastará con manuales y pruebas de taller.\n"
                    "En breve recibirás el resumen; el detalle quedará en el panel."
                )
            else:
                mensaje_cola = (
                    f"⏳ *Analizando consulta (cola #{posicion})*\n"
                    f"Hipótesis preliminar ML: *{diagnostico_ml}* ({confianza_pct}%).\n"
                    "En breve recibirás el resumen; el detalle quedará en el panel."
                )
            if tipo_consulta == "consulta_tecnica":
                mensaje_cola = f"⏳ Analizando (cola #{posicion}). Te respondo en breve."
            return mensaje_cola, {
                "usado": False,
                "modelo": None,
                "modo": "consulta_tecnica_en_cola" if tipo_consulta == "consulta_tecnica" else "en_cola_gemini",
                "solicitud_id": solicitud.id,
                "tokens_entrada": 0,
                "tokens_salida": 0,
                "posicion_cola": posicion,
                "tiempo_espera_cola": espera_segundos,
            }

    # Fallback local determinista cuando no hay LLM o ante fallo de conexión
    return generar_respuesta_degradada(
        tipo_consulta=tipo_consulta,
        contexto_manual=contexto_manual,
        titulo_manual=titulo_manual,
        diagnostico_ml=diagnostico_ml,
        confianza_pct=confianza_pct,
        alerta_revision=alerta_revision,
    )
