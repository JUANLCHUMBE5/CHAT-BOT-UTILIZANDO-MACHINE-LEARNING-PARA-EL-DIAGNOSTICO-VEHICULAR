"""Enrutamiento temático conservador para limitar ruido entre subsistemas."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Any


def _normalizar(texto: str) -> str:
    normalizado = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", str(texto or "").lower())
        if unicodedata.category(caracter) != "Mn"
    )
    # Correcciones conservadoras de errores frecuentes que cambian el ruteo.
    normalizado = re.sub(r"\bmescla\b", "mezcla", normalizado)
    normalizado = re.sub(r"\brecalntar\b", "recalentar", normalizado)
    return normalizado


_REGLAS: dict[str, tuple[str, ...]] = {
    "INYECCION_MEZCLA": (
        r"\binyector(?:es)?\b", r"\binyeccion\b", r"\bmezcla\s+pobre\b",
        r"\bmezcla\s+rica\b", r"\bsensor\s+(?:de\s+)?oxigeno\b",
        r"\bsonda\s+lambda\b", r"\bsensor\s+lambda\b", r"\b(?:p0171|p0172)\b",
        r"\b(?:stft|ltft|fuel\s+trim)\b", r"\briel\s+de\s+combustible\b",
    ),
    "ADMISION_MAP": (
        r"\bsensor\s+map\b", r"\bcarga\s+absoluta\b", r"\bpresion\s+(?:del\s+)?multiple\b",
        r"\bmap\b", r"\bmaf\b", r"\b(?:p0105|p0106|p0107|p0108|p0109)\b",
    ),
    "RALENTI": (
        r"\bralenti\b", r"\bmarcha\s+minima\b", r"\bminimo\b", r"\biac\b",
        r"\bcuerpo\s+de\s+aceleracion\b", r"\bmariposa\b",
    ),
    "REFRIGERACION": (
        r"\brefrigeracion\b",
        r"\brecalienta\w*\b", r"\brecalent\w*\b", r"\bsobrecalienta\w*\b",
        r"\btemperatura\s+(?:del\s+)?motor\b", r"\btemperatura\s+(?:sube|alta|elevada)\b",
        r"\b(?:calienta|se\s+calienta)\b",
        r"\btermostato\b", r"\bradiador\b", r"\bmotoventilador\b", r"\brefrigerante\b",
    ),
    "ENCENDIDO": (
        r"\bbujias?\b", r"\bbobinas?\b", r"\bsin\s+chispa\b", r"\bmisfire\b",
        r"\b(?:el\s+)?motor\s+(?:tiembla|vibra|ratea)\b",
        r"\b(?:tiembla|vibra|ratea)\b.{0,35}\b\d{2,4}\s*rpm\b",
        r"\b\d{2,4}\s*rpm\b.{0,35}\b(?:tiembla|vibra|ratea)\b",
        r"\bminimo\s+bajo\b.{0,30}\bse\s+apaga\b",
        r"\b(?:p030[0-9])\b",
    ),
    "FRENOS": (
        r"\bruido\s+(?:al|cuando)\s+frenar\b", r"\b(?:frena|frenado)\b",
        r"\bpedal\s+de\s+freno\b", r"\bdisco(?:s)?\s+de\s+freno\b",
        r"\bpastillas?\s+(?:de\s+)?freno\b", r"\babs\b",
    ),
    "TRANSMISION": (
        r"\b(?:patina|patinando)\s+(?:el\s+)?embrague\b", r"\bembrague\s+patina\b",
        r"\btransmision\b", r"\bcaja\s+(?:de\s+)?cambios\b", r"\bno\s+entran\s+los\s+cambios\b",
    ),
    "SUSPENSION_DIRECCION": (
        r"\bse\s+inclina\s+en\s+(?:las\s+)?curvas\b", r"\b(?:golpeteo|rebota)\s+en\s+(?:baches|huecos)\b",
        r"\bdesbalanceo\b", r"\balineacion\b", r"\brotula(?:s)?\b", r"\bamortiguador(?:es)?\b",
        r"\b(?:timon|volante)\s+vibra\b.{0,35}\b(?:\d{2,3}\s*km/?h|velocidad)\b",
    ),
    "ELECTRICO_ECU": (
        r"\balternador\b", r"\bbateria\s+(?:se\s+)?descarga\w*\b",
        r"\b(?:ecu|computadora)\s+(?:incompatible|de\s+otra\s+version|no\s+comunica)\b",
        r"\b(?:cambie|cambio|cambiar|cambiaron|reemplazaron|reemplazo)\s+(?:la\s+)?(?:ecu|computadora)\b",
        r"\b(?:error|falla)\s+(?:de\s+)?codificacion\b",
        r"\bperdida\s+de\s+comunicacion\b", r"\bred\s+can\b", r"\bcorto\s+electrico\b",
    ),
}

_TERMINOS_DOCUMENTO: dict[str, tuple[str, ...]] = {
    "INYECCION_MEZCLA": (
        "inyector", "inyeccion", "mezcla pobre", "mezcla rica", "oxigeno", "lambda",
        "fuel trim", "stft", "ltft", "p0171", "p0172", "presion de combustible",
    ),
    "ADMISION_MAP": (
        "sensor map", "presion map", "carga absoluta", "presion del multiple", "p0106",
        "sensor maf", "flujo de aire", "admision",
    ),
    "RALENTI": ("ralenti", "marcha minima", "minimo", "valvula iac", "cuerpo de aceleracion", "mariposa"),
    "REFRIGERACION": (
        "refrigeracion", "recalent", "refrigerante", "radiador", "termostato", "motoventilador",
    ),
    "ENCENDIDO": ("bujia", "bobina", "chispa", "misfire", "p030"),
    "FRENOS": ("freno", "pastilla", "disco", "abs", "frenar"),
    "TRANSMISION": ("embrague", "transmision", "caja de cambios", "sincronizador"),
    "SUSPENSION_DIRECCION": (
        "suspension", "direccion", "amortiguador", "rotula", "desbalanceo", "alineacion", "bache",
    ),
    "ELECTRICO_ECU": ("ecu", "computadora", "red can", "corto electrico", "comunicacion electrica", "alternador", "bateria"),
}
ETIQUETAS_AREA = {
    "INYECCION_MEZCLA": "inyección / mezcla",
    "ADMISION_MAP": "admisión / sensor MAP-MAF",
    "RALENTI": "ralentí",
    "REFRIGERACION": "refrigeración",
    "ENCENDIDO": "encendido",
    "FRENOS": "frenos",
    "TRANSMISION": "transmisión",
    "SUSPENSION_DIRECCION": "suspensión / dirección",
    "ELECTRICO_ECU": "eléctrico / ECU",
}

_ETIQUETA_A_SISTEMA = {
    "INYECCION_MEZCLA": "combustible_admision",
    "ADMISION_MAP": "combustible_admision",
    "RALENTI": "combustible_admision",
    "REFRIGERACION": "refrigeracion",
    "ENCENDIDO": "encendido",
    "FRENOS": "frenos",
    "TRANSMISION": "transmision",
    "SUSPENSION_DIRECCION": "suspension_direccion",
    "ELECTRICO_ECU": "electrico_ecu",
}

_ALIAS_SISTEMA_A_AREA = {
    "refrigeracion": "REFRIGERACION",
    "combustible_admision": "INYECCION_MEZCLA",
    "encendido": "ENCENDIDO",
    "frenos": "FRENOS",
    "transmision": "TRANSMISION",
    "suspension_direccion": "SUSPENSION_DIRECCION",
    "electrico_ecu": "ELECTRICO_ECU",
}

_MARCADORES_CAUSA = {
    "refrigeracion": ("refriger", "radiador", "termostato", "ventilador", "bomba de agua", "refrigerante", "ect"),
    "combustible_admision": (
        "inyector", "inyeccion", "mezcla", "maf", "map", "oxigeno", "lambda", "o2",
        "combustible", "presion de combustible", "fuga de vacio", "admisión", "admision",
    ),
    "encendido": ("bujia", "bujía", "bobina", "chispa", "misfire", "encendido", "cilindro"),
    "frenos": ("freno", "pastilla", "disco", "abs", "liquido de freno"),
    "transmision": ("embrague", "transmision", "transmisión", "caja", "sincronizador", "collarin"),
    "suspension_direccion": ("suspension", "suspensión", "direccion", "dirección", "llanta", "alineacion", "rotula", "amortiguador"),
    "electrico_ecu": ("ecu", "computadora", "corto", "can", "cableado", "masa electrica", "eléctrica", "alternador", "bateria", "bornes"),
}

_CAUSAS_PROHIBIDAS = {
    "refrigeracion": ("oxigeno", "o2", "lambda", "mezcla", "llanta", "embrague", "bujia", "bobina", "inyector", "maf", "freno"),
    "combustible_admision": ("radiador", "termostato", "ventilador", "llanta", "embrague", "pastilla", "amortiguador"),
    "encendido": ("radiador", "termostato", "llanta", "embrague", "pastilla", "amortiguador"),
    "frenos": ("inyector", "sensor o2", "radiador", "embrague", "amortiguador"),
    "transmision": ("inyector", "sensor o2", "radiador", "pastilla", "amortiguador"),
    "suspension_direccion": ("inyector", "sensor o2", "radiador", "pastilla", "embrague"),
    "electrico_ecu": ("llanta", "pastilla", "radiador", "embrague"),
}

# Un vehículo con motor de combustión no debe recibir hipótesis de tracción
# eléctrica cuando el hilo activo es de refrigeración. No bloquear "ventilador
# eléctrico" genéricamente: puede ser un componente legítimo del radiador.
_CAUSAS_EV = (
    "bateria", "bateria de traccion", "bateria de alto voltaje", "inversor",
    "hibrido", "alto voltaje", "high voltage", "vehiculo electrico",
    "motor electrico", "sistema electrico de traccion", "propulsion electrica",
)


@lru_cache(maxsize=1)
def _cargar_modelo_ruteo_candidato() -> Any | None:
    """Carga el SVM de ruteo experimental sin afectar el SVM principal de fallas."""
    from src.config import ML_ROOT

    ruta = (
        ML_ROOT
        / "experiments"
        / "ruteo_sistemas_20261005"
        / "modelo_ruteo_candidato.joblib"
    )
    if not ruta.is_file():
        return None
    try:
        import joblib

        return joblib.load(ruta)
    except Exception:
        return None


def _predecir_sistema_con_modelo(texto: str) -> str | None:
    """Usa el candidato TF-IDF/LinearSVC solo cuando supera un margen conservador."""
    modelo = _cargar_modelo_ruteo_candidato()
    if modelo is None:
        return None
    try:
        puntajes = modelo.decision_function([texto])[0]
        ordenados = sorted((float(puntaje) for puntaje in puntajes), reverse=True)
        if len(ordenados) < 2 or ordenados[0] - ordenados[1] < 1.0:
            return None
        return str(modelo.predict([texto])[0])
    except Exception:
        return None


def detectar_sistema_ruteo(texto: str, usar_modelo: bool = True) -> str | None:
    """Clasifica la frase para ruteo conversacional; RPM aisladas quedan ambiguas."""
    normalizado = _normalizar(texto)
    if re.search(r"\bno\s+tiembla\b", normalizado) and re.search(
        r"\b(?:minimo\s+bajo|ralenti\s+bajo|\d{2,4}\s*rpm)\b", normalizado
    ) and not re.search(r"\b(?:misfire|ratea|cabecea|vibra)\b", normalizado):
        return "ambiguo"
    # Una aclaración de que no tiembla/falla al frenar niega ese indicio;
    # la vibración del timón a velocidad corresponde a chasis/dirección.
    if re.search(
        r"\b(?:al\s+frenar\s+no\s+(?:tiembla|vibra|hace\s+ruido)|"
        r"no\s+(?:tiembla|vibra|hace\s+ruido)\s+al\s+frenar)\b",
        normalizado,
    ):
        normalizado = re.sub(r"\bfrenar\b", "", normalizado)
    # Regla determinista previa al SVM: temblor/misfire junto con ralentí bajo
    # es una ruta de encendido aunque ambas señales estén separadas en la frase.
    texto_sin_negaciones_de_irregularidad = re.sub(
        r"\bno\s+(?:tiembla|tiemblo|vibra|vibro|ratea|cabecea|sacude)\b",
        " ",
        normalizado,
    )
    tiene_irregularidad = bool(
        re.search(
            r"\b(?:tiembla|temblor|vibraci[oó]n|misfire|cabecea|sacude|vibra|ratea)\b",
            texto_sin_negaciones_de_irregularidad,
        )
    )
    tiene_ralenti_bajo = bool(
        re.search(r"\b(?:\d{2,4}\s*rpm|500\s*rpm|m[ií]nimo|ralent[ií])\b", normalizado)
    )
    tiene_area_mas_especifica = bool(
        re.search(
            r"\b(?:sensor\s+map|carga\s+absoluta|\bmap\b|\bmaf\b|inyector(?:es)?|"
            r"mezcla\s+(?:pobre|rica)|sensor\s+(?:de\s+)?ox[ií]geno|\bp0(?:171|172)\b|"
            r"recalienta\w*|refrigeraci[oó]n|termostato|radiador)\b",
            normalizado,
        )
    )
    if tiene_irregularidad and tiene_ralenti_bajo and not tiene_area_mas_especifica:
        return "encendido"
    if re.search(r"\b(?:500\s*rpm|ralenti\s+bajo|minimo\s+bajo)\b", normalizado) and not tiene_irregularidad:
        return "ambiguo"
    # Corrección explícita, aunque el sistema elegido no tenga otro síntoma en la frase.
    if re.search(r"\b(?:es|sera|seria|trata\s+de)\s+(?:refrigeracion|sistema\s+de\s+refrigeracion)\b", normalizado) and not re.search(
        r"\bno\s+(?:es|sera|seria)\s+(?:refrigeracion|sistema\s+de\s+refrigeracion)\b",
        normalizado,
    ):
        return "refrigeracion"
    detectadas = [
        area for area, patrones in _REGLAS.items()
        if any(re.search(patron, normalizado) for patron in patrones)
    ]
    if not detectadas:
        return _predecir_sistema_con_modelo(texto) if usar_modelo else None
    # Evitar interpretar una negación como evidencia positiva del sistema negado.
    filtradas = []
    for area in detectadas:
        patrones = _REGLAS[area]
        negada = any(
            re.search(r"\bno\s+(?:es\s+)?(?:de\s+)?" + patron.removeprefix(r"\b").removesuffix(r"\b"), normalizado)
            for patron in patrones
        )
        if not negada:
            filtradas.append(area)
    if not filtradas:
        return "ambiguo"
    # En frases con más de un indicio, la señal causal explícita gana sobre síntomas secundarios.
    for area in ("REFRIGERACION", "INYECCION_MEZCLA", "ADMISION_MAP", "ENCENDIDO", "FRENOS", "TRANSMISION", "SUSPENSION_DIRECCION", "ELECTRICO_ECU", "RALENTI"):
        if area in filtradas:
            return _ETIQUETA_A_SISTEMA[area]
    return "ambiguo"


def resolver_sistema_activo(texto_actual: str, sistema_activo: str | None = None) -> str | None:
    """Actualiza sistema activo con la señal del turno; conserva memoria en respuestas neutrales."""
    detectado = detectar_sistema_ruteo(texto_actual, usar_modelo=not sistema_activo)
    normalizado = _normalizar(texto_actual)
    if detectado == "ambiguo":
        niega_mezcla = any(
            token in normalizado
            for token in ("no es de mezcla", "no es mezcla", "no es inyeccion")
        )
        if niega_mezcla and sistema_activo == "refrigeracion":
            return sistema_activo
        contradice_activo = any(
            token in normalizado
            for token in ("no es de mezcla", "no es mezcla", "no es inyeccion", "descarta refrigeracion", "no es refrigeracion")
        )
        if sistema_activo and not contradice_activo:
            return sistema_activo
        return "ambiguo"
    # "Detenido en ralentí" solo aporta condición de operación; no debe borrar
    # un diagnóstico activo de encendido cuando el hilo ya detectó misfire.
    if (
        sistema_activo == "encendido"
        and detectado == "combustible_admision"
        and detectar_areas_tecnicas(texto_actual) == ["RALENTI"]
    ):
        return sistema_activo
    if detectado:
        return detectado
    if sistema_activo and any(token in normalizado for token in (
        "no es de mezcla", "no es mezcla", "no es inyeccion", "descarta refrigeracion", "no es refrigeracion"
    )):
        return "ambiguo"
    return sistema_activo


def areas_para_sistema(sistema: str | None, texto: str = "") -> list[str]:
    """Convierte la memoria de sistema en la etiqueta compatible con los filtros actuales."""
    sistema_normalizado = str(sistema or "").lower()
    areas_texto = detectar_areas_tecnicas(texto) if texto else []
    compatibles = [
        area for area in areas_texto
        if _ETIQUETA_A_SISTEMA.get(area) == sistema_normalizado
    ]
    if compatibles:
        if "ADMISION_MAP" in compatibles:
            return ["ADMISION_MAP"]
        no_genericas = [area for area in compatibles if area != "RALENTI"]
        return [no_genericas[0] if no_genericas else compatibles[0]]
    area = _ALIAS_SISTEMA_A_AREA.get(sistema_normalizado)
    return [area] if area else []


def filtrar_causas(sistema_activo: str | None, causas_propuestas: list[Any], evidencia: str = "") -> list[Any]:
    """Filtra hipótesis incompatibles con el sistema activo sin inventar reemplazos."""
    sistema = str(sistema_activo or "").lower()
    marcadores = _MARCADORES_CAUSA.get(sistema)
    if not marcadores:
        return []
    evidencia_normalizada = _normalizar(evidencia)
    bloqueos = list(_CAUSAS_PROHIBIDAS.get(sistema, ()))
    if sistema == "refrigeracion":
        bloqueos.extend(_CAUSAS_EV)
        # Humo blanco junto con consumo de refrigerante respalda investigar
        # estanqueidad de culata; no habilitar esa rama por temperatura sola.
        if "humo blanco" in evidencia_normalizada and "refrigerante" in evidencia_normalizada:
            marcadores = (*marcadores, "culata", "junta")
    if sistema == "combustible_admision" and re.search(r"\binyectores?\s+no\s+inyectan?\b", evidencia_normalizada):
        bloqueos.extend(("iac", "cuerpo de aceleracion"))
    resultado = []
    for causa in causas_propuestas:
        texto = str(causa.get("falla", "") if isinstance(causa, dict) else getattr(causa, "falla", causa))
        normalizado = _normalizar(texto)
        if any(token in normalizado for token in bloqueos):
            continue
        if any(token in normalizado for token in marcadores):
            resultado.append(causa)
    return resultado


def respuesta_menciona_causa_fuera_de_sistema(
    sistema_activo: str | None,
    respuesta: str,
    evidencia: str = "",
) -> bool:
    """Guard simple para no entregar al usuario una causa explícitamente prohibida."""
    sistema = str(sistema_activo or "").lower()
    bloqueos = list(_CAUSAS_PROHIBIDAS.get(sistema, ()))
    if sistema == "refrigeracion":
        bloqueos.extend(_CAUSAS_EV)
    if sistema == "combustible_admision" and re.search(
        r"\binyectores?\s+no\s+inyectan?\b", _normalizar(evidencia)
    ):
        bloqueos.extend(("iac", "cuerpo de aceleracion"))
    normalizada = _normalizar(respuesta)
    return any(token in normalizada for token in bloqueos)


def detectar_areas_tecnicas(texto: str) -> list[str]:
    """Retorna solo áreas explícitamente respaldadas por términos de alta señal."""
    normalizado = _normalizar(texto)
    areas = [
        area
        for area, patrones in _REGLAS.items()
        if any(re.search(patron, normalizado) for patron in patrones)
    ]
    # Un sensor o sistema nombrado explícitamente es más específico que el
    # síntoma secundario de ralentí; no permitir que IAC desvíe esa consulta.
    areas_especificas = [area for area in areas if area != "RALENTI"]
    return areas_especificas or areas


def documento_coincide_con_areas(texto_documento: str, areas: list[str]) -> bool:
    """Exige que el documento mencione al menos un concepto del área solicitada."""
    normalizado = _normalizar(texto_documento)
    return any(
        termino in normalizado
        for area in areas
        for termino in _TERMINOS_DOCUMENTO.get(area, ())
    )


def filtrar_candidatos_por_area(
    candidatos: list[dict[str, Any]], areas: list[str]
) -> list[dict[str, Any]]:
    """Descarta resultados RAG fuera de tema; con área explícita, falla cerrado."""
    if not areas:
        return candidatos
    return [
        candidato
        for candidato in candidatos
        if documento_coincide_con_areas(
            f"{candidato.get('titulo', '')} {candidato.get('documento', '')}", areas
        )
    ]


def falla_coincide_con_areas(falla: str, areas: list[str]) -> bool:
    """Determina si una clase ML es pertinente para las áreas mencionadas."""
    return documento_coincide_con_areas(falla, areas)
