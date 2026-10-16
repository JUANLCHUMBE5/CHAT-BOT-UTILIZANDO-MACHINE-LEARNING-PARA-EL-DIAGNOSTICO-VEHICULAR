"""Alcance local de negaciones sobre eventos, sin inferir fallas físicas."""
from __future__ import annotations

import re

# Una coordinación con predicado propio inicia otra proposición. Las listas
# nominales conservan la negación ("no hay vibración ni ruido").
_CORTES = re.compile(r"[.;?!]+|\b(?:pero|aunque|adem[aá]s|sin\s+embargo|sino|no\s+obstante)\b", re.I)
_COORDINACION = re.compile(r",|\b(?:y|e|ni)\b", re.I)
_VERBO = re.compile(
    r"\b(?:hay|teng\w*|tien\w*|tenemos|present\w*|existe\w*|"
    r"chorrea\w*|gotea\w*|pierde\w*|bota\w*|huele\w*|vibra(?:n|mos|ba|ban)?|"
    r"suena\w*|escuch\w*|sient\w*|not[ao]\w*|detect\w*|observ\w*|"
    r"sale|est[aá]|funciona|falla|aparece)\b", re.I,
)
_NEGACION = re.compile(
    r"\b(?:no|tampoco|ni|sin|nunca|jam[aá]s|cero|descartad[oa])\b", re.I,
)
_INCIERTO = re.compile(
    r"\b(?:no\s+s[eé]|no\s+sabemos|desconozco|quiz[aá]s?|tal\s+vez|"
    r"podr[ií]a|posible|no\s+(?:he|hemos)\s+(?:comprobado|revisado|verificado))\b", re.I,
)


def polaridad_evento(texto: str, inicio: int, fin: int) -> str:
    """Devuelve afirmado/negado/desconocido para UNA aparición del evento.

    La negación de otra proposición nunca cancela esta aparición. Dentro de
    una lista nominal se hereda el alcance; un verbo independiente lo corta.
    """
    cortes = list(_CORTES.finditer(texto[:inicio]))
    base = cortes[-1].end() if cortes else 0
    for separador in _COORDINACION.finditer(texto, base, inicio):
        resto = texto[separador.end():fin]
        anterior = texto[base:separador.start()]
        componente_previo = re.search(r"\b(?:en|del|de\s+la)\s+(?:el\s+|la\s+)?\w+", anterior, re.I)
        if separador.group() == "," or componente_previo or _VERBO.search(resto) or re.match(r"\s*(?:el|la|los|las)\b", resto, re.I):
            base = separador.start() if separador.group().lower() == "ni" else separador.end()
    fragmento = texto[base:inicio]
    if _INCIERTO.search(fragmento) or "¿" in fragmento or "?" in texto[fin:].split(".")[0]:
        return "desconocido"
    negaciones = list(_NEGACION.finditer(fragmento))
    if negaciones:
        cola = fragmento[negaciones[-1].end():]
        verbos = list(_VERBO.finditer(cola))
        # Dos predicados indican que la negación pertenece al evento anterior.
        if len(verbos) <= 1:
            return "negado"
    if re.match(r"\s+(?:no\s+(?:existe|hay|est[aá]\s+presente)|descartad[oa])\b", texto[fin:], re.I):
        return "negado"
    return "afirmado"
