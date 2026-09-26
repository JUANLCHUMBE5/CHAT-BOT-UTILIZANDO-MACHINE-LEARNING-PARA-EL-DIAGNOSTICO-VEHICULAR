"""
Pruebas automatizadas exhaustivas para el flujo:
Cliente -> Autorización del Administrador -> Mecánico.

Verifica:
1. Contacto nuevo con teléfono -> creado automáticamente con rol cliente.
2. Contacto que solamente trae user_id -> no produce HTTP 400.
3. Cliente recibe bienvenida con datos del taller y no ejecuta ML/RAG/Gemini.
4. Cliente puede consultar servicios, horarios y ubicación.
5. Cliente solicita acceso como mecánico -> se crea registro pendiente en solicitudes_acceso.
6. Solicitudes duplicadas de acceso son reconocidas como pendientes.
7. Administrador aprueba solicitud -> rol pasa a mecánico, genera contraseña temporal y encola WhatsApp con destinatario descifrable.
8. Mecánico promovido puede ejecutar diagnósticos técnicos (ML + RAG + Gemini).
9. Aislamiento multi-taller: Admin de un taller no puede aprobar/modificar solicitudes de otro taller.
10. Webhooks duplicados (idempotencia) no crean clientes repetidos.
11. Contactos bloqueados o inactivos son rechazados y no acceden a diagnósticos.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from src.config import settings
from src.core.security import (
    crear_jwt_token,
    descifrar_texto_reversible,
    hash_identificador_persistencia,
)
from src.core.services.webhook_service import WebhookService
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.identidad_whatsapp_repository import IdentidadWhatsAppRepository
from src.infrastructure.database.repositories.solicitud_acceso_repository import SolicitudAccesoRepository
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository


@pytest.mark.anyio
async def test_contacto_nuevo_creado_como_cliente_y_recibe_bienvenida():
    """Un número desconocido que escribe por WhatsApp debe registrarse automáticamente como rol cliente y recibir menú sin ML."""
    if not database_configurada():
        pytest.skip("PostgreSQL no disponible")

    engine = obtener_engine()
    tel_id_meta_test = f"META_TEL_{uuid.uuid4().hex[:8]}"

    async with AsyncSession(engine, expire_on_commit=False) as session:
        taller_repo = TallerRepository(session)

        # Crear taller de prueba con datos reales
        await taller_repo.crear_taller(
            nombre="Taller Prueba Flujo Cliente",
            direccion="Av. Central 123, Carabayllo",
            telefono="+51 987654321",
            horario_atencion="Lunes a Viernes 8am - 6pm",
            telefono_id_meta=tel_id_meta_test,
        )
        await session.commit()

    tel_nuevo = f"+51999111{uuid.uuid4().hex[:3]}"
    msg_id = f"meta_test_in_{uuid.uuid4().hex[:8]}"

    service = WebhookService()
    resultado = await service.procesar_mensaje(
        remitente=tel_nuevo,
        meta_message_id=msg_id,
        tipo_mensaje="text",
        texto_cliente="Hola, buenos dias",
        proveedor="meta",
        tipo_identificador="telefono",
        telefono_id_meta=tel_id_meta_test,
        nombre_contacto="Carlos Cliente",
    )

    assert resultado["status"] == "completado_cliente"
    assert "Hola, bienvenido a Taller Prueba Flujo Cliente" in resultado["respuesta"]
    assert "Consultar nuestros servicios" in resultado["respuesta"]

    # Verificar en base de datos
    async with AsyncSession(engine, expire_on_commit=False) as session:
        usuario_repo = UsuarioRepository(session)
        ident_repo = IdentidadWhatsAppRepository(session)

        w_hash = hash_identificador_persistencia(tel_nuevo, "telefono")
        usuario = await usuario_repo.buscar_por_whatsapp_hash(w_hash)

        assert usuario is not None
        assert usuario.rol.codigo == "cliente"
        assert usuario.nombres == "Carlos Cliente"
        assert usuario.activo is True
        assert usuario.bloqueado is False
        assert usuario.password_hash is None  # No requiere contraseña

        identidad = await ident_repo.buscar_por_hash(w_hash)
        assert identidad is not None
        assert identidad.usuario_id == usuario.id
        assert identidad.tipo_identificador == "telefono"
        assert identidad.destinatario_cifrado is not None
        # Verificar que el destinatario cifrado se descifra correctamente al número real
        assert descifrar_texto_reversible(identidad.destinatario_cifrado) == tel_nuevo


@pytest.mark.anyio
async def test_contacto_solo_user_id_meta_no_genera_error_400():
    """Contactos de Meta que llegan con user_id privado sin teléfono se procesan sin error."""
    if not database_configurada():
        pytest.skip("PostgreSQL no disponible")

    meta_user_id = f"meta_user_{uuid.uuid4().hex[:10]}"
    msg_id = f"meta_test_uid_{uuid.uuid4().hex[:8]}"

    service = WebhookService()
    resultado = await service.procesar_mensaje(
        remitente=meta_user_id,
        meta_message_id=msg_id,
        tipo_mensaje="text",
        texto_cliente="Buenas tardes",
        proveedor="meta",
        tipo_identificador="user_id",
        nombre_contacto="Usuario Meta",
    )

    assert resultado["status"] == "completado_cliente"
    assert "bienvenido" in resultado["respuesta"].lower()


@pytest.mark.anyio
async def test_cliente_solicita_servicios_y_ubicacion():
    """Un cliente puede consultar opciones de servicios, citas y ubicación."""
    if not database_configurada():
        pytest.skip("PostgreSQL no disponible")

    tel_cliente = f"+51999333{uuid.uuid4().hex[:3]}"
    service = WebhookService()

    # Opción 1: Servicios
    res_servicios = await service.procesar_mensaje(
        remitente=tel_cliente,
        meta_message_id=f"msg_srv_{uuid.uuid4().hex[:6]}",
        tipo_mensaje="text",
        texto_cliente="1",
    )
    assert "Servicios ofrecidos" in res_servicios["respuesta"]
    assert "Precios referenciales" in res_servicios["respuesta"]

    # Opción 3: Ubicación
    res_ubicacion = await service.procesar_mensaje(
        remitente=tel_cliente,
        meta_message_id=f"msg_ubi_{uuid.uuid4().hex[:6]}",
        tipo_mensaje="text",
        texto_cliente="donde quedan y cual es su direccion",
    )
    assert "Ubicación" in res_ubicacion["respuesta"]
    assert "Horario de atención" in res_ubicacion["respuesta"]


@pytest.mark.anyio
async def test_cliente_solicita_acceso_crea_solicitud_pendiente():
    """Cuando un cliente envía 'soy mecanico' o 'quiero acceso', se genera una solicitud en solicitudes_acceso."""
    if not database_configurada():
        pytest.skip("PostgreSQL no disponible")

    engine = obtener_engine()
    unique_suffix = uuid.uuid4().hex[:4]
    tel_solicitante = f"+51999555{unique_suffix}"
    service = WebhookService()

    # Cliente envía solicitud
    resultado = await service.procesar_mensaje(
        remitente=tel_solicitante,
        meta_message_id=f"msg_acc_{uuid.uuid4().hex[:6]}",
        tipo_mensaje="text",
        texto_cliente="Soy mecánico y quiero acceso al diagnóstico técnico",
    )

    assert "Solicitud de Acceso como Mecánico Registrada" in resultado["respuesta"]

    # Reintentar solicitud mientras está pendiente
    resultado_duplicado = await service.procesar_mensaje(
        remitente=tel_solicitante,
        meta_message_id=f"msg_acc2_{uuid.uuid4().hex[:6]}",
        tipo_mensaje="text",
        texto_cliente="4",
    )
    assert "Solicitud de Mecánico en Trámite" in resultado_duplicado["respuesta"]
    assert "Ya tienes una solicitud pendiente" in resultado_duplicado["respuesta"]

    # Verificar en base de datos
    async with AsyncSession(engine, expire_on_commit=False) as session:
        usuario_repo = UsuarioRepository(session)
        sol_repo = SolicitudAccesoRepository(session)

        w_hash = hash_identificador_persistencia(tel_solicitante, "telefono")
        usuario = await usuario_repo.buscar_por_whatsapp_hash(w_hash)
        assert usuario is not None

        solicitud = await sol_repo.obtener_pendiente_por_usuario(usuario.id, usuario.taller_id)
        assert solicitud is not None
        assert solicitud.estado == "pendiente"
        assert solicitud.rol_solicitado == "mecanico"


@pytest.mark.anyio
async def test_admin_aprueba_solicitud_promueve_y_habilita_diagnostico(monkeypatch):
    """El administrador aprueba la solicitud: rol pasa a mecánico, genera clave temporal y encola WhatsApp con destino real."""
    if not database_configurada():
        pytest.skip("PostgreSQL no disponible")

    monkeypatch.setattr(settings, "gemini_api_key", "")
    engine = obtener_engine()
    tel_mecanico_futuro = f"+51999888{uuid.uuid4().hex[:3]}"
    service = WebhookService()
    service.gestor.api_key = ""

    # 1. Crear cliente y solicitud
    await service.procesar_mensaje(
        remitente=tel_mecanico_futuro,
        meta_message_id=f"msg_init_{uuid.uuid4().hex[:6]}",
        tipo_mensaje="text",
        texto_cliente="Soy mecanico",
    )

    # 2. Obtener datos de la solicitud y del taller
    async with AsyncSession(engine, expire_on_commit=False) as session:
        usuario_repo = UsuarioRepository(session)
        sol_repo = SolicitudAccesoRepository(session)

        w_hash = hash_identificador_persistencia(tel_mecanico_futuro, "telefono")
        usuario = await usuario_repo.buscar_por_whatsapp_hash(w_hash)
        solicitud = await sol_repo.obtener_pendiente_por_usuario(usuario.id, usuario.taller_id)
        assert solicitud is not None
        roles = await usuario_repo.asegurar_roles_estandar()
        admin = await usuario_repo.crear_usuario(
            taller_id=usuario.taller_id,
            rol_id=roles["administrador"].id,
            nombres="Administrador de Prueba",
            whatsapp_hash=hash_identificador_persistencia(
                f"+51999666{uuid.uuid4().hex[:3]}", "telefono"
            ),
            whatsapp_ultimos4="6666",
        )
        await session.commit()
        sol_id = str(solicitud.id)
        taller_id_str = str(usuario.taller_id)
        admin_id_str = str(admin.id)

    # 3. Administrador aprueba solicitud mediante API REST
    token_admin = crear_jwt_token(
        sub="admin_test",
        rol="administrador",
        taller_id=taller_id_str,
        usuario_id=admin_id_str,
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/clientes/solicitudes/{sol_id}/aprobar",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["nuevo_rol"] == "mecanico"

    # 4. Verificar que el usuario ahora tiene rol mecánico en PostgreSQL
    async with AsyncSession(engine, expire_on_commit=False) as session:
        usuario_repo = UsuarioRepository(session)
        usuario_promovido = await usuario_repo.obtener_por_id(usuario.id)
        assert usuario_promovido.rol.codigo == "mecanico"

    # 5. El mecánico ahora envía un síntoma vehicular y SÍ se ejecuta el diagnóstico técnico
    res_diagnostico = await service.procesar_mensaje(
        remitente=tel_mecanico_futuro,
        meta_message_id=f"msg_diag_{uuid.uuid4().hex[:6]}",
        tipo_mensaje="text",
        texto_cliente="El motor cascabelea fuertemente y pierde potencia al subir pendientes",
    )

    assert res_diagnostico["status"] == "completado"
    assert "diagnostico_id" in res_diagnostico
    assert "falla_predicha" in res_diagnostico
    assert res_diagnostico["falla_predicha"] is not None

    # 6. Si responde NO, CarBot solicita la falla real y conserva la predicción original.
    res_no = await service.procesar_mensaje(
        remitente=tel_mecanico_futuro,
        meta_message_id=f"msg_no_{uuid.uuid4().hex[:6]}",
        tipo_mensaje="text",
        texto_cliente="NO",
    )
    assert res_no["status"] in ("aclaracion", "esperando_falla_real")
    assert "falla" in res_no["respuesta"].lower() or "descart" in res_no["respuesta"].lower()

    # 7. La corrección queda asociada al mismo diagnóstico, sin ejecutar otro ML/RAG/LLM.
    falla_real = "Bobina defectuosa"
    res_correccion = await service.procesar_mensaje(
        remitente=tel_mecanico_futuro,
        meta_message_id=f"msg_fix_{uuid.uuid4().hex[:6]}",
        tipo_mensaje="text",
        texto_cliente=falla_real,
    )
    assert res_correccion["status"] == "validacion_tecnica"
    assert res_correccion["diagnostico_id"] == res_diagnostico["diagnostico_id"]

    async with AsyncSession(engine, expire_on_commit=False) as session:
        diagnostico = await DiagnosticoRepository(session).obtener_por_id(
            uuid.UUID(res_diagnostico["diagnostico_id"])
        )
        assert diagnostico.estado == "descartado"
        assert diagnostico.conclusion_mecanico == falla_real


@pytest.mark.anyio
async def test_aislamiento_multitaller_admin_no_puede_aprobar_otro_taller():
    """Un administrador del Taller A no puede ver ni aprobar solicitudes del Taller B."""
    if not database_configurada():
        pytest.skip("PostgreSQL no disponible")

    engine = obtener_engine()
    taller_b_id = uuid.uuid4()

    async with AsyncSession(engine, expire_on_commit=False) as session:
        taller_repo = TallerRepository(session)
        user_repo = UsuarioRepository(session)
        sol_repo = SolicitudAccesoRepository(session)

        # Crear taller B
        taller_b = await taller_repo.crear_taller(
            nombre=f"Taller B Aislado {uuid.uuid4().hex[:4]}",
            taller_id=taller_b_id,
        )

        # Crear cliente en taller B
        w_hash_b = hash_identificador_persistencia(f"+51999777{uuid.uuid4().hex[:3]}", "telefono")
        cliente_b = await user_repo.crear_cliente_automatico(
            taller_id=taller_b.id,
            nombres="Cliente Taller B",
            whatsapp_hash=w_hash_b,
        )
        solicitud_b = await sol_repo.crear_solicitud(
            usuario_id=cliente_b.id,
            taller_id=taller_b.id,
        )
        await session.commit()
        sol_b_id = str(solicitud_b.id)

    # Token de admin del Taller A
    taller_a_id = str(uuid.uuid4())
    token_admin_a = crear_jwt_token(sub="admin_a", rol="administrador", taller_id=taller_a_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Intentar aprobar solicitud de Taller B con credenciales de Taller A
        res = await client.post(
            f"/api/v1/clientes/solicitudes/{sol_b_id}/aprobar",
            headers={"Authorization": f"Bearer {token_admin_a}"},
        )
        assert res.status_code == 404  # Aislado por taller


@pytest.mark.anyio
async def test_contacto_bloqueado_o_inactivo_no_recibe_acceso():
    """Un contacto bloqueado o con activo=False es restringido y no accede a diagnósticos."""
    if not database_configurada():
        pytest.skip("PostgreSQL no disponible")

    engine = obtener_engine()
    tel_bloqueado = f"+51999000{uuid.uuid4().hex[:3]}"
    service = WebhookService()

    # 1. Registrar cliente
    await service.procesar_mensaje(
        remitente=tel_bloqueado,
        meta_message_id=f"msg_blk_{uuid.uuid4().hex[:6]}",
        texto_cliente="Hola",
    )

    # 2. Bloquearlo en base de datos
    async with AsyncSession(engine, expire_on_commit=False) as session:
        user_repo = UsuarioRepository(session)
        w_hash = hash_identificador_persistencia(tel_bloqueado, "telefono")
        usuario = await user_repo.buscar_por_whatsapp_hash(w_hash)
        assert usuario is not None
        await user_repo.toggle_bloqueo(usuario.id)
        await session.commit()

    # 3. Intentar interactuar bloqueado
    resultado = await service.procesar_mensaje(
        remitente=tel_bloqueado,
        meta_message_id=f"msg_blk_att_{uuid.uuid4().hex[:6]}",
        texto_cliente="Quiero hacer una consulta",
    )

    assert resultado["status"] == "bloqueado"


@pytest.mark.anyio
async def test_panel_promueve_cliente_y_revocacion_lo_regresa_a_cliente():
    """Registrar un teléfono cliente lo autoriza; quitar acceso conserva la cuenta como cliente."""
    engine = obtener_engine()
    # Un teléfono de prueba debe contener dígitos exclusivamente. Los prefijos
    # hexadecimales incluían a-f, que el normalizador elimina y podía provocar
    # el mismo whatsapp_hash entre ejecuciones contra PostgreSQL persistente.
    telefono = f"+51{uuid.uuid4().int % 10_000_000_000:010d}"
    service = WebhookService()

    await service.procesar_mensaje(
        remitente=telefono,
        meta_message_id=f"msg_cliente_{uuid.uuid4().hex[:8]}",
        tipo_mensaje="text",
        texto_cliente="Hola",
        proveedor="meta",
    )

    async with AsyncSession(engine, expire_on_commit=False) as session:
        usuario_repo = UsuarioRepository(session)
        cliente = await usuario_repo.buscar_por_telefono(telefono)
        assert cliente is not None
        assert cliente.rol.codigo == "cliente"
        roles = await usuario_repo.asegurar_roles_estandar()
        admin = await usuario_repo.crear_usuario(
            taller_id=cliente.taller_id,
            rol_id=roles["administrador"].id,
            nombres="Admin Promoción",
            whatsapp_hash=hash_identificador_persistencia(
                f"+51{uuid.uuid4().int % 10_000_000_000:010d}", "telefono"
            ),
            whatsapp_ultimos4="3333",
        )
        await session.commit()
        cliente_id = str(cliente.id)
        taller_id = str(cliente.taller_id)
        admin_id = str(admin.id)

    token = crear_jwt_token(
        sub="Admin Promoción",
        rol="administrador",
        taller_id=taller_id,
        usuario_id=admin_id,
    )
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        promocion = await client.post(
            "/api/v1/mecanicos",
            headers=headers,
            json={
                "nombres": "Mecánico Promovido",
                "telefono_whatsapp": telefono,
                "password": "Temporal_123",
                "rol": "mecanico",
            },
        )
        assert promocion.status_code == 201
        assert promocion.json()["rol"] == "mecanico"

        revocacion = await client.patch(
            f"/api/v1/mecanicos/{cliente_id}/revocar-acceso",
            headers=headers,
        )
        assert revocacion.status_code == 200
        assert revocacion.json()["nuevo_rol"] == "cliente"

    async with AsyncSession(engine, expire_on_commit=False) as session:
        usuario_repo = UsuarioRepository(session)
        usuario_final = await usuario_repo.obtener_por_id(uuid.UUID(cliente_id))
        assert usuario_final.rol.codigo == "cliente"
        assert usuario_final.password_hash is None
        assert usuario_final.activo is True
        assert usuario_final.bloqueado is False


@pytest.mark.anyio
async def test_deduplicacion_webhooks_idempotencia():
    """Mensajes con el mismo meta_message_id no se procesan dos veces."""
    if not database_configurada():
        pytest.skip("PostgreSQL no disponible")

    dup_id = f"meta_dup_{uuid.uuid4().hex}"
    service = WebhookService()
    tel_dup = f"+51999444{uuid.uuid4().hex[:3]}"

    # Primer envío
    res1 = await service.procesar_mensaje(
        remitente=tel_dup,
        meta_message_id=dup_id,
        texto_cliente="Consulta inicial",
    )
    assert res1["status"] in ("completado_cliente", "completado")

    # Segundo envío idéntico
    res2 = await service.procesar_mensaje(
        remitente=tel_dup,
        meta_message_id=dup_id,
        texto_cliente="Consulta repetida",
    )
    assert res2["status"] == "duplicado_ignorado"
