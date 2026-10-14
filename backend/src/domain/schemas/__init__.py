"""Contratos y esquemas de dominio para el flujo conversacional y diagnóstico de CarBot."""

from .conversation_contracts import (
    DiagnosticOutputDTO,
    HechoClinico,
    IntentType,
    MedicionTecnica,
    UserTurnInputDTO,
    VehiculoIdentificado,
)

__all__ = [
    "DiagnosticOutputDTO",
    "HechoClinico",
    "IntentType",
    "MedicionTecnica",
    "UserTurnInputDTO",
    "VehiculoIdentificado",
]
