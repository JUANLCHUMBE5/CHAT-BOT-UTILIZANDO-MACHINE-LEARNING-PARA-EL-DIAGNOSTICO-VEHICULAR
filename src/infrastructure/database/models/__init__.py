"""Modelos ORM que conforman el esquema relacional de CarBot."""

from src.infrastructure.database.models.catalogs import Rol, Taller, Usuario
from src.infrastructure.database.models.diagnostics import Diagnostico, HipotesisDiagnostico, Vehiculo
from src.infrastructure.database.models.jobs import TrabajoGemini
from src.infrastructure.database.models.messaging import Conversacion, Mensaje
from src.infrastructure.database.models.operations import Auditoria, UsoApi

__all__ = [
    "Auditoria",
    "Conversacion",
    "Diagnostico",
    "HipotesisDiagnostico",
    "Mensaje",
    "Rol",
    "Taller",
    "TrabajoGemini",
    "UsoApi",
    "Usuario",
    "Vehiculo",
]
