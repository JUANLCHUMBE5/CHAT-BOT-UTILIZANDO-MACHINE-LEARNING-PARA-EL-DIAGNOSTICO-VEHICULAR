"""Modelos del estado conversacional y trazabilidad diagnóstica."""

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
