"""
Suite de Pruebas de Integración y E2E para Edición de Perfil de Mecánico.
Endpoint: PUT /api/v1/mecanicos/{mecanico_id}

Cubre:
- Tier 1: Edición exitosa (200 OK) de nombres, teléfono WhatsApp y contraseña; verificación de cambios en DB y re-cifrado Fernet en identidades_whatsapp.
- Tier 2: Validaciones de robustez de contraseña (400 Bad Request), validación de teléfono (400 Bad Request), colisión por teléfono duplicado (409 Conflict) y jerarquía de roles (403 Forbidden).
- Tier 3: Verificación de registro de auditoría en la tabla auditoria_operaciones con detalles de los campos modificados.
- Tier 4: Casos de borde (actualizaciones parciales, UUID malformado 400 Bad Request, mecánico no encontrado 404 Not Found, peticiones no autenticadas 401 Unauthorized, nombre en blanco 400 Bad Request).
"""

import re
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from src.core.security import (
    cifrar_texto_reversible,
    crear_jwt_token,
    descifrar_texto_reversible,
    hash_identificador_persistencia,
    verificar_password,
)
from src.infrastructure.database.models import Auditoria, IdentidadWhatsApp, Usuario
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.identidad_whatsapp_repository import IdentidadWhatsAppRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository



@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_user_id():
    return str(uuid.uuid4())


@pytest.fixture
def jefe_user_id():
    return str(uuid.uuid4())


@pytest.fixture
def mecanico_user_id():
    return str(uuid.uuid4())


@pytest.fixture
def test_taller_id():
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def token_admin(admin_user_id, test_taller_id):
    return crear_jwt_token(
        sub="Admin General",
        rol="administrador",
        taller_id=test_taller_id,
        usuario_id=admin_user_id,
    )


@pytest.fixture
def token_jefe(jefe_user_id, test_taller_id):
    return crear_jwt_token(
        sub="Jefe Taller",
        rol="jefe_taller",
        taller_id=test_taller_id,
        usuario_id=jefe_user_id,
    )


@pytest.fixture
def token_mecanico(mecanico_user_id, test_taller_id):
    return crear_jwt_token(
        sub="Mecanico Simple",
        rol="mecanico",
        taller_id=test_taller_id,
        usuario_id=mecanico_user_id,
    )


# ==============================================================================
# TIER 4 & SEGURIDAD GENERAL: Autenticación, formato de UUID y permisos base
# ==============================================================================

def test_actualizar_perfil_requiere_autenticacion(client, mecanico_user_id):
    """Verifica que peticiones sin token JWT retornen HTTP 401 Unauthorized."""
    payload = {
        "nombres": "Nuevo Nombre",
        "telefono_whatsapp": "+51 987 654 321",
    }
    response = client.put(f"/api/v1/mecanicos/{mecanico_user_id}", json=payload)
    assert response.status_code == 401


def test_actualizar_perfil_uuid_invalido(client, token_admin):
    """Verifica que un mecanico_id no UUID retorne HTTP 400 Bad Request."""
    payload = {"nombres": "Nombre Valido"}
    headers = {"Authorization": f"Bearer {token_admin}"}
    response = client.put("/api/v1/mecanicos/id-no-uuid-12345", json=payload, headers=headers)
    assert response.status_code == 400
    assert "UUID inválido" in response.json()["detail"]


def test_actualizar_perfil_rol_no_administrativo_rechazado(client, token_mecanico, mecanico_user_id):
    """Verifica que un usuario con rol 'mecanico' (no administrativo) reciba HTTP 403 Forbidden."""
    payload = {"nombres": "Intento Por Mecanico"}
    headers = {"Authorization": f"Bearer {token_mecanico}"}
    response = client.put(f"/api/v1/mecanicos/{mecanico_user_id}", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Se requiere rol administrativo" in response.json()["detail"]


# ==============================================================================
# TIER 2: Validación de Contraseñas, Nombres y Formato de Teléfono
# ==============================================================================

def test_actualizar_perfil_validacion_password_corta(client, token_admin, mecanico_user_id):
    """Verifica que contraseñas de menos de 12 caracteres sean rechazadas con HTTP 400."""
    payload = {"password": "Short123!"}
    headers = {"Authorization": f"Bearer {token_admin}"}
    response = client.put(f"/api/v1/mecanicos/{mecanico_user_id}", json=payload, headers=headers)
    assert response.status_code == 400
    assert "12 caracteres" in response.json()["detail"].lower()


def test_actualizar_perfil_validacion_password_sin_mayuscula(client, token_admin, mecanico_user_id):
    """Verifica que contraseñas sin mayúsculas sean rechazadas con HTTP 400."""
    payload = {"password": "clavemecanico12345"}
    headers = {"Authorization": f"Bearer {token_admin}"}
    response = client.put(f"/api/v1/mecanicos/{mecanico_user_id}", json=payload, headers=headers)
    assert response.status_code == 400
    assert "mayúsculas" in response.json()["detail"].lower()


def test_actualizar_perfil_validacion_password_sin_minuscula(client, token_admin, mecanico_user_id):
    """Verifica que contraseñas sin minúsculas sean rechazadas con HTTP 400."""
    payload = {"password": "CLAVEMECANICO12345"}
    headers = {"Authorization": f"Bearer {token_admin}"}
    response = client.put(f"/api/v1/mecanicos/{mecanico_user_id}", json=payload, headers=headers)
    assert response.status_code == 400
    assert "minúsculas" in response.json()["detail"].lower()


def test_actualizar_perfil_validacion_password_sin_numero(client, token_admin, mecanico_user_id):
    """Verifica que contraseñas sin dígitos numericos sean rechazadas con HTTP 400."""
    payload = {"password": "ClaveMecanicoSinNumeros"}
    headers = {"Authorization": f"Bearer {token_admin}"}
    response = client.put(f"/api/v1/mecanicos/{mecanico_user_id}", json=payload, headers=headers)
    assert response.status_code == 400
    assert "números" in response.json()["detail"].lower()


def test_actualizar_perfil_validacion_telefono_corto(client, token_admin, mecanico_user_id):
    """Verifica que un número de teléfono con menos de 6 dígitos retorne HTTP 400 Bad Request."""
    payload = {"telefono_whatsapp": "12345"}
    headers = {"Authorization": f"Bearer {token_admin}"}
    response = client.put(f"/api/v1/mecanicos/{mecanico_user_id}", json=payload, headers=headers)
    assert response.status_code == 400
    assert "6 dígitos" in response.json()["detail"].lower()


def test_actualizar_perfil_validacion_nombre_vacio(client, token_admin, mecanico_user_id):
    """Verifica que un nombre compuesto únicamente por espacios en blanco retorne HTTP 400 Bad Request."""
    payload = {"nombres": "   "}
    headers = {"Authorization": f"Bearer {token_admin}"}
    response = client.put(f"/api/v1/mecanicos/{mecanico_user_id}", json=payload, headers=headers)
    assert response.status_code == 400
    assert "vacío" in response.json()["detail"].lower()


def test_actualizar_perfil_validacion_username_invalido(client, token_admin, mecanico_user_id):
    """Verifica que un nombre de usuario con formato inválido o menor a 3 caracteres retorne HTTP 400."""
    payload = {"username": "ab"}
    headers = {"Authorization": f"Bearer {token_admin}"}
    response = client.put(f"/api/v1/mecanicos/{mecanico_user_id}", json=payload, headers=headers)
    assert response.status_code == 400
    assert "3 caracteres" in response.json()["detail"].lower()


# ==============================================================================
# TIER 1, 2, 3 & 4: Pruebas E2E de Base de Datos (Requiere PostgreSQL habilitado)
# ==============================================================================

@pytest.mark.anyio
async def test_actualizar_perfil_e2e_exitoso_db_y_fernet_y_auditoria():
    """
    Tier 1 & Tier 3:
    1. Registra un mecánico en la BD con datos iniciales.
    2. Ejecuta PUT /api/v1/mecanicos/{mecanico_id} actualizando nombres, teléfono y contraseña.
    3. Verifica respuesta HTTP 200 OK y DTO MecanicoResponseDTO.
    4. Verifica que en `usuarios` se actualizó nombres, whatsapp_hash, whatsapp_ultimos4 y password_hash.
    5. Verifica que en `identidades_whatsapp` se re-cifró `destinatario_cifrado` con Fernet y puede descifrarse al nuevo número.
    6. Tier 3: Verifica que se registró la entrada en `auditoria_operaciones` con la acción USUARIO_EDITADO.
    """
    if not database_configurada():
        pytest.skip("PostgreSQL no disponible para pruebas E2E.")

    engine = obtener_engine()
    taller_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
    tel_original = f"+51999111{uuid.uuid4().hex[:3]}"
    tel_nuevo = f"+51999888{uuid.uuid4().hex[:3]}"

    async with AsyncSession(engine, expire_on_commit=False) as session:
        user_repo = UsuarioRepository(session)
        ident_repo = IdentidadWhatsAppRepository(session)
        roles = await user_repo.asegurar_roles_estandar()

        # Crear Admin autorizador
        w_hash_admin = hash_identificador_persistencia(f"+51999777{uuid.uuid4().hex[:3]}", "telefono")
        admin_obj = await user_repo.crear_usuario(
            taller_id=taller_uuid,
            rol_id=roles["administrador"].id,
            nombres="Admin E2E Profile",
            whatsapp_hash=w_hash_admin,
            whatsapp_ultimos4="7777",
        )

        # Crear Mecánico a editar
        w_hash_orig = hash_identificador_persistencia(tel_original, "telefono")
        mecanico_obj = await user_repo.crear_usuario(
            taller_id=taller_uuid,
            rol_id=roles["mecanico"].id,
            nombres="Mecanico Original",
            whatsapp_hash=w_hash_orig,
            whatsapp_ultimos4=tel_original[-4:],
        )
        await ident_repo.registrar_identidad(
            usuario_id=mecanico_obj.id,
            identificador_hash=w_hash_orig,
            tipo_identificador="telefono",
            ultimos4=tel_original[-4:],
            proveedor="meta",
            destinatario_cifrado=cifrar_texto_reversible(tel_original),
        )
        await session.commit()
        mecanico_id = str(mecanico_obj.id)
        admin_id = str(admin_obj.id)

    token_admin = crear_jwt_token(
        sub="Admin E2E Profile",
        rol="administrador",
        taller_id=str(taller_uuid),
        usuario_id=admin_id,
    )
    headers = {"Authorization": f"Bearer {token_admin}"}

    client = TestClient(app)
    nueva_clave = "ClaveSegura_2026_E2E"
    payload = {
        "nombres": "Carlos Mecanico Actualizado",
        "telefono_whatsapp": tel_nuevo,
        "password": nueva_clave,
    }

    # Ejecutar PUT
    res = client.put(f"/api/v1/mecanicos/{mecanico_id}", json=payload, headers=headers)
    assert res.status_code == 200, f"Error en PUT: {res.text}"
    dto = res.json()
    assert dto["id"] == mecanico_id
    assert dto["nombres"] == "Carlos Mecanico Actualizado"
    assert dto["telefono"].endswith(tel_nuevo[-4:])
    assert dto["rol"] == "mecanico"

    # Verificar sincronización en Base de Datos
    async with AsyncSession(engine, expire_on_commit=False) as session:
        user_repo = UsuarioRepository(session)
        usuario_db = await user_repo.obtener_por_id(uuid.UUID(mecanico_id))
        assert usuario_db is not None
        assert usuario_db.nombres == "Carlos Mecanico Actualizado"
        assert usuario_db.whatsapp_ultimos4 == tel_nuevo[-4:]
        assert usuario_db.whatsapp_hash == hash_identificador_persistencia(tel_nuevo, "telefono")
        assert verificar_password(nueva_clave, usuario_db.password_hash) is True
        assert usuario_db.debe_cambiar_password is False

        # Verificar re-cifrado Fernet en identidades_whatsapp
        ident_stmt = select(IdentidadWhatsApp).where(IdentidadWhatsApp.usuario_id == usuario_db.id)
        ident_res = await session.execute(ident_stmt)
        identidad_db = ident_res.scalars().first()
        assert identidad_db is not None
        assert identidad_db.ultimos4 == tel_nuevo[-4:]
        assert descifrar_texto_reversible(identidad_db.destinatario_cifrado) == tel_nuevo

        # Tier 3: Verificar registro en la tabla auditoria
        audit_stmt = select(Auditoria).where(
            Auditoria.entidad_id == usuario_db.id,
            Auditoria.accion == "USUARIO_EDITADO",
        )
        audit_res = await session.execute(audit_stmt)
        audit_log = audit_res.scalars().first()
        assert audit_log is not None
        assert audit_log.entidad == "usuario"
        assert str(audit_log.usuario_id) == admin_id
        assert audit_log.detalles["nombres_modificados"] is True
        assert audit_log.detalles["telefono_modificado"] is True
        assert audit_log.detalles["password_modificado"] is True



@pytest.mark.anyio
async def test_actualizar_perfil_colision_telefono_duplicado_409():
    """
    Tier 2:
    Verifica que intentar actualizar el número de WhatsApp a un teléfono ya perteneciente
    a otro usuario del sistema retorne HTTP 409 Conflict.
    """
    if not database_configurada():
        pytest.skip("PostgreSQL no disponible para pruebas E2E.")

    engine = obtener_engine()
    taller_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
    tel_user_a = f"+51999222{uuid.uuid4().hex[:3]}"
    tel_user_b = f"+51999333{uuid.uuid4().hex[:3]}"

    async with AsyncSession(engine, expire_on_commit=False) as session:
        user_repo = UsuarioRepository(session)
        roles = await user_repo.asegurar_roles_estandar()

        # Admin
        admin_obj = await user_repo.crear_usuario(
            taller_id=taller_uuid,
            rol_id=roles["administrador"].id,
            nombres="Admin Collision Test",
            whatsapp_hash=hash_identificador_persistencia(f"+51999000{uuid.uuid4().hex[:3]}", "telefono"),
            whatsapp_ultimos4="0000",
        )

        # Usuario A
        w_hash_a = hash_identificador_persistencia(tel_user_a, "telefono")
        user_a = await user_repo.crear_usuario(
            taller_id=taller_uuid,
            rol_id=roles["mecanico"].id,
            nombres="Mecanico User A",
            whatsapp_hash=w_hash_a,
            whatsapp_ultimos4=tel_user_a[-4:],
        )

        # Usuario B
        w_hash_b = hash_identificador_persistencia(tel_user_b, "telefono")
        user_b = await user_repo.crear_usuario(
            taller_id=taller_uuid,
            rol_id=roles["mecanico"].id,
            nombres="Mecanico User B",
            whatsapp_hash=w_hash_b,
            whatsapp_ultimos4=tel_user_b[-4:],
        )

        await session.commit()
        user_a_id = str(user_a.id)
        admin_id = str(admin_obj.id)

    token_admin = crear_jwt_token(
        sub="Admin Collision Test",
        rol="administrador",
        taller_id=str(taller_uuid),
        usuario_id=admin_id,
    )
    headers = {"Authorization": f"Bearer {token_admin}"}

    client = TestClient(app)
    # Intentar asignar el teléfono de User B a User A
    payload = {"telefono_whatsapp": tel_user_b}

    res = client.put(f"/api/v1/mecanicos/{user_a_id}", json=payload, headers=headers)
    assert res.status_code == 409
    assert "ya está registrado" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_actualizar_perfil_jerarquia_jefe_no_puede_editar_admin():
    """
    Tier 2:
    Verifica que un jefe de taller (rol no admin) no pueda editar la cuenta de un administrador (HTTP 403 Forbidden).
    """
    if not database_configurada():
        pytest.skip("PostgreSQL no disponible para pruebas E2E.")

    engine = obtener_engine()
    taller_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

    async with AsyncSession(engine, expire_on_commit=False) as session:
        user_repo = UsuarioRepository(session)
        roles = await user_repo.asegurar_roles_estandar()

        # Admin target
        admin_target = await user_repo.crear_usuario(
            taller_id=taller_uuid,
            rol_id=roles["administrador"].id,
            nombres="Admin Target",
            whatsapp_hash=hash_identificador_persistencia(f"+51999555{uuid.uuid4().hex[:3]}", "telefono"),
            whatsapp_ultimos4="5555",
        )

        # Jefe de taller editor
        jefe_editor = await user_repo.crear_usuario(
            taller_id=taller_uuid,
            rol_id=roles["jefe_taller"].id,
            nombres="Jefe Editor",
            whatsapp_hash=hash_identificador_persistencia(f"+51999444{uuid.uuid4().hex[:3]}", "telefono"),
            whatsapp_ultimos4="4444",
        )

        await session.commit()
        admin_target_id = str(admin_target.id)
        jefe_editor_id = str(jefe_editor.id)

    token_jefe = crear_jwt_token(
        sub="Jefe Editor",
        rol="jefe_taller",
        taller_id=str(taller_uuid),
        usuario_id=jefe_editor_id,
    )
    headers = {"Authorization": f"Bearer {token_jefe}"}

    client = TestClient(app)
    payload = {"nombres": "Nombre Modificado Por Jefe"}

    res = client.put(f"/api/v1/mecanicos/{admin_target_id}", json=payload, headers=headers)
    assert res.status_code == 403
    assert "No tiene permisos para editar a un administrador" in res.json()["detail"]


@pytest.mark.anyio
async def test_actualizar_perfil_actualizacion_parcial_campos():
    """
    Tier 4:
    Verifica que se puedan actualizar campos de forma individual (solo nombres, solo teléfono, o solo contraseña).
    """
    if not database_configurada():
        pytest.skip("PostgreSQL no disponible para pruebas E2E.")

    engine = obtener_engine()
    taller_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
    tel_original = f"+51999666{uuid.uuid4().hex[:3]}"
    tel_solo_nuevo = f"+51999777{uuid.uuid4().hex[:3]}"

    async with AsyncSession(engine, expire_on_commit=False) as session:
        user_repo = UsuarioRepository(session)
        roles = await user_repo.asegurar_roles_estandar()

        admin_obj = await user_repo.crear_usuario(
            taller_id=taller_uuid,
            rol_id=roles["administrador"].id,
            nombres="Admin Partial Test",
            whatsapp_hash=hash_identificador_persistencia(f"+51999001{uuid.uuid4().hex[:3]}", "telefono"),
            whatsapp_ultimos4="0001",
        )

        mecanico_obj = await user_repo.crear_usuario(
            taller_id=taller_uuid,
            rol_id=roles["mecanico"].id,
            nombres="Mecanico Parcial",
            whatsapp_hash=hash_identificador_persistencia(tel_original, "telefono"),
            whatsapp_ultimos4=tel_original[-4:],
        )
        await session.commit()
        mecanico_id = str(mecanico_obj.id)
        admin_id = str(admin_obj.id)

    token_admin = crear_jwt_token(
        sub="Admin Partial Test",
        rol="administrador",
        taller_id=str(taller_uuid),
        usuario_id=admin_id,
    )
    headers = {"Authorization": f"Bearer {token_admin}"}
    client = TestClient(app)

    # 1. Actualizar SOLO nombre
    res_nombre = client.put(
        f"/api/v1/mecanicos/{mecanico_id}",
        json={"nombres": "Nombre Actualizado Solo"},
        headers=headers,
    )
    assert res_nombre.status_code == 200
    assert res_nombre.json()["nombres"] == "Nombre Actualizado Solo"

    # 2. Actualizar SOLO teléfono
    res_tel = client.put(
        f"/api/v1/mecanicos/{mecanico_id}",
        json={"telefono_whatsapp": tel_solo_nuevo},
        headers=headers,
    )
    assert res_tel.status_code == 200
    assert res_tel.json()["telefono"].endswith(tel_solo_nuevo[-4:])

    # 3. Actualizar SOLO contraseña
    res_pass = client.put(
        f"/api/v1/mecanicos/{mecanico_id}",
        json={"password": "ClaveParcialUnica_2026"},
        headers=headers,
    )
    assert res_pass.status_code == 200
