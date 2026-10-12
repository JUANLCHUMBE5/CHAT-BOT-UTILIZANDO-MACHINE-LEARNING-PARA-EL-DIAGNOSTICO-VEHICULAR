"""Formateador de respuestas conversacionales compactas para WhatsApp (Fase 9.3).

Fachada modular y retrocompatible.
"""

from __future__ import annotations

from src.core.conversacion.formato_salidas import (
    calcular_scores_presentacion,
    es_paso_preparatorio,
    evitar_respuesta_repetida,
    extraer_accion_prioritaria,
    formatear_detalle_tecnico,
    formatear_orientacion_abstencion,
    formatear_respuesta_diagnostico,
    generar_pregunta_contextual,
    integrar_respuesta_llm,
    obtener_pregunta_contextual,
    simplificar_nombre_falla,
)

# Aliases privados retrocompatibles
_simplificar_nombre_falla = simplificar_nombre_falla
_extraer_accion_prioritaria = extraer_accion_prioritaria
_generar_pregunta_contextual = generar_pregunta_contextual
_es_paso_preparatorio = es_paso_preparatorio


class FormateadorCompacto:
    """Formateador oficial de salidas compactas para WhatsApp."""

    simplificar_nombre_falla = staticmethod(simplificar_nombre_falla)
    extraer_accion_prioritaria = staticmethod(extraer_accion_prioritaria)
    generar_pregunta_contextual = staticmethod(generar_pregunta_contextual)
    integrar_respuesta_llm = staticmethod(integrar_respuesta_llm)
    evitar_respuesta_repetida = staticmethod(evitar_respuesta_repetida)
    calcular_scores_presentacion = staticmethod(calcular_scores_presentacion)
    formatear_orientacion_abstencion = staticmethod(formatear_orientacion_abstencion)
    formatear_respuesta_diagnostico = staticmethod(formatear_respuesta_diagnostico)
    obtener_pregunta_contextual = staticmethod(obtener_pregunta_contextual)
    formatear_detalle_tecnico = staticmethod(formatear_detalle_tecnico)


__all__ = [
    "FormateadorCompacto",
    "_es_paso_preparatorio",
    "_extraer_accion_prioritaria",
    "_generar_pregunta_contextual",
    "_simplificar_nombre_falla",
    "calcular_scores_presentacion",
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
