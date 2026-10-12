"""Módulo de interpretación contextual de respuestas cortas, ambiguas y 'no sé' en WhatsApp.

Fachada modular y retrocompatible.
"""

from __future__ import annotations

from src.core.conversacion.respuestas_cortas.extractor_mediciones import (
    extraer_medicion,
    extraer_medicion_fragmento,
    extraer_todas_mediciones,
    resolver_condicion_fragmento,
)
from src.core.conversacion.respuestas_cortas.interprete_intenciones import (
    interpretar_respuesta_corta,
)
from src.core.conversacion.respuestas_cortas.patrones_deteccion import (
    CUES_RESPUESTA_CORTA,
    PATRON_AMBIGUO,
    PATRON_NO_APLICA,
    PATRON_NO_SE,
    PATRON_NUMERICO_MEDICION,
    PATRON_OPCION_NUMERICA,
    es_respuesta_corta,
)


class InterpreteRespuestasCortas:
    """Interpreta respuestas breves del usuario respecto a la última pregunta formulada."""

    es_respuesta_corta = staticmethod(es_respuesta_corta)
    _extraer_medicion = staticmethod(extraer_medicion)
    _resolver_condicion_fragmento = staticmethod(resolver_condicion_fragmento)
    _extraer_medicion_fragmento = staticmethod(extraer_medicion_fragmento)
    _extraer_todas_mediciones = staticmethod(extraer_todas_mediciones)
    interpretar = staticmethod(interpretar_respuesta_corta)


__all__ = [
    "CUES_RESPUESTA_CORTA",
    "InterpreteRespuestasCortas",
    "PATRON_AMBIGUO",
    "PATRON_NO_APLICA",
    "PATRON_NO_SE",
    "PATRON_NUMERICO_MEDICION",
    "PATRON_OPCION_NUMERICA",
]
