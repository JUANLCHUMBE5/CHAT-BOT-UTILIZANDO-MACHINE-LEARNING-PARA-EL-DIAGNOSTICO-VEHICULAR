"""Contrato local de salida de Gemini; la validación de seguridad sigue siendo posterior."""

from __future__ import annotations

import json

CAMPOS = ("hipotesis", "explicacion", "siguiente_prueba", "pregunta")
INSTRUCCION_JSON = (
    "Devuelve SOLO un objeto JSON válido con cuatro campos de texto: "
    '"hipotesis", "explicacion", "siguiente_prueba", "pregunta". '
    "Máximo 120 palabras en total y una sola pregunta. Usa únicamente la evidencia "
    "recibida. Si falta evidencia para una causa, escribe 'información insuficiente' "
    "en hipotesis; no inventes valores OEM, piezas ni mediciones."
)


def validar_y_formatear(texto: str) -> str:
    """Falla cerrada ante JSON inválido, claves extra o texto excesivo."""
    try:
        datos = json.loads(texto)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("Respuesta LLM no es JSON válido") from exc
    if not isinstance(datos, dict) or set(datos) != set(CAMPOS):
        raise ValueError("Campos JSON de diagnóstico incompletos o adicionales")
    if any(not isinstance(datos[c], str) or not datos[c].strip() for c in CAMPOS):
        raise ValueError("Campos JSON de diagnóstico vacíos")
    if sum(len(datos[c].split()) for c in CAMPOS) > 120:
        raise ValueError("Respuesta LLM supera 120 palabras")
    pregunta = datos["pregunta"].strip()
    if pregunta.count("¿") > 1 or pregunta.count("?") > 1:
        raise ValueError("Respuesta LLM contiene más de una pregunta")
    return (
        f"🛠️ Hipótesis: {datos['hipotesis'].strip()}\n"
        f"Evidencia: {datos['explicacion'].strip()}\n"
        f"Siguiente prueba: {datos['siguiente_prueba'].strip()}\n"
        f"{pregunta}"
    ).strip()
