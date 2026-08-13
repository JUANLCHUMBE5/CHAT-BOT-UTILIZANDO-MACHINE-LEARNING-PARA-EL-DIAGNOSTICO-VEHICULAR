"""Conexión asíncrona y pool de sesiones para PostgreSQL."""

import asyncio
from collections.abc import AsyncIterator
from typing import Optional

from sqlalchemy import URL, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.config import settings

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
_bound_loop: Optional[asyncio.AbstractEventLoop] = None


def database_configurada() -> bool:
    """Indica si la aplicación debe utilizar PostgreSQL."""

    return settings.database.enabled


def construir_url_postgresql() -> URL:
    """Construye la URL sin concatenar ni registrar la contraseña manualmente."""

    config = settings.database
    if config.url:
        url = make_url(config.url)
        if url.drivername == "postgresql":
            url = url.set(drivername="postgresql+asyncpg")
        if url.drivername != "postgresql+asyncpg":
            raise ValueError("DATABASE_URL debe utilizar PostgreSQL con el driver asyncpg.")
        return url

    password = config.password.get_secret_value()
    if not password:
        raise RuntimeError("Falta POSTGRES_PASSWORD para conectar con PostgreSQL.")

    return URL.create(
        drivername="postgresql+asyncpg",
        username=config.user,
        password=password,
        host=config.host,
        port=config.port,
        database=config.database,
    )


def obtener_engine() -> AsyncEngine:
    """Crea o reutiliza la instancia del engine ligada al event loop actual."""

    global _engine, _session_factory, _bound_loop

    if not database_configurada():
        raise RuntimeError("PostgreSQL está desactivado. Configure DATABASE_ENABLED=true.")

    try:
        loop_actual = asyncio.get_running_loop()
    except RuntimeError:
        loop_actual = None

    if _engine is None or _bound_loop != loop_actual or (_bound_loop is not None and _bound_loop.is_closed()):
        config = settings.database
        pool_kwargs = {}
        if config.pool_size <= 0:
            pool_kwargs["poolclass"] = NullPool
        else:
            pool_kwargs["pool_size"] = config.pool_size
            pool_kwargs["max_overflow"] = config.max_overflow
            pool_kwargs["pool_timeout"] = config.pool_timeout_seconds

        _engine = create_async_engine(
            construir_url_postgresql(),
            echo=config.echo_sql,
            pool_pre_ping=True,
            **pool_kwargs,
        )
        _bound_loop = loop_actual
        _session_factory = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _engine


async def obtener_sesion_db() -> AsyncIterator[AsyncSession]:
    """Dependencia FastAPI que entrega una sesión y controla commit/rollback."""

    obtener_engine()
    if _session_factory is None:
        raise RuntimeError("No se pudo inicializar la fábrica de sesiones PostgreSQL.")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def comprobar_conexion() -> None:
    """Ejecuta SELECT 1 y genera una excepción si PostgreSQL no responde."""

    async with obtener_engine().connect() as connection:
        await connection.execute(text("SELECT 1"))


async def cerrar_conexion() -> None:
    """Libera el pool de conexiones durante el apagado de FastAPI."""

    global _engine, _session_factory, _bound_loop
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
    _bound_loop = None
