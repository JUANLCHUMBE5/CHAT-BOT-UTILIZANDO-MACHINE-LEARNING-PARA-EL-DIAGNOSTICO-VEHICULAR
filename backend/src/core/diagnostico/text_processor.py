"""Procesamiento y orquestación secuencial de consultas de texto para diagnóstico y consultas técnicas.

Fachada modular y retrocompatible.
"""

from __future__ import annotations

from src.core.diagnostico.procesador_texto import (
    procesar_consulta_tecnica,
    procesar_consulta_texto,
)

__all__ = [
    "procesar_consulta_tecnica",
    "procesar_consulta_texto",
]
