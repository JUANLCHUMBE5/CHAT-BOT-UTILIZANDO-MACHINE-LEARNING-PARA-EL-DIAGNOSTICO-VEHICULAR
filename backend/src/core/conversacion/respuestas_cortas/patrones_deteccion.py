"""Patrones y heurísticas para detectar respuestas cortas y dependientes de contexto."""

from __future__ import annotations

import re

PATRON_OPCION_NUMERICA = re.compile(
    r"^(?:(?:me\s+inclino\s+por|elijo|escojo|prefiero)\s+)?(la\s+)?(opci[oó]n\s+)?([1-9]|0|primera|segunda|tercera|cuarta|quinta|1️⃣|2️⃣|3️⃣)\s*[.!]?\s*$",
    re.IGNORECASE,
)

PATRON_NO_SE = re.compile(
    r"\b(no\s+s[eé]|ni\s+idea|no\s+me\s+fij[eé]|no\s+sabr[ií]a|no\s+estoy\s+seguro|desconozco|"
    r"tendr[ií]a\s+que\s+revisar|no\s+tengo\s+c[oó]mo\s+(?:comprobarlo|probarlo|revisarlo)|"
    r"no\s+tengo\s+como\s+(?:comprobarlo|probarlo|revisarlo)|no\s+sabr[ií]a\s+decir(?:te)?)\b",
    re.IGNORECASE,
)

PATRON_NO_APLICA = re.compile(
    r"\b(no\s+aplica|eso\s+no\s+aplica|no\s+corresponde|no\s+tiene\s+ese\s+sistema|no\s+cuenta\s+con\s+eso)\b",
    re.IGNORECASE,
)

PATRON_AMBIGUO = re.compile(
    r"\b(a\s+veces|creo|creo\s+que\s+s[ií]|m[aá]s\s+o\s+menos|puede\s+ser|de\s+vez\s+en\s+cuando|a\s+ratos|tal\s+vez|"
    r"parece\s+que\s+s[ií]|capaz|por\s+ratos|a\s+momentos)\b",
    re.IGNORECASE,
)

PATRON_NUMERICO_MEDICION = re.compile(
    r"(?:baja\s+a\s+|marca\s+|mide\s+|llega\s+a\s+|da\s+|tengo\s+|est[aá]\s+en\s+)?(-?\d+(?:[.,]\d+)?)\s*(psi|bar|kpa|mbar|inhg|in\s*hg|\"hg|mv|v(?:oltios?|olts?)?|ma|miliamperios?|a(?:mperios?)?|amp|ohm(?:ios)?|kohm|Ω|°c|°f|grados?(?:\s+(?:celsius|cent[ií]grados?|fahrenheit))?|rpm|km/h|%|mm|ms|ml|cm3|cc|g/s|nm)?\b",
    re.IGNORECASE,
)

CUES_RESPUESTA_CORTA = (
    "la 1",
    "la 2",
    "la 3",
    "opcion 1",
    "opcion 2",
    "opcion 3",
    "opcion 5",
    "opción 5",
    "ya revise eso",
    "ya revisé eso",
    "ya revise eso y esta todo bien",
    "ya revisé eso y está todo bien",
    "ya lo cambie",
    "ya lo cambié",
    "eso ya lo revise",
    "eso ya lo revisé",
    "ya lo revise y eso esta bien",
    "ya lo revisé y eso está bien",
    "solo caliente",
    "solo en frio",
    "solo en semaforo",
    "solo parado",
    "no se",
    "no sé",
    "ni idea",
    "creo que si",
    "creo que sí",
    "a veces",
    "no aplica",
    "eso no aplica",
    "ninguno",
    "ninguna",
    "no tengo",
    "no cuento",
    "no tengo tester",
    "tengo tester",
    "se mantienen igual",
    "permanecen igual",
    "se ponen tenues",
    "bajan bastante",
    "no lo he revisado",
    "no he revisado",
    "no revisé",
    "no revise",
    "no tengo herramientas",
    "sin herramientas",
    "no sé usarlo",
    "no se usarlo",
    "no sé cómo",
    "no se como",
    "no sé bien cómo",
    "no se bien como",
    "cómo comprobar",
    "como comprobar",
    "cómo revisar",
    "como revisar",
    "ya conseguí",
    "ya consegui",
    "me prestaron",
    "no dispongo",
    "sí tengo",
    "si tengo",
    "sí cuento",
    "si cuento",
    "lo tengo",
    "ya lo conecté",
    "ya lo conecte",
    "sí maestro",
    "si maestro",
    "si causa",
    "ajá",
    "aja",
    "así es",
    "asi es",
    "exactamente",
    "eso mismo",
    "para nada",
    "negativo",
    "nunca",
    "eso no pasa",
    "tendría que revisar",
    "tendria que revisar",
    "no tengo cómo comprobarlo",
    "no tengo como comprobarlo",
    "no estoy seguro",
)


def es_respuesta_corta(texto: str) -> bool:
    """Determina si un mensaje es una respuesta breve dependiente de contexto."""
    if not texto:
        return False
    limpio = texto.strip().lower()
    palabras = limpio.split()
    if len(palabras) <= 4:
        return True
    if any(c in limpio for c in CUES_RESPUESTA_CORTA):
        return True
    # Frases de corrección explícita no son respuestas cortas dependientes de la pregunta previa
    if re.search(r"\b(?:corrijo|me\s+equivoqu[eé]|me\s+confund[ií]|en\s+realidad|quise\s+decir)\b", limpio):
        return False
    # Afirmaciones
    if re.search(
        r"^(?:s[ií](?:[,\\s]+(?:causa|maestro|amigo|bot|carbot))?|[aá]firmativo|correcto|exactamente|eso\s+mismo|as[ií]\s+es|aj[aá]|claro(?:\s+que\s+s[ií])?|por\s+supuesto|efectivamente|lo\s+tengo|ya\s+lo\s+conect[eé]|s[ií]\s+(?:tengo|cuento|dispongo))\b",
        limpio,
    ):
        return True
    # Negaciones
    if re.search(
        r"^(?:no(?:[,\\s]+(?:causa|maestro|amigo|bot|carbot))?|negativo|para\s+nada|nunca|eso\s+no\s+pasa|en\s+lo\s+absoluto|jam[aá]s|tampoco)\b",
        limpio,
    ):
        return True
    # Menciones numéricas con unidades técnicas explícitas
    tiene_unidad_tecnica = bool(
        re.search(
            r"\b\d+(?:[.,]\d+)?\s*(?:psi|bar|kpa|mv|v(?:oltios?|olts?)?|ma|a(?:mperios?)?|ohm(?:ios)?|Ω|°c|°f|rpm|km/h|%|mm|ms)\b",
            limpio,
        )
    )
    es_duracion_temporal = bool(
        re.search(r"\b\d+\s*(?:minutos?|min|horas?|h|segundos?|seg|d[ií]as?)\b", limpio)
    )
    if tiene_unidad_tecnica or re.search(
        r"\b(?:baja\s+a|marca|da|sube\s+a|llega\s+a)\s+\d+(?:[.,]\d+)?\b", limpio
    ):
        return True
    if es_duracion_temporal:
        return False
    from src.core.conversacion.gestor_plan_b import GestorPlanB

    if (
        GestorPlanB.detectar_indisponibilidad_en_texto(limpio)
        or GestorPlanB.detectar_no_revisado(limpio)
        or GestorPlanB.detectar_no_sabe_usar(limpio)
        or GestorPlanB.detectar_no_sabe_realizar(limpio)
        or GestorPlanB.detectar_recuperacion_herramienta(limpio)
    ):
        return True
    return False
