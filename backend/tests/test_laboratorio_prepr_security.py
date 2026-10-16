"""Opt-in, autorización e aislamiento del laboratorio; sin proveedores reales."""
import pytest
from fastapi.testclient import TestClient

from main import app
from src.config import AppSettings, settings
from src.core.security import crear_jwt_token


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(settings, "enable_laboratory", True)
    monkeypatch.setattr(settings, "environment", "test")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setenv("CARBOT_BLOCK_DOTENV", "true")


def client(user="00000000-0000-0000-0000-000000000031", role="administrador", workshop=None):
    token = crear_jwt_token(usuario_id=user, rol=role, taller_id=workshop)
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_LABORATORY", raising=False)
    assert AppSettings().enable_laboratory is False
    monkeypatch.setattr(settings, "enable_laboratory", False)
    assert client().post("/api/v1/laboratorio/mensaje", json={"mensaje": "Hola"}).status_code == 403


@pytest.mark.parametrize("path,body", [
    ("/api/v1/laboratorio/mensaje", {"mensaje": "Hola"}),
    ("/api/v1/laboratorio/reiniciar?session_id=guard", None),
    ("/api/v1/laboratorio/ejecutar-caso/toyota", None),
])
def test_production_blocks_even_enabled(enabled, monkeypatch, path, body):
    monkeypatch.setattr(settings, "environment", "production")
    assert client().post(path, json=body).status_code == 403


def test_opt_in_from_environment(monkeypatch):
    monkeypatch.setenv("ENABLE_LABORATORY", "true")
    assert AppSettings().enable_laboratory is True


def test_jwt_and_admin_required(enabled):
    path = "/api/v1/laboratorio/mensaje"
    assert TestClient(app).post(path, json={"mensaje": "Hola"}).status_code == 401
    assert client(role="mecanico").post(path, json={"mensaje": "Hola"}).status_code == 403


@pytest.mark.parametrize("field", ["gemini_api_key", "groq_api_key"])
def test_credentials_fail_closed(enabled, monkeypatch, field):
    monkeypatch.setattr(settings, field, "synthetic-test-credential")
    assert client().post("/api/v1/laboratorio/mensaje", json={"mensaje": "Hola"}).status_code == 403


def test_dotenv_and_origin_fail_closed(enabled, monkeypatch):
    c = client()
    path = "/api/v1/laboratorio/mensaje"
    assert c.post(path, json={"mensaje": "Hola"}, headers={"Origin": "https://untrusted.invalid"}).status_code == 403
    monkeypatch.setenv("CARBOT_BLOCK_DOTENV", "false")
    assert c.post(path, json={"mensaje": "Hola"}).status_code == 403


def test_nonlocal_connection_denied(enabled):
    token = crear_jwt_token()
    c = TestClient(app, client=("203.0.113.10", 12345), headers={"Authorization": f"Bearer {token}"})
    assert c.post("/api/v1/laboratorio/mensaje", json={"mensaje": "Hola"}).status_code == 403


def test_authorized_users_cannot_share_case(enabled, monkeypatch):
    import requests

    def no_external(*args, **kwargs):
        pytest.fail("El laboratorio intentó una llamada HTTP externa")

    monkeypatch.setattr(requests.Session, "request", no_external)
    a = client()
    b = client("00000000-0000-0000-0000-000000000032", workshop="00000000-0000-0000-0000-000000000002")
    payload = {"session_id": "same-public-session", "mensaje": "Toyota Yaris 2020 gasolina placa SEC123. Vibra al frenar."}
    r1 = a.post("/api/v1/laboratorio/mensaje", json=payload)
    r2 = b.post("/api/v1/laboratorio/mensaje", json={**payload, "mensaje": "Hola"})
    assert r1.status_code == r2.status_code == 200
    assert r1.json()["case_id"] != r2.json()["case_id"]
    assert r2.json()["placa"] is None
    again = a.post("/api/v1/laboratorio/mensaje", json={**payload, "mensaje": "Consulta mi memoria"})
    assert again.json()["case_id"] == r1.json()["case_id"]
    assert again.json()["placa"] == "SEC-123"


def test_thermal_coverage_independent_of_numeric_fixture(enabled):
    r = client().post("/api/v1/laboratorio/mensaje", json={
        "session_id": "thermal-independent", "mensaje": "El motor recalienta a 108 grados. ¿Puedo abrir el radiador?",
    })
    assert r.status_code == 200
    text = r.json()["respuesta_texto"].lower()
    assert "no" in text and "radiador" in text
    assert "quemadura" in text or "presurizado" in text
