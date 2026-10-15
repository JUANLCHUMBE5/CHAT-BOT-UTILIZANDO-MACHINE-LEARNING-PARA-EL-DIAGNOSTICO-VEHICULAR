"""Generador de preguntas discriminantes Top-3, comprobación already_known y regla anti-loop (Adenda 9.1).

Fachada modular y retrocompatible.
"""

from __future__ import annotations

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


class GeneradorPreguntas:
    """Gestiona la formulación de preguntas discriminantes y garantiza el escape de bucles."""

    permite_caracterizar_ruido_suspension = staticmethod(permite_caracterizar_ruido_suspension)
    already_known = staticmethod(already_known)
    obtener_siguiente_pregunta_tecnica = staticmethod(obtener_siguiente_pregunta_tecnica)
    pregunta_por_area = staticmethod(pregunta_por_area)
    falta_medicion_discriminante_por_area = staticmethod(falta_medicion_discriminante_por_area)
    formular_pregunta_discriminante_post_descarte = staticmethod(formular_pregunta_discriminante_post_descarte)
    puede_preguntar = staticmethod(puede_preguntar)
    es_pregunta_compatible = staticmethod(es_pregunta_compatible)
    generar_pregunta_discriminante_top3 = staticmethod(generar_pregunta_discriminante_top3)
    seleccionar_pregunta_con_filtro = staticmethod(seleccionar_pregunta_con_filtro)
    generar_pregunta_aclaratoria_inicial = staticmethod(generar_pregunta_aclaratoria_inicial)
    construir_salida_limite_repreguntas = staticmethod(construir_salida_limite_repreguntas)


__all__ = ["GeneradorPreguntas"]
