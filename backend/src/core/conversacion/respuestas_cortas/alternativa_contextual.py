"""Conserva el componente observado cuando falta una medición o una herramienta."""
import re

from src.core.conversacion.aislamiento_subsistemas import normalizar
from src.core.conversacion.models import QuestionIntent


def alternativa_por_evidencia(estado):
    texto = normalizar(' '.join(estado.active_symptoms + estado.historial_mensajes_usuario))
    if re.search(r'\b(?:sensor map|carga absoluta|presion absoluta)\b', texto):
        return (
            'lectura de MAP pendiente; inspección externa sin abrir circuitos',
            'Mantengo pendiente la medición del MAP; no confirmaré una causa sin una lectura y su condición. '
            'Sin equipo, no supongas que falló la bomba de combustible ni sustituyas el sensor. '
            'Con el motor apagado y frío, ¿hay daños visibles en el conector o la manguera del MAP? '
            'Si no puedes inspeccionarlo con seguridad, solicita la prueba con equipo y manual aplicable.',
            QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
        )
    if estado.obtener_hecho('caudal_inyectores_reportado') is not None:
        return (
            'contrastar el informe de caudal/patrón de pulverización de inyectores',
            'Conservo el caudal insuficiente de inyectores como hallazgo reportado, sin confirmar una avería. '
            '¿Ese caudal/patrón de pulverización proviene de una prueba de banco o de una observación sin medición? '
            'Si no dispones del equipo, deja pendiente esa comprobación y deriva la prueba; '
            'no abras líneas presurizadas ni pruebes pulverización con el motor funcionando.',
            QuestionIntent.COMPONENTE_REVISADO,
        )
    return None
