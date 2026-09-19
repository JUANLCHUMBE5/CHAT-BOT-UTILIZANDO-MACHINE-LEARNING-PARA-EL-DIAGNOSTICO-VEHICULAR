import pytest
from pydantic import SecretStr

from src.config import settings
from src.infrastructure.database.connection import construir_url_postgresql, database_configurada


def test_database_desactivada_por_configuracion(monkeypatch):
    monkeypatch.setattr(settings.database, "enabled", False)
    assert database_configurada() is False


def test_construir_url_postgresql_por_campos(monkeypatch):
    monkeypatch.setattr(settings.database, "url", "")
    monkeypatch.setattr(settings.database, "host", "127.0.0.1")
    monkeypatch.setattr(settings.database, "port", 5432)
    monkeypatch.setattr(settings.database, "database", "carbot_db")
    monkeypatch.setattr(settings.database, "user", "carbot_app")
    monkeypatch.setattr(settings.database, "password", SecretStr("clave local segura"))

    url = construir_url_postgresql()

    assert url.drivername == "postgresql+asyncpg"
    assert url.host == "127.0.0.1"
    assert url.port == 5432
    assert url.database == "carbot_db"
    assert url.username == "carbot_app"


def test_rechazar_driver_no_postgresql(monkeypatch):
    monkeypatch.setattr(settings.database, "url", "sqlite+aiosqlite:///:memory:")

    with pytest.raises(ValueError, match="PostgreSQL"):
        construir_url_postgresql()
