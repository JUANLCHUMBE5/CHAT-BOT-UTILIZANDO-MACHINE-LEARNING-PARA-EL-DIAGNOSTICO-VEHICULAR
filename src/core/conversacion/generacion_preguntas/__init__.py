"""Subpaquete de generación y selección de preguntas discriminantes."""

from src.core.conversacion.generacion_preguntas.candidatas import (
    construir_salida_limite_repreguntas,
    formular_pregunta_discriminante_post_descarte,
    generar_pregunta_discriminante_top3,
)
from src.core.conversacion.generacion_preguntas.compatibilidad import (
    es_pregunta_compatible,
    puede_preguntar,
)
from src.core.conversacion.generacion_preguntas.known_checker import (
    already_known,
    falta_medicion_discriminante_por_area,
    obtener_siguiente_pregunta_tecnica,
    permite_caracterizar_ruido_suspension,
    pregunta_por_area,
)
from src.core.conversacion.generacion_preguntas.selector import (
    generar_pregunta_aclaratoria_inicial,
    seleccionar_pregunta_con_filtro,
)

__all__ = [
    "already_known",
    "construir_salida_limite_repreguntas",
    "es_pregunta_compatible",
    "falta_medicion_discriminante_por_area",
    "formular_pregunta_discriminante_post_descarte",
    "generar_pregunta_aclaratoria_inicial",
    "generar_pregunta_discriminante_top3",
    "obtener_siguiente_pregunta_tecnica",
    "permite_caracterizar_ruido_suspension",
    "pregunta_por_area",
    "puede_preguntar",
    "seleccionar_pregunta_con_filtro",
]
