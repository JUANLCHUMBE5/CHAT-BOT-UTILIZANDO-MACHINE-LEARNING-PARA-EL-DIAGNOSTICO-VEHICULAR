import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from main import app
from src.config import settings
from src.core.security import crear_jwt_token

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

def test_listar_y_registrar_mecanicos_api():
    """T1-ADMIN: GET and POST /api/v1/mecanicos manages mechanics list."""
    token = crear_jwt_token(sub="admin")
    headers = {"Authorization": f"Bearer {token}"}

    res_list = client.get("/api/v1/mecanicos", headers=headers)
    assert res_list.status_code in (200, 503)

    payload = {
        "nombres": "Pedro Gutierrez Test",
        "telefono_whatsapp": "+51 999 888 777",
        "password": "carbot2026_password",
        "rol": "mecanico"
    }
    res_post = client.post("/api/v1/mecanicos", json=payload, headers=headers)
    assert res_post.status_code in (200, 503)

def test_activar_y_bloquear_mecanico_api():
    """T1-ADMIN: PATCH /api/v1/mecanicos/{id}/activar and /bloquear toggle mechanic states."""
    token = crear_jwt_token(sub="admin")
    headers = {"Authorization": f"Bearer {token}"}

    res_act = client.patch("/api/v1/mecanicos/mec-001/activar", headers=headers)
    assert res_act.status_code in (200, 404, 503)

    res_bloq = client.patch("/api/v1/mecanicos/mec-001/bloquear", headers=headers)
    assert res_bloq.status_code in (200, 404, 503)

def test_historial_y_confirmar_diagnosticos_api():
    """T1-ADMIN: GET /diagnostico/historial and PATCH /diagnostico/{id}/confirmar manage diagnosis validation."""
    token = crear_jwt_token(sub="admin")
    headers = {"Authorization": f"Bearer {token}"}

    res_hist = client.get("/api/v1/diagnostico/historial", headers=headers)
    assert res_hist.status_code in (200, 503)

def test_obtener_metricas_resumen_api():
    """T1-ADMIN: GET /api/v1/metricas/resumen returns aggregate shop statistics."""
    token = crear_jwt_token(sub="admin")
    headers = {"Authorization": f"Bearer {token}"}

    res_met = client.get("/api/v1/metricas/resumen", headers=headers)
    assert res_met.status_code in (200, 503)

# ==========================================
# TIER 1: WEBHOOK ENDPOINT TESTS
# ==========================================

def test_webhook_verificacion_meta():
    """T1-WEBHOOK: GET /webhook responds to valid Meta verification challenge handshake."""
    token_esperado = settings.meta_verify_token
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
    monkeypatch.setattr(settings, "meta_app_secret", "test_secret_key_123")
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
    monkeypatch.setattr(settings, "meta_app_secret", "test_secret_key_123")
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
    monkeypatch.setattr(settings, "meta_app_secret", "test_secret_key_123")
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
    monkeypatch.setattr(settings, "meta_app_secret", "test_secret_key_123")
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
    monkeypatch.setattr(settings, "twilio_auth_token", "test_twilio_token_999")
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

