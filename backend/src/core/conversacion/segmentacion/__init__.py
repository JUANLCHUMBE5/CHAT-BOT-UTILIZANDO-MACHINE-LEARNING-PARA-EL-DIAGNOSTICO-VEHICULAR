"""Subpaquete de segmentación de casos y aislamiento de contexto automotriz."""

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

__all__ = [
    "PREGUNTA_ACLARACION_CANONICA",
    "DecisionTransicion",
    "SubsistemaVehicular",
    "TransicionCasoResultado",
    "archivar_y_limpiar_caso",
    "detectar_subsistema_texto",
    "es_nueva_queja_principal",
    "es_sintoma_coexistente",
    "evaluar_transicion",
    "obtener_subsistema_estado",
    "resolver_transicion_turno",
]
