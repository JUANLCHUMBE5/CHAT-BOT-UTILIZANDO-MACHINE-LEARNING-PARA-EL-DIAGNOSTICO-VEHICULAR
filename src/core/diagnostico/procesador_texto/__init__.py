"""Subpaquete de procesamiento y orquestación de consultas de diagnóstico y técnicas."""

from src.core.diagnostico.procesador_texto.consulta_tecnica import (
    procesar_consulta_tecnica,
)
from src.core.diagnostico.procesador_texto.orquestador_diagnostico import (
    procesar_consulta_texto,
)

__all__ = [
    "procesar_consulta_tecnica",
    "procesar_consulta_texto",
]
