"""Gobernanza de salida: evidencia reportada no equivale a una especificación OEM."""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable

MAGNITUD = re.compile(
    r"(?<![\w.])(-?\d+(?:[.,]\d+)*(?:\s*(?:[-–]|a)\s*\d+(?:[.,]\d+)*)?)\s*\+?\s*"
    r"(n[.· ]?m|lb[- ]?ft|kgf[.·]?m|m?bar|psi|[km]?pa|mm|micras?|[µu]m|mv|v|"
    r"ohmios?|ohms?|ma|amperios|°\s*c|grados\s*c|gramos?|litros?|minutos?|segundos?|rpm)\b",
    re.I,
)


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def magnitudes(texto):
    return {
        (m[0].replace(",", ".").replace(" ", ""), re.sub(r"[.·\s]", "", m[1].lower()))
        for m in MAGNITUD.findall(texto or "")
    }


def es_reporte_medicion(texto):
    t = normalizar(texto)
    return bool(
        magnitudes(texto)
        and not re.search(r"(?:\?|\bcual\b|\btolerancia\b|\bdeberia\b)", t)
        and re.search(r"\b(?:medi|medimos|mide|marca|marco|registro|lectura|compresion es|obtuve|dio)\b", t)
    )


def es_solicitud_especificacion(texto):
    t = normalizar(texto)
    return bool(
        re.search(
            r"\b(?:tolerancia|especificacion|torque|par de apriete|cual es el valor|a que temperatura|cuantos)\b",
            t,
        )
    )


def limpiar_advertencia(texto):
    """Conserva la prohibición específica; elimina cifras y órdenes normativas.

    No otorga permiso por un encabezado. El mismo control documental ya decidió
    que la salida necesitaba intervención antes de aplicar esta redacción.
    """
    partes = re.split(r"(?<=[.!?])\s+|\n", texto)
    seguras = []
    for parte in partes:
        n = normalizar(parte)
        if re.search(r"\b(?:tolerancia es|la tolerancia|exige rectificado|requiere cambio|debe medir)\b", n):
            continue
        seguras.append(MAGNITUD.sub("[cifra no autorizada]", parte))
    return "\n".join(seguras)


def proteger_salida_conversacional(
    respuesta_propuesta: str,
    vehiculo_str: str,
    consulta_usuario: str,
    corpus_validado: bool = False,
    especificacion_autorizada: bool = False,
    mediciones_reportadas: Iterable[str] = (),
):
    """Cifras observadas se permiten solo sin inferir límites ni ordenar intervención.

    La autorización documental requiere ambos controles; un marcador textual de
    seguridad nunca concede autorización. La confianza devuelta es un límite de
    política y no una predicción SVM.
    """
    if corpus_validado and especificacion_autorizada:
        return respuesta_propuesta, 1.0, False
    fuentes = [t for t in mediciones_reportadas if es_reporte_medicion(t)]
    if es_reporte_medicion(consulta_usuario):
        fuentes.append(consulta_usuario)
    observadas = set().union(*(magnitudes(t) for t in fuentes)) if fuentes else set()
    propuestas = magnitudes(respuesta_propuesta)
    texto = normalizar(respuesta_propuesta)
    consulta_sin_respuesta = not respuesta_propuesta.strip() and re.search(
        r"\b(?:tolerancia|alabeo|torque|apriete|especificacion|apertura|calibracion)\b",
        normalizar(consulta_usuario),
    )
    normativa = bool(
        re.search(
            r"\b(?:tolerancia (?:es|oem|admisible)|maximo admisible|minimo permitido|debe medir|"
            r"debe (?:ser|estar|abrir)|valor nominal|exige rectificado|requiere (?:cambio|rectificado)|"
            r"fuera de tolerancia|termostato trabado|ajust[ae] (?:a|el)|calibr[ae] (?:a|el))\b",
            texto,
        )
    )
    if (
        consulta_sin_respuesta
        or (propuestas and (not propuestas.issubset(observadas) or normativa))
        or normativa
    ):
        aviso = (
            "Aviso de control metrológico CarBot: No dispongo de documentación OEM validada para emitir esa especificación "
            f"de {vehiculo_str.strip() or 'este vehículo'}. No autoriza rectificado, "
            "reemplazo ni ajuste a partir de límites no verificados. Confirma componente, "
            "motor y mercado y consulta la página aplicable del manual oficial. "
            "(corpus_validado=False)."
        )
        # Reconocer la evidencia preservada sin convertirla en criterio normativo.
        if fuentes:
            aviso += "\nMediciones reportadas por el mecánico (sin validar contra límites OEM): " + "; ".join(
                fuentes
            )
        partes = re.split(r"(?<=[.!?])\s+|\n", respuesta_propuesta)
        conservadas = []
        for parte in partes:
            n = normalizar(parte)
            cifras = magnitudes(parte)
            if cifras and not cifras.issubset(observadas):
                continue
            if re.search(
                r"\b(?:la tolerancia|maximo admisible|minimo permitido|debe medir|debe ser|"
                r"valor nominal|exige rectificado|requiere (?:cambio|rectificado)|fuera de tolerancia|"
                r"termostato trabado|ajust[ae] (?:a|el)|calibr[ae] (?:a|el))\b",
                n,
            ):
                continue
            if parte.strip():
                conservadas.append(parte)
        # Una consulta de cifras debe abstenerse. En seguimiento clínico se conserva
        # la pregunta/Plan B/hipótesis cualitativa que no depende de la cifra retirada.
        if conservadas and not es_solicitud_especificacion(consulta_usuario):
            aviso = "\n".join(conservadas) + "\n" + aviso
        return aviso, 0.0, True
    return respuesta_propuesta, 1.0, False
