"""Paquete de memoria conversacional y auto-interrogador inteligente para CarBot (Fase 9.1)."""

from src.core.conversacion.diccionario_automotriz import (
    extraer_hechos_linguisticos,
    normalizar_jerga_automotriz,
)
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas
from src.core.conversacion.maquina_estados import MaquinaEstadosConversacion
from src.core.conversacion.models import (
    ConversationPhase,
    ConversationState,
    DiagnosticFact,
    DtcStatus,
    EvidenceLevel,
    FactState,
    FactType,
    QuestionIntent,
    TurnTrace,
)
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import (
    ConversationStateRepository,
    InMemoryConversationRepository,
    PostgresConversationRepository,
)
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta
from src.core.conversacion.suficiencia_informacion import EvaluadorSuficiencia

__all__ = [
    "ConversationPhase",
    "ConversationState",
    "DiagnosticFact",
    "FactState",
    "EvidenceLevel",
    "DtcStatus",
    "FactType",
    "QuestionIntent",
    "TurnTrace",
    "normalizar_jerga_automotriz",
    "extraer_hechos_linguisticos",
    "ExtractorHechos",
    "InterpreteRespuestasCortas",
    "EvaluadorSuficiencia",
    "GeneradorPreguntas",
    "SintetizadorConsulta",
    "MaquinaEstadosConversacion",
    "ConversationStateRepository",
    "InMemoryConversationRepository",
    "PostgresConversationRepository",
    "OrquestadorConversacion",
]
