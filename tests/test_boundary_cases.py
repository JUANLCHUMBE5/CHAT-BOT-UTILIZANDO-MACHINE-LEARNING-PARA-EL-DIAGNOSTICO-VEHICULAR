import time

import jwt
import pytest
from fastapi.testclient import TestClient
from main import app
from src.core.security import crear_jwt_token, JWT_SECRET_KEY, JWT_ALGORITHM
from src.core.sanitizer import sanitizar_prompt_usuario
from src.core.gestor_diagnostico import GestorDiagnostico
from src.infrastructure.container import ServiceContainer
from src.config import settings

client = TestClient(app)

# ==========================================
# TIER 2: BOUNDARY & CORNER CASE TESTS
# ==========================================

def test_jwt_token_expirado_retorna_401():
    """T2-BOUNDARY: Expired JWT token (exp in past) returns HTTP 401 Unauthorized."""
    past_time = int(time.time()) - 100
    expired_payload = {
        "sub": "user_expired",
        "iat": past_time - 7200,
        "exp": past_time,
        "iss": "CarBot-API-V1"
    }
    expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    headers = {"Authorization": f"Bearer {expired_token}"}
    
    response = client.post("/api/v1/diagnostico/analizar", json={"sintoma": "freno esponjoso"}, headers=headers)
    assert response.status_code == 401
    assert "expirado" in response.json()["detail"].lower()

def test_jwt_token_firma_alterada_o_alg_invalido():
    """T2-BOUNDARY: JWT signed with wrong secret key returns HTTP 401 Unauthorized."""
    fake_token = jwt.encode({"sub": "hacker", "exp": int(time.time()) + 3600}, "wrong_secret_key", algorithm="HS256")
    headers = {"Authorization": f"Bearer {fake_token}"}
    
    response = client.post("/api/v1/diagnostico/analizar", json={"sintoma": "freno esponjoso"}, headers=headers)
    assert response.status_code == 401
    assert "inválido" in response.json()["detail"].lower() or "alterada" in response.json()["detail"].lower()

def test_webhook_post_firma_hmac_invalida_retorna_401(monkeypatch):
    """T2-BOUNDARY: POST /webhook with corrupted HMAC SHA-256 signature returns HTTP 401 Unauthorized."""
    monkeypatch.setattr(settings, "META_APP_SECRET", "enforce_secret_999")
    payload = {"entry": []}
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": "sha256=invalid_hex_signature_string"
    }
    
    response = client.post("/api/v1/webhook", json=payload, headers=headers)
    assert response.status_code == 401
    assert "inválida" in response.json()["detail"].lower()

def test_diagnostico_sintoma_vacio_retorna_400():
    """T2-BOUNDARY: POST /diagnostico/analizar with empty symptom text returns HTTP 400 Bad Request."""
    token = crear_jwt_token(sub="admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test empty string
    res1 = client.post("/api/v1/diagnostico/analizar", json={"sintoma": ""}, headers=headers)
    assert res1.status_code == 400
    
    # Test whitespace string
    res2 = client.post("/api/v1/diagnostico/analizar", json={"sintoma": "   \n\t  "}, headers=headers)
    assert res2.status_code == 400

def test_diagnostico_sintoma_supera_limite_caracteres():
    """T2-BOUNDARY: Symptom text exceeding 500 characters is rejected by Pydantic max_length schema validation (HTTP 422)."""
    token = crear_jwt_token(sub="admin")
    headers = {"Authorization": f"Bearer {token}"}
    
    long_symptom = "pastillas de freno chillan seco " * 30  # > 600 chars
    assert len(long_symptom) > 500
    
    response = client.post("/api/v1/diagnostico/analizar", json={"sintoma": long_symptom}, headers=headers)
    assert response.status_code == 422
    # Verify core sanitization truncates to max_length 500
    sanitized = sanitizar_prompt_usuario(long_symptom, max_length=500)
    assert len(sanitized) == 500


def test_ml_rag_input_gibberish_o_bajo_umbral():
    """T2-BOUNDARY: Gibberish input without mechanical keywords triggers low confidence / ambiguity flag."""
    gestor = GestorDiagnostico()
    gibberish = "qwertyuiop asdfghjkl zxcvbnm 123456789"
    res = gestor.procesar_consulta_texto(texto_usuario=gibberish)
    
    assert res.requiere_revision_humana is True
    assert res.confianza_ml < 50.0 or "ambigua" in res.respuesta_texto.lower() or "detalle" in res.respuesta_texto.lower()

def test_ml_rag_dtc_codigo_desconocido():
    """T2-BOUNDARY: Non-existent DTC fault code ('P9999') handles gracefully without throwing exceptions."""
    motor_rag = ServiceContainer.get_motor_rag()
    manual_texto, titulo = motor_rag.recuperar_contexto("DTC P9999 falla desconocida")
    assert isinstance(titulo, str)
    assert isinstance(manual_texto, str)


def test_audio_sin_muestras_reales_no_se_simula():
    gestor = GestorDiagnostico()
    with pytest.raises(ValueError, match="muestras reales"):
        gestor.procesar_consulta_audio("identificador-remoto", None)
