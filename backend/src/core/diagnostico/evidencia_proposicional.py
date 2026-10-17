"""Alcance de evidencia declarada; una mención nunca acredita una inspección."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


def normalizar(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto.lower())
        if not unicodedata.combining(c)
    )


@dataclass(frozen=True)
class Proposicion:
    texto: str
    estado: str  # AFIRMADO, NEGADO, HISTORICO, NO_COMPROBADO


def analizar_proposiciones(texto: str) -> list[Proposicion]:
    """Divide conectores y conserva el alcance de «ni» bajo una negación.

    «No arranca/no comunica/sin chispa» describen anomalías, no ausencia de falla.
    «No hay falla», «no presenta» y «sin problemas» niegan la proposición.
    """
    partes = re.split(r"([.;!?\n]|,(?!\d)|\bpero\b|\baunque\b|\bademas\b|\by\b|\bni\b)", texto, flags=re.I)
    resultado = []
    hereda_negacion = False
    conector = ""
    for parte in partes:
        original = parte.strip()
        parte = normalizar(original)
        if not parte:
            continue
        if re.fullmatch(r"[.;!?\n,]|pero|aunque|ademas|y|ni", parte):
            conector = parte
            continue
        negado = bool(re.search(
            r"\b(?:no\s+(?:hay|tengo|tiene|presenta|presento|existe|es|ocurre|detecte|observe)|"
            r"sin\s+(?:fallas?|problemas?|misfire|vibraciones?|ruidos?|fugas?)|descartad[oa])\b", parte
        )) or (conector == "ni" and hereda_negacion)
        pendiente = bool(re.search(
            r"\b(?:no\s+(?:se\s+(?:si|que|como)|puedo|pude|comprobe|medi|revise)|sin\s+(?:medir|comprobar)|"
            r"pendiente|supuest[oa]|quizas|tal\s+vez)\b", parte
        ))
        pendiente = pendiente or parte == "no se"
        historico = bool(re.search(
            r"\b(?:antecedente|antes|anteriormente|reemplaz\w*|cambie|cambiaron|nuev[oa]s?)\b", parte
        ))
        if historico and re.search(r"\b(?:ahora|desde entonces|error|codificacion|no arranca|no enciende|no comunica)\b", parte):
            historico = False  # relación temporal con una anomalía vigente, no pieza confirmada
        estado = "NEGADO" if negado else "NO_COMPROBADO" if pendiente else "HISTORICO" if historico else "AFIRMADO"
        resultado.append(Proposicion(original, estado))
        hereda_negacion = negado
        conector = ""
    return resultado


def evidencia_afirmada(texto: str) -> str:
    proposiciones = analizar_proposiciones(texto)
    if all(p.estado == "AFIRMADO" for p in proposiciones):
        return texto
    return ". ".join(p.texto for p in proposiciones if p.estado == "AFIRMADO")


def excluir_hipotesis_negadas(texto: str, predicciones: list) -> list:
    """Excluye solamente eventos explícitamente negados, no piezas reemplazadas."""
    negadas = " ".join(normalizar(p.texto) for p in analizar_proposiciones(texto) if p.estado == "NEGADO")
    eventos = (
        (r"\b(?:ect|sensor de temperatura)\b", r"\b(?:ect|sensor de temperatura)\b"),
        (r"\bmisfire\b", r"\bmisfire\b"),
        (r"\bmaf\b", r"\bmaf\b"),
        (r"\btps\b", r"\btps\b"),
        (r"\b(?:ckp|cmp)\b", r"\b(?:ckp|cmp)\b"),
        (r"\bcommon rail\b", r"\bcommon rail\b"),
    )
    patrones = [falla for evento, falla in eventos if re.search(evento, negadas)]
    return [p for p in predicciones if not any(re.search(pat, normalizar(p.falla)) for pat in patrones)]
