from fastapi.testclient import TestClient

from main import app
from src.config import settings
from src.core.security import crear_jwt_token


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
    assert login.json()["refresh_token"] is None
    token_original = client.cookies.get(settings.refresh_cookie_name)
    assert token_original

    renovacion = client.post("/api/v1/auth/refresh")
    assert renovacion.status_code == 200

    cliente_atacante = TestClient(app)
    cliente_atacante.cookies.set(settings.refresh_cookie_name, token_original, path="/api/v1/auth")
    reutilizacion = cliente_atacante.post("/api/v1/auth/refresh")
    assert reutilizacion.status_code == 401


def test_logout_revoca_refresh_token():
    client = TestClient(app)
    client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "carbot2026"},
    )
    token = client.cookies.get(settings.refresh_cookie_name)
    assert token

    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 200

    cliente_atacante = TestClient(app)
    cliente_atacante.cookies.set(settings.refresh_cookie_name, token, path="/api/v1/auth")
    renovacion = cliente_atacante.post("/api/v1/auth/refresh")
    assert renovacion.status_code == 401


def test_logout_revoca_access_token_presentado():
    client = TestClient(app)
    token = crear_jwt_token(sub="admin", rol="administrador")

    logout = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout.status_code == 200

    respuesta = client.get(
        "/api/v1/metricas/colas",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert respuesta.status_code == 401
