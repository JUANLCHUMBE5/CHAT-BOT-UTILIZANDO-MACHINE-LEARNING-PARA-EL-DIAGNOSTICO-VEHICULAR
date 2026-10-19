"""Herramientas y patrones de disponibilidad de taller."""

import re
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class HerramientaAutomotriz:
    clave: str
    nombre_canonico: str
    terminos: Tuple[str, ...]
    patron_mencion: re.Pattern


CATALOGO_HERRAMIENTAS: Dict[str, HerramientaAutomotriz] = {
    "multimetro": HerramientaAutomotriz(
        clave="multimetro",
        nombre_canonico="multímetro / tester automotriz",
        terminos=("multímetro", "multimetro", "tester", "voltímetro", "voltimetro"),
        patron_mencion=re.compile(r"\b(mult[ií]metro|tester|volt[ií]metro)\b", re.IGNORECASE),
    ),
    "manometro": HerramientaAutomotriz(
        clave="manometro",
        nombre_canonico="manómetro de presión de combustible",
        terminos=("manómetro", "manometro", "medidor de presión", "presión de gasolina"),
        patron_mencion=re.compile(
            r"\b(man[oó]metro|medir\s+(?:la\s+)?presi[oó]n|presi[oó]n\s+de\s+(?:gasolina|combustible))\b",
            re.IGNORECASE,
        ),
    ),
    "chispa": HerramientaAutomotriz(
        clave="chispa",
        nombre_canonico="probador de chispa / herramientas de encendido",
        terminos=("chispa", "probador de chispa", "sacar bujías", "llave de bujías"),
        patron_mencion=re.compile(
            r"\b(comprobar\s+(?:la\s+)?chispa|probador\s+de\s+chispa|llave\s+de\s+buj[ií]as?|sacar\s+(?:las\s+)?buj[ií]as?|chispa)\b",
            re.IGNORECASE,
        ),
    ),
    "escaner": HerramientaAutomotriz(
        clave="escaner",
        nombre_canonico="escáner de diagnóstico OBD-II",
        terminos=("escáner", "escaner", "scanner", "obd", "obd2", "lector de códigos"),
        patron_mencion=re.compile(r"\b(esc[aá]ner|scanner|lector\s+obd|obd2?)\b", re.IGNORECASE),
    ),
    "compresimetro": HerramientaAutomotriz(
        clave="compresimetro",
        nombre_canonico="compresímetro de motor",
        terminos=("compresímetro", "compresimetro", "medir compresión"),
        patron_mencion=re.compile(r"\b(compres[ií]metro|medir\s+(?:la\s+)?compresi[oó]n)\b", re.IGNORECASE),
    ),
    "vacuometro": HerramientaAutomotriz(
        clave="vacuometro",
        nombre_canonico="vacuómetro de vacío de admisión",
        terminos=("vacuómetro", "vacuometro", "medidor de vacío"),
        patron_mencion=re.compile(r"\b(vacu[oó]metro|medidor\s+de\s+vac[ií]o)\b", re.IGNORECASE),
    ),
    "elevador": HerramientaAutomotriz(
        clave="elevador",
        nombre_canonico="elevador de taller / gata hidráulica",
        terminos=("elevador", "gata", "fosa", "caballetes"),
        patron_mencion=re.compile(r"\b(elevador|gata(\s+hidr[aá]ulica)?|fosa|caballetes)\b", re.IGNORECASE),
    ),
    "reloj_comparador": HerramientaAutomotriz(
        clave="reloj_comparador",
        nombre_canonico="reloj comparador de carátula",
        terminos=("reloj comparador", "micrómetro", "vernier"),
        patron_mencion=re.compile(r"\b(reloj\s+comparador|micr[oó]metro|vernier)\b", re.IGNORECASE),
    ),
    "osciloscopio": HerramientaAutomotriz(
        clave="osciloscopio",
        nombre_canonico="osciloscopio automotriz",
        terminos=("osciloscopio", "osciloscopio digital", "oscilograma"),
        patron_mencion=re.compile(r"\b(osciloscopio|oscilograma)\b", re.IGNORECASE),
    ),
    "extractor": HerramientaAutomotriz(
        clave="extractor",
        nombre_canonico="extractor hidr\u00e1ulico de inyectores",
        terminos=("extractor", "extractor hidr\u00e1ulico"),
        patron_mencion=re.compile(r"\b(extractor(\s+hidr[a\u00e1]ulico)?)\b", re.IGNORECASE),
    ),
    "ayudante": HerramientaAutomotriz(
        clave="ayudante",
        nombre_canonico="asistente o ayudante de taller",
        terminos=("ayudante", "asistente", "otra persona", "solo en el taller"),
        patron_mencion=re.compile(
            r"\b(ayudante|asistente|otra\s+persona|solo(\s+en\s+el\s+taller)?)\b", re.IGNORECASE
        ),
    ),
    "general": HerramientaAutomotriz(
        clave="general",
        nombre_canonico="herramientas de taller",
        terminos=("herramientas", "instrumentos", "equipo"),
        patron_mencion=re.compile(r"\b(herramientas?|instrumental|equipo|llaves)\b", re.IGNORECASE),
    ),
}

PATRON_NO_TENGO = re.compile(
    r"\b((?:no|tampoco|ni)\s+(?:tengo|cuento\s+con|dispongo\s+de|poseo)|"
    r"sin\s+herramientas?|ninguna\s+herramienta|cero\s+herramientas|"
    r"sin\s+(?:extractor|ayudante|asistente|osciloscopio)|"
    r"estoy\s+solo|no\s+puedo\s+(?:dar\s+arranque|desmontar|sacar))\b",
    re.IGNORECASE,
)

PATRON_NO_SE_USAR = re.compile(
    r"\b(no\s+s[eé]\s+(?:usar(?:lo|la)?|c[oó]mo\s+usar(?:lo|la)?|ocupar(?:lo|la)?)|no\s+tengo\s+experiencia\s+usando)\b",
    re.IGNORECASE,
)

PATRON_NO_REVISADO = re.compile(
    r"\b(no\s+(?:lo\s+)?he\s+(?:revisado|probado|chequeado|checado|verificado|mirado)|"
    r"no\s+he\s+revisado\s+nada|todav[ií]a\s+no|a[uú]n\s+no\s+(?:lo\s+)?(?:reviso|s[eé])|"
    r"no\s+revis[eé]\s+(?:nada|todav[ií]a)?)\b",
    re.IGNORECASE,
)

PATRON_NO_SABE_REALIZAR = re.compile(
    r"\b("
    r"(?:no\s+s[eé]|no\s+sabemos|no\s+sabr[ií]a|no\s+s[eé]\s+bien)\s+(?:bien\s+)?(?:c[oó]mo\s+)?(?:comprobar|revisar|verificar|chequear|checar|medir|probar|hacer(?:lo|la)?|ver|mirar)|"
    r"c[oó]mo\s+(?:se\s+)?(?:comprueba|revisa|verifica|mide|prueba|chequea|hace)|"
    r"no\s+s[eé]\s+(?:hacer|comprobar|revisar|medir)|"
    r"no\s+tengo\s+experiencia\s+(?:comprobando|revisando|midiendo)|"
    r"no\s+s[eé]\s+c[oó]mo\s+(?:hacer|comprobar|revisar|medir)"
    r")\b",
    re.IGNORECASE,
)

# A diferencia de "no sé cómo hacerlo", esta declaración indica que el usuario
# no puede realizar ninguna comprobación física del caso. No debe abrir otra
# cadena de preguntas de Plan B: se conserva el caso y se deriva a revisión.
PATRON_CONSIGUIO_HERRAMIENTA = re.compile(
    r"\b(ya\s+(?:consegu[ií]|tengo|me\s+prestaron)|ahora\s+s[ií]\s+tengo|consegu[ií]\s+(?:un|una))\b",
    re.IGNORECASE,
)
