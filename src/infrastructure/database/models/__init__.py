"""Modelos ORM que conforman el esquema relacional de CarBot."""

from src.infrastructure.database.models.access_requests import IdentidadWhatsApp, SolicitudAcceso
from src.infrastructure.database.models.catalogs import Rol, Taller, Usuario
from src.infrastructure.database.models.diagnostics import Diagnostico, HipotesisDiagnostico, Vehiculo
from src.infrastructure.database.models.jobs import TrabajoGemini, TrabajoSistema, WorkerSistema
from src.infrastructure.database.models.messaging import Conversacion, Mensaje
from src.infrastructure.database.models.operations import Auditoria, UsoApi
from src.infrastructure.database.models.validation import ValidacionTaller

__all__ = [
    "Auditoria",
    "Conversacion",
    "Diagnostico",
    "HipotesisDiagnostico",
    "IdentidadWhatsApp",
    "Mensaje",
    "Rol",
    "SolicitudAcceso",
    "Taller",
    "TrabajoGemini",
    "TrabajoSistema",
    "WorkerSistema",
    "UsoApi",
    "Usuario",
    "Vehiculo",
    "ValidacionTaller",
]
