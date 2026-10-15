"""Compatibilidad física previa a preguntas, documentos y respuestas REST."""
from copy import deepcopy
from typing import Any

from src.core.conversacion.models import ConversationState
from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad
from src.core.vehicle_profile import extraer_datos_vehiculo


def filtrar_predicciones_compatibles(texto: str, predicciones: list, sesion: Any = None) -> tuple[list, list]:
    estado = deepcopy(getattr(sesion, "conversation_state", None)) or ConversationState(session_id="compatibilidad")
    perfil = extraer_datos_vehiculo(texto)
    for campo in ("combustible", "transmision"):
        if perfil.get(campo):
            setattr(estado, campo, perfil[campo])
    compatibles = []
    exclusiones = []
    for prediccion in predicciones:
        valido, motivo = ValidadorCompatibilidad.validar_compatibilidad_hipotesis(prediccion.falla, estado)
        if valido:
            compatibles.append(prediccion)
        else:
            exclusiones.append({"falla": prediccion.falla, "probabilidad_raw": prediccion.probabilidad,
                                "motivo": motivo})
    return compatibles, exclusiones
