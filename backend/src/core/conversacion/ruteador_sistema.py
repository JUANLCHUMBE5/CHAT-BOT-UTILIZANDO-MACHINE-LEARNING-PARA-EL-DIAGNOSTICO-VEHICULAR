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

# Términos específicos: evitar palabras transversales como "bomba" o "aire".
CATEGORIAS = {
    "ENCENDIDO": ("bobina", "bujia", "chispa", "p030"),
    "PROGRAMACION": ("reprogramacion", "programacion", "inmovilizador", "codificacion", "ecu"),
    "REFRIGERACION": ("refrigerante", "termostato", "radiador", "bomba de agua", "sobrecalentamiento"),
    "ADMISION_RALENTI": ("iac", "tps", "cuerpo de aceleracion", "mariposa"),
    "LUBRICACION": ("presion de aceite", "bomba de aceite", "consumo de aceite"),
    "ARRANQUE_CARGA": ("alternador", "bateria", "bornes", "motor de arranque", "solenoide de arranque"),
    "FRENOS": ("freno", "pastillas", "discos", "abs"),
    "SUSPENSION_DIRECCION": ("rotula", "bieleta", "amortiguador", "desbalanceo", "alineacion"),
    "TRANSMISION": ("embrague", "caja de cambios", "transmision", "cvt"),
    "CLIMATIZACION": ("aire acondicionado", "compresor de ac", "evaporador"),
}


def _contiene(texto: str, termino: str) -> bool:
    return bool(re.search(r"\b" + re.escape(termino) + r"\w*\b", texto))


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
        "injector": "inyector",
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
    detectadas = [
        (categoria, tuple(t for t in terminos if _contiene(texto, t)))
        for categoria, terminos in CATEGORIAS.items()
    ]
    detectadas = [(c, e) for c, e in detectadas if e]
    if len(detectadas) == 1:
        return RutaSistema(*detectadas[0])
    # Con evidencia de varios sistemas no forzar una clasificación arbitraria.
    return RutaSistema(None, ())


def hipotesis_compatibles_con_ruta(falla: str, sistema: str | None) -> bool:
    """Evita mezclar sistemas cuando hay una ruta técnica fuerte."""
    if sistema != SISTEMA_INYECCION_MEZCLA:
        # Las categorías restantes orientan la entrevista, pero sus nombres no
        # son una taxonomía completa de las etiquetas del Linear SVM. Filtrarlas
        # por una lista corta de palabras vaciaría candidatos válidos (p. ej.
        # climatización -> presión de refrigerante/electroventilador). La ruta
        # de inyección/mezcla sí cuenta con evidencia y exclusiones explícitas.
        return True
    texto = _normalizar(falla)
    compatibles = (
        "inyector", "inyeccion", "combustible",
        "oxigeno", "lambda", "mezcla", "maf", "aire no medido", "vacio", "admision",
        "p017", "evap", "riel",
    )
    if any(token in texto for token in compatibles):
        return True
    # "Presión" sin el sistema es ambigua: no debe permitir que presión de
    # aceite se infiltre en una ruta de combustible/mezcla.
    return "presion" in texto and any(token in texto for token in ("combustible", "riel", "inyeccion"))


def requisito_tecnico_ausente(estado: Any, falla: str, evidencia: str | None = None) -> str | None:
    """No asumir equipamiento específico solo porque el ML lo predijo."""
    texto = _texto_caso(estado, evidencia)
    candidato = _normalizar(falla)
    requisitos = (
        (("flex", "etanol", "alcohol", "bi-combustible"), ("flex", "etanol", "e85", "alcohol")),
        (("gdi", "inyeccion directa"), ("gdi", "inyeccion directa", "fsi", "tfsi")),
        (("glp",), ("glp", "gas licuado")),
        (("gnv",), ("gnv", "gas natural")),
        (("diesel", "adblue", "dpf"), ("diesel", "adblue", "dpf")),
    )
    for etiquetas, evidencias in requisitos:
        if any(_contiene(candidato, t) for t in etiquetas):
            if not any(_contiene(texto, t) for t in evidencias):
                return "Equipamiento o combustible no confirmado por el mecánico"
    return None


def hipotesis_de_respaldo(sistema: str | None) -> list[dict[str, Any]]:
    """Hipótesis orientativas solo si el Top ML no contiene opciones del sistema detectado."""
    if sistema != SISTEMA_INYECCION_MEZCLA:
        return []
    # No fabricar clases ni probabilidades cuando el modelo no ofrece candidatos.
    return []


def tiene_descarte_de_componente(estado: Any, falla: str) -> bool:
    """Relaciona un descarte escrito por el mecánico con la hipótesis propuesta."""
    candidato = _normalizar(falla)
    mensajes = getattr(estado, "historial_mensajes_usuario", []) or []
    componentes = {
        "iac": ("iac", "valvula iac", "minimo"),
        "termostato": ("termostato",),
        "ventilador": ("ventilador", "electroventilador"),
    }
    for clave, sinonimos in componentes.items():
        if clave in candidato:
            for mensaje in mensajes:
                for clausula in re.split(r"[.;]|\bpero\b", _normalizar(mensaje)):
                    if any(s in clausula for s in sinonimos) and re.search(
                        r"\b(descartado|descartada|esta\s+bien|funciona\s+bien)\b", clausula
                    ):
                        return True
    return False
