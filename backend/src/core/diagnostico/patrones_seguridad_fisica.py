"""Detección determinista de riesgos físicos formulados en lenguaje de taller."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from src.core.diagnostico.banners_seguridad import (
    BANNER_ACEITE,
    BANNER_AIRBAG_SRS,
    BANNER_ALTERNADOR_SOBREVOLTAJE,
    BANNER_BATERIA_DANADA,
    BANNER_COMBUSTIBLE,
    BANNER_DIESEL_ALTA_PRESION,
    BANNER_DIESEL_EMBALAMIENTO_ACTIVO,
    BANNER_DIRECCION_CRITICA,
    BANNER_ESCAPE_CALIENTE,
    BANNER_FRENO,
    BANNER_GATO_SIN_CABALLETES,
    BANNER_HV,
    BANNER_MONOXIDO_CARBONO,
    BANNER_SOLDADURA_TANQUE,
    BANNER_VEHICULO_RODANDO,
)


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(caracter for caracter in texto if unicodedata.category(caracter) != "Mn")


_PATRONES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"(?=.*\b(?:luz|testigo)\b.{0,30}\b(?:roja?\s+)?(?:de\s+)?aceite\b)"
            r"(?=.*\b(?:parpade\w*|encendid\w*|prendid\w*|presion\s+(?:de\s+)?aceite\s+\w+)\b)"
            r"(?=.*\b(?:traquete\w*|golpete\w*|cascabele\w*|ruido\s+metalico|golpe\w*\s+metalico)\b)"
        ),
        BANNER_ACEITE,
    ),
    (
        re.compile(
            r"(?=.*\b24\s*(?:v|voltios)\b)(?=.*\b12\s*(?:v|voltios)\b)"
            r"(?=.*\balternador\b)"
            r"(?=.*\b(?:meter\w*|aplic\w*|conect\w*|pon\w*|probar|energiz\w*|puente\w*)\b)"
        ),
        BANNER_ALTERNADOR_SOBREVOLTAJE,
    ),
    (
        re.compile(
            r"\b(?:motor|diesel)\b.{0,90}\b(?:se acelero solo|se embalo|no se apaga|"
            r"no apaga con la llave|no responde a la llave)\b.{0,90}\b(?:humo|llave|solo|"
            r"aceler|apaga|control)\b",
        ),
        BANNER_DIESEL_EMBALAMIENTO_ACTIVO,
    ),
    (
        re.compile(
            r"\b(?:afloj\w*|desconect\w*|solt\w*|retir\w*|purg\w*)\b.{0,70}\b"
            r"(?:caneria|cano|tuberia|tubo|riel|rail|common\s*rail|inyector)\b.{0,65}\b"
            r"(?:motor\s+(?:encendido|funcionando|en\s+marcha)|presurizad\w*|alta\s+presion)\b|"
            r"\b(?:motor\s+(?:encendido|funcionando|en\s+marcha)|presurizad\w*)\b.{0,70}\b"
            r"(?:afloj\w*|desconect\w*|solt\w*|retir\w*|purg\w*)\b.{0,65}\b"
            r"(?:caneria|cano|tuberia|tubo|riel|rail|common\s*rail|inyector)\b"
        ),
        BANNER_DIESEL_ALTA_PRESION,
    ),
    (
        re.compile(
            r"(?=.*\b(?:bajada|pendiente|cuesta)\b)"
            r"(?=.*\b(?:rodando|se\s+mueve|desplazandose|rueda|moviendo)\b)"
            r"(?=.*\b(?:freno\s+de\s+mano|cable\s+(?:de\s+)?freno|sin\s+freno)\b)"
        ),
        BANNER_VEHICULO_RODANDO,
    ),
    (
        re.compile(
            r"\bpedal\s+(?:de\s+)?freno\b.{0,50}\b(?:se\s+va|llega|se\s+hunde|cede)\b"
            r".{0,25}\b(?:fondo|piso)\b|"
            r"\b(?:no\s+frena\s+casi\s+nada|frena\s+apenas|pierde\s+liquido\s+(?:de\s+)?"
            r"frenos?|testigo\s+rojo.{0,25}\bfreno|liquido\s+de\s+freno.{0,30}"
            r"(?:gotea|pierde|se\s+sale)|manguera.{0,60}(?:freno|liquido).{0,35}"
            r"(?:hernia|hinchad\w*|abultad\w*|bola))\b"
        ),
        BANNER_FRENO,
    ),
    (
        re.compile(
            r"\b(?:timon|volante|direccion\s+asistida)\b.{0,55}\b(?:duro|trancad\w*|"
            r"pesad\w*|se\s+puso)\b.{0,60}\b(?:golpe|curva|circul|manejan|pista)\b|"
            r"\b(?:bomba\s+de\s+direccion|bomba\s+hidraulica)\b.{0,80}\b"
            r"(?:humo|huele\s+a\s+quemado|chilla\s+durisimo|se\s+quema)\b"
        ),
        BANNER_DIRECCION_CRITICA,
    ),
    (
        re.compile(
            r"\b(?:combustible|gasolina|nafta|petroleo|diesel)\b.{0,60}\b"
            r"(?:gotea|goteando|chorrea|derramand\w*|cayendo)\b.{0,85}\b"
            r"(?:multiple|escape|tubo\s+de\s+escape|caliente|calor)\b|"
            r"\b(?:gotea|goteando|chorrea|derramand\w*)\b.{0,60}\b"
            r"(?:combustible|gasolina|nafta|petroleo|diesel)\b.{0,85}\b"
            r"(?:multiple|escape|caliente|calor)\b"
        ),
        BANNER_COMBUSTIBLE,
    ),
    (
        re.compile(
            r"\b(?:cort\w*|manipul\w*|desconect\w*|revis\w*|abr\w*)\b.{0,70}\b"
            r"cables?\s+naranj\w*|\bcables?\s+naranj\w*.{0,70}\b"
            r"(?:cort\w*|manipul\w*|desconect\w*|revis\w*)\b"
        ),
        BANNER_HV,
    ),
    (
        re.compile(
            r"\bbateria\b.{0,80}\b(?:hinchad\w*|deformad\w*|ardiendo|muy\s+caliente|"
            r"caliente)\b.{0,80}\b(?:gas|huevo\s+podrido|azufre|huele|olor)\b|"
            r"\bbateria\b.{0,80}\b(?:gas\s+de\s+azufre|olor\s+a\s+huevo\s+podrido)\b"
        ),
        BANNER_BATERIA_DANADA,
    ),
    (
        re.compile(
            r"\b(?:gato|gata|gata\s+hidraulica)\b.{0,90}\b(?:solo|unico|sin\s+caballetes|"
            r"sin\s+soportes|sin\s+torres)\b.{0,120}\b(?:debajo|abajo|meter\w*\s+debajo|"
            r"trabajar\s+abajo)\b|"
            r"\b(?:debajo|meter\w*\s+abajo|trabajar\s+debajo)\b.{0,100}\b"
            r"(?:gato|gata)\b.{0,70}\b(?:solo|unico|sin\s+caballetes|sin\s+soportes|sin\s+torres)\b"
        ),
        BANNER_GATO_SIN_CABALLETES,
    ),
    (
        re.compile(
            r"\b(?:taller|garaje|garage|local)\b.{0,75}\b(?:cerrad\w*|sin\s+ventanas|"
            r"sin\s+ventilacion|sin\s+extractor)\b.{0,100}\b(?:motor|acelerand\w*|"
            r"encendid\w*)\b.{0,120}\b(?:maread\w*|mareo|maree|nauseas|dolor\s+de\s+cabeza)\b|"
            r"\b(?:motor|acelerand\w*|encendid\w*)\b.{0,75}\b(?:taller|garaje|garage)\b"
            r".{0,75}\b(?:cerrad\w*|sin\s+ventanas|sin\s+ventilacion|sin\s+extractor)\b"
            r".{0,120}\b(?:maread\w*|mareo|maree|nauseas|dolor\s+de\s+cabeza)\b"
        ),
        BANNER_MONOXIDO_CARBONO,
    ),
    (
        re.compile(
            r"\b(?:airbag|bolsa\s+de\s+aire|detonador|squib)\b.{0,80}\b"
            r"(?:multimetro|continuidad|ohm\w*|resistencia)\b|"
            r"\b(?:multimetro|continuidad|ohm\w*|resistencia)\b.{0,80}\b"
            r"(?:airbag|bolsa\s+de\s+aire|detonador|squib)\b"
        ),
        BANNER_AIRBAG_SRS,
    ),
    (
        re.compile(
            r"\b(?:turbo|caracola|multiple|escape)\b.{0,80}\b(?:al\s+rojo\s+vivo|"
            r"incandescente|rojo\s+vivo)\b.{0,80}\b(?:humo|aceite|llama|fuego)\b|"
            r"\b(?:al\s+rojo\s+vivo|incandescente|rojo\s+vivo)\b.{0,80}\b"
            r"(?:turbo|caracola|multiple|escape)\b.{0,80}\b(?:humo|aceite|llama|fuego)\b"
        ),
        BANNER_ESCAPE_CALIENTE,
    ),
    (
        re.compile(
            r"\b(?:sold\w*|soplete|cort\w*|esmeril\w*)\b.{0,90}\b"
            r"(?:tanque|deposito)\b.{0,60}\b(?:gasolina|combustible|nafta|diesel|vaciad\w*)\b|"
            r"\b(?:tanque|deposito)\b.{0,60}\b(?:gasolina|combustible|nafta|diesel)\b"
            r".{0,90}\b(?:sold\w*|soplete|cort\w*|esmeril\w*)\b"
        ),
        BANNER_SOLDADURA_TANQUE,
    ),
)


def detectar_riesgo_fisico(texto: str) -> Optional[str]:
    """Devuelve un bloqueo seguro para un riesgo activo o una maniobra inminente."""
    normalizado = _normalizar(texto or "")
    for patron, banner in _PATRONES:
        if patron.search(normalizado):
            return banner
    return None
