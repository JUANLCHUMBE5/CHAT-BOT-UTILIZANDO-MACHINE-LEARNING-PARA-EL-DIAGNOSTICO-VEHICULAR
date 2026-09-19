"""Interpretación determinista del combustible y su modo de falla en conversaciones."""

from __future__ import annotations

import re
from typing import Optional

_GLP = r"(?:glp|gas licuado(?: de petr[oó]leo)?|autogas|propano)"
_GNV = r"(?:gnv|gas natural(?: vehicular)?|metano)"
_GASOLINA = r"gasolina"
_GAS = rf"(?:{_GLP}|{_GNV}|gas)"
_EXCLUSIVO = r"(?:solo|solamente|[úu]nicamente)"
_SUFIJO_EXCLUSIVO = r"(?:nom[áa]s|nada m[áa]s)"


def _detectar_combustible(texto: str) -> Optional[str]:
    if re.search(rf"\b{_GNV}\b", texto):
        return "GNV"
    if re.search(rf"\b{_GLP}\b", texto):
        return "GLP"
    if re.search(rf"\b{_GASOLINA}\b", texto):
        return "gasolina"
    return None


def extraer_contexto_combustible(
    texto: str,
    combustible_previo: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Devuelve combustible y modo: solo_gas, solo_gasolina o ambos.

    Esta capa solo interpreta el lenguaje conversacional. No predice fallas ni
    sustituye la comparación solicitada cuando el mensaje continúa ambiguo.
    """
    limpio = texto.lower().strip()
    combustible = _detectar_combustible(limpio) or combustible_previo
    contiene_exclusivo = bool(re.search(rf"\b{_EXCLUSIVO}\b|\b{_SUFIJO_EXCLUSIVO}\b", limpio))

    solo_gas = bool(
        re.search(
            rf"\b{_EXCLUSIVO}\s+(?:falla\s+)?(?:en\s+|a\s+|con\s+|usando\s+)?{_GAS}\b",
            limpio,
        )
        or re.search(rf"\b{_GAS}\s+{_SUFIJO_EXCLUSIVO}\b", limpio)
    )
    solo_gasolina = bool(
        re.search(
            rf"\b{_EXCLUSIVO}\s+(?:falla\s+)?(?:en\s+|a\s+|con\s+|usando\s+)?{_GASOLINA}\b",
            limpio,
        )
        or re.search(rf"\b{_GASOLINA}\s+{_SUFIJO_EXCLUSIVO}\b", limpio)
    )

    frases_bien = ("funciona bien", "anda bien", "va bien", "normal", "no falla")
    clausulas = [parte.strip() for parte in re.split(r"[,;]|\bpero\b", limpio) if parte.strip()]
    gasolina_bien = any(
        re.search(rf"\b{_GASOLINA}\b", clausula) and any(frase in clausula for frase in frases_bien)
        for clausula in clausulas
    )
    gas_bien = any(
        re.search(rf"\b{_GAS}\b", clausula) and any(frase in clausula for frase in frases_bien)
        for clausula in clausulas
    )

    if solo_gas:
        return combustible, "solo_gas"
    if solo_gasolina:
        return combustible, "solo_gasolina"
    if gasolina_bien and combustible_previo in {"GNV", "GLP"}:
        return combustible_previo, "solo_gas"
    if gas_bien:
        return combustible, "solo_gasolina"

    ambos = bool(
        re.search(r"\b(?:ambos|los dos|las dos)\b", limpio)
        or (
            not contiene_exclusivo
            and re.search(rf"\b{_GASOLINA}\s+y\s+(?:{_GLP}|{_GNV})\b", limpio)
        )
        or (
            not contiene_exclusivo
            and re.search(rf"\b(?:{_GLP}|{_GNV})\s+y\s+{_GASOLINA}\b", limpio)
        )
    )
    return combustible, "ambos" if ambos else None
