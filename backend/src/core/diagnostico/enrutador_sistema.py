"""Enrutamiento determinista de sistemas técnicos para consultas multimarca."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Any

from src.core.diagnostico.enrutamiento_catalogo import (
    _ALIAS_SISTEMA_A_AREA,
    _AREAS_EN_ORDEN,
    _CAUSAS_EV,
    _CAUSAS_EV_ESTRICTAS,
    _CAUSAS_PROHIBIDAS,
    _ETIQUETA_A_SISTEMA,
    _MARCADORES_CAUSA,
    _PATRON_FUERA_RUTEO_EXPERIMENTAL,
    _REGLAS,
    _TERMINOS_DOCUMENTO,
)
from src.core.diagnostico.enrutamiento_catalogo import (
    ETIQUETAS_AREA as ETIQUETAS_AREA,
)
from src.core.diagnostico.evidencia_proposicional import evidencia_afirmada
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
    normalizado = _normalizar(evidencia_afirmada(texto))
    # A thermal symptom belongs to the explicitly named assembly, not always engine cooling.
    if re.search(r"\b(?:cvt|dsg|caja automatica|aceite de transmision)\b", normalizado):
        normalizado = re.sub(r"\b(?:sobrecalent\w*|recalent\w*)\b", "temperatura de transmision", normalizado)
    if re.search(r"\b(?:dpf|fap|adblue|filtro de particulas)\b", normalizado):
        normalizado = re.sub(r"modo (?:de )?(?:degradado|proteccion|emergencia)", "limitacion de potencia", normalizado)
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
    normalizado = _normalizar(evidencia_afirmada(texto))
    # A thermal symptom belongs to the explicitly named assembly, not always engine cooling.
    if re.search(r"\b(?:cvt|dsg|caja automatica|aceite de transmision)\b", normalizado):
        normalizado = re.sub(r"\b(?:sobrecalent\w*|recalent\w*)\b", "temperatura de transmision", normalizado)
    if re.search(r"\b(?:dpf|fap|adblue|filtro de particulas)\b", normalizado):
        normalizado = re.sub(r"modo (?:de )?(?:degradado|proteccion|emergencia)", "limitacion de potencia", normalizado)
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
    normalizado = _normalizar(evidencia_afirmada(texto))
    # A thermal symptom belongs to the explicitly named assembly, not always engine cooling.
    if re.search(r"\b(?:cvt|dsg|caja automatica|aceite de transmision)\b", normalizado):
        normalizado = re.sub(r"\b(?:sobrecalent\w*|recalent\w*)\b", "temperatura de transmision", normalizado)
    if re.search(r"\b(?:dpf|fap|adblue|filtro de particulas)\b", normalizado):
        normalizado = re.sub(r"modo (?:de )?(?:degradado|proteccion|emergencia)", "limitacion de potencia", normalizado)
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
