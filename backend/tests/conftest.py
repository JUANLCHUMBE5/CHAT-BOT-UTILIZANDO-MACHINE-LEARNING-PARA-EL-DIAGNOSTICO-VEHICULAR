import asyncio
import os
import uuid
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

# Cargar variables de entorno de .env antes de importar settings
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Configuración determinista y exclusiva del proceso de pruebas.
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET_KEY"] = "test_jwt_secret_key_with_more_than_32_chars"
os.environ["PRIVACY_SECRET_KEY"] = "test_privacy_secret_with_more_than_32_chars"
os.environ["LOCAL_AUTH_USERNAME"] = "admin"
os.environ["LOCAL_AUTH_PASSWORD"] = "carbot2026"

import pytest

from src.config import settings
from src.core.access_token_store import access_token_store
from src.core.gemini_queue import gemini_rate_limiter
from src.core.login_attempt_store import login_attempt_store
from src.core.refresh_token_store import refresh_token_store
from src.limiter import limiter

# Asegurar habilitación de base de datos para pruebas si están configuradas
test_database_url = os.getenv("TEST_DATABASE_URL", "").strip()
if test_database_url:
    settings.database.enabled = True
    settings.database.required = True
    settings.database.url = test_database_url
    settings.database.database = urlparse(test_database_url).path.lstrip("/")
elif os.getenv("DATABASE_ENABLED", "false").lower() in ("1", "true", "yes", "si"):
    settings.database.enabled = True
    settings.database.url = os.getenv("DATABASE_URL", "")
    settings.database.host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    settings.database.port = int(os.getenv("POSTGRES_PORT", 5433))
    settings.database.database = os.getenv("POSTGRES_DB", "carbot_db")
    settings.database.user = os.getenv("POSTGRES_USER", "carbot_app")
settings.database.pool_size = 0


def _nombre_base_configurada() -> str:
    if settings.database.url:
        return urlparse(str(settings.database.url)).path.lstrip("/").lower()
    return settings.database.database.lower()


def _es_base_pruebas_segura() -> bool:
    if not settings.database.enabled:
        return False
    nombre = _nombre_base_configurada()
    return nombre.endswith("_test")


def pytest_sessionstart(session):
    """Limpia exclusivamente la base *_test antes de iniciar la suite.

    Nunca se permite truncar carbot_db, postgres ni cualquier base sin el
    sufijo explícito ``_test``.
    """
    if not _es_base_pruebas_segura():
        return

    async def _limpiar() -> None:
        from sqlalchemy import text

        from src.infrastructure.database.connection import obtener_engine

        engine = obtener_engine()
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "TRUNCATE TABLE talleres, trabajos_gemini, trabajos_sistema, workers_sistema, "
                    "cuotas_gemini_global RESTART IDENTITY CASCADE"
                )
            )
            await connection.execute(
                text(
                    "INSERT INTO talleres "
                    "(id, nombre, direccion, telefono, horario_atencion, servicios, "
                    "telefono_id_meta, activo, creado_en, actualizado_en) "
                    "VALUES (:id, :nombre, :direccion, :telefono, :horario, :servicios, "
                    ":telefono_id_meta, true, now(), now())"
                ),
                {
                    "id": uuid.uuid4(),
                    "nombre": "Taller Automatizado de Pruebas",
                    "direccion": "Dirección exclusiva de pruebas",
                    "telefono": "+51000000000",
                    "horario": "Horario de pruebas",
                    "servicios": "Servicios de pruebas",
                    "telefono_id_meta": settings.meta_phone_number_id or "META_TEST_DEFAULT",
                },
            )
        await engine.dispose()

    asyncio.run(_limpiar())


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """
    Fixture autouse que reinicia los contadores del Limiter de SlowAPI y Gemini Rate Limiter
    antes de cada prueba, evitando contaminación entre tests.
    """
    try:
        limiter.reset()
    except Exception:
        if hasattr(limiter, "_storage") and hasattr(limiter._storage, "reset"):
            limiter._storage.reset()
    gemini_rate_limiter.reiniciar()
    login_attempt_store.reiniciar_local()
    refresh_token_store.reiniciar_local()
    access_token_store.reiniciar_local()
    yield


@pytest.fixture(autouse=True)
def aislar_postgresql_en_pruebas_unitarias(request, monkeypatch):
    """Evita que webhooks unitarios escriban en la base local del desarrollador."""
    modulos_integracion_db = {
        "test_database_connection.py",
        "test_database_models.py",
        "test_database_repositories.py",
        "test_webhook_persistence.py",
        "test_cli_registrar_admin.py",
        "test_gemini_rate_limiting.py",
        "test_dashboard_postgresql_integration.py",
        "test_flujo_cliente_mecanico.py",
    }
    if request.path.name in modulos_integracion_db and not _es_base_pruebas_segura():
        pytest.skip(
            "Integracion PostgreSQL bloqueada: configure TEST_DATABASE_URL hacia una base *_test."
        )
    if request.path.name not in modulos_integracion_db:
        monkeypatch.setattr(settings.database, "enabled", False)
    yield


@pytest.fixture(autouse=True)
def aislar_estado_persistente_gemini(request):
    """Evita que un caso de cola/cuota altere el orden esperado por el siguiente."""
    if request.path.name != "test_gemini_rate_limiting.py" or not _es_base_pruebas_segura():
        yield
        return

    async def _limpiar() -> None:
        from sqlalchemy import text

        from src.infrastructure.database.connection import obtener_engine

        engine = obtener_engine()
        async with engine.begin() as connection:
            await connection.execute(text("DELETE FROM trabajos_gemini"))
            await connection.execute(text("DELETE FROM cuotas_gemini_global"))

    asyncio.run(_limpiar())
    yield


@pytest.fixture
async def async_db_session():
    """Entrega una sesión asíncrona conectada a PostgreSQL para pruebas de integración."""
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.infrastructure.database.connection import database_configurada, obtener_engine

    if not database_configurada() or not _es_base_pruebas_segura():
        pytest.skip("PostgreSQL no está configurado para pruebas.")

    engine = obtener_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture(autouse=True)
def mock_gemini_en_todas_las_pruebas(request, monkeypatch):
    """
    Bloquea rigurosamente cualquier llamada externa a Google Gemini en los tests automáticos,
    excepto en pruebas explícitas de integración real con Gemini.
    """
    if "real_gemini" in request.keywords:
        yield
        return

    import requests

    def mocked_requests_post(url, *args, **kwargs):
        if "generativelanguage.googleapis.com" in str(url):
            class MockGeminiResponse:
                status_code = 200

                def json(self):
                    return {
                        "candidates": [{
                            "content": {
                                "parts": [{
                                    "text": (
                                        "🛠️ **1. Posible Falla Vehicular**\n"
                                        "• **Diagnóstico Sugerido (ML):** Falla en el sistema de frenos\n"
                                        "• **Certeza:** 85%\n\n"
                                        "📖 **2. Procedimiento Técnico de Reparación**\n"
                                        "1. Inspeccionar pastillas y discos de freno.\n"
                                        "2. Realizar purga y verificación de líquido de frenos.\n\n"
                                        "⏱️ **3. Tiempo Estimado y Gravedad**\n"
                                        "• **Tiempo Estimado:** 45-60 minutos\n"
                                        "• **Gravedad:** Alta (requiere atención prioritaria)"
                                    )
                                }]
                            }
                        }],
                        "usageMetadata": {
                            "promptTokenCount": 110,
                            "candidatesTokenCount": 140,
                            "totalTokenCount": 250,
                        },
                    }

            return MockGeminiResponse()
        if "graph.facebook.com" in str(url):
            class MockMetaResponse:
                status_code = 200
                content = b'{"messages":[{"id":"wamid.mock"}]}'
                def json(self):
                    return {"messages": [{"id": "wamid.mock"}]}
            return MockMetaResponse()
        if "api.twilio.com" in str(url):
            class MockTwilioResponse:
                status_code = 201
                content = b'{"sid":"SMmock"}'
                def json(self):
                    return {"sid": "SMmock"}
            return MockTwilioResponse()
        raise AssertionError(f"Llamada HTTP externa no simulada durante pruebas: {url}")

    monkeypatch.setattr(requests, "post", mocked_requests_post)
    yield


@pytest.fixture(autouse=True)
def isolate_tracker_csv(tmp_path, monkeypatch):
    """
    Fixture autouse que aisla las pruebas utilizando un archivo tracker CSV temporal en tmp_path.
    Previene totalmente la contaminación del archivo data/tracker_diagnosticos.csv del repositorio.
    """
    temp_tracker = tmp_path / "tracker_diagnosticos.csv"
    original_tracker = settings.paths.tracker_csv
    if os.path.exists(original_tracker):
        with open(original_tracker, "r", encoding="utf-8") as f:
            header = f.readline()
        with open(temp_tracker, "w", encoding="utf-8") as f:
            f.write(header)
    else:
        with open(temp_tracker, "w", encoding="utf-8") as f:
            f.write(
                "id,momento,fecha,placa,vehiculo,sintoma,diagnostico_ml,falla_real,campos_completos,ml_coincide,conforme_con_diagnostico\n"
            )

    monkeypatch.setattr(settings.paths, "tracker_csv", temp_tracker)
    yield
