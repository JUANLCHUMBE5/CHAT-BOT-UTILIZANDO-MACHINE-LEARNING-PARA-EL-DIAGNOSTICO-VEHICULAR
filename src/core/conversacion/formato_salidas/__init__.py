"""Subpaquete de formateo de salidas y respuestas para WhatsApp."""

from src.core.conversacion.formato_salidas.acciones_prioritarias import (
    es_paso_preparatorio,
    extraer_accion_prioritaria,
    generar_pregunta_contextual,
    simplificar_nombre_falla,
)
from src.core.conversacion.formato_salidas.detalle_tecnico import (
    formatear_detalle_tecnico,
)
from src.core.conversacion.formato_salidas.generador_diagnostico import (
    calcular_scores_presentacion,
    evitar_respuesta_repetida,
    formatear_respuesta_diagnostico,
    integrar_respuesta_llm,
    obtener_pregunta_contextual,
)
from src.core.conversacion.formato_salidas.orientacion_abstencion import (
    formatear_orientacion_abstencion,
)

__all__ = [
    "calcular_scores_presentacion",
    "es_paso_preparatorio",
    "evitar_respuesta_repetida",
    "extraer_accion_prioritaria",
    "formatear_detalle_tecnico",
    "formatear_orientacion_abstencion",
    "formatear_respuesta_diagnostico",
    "generar_pregunta_contextual",
    "integrar_respuesta_llm",
    "obtener_pregunta_contextual",
    "simplificar_nombre_falla",
]
