import asyncio
import csv
import io
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from main import app
from src.core.security import crear_jwt_token
from src.interfaces.api.v1.endpoints import validacion_taller
from src.interfaces.api.v1.endpoints.validacion_taller import (
    _bloqueo_archivo_interproceso,
    _guardar_df_tracker_atomico,
    _pseudonimizar_placa,
)

client = TestClient(app)

TALLER_1_ID = "00000000-0000-0000-0000-000000000001"
TALLER_2_ID = "00000000-0000-0000-0000-000000000002"


def _worker_escribir_proceso(csv_path_str: str, worker_id: int) -> bool:
    """Función de nivel superior ejecutable por un subproceso independiente del SO."""
    csv_p = Path(csv_path_str)
    with _bloqueo_archivo_interproceso(csv_p, timeout=8.0):
        df = pd.read_csv(csv_p)
        item_id = int(df["item"].max()) + 1 if not df.empty and "item" in df.columns else 1
        nueva_fila = {
            "item": item_id,
            "fase": "Post-test",
            "fecha": "2026-08-17",
            "placa": f"PRC-{worker_id:03d}",
            "placa_hash": f"hash_proc_{worker_id:03d}".ljust(64, "0"),
            "marca_modelo": f"Car Multiprocess {worker_id}",
            "sintoma": f"Sintoma proceso {worker_id}",
            "falla_real": f"Falla proceso {worker_id}",
            "chatbot_prediccion": "Prediccion proceso",
            "campos_completos": 1,
            "tiempo_diagnostico_minutos": 12,
            "prediccion_correcta": 1,
            "taller_id": TALLER_1_ID,
            "mecanico_id": f"mecanico-{worker_id}",
            "metodo_confirmacion": "Prueba Multiproceso OS",
            "evidencia_ref": "",
        }
        df_act = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
        _guardar_df_tracker_atomico(df_act, csv_p)
    return True


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
            "placa_hash": _pseudonimizar_placa("ABC-101")[1],
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
            "placa_hash": _pseudonimizar_placa("XYZ-202")[1],
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
            "placa_hash": _pseudonimizar_placa("MNO-303")[1],
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


def test_estabilidad_placa_hash_post_hacia_get(auth_headers_admin_taller1):
    """Verifica que el hash HMAC-SHA-256 persista intacto e inmutable entre POST y GET."""
    caso_crear = {
        "fase": "Post-test",
        "fecha": "2026-08-17",
        "placa": "DEF-456",
        "marca_modelo": "Toyota Corolla 2021",
        "sintoma": "Pedal de freno esponjoso",
        "falla_real": "Aire en lineas de freno",
        "chatbot_prediccion": "Fuga de liquido de frenos",
        "campos_completos": 1,
        "tiempo_diagnostico_minutos": 14,
        "prediccion_correcta": 1,
        "metodo_confirmacion": "Prueba de Purga Hidráulica",
        "evidencia_ref": "EVID_DEF456.JPG",
    }
    resp_post = client.post("/api/v1/validacion-taller", json=caso_crear, headers=auth_headers_admin_taller1)
    assert resp_post.status_code == 201
    data_post = resp_post.json()
    post_item = data_post["item"]
    post_hash = data_post["placa_hash"]
    assert len(post_hash) == 64
    assert data_post["placa_enmascarada"] == "DEF-***"

    # Consultar por GET y encontrar el item creado
    resp_get = client.get("/api/v1/validacion-taller?limit=10", headers=auth_headers_admin_taller1)
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    
    caso_encontrado = None
    for c in data_get["casos"]:
        if c["item"] == post_item:
            caso_encontrado = c
            break

    assert caso_encontrado is not None
    # El hash retornado en GET debe ser idéntico al persistido en el POST
    assert caso_encontrado["placa_hash"] == post_hash
    assert caso_encontrado["placa_enmascarada"] == "DEF-***"


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


def test_bloqueo_interproceso_timeout_devuelve_503(auth_headers_admin_taller1, mock_tracker_csv):
    """Verifica que si un proceso activo retiene el archivo de bloqueo .lock, el endpoint responde HTTP 503."""
    lock_file = mock_tracker_csv.with_suffix(".lock")
    # Crear lockfile manual con PID actual para simular proceso activo ocupado
    fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
    try:
        os.write(fd, f"{os.getpid()}:{time.time()}\n".encode("utf-8"))
    finally:
        os.close(fd)

    try:
        payload = {
            "fase": "Post-test",
            "fecha": "2026-08-17",
            "placa": "LCK-001",
            "marca_modelo": "Lock Test Car",
            "sintoma": "Sintoma de prueba bloqueo",
            "falla_real": "Falla prueba bloqueo",
            "chatbot_prediccion": "Prediccion",
            "campos_completos": 1,
            "tiempo_diagnostico_minutos": 10,
            "prediccion_correcta": 1,
        }
        # Intentar POST mientras el lock está tomado (con timeout corto)
        resp = client.post("/api/v1/validacion-taller", json=payload, headers=auth_headers_admin_taller1)
        assert resp.status_code == 503
        assert "ocupado" in resp.json()["detail"].lower()
    finally:
        if lock_file.exists():
            try:
                lock_file.unlink()
            except Exception:
                pass


def test_bloqueo_interproceso_auto_recuperacion_lock_abandonado(mock_tracker_csv):
    """Verifica que un lock abandonado con PID muerto se auto-recupere sin saturar."""
    lock_file = mock_tracker_csv.with_suffix(".lock")
    # Simular lock huérfano con PID inexistente
    fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
    try:
        os.write(fd, b"99999999:1000.0\n")
    finally:
        os.close(fd)

    # Debe auto-recuperar y adquirir el lock sin lanzar TimeoutError
    with _bloqueo_archivo_interproceso(mock_tracker_csv, timeout=2.0):
        assert lock_file.exists()


@pytest.mark.anyio
async def test_concurrencia_escrituras_atomicas(auth_headers_admin_taller1, mock_tracker_csv):
    """Verifica que múltiples corrutinas concurrentes se ejecuten atómicamente sin pérdida de datos."""
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


def test_concurrencia_multiproceso_real_os(mock_tracker_csv):
    """Verifica concurrencia real entre procesos de sistema operativo independientes."""
    csv_str = str(mock_tracker_csv)
    with ProcessPoolExecutor(max_workers=4) as executor:
        resultados = list(executor.map(_worker_escribir_proceso, [csv_str] * 4, [101, 102, 103, 104]))

    assert all(r is True for r in resultados)
    df_res = pd.read_csv(mock_tracker_csv)
    # 3 iniciales + 4 procesos OS = 7 filas
    assert len(df_res) == 7
    assert len(df_res["item"].unique()) == 7


def test_mecanico_no_puede_acceder_validacion(auth_headers_mecanico):
    """Verifica control de acceso basado en roles (403 para mecánicos)."""
    resp_metricas = client.get("/api/v1/validacion-taller/metricas", headers=auth_headers_mecanico)
    assert resp_metricas.status_code == 403

    resp_listado = client.get("/api/v1/validacion-taller", headers=auth_headers_mecanico)
    assert resp_listado.status_code == 403

    resp_csv = client.get("/api/v1/validacion-taller/exportar-csv", headers=auth_headers_mecanico)
    assert resp_csv.status_code == 403
