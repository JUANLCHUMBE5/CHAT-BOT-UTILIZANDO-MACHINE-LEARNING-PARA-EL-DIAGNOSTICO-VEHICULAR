"""Ejecución y resolución de transiciones de caso conversacional."""

from __future__ import annotations

import re
import time
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import QuestionIntent, TurnTrace
from src.core.conversacion.segmentacion.detector_subsistemas import (
    detectar_subsistema_texto,
    obtener_subsistema_estado,
)
from src.core.conversacion.segmentacion.evaluador_reglas import (
    PREGUNTA_ACLARACION_CANONICA,
    evaluar_transicion,
)
from src.core.conversacion.segmentacion.tipos import (
    DecisionTransicion,
    SubsistemaVehicular,
    TransicionCasoResultado,
)
from src.core.version import ORCHESTRATOR_VERSION

if TYPE_CHECKING:
    from src.core.conversacion.models import ConversationState


def archivar_y_limpiar_caso(
    estado: ConversationState,
    nuevo_case_id: Optional[str] = None,
    preservar_vehiculo: bool = False,
) -> str:
    """Archiva los hechos del caso activo en hechos_historicos y resetea la memoria activa."""
    nuevo_id = nuevo_case_id or str(uuid.uuid4())
    estado.archivar_caso_actual(
        nuevo_id,
        preservar_vehiculo=preservar_vehiculo,
    )
    return nuevo_id


def resolver_transicion_turno(
    estado: ConversationState,
    texto_limpio: str,
    gestor_diagnostico: Any,
    session_id: str,
    t0: float,
    contexto_previo: Dict[str, Any],
    tipo_mensaje: str = "sintoma_nuevo",
) -> Tuple[Optional[Dict[str, Any]], TransicionCasoResultado]:
    """Evalúa y aplica la transición de caso en el estado conversacional."""
    res_op = ExtractorHechos.inferir_estado_operativo(estado, texto_limpio)
    estado_op_det, _, meta_op = res_op[0], res_op[1], res_op[2]

    solicitud_caso = ExtractorHechos.clasificar_solicitud_caso(texto_limpio)
    es_nuevo_caso_explicito = bool(
        solicitud_caso and solicitud_caso.get("accion") == "nuevo_caso"
    )
    texto_normalizado = texto_limpio.casefold().translate(
        str.maketrans("áéíóúüñ", "aeiouun")
    )
    es_presentacion_completa = bool(
        re.search(
            r"\b(?:tengo|ingreso|llego|recibi)\s+(?:un|otro)\s+vehiculo\b|"
            r"\bel\s+cliente\s+(?:comenta|reporta|indica)\b",
            texto_normalizado,
        )
        and detectar_subsistema_texto(texto_limpio) != obtener_subsistema_estado(estado)
    )
    cambio_sistema_declarado = (
        detectar_subsistema_texto(texto_limpio) != SubsistemaVehicular.DESCONOCIDO
        and detectar_subsistema_texto(texto_limpio) != obtener_subsistema_estado(estado)
        and ExtractorHechos.contiene_informacion_diagnostica(texto_limpio)
    )
    if (
        tipo_mensaje not in ("sintoma_nuevo", "correccion_sistema")
        and not es_nuevo_caso_explicito
        and not es_presentacion_completa
        and not cambio_sistema_declarado
        and (estado.hechos or estado.active_symptoms)
    ):
        transicion = TransicionCasoResultado(
            decision=DecisionTransicion.MANTENER_CASO,
            motivo=f"CONTINUIDAD_{tipo_mensaje.upper()}",
            estado_previo=estado.estado_operativo,
            estado_detectado_mensaje=estado_op_det,
        )
    else:
        transicion = evaluar_transicion(
            estado=estado,
            texto_usuario=texto_limpio,
            estado_detectado_mensaje=estado_op_det,
            seniales_mensaje=meta_op.get("seniales_mensaje", {}),
            seniales_heredadas=meta_op.get("seniales_heredadas", {}),
        )
    transicion.dominio_previo = obtener_subsistema_estado(estado)
    if not transicion.motivo.startswith("RECTIFICACION_SISTEMA_"):
        transicion.dominio_detectado_mensaje = detectar_subsistema_texto(texto_limpio)
    else:
        from src.core.conversacion.segmentacion.rectificacion import rectificar_sistema

        rectificar_sistema(estado, texto_limpio, transicion.dominio_detectado_mensaje, estado_op_det)

    if transicion.decision == DecisionTransicion.CAMBIO_DE_CASO:
        archivar_y_limpiar_caso(
            estado,
            transicion.nuevo_case_id,
            preservar_vehiculo=(
                transicion.motivo.startswith("CORRECCION_SISTEMA_")
                or transicion.motivo.endswith("_MISMO_VEHICULO")
            ),
        )
        if transicion.dominio_detectado_mensaje and transicion.dominio_detectado_mensaje != SubsistemaVehicular.DESCONOCIDO:
            estado.dominio_probable = transicion.dominio_detectado_mensaje.value
        if hasattr(gestor_diagnostico, "session_manager") and gestor_diagnostico.session_manager is not None:
            gestor_diagnostico.session_manager.cargar_contexto(
                session_id,
                {"case_id": estado.case_id, "conversation_state": estado.exportar_dict()},
            )
        return None, transicion

    if transicion.decision == DecisionTransicion.ACLARACION_REQUERIDA:
        # Registrar el turno aun cuando sus hechos esperen aclaración de alcance.
        if not estado.historial_mensajes_usuario or estado.historial_mensajes_usuario[-1] != texto_limpio:
            estado.historial_mensajes_usuario.append(texto_limpio)
            estado.turno_actual += 1
        from src.core.conversacion.extraccion_hechos.extraccion_taller import extraer_comprobaciones_taller
        if transicion.dominio_detectado_mensaje != SubsistemaVehicular.DESCONOCIDO:
            # La orientación activa debe corresponder al mensaje actual aunque
            # el alcance del caso todavía espere confirmación del mecánico.
            estado.dominio_probable = transicion.dominio_detectado_mensaje.value
        extraer_comprobaciones_taller(estado, texto_limpio, texto_limpio.lower())
        pregunta_aclarar = transicion.pregunta_aclaracion or PREGUNTA_ACLARACION_CANONICA
        estado.registrar_pregunta(
            intent=QuestionIntent.ACLARACION_ALCANCE,
            texto=pregunta_aclarar,
            incrementar_repregunta=False,
        )
        traza = TurnTrace(
            turno=estado.turno_actual,
            mensaje_original=texto_limpio,
            contexto_previo=contexto_previo,
            decision="ACLARACION_CASO",
            motivo_decision=transicion.motivo,
            respuesta_enviada=pregunta_aclarar,
            hechos_nuevos_extraidos=[],
            hechos_actualizados=[],
            consulta_consolidada="",
            top3=[],
            confianza=1.0,
            estado_operativo=estado.estado_operativo.value,
            question_intent=QuestionIntent.ACLARACION_ALCANCE.value,
            pregunta_final=pregunta_aclarar,
            estado_previo=transicion.estado_previo.value,
            estado_detectado_mensaje_actual=transicion.estado_detectado_mensaje.value,
            decision_transicion=transicion.decision.value,
            motivo_transicion=transicion.motivo,
            dominio_previo=transicion.dominio_previo.value,
            dominio_detectado_actual=transicion.dominio_detectado_mensaje.value,
            dominio_actual=estado.dominio_probable,
            version_orquestador=ORCHESTRATOR_VERSION,
        )
        estado.trazabilidad.append(traza.to_dict())
        ret = {
            "status": "aclaracion_caso",
            "respuesta_texto": pregunta_aclarar,
            "diagnostico_ml": "Aclaración de alcance",
            "confianza_ml": estado.confianza_actual,
            "fase": estado.fase.value,
            "es_pregunta": True,
            "decision": "ACLARACION_CASO",
            "motivo_decision": transicion.motivo,
            "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
            "estado": estado,
            "estado_operativo": estado.estado_operativo.value,
            "question_intent": QuestionIntent.ACLARACION_ALCANCE.value,
            "pregunta_final": pregunta_aclarar,
            "decision_transicion": transicion.decision.value,
            "motivo_transicion": transicion.motivo,
            "estado_previo": transicion.estado_previo.value,
            "estado_detectado_mensaje_actual": transicion.estado_detectado_mensaje.value,
            "dominio_previo": transicion.dominio_previo.value,
            "dominio_detectado_actual": transicion.dominio_detectado_mensaje.value,
            "dominio_actual": estado.dominio_probable,
            "version_orquestador": ORCHESTRATOR_VERSION,
        }
        return ret, transicion

    return None, transicion
