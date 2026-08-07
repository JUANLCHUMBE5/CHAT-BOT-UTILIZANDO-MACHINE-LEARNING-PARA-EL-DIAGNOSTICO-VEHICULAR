import hmac
import hashlib
import json
from fastapi.testclient import TestClient
from main import app
from src.core.security import crear_jwt_token
from src.config import settings

client = TestClient(app)

# ==========================================
# TIER 1: AUTH & API ENDPOINT TESTS
# ==========================================

def test_login_y_obtencion_token_jwt():
    """T1-AUTH: Valid credentials issue a 2-hour expiring Bearer JWT token."""
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "carbot2026"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in_seconds"] == 7200

def test_login_credenciales_invalidas():
    """T1-AUTH: Incorrect username/password returns 401 Unauthorized."""
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 401
    assert "Credenciales" in response.json()["detail"]

def test_endpoint_diagnostico_sin_token_retorna_401():
    """T1-AUTH: Unauthenticated request to /diagnostico/analizar returns HTTP 401."""
    response = client.post("/api/v1/diagnostico/analizar", json={"sintoma": "freno esponjoso"})
    assert response.status_code == 401

def test_endpoint_diagnostico_con_token_jwt_valido():
    """T1-AUTH: Authenticated request with valid JWT token executes diagnosis successfully."""
    token = crear_jwt_token(sub="admin")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "sintoma": "pastillas de freno chillan al frenar",
        "marca": "Toyota",
        "modelo": "Yaris",
        "placa": "ABC-123"
    }
    response = client.post("/api/v1/diagnostico/analizar", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "falla_predicha" in data
    assert "respuesta_explicativa" in data
    assert data["confianza"] > 0.0

# ==========================================
# TIER 1: WEBHOOK ENDPOINT TESTS
# ==========================================

def test_webhook_verificacion_meta():
    """T1-WEBHOOK: GET /webhook responds to valid Meta verification challenge handshake."""
    token_esperado = getattr(settings, "META_VERIFY_TOKEN", getattr(settings, "VERIFY_TOKEN", "carbot_verify_token_ucv_2026"))
    response = client.get(f"/api/v1/webhook?hub.mode=subscribe&hub.verify_token={token_esperado}&hub.challenge=CHALLENGE_CODE")
    assert response.status_code == 200
    assert response.text == "CHALLENGE_CODE"

def test_webhook_get_verify_token_invalido():
    """T1-WEBHOOK: GET /webhook returns HTTP 403 Forbidden on invalid verify token."""
    response = client.get("/api/v1/webhook?hub.mode=subscribe&hub.verify_token=BAD_TOKEN&hub.challenge=CHALLENGE_CODE")
    assert response.status_code == 403
    assert "Token de verificación inválido" in response.json()["detail"] or "incorrecto" in response.json()["detail"]

def test_webhook_post_firma_hmac_valida(monkeypatch):
    """T1-WEBHOOK: POST /webhook accepts valid HMAC SHA-256 signature."""
    monkeypatch.setattr(settings, "META_APP_SECRET", "test_secret_key_123")
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "51987654321",
                        "type": "text",
                        "text": {"body": "mi carro no arranca por la mañana"}
                    }]
                }
            }]
        }]
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(b"test_secret_key_123", raw_body, hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={sig}"
    }
    response = client.post("/api/v1/webhook", content=raw_body, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "procesado"

def test_webhook_post_firma_hmac_invalida(monkeypatch):
    """T1-WEBHOOK: POST /webhook rejects invalid HMAC SHA-256 signature with 401 Unauthorized."""
    monkeypatch.setattr(settings, "META_APP_SECRET", "test_secret_key_123")
    payload = {"sintoma": "freno duro"}
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": "sha256=invalid_signature_hex"
    }
    response = client.post("/api/v1/webhook", json=payload, headers=headers)
    assert response.status_code == 401
    assert "Firma de webhook inválida" in response.json()["detail"]

def test_webhook_post_payload_whatsapp_text(monkeypatch):
    """T1-WEBHOOK: POST /webhook/meta processes standard WhatsApp text payload structure with valid signature."""
    monkeypatch.setattr(settings, "META_APP_SECRET", "test_secret_key_123")
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "51999888777",
                        "type": "text",
                        "text": {"body": "el timon tiembla cuando corro a 80 km/h"}
                    }]
                }
            }]
        }]
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(b"test_secret_key_123", raw_body, hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={sig}"
    }
    response = client.post("/api/v1/webhook/meta", content=raw_body, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "procesado"
    assert data["tiempo_respuesta_ms"] >= 0.0


def test_webhook_meta_ignora_evento_de_estado(monkeypatch):
    """Los recibos de entrega de Meta no deben crear una consulta diagnóstica."""
    monkeypatch.setattr(settings, "META_APP_SECRET", "test_secret_key_123")
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "statuses": [{"id": "wamid.estado", "status": "delivered"}]
                }
            }]
        }]
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(b"test_secret_key_123", raw_body, hashlib.sha256).hexdigest()
    response = client.post(
        "/api/v1/webhook/meta",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": f"sha256={sig}",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "evento_ignorado"

def test_webhook_twilio_endpoint_con_firma_valida(monkeypatch):
    """T1-WEBHOOK: POST /webhook/twilio processes Twilio form payload with valid X-Twilio-Signature."""
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "test_twilio_token_999")
    import base64
    url = "http://testserver/api/v1/webhook/twilio"
    form_data = {"From": "whatsapp:+51987654321", "Body": "freno duro al pisar el pedal"}
    
    expected_str = url + "Bodyfreno duro al pisar el pedal" + "Fromwhatsapp:+51987654321"
    mac = hmac.new(b"test_twilio_token_999", expected_str.encode("utf-8"), hashlib.sha1)
    sig = base64.b64encode(mac.digest()).decode("utf-8")
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Twilio-Signature": sig
    }
    response = client.post("/api/v1/webhook/twilio", data=form_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "procesado"
    assert data["proveedor"] == "Twilio"
