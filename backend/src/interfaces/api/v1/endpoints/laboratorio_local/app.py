"""Entrada ASGI independiente; nunca se incorpora a la API pública."""
from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

from src.config import settings


def create_laboratory_app() -> FastAPI:
    app = FastAPI(title="CarBot - laboratorio LOCAL", docs_url=None, redoc_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])
    if (
        settings.enable_laboratory
        and not settings.is_production
        and settings.environment in {"test", "development", "local"}
    ):
        from .routes import router
        app.include_router(router, prefix="/api/v1/laboratorio")
    return app
