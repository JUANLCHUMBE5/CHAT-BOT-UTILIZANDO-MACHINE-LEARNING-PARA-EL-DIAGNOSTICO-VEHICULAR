"""Recuperación de arranque sin reservar trabajos ni contactar proveedores."""
from unittest.mock import AsyncMock

import pytest

from src.application.jobs import conexion_inicial


@pytest.mark.anyio
async def test_arranque_reintenta_dns_temporal(monkeypatch):
    conectar = AsyncMock(side_effect=[OSError("synthetic DNS failure"), None])
    dormir = AsyncMock()
    monkeypatch.setattr(conexion_inicial, "comprobar_conexion", conectar)
    monkeypatch.setattr(conexion_inicial.asyncio, "sleep", dormir)
    await conexion_inicial.esperar_base_disponible()
    assert conectar.await_count == 2
    dormir.assert_awaited_once_with(1)


@pytest.mark.anyio
async def test_arranque_no_reintenta_indefinidamente(monkeypatch):
    conectar = AsyncMock(side_effect=OSError("synthetic unavailable database"))
    monkeypatch.setattr(conexion_inicial, "comprobar_conexion", conectar)
    monkeypatch.setattr(conexion_inicial.asyncio, "sleep", AsyncMock())
    with pytest.raises(OSError):
        await conexion_inicial.esperar_base_disponible(intentos=3)
    assert conectar.await_count == 3


@pytest.mark.anyio
async def test_error_configuracion_no_es_transitorio(monkeypatch):
    conectar = AsyncMock(side_effect=ValueError("synthetic configuration error"))
    monkeypatch.setattr(conexion_inicial, "comprobar_conexion", conectar)
    with pytest.raises(ValueError):
        await conexion_inicial.esperar_base_disponible()
    assert conectar.await_count == 1
