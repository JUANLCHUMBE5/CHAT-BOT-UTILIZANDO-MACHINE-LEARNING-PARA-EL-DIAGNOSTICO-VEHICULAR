"""Motor de comprensión semántica de mensajes del mecánico con LLM y fallback determinista."""

from __future__ import annotations

import json
import re
import time
from typing import Any

import requests

from src.config import settings
from src.core.conversacion.comprension_semantica.contratos import (
    EstadoHechoSemantico,
    HechoSemantico,
    InterpretacionSemantica,
    TipoHechoSemantico,
)
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.logger import logger
from src.core.parser.message_parser import SinglePassMessageParser
from src.core.sanitizer import redactar_datos_sensibles_para_llm, sanitizar_prompt_usuario

PROMPT_COMPRENSION_SISTEMA = """Eres el analizador semántico de CarBot, sistema experto de diagnóstico automotriz para talleres.
Tu tarea es interpretar mensajes en lenguaje natural de mecánicos automotrices y devolver EXCLUSIVAMENTE un objeto JSON válido según el esquema solicitado.

REGLAS OBLIGATORIAS:
1. DISTINGUIR NO_REVISADO, DESCARTADO Y REEMPLAZADO:
   - "no he comprobado", "no he revisado", "todavía no mido", "sin probar" -> estado="NO_REVISADO", tipo="comprobacion". ¡JAMÁS marques esto como descartado ni reemplazado!
   - "cambié", "puse nuevo", "reemplacé ayer y sigue igual", "puse nuevas" -> estado="REEMPLAZADO", tipo="comprobacion". Indica que la pieza se cambió como antecedente, ¡NO la marques como DESCARTADO ni descartes el sistema!
   - "descarté", "medí y está en tolerancia", "prueba física superada", "descartamos esa causa" -> estado="DESCARTADO", tipo="comprobacion".
2. IDENTIFICAR PREGUNTAS TÉCNICAS:
   - Si el mecánico pregunta qué otras causas pueden ser, cómo diferenciar, o pide una prueba concreta -> extrae la pregunta textual en "pregunta_tecnica_usuario" y activa "solicitar_causas_alternativas" si corresponde.
3. DETECTAR INTENCIONES MÚLTIPLES:
   - Un mecánico puede en un solo mensaje: aportar síntomas, aclarar que algo no se revisó o se reemplazó, y preguntar causas alternativas. Registra todas las intenciones presentes.
4. DETECTAR CONDICIONES OPERATIVAS:
   - "en subida", "en frío", "en tráfico", "en autopista", "con tanque lleno/medio" -> tipo="condicion".
5. RECONOCER CONTINUAR vs NUEVO CASO:
   - "quiero continuar el mismo caso", "sigamos con este auto" -> solicita_continuar=true, solicita_nuevo_caso=false.
   - "nuevo caso", "neuvo caso", "otro auto", "cambiar vehículo" -> solicita_nuevo_caso=true.
6. NO INVENTAR DATOS:
   - Extrae solo lo que el mecánico escribió o infirió de forma directa. No inventes mediciones numéricas ni códigos DTC.

ESQUEMA JSON REQUERIDO:
{
  "intenciones": ["reportar_sintoma", "aclarar_comprobacion", "solicitar_alternativas", "continuar_caso"],
  "hechos_nuevos": [
    {
      "tipo": "sintoma" | "condicion" | "comprobacion" | "vehiculo" | "herramienta",
      "campo": "nombre_normalizado",
      "valor": "descripcion del hallazgo",
      "estado": "CONFIRMADO" | "NO_REVISADO" | "DESCARTADO" | "REEMPLAZADO" | "AUSENTE_NEGADO",
      "evidencia_texto": "cita textual del mensaje"
    }
  ],
  "pregunta_tecnica_usuario": "texto de la pregunta realizada o null",
  "solicita_causas_alternativas": true | false,
  "solicita_nuevo_caso": true | false,
  "solicita_continuar": true | false,
  "datos_vehiculo": {
    "marca": "Toyota" o null,
    "modelo": "Corolla" o null,
    "anio": "2015" o null,
    "placa": "ABC123" o null
  },
  "requiere_aclaracion": false,
  "explicacion_resumida": "breve sintesis"
}
Devuelve SOLO el JSON sin markdown, sin texto antes ni después."""


def _construir_contexto_resumido(contexto_estado: Any) -> str:
    """Prepara un resumen compacto del estado conversacional activo para guiar la interpretación."""
    if not contexto_estado:
        return "Sin caso activo previo."

    lineas = []
    if isinstance(contexto_estado, dict):
        marca = contexto_estado.get("marca")
        modelo = contexto_estado.get("modelo")
        placa = contexto_estado.get("placa")
        falla = contexto_estado.get("falla_principal")
        sintomas = contexto_estado.get("active_symptoms") or []
        pregunta = contexto_estado.get("pending_question")
    else:
        marca = getattr(contexto_estado, "marca", None)
        modelo = getattr(contexto_estado, "modelo", None)
        placa = getattr(contexto_estado, "placa", None)
        falla = getattr(contexto_estado, "falla_principal", None)
        sintomas = getattr(contexto_estado, "active_symptoms", []) or []
        pregunta = getattr(contexto_estado, "pending_question", None)

    placa_limpia = str(placa or '').strip().upper()
    placa_str = (
        f" (Placa: {placa})"
        if placa_limpia and placa_limpia not in ("SIN-PLACA", "WAPP-01", "REST-API", "DESCONOCIDO")
        else ""
    )
    vehiculo_str = f"{marca or ''} {modelo or ''}{placa_str}".strip()
    if vehiculo_str:
        lineas.append(f"- Vehículo activo: {vehiculo_str}")
    if falla:
        lineas.append(f"- Falla evaluada recientemente: {falla}")
    if sintomas:
        ultimos_sintomas = sintomas[-2:] if isinstance(sintomas, list) else [str(sintomas)]
        lineas.append(f"- Síntomas previos: {'; '.join(str(s) for s in ultimos_sintomas)}")
    if pregunta:
        lineas.append(f"- Pregunta pendiente realizada por CarBot: {pregunta}")

    return "\n".join(lineas) if lineas else "Caso activo sin datos consolidados."


def _fallback_heuristico_determinista(
    texto_usuario: str,
    contexto_estado: Any,
    latencia_ms: float = 0.0,
) -> InterpretacionSemantica:
    """Fallback seguro ante caída o ausencia de conectividad con el LLM."""
    from src.core.conversacion.state_models.state import ConversationState

    temp_state = ConversationState(session_id="temp_fallback")
    if contexto_estado:
        temp_state.active_system = getattr(contexto_estado, "active_system", None)
        temp_state.marca = getattr(contexto_estado, "marca", None)
        temp_state.modelo = getattr(contexto_estado, "modelo", None)
        temp_state.placa = getattr(contexto_estado, "placa", None)

    hechos_extraidos = ExtractorHechos.extraer_y_actualizar(temp_state, texto_usuario)
    hechos_nuevos: list[HechoSemantico] = []

    for h_dict in hechos_extraidos:
        campo = h_dict.get("campo", "")
        cat = h_dict.get("categoria", "sintoma")
        tipo_map = {
            "sintoma": TipoHechoSemantico.SINTOMA,
            "condicion": TipoHechoSemantico.CONDICION,
            "inspeccion_pendiente": TipoHechoSemantico.COMPROBACION,
            "verificacion_fisica": TipoHechoSemantico.COMPROBACION,
            "componente_descartado": TipoHechoSemantico.COMPROBACION,
            "componente_reemplazado": TipoHechoSemantico.COMPROBACION,
            "antecedente": TipoHechoSemantico.COMPROBACION,
            "vehiculo": TipoHechoSemantico.VEHICULO,
            "herramienta": TipoHechoSemantico.HERRAMIENTA,
        }
        tipo_h = tipo_map.get(cat, TipoHechoSemantico.CONDICION)

        estado_crudo = str(h_dict.get("estado", "CONFIRMADO"))
        if "NO_REVISADO" in estado_crudo:
            est = EstadoHechoSemantico.NO_REVISADO
        elif cat in ("componente_reemplazado", "antecedente") or "reemplazad" in campo or "cambiad" in campo:
            est = EstadoHechoSemantico.REEMPLAZADO
        elif "DESCARTADO" in estado_crudo:
            est = EstadoHechoSemantico.DESCARTADO
        elif "AUSENTE" in estado_crudo:
            est = EstadoHechoSemantico.AUSENTE_NEGADO
        else:
            est = EstadoHechoSemantico.CONFIRMADO

        hechos_nuevos.append(
            HechoSemantico(
                tipo=tipo_h,
                campo=campo,
                valor=str(h_dict.get("valor", "")),
                estado=est,
                evidencia_texto=str(h_dict.get("texto_crudo", "")),
            )
        )

    intenciones = []
    solicita_alternativas = bool(
        re.search(
            r"\b(?:otra\s+causa|otras\s+causas|posibles\s+causas|diferenci\w*|qu[eé]\s+m[aá]s\s+puede\s+ser)\b",
            texto_usuario,
            re.IGNORECASE,
        )
    )
    if solicita_alternativas:
        intenciones.append("solicitar_alternativas")

    if ExtractorHechos.contiene_informacion_diagnostica(texto_usuario):
        intenciones.append("reportar_sintoma")

    solicita_continuar = bool(
        re.search(r"\b(?:continuar|seguir|mismo\s+caso|mismo\s+diagnostico)\b", texto_usuario, re.IGNORECASE)
    )
    if solicita_continuar:
        intenciones.append("continuar_caso")

    solicitud_caso = ExtractorHechos.clasificar_solicitud_caso(texto_usuario) or {}
    solicita_nuevo = solicitud_caso.get("accion") == "nuevo_caso"
    if solicita_nuevo:
        intenciones.append("nuevo_caso")

    pregunta_usuario = None
    m_preg = re.search(r"(?:¿|\bqu[eé]\b|\bc[oó]mo\b)[^.!?\n]+(?:\?|$)", texto_usuario, re.IGNORECASE)
    if m_preg:
        pregunta_usuario = m_preg.group(0).strip()

    veh_id = SinglePassMessageParser.extraer_vehiculo(texto_usuario)
    datos_vehiculo = {}
    if veh_id.marca:
        datos_vehiculo["marca"] = veh_id.marca
    if veh_id.modelo:
        datos_vehiculo["modelo"] = veh_id.modelo
    if veh_id.anio:
        datos_vehiculo["anio"] = str(veh_id.anio)

    placa_detectada, _ = SinglePassMessageParser.extraer_placa(texto_usuario, [])
    if placa_detectada:
        datos_vehiculo["placa"] = placa_detectada

    return InterpretacionSemantica(
        intenciones=intenciones or ["reportar_sintoma"],
        hechos_nuevos=hechos_nuevos,
        pregunta_tecnica_usuario=pregunta_usuario,
        solicita_causas_alternativas=solicita_alternativas,
        solicita_nuevo_caso=solicita_nuevo,
        solicita_continuar=solicita_continuar,
        datos_vehiculo=datos_vehiculo,
        requiere_aclaracion=False,
        explicacion_resumida="Interpretación por fallback determinista",
        confianza_interpretacion=0.75,
        origen="heuristica_fallback",
        latencia_ms=latencia_ms,
    )


def interpretar_mensaje_usuario(
    texto_usuario: str,
    contexto_estado: Any = None,
    timeout_segundos: float = 3.5,
) -> InterpretacionSemantica:
    """Interpreta semánticamente el mensaje del mecánico utilizando LLM de entrada (Groq/Gemini)."""
    t_start = time.perf_counter()
    texto_limpio = (texto_usuario or "").strip()

    if not texto_limpio:
        return _fallback_heuristico_determinista(texto_limpio, contexto_estado, 0.0)

    # 1. Comprobar si Groq está disponible para comprensión semántica ultrarrápida
    clave_groq = settings.groq_api_key.strip()
    if clave_groq and settings.groq_chat_enabled:
        try:
            texto_sanitizado = redactar_datos_sensibles_para_llm(
                sanitizar_prompt_usuario(texto_limpio, max_length=settings.user_text_max_chars)
            )
            resumen_contexto = _construir_contexto_resumido(contexto_estado)

            prompt_usuario = (
                f"CONTEXTO DEL CASO:\n{resumen_contexto}\n\n"
                f'MENSAJE DEL MECÁNICO:\n"{texto_sanitizado}"\n\n'
                "Interpreta las intenciones, síntomas, condiciones, comprobaciones (distinguiendo NO_REVISADO, REEMPLAZADO y DESCARTADO) "
                "y la pregunta técnica si existe. Devuelve el JSON:"
            )

            payload = {
                "model": settings.groq_model,
                "messages": [
                    {"role": "system", "content": PROMPT_COMPRENSION_SISTEMA},
                    {"role": "user", "content": prompt_usuario},
                ],
                "temperature": 0.1,
                "max_tokens": 450,
                "response_format": {"type": "json_object"},
            }

            timeout_req = min(float(settings.groq_timeout_seconds), timeout_segundos)
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {clave_groq}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=timeout_req,
            )

            if resp.status_code == 200:
                body = resp.json()
                raw_content = body["choices"][0]["message"]["content"].strip()
                data = json.loads(raw_content)

                latencia_ms = round((time.perf_counter() - t_start) * 1000, 2)
                interp = InterpretacionSemantica.model_validate(data)
                interp.origen = "llm_groq"
                interp.latencia_ms = latencia_ms

                # Salvaguarda determinista de vehículo: si no vino en el JSON pero está en el texto
                if not interp.datos_vehiculo or not interp.datos_vehiculo.get("marca"):
                    veh_id = SinglePassMessageParser.extraer_vehiculo(texto_limpio)
                    if veh_id.marca:
                        interp.datos_vehiculo["marca"] = veh_id.marca
                    if veh_id.modelo and not interp.datos_vehiculo.get("modelo"):
                        interp.datos_vehiculo["modelo"] = veh_id.modelo
                    if veh_id.anio and not interp.datos_vehiculo.get("anio"):
                        interp.datos_vehiculo["anio"] = str(veh_id.anio)

                if not interp.datos_vehiculo.get("placa"):
                    placa_detectada, _ = SinglePassMessageParser.extraer_placa(texto_limpio, [])
                    if placa_detectada:
                        interp.datos_vehiculo["placa"] = placa_detectada

                logger.info(
                    f"[ComprensionSemantica:Groq] Éxito en {latencia_ms}ms | "
                    f"Intenciones: {interp.intenciones} | Hechos: {len(interp.hechos_nuevos)} | "
                    f"Alternativas: {interp.solicita_causas_alternativas} | Nuevo caso: {interp.solicita_nuevo_caso}"
                )
                return interp
            else:
                logger.warning(f"[ComprensionSemantica:Groq] HTTP {resp.status_code}: {resp.text[:150]}")
        except Exception as exc:
            logger.warning(f"[ComprensionSemantica:Groq] Falló interpretación: {type(exc).__name__}: {exc}")

    # 2. Si no hay Groq o falló, recurrir al fallback determinista
    latencia_ms = round((time.perf_counter() - t_start) * 1000, 2)
    return _fallback_heuristico_determinista(texto_limpio, contexto_estado, latencia_ms)
