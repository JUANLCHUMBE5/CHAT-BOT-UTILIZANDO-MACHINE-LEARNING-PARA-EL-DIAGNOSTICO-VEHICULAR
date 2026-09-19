"""Formato breve y legible para respuestas técnicas enviadas por WhatsApp."""

from __future__ import annotations

import re


def formatear_consulta_tecnica_whatsapp(
    texto: str,
    *,
    modelo_informado: bool = False,
    limite_cuerpo: int = 240,
) -> str:
    """Reduce explicaciones extensas sin convertir datos opcionales en requisitos."""

    limpio = re.sub(r"\s+", " ", texto.replace("**", "").replace("*", "")).strip()
    encabezados = (
        "Orientación general:",
        "Especificación exacta del fabricante:",
        "Datos faltantes para mayor precisión:",
        "Verificación segura:",
    )
    for encabezado in encabezados:
        limpio = limpio.replace(encabezado, "")
    limpio = re.sub(r"\s+", " ", limpio).strip()

    if len(limpio) > limite_cuerpo:
        corte = limpio.rfind(" ", 0, limite_cuerpo)
        limpio = limpio[: corte if corte > 0 else limite_cuerpo].rstrip(" ,;:.") + "…"

    respuesta = f"💡 *Orientación CarBot*\n{limpio}"
    if not modelo_informado:
        respuesta += "\n🚗 Si sabes el modelo, envíalo para afinar."
    return respuesta
