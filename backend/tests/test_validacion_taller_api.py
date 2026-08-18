import asyncio
import csv
import io
import pandas as pd
import pytest
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

from main import app
from src.config import settings
from src.core.security import crear_jwt_token
from src.interfaces.api.v1.endpoints import validacion_taller
from src.interfaces.api.v1.endpoints.validacion_taller import _pseudonimizar_placa

client = TestClient(app)

TALLER_1_ID = "00000000-0000-0000-0000-000000000001"
TALLER_2_ID = "00000000-0000-0000-0000-000000000002"


@pytest.fixture(autouse=True)
def mock_tracker_csv(tmp_path, monkeypatch):
    """Fixture que aisla completamente las pruebas en un archivo CSV temporal."""
    test_csv = tmp_path / "tracker_diagnosticos_test.csv"
    filas_iniciales = [
        {
            "item": 1,
            "fase": "Pre-test",
            "fecha": "2026-08-01",
            "placa": "ABC-***",
            "marca_modelo": "Toyota Yaris 2019",
            "sintoma": "Pedal de freno duro",
            "falla_real": "Pastillas desgastadas",
            "chatbot_prediccion": "Desgaste de pastillas",
            "campos_completos": 1,
            "tiempo_diagnostico_minutos": 25,
            "prediccion_correcta": 1,
            "taller_id": TALLER_1_ID,
            "mecanico_id": "mecanico-01",
            "metodo_confirmacion": "Inspección Visual",
            "evidencia_ref": "EVID_01.JPG",
        },
        {
            "item": 2,
            "fase": "Post-test",
            "fecha": "2026-08-02",
            "placa": "XYZ-***",
            "marca_modelo": "Hyundai Accent 2020",
            "sintoma": "Motor cascabelea",
            "falla_real": "Bujias sulfatadas",
            "chatbot_prediccion": "Falla de bujias",
            "campos_completos": 1,
            "tiempo_diagnostico_minutos": 10,
            "prediccion_correcta": 1,
            "taller_id": TALLER_1_ID,
            "mecanico_id": "mecanico-01",
            "metodo_confirmacion": "Escáner OBD",
            "evidencia_ref": "EVID_02.JPG",
        },
        {
            "item": 3,
            "fase": "Post-test",
            "fecha": "2026-08-03",
            "placa": "MNO-***",
            "marca_modelo": "Nissan Sentra 2021",
            "sintoma": "Zumbido en caja CVT",
            "falla_real": "Degradación fluido CVT",
            "chatbot_prediccion": "Falla transmision CVT",
            "campos_completos": 1,
            "tiempo_diagnostico_minutos": 12,
            "prediccion_correcta": 1,
            "taller_id": TALLER_2_ID,
            "mecanico_id": "mecanico-02",
            "metodo_confirmacion": "Prueba de Presión",
            "evidencia_ref": "EVID_03.JPG",
        },
    ]
    pd.DataFrame(filas_iniciales).to_csv(test_csv, index=False, encoding="utf-8")
    monkeypatch.setattr(validacion_taller, "TRACKER_CSV_PATH", test_csv)
    return test_csv


@pytest.fixture
def auth_headers_admin_taller1():
    token = crear_jwt_token(
        sub="admin-user-01",
        rol="administrador",
        taller_id=TALLER_1_ID,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_admin_taller2():
    token = crear_jwt_token(
        sub="admin-user-02",
        rol="administrador",
        taller_id=TALLER_2_ID,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_mecanico():
    token = crear_jwt_token(
        sub="mecanico-user-01",
        rol="mecanico",
        taller_id=TALLER_1_ID,
    )
    return {"Authorization": f"Bearer {token}"}


def test_aislamiento_multitenant_listado(auth_headers_admin_taller1, auth_headers_admin_taller2):
    """Verifica que el admin del Taller 1 no vea registros del Taller 2 y viceversa."""
    resp1 = client.get("/api/v1/validacion-taller", headers=auth_headers_admin_taller1)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["total"] == 2
    for c in data1["casos"]:
        assert c["taller_id"] == TALLER_1_ID

    resp2 = client.get("/api/v1/validacion-taller", headers=auth_headers_admin_taller2)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["total"] == 1
    assert data2["casos"][0]["taller_id"] == TALLER_2_ID
    assert data2["casos"][0]["marca_modelo"] == "Nissan Sentra 2021"


def test_aislamiento_multitenant_metricas_y_exportacion(auth_headers_admin_taller1, auth_headers_admin_taller2):
    """Verifica que las métricas y la exportación CSV se calculen aisladas por taller."""
    # Métricas Taller 1
    m1 = client.get("/api/v1/validacion-taller/metricas", headers=auth_headers_admin_taller1).json()
    assert m1["total_casos"] == 2
    assert m1["casos_pretest"] == 1
    assert m1["casos_posttest"] == 1

    # Métricas Taller 2
    m2 = client.get("/api/v1/validacion-taller/metricas", headers=auth_headers_admin_taller2).json()
    assert m2["total_casos"] == 1
    assert m2["casos_pretest"] == 0
    assert m2["casos_posttest"] == 1

    # Exportar CSV Taller 2
    csv_resp = client.get("/api/v1/validacion-taller/exportar-csv", headers=auth_headers_admin_taller2)
    assert csv_resp.status_code == 200
    contenido = csv_resp.content.decode("utf-8-sig")
    assert "Nissan Sentra 2021" in contenido
    assert "Toyota Yaris 2019" not in contenido


def test_hmac_sha256_pseudonimizacion():
    """Verifica hash HMAC-SHA-256 completo de 64 caracteres y enmascaramiento."""
    enmascarada, hash1 = _pseudonimizar_placa("ABC-123", secret_key="clave_secreta_A")
    assert enmascarada == "ABC-***"
    assert len(hash1) == 64
    assert all(c in "0123456789abcdef" for c in hash1)

    # Con clave secreta distinta el hash cambia
    _, hash2 = _pseudonimizar_placa("ABC-123", secret_key="clave_secreta_B")
    assert hash1 != hash2


def test_sanitizacion_ataques_csv_formula_injection(auth_headers_admin_taller1):
    """Verifica que payloads maliciosos de fórmulas (=, +, -, @) sean neutralizados con comilla simple."""
    caso_malicioso = {
        "fase": "Post-test",
        "fecha": "2026-08-17",
        "placa": "MAL-666",
        "marca_modelo": "=cmd|' /C calc'!A0",
        "sintoma": "@SUM(1+1)*cmd",
        "falla_real": "+2+5",
        "chatbot_prediccion": "-10*2",
        "campos_completos": 1,
        "tiempo_diagnostico_minutos": 10,
        "prediccion_correcta": 1,
        "metodo_confirmacion": "=HYPERLINK(\"http://evil.com\")",
        "evidencia_ref": "EVID_TEST.JPG",
    }
    post_resp = client.post("/api/v1/validacion-taller", json=caso_malicioso, headers=auth_headers_admin_taller1)
    assert post_resp.status_code == 201

    # Descargar CSV y verificar que cada celda peligrosa empiece con '
    csv_resp = client.get("/api/v1/validacion-taller/exportar-csv", headers=auth_headers_admin_taller1)
    filas = list(csv.reader(io.StringIO(csv_resp.content.decode("utf-8-sig"))))
    
    # Buscar la fila insertada
    fila_encontrada = None
    for f in filas:
        if "MAL-***" in f:
            fila_encontrada = f
            break
    assert fila_encontrada is not None
    # Verificar neutralización de prefijo en campos de fórmula
    assert any(col.startswith("'=cmd") for col in fila_encontrada)
    assert any(col.startswith("'@SUM") for col in fila_encontrada)
    assert any(col.startswith("'+2+5") for col in fila_encontrada)
    assert any(col.startswith("'-10*2") for col in fila_encontrada)


@pytest.mark.anyio
async def test_concurrencia_escrituras_atomicas(auth_headers_admin_taller1, mock_tracker_csv):
    """Verifica que múltiples escrituras concurrentes se ejecuten atómicamente sin pérdida de datos."""
    import httpx
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        async def _enviar_post(i):
            payload = {
                "fase": "Post-test",
                "fecha": "2026-08-17",
                "placa": f"CON-{i:03d}",
                "marca_modelo": f"Test Car {i}",
                "sintoma": f"Sintoma de prueba de concurrencia {i}",
                "falla_real": f"Falla confirmada {i}",
                "chatbot_prediccion": f"Prediccion {i}",
                "campos_completos": 1,
                "tiempo_diagnostico_minutos": 15,
                "prediccion_correcta": 1,
                "metodo_confirmacion": "Prueba de Concurrencia",
            }
            return await async_client.post("/api/v1/validacion-taller", json=payload, headers=auth_headers_admin_taller1)

        respuestas = await asyncio.gather(*[_enviar_post(i) for i in range(10)])

    for r in respuestas:
        assert r.status_code == 201

    df_final = pd.read_csv(mock_tracker_csv)
    # 3 iniciales + 10 concurrentes = 13 filas en total
    assert len(df_final) == 13
    assert len(df_final["item"].unique()) == 13


def test_mecanico_no_puede_acceder_validacion(auth_headers_mecanico):
    """Verifica control de acceso basado en roles (403 para mecánicos)."""
    resp_metricas = client.get("/api/v1/validacion-taller/metricas", headers=auth_headers_mecanico)
    assert resp_metricas.status_code == 403

    resp_listado = client.get("/api/v1/validacion-taller", headers=auth_headers_mecanico)
    assert resp_listado.status_code == 403

    resp_csv = client.get("/api/v1/validacion-taller/exportar-csv", headers=auth_headers_mecanico)
    assert resp_csv.status_code == 403
