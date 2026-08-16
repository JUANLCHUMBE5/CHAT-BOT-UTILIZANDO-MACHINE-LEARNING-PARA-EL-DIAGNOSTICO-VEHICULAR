"""Extracción conservadora de datos del vehículo desde mensajes breves."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


MARCAS = (
    "alfa romeo", "aston martin", "great wall", "mercedes benz", "land rover",
    "toyota", "suzuki", "hyundai", "kia", "nissan", "chevrolet", "volkswagen",
    "ford", "mazda", "honda", "mitsubishi", "subaru", "renault", "peugeot",
    "citroen", "fiat", "bmw", "audi", "volvo", "lexus", "changan", "jac",
    "dfsk", "byd", "geely", "jeep", "dodge", "ram", "isuzu", "foton",
)

COMBUSTIBLES = {
    "gasolina": "gasolina",
    "diesel": "diésel",
    "petroleo": "diésel",
    "gnv": "GNV",
    "glp": "GLP",
    "hibrido": "híbrido",
    "electrico": "eléctrico",
}


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto.lower())
    return " ".join(
        "".join(c for c in base if not unicodedata.combining(c)).split()
    )


def extraer_datos_vehiculo(texto: str) -> dict[str, Any]:
    """Extrae solo datos explícitos; nunca intenta adivinar una versión."""

    normalizado = _normalizar(texto)
    datos: dict[str, Any] = {}

    anio = re.search(r"\b((?:19|20)\d{2})\b", normalizado)
    if anio:
        valor = int(anio.group(1))
        if 1886 <= valor <= 2100:
            datos["anio"] = valor

    marca_encontrada = next(
        (marca for marca in MARCAS if re.search(rf"\b{re.escape(marca)}\b", normalizado)),
        None,
    )
    marca_etiquetada = re.search(
        r"\bmarca\s*[:=-]?\s*([a-z][a-z ]{1,30}?)(?=\s+(?:modelo|ano|año|motor|combustible)\b|[,;\n]|$)",
        normalizado,
    )
    if marca_encontrada:
        datos["marca"] = marca_encontrada.title()
    elif marca_etiquetada:
        datos["marca"] = marca_etiquetada.group(1).strip().title()

    modelo_etiquetado = re.search(
        r"\bmodelo\s*[:=-]?\s*([a-z0-9][a-z0-9 .-]{0,35}?)(?=\s+(?:ano|año|motor|combustible|cilindrada)\b|[,;\n]|$)",
        normalizado,
    )
    if modelo_etiquetado:
        datos["modelo"] = modelo_etiquetado.group(1).strip().upper()
    elif marca_encontrada:
        despues = normalizado.split(marca_encontrada, 1)[1].strip()
        candidatos = []
        for token in despues.split():
            token_limpio = token.strip(",;")
            if re.fullmatch(r"(?:19|20)\d{2}", token_limpio):
                break
            if token_limpio in {"del", "de", "ano", "año", "motor", "combustible", "con", "a", "es"}:
                if candidatos:
                    break
                continue
            if re.fullmatch(r"\d+(?:\.\d+)?", token_limpio) or token_limpio in COMBUSTIBLES:
                break
            candidatos.append(token_limpio)
            if len(candidatos) >= 3:
                break
        if candidatos:
            datos["modelo"] = " ".join(candidatos).upper()

    motor = re.search(
        r"\b(?:motor|cilindrada)\s*[:=-]?\s*(\d{1,4}(?:[.,]\d{1,2})?)\s*(cc|cm3|l|litros?)?\b",
        normalizado,
    )
    if not motor:
        motor = re.search(r"\b(\d[.,]\d)\s*(l|litros?)\b", normalizado)
    if motor:
        valor = motor.group(1).replace(",", ".")
        unidad = (motor.group(2) or "L").upper()
        datos["motor"] = f"{valor} {unidad}"

    combustibles = [
        etiqueta for termino, etiqueta in COMBUSTIBLES.items()
        if re.search(rf"\b{termino}\b", normalizado)
    ]
    if combustibles:
        datos["combustible"] = " + ".join(dict.fromkeys(combustibles))

    equipo = re.search(
        r"\b(?:equipo|kit)\s+(?:gnv|glp|de gas)?\s*[:=-]?\s*([a-z][a-z0-9 .-]{2,40}?)(?=\s+(?:marca|modelo|ano|año|motor)\b|[,;\n]|$)",
        normalizado,
    )
    if equipo:
        datos["equipo_gas"] = equipo.group(1).strip().title()

    if re.search(r"\bno (?:se|lo)\b|\bno se(?:\s+cual|\s+que)?\b", normalizado):
        for campo in ("motor", "equipo_gas"):
            if campo not in datos:
                datos[campo] = "desconocido"

    kilometraje = re.search(r"\b(\d[\d .]*)\s*(mil)?\s*km\b", normalizado)
    if kilometraje:
        base = int(re.sub(r"\D", "", kilometraje.group(1)))
        datos["kilometraje"] = base * 1000 if kilometraje.group(2) else base

    return datos


def kilometraje_es_ambiguo(texto: str) -> bool:
    """Detecta cifras pequeñas que suelen representar una omisión de «mil»."""

    normalizado = _normalizar(texto)
    coincidencia = re.search(r"\b(?:mas de\s+)?(\d{2,3})\s*km\b", normalizado)
    return bool(coincidencia and int(coincidencia.group(1)) <= 500)
