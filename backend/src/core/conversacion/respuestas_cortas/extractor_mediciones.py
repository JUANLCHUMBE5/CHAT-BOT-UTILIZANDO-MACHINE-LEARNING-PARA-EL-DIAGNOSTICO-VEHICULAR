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


def normalizar_unidad_automotriz(unidad_raw: str) -> Optional[str]:
    """Estandariza unidades de medida de taller a su convención técnica formal."""
    u = unidad_raw.lower().strip()
    if not u:
        return None
    if "psi" in u:
        return "PSI"
    if "mbar" in u:
        return "mbar"
    if "bar" in u:
        return "bar"
    if "kpa" in u:
        return "kPa"
    if "inhg" in u or "in hg" in u or '"hg' in u:
        return "inHg"
    if "°c" in u or u == "c" or "celsius" in u or "centigr" in u or "centígr" in u or u.startswith("grado"):
        return "°C"
    if "°f" in u or u == "f" or "fahrenheit" in u:
        return "°F"
    if "mv" in u:
        return "mV"
    if "ma" in u or "miliamperio" in u:
        return "mA"
    if "v" in u or "volt" in u:
        return "V"
    if u == "a" or "amp" in u:
        return "A"
    if "kohm" in u:
        return "kohm"
    if "ohm" in u or "ω" in u or "Ω" in unidad_raw:
        return "ohm"
    if "rpm" in u:
        return "RPM"
    if "km/h" in u:
        return "km/h"
    if "%" in u:
        return "%"
    if "mm" in u:
        return "mm"
    if "ml" in u or "cm3" in u or "cc" in u:
        return "ml"
    if "g/s" in u:
        return "g/s"
    if "nm" in u:
        return "Nm"
    if "ms" in u:
        return "ms"
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

    unidad_norm = normalizar_unidad_automotriz(unidad_raw)
    if unidad_norm:
        unidad = unidad_norm
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
    mejor_match = None
    for m in PATRON_NUMERICO_MEDICION.finditer(fragmento):
        u_raw = (m.group(2) or "").lower()
        u_norm = normalizar_unidad_automotriz(u_raw)
        if u_norm:
            mejor_match = (m, u_norm)
            break

    if mejor_match:
        m, unidad = mejor_match
        val_str = m.group(1).replace(",", ".")
        try:
            val = float(val_str)
        except ValueError:
            return None
    else:
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

        unidad_norm = normalizar_unidad_automotriz(unidad_raw)
        if unidad_norm:
            unidad = unidad_norm
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
    resultados: List[Tuple[float, str, Optional[str]]] = []

    # 1. Evaluar por cláusulas para respetar la condición operativa local
    clausulas = re.split(r'[,;]|\s+(?:y|pero|pero\s+con|mientras)\s+', texto_l, flags=re.IGNORECASE)
    for c in clausulas:
        c_l = c.strip()
        if not c_l:
            continue
        if re.search(r"\b\d+\s*(?:minutos?|min|horas?|h|segundos?|seg)\b", c_l) and not re.search(
            r"\b\d+(?:[.,]\d+)?\s*(?:psi|bar|kpa|mbar|inhg|mv|v|volt|ma|a|ohm|rpm|mm|ml|g/s)\b", c_l
        ):
            continue
        explicitas = []
        for coincidencia in PATRON_NUMERICO_MEDICION.finditer(c_l):
            unidad = normalizar_unidad_automotriz(coincidencia.group(2) or "")
            if not unidad:
                continue
            try:
                valor = float(coincidencia.group(1).replace(",", "."))
            except ValueError:
                continue
            explicitas.append((valor, unidad, resolver_condicion_fragmento(c_l)))
        if explicitas:
            resultados.extend(explicitas)
            continue
        med = extraer_medicion_fragmento(c_l, intent_str, texto_preg, pending_q)
        if med and med[1] != "unidades":
            resultados.append(med)

    if resultados:
        return resultados

    # 2. Si no hubo por cláusulas, búsqueda exhaustiva directa con unidades explícitas
    for m in PATRON_NUMERICO_MEDICION.finditer(texto_l):
        val_str = m.group(1).replace(",", ".")
        try:
            val = float(val_str)
        except ValueError:
            continue
        unit_raw = (m.group(2) or "").lower()
        if not unit_raw:
            continue
        unit_norm = normalizar_unidad_automotriz(unit_raw)
        if unit_norm:
            cond = resolver_condicion_fragmento(texto_l)
            resultados.append((val, unit_norm, cond))

    if not resultados:
        med_unica = extraer_medicion(texto_l, intent_str, texto_preg, pending_q)
        if med_unica:
            resultados.append(med_unica)
    return resultados
