"""Enrutamiento determinista de sistemas técnicos para consultas multimarca."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Any

from src.core.diagnostico.taxonomia_sistemas import (
    obtener_subareas_de_clase,
)
from src.core.traductor_jerga import normalizar_jerga_peruana


def _normalizar(texto: str) -> str:
    normalizado = normalizar_jerga_peruana(texto or "")
    sin_tildes = unicodedata.normalize("NFKD", normalizado.lower())
    limpio = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    res = " ".join(limpio.split())
    res = re.sub(r"\bmescla\b", "mezcla", res)
    res = re.sub(r"\brecalntar\b", "recalentar", res)
    return res


ETIQUETAS_AREA: dict[str, str] = {
    "SOPORTES_MOTOR": "soportes de motor",
    "CLIMATIZACION": "climatización",
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

_AREAS_EN_ORDEN: tuple[str, ...] = (
    "SOPORTES_MOTOR",
    "CLIMATIZACION",
    "INYECCION_MEZCLA",
    "ADMISION_MAP",
    "RALENTI",
    "REFRIGERACION",
    "ENCENDIDO",
    "FRENOS",
    "TRANSMISION",
    "SUSPENSION_DIRECCION",
    "ELECTRICO_ECU",
)

_REGLAS: dict[str, tuple[str, ...]] = {
    "SOPORTES_MOTOR": (
        r"\bsoportes?\s+(?:de\s+)?motor\b", r"\btacos?\s+(?:de\s+)?motor\b",
    ),
    "CLIMATIZACION": (
        r"\baire acondicionado\b", r"\bclimatizacion\b", r"\ba/c\b",
        r"\bcompresor\b", r"\bcondensador\b", r"\br134a\b",
    ),
    "INYECCION_MEZCLA": (
        r"\binyector(?:es)?\b", r"\binyeccion\b", r"\bmezcla\s+pobre\b",
        r"\bmezcla\s+rica\b", r"\bsensor\s+(?:de\s+)?oxigeno\b",
        r"\bsonda\s+lambda\b", r"\bsensor\s+lambda\b", r"\b(?:p0171|p0172)\b",
        r"\b(?:stft|ltft|fuel\s+trim)\b", r"\briel\s+de\s+combustible\b",
        r"\bbomba\s+de\s+(?:gasolina|combustible)\b", r"\b(?:fscm|pem)\b",
        r"\bcommon\s+rail\b",
    ),
    "ADMISION_MAP": (
        r"\bsensor\s+map\b", r"\bcarga\s+absoluta\b", r"\bpresion\s+(?:del\s+)?multiple\b",
        r"\bmap\b", r"\bmaf\b", r"\b(?:p0105|p0106|p0107|p0108|p0109)\b",
    ),
    "RALENTI": (
        r"\bralenti\b", r"\bmarcha\s+minima\b", r"\bminimo\b", r"\biac\b",
        r"\bcuerpo\s+de\s+aceleracion\b", r"\bmariposa\b",
        r"\b(?:revoluciones|rpm)\b.{0,45}\b(?:suben?\s+y\s+bajan?|oscila\w*|inestable)\b",
        r"\b(?:suben?\s+y\s+bajan?|oscila\w*)\b.{0,45}\b(?:revoluciones|rpm)\b",
    ),
    "REFRIGERACION": (
        r"\brefrigeracion\b",
        r"\brecalienta\w*\b", r"\brecalent\w*\b", r"\bsobrecalienta\w*\b", r"\bsobrecalent\w*\b",
        r"\btemperatura\s+(?:del\s+)?motor\b", r"\btemperatura\s+(?:sube|alta|elevada)\b",
        r"\b(?:se\s+calienta|calienta\s+demasiado|motor\s+calienta)\b",
        r"\btermostato\b", r"\bcaja\s+termostatica\b", r"\bradiador\b",
        r"\bmotoventilador\b", r"\brefrigerante\b",
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
        r"\b(?:vibra|tiembla)\b.{0,80}\bal\s+frenar\b",
        r"\b(?:cuando|al)\s+fren(?:o|ar|a)\b.{0,80}\b(?:vibra|tiembla|chirrido|ruido)\b",
        r"\bdisco(?:s)?\s+alabeado(?:s)?\b",
        r"\bruido\s+(?:al|cuando)\s+frenar\b",
        r"\bchirrido\b.{0,60}\b(?:ruedas?|fren(?:o|ar|a))\b",
        r"\bpedal\s+de\s+freno\b", r"\bdisco(?:s)?\s+de\s+freno\b",
        r"\bpastillas?\s+(?:de\\s+)?freno\b", r"\babs\b",
    ),
    "TRANSMISION": (
        r"\b(?:patina|patinando)\s+(?:el\s+)?embrague\b", r"\bembrague\s+patina\b",
        r"\btransmision\b", r"\bcaja\s+(?:de\s+)?cambios\b", r"\bno\s+entran\s+los\s+cambios\b",
        r"\b(?:dsg|cvt|caja\s+automatica|pasar\s+(?:los\s+)?cambios|al\s+pasar\s+cambios)\b",
    ),
    "SUSPENSION_DIRECCION": (
        r"\bse\s+inclina\s+en\s+(?:las\s+)?curvas\b",
        r"\b(?:golpeteo|golpes?|rebota)\s+(?:met[aá]licos?\s+)?(?:en\s+)?(?:baches|huecos)\b",
        r"\bgolpes?\s+met[aá]licos?\b.{0,60}\b(?:suspensi[oón]|baches?)\b",
        r"\bsuspensi[oón]\b.{0,60}\b(?:golpes?|baches?|ruido|met[aá]licos?)\b",
        r"\bdesbalanceo\b", r"\balineacion\b", r"\brotula(?:s)?\b", r"\bamortiguador(?:es)?\b",
        r"\bbujes?\s+(?:de\s+)?(?:trapecio|suspensi[oón]|barra)\b",
        r"\b(?:timon|volante)\s+vibra\b.{0,35}\b(?:\d{2,3}\s*km/?h|velocidad)\b",
    ),
    "ELECTRICO_ECU": (
        r"\balternador\b", r"\bbateria\s+(?:se\s+)?descarga\w*\b",
        r"\b(?:ecu|pcm|ecm|bcm|tcm|computadora|modulo(?:\s+de\s+control)?)\b.{0,55}\b(?:incompatible|de\s+otra\s+version|otro\s+modelo|desguace|usad[oa]|no\s+comunica|sin\s+comunicacion|bloquead[oa]|no\s+codificad[oa]|reprogramar|programar|hermanar|clonar|virgen|emergencia|proteccion)\b",
        r"\b(?:escaner|scanner|interfaz|obd2?|puerto)\b.{0,55}\b(?:no\s+comunica|sin\s+comunicacion|error\s+de\s+(?:enlace|comunicacion)|no\s+conecta|no\s+entra|no\s+enlaza)\b",
        r"\b(?:cambie|cambio|cambiar|cambiaron|reemplaz\w*|pusieron|instalaron|montaron)\b.{0,35}\b(?:la\s+|el\s+|una?\s+)?(?:ecu|pcm|ecm|computadora|modulo(?:\s+de\s+motor)?)\b",
        r"\b(?:error|falla|falta)\s+(?:de\s+)?(?:codificacion|programacion|sincronizacion|inmovilizador|enlace)\b",
        r"\b(?:inmovilizador|llave\s+codificada|transponder|testigo\s+(?:de\s+)?(?:llave|candado|inmovilizador))\b.{0,55}\b(?:parpadea|encendido|activo|bloquea\w*|no\s+arranca|se\s+apaga)\b",
        r"\b(?:perdida\s+de\s+comunicacion|red\s+can|bus\s+can|can\s+(?:high|low|h|l)|u0100|u0101|u0121|u0140|u0155|p0601|p0602|p0606)\b",
        r"\b(?:corto\s+electrico|cortocircuito|cable(?:s)?\s+(?:pelado|quemado|en\s+corto|aterrizado|a\s+masa)|arnes\s+(?:en\s+corto|quemado|danado|dañado)|quema\s+(?:el\s+)?fusible|modo\s+(?:de\s+)?(?:proteccion|emergencia|seguro|degradado)|limp\s+mode)\b",
        r"\bantecedente\s+(?:electrico[/\s]+)?(?:ecu|computadora|arnes)\b",
    ),
}

_TERMINOS_DOCUMENTO: dict[str, tuple[str, ...]] = {
    "SOPORTES_MOTOR": ("soporte de motor", "soportes de motor", "taco de motor"),
    "CLIMATIZACION": ("aire acondicionado", "climatizacion", "compresor", "condensador", "r134a"),
    "INYECCION_MEZCLA": (
        "inyector", "inyeccion", "mezcla pobre", "mezcla rica", "oxigeno", "lambda",
        "fuel trim", "stft", "ltft", "p0171", "p0172", "presion de combustible",
        "bomba de gasolina", "baja presion", "fscm", "pem", "common rail",
        "intercooler", "turbocompresor", "vgt", "gdi", "descarbonizacion",
        "dpf", "fap", "adblue", "evap", "canister", "catalitico", "flex", "etanol",
    ),
    "ADMISION_MAP": (
        "sensor map", "presion map", "carga absoluta", "presion del multiple", "p0106",
        "sensor maf", "flujo de aire", "admision", "fuga de vacio",
    ),
    "RALENTI": ("ralenti", "marcha minima", "minimo", "valvula iac", "cuerpo de aceleracion", "mariposa", "tps"),
    "REFRIGERACION": (
        "refrigeracion", "recalent", "refrigerante", "radiador", "termostato", "motoventilador",
        "culata", "junta", "sensor de temperatura", "ect",
    ),
    "ENCENDIDO": (
        "bujia", "bobina", "chispa", "misfire", "p030", "ciguenal", "ckp", "cmp",
        "arbol de levas", "distribucion", "vvt", "valvetronic", "compresion",
    ),
    "FRENOS": (
        "freno", "pastilla", "disco", "abs", "frenar", "servofreno", "booster",
        "caliper", "mordaza", "secador aps", "maxi-brake",
    ),
    "TRANSMISION": (
        "embrague", "transmision", "caja de cambios", "sincronizador",
        "aceite de caja", "dsg", "cvt", "automatica", "bombin", "diferencial",
        "dualogic", "i-motion", "easytronic", "collarin", "crapodina",
    ),
    "SUSPENSION_DIRECCION": (
        "suspension", "direccion", "amortiguador", "rotula", "desbalance", "desaline",
        "alineacion", "llanta", "bache", "homocinetica", "palier", "cremallera", "rodamiento", "maza",
    ),
    "ELECTRICO_ECU": (
        "ecu", "computadora", "red can", "corto electrico", "comunicacion electrica",
        "alternador", "bateria", "inmovilizador", "codificacion", "motor de arranque",
        "solenoide", "fuga parasita", "inversor", "igbt", "fscm", "pem",
    ),
}

_ETIQUETA_A_SISTEMA = {
    "CLIMATIZACION": "climatizacion",
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
    "climatizacion": "CLIMATIZACION",
    "refrigeracion": "REFRIGERACION",
    "combustible_admision": "INYECCION_MEZCLA",
    "encendido": "ENCENDIDO",
    "frenos": "FRENOS",
    "transmision": "TRANSMISION",
    "suspension_direccion": "SUSPENSION_DIRECCION",
    "electrico_ecu": "ELECTRICO_ECU",
}

_MARCADORES_CAUSA = {
    "climatizacion": ("compresor", "aire acondicionado", "condensador", "r134a", "climatizacion"),
    "refrigeracion": ("refriger", "radiador", "termostato", "ventilador", "bomba de agua", "refrigerante", "ect"),
    "combustible_admision": (
        "inyector", "inyeccion", "mezcla", "maf", "map", "oxigeno", "lambda", "o2",
        "vacio", "combustible", "iac", "cuerpo de aceleracion", "tps", "admision",
        "mariposa", "ralenti", "fscm", "pem", "common rail", "intercooler", "turbo",
        "vgt", "gdi", "dpf", "fap", "adblue", "evap", "canister", "catalitico", "etanol", "flex",
    ),
    "encendido": (
        "bujia", "bobina", "encendido", "chispa", "misfire", "cilindro",
        "ciguenal", "ckp", "cmp", "arbol de levas", "distribucion", "vvt",
        "valvetronic", "compresion", "preignicion", "detonacion",
    ),
    "frenos": (
        "freno", "pastilla", "disco", "caliper", "abs", "liquido de frenos",
        "servofreno", "booster", "mordaza", "secador aps", "maxi-brake",
    ),
    "transmision": (
        "embrague", "caja", "transmision", "sincronizador", "convertidor", "marcha",
        "bombin", "diferencial", "dualogic", "i-motion", "easytronic", "cvt", "dsg",
        "collarin", "crapodina",
    ),
    "suspension_direccion": (
        "amortiguador", "rotula", "buje", "bieleta", "direccion", "cremallera",
        "llanta", "balanceo", "alineacion", "suspension", "homocinetica",
        "palier", "rodamiento", "maza", "soporte",
    ),
    "electrico_ecu": (
        "ecu", "computadora", "corto", "can", "cableado", "masa electrica", "eléctrica",
        "alternador", "bateria", "bornes", "inmovilizador", "codificacion",
        "motor de arranque", "solenoide", "fuga parasita", "inversor", "igbt", "fscm", "pem",
    ),
}

_CAUSAS_PROHIBIDAS = {
    "climatizacion": ("bujia", "embrague", "pastilla", "inyector", "bateria de traccion", "inversor"),
    "refrigeracion": ("oxigeno", "o2", "lambda", "mezcla", "llanta", "embrague", "bujia", "bobina", "inyector", "maf", "freno"),
    "combustible_admision": ("radiador", "termostato", "ventilador", "llanta", "embrague", "pastilla", "amortiguador", "freno"),
    "encendido": ("radiador", "termostato", "llanta", "embrague", "pastilla", "amortiguador", "freno", "disco"),
    "frenos": ("inyector", "sensor o2", "radiador", "embrague", "amortiguador", "bujia", "bobina", "chispa", "misfire", "alternador", "bateria"),
    "transmision": ("inyector", "sensor o2", "radiador", "pastilla", "amortiguador", "freno"),
    "suspension_direccion": ("inyector", "sensor o2", "radiador", "pastilla", "embrague", "freno", "disco", "liquido de freno", "caliper", "mordaza", "bujia", "bobina", "chispa"),
    "electrico_ecu": ("llanta", "pastilla", "radiador", "embrague", "amortiguador"),
}

_CAUSAS_EV = (
    "bateria", "bateria de traccion", "bateria de alto voltaje", "inversor",
    "hibrido", "alto voltaje", "high voltage", "vehiculo electrico",
    "motor electrico", "sistema electrico de traccion", "propulsion electrica",
)

_CAUSAS_EV_ESTRICTAS = (
    "bateria de traccion", "bateria de alto voltaje", "inversor", "igbt",
    "hibrido", "alto voltaje", "high voltage", "vehiculo electrico",
    "motor electrico", "sistema electrico de traccion", "propulsion electrica",
)

_PATRON_FUERA_RUTEO_EXPERIMENTAL = re.compile(
    r"\b(?:limpiaparabrisas|parabrisas|plumas?|cerradura|chapa|pestillo|manija|"
    r"cierre\s+centralizado|elevalunas|alzacristales|alzavidrios|elevador\s+de\s+vidrio|"
    r"frenos?\s+neumaticos?|frenos?\s+de\s+aire|secador\s+aps|maxi[- ]?brake|"
    r"dpf|fap|adblue|filtro\s+de\s+particulas|presion\s+de\s+aceite|bomba\s+de\s+aceite|"
    r"consumo\s+de\s+aceite|humo\s+azul)\b"
)


def _evidencia_menciona_ev_hibrido(evidencia_normalizada: str) -> bool:
    return bool(
        re.search(
            r"\b(?:bateria\s+de\s+(?:alto\s+voltaje|traccion)|sistema\s+hibrido|hibrid[oa]s?|"
            r"prius|inversor|igbt|alto\s+voltaje|vehiculo\s+electrico|auto\s+electrico|"
            r"modo\s+ready|p0a80|\bev\b|\bhev\b|\bphev\b)\b",
            evidencia_normalizada,
        )
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
    normalizado = _normalizar(texto)
    if _PATRON_FUERA_RUTEO_EXPERIMENTAL.search(normalizado):
        return None
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
    if _PATRON_FUERA_RUTEO_EXPERIMENTAL.search(normalizado):
        return None
    if re.search(r"\bno\s+tiembla\b", normalizado) and re.search(
        r"\b(?:minimo\s+bajo|ralenti\s+bajo|\d{2,4}\s*rpm)\b", normalizado
    ) and not re.search(r"\b(?:misfire|ratea|cabecea|vibra)\b", normalizado):
        return "ambiguo"
    if re.search(
        r"\b(?:al\s+frenar\s+no\s+(?:tiembla|vibra|hace\s+ruido)|"
        r"no\s+(?:tiembla|vibra|hace\s+ruido)\s+al\s+frenar)\b",
        normalizado,
    ):
        normalizado = re.sub(r"\bfrenar\b", "", normalizado)
        if re.search(r"\b(?:volante|timon)\s+(?:vibra|tiembla)\b", normalizado):
            return "suspension_direccion"
    texto_sin_negaciones_de_irregularidad = re.sub(
        r"\bno\s+(?:tiembla|tiemblo|vibra|vibro|ratea|cabecea|sacude)\b",
        " ",
        normalizado,
    )
    tiene_irregularidad = bool(
        re.search(
            r"\b(?:tiembla|temblor|vibraci[oón]|misfire|cabecea|sacude|vibra|ratea)\b",
            texto_sin_negaciones_de_irregularidad,
        )
    )
    tiene_oscilacion_ralenti = bool(
        re.search(
            r"\b(?:suben?\s+y\s+bajan?|oscila\w*|ralenti\s+inestable|minimo\s+inestable)\b",
            normalizado,
        )
    )
    tiene_ralenti_bajo = bool(
        re.search(r"\b(?:\d{2,4}\s*rpm|500\s*rpm|m[ií]nimo|ralent[ií])\b", normalizado)
    )
    tiene_area_mas_especifica = bool(
        re.search(
            r"\b(?:sensor\s+map|carga\s+absoluta|\bmap\b|\bmaf\b|inyector(?:es)?|"
            r"mezcla\s+(?:pobre|rica)|sensor\s+(?:de\s+)?ox[ií]geno|\bp0(?:171|172)\b|"
            r"recalienta\w*|refrigeraci[oón]|termostato|radiador|bomba\s+de\s+gasolina|"
            r"common\s+rail|fscm|pem)\b",
            normalizado,
        )
    )
    if tiene_irregularidad and tiene_ralenti_bajo and not tiene_area_mas_especifica:
        return "encendido"
    if (
        re.search(r"\b(?:500\s*rpm|ralenti\s+bajo|minimo\s+bajo)\b", normalizado)
        and not tiene_irregularidad
        and not tiene_oscilacion_ralenti
    ):
        return "ambiguo"
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
    filtradas = []
    for area in detectadas:
        patrones = _REGLAS[area]
        negada = any(
            re.search(r"\bno\s+(?:es\s+)?(?:de\s+)?(?:vibra\s+al\s+)?" + patron.removeprefix(r"\b").removesuffix(r"\b"), normalizado)
            for patron in patrones
        )
        if area == "FRENOS" and re.search(r"\b(?:no\s+(?:presenta|tiene|hay)\s+problemas?\s+(?:de\s+)?frenos?|sin\s+problemas?\s+de\s+frenos?|no\s+vibra\s+al\s+frenar)\b", normalizado):
            negada = True
        elif area == "SUSPENSION_DIRECCION" and re.search(r"\b(?:no\s+(?:presenta|tiene|hay)\s+problemas?\s+(?:de\s+)?suspensi[oón]|sin\s+problemas?\s+de\s+suspensi[oón])\b", normalizado):
            negada = True
        elif area == "ENCENDIDO" and re.search(r"\b(?:no\s+(?:presenta|tiene|hay)\s+problemas?\s+(?:de\s+)?encendido|sin\s+problemas?\s+de\s+encendido)\b", normalizado):
            negada = True
        if not negada:
            filtradas.append(area)
    if not filtradas:
        return "ambiguo"
    for area in ("CLIMATIZACION", "REFRIGERACION", "INYECCION_MEZCLA", "ADMISION_MAP", "ENCENDIDO", "FRENOS", "TRANSMISION", "SUSPENSION_DIRECCION", "ELECTRICO_ECU", "RALENTI"):
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


def areas_para_sistema(sistema_activo: str | None, texto_actual: str = "") -> list[str]:
    """Convierte el sistema activo en áreas internas compatibles con el resto del pipeline."""
    if not sistema_activo or sistema_activo == "ambiguo":
        return []
    if sistema_activo == "combustible_admision":
        especificas = [
            area for area in detectar_areas_tecnicas(texto_actual)
            if area in {"INYECCION_MEZCLA", "ADMISION_MAP", "RALENTI"}
        ]
        if especificas:
            return especificas
        return ["INYECCION_MEZCLA", "ADMISION_MAP", "RALENTI"]
    area = _ALIAS_SISTEMA_A_AREA.get(sistema_activo)
    return [area] if area else []


def filtrar_causas(sistema_activo: str | None, causas_propuestas: list[Any], evidencia: str = "") -> list[Any]:
    """Filtra hipótesis incompatibles con el sistema activo sin inventar reemplazos."""
    sistema = str(sistema_activo or "").lower()
    marcadores = _MARCADORES_CAUSA.get(sistema)
    if not marcadores:
        return []
    evidencia_normalizada = _normalizar(evidencia)
    bloqueos = list(_CAUSAS_PROHIBIDAS.get(sistema, ()))
    if not _evidencia_menciona_ev_hibrido(evidencia_normalizada):
        if sistema == "refrigeracion":
            bloqueos.extend(_CAUSAS_EV)
        else:
            bloqueos.extend(_CAUSAS_EV_ESTRICTAS)
    if sistema == "refrigeracion":
        if re.search(r"\b(?:humo|vapor) blanco\b", evidencia_normalizada) and "refrigerante" in evidencia_normalizada:
            marcadores = (*marcadores, "culata", "junta")
    if sistema == "combustible_admision":
        if (
            re.search(r"\binyectores?\s+no\s+inyectan?\b", evidencia_normalizada)
            or re.search(r"\b(?:iac|cuerpo\s+de\s+aceleracion)\s+ya\s+lo\s+revise\b", evidencia_normalizada)
            or (
                "mezcla pobre" in evidencia_normalizada
                and not any(
                    w in evidencia_normalizada
                    for w in ("ralenti", "minimo", "apaga", "tiron", "acelera", "tps")
                )
            )
        ):
            bloqueos.extend(("iac", "cuerpo de aceleracion"))
    resultado = []
    for causa in causas_propuestas:
        texto = str(causa.get("falla", "") if isinstance(causa, dict) else getattr(causa, "falla", causa))
        normalizado = _normalizar(texto)
        if any(token in normalizado for token in bloqueos):
            continue
        subareas_ml = obtener_subareas_de_clase(texto)
        coincide_subarea = (
            sistema in subareas_ml
            and not (sistema == "refrigeracion" and ("culata" in normalizado or "junta" in normalizado) and "culata" not in marcadores)
        )
        if any(token in normalizado for token in marcadores) or coincide_subarea:
            resultado.append(causa)
    return resultado


def respuesta_menciona_causa_fuera_de_sistema(
    sistema_activo: str | None,
    respuesta: str,
    evidencia: str = "",
) -> bool:
    """Guard simple para no entregar al usuario una causa explícitamente prohibida."""
    sistema = str(sistema_activo or "").lower() if sistema_activo else ""
    evidencia_normalizada = _normalizar(evidencia)
    bloqueos = list(_CAUSAS_PROHIBIDAS.get(sistema, ()))
    if sistema == "refrigeracion" and not _evidencia_menciona_ev_hibrido(evidencia_normalizada):
        bloqueos.extend(_CAUSAS_EV)
    elif not _evidencia_menciona_ev_hibrido(evidencia_normalizada):
        bloqueos.extend(_CAUSAS_EV_ESTRICTAS)
    if sistema == "combustible_admision" and re.search(
        r"\binyectores?\s+no\s+inyectan?\b", evidencia_normalizada
    ):
        bloqueos.extend(("iac", "cuerpo de aceleracion"))
    normalizada = _normalizar(respuesta)
    return any(token in normalizada for token in bloqueos)


def detectar_areas_tecnicas(texto: str) -> list[str]:
    """Devuelve áreas explícitas mencionadas por el usuario en orden de especificidad."""
    normalizado = _normalizar(texto)
    if re.search(r"\bno\s+es\s+(?:de\s+)?mezcla\b", normalizado) and "refrigeracion" in normalizado:
        return ["REFRIGERACION"]
    detectadas = [
        area
        for area in _AREAS_EN_ORDEN
        if any(re.search(patron, normalizado) for patron in _REGLAS[area])
    ]
    filtradas = []
    for area in detectadas:
        patrones = _REGLAS[area]
        negada = any(
            re.search(r"\bno\s+(?:es\s+)?(?:de\s+)?(?:vibra\s+al\s+)?" + patron.removeprefix(r"\b").removesuffix(r"\b"), normalizado)
            for patron in patrones
        )
        if area == "FRENOS" and re.search(r"\b(?:no\s+(?:presenta|tiene|hay)\s+problemas?\s+(?:de\s+)?frenos?|sin\s+problemas?\s+de\s+frenos?|no\s+vibra\s+al\s+frenar)\b", normalizado):
            negada = True
        elif area == "SUSPENSION_DIRECCION" and re.search(r"\b(?:no\s+(?:presenta|tiene|hay)\s+problemas?\s+(?:de\s+)?suspensi[oón]|sin\s+problemas?\s+de\s+suspensi[oón])\b", normalizado):
            negada = True
        elif area == "ENCENDIDO" and re.search(r"\b(?:no\s+(?:presenta|tiene|hay)\s+problemas?\s+(?:de\s+)?encendido|sin\s+problemas?\s+de\s+encendido)\b", normalizado):
            negada = True
        if not negada:
            filtradas.append(area)
    detectadas = filtradas
    if "SOPORTES_MOTOR" in detectadas:
        detectadas = [area for area in detectadas if area != "ENCENDIDO"]
    # Un subsistema específico o componente técnico domina sobre la condición genérica de ralentí
    areas_especificas = [area for area in detectadas if area != "RALENTI"]
    return areas_especificas or detectadas


def falla_coincide_con_areas(falla: str, areas: list[str]) -> bool:
    if not areas:
        return True
    subareas_ml = obtener_subareas_de_clase(falla)
    if any(area in subareas_ml for area in areas):
        return True
    normalizada = _normalizar(falla)
    return any(
        any(termino in normalizada for termino in _TERMINOS_DOCUMENTO.get(area, ()))
        for area in areas
    )


def filtrar_candidatos_por_area(
    candidatos: list[dict[str, Any]],
    areas: list[str],
) -> list[dict[str, Any]]:
    """Filtra documentos RAG para que pertenezcan al subsistema técnico detectado."""
    if not areas:
        return candidatos
    filtrados = []
    for item in candidatos:
        meta = item.get("metadatos") or {}
        texto = _normalizar(
            " ".join(
                str(parte or "")
                for parte in (
                    item.get("titulo"),
                    item.get("documento"),
                    meta.get("falla"),
                    meta.get("componente"),
                    meta.get("categoria"),
                    item.get("contenido"),
                )
            )
        )
        if any(
            any(termino in texto for termino in _TERMINOS_DOCUMENTO.get(area, ()))
            for area in areas
        ):
            filtrados.append(item)
    return filtrados
