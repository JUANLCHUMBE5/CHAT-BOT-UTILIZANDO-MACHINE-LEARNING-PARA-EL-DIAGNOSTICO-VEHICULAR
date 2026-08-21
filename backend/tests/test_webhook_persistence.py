"""Pruebas de integración para el servicio de Webhook con PostgreSQL y autorización de mecánicos."""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.security import hash_identificador_persistencia
from src.core.services.webhook_service import WebhookService
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.models.catalogs import Taller, Usuario
from src.infrastructure.database.models.diagnostics import Diagnostico, HipotesisDiagnostico, Vehiculo
from src.infrastructure.database.models.jobs import TrabajoGemini
from src.infrastructure.database.models.messaging import Conversacion, Mensaje
from src.infrastructure.database.models.operations import Auditoria, UsoApi
from src.infrastructure.database.repositories.conversacion_repository import ConversacionRepository
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.mensaje_repository import MensajeRepository
from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository


@pytest.fixture
async def setup_test_db():
    """Configura el taller y mecánico de pruebas en PostgreSQL y realiza limpieza al finalizar."""
    if not database_configurada():
        pytest.skip("PostgreSQL no está configurado para pruebas.")

    engine = obtener_engine()
    taller_id = uuid.uuid4()
    mecanico_id = uuid.uuid4()

    tel_autorizado = f"+51 987 {uuid.uuid4().int % 1000000:06d}"
    tel_no_autorizado = f"+51 911 {uuid.uuid4().int % 1000000:06d}"
    w_hash = hash_identificador_persistencia(tel_autorizado, "telefono")
    ultimos4 = tel_autorizado[-4:]

    # Registrar en PostgreSQL
    async with AsyncSession(engine, expire_on_commit=False) as session:
        taller_repo = TallerRepository(session)
        user_repo = UsuarioRepository(session)
        taller = await taller_repo.crear_taller(
            nombre="Taller Autorizado Carabayllo Test",
            ruc=f"20{uuid.uuid4().int % 1000000000:09d}",
            taller_id=taller_id,
        )
        roles = await user_repo.asegurar_roles_estandar()
        await user_repo.crear_usuario(
            taller_id=taller.id,
            rol_id=roles["mecanico"].id,
            nombres="Juan Mecánico Test",
            whatsapp_hash=w_hash,
            whatsapp_ultimos4=ultimos4,
            activo=True,
            usuario_id=mecanico_id,
        )
        await session.commit()

    yield {
        "engine": engine,
        "telefono_autorizado": tel_autorizado,
        "telefono_no_autorizado": tel_no_autorizado,
        "taller_id": taller_id,
        "mecanico_id": mecanico_id,
    }

    # Limpieza de registros creados en PostgreSQL
    async with AsyncSession(engine, expire_on_commit=False) as session:
        subq = select(Diagnostico.id).where(Diagnostico.taller_id == taller_id)
        await session.execute(delete(HipotesisDiagnostico).where(HipotesisDiagnostico.diagnostico_id.in_(subq)))
        await session.execute(delete(UsoApi).where(UsoApi.taller_id == taller_id))
        await session.execute(delete(TrabajoGemini).where(TrabajoGemini.taller_id == taller_id))
        await session.execute(delete(Auditoria).where(Auditoria.taller_id == taller_id))
        await session.execute(
            delete(Auditoria).where(
                Auditoria.detalles["meta_message_id"].as_string().like("wamid_unauth_%")
            )
        )
        await session.execute(delete(Diagnostico).where(Diagnostico.taller_id == taller_id))
        await session.execute(delete(Mensaje).where(Mensaje.taller_id == taller_id))
        await session.execute(delete(Conversacion).where(Conversacion.taller_id == taller_id))
        await session.execute(delete(Vehiculo).where(Vehiculo.taller_id == taller_id))
        await session.execute(delete(Usuario).where(Usuario.taller_id == taller_id))
        await session.execute(delete(Taller).where(Taller.id == taller_id))
        await session.commit()


@pytest.mark.anyio
async def test_webhook_mecanico_autorizado_guarda_en_tablas(setup_test_db, monkeypatch):
    data = setup_test_db
    monkeypatch.setattr(WebhookService, "enviar_mensaje_whatsapp", lambda self, dest, txt: True)

    gestor = GestorDiagnostico()
    gestor.api_key = ""
    service = WebhookService(gestor)

    meta_msg_id = f"wamid_test_{uuid.uuid4().hex}"
    resultado = await service.procesar_mensaje(
        remitente=data["telefono_autorizado"],
        meta_message_id=meta_msg_id,
        tipo_mensaje="text",
        texto_cliente="Siento un chillido agudo al frenar el auto",
        placa="ABC-123",
        marca_modelo="Toyota Yaris",
    )

    assert resultado["status"] == "completado"
    assert "Frenos" in resultado["falla_predicha"] or "Pastillas" in resultado["falla_predicha"] or resultado["confianza"] > 0
    assert resultado["tiempo_total_ms"] > 0

    # Verificar directamente en las tablas de PostgreSQL
    engine = data["engine"]
    async with AsyncSession(engine, expire_on_commit=False) as session:
        msg_repo = MensajeRepository(session)
        conv_repo = ConversacionRepository(session)
        diag_repo = DiagnosticoRepository(session)
        op_repo = OperacionesRepository(session)

        # 1. Mensaje guardado y dedup verificado
        assert await msg_repo.existe_meta_message_id(meta_msg_id) is True

        # 2. Conversación activa existente
        conv = await conv_repo.obtener_por_id(uuid.UUID(resultado["conversacion_id"]))
        assert conv is not None
        assert conv.estado == "abierta"

        # 3. Diagnóstico e hipótesis persistidos
        diag = await diag_repo.obtener_por_id(uuid.UUID(resultado["diagnostico_id"]))
        assert diag is not None
        assert diag.sintoma_original.lower() == "siento un chillido agudo al frenar el auto"
        assert diag.modo_diagnostico in ("completo_ml_rag_llm", "diagnostico_degradado_ml_rag")
        assert len(diag.hipotesis) >= 1
        assert diag.hipotesis[0].orden == 1
        assert diag.hipotesis[0].prueba_recomendada
        assert diag.hipotesis[0].prueba_recomendada != diag.sintoma_normalizado
        assert "no se encontr" not in diag.hipotesis[0].prueba_recomendada.lower()
        assert diag.hipotesis[0].evidencia.startswith("Fuente:")

        # 4. Uso de API y costos registrados
        costo_total = await op_repo.obtener_costo_total_taller(data["taller_id"])
        assert costo_total == Decimal("0")

        # Sin API key/uso confirmado de Gemini no debe inventarse consumo Google.
        usos_google = await session.execute(
            select(UsoApi).where(
                UsoApi.taller_id == data["taller_id"],
                UsoApi.proveedor == "google",
            )
        )
        assert usos_google.scalars().all() == []

        salida = await msg_repo.obtener_por_meta_message_id(f"out_{meta_msg_id}")
        assert salida is not None
        assert salida.estado_entrega == "pendiente"
        assert salida.proveedor == "meta"
        assert salida.destinatario_cifrado is not None
        assert data["telefono_autorizado"] not in salida.destinatario_cifrado


@pytest.mark.anyio
async def test_webhook_rechaza_mecanico_no_autorizado(setup_test_db, monkeypatch):
    data = setup_test_db
    mensajes_enviados = []
    async def envio_mock(proveedor, destino, texto):
        mensajes_enviados.append((destino, texto))
        from src.core.services.whatsapp_provider import ResultadoEnvioWhatsApp
        return ResultadoEnvioWhatsApp(True, False, "mock-id")

    monkeypatch.setattr(
        "src.core.services.webhook_service.whatsapp_provider_service.enviar", envio_mock
    )

    gestor = GestorDiagnostico()
    gestor.api_key = ""
    service = WebhookService(gestor)

    meta_msg_id = f"wamid_unauth_{uuid.uuid4().hex}"
    resultado = await service.procesar_mensaje(
        remitente=data["telefono_no_autorizado"],
        meta_message_id=meta_msg_id,
        tipo_mensaje="text",
        texto_cliente="Hola quiero un diagnóstico",
    )

    assert resultado["status"] == "completado_cliente"
    assert "bienvenido" in resultado["respuesta"].lower()

    # Comprobar que se persistió la respuesta del menú en la cola outbox para entrega
    async with AsyncSession(data["engine"], expire_on_commit=False) as session:
        msg_repo = MensajeRepository(session)
        salida = await msg_repo.obtener_por_meta_message_id(f"out_{meta_msg_id}")
        assert salida is not None
        assert salida.estado_entrega == "pendiente"
        assert "bienvenido" in salida.texto.lower()


@pytest.mark.anyio
async def test_consulta_tecnica_autorizada_no_crea_diagnostico(setup_test_db):
    data = setup_test_db
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    service = WebhookService(gestor)
    meta_msg_id = f"wamid_info_{uuid.uuid4().hex}"

    resultado = await service.procesar_mensaje(
        remitente=data["telefono_autorizado"],
        meta_message_id=meta_msg_id,
        tipo_mensaje="text",
        texto_cliente="qué potencia deben tener los focos LED H4 para una Suzuki APV",
    )

    assert resultado["status"] == "consulta_tecnica"
    async with AsyncSession(data["engine"], expire_on_commit=False) as session:
        diagnosticos = await session.execute(
            select(Diagnostico).where(Diagnostico.taller_id == data["taller_id"])
        )
        assert diagnosticos.scalars().all() == []
        salida = await MensajeRepository(session).obtener_por_meta_message_id(f"out_{meta_msg_id}")
        assert salida is not None
        assert "falla vehicular" not in (salida.texto or "").lower()


@pytest.mark.anyio
async def test_webhook_idempotencia_meta_duplicados(setup_test_db, monkeypatch):
    data = setup_test_db
    monkeypatch.setattr(WebhookService, "enviar_mensaje_whatsapp", lambda self, dest, txt: True)

    gestor = GestorDiagnostico()
    gestor.api_key = ""
    service = WebhookService(gestor)

    meta_msg_id = f"wamid_dup_{uuid.uuid4().hex}"

    # Primera llamada: procesa normalmente
    res1 = await service.procesar_mensaje(
        remitente=data["telefono_autorizado"],
        meta_message_id=meta_msg_id,
        tipo_mensaje="text",
        texto_cliente="El carro vibra al acelerar en subida",
    )
    assert res1["status"] == "completado"

    # Segunda llamada con el MISMO meta_message_id: debe ser ignorado de inmediato
    res2 = await service.procesar_mensaje(
        remitente=data["telefono_autorizado"],
        meta_message_id=meta_msg_id,
        tipo_mensaje="text",
        texto_cliente="El carro vibra al acelerar en subida",
    )
    assert res2["status"] == "duplicado_ignorado"
    assert res2["meta_message_id"] == meta_msg_id
