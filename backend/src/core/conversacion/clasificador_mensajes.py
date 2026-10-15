"""Intención conversacional previa a extracción y segmentación del caso."""

from __future__ import annotations

import re

from src.core.conversacion.models import ConversationState


def clasificar_mensaje(texto: str, estado: ConversationState) -> str:
    """Clasificación conservadora: nunca interpreta un descarte como caso nuevo."""
    mensaje = " ".join(texto.casefold().split())
    if re.fullmatch(r"(?:s[ií]|correcto|confirmo|exacto)", mensaje):
        return "confirmacion"
    if re.fullmatch(r"(?:no|incorrecto|descarto|no es esa)", mensaje):
        return "descarte" if estado.top3_actual or estado.falla_principal else "respuesta_pendiente"
    if re.search(r"\b(?:ya\s+(?:lo\s+)?revis[eé]|ya\s+chequ[eé]|est[aá]\s+bien|no\s+es\s+|descart[ée])\b", mensaje):
        return "descarte"
    if re.search(r"\b(?:encontr[eé]|hall[eé]|detect[eé]|inyectores?|injectores?|maf\s+da|fuga\s+de)\b", mensaje):
        return "hallazgo_mecanico"
    if estado.preguntas_realizadas and (
        re.search(r"\b(?:no\s+s[eé]|no\s+(?:lo\s+)?tengo|sin\s+(?:dato|lectura))\b", mensaje)
        or re.search(r"\b(?:al\s+acelerar|en\s+caliente|en\s+fr[ií]o|\d+\s*(?:rpm|psi|kpa|%))\b", mensaje)
    ):
        return "respuesta_pendiente"
    return "sintoma_nuevo"
