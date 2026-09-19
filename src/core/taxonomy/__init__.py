"""Módulo de taxonomía automotriz canónica y directrices de taller."""

from src.core.taxonomy.catalogo_fallas import CATALOGO_TAXONOMIA, FallaVehicularEstandar
from src.core.taxonomy.catalogo_pruebas_taller import (
    DirectrizTaller,
    es_falla_mecanica_pura,
    listar_todas_las_directrices,
    obtener_directriz_taller,
    obtener_prueba_taller,
)

__all__ = [
    "CATALOGO_TAXONOMIA",
    "FallaVehicularEstandar",
    "DirectrizTaller",
    "obtener_directriz_taller",
    "es_falla_mecanica_pura",
    "obtener_prueba_taller",
    "listar_todas_las_directrices",
]
