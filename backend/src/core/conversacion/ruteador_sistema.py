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
    "ENCENDIDO": ("bobina", "bujia", "chispa", "p030", "ratea", "misfire", "tironea"),
    "PROGRAMACION": ("reprogramacion", "programacion", "inmovilizador", "codificacion", "ecu"),
    "REFRIGERACION": (
        "refrigerante", "termostato", "radiador", "bomba de agua", "sobrecalentamiento",
        "recalienta", "recalentamiento", "temperatura", "electroventilador", "ventilador",
        "motoventilador", "hirviendo",
    ),
    "ADMISION_RALENTI": (
        "iac", "tps", "cuerpo de aceleracion", "mariposa", "ralenti",
        "minimo bajo", "ralenti inestable", "bajas revoluciones",
    ),
    "LUBRICACION": ("presion de aceite", "bomba de aceite", "consumo de aceite"),
    "ARRANQUE_CARGA": ("alternador", "bateria", "bornes", "motor de arranque", "solenoide de arranque"),
    "FRENOS": ("freno", "pastillas", "discos", "abs"),
    "SUSPENSION_DIRECCION": ("rotula", "bieleta", "amortiguador", "desbalanceo", "alineacion"),
    "TRANSMISION": (
        "embrague", "clutch", "caja de cambios", "transmision", "cvt",
        "zapateo", "zapatea", "trepidacion", "patinado",
    ),
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
        "ajuste de mezcla": "ajuste de mezcla",
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
        "sensor map": "sensor MAP / presión absoluta",
        "carga absoluta": "sensor MAP / presión absoluta",
        "presion absoluta": "sensor MAP / presión absoluta",
        "fuga de vacio": "fuga de vacío de admisión",
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
    texto = _normalizar(falla)
    if sistema == "ADMISION_RALENTI":
        compatibles_ralenti = (
            "ralenti", "minimo", "iac", "aceleracion", "acelerador", "mariposa",
            "tps", "admision", "vacio", "aire", "inyector", "inyeccion",
            "combustible", "presion de combustible",
        )
        return any(token in texto for token in compatibles_ralenti)
    if sistema != SISTEMA_INYECCION_MEZCLA:
        # Las categorías restantes orientan la entrevista, pero sus nombres no
        # son una taxonomía completa de las etiquetas del Linear SVM. Filtrarlas
        # por una lista corta de palabras vaciaría candidatos válidos (p. ej.
        # climatización -> presión de refrigerante/electroventilador). La ruta
        # de inyección/mezcla sí cuenta con evidencia y exclusiones explícitas.
        return True
    compatibles = (
        "inyector", "inyeccion", "combustible",
        "oxigeno", "lambda", "mezcla", "maf", "map", "presion absoluta", "aire no medido", "vacio", "admision",
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
    """Relaciona un descarte escrito por el mecánico o registrado en hechos con la hipótesis propuesta."""
    if not falla:
        return False
    candidato = _normalizar(falla)
    descartadas = getattr(estado, "hipotesis_descartadas", []) or []
    if any(_normalizar(d) in candidato or candidato in _normalizar(d) for d in descartadas):
        return True

    componentes = {
        "iac": ("iac", "valvula iac", "minimo"),
        "termostato": ("termostato",),
        "ventilador": ("ventilador", "electroventilador", "motoventilador"),
        "bujia": ("bujia", "bujias"),
        "bobina": ("bobina", "bobinas"),
        "bateria": ("bateria", "acumulador", "bornes"),
        "alternador": ("alternador",),
        "bomba": ("bomba de gasolina", "bomba de combustible", "bomba de alta", "pila de gasolina"),
        "inyector": ("inyector", "inyectores"),
        "oxigeno": ("sensor de oxigeno", "sensor o2", "sonda lambda"),
        "rotula": ("rotula", "rotulas"),
        "amortiguador": ("amortiguador", "amortiguadores"),
        "embrague": ("embrague", "clutch", "disco de embrague"),
        "fusible": ("fusible", "fusibles", "rele", "reles"),
    }

    # 1. Comprobación contra hechos estructurados de descarte en el estado
    hechos = getattr(estado, "hechos", {}) or {}
    for h_clave, h_obj in hechos.items():
        h_txt = f"{h_clave} {getattr(h_obj, 'valor', '')} {getattr(h_obj, 'texto_crudo', '')}".lower()
        cat = getattr(h_obj, "categoria", "")
        if cat in ("componente_descartado", "rechazo_hipotesis_usuario") or any(
            w in h_txt for w in ("descartad", "probado", "reemplazad", "nuevo", "buen estado", "intact")
        ):
            for clave, sinonimos in componentes.items():
                if any(s in candidato for s in sinonimos) and any(s in h_txt for s in sinonimos):
                    return True

    # 2. Comprobación contra el historial de mensajes del usuario
    mensajes = getattr(estado, "historial_mensajes_usuario", []) or []
    patron_descarte = re.compile(
        r"\b(descartad[oa]s?|est[aá]n?\s+(?:bien|buen[oa]s?|operativ[oa]s?|intact[oa]s?)|"
        r"funciona\s+bien|sigue\s+igual|cambi[eé]\s+nuev[oa]s?|son\s+nuev[oa]s?|"
        r"reci[eé]n\s+(?:puest|cambiad)[oa]s?|no\s+son?\s+(?:l[ao]s|el|la)|"
        r"nuev[oa]s?\s+originales|prob[eé]\s+con\s+otr[ao]|no\s+es\s+(?:el|la|los|las))\b",
        re.IGNORECASE,
    )
    for clave, sinonimos in componentes.items():
        if any(s in candidato for s in sinonimos):
            for mensaje in mensajes:
                for clausula in re.split(r"[.;]|\bpero\b", _normalizar(mensaje)):
                    if any(s in clausula for s in sinonimos) and patron_descarte.search(clausula):
                        return True
    return False
