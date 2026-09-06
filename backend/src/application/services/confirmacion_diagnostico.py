"""Interpretación segura de confirmaciones técnicas recibidas por WhatsApp."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConfirmacionDiagnosticoWhatsApp:
    """Comando explícito enviado por un mecánico para validar su último diagnóstico."""

    estado: str
    observacion: str | None = None
    requiere_observacion: bool = False


def _normalizar(texto: str) -> str:
    sin_tildes = "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caracter)
    )
    return re.sub(r"\s+", " ", sin_tildes.strip().lower())


def _extraer_observacion(texto: str, prefijos: tuple[str, ...]) -> str | None:
    original = texto.strip()
    normalizado = _normalizar(original)
    for prefijo in sorted(prefijos, key=len, reverse=True):
        if normalizado == prefijo:
            return None
        if normalizado.startswith(prefijo):
            resto = original[len(prefijo) :].lstrip(" :-–—\t")
            return resto.strip()[:4000] or None
    return None


def interpretar_confirmacion_whatsapp(
    texto: str,
) -> ConfirmacionDiagnosticoWhatsApp | None:
    """Reconoce únicamente órdenes explícitas para no confundir síntomas con validaciones."""

    normalizado = _normalizar(texto)
    confirmar = ("confirmar", "confirmado", "falla confirmada", "diagnostico confirmado")
    descartar = ("descartar", "descartado", "falla diferente", "diagnostico incorrecto")
    revisar = ("revisar", "en revision", "dejar en revision")

    for prefijos, estado, requiere_observacion in (
        (confirmar, "confirmado", False),
        (descartar, "descartado", True),
        (revisar, "en_revision", False),
    ):
        if any(
            normalizado == prefijo
            or normalizado.startswith(f"{prefijo}:")
            or normalizado.startswith(f"{prefijo} -")
            for prefijo in prefijos
        ):
            return ConfirmacionDiagnosticoWhatsApp(
                estado=estado,
                observacion=_extraer_observacion(texto, prefijos),
                requiere_observacion=requiere_observacion,
            )
    return None


def interpretar_respuesta_validacion_whatsapp(texto: str) -> str | None:
    """Interpreta un SÍ/NO únicamente cuando el flujo ya espera esa respuesta."""

    normalizado = _normalizar(texto).strip(" .,!¡¿?")
    respuestas_positivas = {
        "si",
        "correcto",
        "correcta",
        "fue correcto",
        "fue correcta",
        "esta bien",
    }
    respuestas_negativas = {
        "no",
        "incorrecto",
        "incorrecta",
        "fue incorrecto",
        "fue incorrecta",
        "esta mal",
    }
    if normalizado in respuestas_positivas:
        return "si"
    if normalizado in respuestas_negativas:
        return "no"
    return None


def instrucciones_confirmacion_whatsapp() -> str:
    """Pregunta breve que acompaña cada resultado dirigido a personal técnico."""

    return (
        "\n\n🔎 ¿Fue correcta? *SÍ / NO*"
    )
