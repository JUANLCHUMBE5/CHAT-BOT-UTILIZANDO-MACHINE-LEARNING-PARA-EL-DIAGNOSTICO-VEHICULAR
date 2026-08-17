import pytest
from fastapi.testclient import TestClient

from main import app
from src.config import settings
from src.core.security import crear_jwt_token

client = TestClient(app)


@pytest.fixture
def auth_headers_admin():
    token = crear_jwt_token(
        sub="00000000-0000-0000-0000-000000000001",
        rol="administrador",
        taller_id="00000000-0000-0000-0000-000000000001",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_mecanico():
    token = crear_jwt_token(
        sub="00000000-0000-0000-0000-000000000002",
        rol="mecanico",
        taller_id="00000000-0000-0000-0000-000000000001",
    )
    return {"Authorization": f"Bearer {token}"}


def test_obtener_metricas_validacion_taller(auth_headers_admin):
    resp = client.get("/api/v1/validacion-taller/metricas", headers=auth_headers_admin)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_casos" in data
    assert "tasa_acierto_global_porcentaje" in data
    assert "reduccion_tiempo_porcentaje" in data
    assert "nota_metodologica" in data
    assert data["total_casos"] >= 1900


def test_listar_casos_validacion_taller_paginado(auth_headers_admin):
    resp = client.get("/api/v1/validacion-taller?skip=0&limit=10", headers=auth_headers_admin)
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "casos" in data
    assert len(data["casos"]) <= 10
    if len(data["casos"]) > 0:
        primer_caso = data["casos"][0]
        assert "placa_enmascarada" in primer_caso
        assert "placa_hash" in primer_caso
        assert "falla_real" in primer_caso
        assert "prediccion_correcta" in primer_caso


def test_crear_caso_validacion_y_pseudonimizacion(auth_headers_admin):
    nuevo_caso = {
        "fase": "Post-test",
        "fecha": "2026-08-17",
        "placa": "XYZ-999",
        "marca_modelo": "Toyota Yaris 2020",
        "sintoma": "Pedal de freno esponjoso y perdida de presion",
        "falla_real": "Fuga en cilindro maestro de frenos",
        "chatbot_prediccion": "Fuga de liquido de frenos",
        "campos_completos": 1,
        "tiempo_diagnostico_minutos": 14,
        "prediccion_correcta": 1,
        "metodo_confirmacion": "Prueba Hidráulica Manómetro",
        "evidencia_ref": "EVIDENCIA_TEST_001.JPG",
    }
    resp = client.post("/api/v1/validacion-taller", json=nuevo_caso, headers=auth_headers_admin)
    assert resp.status_code == 201
    data = resp.json()
    assert data["placa_enmascarada"] == "XYZ-***"
    assert "placa_hash" in data
    assert data["falla_real"] == "Fuga en cilindro maestro de frenos"
    assert data["metodo_confirmacion"] == "Prueba Hidráulica Manómetro"


def test_exportar_csv_sanitizado(auth_headers_admin):
    resp = client.get("/api/v1/validacion-taller/exportar-csv", headers=auth_headers_admin)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    content = resp.content.decode("utf-8-sig")
    assert "item,fase,fecha,placa" in content


def test_mecanico_no_puede_acceder_validacion(auth_headers_mecanico):
    resp = client.get("/api/v1/validacion-taller/metricas", headers=auth_headers_mecanico)
    assert resp.status_code == 403
