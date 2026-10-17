"""Reglas conservadoras que reordenan hipótesis sin inventar probabilidad ML."""

from __future__ import annotations

import re
import unicodedata
from typing import List, Sequence, Tuple

from src.core.diagnostico.models import PrediccionML

CADENA = "Faja o cadena de distribucion destensada o con salto de punto"
COMMON_RAIL = "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)"
RESTRICCION = "Inyectores sucios o filtro de combustible obstruido"


def _normalizar(texto: str) -> str:
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(caracter) != "Mn"
    )


def _promover(
    falla: str,
    actuales: Sequence[PrediccionML],
    originales: Sequence[PrediccionML],
) -> Tuple[List[PrediccionML], float]:
    candidata = next((p for p in originales if p.falla == falla), None)
    probabilidad = candidata.probabilidad if candidata else 0.0
    promovida = PrediccionML(
        falla=falla,
        probabilidad=probabilidad,
        origen_probabilidad="SVM_ORIGINAL_REORDENADO_REGLA" if candidata else "REGLA_SIN_PROBABILIDAD",
    )
    return [promovida, *(p for p in actuales if p.falla != falla)][:3], probabilidad


def aplicar_reglas_coherencia(
    texto: str,
    diagnostico: str,
    confianza: float,
    predicciones: List[PrediccionML],
    originales: List[PrediccionML],
) -> Tuple[str, float, List[PrediccionML], str]:
    """Reordena solo con mediciones/inspecciones explícitas y conserva el score SVM original."""
    normalizado = _normalizar(texto)
    combustible_gasolina = bool(re.search(r"\b(?:gasolina|gnv|glp)\b", normalizado))
    combustible_diesel = bool(re.search(
        r"\b(?:diesel|petroleo|4jj1|1gd|2kd|common rail|dpf|adblue)\b", normalizado
    )) and not combustible_gasolina

    if combustible_diesel:
        incompatibles = ("gasolina quemada", "alcohol/etanol", "flex / bi-combustible", "catalizador tapado (gasolina)")
        predicciones = [p for p in predicciones if not any(x in _normalizar(p.falla) for x in incompatibles)]
        if predicciones:
            diagnostico, confianza = predicciones[0].falla, predicciones[0].probabilidad

    negacion_distribucion = bool(re.search(r"\b(?:no hay|sin)\s+(?:desfase|desfasaje|elongacion)\b", normalizado))
    medicion_distribucion = bool(re.search(
        r"\b(?:tensor|elongacion|correlacion|sincronizacion|desfase).{0,45}\d+(?:[.,]\d+)?\s*(?:mm|grados?|dientes?)\b",
        normalizado,
    ))
    if medicion_distribucion and not negacion_distribucion:
        predicciones, confianza = _promover(CADENA, predicciones, originales)
        return CADENA, confianza, predicciones, "Regla distribución: medición explícita; score SVM original conservado"

    presiones = [int(valor) for valor in re.findall(r"(?:presion\s+(?:del?\s+)?riel|riel).{0,30}?(\d{2,3})\s*bar", normalizado)]
    evidencia_riel_bajo = combustible_diesel and "caliente" in normalizado and any(presion < 250 for presion in presiones)
    if evidencia_riel_bajo:
        predicciones, confianza = _promover(COMMON_RAIL, predicciones, originales)
        return COMMON_RAIL, confianza, predicciones, "Regla Common Rail: presión de riel medida baja; score SVM original conservado"

    es_contexto_dpf = bool(re.search(r"\b(?:filtro\s+de\s+particulas|dpf|fap|adblue|def)\b", normalizado))
    inspeccion_restriccion = (
        combustible_diesel
        and not es_contexto_dpf
        and bool(
            re.search(
                r"\b(?:pescador|malla|filtro(?!\s+de\s+(?:particulas|aire|aceite|cabina|polen))).{0,35}(?:colmatad[oa]|obstruid[oa]|tapad[oa]|sedimento|baba)\b",
                normalizado,
            )
        )
    )
    medicion_restriccion = combustible_diesel and bool(re.search(
        r"\b(?:vacuometro.{0,25}-?\d+(?:[.,]\d+)?\s*(?:inhg|bar)|presion.{0,30}(?:cae|baja).{0,15}\d+(?:[.,]\d+)?\s*(?:bar|psi))\b",
        normalizado,
    ))
    if inspeccion_restriccion or medicion_restriccion:
        predicciones, confianza = _promover(RESTRICCION, predicciones, originales)
        return RESTRICCION, confianza, predicciones, "Regla combustible: inspección/medición explícita; score SVM original conservado"

    return diagnostico, confianza, predicciones, ""
