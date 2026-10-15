"""Límite de aclaraciones del caso, independiente del tipo de pregunta."""

from __future__ import annotations

import re

from src.core.conversacion.models import ConversationState


def dato_desconocido(texto: str) -> bool:
    """Reconoce que el mecánico no dispone del dato solicitado."""
    return bool(re.search(
        r"\b(?:no\s+(?:s[eé]|lo\s+(?:s[eé]|tengo)|tengo|dispongo)|"
        r"sin\s+(?:dato|lectura|esc[aá]ner|medici[oó]n)|"
        r"todav[ií]a\s+no\s+(?:lo\s+)?(?:med[ií]|tengo))\b",
        texto.casefold(),
    ))


def aclaraciones_emitidas(estado: ConversationState) -> int:
    """Cuenta preguntas únicas realmente mostradas, aunque se registraran sin contador."""
    return len({
        " ".join(str(p.get("texto", "")).casefold().split())
        for p in estado.preguntas_realizadas
        if "¿" in str(p.get("texto", ""))
    })


def debe_avanzar(estado: ConversationState, texto: str) -> bool:
    """No sigue solicitando la misma medición ausente ni supera el tope configurado."""
    if not estado.active_symptoms and not estado.hechos:
        return False
    return aclaraciones_emitidas(estado) >= estado.max_repreguntas or (
        bool(estado.preguntas_realizadas) and dato_desconocido(texto)
    )
