"""Enrutamiento determinista por sistema antes de presentar hipótesis.

No sustituye al clasificador Linear SVM/TF-IDF. Su responsabilidad es impedir que
una predicción estadística contradiga evidencia técnica explícita aportada en el
caso activo (por ejemplo, mezcla pobre, inyector con bajo caudal o señal O2).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

SISTEMA_INYECCION_MEZCLA = "INYECCION_MEZCLA"


@dataclass(frozen=True)
class RutaSistema:
    """Resultado explicable del enrutamiento de un caso."""

    sistema: str | None
    evidencia: tuple[str, ...]


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto or "")
    return "".join(c for c in texto.lower() if unicodedata.category(c) != "Mn")


def _texto_caso(estado: Any, nueva_evidencia: str | None) -> str:
    partes: list[str] = list(getattr(estado, "historial_mensajes_usuario", []) or [])
    partes.extend(
        f"{getattr(h, 'campo', '')} {getattr(h, 'valor', '')}"
        for h in (getattr(estado, "hechos", {}) or {}).values()
    )
    if nueva_evidencia:
        partes.append(nueva_evidencia)
    return _normalizar(" ".join(partes))


def detectar_ruta_sistema(estado: Any, nueva_evidencia: str | None = None) -> RutaSistema:
    """Determina un sistema solo cuando la evidencia es específica y acumulada."""
    texto = _texto_caso(estado, nueva_evidencia)
    marcadores = {
        "inyector": "inyector",
        "mezcla pobre": "mezcla pobre",
        "p0171": "DTC P0171",
        "p0174": "DTC P0174",
        "sensor de oxigeno": "sensor O2",
        "sensor o2": "sensor O2",
        "lambda": "sensor lambda",
        "bajo caudal": "caudal de inyección",
        "no inyectan": "caudal de inyección",
        "presion de combustible": "presión de combustible",
        "presion en el riel": "presión de combustible",
        "maf": "medición de aire MAF",
    }
    evidencia = tuple(valor for patron, valor in marcadores.items() if patron in texto)
    if evidencia:
        return RutaSistema(SISTEMA_INYECCION_MEZCLA, evidencia)
    return RutaSistema(None, ())


def hipotesis_compatibles_con_ruta(falla: str, sistema: str | None) -> bool:
    """Evita mezclar sistemas cuando hay una ruta técnica fuerte."""
    if sistema != SISTEMA_INYECCION_MEZCLA:
        return True
    texto = _normalizar(falla)
    compatibles = (
        "inyector", "inyeccion", "combustible", "bomba", "filtro",
        "oxigeno", "lambda", "mezcla", "maf", "aire", "vacio", "admi",
        "p017", "evap", "riel",
    )
    if any(token in texto for token in compatibles):
        return True
    # "Presión" sin el sistema es ambigua: no debe permitir que presión de
    # aceite se infiltre en una ruta de combustible/mezcla.
    return "presion" in texto and any(token in texto for token in ("combustible", "riel", "inyeccion"))


def hipotesis_de_respaldo(sistema: str | None) -> list[dict[str, Any]]:
    """Hipótesis orientativas solo si el Top ML no contiene opciones del sistema detectado."""
    if sistema != SISTEMA_INYECCION_MEZCLA:
        return []
    return [
        {
            "falla": "Caudal insuficiente de inyectores o presión de combustible (evidencia reportada)",
            "probabilidad": 0.65,
        },
        {
            "falla": "Señal o circuito del sensor de oxígeno (O2/lambda)",
            "probabilidad": 0.55,
        },
        {
            "falla": "Entrada de aire no medida o lectura MAF fuera de rango",
            "probabilidad": 0.45,
        },
    ]


def tiene_descarte_de_componente(estado: Any, falla: str) -> bool:
    """Relaciona un descarte escrito por el mecánico con la hipótesis propuesta."""
    candidato = _normalizar(falla)
    texto = _texto_caso(estado, None)
    componentes = {
        "iac": ("iac", "valvula iac", "minimo"),
        "termostato": ("termostato",),
        "ventilador": ("ventilador", "electroventilador"),
    }
    for clave, sinonimos in componentes.items():
        if clave in candidato and any(s in texto for s in sinonimos):
            if re.search(r"\b(ya\s+revise|ya\s+revice|descart|no\s+es|esta\s+bien)\b", texto):
                return True
    return False
