"""Módulo de comprensión semántica con LLM y fallback determinista."""

from src.core.conversacion.comprension_semantica.contratos import (
    EstadoHechoSemantico,
    HechoSemantico,
    IntencionConversacional,
    InterpretacionSemantica,
    TipoHechoSemantico,
)
from src.core.conversacion.comprension_semantica.interprete import (
    interpretar_mensaje_usuario,
)

__all__ = [
    "EstadoHechoSemantico",
    "HechoSemantico",
    "InterpretacionSemantica",
    "IntencionConversacional",
    "TipoHechoSemantico",
    "interpretar_mensaje_usuario",
]
