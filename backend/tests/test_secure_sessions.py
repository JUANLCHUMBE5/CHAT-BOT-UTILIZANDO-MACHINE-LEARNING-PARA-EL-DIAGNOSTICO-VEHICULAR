from fastapi.testclient import TestClient

from main import app
from src.config import settings


def test_login_emite_cookie_refresh_httponly(monkeypatch):
    monkeypatch.setattr(settings, "legacy_refresh_token_body", False)
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "carbot2026"},
    )

    assert response.status_code == 200
    assert response.json()["refresh_token"] is None
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "path=/api/v1/auth" in cookie


def test_refresh_token_no_puede_reutilizarse():
    client = TestClient(app)
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "carbot2026"},
    )
    token_original = login.json()["refresh_token"]

    renovacion = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": token_original},
    )
    assert renovacion.status_code == 200

    cliente_atacante = TestClient(app)
    reutilizacion = cliente_atacante.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": token_original},
    )
    assert reutilizacion.status_code == 401


def test_logout_revoca_refresh_token():
    client = TestClient(app)
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "carbot2026"},
    )
    token = login.json()["refresh_token"]

    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 200

    cliente_atacante = TestClient(app)
    renovacion = cliente_atacante.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": token},
    )
    assert renovacion.status_code == 401
