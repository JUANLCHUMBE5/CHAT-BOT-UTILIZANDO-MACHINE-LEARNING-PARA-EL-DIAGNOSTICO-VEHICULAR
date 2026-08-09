import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Cargar variables de entorno de .env antes de importar settings
load_dotenv()

import pytest
from src.limiter import limiter
from src.config import settings
from src.core.gemini_queue import gemini_rate_limiter

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
    return settings.database.enabled and _nombre_base_configurada().endswith("_test")


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
    }
    if request.path.name in modulos_integracion_db and not _es_base_pruebas_segura():
        pytest.skip(
            "Integracion PostgreSQL bloqueada: configure TEST_DATABASE_URL hacia una base *_test."
        )
    if request.path.name not in modulos_integracion_db:
        monkeypatch.setattr(settings.database, "enabled", False)
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
def mock_gemini_en_todas_las_pruebas(monkeypatch):
    """
    Bloquea rigurosamente cualquier llamada externa a Google Gemini en los tests automáticos.
    Evita cobros, consumo de cuota real y dependencia de conexión a internet durante pruebas.
    """
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
