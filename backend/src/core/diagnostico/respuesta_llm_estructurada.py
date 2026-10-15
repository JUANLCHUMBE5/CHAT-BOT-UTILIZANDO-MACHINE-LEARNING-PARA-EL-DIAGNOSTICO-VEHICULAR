"""Contrato local de salida de Gemini; la validación de seguridad sigue siendo posterior."""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Iterable, Optional

CAMPOS = ("hipotesis", "explicacion", "siguiente_prueba", "pregunta")
INSTRUCCION_JSON = (
    "Devuelve SOLO un objeto JSON válido con cuatro campos de texto: "
    '"hipotesis", "explicacion", "siguiente_prueba", "pregunta". '
    "Máximo 120 palabras en total y una sola pregunta. Usa únicamente la evidencia "
    "recibida. Si falta evidencia para una causa, escribe 'información insuficiente' "
    "en hipotesis; no inventes valores OEM, piezas ni mediciones."
)


def validar_y_formatear(
    texto: str,
    hipotesis_permitidas: Optional[Iterable[str]] = None,
) -> str:
    """Falla cerrada ante JSON inválido, claves extra o texto excesivo."""
    try:
        datos = json.loads(texto)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("Respuesta LLM no es JSON válido") from exc
    if not isinstance(datos, dict) or set(datos) != set(CAMPOS):
        raise ValueError("Campos JSON de diagnóstico incompletos o adicionales")
    if any(not isinstance(datos[c], str) or not datos[c].strip() for c in CAMPOS):
        raise ValueError("Campos JSON de diagnóstico vacíos")
    permitidas = {
        _normalizar_etiqueta(valor)
        for valor in (hipotesis_permitidas or [])
        if isinstance(valor, str) and valor.strip()
    }
    hipotesis = _normalizar_etiqueta(datos["hipotesis"])
    if permitidas and not (
        hipotesis in permitidas
        or hipotesis.startswith("informacion insuficiente")
    ):
        raise ValueError("La hipótesis del LLM no coincide con una hipótesis permitida")
    if sum(len(datos[c].split()) for c in CAMPOS) > 120:
        raise ValueError("Respuesta LLM supera 120 palabras")
    pregunta = datos["pregunta"].strip()
    if pregunta.count("¿") > 1 or pregunta.count("?") > 1:
        raise ValueError("Respuesta LLM contiene más de una pregunta")
    contenido = _normalizar_etiqueta(" ".join(datos.values()))
    patrones_peligrosos = (
        r"destap\w*\s+(?:el\s+)?radiador.{0,30}(?:caliente|hirviendo)",
        r"puent\w*.{0,35}(?:riel|common rail|inyector)",
        r"desconect\w*.{0,35}(?:inyector|bobina).{0,35}(?:motor encendido|en marcha)",
        r"regener\w*.{0,30}dpf.{0,45}(?:aceite contaminado|nivel de aceite alto)",
    )
    if any(re.search(patron, contenido) for patron in patrones_peligrosos):
        raise ValueError("Respuesta LLM contiene una instrucción peligrosa")
    explicacion = _normalizar_etiqueta(datos["explicacion"])
    if re.search(
        r"\b(?:confirmado|comprobado|medido|marca|marco|dio)\b.{0,25}"
        r"\d+(?:[.,]\d+)?\s*(?:v|bar|psi|kpa|mm|grados|rpm)\b",
        explicacion,
    ):
        raise ValueError("Respuesta LLM afirma una medición no aportada por el contrato")
    return (
        f"🛠️ Hipótesis: {datos['hipotesis'].strip()}\n"
        f"Evidencia: {datos['explicacion'].strip()}\n"
        f"Siguiente prueba: {datos['siguiente_prueba'].strip()}\n"
        f"{pregunta}"
    ).strip()


def _normalizar_etiqueta(texto: str) -> str:
    sin_acentos = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", (texto or "").casefold())
        if unicodedata.category(caracter) != "Mn"
    )
    return " ".join(re.sub(r"[^a-z0-9]+", " ", sin_acentos).split())
