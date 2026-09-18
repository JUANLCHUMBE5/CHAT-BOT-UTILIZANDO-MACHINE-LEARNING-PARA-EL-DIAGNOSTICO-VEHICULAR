"""Pruebas unitarias para el servicio de consulta de códigos DTC / OBD-II."""

import pytest
from src.infrastructure.dtc.dtc_lookup_service import DtcLookupService
from src.infrastructure.container import ServiceContainer


def test_dtc_service_disponible():
    servicio = ServiceContainer.get_dtc_service()
    assert servicio.disponible is True


def test_consultar_codigo_generico_p0301():
    servicio = ServiceContainer.get_dtc_service()
    info = servicio.consultar_codigo("P0301")
    assert info is not None
    assert info["codigo"] == "P0301"
    assert "Misfire" in info["descripcion"] or "Cylinder 1" in info["descripcion"]


def test_consultar_codigo_generico_p0171():
    servicio = ServiceContainer.get_dtc_service()
    info = servicio.consultar_codigo("p0171")
    assert info is not None
    assert info["codigo"] == "P0171"
    assert "Lean" in info["descripcion"] or "System" in info["descripcion"]


def test_consultar_codigo_fabricante_toyota():
    servicio = ServiceContainer.get_dtc_service()
    info = servicio.consultar_codigo("P1135", marca="Toyota")
    if info:
        assert info["codigo"] == "P1135"
        assert info["es_especifico_fabricante"] is True


def test_consultar_codigo_inexistente():
    servicio = ServiceContainer.get_dtc_service()
    info = servicio.consultar_codigo("P9999")
    assert info is None


def test_extraer_codigos_en_texto():
    servicio = ServiceContainer.get_dtc_service()
    texto = "Mecánico, el escáner arrojó el código P0301 y también el P0420 con falla de catalizador"
    codigos = servicio.extraer_codigos_en_texto(texto)
    assert "P0301" in codigos
    assert "P0420" in codigos
