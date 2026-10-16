"""Pruebas del Laboratorio Web de Pruebas CarBot.

Valida:
1. Bloqueo estricto en entorno productivo (403 Forbidden).
2. Procesamiento de mensajes reales a través del GestorDiagnostico.
3. Reinicio de sesión de prueba.
4. Reproducción automatizada de casos (Toyota Yaris y Nissan Sentra).
5. Inspección de estado: placa, síntomas, negaciones, limitaciones, SVM y RAG.
6. Aprobación de comprobaciones automáticas de calidad.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.config import settings
from src.interfaces.api.v1.endpoints.laboratorio_local.app import create_laboratory_app

app = create_laboratory_app()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from src.config import settings
    from src.core.security import crear_jwt_token

    monkeypatch.setattr(settings, "enable_laboratory", True)
    monkeypatch.setenv("CARBOT_BLOCK_DOTENV", "true")
    global app
    app = create_laboratory_app()
    token = crear_jwt_token(usuario_id="00000000-0000-0000-0000-000000000021")
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


def test_laboratorio_bloqueado_en_produccion(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifica que cualquier llamada a /laboratorio sea rechazada con 403 si el entorno es producción."""
    monkeypatch.setattr(settings, "environment", "production")

    response = client.post(
        "/api/v1/laboratorio/mensaje",
        json={"mensaje": "Hola CarBot", "session_id": "test_prod"},
    )
    assert response.status_code == 403
    detail = response.json()["detail"].lower()
    assert "deshabilitado" in detail
    assert "producci" in detail


def test_laboratorio_mensaje_y_estado(client: TestClient) -> None:
    """Ejecuta un mensaje real y verifica la inspección de estado y comprobaciones."""
    session_id = "test_lab_session_1"

    # Enviar mensaje con vehículo y síntomas
    msg = (
        "Mi vehículo es un Toyota Yaris 2020, placa ABC123. "
        "Cuando freno escucho un chirrido en las ruedas delanteras y siento que el pedal vibra."
    )
    response = client.post(
        "/api/v1/laboratorio/mensaje",
        json={"mensaje": msg, "session_id": session_id},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["session_id"] == session_id
    assert len(data["respuesta_texto"]) > 0
    assert data["placa"] in ("ABC123", "ABC-123")
    assert "TOYOTA" in data["vehiculo"].upper()
    assert len(data["sintomas_confirmados"]) > 0

    # Comprobaciones automáticas
    comprobaciones = {c["criterio"]: c for c in data["comprobaciones"]}
    assert "Captura y persistencia de placa" in comprobaciones
    assert comprobaciones["Captura y persistencia de placa"]["resultado"] == "APROBADO"


def test_laboratorio_reinicio_sesion(client: TestClient) -> None:
    """Verifica que reiniciar limpie la sesión de prueba."""
    session_id = "test_lab_session_reinicio"

    client.post(
        "/api/v1/laboratorio/mensaje",
        json={"mensaje": "Mi vehículo es un Toyota Yaris 2020, placa ABC123", "session_id": session_id},
    )

    response = client.post(f"/api/v1/laboratorio/reiniciar?session_id={session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_laboratorio_ejecutar_caso_toyota(client: TestClient) -> None:
    """Verifica la reproducción automatizada del caso Toyota Yaris de 3 turnos."""
    response = client.post("/api/v1/laboratorio/ejecutar-caso/toyota")
    assert response.status_code == 200
    data = response.json()

    assert data["caso"] == "toyota"
    assert len(data["resultados"]) == 3

    # El paso 2 debe reflejar negaciones y limitaciones
    paso2 = data["resultados"][1]["respuesta"]
    assert len(paso2["sintomas_negados"]) > 0
    assert len(paso2["limitaciones"]) > 0

    # Todas las comprobaciones de los pasos deben estar presentes
    comprobaciones_finales = data["resultados"][-1]["respuesta"]["comprobaciones"]
    assert any("placa" in c["criterio"].lower() and c["resultado"] == "APROBADO" for c in comprobaciones_finales)


def test_laboratorio_ejecutar_caso_nissan(client: TestClient) -> None:
    """Verifica la reproducción automatizada del caso Nissan Sentra (aislamiento y cambio de caso)."""
    response = client.post("/api/v1/laboratorio/ejecutar-caso/nissan")
    assert response.status_code == 200
    data = response.json()

    assert data["caso"] == "nissan"
    assert len(data["resultados"]) == 1

    paso1 = data["resultados"][0]["respuesta"]
    assert paso1["placa"] in ("XYZ789", "XYZ-789")
    assert "NISSAN" in paso1["vehiculo"].upper()
    assert "SENTRA" in paso1["vehiculo"].upper()

    # Comprobación de no repetición de preguntas para datos ya provistos
    comprobaciones = {c["criterio"]: c for c in paso1["comprobaciones"]}
    assert "Prevención de preguntas redundantes" in comprobaciones
    assert comprobaciones["Prevención de preguntas redundantes"]["resultado"] == "APROBADO"
