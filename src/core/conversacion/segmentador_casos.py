"""Módulo de segmentación automática de casos y aislamiento de contexto (Fase 9.10).

Fachada modular y retrocompatible.
"""

from __future__ import annotations

from src.core.conversacion.segmentacion.detector_subsistemas import (
    detectar_subsistema_texto,
    es_sintoma_coexistente,
    obtener_subsistema_estado,
)
from src.core.conversacion.segmentacion.ejecutor_transicion import (
    archivar_y_limpiar_caso,
    resolver_transicion_turno,
)
from src.core.conversacion.segmentacion.evaluador_reglas import (
    PREGUNTA_ACLARACION_CANONICA,
    es_nueva_queja_principal,
    evaluar_transicion,
)
from src.core.conversacion.segmentacion.tipos import (
    DecisionTransicion,
    SubsistemaVehicular,
    TransicionCasoResultado,
)


class SegmentadorCasos:
    """Evalúa transiciones automáticas de caso diagnóstico basadas en compatibilidad operacional."""

    PREGUNTA_ACLARACION_CANONICA = PREGUNTA_ACLARACION_CANONICA

    detectar_subsistema_texto = staticmethod(detectar_subsistema_texto)
    obtener_subsistema_estado = staticmethod(obtener_subsistema_estado)
    es_sintoma_coexistente = staticmethod(es_sintoma_coexistente)
    es_nueva_queja_principal = staticmethod(es_nueva_queja_principal)
    evaluar_transicion = staticmethod(evaluar_transicion)
    archivar_y_limpiar_caso = staticmethod(archivar_y_limpiar_caso)
    resolver_transicion_turno = staticmethod(resolver_transicion_turno)


__all__ = [
    "DecisionTransicion",
    "SegmentadorCasos",
    "SubsistemaVehicular",
    "TransicionCasoResultado",
]
