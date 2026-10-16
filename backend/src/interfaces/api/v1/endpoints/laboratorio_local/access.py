"""Acceso local explícito, autenticado y sin proveedores externos."""
import copy
import os
from threading import RLock
from urllib.parse import urlparse

from fastapi import Depends, HTTPException, Request

from src.config import settings
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.security import verificar_jwt_administrador
from src.core.session_manager import SessionManager

_GESTORES_LOCK = RLock()
_HOSTS_LOCALES = {"127.0.0.1", "::1", "localhost"}


def verificar_laboratorio_permitido(request: Request) -> None:
    """Falla cerrado incluso con opt-in accidental en producción."""
    if settings.is_production or not settings.enable_laboratory:
        raise HTTPException(403, "Laboratorio de pruebas deshabilitado en entornos de producción o sin autorización explícita.")
    if settings.environment not in {"test", "development", "local"}:
        raise HTTPException(403, "Entorno no autorizado para laboratorio.")
    host = request.client.host if request.client else ""
    if host not in _HOSTS_LOCALES and not (host == "testclient" and settings.environment == "test"):
        raise HTTPException(403, "Laboratorio restringido a conexiones locales.")
    origin = request.headers.get("origin")
    if origin and urlparse(origin).hostname not in _HOSTS_LOCALES:
        raise HTTPException(403, "Origen no autorizado para laboratorio.")
    if os.getenv("CARBOT_BLOCK_DOTENV", "").lower() != "true":
        raise HTTPException(403, "El laboratorio requiere dotenv bloqueado.")
    if settings.gemini_api_key or settings.groq_api_key:
        raise HTTPException(403, "El laboratorio requiere proveedores externos sin credenciales.")


def obtener_gestor(
    request: Request,
    payload: dict = Depends(verificar_jwt_administrador),
) -> GestorDiagnostico:
    """Memoria independiente por taller/usuario autenticado; no comparte sesiones reales."""
    owner = (payload.get("taller_id"), payload.get("usuario_id"))
    if not all(owner):
        raise HTTPException(403, "La identidad debe incluir taller y usuario.")
    with _GESTORES_LOCK:
        managers = getattr(request.app.state, "gestores_laboratorio", None)
        if managers is None:
            managers = {}
            request.app.state.gestores_laboratorio = managers
        if owner not in managers:
            base = getattr(request.app.state, "gestor_diagnostico", None) or GestorDiagnostico()
            if base.api_key:
                raise HTTPException(403, "Gestor con credenciales externas no permitido.")
            lab = copy.copy(base)
            lab.session_manager = SessionManager()
            lab.conversation_repo = InMemoryConversationRepository()
            managers[owner] = lab
        # Alias de compatibilidad para inspección local; las peticiones resuelven por owner.
        request.app.state.gestor_laboratorio = managers[owner]
        return managers[owner]
