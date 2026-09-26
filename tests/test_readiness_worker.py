"""La API no debe anunciar disponibilidad con el worker externo caído."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import main
from src.config import settings


@pytest.mark.parametrize("activo, status", [(True, 200), (False, 503)])
def test_readiness_exige_heartbeat_reciente(monkeypatch, activo, status):
    monkeypatch.setattr(settings.database, "enabled", True)
    monkeypatch.setattr(settings, "expose_health_details", True)
    monkeypatch.setattr(main, "comprobar_conexion", AsyncMock())

    async def sesiones():
        yield object()

    monkeypatch.setattr(main, "obtener_sesion_db", sesiones)
    monkeypatch.setattr(
        main.TrabajoSistemaRepository, "obtener_worker_activo",
        AsyncMock(return_value=object() if activo else None),
    )
    monkeypatch.setattr(main.app.state, "gestor_diagnostico", SimpleNamespace(
        modelo_ml=SimpleNamespace(modelo=True), motor_rag=SimpleNamespace(faiss_index=True),
    ), raising=False)
    response = TestClient(main.app).get("/health/ready")
    assert response.status_code == status
    assert response.json()["componentes"]["worker_sistema_activo"] is activo
