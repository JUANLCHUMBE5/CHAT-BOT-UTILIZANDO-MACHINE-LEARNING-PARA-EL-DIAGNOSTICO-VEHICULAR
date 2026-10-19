"""Etapa entrada segura; contexto por turno."""

from __future__ import annotations

import time
import uuid
from importlib import import_module as _importar

from src.config import settings
from src.core.conversacion.control_aclaraciones import aclaraciones_emitidas
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState, FactState, FactType, TurnTrace
from src.core.logger import logger
from src.core.version import ORCHESTRATOR_VERSION


async def entrada_segura(self, turno):
    turno.t0 = time.perf_counter()
    turno.texto_limpio = (turno.texto_usuario or "").strip()
    turno.estado = await self.repositorio.get_session(turno.session_id)
    if turno.estado is None:
        turno.sesion_mgr = getattr(turno.gestor_diagnostico, "session_manager", None)
        turno.sesion_existente = (
            turno.sesion_mgr.obtener_sesion(turno.session_id) if turno.sesion_mgr else None
        )
        if turno.sesion_existente and turno.sesion_existente.conversation_state:
            turno.estado = turno.sesion_existente.conversation_state
            if turno.sesion_existente.case_id and (not turno.estado.case_id):
                turno.estado.case_id = turno.sesion_existente.case_id
        else:
            turno.estado = ConversationState(session_id=turno.session_id)
    turno.contexto_previo = turno.estado.exportar_dict(incluir_trazabilidad=False)
    turno.BANNER_ACEITE = _importar("src.core.diagnostico.politica_seguridad").BANNER_ACEITE
    turno.BANNER_TEMPERATURA = _importar("src.core.diagnostico.politica_seguridad").BANNER_TEMPERATURA
    turno.PoliticaSeguridad = _importar("src.core.diagnostico.politica_seguridad").PoliticaSeguridad
    turno.SeveridadSeguridad = _importar("src.core.diagnostico.politica_seguridad").SeveridadSeguridad
    turno.sev_seguridad_early, turno.banner_seguridad_early = turno.PoliticaSeguridad.evaluar_severidad(
        turno.texto_limpio, str(turno.estado.falla_principal or ""), estado=turno.estado
    )
    if (
        turno.sev_seguridad_early == turno.SeveridadSeguridad.CRITICAL_STOP
        and turno.banner_seguridad_early
    ):
        if not turno.estado.case_id:
            turno.estado.case_id = str(uuid.uuid4())
            turno.estado.active_problem_id = str(uuid.uuid4())
        ExtractorHechos.extraer_y_actualizar(turno.estado, turno.texto_limpio)
        if turno.texto_limpio not in turno.estado.historial_mensajes_usuario:
            turno.estado.historial_mensajes_usuario.append(turno.texto_limpio)
        if turno.texto_limpio not in turno.estado.active_symptoms:
            turno.estado.active_symptoms.append(turno.texto_limpio)
        turno.estado.registrar_hecho(
            "alerta_seguridad_mecanica_activada",
            "SI",
            categoria="seguridad",
            texto_crudo=turno.texto_limpio,
            tipo=FactType.CONDICION,
        )
        logger.warning(
            f"[SeguridadMecanica] Intervención prioritaria activada en sesión {turno.session_id} Turno {turno.estado.turno_actual}"
        )
        turno.resp_seguridad = turno.banner_seguridad_early.strip()
        turno.traza = TurnTrace(
            turno=turno.estado.turno_actual,
            mensaje_original=turno.texto_limpio,
            contexto_previo=turno.contexto_previo,
            hechos_nuevos_extraidos=[],
            hechos_actualizados=[
                h.to_dict() for h in turno.estado.hechos.values() if h.estado == FactState.CONFIRMADO
            ],
            consulta_consolidada=turno.texto_limpio,
            top3=turno.estado.top3_actual,
            confianza=turno.estado.confianza_actual,
            origen_confianza="SEGURIDAD_CRITICA",
            decision="SEGURIDAD_CRITICA",
            motivo_decision="Intervención prioritaria por riesgo crítico de seguridad mecánica",
            respuesta_enviada=turno.resp_seguridad,
            estado_operativo=turno.estado.estado_operativo.value,
            question_intent=None,
            preguntas_candidatas=[],
            preguntas_descartadas=[],
            pregunta_final=None,
            hipotesis_rechazadas_usuario=list(turno.estado.hipotesis_descartadas),
            version_orquestador=ORCHESTRATOR_VERSION,
            tipo_mensaje="seguridad_critica",
        )
        turno.estado.trazabilidad.append(turno.traza.to_dict())
        if len(turno.estado.trazabilidad) > 15:
            turno.estado.trazabilidad = turno.estado.trazabilidad[-15:]
        await self.repositorio.save_session(turno.session_id, turno.estado)
        if (
            hasattr(turno.gestor_diagnostico, "session_manager")
            and turno.gestor_diagnostico.session_manager is not None
        ):
            turno.gestor_diagnostico.session_manager.cargar_contexto(
                turno.session_id,
                {"case_id": turno.estado.case_id, "conversation_state": turno.estado.exportar_dict()},
            )
        return {
            "status": "completado",
            "respuesta_texto": turno.resp_seguridad,
            "diagnostico_ml": turno.estado.falla_principal or "Advertencia de seguridad mecánica",
            "confianza_ml": 0.0,
            "top3_actual": turno.estado.top3_actual,
            "scores_presentacion": {},
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "SEGURIDAD_CRITICA",
            "motivo_decision": "Intervención prioritaria por riesgo crítico de seguridad mecánica",
            "pregunta_final": None,
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    turno.es_opcion_menu = turno.texto_limpio.isdecimal() and len(turno.texto_limpio) <= 2
    turno.es_menu = turno.texto_limpio.casefold() in {"menu", "menú"}
    turno.pregunta_sin_respuesta = bool(turno.estado.preguntas_realizadas) and len(
        turno.estado.respuestas_obtenidas
    ) < len(turno.estado.preguntas_realizadas)
    if (
        not turno.texto_limpio
        or not any((caracter.isalnum() for caracter in turno.texto_limpio))
        or turno.es_menu
        or (
            turno.es_opcion_menu
            and (not turno.estado.pending_question)
            and (not turno.estado.top3_actual)
            and (not turno.pregunta_sin_respuesta)
        )
    ):
        return {
            "status": "entrada_insuficiente",
            "respuesta_texto": "No recibí un síntoma que pueda evaluar. Describe qué falla presenta el vehículo.",
            "diagnostico_ml": "Entrada insuficiente",
            "confianza_ml": 0.0,
            "fase": turno.estado.fase.value,
            "es_pregunta": True,
            "decision": "PEDIR_TEXTO",
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if ExtractorHechos.es_consulta_memoria(turno.texto_limpio):
        turno.generar_resumen_memoria = _importar(
            "src.core.conversacion.resumen_memoria"
        ).generar_resumen_memoria
        return {
            "status": "consulta_memoria",
            "respuesta_texto": turno.generar_resumen_memoria(turno.estado),
            "diagnostico_ml": turno.estado.falla_principal or "Consulta de memoria",
            "confianza_ml": turno.estado.confianza_actual,
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "CONSULTA_MEMORIA",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    turno.estado.max_repreguntas = settings.diagnostic.max_clarifications
    if not turno.estado.case_id:
        turno.sesion_mgr = getattr(turno.gestor_diagnostico, "session_manager", None)
        turno.sesion_existente = (
            turno.sesion_mgr.obtener_sesion(turno.session_id) if turno.sesion_mgr else None
        )
        if turno.sesion_existente and turno.sesion_existente.case_id:
            turno.estado.case_id = turno.sesion_existente.case_id
        else:
            turno.estado.case_id = str(uuid.uuid4())
        if not turno.estado.active_problem_id:
            turno.estado.active_problem_id = str(uuid.uuid4())
    if (
        hasattr(turno.gestor_diagnostico, "session_manager")
        and turno.gestor_diagnostico.session_manager is not None
    ):
        turno.gestor_diagnostico.session_manager.cargar_contexto(
            turno.session_id,
            {"case_id": turno.estado.case_id, "conversation_state": turno.estado.exportar_dict()},
        )
    turno.contexto_previo = turno.estado.exportar_dict(incluir_trazabilidad=False)
    turno.aclaraciones_previas = aclaraciones_emitidas(turno.estado)
