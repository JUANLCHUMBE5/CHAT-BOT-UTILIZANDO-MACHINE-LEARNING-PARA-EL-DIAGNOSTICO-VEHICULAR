"""Fachada compatible del laboratorio local; acceso deshabilitado por defecto."""
from .laboratorio_local.routes import router

__all__ = ["router"]
