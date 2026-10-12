"""Extracción contextual de magnitudes físicas y mediciones cuantitativas automotrices."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from src.core.conversacion.respuestas_cortas.patrones_deteccion import PATRON_NUMERICO_MEDICION


def resolver_condicion_fragmento(frag: str) -> Optional[str]:
    """Determina la condición de operación automotriz descrita en un fragmento."""
    frag_l = frag.lower()
    if any(w in frag_l for w in ("con luces", "luces prendidas", "luces altas", "luces bajas", "prendo luces", "con carga")):
        return "con_carga_electrica"
    elif any(w in frag_l for w in ("arranque", "doy arranque", "al prender", "al dar contacto", "intentar prender", "intento prender", "al dar marcha", "doy marcha", "al arrancar", "al girar la llave", "dando marcha")):
        return "durante_arranque"
    elif any(w in frag_l for w in ("ralenti", "ralentí", "en marcha minima", "marcha lenta")):
        return "ralenti_carga"
    elif any(w in frag_l for w in ("reposo", "apagado", "motor apagado", "en frio", "en frío")):
        return "reposo"
    elif any(w in frag_l for w in ("contacto", "llave en on", "contacto puesto")):
        return "contacto_on"
    elif any(w in frag_l for w in ("acelerando", "al acelerar", "en marcha")):
        return "en_aceleracion"
    return None


def extraer_medicion(
    texto_l: str,
    intent_str: str,
    texto_preg: str,
    pending_q: Optional[Dict[str, Any]] = None,
) -> Optional[Tuple[float, str, Optional[str]]]:
    """Extrae valor, unidad y condición operacional de una respuesta técnica numérica sin mezclar magnitudes."""
    m = PATRON_NUMERICO_MEDICION.search(texto_l)
    if not m:
        return None
    val_str = m.group(1).replace(",", ".")
    try:
        val = float(val_str)
    except ValueError:
        return None

    unidad_raw = (m.group(2) or "").lower()
    if not unidad_raw:
        if any(w in texto_l for w in ("minuto", "minutos", "min", "hora", "horas", "segundo", "segundos")):
            return None
        if re.match(r"^(?:19[89]\d|20[0-2]\d)$", m.group(1)):
            return None
    if "psi" in unidad_raw:
        unidad = "PSI"
    elif "bar" in unidad_raw:
        unidad = "bar"
    elif "kpa" in unidad_raw:
        unidad = "kPa"
    elif "mv" in unidad_raw:
        unidad = "mV"
    elif "v" in unidad_raw or "volt" in unidad_raw:
        unidad = "V"
    elif "ma" in unidad_raw:
        unidad = "mA"
    elif "a" in unidad_raw or "amp" in unidad_raw:
        unidad = "A"
    elif "ohm" in unidad_raw or "Ω" in unidad_raw:
        unidad = "ohm"
    elif "°c" in unidad_raw or "c" == unidad_raw:
        unidad = "°C"
    elif "°f" in unidad_raw or "f" == unidad_raw:
        unidad = "°F"
    elif "rpm" in unidad_raw:
        unidad = "RPM"
    elif "km/h" in unidad_raw:
        unidad = "km/h"
    elif "%" in unidad_raw:
        unidad = "%"
    elif "mm" in unidad_raw:
        unidad = "mm"
    elif "ms" in unidad_raw:
        unidad = "ms"
    elif pending_q and pending_q.get("expected_units"):
        unidad = pending_q["expected_units"][0]
    elif "presion" in texto_preg or "manometro" in texto_preg or "combustible" in texto_preg:
        unidad = "PSI"
    elif "volt" in texto_preg or "multimetro" in texto_preg or "bateria" in texto_preg:
        unidad = "V"
    else:
        unidad = "unidades"

    condicion = resolver_condicion_fragmento(texto_l)
    return val, unidad, condicion


def extraer_medicion_fragmento(
    fragmento: str,
    intent_str: str,
    texto_preg: str,
    pending_q: Optional[Dict[str, Any]] = None,
) -> Optional[Tuple[float, str, Optional[str]]]:
    """Extrae lectura y unidad dentro de un fragmento de texto asignando su condición local."""
    m = PATRON_NUMERICO_MEDICION.search(fragmento)
    if not m:
        return None
    val_str = m.group(1).replace(",", ".")
    try:
        val = float(val_str)
    except ValueError:
        return None

    unidad_raw = (m.group(2) or "").lower()
    if not unidad_raw:
        if re.match(r"^(?:19[89]\d|20[0-2]\d)$", m.group(1)):
            return None
        if any(w in fragmento.lower() for w in ("minuto", "minutos", "min", "hora", "horas", "segundo")):
            return None

    if "psi" in unidad_raw:
        unidad = "PSI"
    elif "bar" in unidad_raw:
        unidad = "bar"
    elif "kpa" in unidad_raw:
        unidad = "kPa"
    elif "mv" in unidad_raw:
        unidad = "mV"
    elif "v" in unidad_raw or "volt" in unidad_raw:
        unidad = "V"
    elif "ma" in unidad_raw:
        unidad = "mA"
    elif "a" in unidad_raw or "amp" in unidad_raw:
        unidad = "A"
    elif "ohm" in unidad_raw or "Ω" in unidad_raw:
        unidad = "ohm"
    elif "°c" in unidad_raw or "c" == unidad_raw:
        unidad = "°C"
    elif "°f" in unidad_raw or "f" == unidad_raw:
        unidad = "°F"
    elif "rpm" in unidad_raw:
        unidad = "RPM"
    elif "km/h" in unidad_raw:
        unidad = "km/h"
    elif "%" in unidad_raw:
        unidad = "%"
    elif "mm" in unidad_raw:
        unidad = "mm"
    elif "ms" in unidad_raw:
        unidad = "ms"
    elif pending_q and pending_q.get("expected_units"):
        unidad = pending_q["expected_units"][0]
    elif "presion" in texto_preg or "manometro" in texto_preg or "combustible" in texto_preg:
        unidad = "PSI"
    elif "volt" in texto_preg or "multimetro" in texto_preg or "bateria" in texto_preg:
        unidad = "V"
    else:
        unidad = "unidades"

    condicion = resolver_condicion_fragmento(fragmento)
    return val, unidad, condicion


def extraer_todas_mediciones(
    texto_l: str,
    intent_str: str,
    texto_preg: str,
    pending_q: Optional[Dict[str, Any]] = None,
) -> List[Tuple[float, str, Optional[str]]]:
    """Extrae todas las mediciones cuantitativas identificando cláusulas y condiciones operativas."""
    clausulas = re.split(r'[,;]|\s+(?:y|pero|pero\s+con|mientras)\s+', texto_l, flags=re.IGNORECASE)
    resultados: List[Tuple[float, str, Optional[str]]] = []
    for c in clausulas:
        c_l = c.strip()
        if not c_l:
            continue
        if re.search(r"\b\d+\s*(?:minutos?|min|horas?|h|segundos?|seg)\b", c_l) and not re.search(
            r"\b\d+(?:[.,]\d+)?\s*(?:psi|bar|kpa|mv|v|volt|rpm)\b", c_l
        ):
            continue
        med = extraer_medicion_fragmento(c_l, intent_str, texto_preg, pending_q)
        if med:
            resultados.append(med)
    if not resultados:
        med_unica = extraer_medicion(texto_l, intent_str, texto_preg, pending_q)
        if med_unica:
            resultados.append(med_unica)
    return resultados
