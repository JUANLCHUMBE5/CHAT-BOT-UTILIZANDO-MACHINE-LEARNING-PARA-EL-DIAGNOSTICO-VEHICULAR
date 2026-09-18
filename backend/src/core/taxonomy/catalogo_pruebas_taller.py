"""Directrices técnicas de taller automotriz y procedimientos de comprobación.

Centraliza el conocimiento de comprobación en taller para las 48 fallas canónicas,
distinguiendo entre averías mecánicas puras (que requieren pruebas físicas/metrológicas
sin escáner) y averías con control electrónico (que requieren diagnóstico OBD-II).
"""

from __future__ import annotations

from typing import Dict, Optional

from src.core.taxonomy.directrices_electronicas import DIRECTRICES_ELECTRONICAS
from src.core.taxonomy.directrices_mecanicas import DIRECTRICES_MECANICAS, DirectrizTaller

# Catálogo completo estructurado de directrices de taller (48 fallas canónicas)
_REGLAS_DIRECTRICES: list[DirectrizTaller] = DIRECTRICES_MECANICAS + DIRECTRICES_ELECTRONICAS

# Índices para búsqueda rápida O(1) por código o por nombre de falla
_DIRECTRICES_POR_CODIGO: Dict[str, DirectrizTaller] = {d.codigo: d for d in _REGLAS_DIRECTRICES}
_DIRECTRICES_POR_FALLA: Dict[str, DirectrizTaller] = {d.falla.lower().strip(): d for d in _REGLAS_DIRECTRICES}


def obtener_directriz_taller(falla_o_codigo: Optional[str]) -> Optional[DirectrizTaller]:
    """Obtiene la directriz técnica de taller a partir del código canónico o del nombre de la falla."""
    if not falla_o_codigo:
        return None
    clave = falla_o_codigo.strip()
    # Buscar primero por código
    if clave.upper() in _DIRECTRICES_POR_CODIGO:
        return _DIRECTRICES_POR_CODIGO[clave.upper()]
    # Buscar por nombre exacto normalizado
    clave_lower = clave.lower()
    if clave_lower in _DIRECTRICES_POR_FALLA:
        return _DIRECTRICES_POR_FALLA[clave_lower]
    # Buscar coincidencia parcial si el nombre varía levemente
    for k, directriz in _DIRECTRICES_POR_FALLA.items():
        if k in clave_lower or clave_lower in k:
            return directriz
    return None


def es_falla_mecanica_pura(falla_o_codigo: Optional[str]) -> bool:
    """Retorna True si la avería es puramente mecánica/hidráulica y no requiere escáner electrónico."""
    directriz = obtener_directriz_taller(falla_o_codigo)
    if directriz:
        return directriz.es_mecanica_pura
    return False


def obtener_prueba_taller(falla_o_codigo: Optional[str]) -> Optional[str]:
    """Retorna la prueba física o electrónica recomendada para la falla vehicular."""
    directriz = obtener_directriz_taller(falla_o_codigo)
    if directriz:
        return directriz.prueba_sugerida
    return None


def listar_todas_las_directrices() -> list[DirectrizTaller]:
    """Retorna la lista completa de directrices de taller registradas."""
    return list(_REGLAS_DIRECTRICES)


__all__ = [
    "DirectrizTaller",
    "obtener_directriz_taller",
    "es_falla_mecanica_pura",
    "obtener_prueba_taller",
    "listar_todas_las_directrices",
]
