"""Gobernanza de salida: evidencia reportada no equivale a una especificación OEM."""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Iterable

MAGNITUD = re.compile(
    r"(?<![\w.])(-?\d+(?:[.,]\d+)*(?:\s*(?:[–-]|a)\s*\d+(?:[.,]\d+)*)?)\s*\+?\s*"
    r"((?i:n[.\· ]?m|lb[- ]?ft|kgf[.\· ]?m|m?bar|psi|[km]?pa|mm|micras?|[µu]m|mv|v|"
    r"ohmios?|ohms?|Ω|ma|amp(?:erio)?s?|voltios?|volts?|°\s*c|grados\s*c|gramos?|ml|litros?|inHg|"
    r"min(?:utos?)?|segundos?|rpm)|A)(?!\w)"
)


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def magnitudes(texto):
    def valor_normalizado(valor):
        valor = valor.replace(",", ".").replace(" ", "")
        try:
            return str(Decimal(valor).normalize())
        except InvalidOperation:
            return valor

    return {
        (valor_normalizado(m[0]), re.sub(r"[.\·\s]", "", m[1].lower()))
        for m in MAGNITUD.findall(texto or "")
    }


def es_reporte_medicion(texto):
    t = normalizar(texto)
    return bool(
        magnitudes(texto)
        and not re.search(r"(?:\?|\bcual\b|\btolerancia\b|\bdeberia\b)", t)
        and re.search(
            r"\b(?:medi|medimos|mide|marca|marco|marcando|registro|registra|lectura|compresion es|obtuve|dio|da|tengo|tenemos|tiene|esta en|baja a|bajo a|cae a|cayo a|sube a|subio a|arroja|arrojando|tira|entrega|oscila|meti|alimente|aplique)\b",
            t,
        )
    )


def es_solicitud_especificacion(texto):
    t = normalizar(texto)
    return bool(
        re.search(
            r"\b(?:tolerancia|especificacion|torque|par de apriete|cual es el valor|a que temperatura|cuantos)\b",
            t,
        )
    )


def es_banner_seguridad_canonico(texto: str) -> bool:
    """Verifica si el texto corresponde estrictamente a una advertencia canónica autoritativa."""
    from src.core.diagnostico import banners_seguridad as bs

    texto_strip = (texto or "").strip()
    texto_strip = re.sub(r"^(?:Veh[ií]culo:[^\n]*\n+)+", "", texto_strip, flags=re.I).strip()
    banners = (
        bs.BANNER_DIESEL_ALTA_PRESION.strip(),
        bs.BANNER_BLOQUEO_REGENERACION_DILUCION.strip(),
        bs.PRERREQUISITOS_REGENERACION_DPF_OEM.strip(),
        bs.BANNER_BATERIA_MOTOR_ENCENDIDO.strip(),
        bs.BANNER_BATERIA_EXPLOSION.strip(),
        bs.BANNER_INCOMPATIBILIDAD_24V_12V.strip(),
        bs.BANNER_INCOMPATIBILIDAD_BUJIAS_DIESEL.strip(),
        bs.BANNER_TURBO_INCENDIO.strip(),
        bs.BANNER_TEMPERATURA.strip(),
        bs.BANNER_HV.strip(),
        bs.BANNER_COMBUSTIBLE.strip(),
        bs.BANNER_DIESEL_EMBALAMIENTO.strip(),
        bs.BANNER_FRENO.strip(),
        bs.BANNER_FRENO_ESTACIONAMIENTO_RODANDO.strip(),
        bs.BANNER_ACEITE.strip(),
        bs.BANNER_ACEITE_DETENCION_INMEDIATA.strip(),
        bs.BANNER_DIRECCION_CRITICA.strip(),
    )
    for b in banners:
        if texto_strip == b or texto_strip.startswith(b):
            return True
    return False


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


def es_mandato_intervencion(texto):
    """Una cifra observada tampoco autoriza ajustar o sustituir una pieza."""
    for coincidencia in re.finditer(
        r"\b(?:apriet[ae](?=\s+(?:el|la|los|las|a|\d)\b)|rectifi(?:ca|que)|sustituy[ae]|reemplaz[ae]|"
        r"(?:calibr[ae]|ajust[ae])(?=\s+(?:el|la|los|las|a)\b)|"
        r"debe\s+(?:cambiarse|reemplazarse|rectificarse|sustituirse))\b",
        texto,
    ):
        prefijo = texto[max(0, coincidencia.start() - 30) : coincidencia.start()]
        if not re.search(r"\b(?:no|nunca)\s+(?:\w+\s+){0,2}$", prefijo):
            return True
    return False


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
    seguridad arbitrario nunca concede autorización. La confianza devuelta es un límite de
    política y no una predicción SVM.
    """
    if corpus_validado and especificacion_autorizada:
        return respuesta_propuesta, 1.0, False

    # Los banners canónicos autoritativos de seguridad física no se censuran
    if es_banner_seguridad_canonico(respuesta_propuesta):
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
    normativa = es_mandato_intervencion(texto) or bool(
        re.search(
            r"\b(?:tolerancia (?:es|oem|admisible)|maximo admisible|minimo permitido|debe medir|"
            r"no debe superar|valor aceptable no debe superar|"
            r"debe (?:ser|estar|abrir)|valor nominal|exige rectificado|requiere (?:cambio|rectificado)|"
            r"fuera de tolerancia|termostato trabado|ajust[ae] (?:a|el)|calibr[ae] (?:a|el))\b",
            texto,
        )
    )

    # La herramienta o un encabezado de seguridad arbitrario no acreditan ninguna cifra.
    propuestas_no_estandar = propuestas

    if (
        consulta_sin_respuesta
        or (propuestas_no_estandar and (not propuestas_no_estandar.issubset(observadas) or normativa))
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
        partes = re.split(r"(?<=[!?])\s+|(?<=[a-zA-Z\)])\.\s+|\n+", respuesta_propuesta)
        conservadas = []
        for parte in partes:
            n = normalizar(parte)
            cifras = magnitudes(parte)
            if cifras and not cifras.issubset(observadas):
                continue
            if es_mandato_intervencion(n):
                continue
            if re.search(
                r"\b(?:la tolerancia|maximo admisible|minimo permitido|debe medir|debe ser|"
                r"no debe superar|valor aceptable no debe superar|"
                r"valor nominal|exige rectificado|requiere (?:cambio|rectificado)|fuera de tolerancia|"
                r"termostato trabado|ajust[ae] (?:a|el)|calibr[ae] (?:a|el))\b",
                n,
            ):
                continue
            if parte.strip():
                conservadas.append(parte)
        # Una consulta de cifras debe abstenerse. En seguimiento clínico se conserva
        # la pregunta orientativa si no contiene cifras ni órdenes normativas.
        if conservadas and not es_solicitud_especificacion(consulta_usuario):
            cuerpo = " ".join(conservadas).strip()
            # La prohibición persiste aunque conservemos una pregunta orientativa.
            return f"{aviso}\n\nOrientación preliminar:\n{cuerpo}", 0.0, True
        return aviso, 0.0, True

    return respuesta_propuesta, 1.0, False
