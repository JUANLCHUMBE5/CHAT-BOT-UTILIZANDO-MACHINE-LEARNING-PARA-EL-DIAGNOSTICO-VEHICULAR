from fastapi.testclient import TestClient

from main import app
from src.config import settings

client = TestClient(app)


def test_respuestas_incluyen_encabezados_de_seguridad():
    response = client.get("/health/live")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"]


def test_request_id_invalido_no_se_refleja():
    response = client.get(
        "/health/live",
        headers={"X-Request-ID": "valor con espacios y caracteres no permitidos"},
    )

    assert response.headers["x-request-id"] != "valor con espacios y caracteres no permitidos"


def test_health_ready_oculta_detalles_en_produccion(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "expose_health_details", False)

    response = client.get("/health/ready")

    assert "componentes" not in response.json()
