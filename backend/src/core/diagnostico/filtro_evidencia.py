"""Aplica las restricciones del caso antes de RAG y generación de respuesta."""

from src.core.conversacion.models import ConversationState
from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad
from src.core.diagnostico.models import PrediccionML, ResultadoDiagnostico


def filtrar_predicciones(predicciones, texto, sesion=None):
    estado = getattr(sesion, "conversation_state", None)
    if not isinstance(estado, ConversationState):
        estado = ConversationState(session_id="consulta-aislada")
    finales, excluidas = ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
        [p.model_dump() for p in predicciones], estado, texto
    )
    return [PrediccionML(**p) for p in finales], excluidas


def resultado_sin_candidatas(texto, originales):
    return ResultadoDiagnostico(
        respuesta_texto=(
            "La evidencia registrada no respalda las hipótesis propuestas por el modelo. "
            "Conservo las pruebas y los descartes del caso. Es necesaria una revisión técnica "
            "para identificar la causa; no corresponde confirmar una falla ni cambiar piezas todavía."
        ),
        diagnostico_ml="Sin hipótesis compatible: requiere revisión técnica",
        confianza_ml=0.0, contexto_manual="", titulo_manual="",
        predicciones_ml=[], predicciones_ml_raw=originales,
        requiere_revision_humana=True, modo_diagnostico="baja_confianza",
        sintoma_evaluado=texto,
    )
