"""Pruebas completas para las 48 directrices canónicas de taller automotriz (mecánicas vs electrónicas)."""

from __future__ import annotations

import pytest

from src.core.taxonomy.catalogo_fallas import CATALOGO_TAXONOMIA
from src.core.taxonomy.catalogo_pruebas_taller import (
    es_falla_mecanica_pura,
    listar_todas_las_directrices,
    obtener_directriz_taller,
)


def test_catalogo_48_directrices_registradas():
    """Verifica que existan exactamente las 48 directrices oficiales de taller."""
    directrices = listar_todas_las_directrices()
    assert len(directrices) == 48

    codigos = {d.codigo for d in directrices}
    assert len(codigos) == 48


def test_distribucion_mecanicas_y_electronicas():
    """Verifica la separación estricta entre averías mecánicas puras y con control electrónico."""
    directrices = listar_todas_las_directrices()
    mecanicas = [d for d in directrices if d.es_mecanica_pura]
    electronicas = [d for d in directrices if not d.es_mecanica_pura]

    assert len(mecanicas) == 27
    assert len(electronicas) == 21
    assert len(mecanicas) + len(electronicas) == 48


@pytest.mark.parametrize("codigo,item", CATALOGO_TAXONOMIA.items())
def test_cada_falla_de_taxonomia_tiene_directriz_valida(codigo, item):
    """Verifica que cada una de las 48 fallas taxonómicas tenga directriz técnica asociada."""
    directriz = obtener_directriz_taller(item.falla_principal)
    assert directriz is not None, f"No se encontró directriz para la falla '{item.falla_principal}' ({codigo})"
    assert directriz.codigo == codigo
    assert len(directriz.prueba_sugerida) > 20


def test_averias_mecanicas_puras_nunca_piden_escaner_dtc():
    """Regla metodológica de tesis: averías mecánicas puras nunca deben sugerir escaneo DTC preliminar."""
    acciones_prohibidas = [
        "realizar escaneo", "conectar escáner", "conectar escaner",
        "lectura de dtc", "escanear con obd", "borrar dtc",
    ]

    for directriz in listar_todas_las_directrices():
        if not directriz.es_mecanica_pura:
            continue

        prueba_lower = directriz.prueba_sugerida.lower()
        for accion in acciones_prohibidas:
            assert accion not in prueba_lower, (
                f"Avería mecánica pura '{directriz.falla}' sugiere indebidamente '{accion}': {directriz.prueba_sugerida}"
            )
        assert es_falla_mecanica_pura(directriz.falla) is True


def test_averias_electronicas_definen_dtc_frecuente():
    """Verifica que las 21 averías con control electrónico especifiquen su DTC característico."""
    for directriz in listar_todas_las_directrices():
        if directriz.es_mecanica_pura:
            continue

        assert directriz.dtc_frecuente is not None, f"Avería electrónica '{directriz.falla}' sin DTC"
        assert len(directriz.dtc_frecuente) >= 4
        assert directriz.dtc_frecuente[0] in ("P", "C", "B", "U")
