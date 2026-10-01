"""Aplica las restricciones del caso antes de RAG y generación de respuesta."""

from src.core.conversacion.models import ConversationState
from src.core.conversacion.ruteador_sistema import (
    SISTEMA_INYECCION_MEZCLA,
    detectar_ruta_sistema,
)
from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad
from src.core.diagnostico.models import PrediccionML, ResultadoDiagnostico


def filtrar_predicciones(predicciones, texto, sesion=None):
    estado = getattr(sesion, "conversation_state", None)
    if not isinstance(estado, ConversationState):
        estado = ConversationState(session_id="consulta-aislada")
    finales, excluidas = ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
        [p.model_dump() for p in predicciones], estado, texto
    )
    ruta = detectar_ruta_sistema(estado, texto)
    # La ausencia de candidatos es una respuesta segura cuando el mecánico
    # aportó evidencia fuerte de inyección/mezcla incompatible con el Top ML.
    # No debe vaciar diagnósticos de otros sistemas por restricciones de
    # equipamiento que todavía no fueron preguntadas (A/C, arranque, frenos).
    if not finales and ruta.sistema != SISTEMA_INYECCION_MEZCLA:
        motivos = {item.get("motivo") for item in excluidas}
        if motivos <= {"EQUIPAMIENTO_NO_CONFIRMADO"}:
            return list(predicciones), excluidas
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
