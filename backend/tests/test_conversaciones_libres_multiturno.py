"""Suite de regresión sistémica para conversaciones libres, multiturno y laboratorio web.

Valida causas estructurales:
1. Conversación libre con errores ortográficos, selección numérica ('3') y nuevos síntomas sin pérdida de memoria.
2. Escenario Toyota Yaris (ABC123): case_id persistente, fase real, negaciones específicas sin negar el sistema de frenos,
   Top-3 libre de contaminación de encendido, y consulta de memoria con 'No aplica'.
3. Escenario Nissan Sentra (XYZ789): aislamiento de caso, negación explícita del sistema de frenos,
   Top-3 exclusivo de suspensión sin contaminación de pastillas/fuga hidráulica, y alerta de seguridad vial.
4. Conversación fragmentada sin vehículo inicial y agregación progresiva de placa, síntomas y limitaciones.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.interfaces.api.v1.endpoints.laboratorio_local.app import create_laboratory_app

app = create_laboratory_app()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from src.config import settings
    from src.core.security import crear_jwt_token

    monkeypatch.setattr(settings, "enable_laboratory", True)
    monkeypatch.setattr(settings, "environment", "test")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setenv("CARBOT_BLOCK_DOTENV", "true")
    global app
    app = create_laboratory_app()
    token = crear_jwt_token(usuario_id="00000000-0000-0000-0000-000000000021")
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


def test_conversacion_libre_errores_ortograficos_y_opcion_numerica(client: TestClient) -> None:
    """Reproduce exactamente la conversación manual fallida reportada en la auditoría:
    Turn 1: 'holaa'
    Turn 2: 'tengo rpoblemas con mi vehciuelo al acelerar'
    Turn 3: '3'
    Turn 4: 'cuando va a 30 kilometros este timebla'
    """
    session_id = "test_libre_ortografia_opcion_3"

    # Turno 1: Saludo informal con letras repetidas
    r1 = client.post(
        "/api/v1/laboratorio/mensaje",
        json={"session_id": session_id, "mensaje": "holaa"},
    )
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["case_id"] is not None
    assert d1["confianza_ml"] == 0.0
    assert "no aplica" in (d1["diagnostico_ml"] or "").lower()

    # Turno 2: Síntoma con errores ortográficos ('rpoblemas', 'vehciuelo') sin placa ni marca
    r2 = client.post(
        "/api/v1/laboratorio/mensaje",
        json={"session_id": session_id, "mensaje": "tengo rpoblemas con mi vehciuelo al acelerar"},
    )
    assert r2.status_code == 200
    d2 = r2.json()
    case_id_activo = d2["case_id"]
    assert case_id_activo is not None
    assert d2["fase"].upper() != "INICIO"
    assert len(d2["sintomas_confirmados"]) > 0

    # Turno 3: Selección numérica '3' (debe conservar memoria, generar Top-3 y nunca pedir describir síntoma desde cero)
    r3 = client.post(
        "/api/v1/laboratorio/mensaje",
        json={"session_id": session_id, "mensaje": "3"},
    )
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["case_id"] == case_id_activo
    assert "describe el síntoma, por ejemplo" not in d3["respuesta_texto"].lower()
    assert len(d3["sintomas_confirmados"]) > 0
    assert len(d3["top3_actual"]) > 0

    # Turno 4: Nuevo síntoma con error ortográfico ('timebla') y velocidad ('cuando va a 30 kilometros')
    r4 = client.post(
        "/api/v1/laboratorio/mensaje",
        json={"session_id": session_id, "mensaje": "cuando va a 30 kilometros este timebla"},
    )
    assert r4.status_code == 200
    d4 = r4.json()
    assert d4["case_id"] == case_id_activo
    assert d4["fase"].upper() != "INICIO"
    assert "no dispongo de información suficientemente verificada" not in d4["respuesta_texto"].lower()
    sintomas_joined = " ".join(d4["sintomas_confirmados"]).lower()
    assert "vibración" in sintomas_joined and "potencia" in sintomas_joined

    # Turno 5: Selección numérica '3' sobre el Top-3 activo (selección provisional, no confirmación física)
    r5 = client.post(
        "/api/v1/laboratorio/mensaje",
        json={"session_id": session_id, "mensaje": "3"},
    )
    assert r5.status_code == 200
    d5 = r5.json()
    assert d5["case_id"] == case_id_activo
    assert "seleccionaste provisionalmente" in d5["respuesta_texto"].lower() or "comprobación" in d5["respuesta_texto"].lower()
    assert len(d5["sintomas_confirmados"]) >= 2


def test_toyota_yaris_semantica_frenos_negaciones_y_memoria(client: TestClient) -> None:
    """Valida todos los hallazgos semánticos del caso Toyota Yaris 2020 (ABC123)."""
    response = client.post("/api/v1/laboratorio/ejecutar-caso/toyota")
    assert response.status_code == 200
    data = response.json()
    resultados = data["resultados"]
    assert len(resultados) == 3

    t1 = resultados[0]["respuesta"]
    t2 = resultados[1]["respuesta"]
    t3 = resultados[2]["respuesta"]

    # 1. case_id no nulo y persistente en los 3 turnos; fase avanza de INICIO
    assert t1["case_id"] is not None
    assert t1["case_id"] == t2["case_id"] == t3["case_id"]
    assert t1["fase"].upper() != "INICIO"
    assert t2["fase"].upper() != "INICIO"

    # 2. Negaciones específicas: nunca debe negar 'anomalía en frenos' ni 'problemas de frenos'
    negados_t2 = [n.lower() for n in t2["sintomas_negados"]]
    assert any("esponjoso" in n or "fondo" in n for n in negados_t2)
    assert not any("anomalía en frenos" in n or "problemas de frenos" in n for n in negados_t2)

    # 3. Top-3 libre de contaminación de encendido (bujías / bobinas)
    for turno_resp in (t1, t2):
        for item in turno_resp["top3_actual"]:
            falla_l = str(item.get("falla", "")).lower()
            assert "bujía" not in falla_l and "bujia" not in falla_l
            assert "bobina" not in falla_l

    # 4. Consulta de memoria en Turno 3 debe indicar 'No aplica' y confianza 0.0
    assert t3["confianza_ml"] == 0.0
    assert "no aplica" in (t3["diagnostico_ml"] or "").lower()

    # 5. Comprobación de seguridad física aprobada
    comprobaciones_t1 = {c["criterio"]: c["resultado"] for c in t1["comprobaciones"]}
    assert comprobaciones_t1.get("Advertencia de seguridad física (frenos/suspensión/térmico)") == "APROBADO"


def test_nissan_sentra_aislamiento_y_pertinencia_suspension(client: TestClient) -> None:
    """Valida aislamiento de caso y pertinencia estricta de suspensión en Nissan Sentra 2021 (XYZ789)."""
    session_id = "test_transicion_toyota_a_nissan"

    # Primero registrar caso Toyota
    r_toyota = client.post(
        "/api/v1/laboratorio/mensaje",
        json={
            "session_id": session_id,
            "mensaje": (
                "Mi vehículo es un Toyota Yaris 2020, placa ABC123. "
                "Cuando freno escucho un chirrido en las ruedas delanteras y siento que el pedal vibra."
            ),
        },
    )
    assert r_toyota.status_code == 200
    d_toyota = r_toyota.json()
    case_toyota = d_toyota["case_id"]
    assert case_toyota is not None

    # Ahora enviar cambio a Nissan Sentra negando problemas de frenos y reportando suspensión
    r_nissan = client.post(
        "/api/v1/laboratorio/mensaje",
        json={
            "session_id": session_id,
            "mensaje": (
                "Quiero iniciar un diagnóstico nuevo para otro vehículo. "
                "Es un Nissan Sentra 2021, placa XYZ789. No presenta problemas de frenos. "
                "Escucho golpes metálicos en la suspensión delantera cuando paso por baches. "
                "¿Qué podría estar fallando?"
            ),
        },
    )
    assert r_nissan.status_code == 200
    d_nissan = r_nissan.json()

    # Aislamiento de case_id y vehículo
    assert d_nissan["case_id"] is not None
    assert d_nissan["case_id"] != case_toyota
    assert d_nissan["placa"] in ("XYZ789", "XYZ-789")
    assert "NISSAN" in (d_nissan["vehiculo"] or "").upper()
    assert d_nissan["fase"].upper() != "INICIO"

    # Síntomas confirmados de suspensión y sin residuos de Toyota
    confirmados_l = " ".join(d_nissan["sintomas_confirmados"]).lower()
    assert "suspensión" in confirmados_l or "ruido" in confirmados_l
    assert "chirrido en ruedas" not in confirmados_l

    # Pertinencia de hipótesis: cero pastillas de freno o fuga hidráulica de frenos
    assert len(d_nissan["top3_actual"]) > 0
    for item in d_nissan["top3_actual"]:
        falla_l = str(item.get("falla", "")).lower()
        assert "pastilla" not in falla_l
        assert "freno" not in falla_l
        assert "caliper" not in falla_l and "cáliper" not in falla_l

    # Comprobación de seguridad y aislamiento aprobadas
    comprobaciones = {c["criterio"]: c["resultado"] for c in d_nissan["comprobaciones"]}
    assert comprobaciones.get("Aislamiento estricto de case_id") == "APROBADO"
    assert comprobaciones.get("Advertencia de seguridad física (frenos/suspensión/térmico)") == "APROBADO"


def test_conversacion_fragmentada_progresiva_sin_perdida_contexto(client: TestClient) -> None:
    """Verifica que síntomas reportados antes de identificar el vehículo se conserven al agregar placa y limitaciones."""
    session_id = "test_fragmentada_progresiva"

    # Turno 1: Síntoma inicial sin datos de vehículo
    r1 = client.post(
        "/api/v1/laboratorio/mensaje",
        json={"session_id": session_id, "mensaje": "Cuando paso por baches suena un golpe seco adelante"},
    )
    assert r1.status_code == 200
    d1 = r1.json()
    cid = d1["case_id"]
    assert cid is not None
    assert len(d1["sintomas_confirmados"]) > 0

    # Turno 2: Usuario proporciona vehículo y placa después
    r2 = client.post(
        "/api/v1/laboratorio/mensaje",
        json={"session_id": session_id, "mensaje": "Es un Hyundai Accent 2019, placa MNP456"},
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["case_id"] == cid
    assert d2["placa"] in ("MNP456", "MNP-456")
    assert "HYUNDAI" in (d2["vehiculo"] or "").upper()
    assert len(d2["sintomas_confirmados"]) > 0

    # Turno 3: Usuario reporta limitación de herramientas
    r3 = client.post(
        "/api/v1/laboratorio/mensaje",
        json={"session_id": session_id, "mensaje": "No tengo elevador ni puedo desmontar las ruedas"},
    )
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["case_id"] == cid
    assert d3["placa"] in ("MNP456", "MNP-456")
    assert len(d3["sintomas_confirmados"]) > 0
    assert len(d3["limitaciones"]) > 0
