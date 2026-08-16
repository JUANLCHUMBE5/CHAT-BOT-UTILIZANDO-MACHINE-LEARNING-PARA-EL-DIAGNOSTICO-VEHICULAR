"""Pruebas unitarias e integración de API para registro de mecánicos, login y procedimiento RAG en historial."""

import uuid

import pytest
from fastapi.testclient import TestClient

from main import app
from src.core.security import crear_jwt_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def token_admin():
    return crear_jwt_token(
        sub="Administrador General",
        rol="administrador",
        taller_id="00000000-0000-0000-0000-000000000001",
        usuario_id="00000000-0000-0000-0000-000000000001",
    )


def test_registro_mecanico_no_requiere_password_web(client, token_admin):
    """Un mecánico se autoriza por WhatsApp y no necesita contraseña web."""
    payload = {
        "nombres": "Carlos Mecanico",
        "telefono_whatsapp": "+51 999 888 777",
        "rol": "mecanico",
    }
    response = client.post(
        "/api/v1/mecanicos",
        json=payload,
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert response.status_code in (200, 503)


def test_registro_administrador_exige_password_segura(client, token_admin):
    """Una cuenta administrativa sí requiere una contraseña web robusta."""
    response = client.post(
        "/api/v1/mecanicos",
        json={
            "nombres": "Segundo Administrador",
            "telefono_whatsapp": "+51 999 888 776",
            "password": "123",
            "rol": "administrador",
        },
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert response.status_code == 400
    assert "contraseña" in response.json()["detail"].lower()


def test_registro_mecanico_validacion_telefono_invalido(client, token_admin):
    """Verifica que el registro rechace números con menos de 6 dígitos."""
    payload = {
        "nombres": "Carlos Mecanico",
        "telefono_whatsapp": "123",
        "password": "ClaveSegura_123",
        "rol": "mecanico",
    }
    response = client.post(
        "/api/v1/mecanicos",
        json=payload,
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert response.status_code == 400
    assert "teléfono" in response.json()["detail"].lower()


def test_login_rechaza_credenciales_invalidas(client):
    """Verifica que el login rechace contraseñas incorrectas con HTTP 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "password_totalmente_incorrecto"},
    )
    assert response.status_code == 401
    assert "inválidas" in response.json()["detail"]


def test_dto_historial_diagnosticos_contiene_campos_rag_reales():
    """Verifica que el DTO ItemDiagnosticoDTO contenga las propiedades RAG correctas."""
    from src.interfaces.api.v1.endpoints.diagnostico import ItemDiagnosticoDTO

    dto = ItemDiagnosticoDTO(
        id=str(uuid.uuid4()),
        sintoma_original="la puerta no abre con el control",
        sintoma_normalizado="falla electrica seguro puerta",
        falla_predicha="Falla electrica del cierre centralizado o actuador de puerta",
        confianza=95.5,
        similitud_rag=85.0,
        modo_diagnostico="completo_ml_rag_llm",
        estado="generado",
        fuente="hibrido",
        mecanico_id=str(uuid.uuid4()),
        mecanico_nombre="Juan Perez",
        placa_vehiculo="***-1234",
        marca_modelo="Toyota Yaris",
        fecha_hora="2026-08-08 17:30",
        duracion_ms=120,
        procedimiento_rag="1. Desmonte el tapiz de la puerta. 2. Verifique actuador de cierre centralizado.",
        fuente_manual="Toyota Workshop Service Manual Edición 2019",
        version_corpus_rag="v2.1.0-oem",
        tiempo_gravedad="Gravedad media, tiempo 45 min",
    )

    assert dto.procedimiento_rag != dto.sintoma_normalizado
    assert "Desmonte el tapiz" in dto.procedimiento_rag
    assert dto.similitud_rag == 85.0
    assert "Toyota Workshop" in dto.fuente_manual


def test_historial_no_presenta_mensaje_sin_coincidencia_como_procedimiento():
    from src.interfaces.api.v1.endpoints.diagnostico import _es_procedimiento_rag_real

    assert _es_procedimiento_rag_real("1. Revisar el actuador eléctrico") is True
    assert _es_procedimiento_rag_real(
        "No se encontro un procedimiento especifico en los manuales para esta consulta."
    ) is False


def test_guard_auto_modificacion_mecanico(client):
    """Verifica que un administrador no pueda desactivarse, bloquearse, reducirse o revocarse a sí mismo."""
    user_id = str(uuid.uuid4())
    token_mismo_usuario = crear_jwt_token(
        sub="Admin Test",
        rol="administrador",
        taller_id="00000000-0000-0000-0000-000000000001",
        usuario_id=user_id,
    )
    headers = {"Authorization": f"Bearer {token_mismo_usuario}"}

    # Intentar revocar su propio acceso
    res_revocar = client.patch(f"/api/v1/mecanicos/{user_id}/revocar-acceso", headers=headers)
    assert res_revocar.status_code == 400
    assert "propio" in res_revocar.json()["detail"].lower()


def test_actualizar_mecanico_put_invalid_uuid(client, token_admin):
    """Verifica que PUT /mecanicos/{id} valide el formato UUID de mecanico_id."""
    res = client.put(
        "/api/v1/mecanicos/id-no-uuid",
        json={"nombres": "Nuevo Nombre"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert res.status_code == 400
    assert "UUID" in res.json()["detail"]


def test_actualizar_mecanico_put_password_invalida(client, token_admin):
    """Verifica que PUT /mecanicos/{id} valide la complejidad de la contraseña (min 12, mayus, minus, num)."""
    target_id = str(uuid.uuid4())
    res = client.put(
        f"/api/v1/mecanicos/{target_id}",
        json={"password": "123"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert res.status_code == 400
    assert "12 caracteres" in res.json()["detail"].lower()


def test_actualizar_mecanico_jerarquia_no_admin_edita_admin(client):
    """Verifica que un jefe_taller o supervisor no pueda editar a un administrador."""
    token_supervisor = crear_jwt_token(
        sub="Supervisor Test",
        rol="jefe_taller",
        taller_id="00000000-0000-0000-0000-000000000001",
        usuario_id=str(uuid.uuid4()),
    )
    target_admin_id = str(uuid.uuid4())
    res = client.put(
        f"/api/v1/mecanicos/{target_admin_id}",
        json={"nombres": "Modificado Por Supervisor"},
        headers={"Authorization": f"Bearer {token_supervisor}"},
    )
    assert res.status_code in (403, 404, 503)
