"""Pruebas unitarias y de regresión de privacidad, despacho y transaccionalidad de la cola general."""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.jobs.system_worker import SystemWorker
from src.core.security import cifrar_texto_reversible
from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.jobs import TrabajoSistema
from src.infrastructure.database.repositories.trabajo_sistema_repository import TrabajoSistemaRepository


def test_payload_trabajo_se_guarda_cifrado_y_se_recupera_en_memoria():
    payload = {"remitente": "+51987654321", "texto_cliente": "el motor falla"}
    cifrado = cifrar_texto_reversible(json.dumps(payload))
    trabajo = TrabajoSistema(
        tipo="webhook_mensaje",
        cola="diagnosticos",
        payload_cifrado=cifrado,
    )

    assert "+51987654321" not in trabajo.payload_cifrado
    assert TrabajoSistemaRepository(None).obtener_payload(trabajo) == payload  # type: ignore[arg-type]


@pytest.mark.anyio
async def test_worker_despacha_webhook_sin_exponer_payload(monkeypatch):
    recibido = {}

    class WebhookFalso:
        def __init__(self, gestor):
            self.gestor = gestor

        async def procesar_mensaje(self, **payload):
            recibido.update(payload)
            return {"status": "completado", "tiempo_ms": 12}

    monkeypatch.setattr("src.application.jobs.system_worker.WebhookService", WebhookFalso)
    worker = SystemWorker(gestor=object())  # type: ignore[arg-type]
    resumen = await worker._procesar(
        "webhook_mensaje",
        {"remitente": "+51987654321", "meta_message_id": "wamid-test"},
    )

    assert recibido["meta_message_id"] == "wamid-test"
    assert json.loads(resumen)["status"] == "completado"


@pytest.mark.anyio
async def test_worker_procesar_siguiente_maneja_transaccion_abierta(monkeypatch):
    """Regresión: Verifica que procesar_siguiente no lance InvalidRequestError
    cuando _procesar deja una transacción activa en la sesión (SQLAlchemy autobegin)."""
    worker = SystemWorker(gestor=object())  # type: ignore[arg-type]

    trabajo_mock = MagicMock(spec=TrabajoSistema)
    trabajo_mock.id = uuid.uuid4()
    trabajo_mock.tipo = "diagnostico_api"
    trabajo_mock.taller_id = uuid.uuid4()

    # Simular sesión donde in_transaction() es True tras ejecutar _procesar
    session_mock = MagicMock()
    session_mock.in_transaction.return_value = True
    session_mock.commit = AsyncMock()
    session_mock.rollback = AsyncMock()

    # Mock del begin context manager
    begin_cm = MagicMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session_mock.begin.return_value = begin_cm

    # AsyncSession context manager
    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=session_mock)
    session_cm.__aexit__ = AsyncMock(return_value=None)

    monkeypatch.setattr(
        "src.application.jobs.system_worker.obtener_engine",
        lambda: MagicMock(),
    )
    monkeypatch.setattr(
        "src.application.jobs.system_worker.AsyncSession",
        lambda *args, **kwargs: session_cm,
    )
    monkeypatch.setattr(
        TrabajoSistemaRepository,
        "reclamar_siguiente",
        AsyncMock(return_value=trabajo_mock),
    )
    monkeypatch.setattr(
        TrabajoSistemaRepository,
        "obtener_payload",
        lambda self, t: {"session_id": "s1", "sintoma": "falla"},
    )
    monkeypatch.setattr(
        TrabajoSistemaRepository,
        "marcar_completado",
        AsyncMock(return_value="completado"),
    )
    monkeypatch.setattr(
        worker,
        "_procesar",
        AsyncMock(return_value=json.dumps({"status": "completado"})),
    )

    procesado = await worker.procesar_siguiente()
    assert procesado is True
    # Debe haber llamado a commit sobre la transacción activa en lugar de intentar session.begin()
    session_mock.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_worker_procesar_siguiente_rollback_limpio_en_error(monkeypatch):
    """Regresión: Verifica que ante una excepción con transacción activa,
    el worker realice rollback antes de invocar marcar_error, evitando InvalidRequestError."""
    worker = SystemWorker(gestor=object())  # type: ignore[arg-type]

    trabajo_mock = MagicMock(spec=TrabajoSistema)
    trabajo_mock.id = uuid.uuid4()
    trabajo_mock.tipo = "diagnostico_api"
    trabajo_mock.taller_id = uuid.uuid4()

    # La sesión reporta transacción activa cuando falla _procesar
    transaccion_activa = True

    def mock_in_transaction():
        return transaccion_activa

    async def mock_rollback():
        nonlocal transaccion_activa
        transaccion_activa = False

    session_mock = MagicMock()
    session_mock.in_transaction = mock_in_transaction
    session_mock.rollback = mock_rollback

    begin_cm = MagicMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session_mock.begin.return_value = begin_cm

    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=session_mock)
    session_cm.__aexit__ = AsyncMock(return_value=None)

    monkeypatch.setattr(
        "src.application.jobs.system_worker.obtener_engine",
        lambda: MagicMock(),
    )
    monkeypatch.setattr(
        "src.application.jobs.system_worker.AsyncSession",
        lambda *args, **kwargs: session_cm,
    )
    monkeypatch.setattr(
        TrabajoSistemaRepository,
        "reclamar_siguiente",
        AsyncMock(return_value=trabajo_mock),
    )
    monkeypatch.setattr(
        TrabajoSistemaRepository,
        "obtener_payload",
        lambda self, t: {"sintoma": "falla"},
    )
    monkeypatch.setattr(
        TrabajoSistemaRepository,
        "marcar_error",
        AsyncMock(return_value="pendiente_reintento"),
    )
    monkeypatch.setattr(
        worker,
        "_procesar",
        AsyncMock(side_effect=RuntimeError("Fallo simulado en procesamiento")),
    )

    procesado = await worker.procesar_siguiente()
    assert procesado is True
    # Tras el rollback, transaccion_activa debió quedar en False y session.begin() se llamó para marcar_error
    assert transaccion_activa is False
    TrabajoSistemaRepository.marcar_error.assert_awaited_once()


@pytest.mark.anyio
async def test_system_worker_flujo_real_postgresql():
    """Prueba de integración end-to-end con PostgreSQL real:
    Verifica que la ejecución real con consultas SQL concurrentes en _procesar
    no colisione con el ciclo de completitud del worker."""
    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        async with session.begin():
            repo = TrabajoSistemaRepository(session)
            trabajo, _ = await repo.crear_trabajo(
                cola="diagnosticos",
                tipo="diagnostico_api",
                payload={"session_id": "test_regresion_worker", "sintoma": "falla test"},
            )
            trabajo_id = trabajo.id

    worker = SystemWorker(gestor=object())  # type: ignore[arg-type]

    # En _procesar simulamos una consulta directa sobre la sesión para forzar autobegin en PostgreSQL
    async def _procesar_con_query(tipo: str, payload: dict, taller_id=None, session=None):
        assert session is not None
        # Esta consulta en SQLAlchemy 2.0 activa la transacción implícita
        await session.execute(text("SELECT 1"))
        return json.dumps({"falla_predicha": "Batería descargada", "confianza": 90.0})

    worker._procesar = _procesar_con_query  # type: ignore[method-assign]

    procesado = await worker.procesar_siguiente()
    assert procesado is True

    # Verificar que en la base de datos PostgreSQL el trabajo quedó completado
    async with AsyncSession(engine, expire_on_commit=False) as session:
        res = await session.execute(
            select(TrabajoSistema).where(TrabajoSistema.id == trabajo_id)
        )
        trabajo_db = res.scalar_one_or_none()
        assert trabajo_db is not None
        assert trabajo_db.estado == "completado"
        resultado_obj = json.loads(trabajo_db.resultado_resumen or "{}")
        assert resultado_obj.get("falla_predicha") == "Batería descargada"

        # Limpiar fila de prueba
        await session.execute(
            text(f"DELETE FROM trabajos_sistema WHERE id = '{trabajo_id}'")
        )
        await session.commit()
