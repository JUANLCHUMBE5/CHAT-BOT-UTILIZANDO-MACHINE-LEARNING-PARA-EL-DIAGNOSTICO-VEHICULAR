"""Modelos y tipos de datos para la memoria conversacional estructurada de CarBot (Fase 9.1).

Fachada retrocompatible: todos los tipos continúan exportándose desde este módulo.
"""

from __future__ import annotations

from src.core.conversacion.state_models.enums import (
    ConversationPhase,
    DtcStatus,
    EstadoOperativo,
    EvidenceLevel,
    FactState,
    FactType,
    QuestionIntent,
)
from src.core.conversacion.state_models.facts import DiagnosticFact
from src.core.conversacion.state_models.state import ConversationState
from src.core.conversacion.state_models.trace import TurnTrace

__all__ = [
    "ConversationPhase",
    "ConversationState",
    "DiagnosticFact",
    "DtcStatus",
    "EstadoOperativo",
    "EvidenceLevel",
    "FactState",
    "FactType",
    "QuestionIntent",
    "TurnTrace",
]
