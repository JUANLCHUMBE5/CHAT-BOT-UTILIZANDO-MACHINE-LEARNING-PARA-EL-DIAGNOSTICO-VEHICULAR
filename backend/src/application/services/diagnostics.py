"""Punto de entrada estable del caso de uso de diagnóstico.

La implementación permanece temporalmente en ``src.core`` para que el cambio
de arquitectura no altere el comportamiento en producción.
"""

from src.core.gestor_diagnostico import (
    GestorDiagnostico,
    PrediccionML,
    ResultadoDiagnostico,
)

__all__ = ["GestorDiagnostico", "PrediccionML", "ResultadoDiagnostico"]
