"""Orquestador principal de la memoria conversacional acumulativa y auto-interrogador inteligente."""

from __future__ import annotations

import re
import time
import uuid
from typing import Any, Dict, Optional

from src.config import settings
from src.core.conversacion.clasificador_mensajes import clasificar_mensaje
from src.core.conversacion.control_aclaraciones import (
    aclaraciones_emitidas,
    dato_desconocido,
    debe_avanzar,
    desconocidos_consecutivos,
    hay_evidencia_diagnostica,
)
from src.core.conversacion.extraccion_hechos.patrones_hechos import PATRON_CORRECCION_VEHICULO
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas
from src.core.conversacion.maquina_estados import MaquinaEstadosConversacion
from src.core.conversacion.models import (
    ConversationPhase,
    ConversationState,
    DtcStatus,
    FactState,
    FactType,
    QuestionIntent,
    TurnTrace,
)
from src.core.conversacion.repositorio import (
    ConversationStateRepository,
    PostgresConversationRepository,
)
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta
from src.core.conversacion.suficiencia_informacion import EvaluadorSuficiencia
from src.core.logger import logger
from src.core.version import ORCHESTRATOR_VERSION


class OrquestadorConversacion:
    """Coordina el ciclo de vida de la conversación, extracción acumulativa y diagnóstico."""

    def __init__(self, repositorio: Optional[ConversationStateRepository] = None):
        self.repositorio = repositorio or PostgresConversationRepository()

    async def finalizar_caso(self, session_id: str, gestor_diagnostico: Optional[Any] = None) -> None:
        """Finaliza formalmente el case_id en el repositorio y en el SessionManager."""
        nuevo_id = None
        session_manager = getattr(gestor_diagnostico, "session_manager", None)
        if session_manager is not None:
            nuevo_id = session_manager.finalizar_caso(session_id)
        await self.repositorio.finalizar_caso(session_id, nuevo_id)

    async def procesar_turno(
        self,
        session_id: str,
        texto_usuario: str,
        gestor_diagnostico: Any,
        placa: Optional[str] = None,
        marca_modelo: Optional[str] = None,
        proveedor: str = "meta",
        diagnostico_forzado: Optional[str] = None,
        diferir_encolado_persistente: bool = False,
        taller_id: Optional[str] = None,
        usuario_id: Optional[str] = None,
        conversacion_id: Optional[str] = None,
        remitente: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Procesa un turno conversacional de WhatsApp con memoria y auto-interrogador inteligente."""
        t0 = time.perf_counter()
        texto_limpio = (texto_usuario or "").strip()

        # 1. Recuperar o inicializar estado de sesión
        estado = await self.repositorio.get_session(session_id)
        if estado is None:
            sesion_mgr = getattr(gestor_diagnostico, "session_manager", None)
            sesion_existente = sesion_mgr.obtener_sesion(session_id) if sesion_mgr else None
            if sesion_existente and sesion_existente.conversation_state:
                estado = sesion_existente.conversation_state
                if sesion_existente.case_id and not estado.case_id:
                    estado.case_id = sesion_existente.case_id
            else:
                estado = ConversationState(session_id=session_id)

        es_opcion_menu = texto_limpio.isdecimal() and len(texto_limpio) <= 2
        es_menu = texto_limpio.casefold() in {"menu", "menú"}
        pregunta_sin_respuesta = (
            bool(estado.preguntas_realizadas)
            and len(estado.respuestas_obtenidas) < len(estado.preguntas_realizadas)
        )
        if (
            not texto_limpio
            or not any(caracter.isalnum() for caracter in texto_limpio)
            or es_menu
            or (
                es_opcion_menu
                and not estado.pending_question
                and not estado.top3_actual
                and not pregunta_sin_respuesta
            )
        ):
            return {
                "status": "entrada_insuficiente",
                "respuesta_texto": (
                    "No recibí un síntoma que pueda evaluar. Describe qué falla presenta el vehículo."
                ),
                "diagnostico_ml": "Entrada insuficiente",
                "confianza_ml": 0.0,
                "fase": estado.fase.value,
                "es_pregunta": True,
                "decision": "PEDIR_TEXTO",
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
            }

        if ExtractorHechos.es_consulta_memoria(texto_limpio):
            from src.core.conversacion.resumen_memoria import generar_resumen_memoria

            return {
                "status": "consulta_memoria",
                "respuesta_texto": generar_resumen_memoria(estado),
                "diagnostico_ml": estado.falla_principal or "Consulta de memoria",
                "confianza_ml": estado.confianza_actual,
                "fase": estado.fase.value,
                "es_pregunta": False,
                "decision": "CONSULTA_MEMORIA",
                "case_id": estado.case_id,
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
            }

        estado.max_repreguntas = settings.diagnostic.max_clarifications

        if not estado.case_id:
            sesion_mgr = getattr(gestor_diagnostico, "session_manager", None)
            sesion_existente = sesion_mgr.obtener_sesion(session_id) if sesion_mgr else None
            if sesion_existente and sesion_existente.case_id:
                estado.case_id = sesion_existente.case_id
            else:
                estado.case_id = str(uuid.uuid4())
            if not estado.active_problem_id:
                estado.active_problem_id = str(uuid.uuid4())

        # La sesión conversacional persistida es la fuente de verdad. No reemplazar
        # su caso por un case_id potencialmente obsoleto del caché en memoria.
        if hasattr(gestor_diagnostico, "session_manager") and gestor_diagnostico.session_manager is not None:
            gestor_diagnostico.session_manager.cargar_contexto(
                session_id,
                {"case_id": estado.case_id, "conversation_state": estado.exportar_dict()},
            )

        contexto_previo = estado.exportar_dict(incluir_trazabilidad=False)
        aclaraciones_previas = aclaraciones_emitidas(estado)

        solicitud_caso = ExtractorHechos.clasificar_solicitud_caso(texto_limpio)
        if solicitud_caso and solicitud_caso.get("accion") == "reanudar":
            case_id_objetivo = solicitud_caso.get("case_id")
            if not case_id_objetivo and solicitud_caso.get("caso_anterior"):
                case_id_objetivo = next(
                    (
                        caso.get("case_id")
                        for caso in reversed(estado.hechos_historicos)
                        if caso.get("case_id") and caso.get("case_id") != estado.case_id
                    ),
                    None,
                )
            if case_id_objetivo and estado.restaurar_caso_archivado(str(case_id_objetivo)):
                await self.repositorio.save_session(session_id, estado)
                session_manager = getattr(gestor_diagnostico, "session_manager", None)
                if session_manager is not None:
                    session_manager.cargar_contexto(
                        session_id,
                        {"case_id": estado.case_id, "conversation_state": estado.exportar_dict()},
                    )
                return {
                    "status": "caso_reanudado",
                    "respuesta_texto": (
                        "Retomé exclusivamente el caso anterior solicitado. Su contexto queda aislado "
                        "del caso que acabamos de cerrar."
                    ),
                    "diagnostico_ml": "Caso anterior reanudado",
                    "confianza_ml": estado.confianza_actual,
                    "fase": estado.fase.value,
                    "es_pregunta": False,
                    "decision": "REANUDAR_CASO",
                    "case_id": estado.case_id,
                    "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                    "estado": estado,
                }
            return {
                "status": "reanudar_no_encontrado",
                "respuesta_texto": (
                    "No encontré ese caso en el historial de esta conversación. Indica el case_id "
                    "o solicita retomar el caso anterior disponible. No cambié el caso activo."
                ),
                "diagnostico_ml": "Caso histórico no encontrado",
                "confianza_ml": 0.0,
                "fase": estado.fase.value,
                "es_pregunta": True,
                "decision": "ACLARAR_REANUDACION",
                "case_id": estado.case_id,
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
            }

        if (
            solicitud_caso
            and solicitud_caso.get("accion") in ("nuevo_caso", "cancelar")
            and not ExtractorHechos.contiene_informacion_diagnostica(texto_limpio)
        ):
            es_cancelacion = solicitud_caso["accion"] == "cancelar"
            preservar_vehiculo = bool(
                solicitud_caso.get("preservar_vehiculo")
                and any((estado.placa, estado.marca, estado.modelo))
            )
            estado.iniciar_nuevo_caso(
                None if es_cancelacion else str(uuid.uuid4()),
                preservar_vehiculo=preservar_vehiculo,
            )
            if es_cancelacion:
                estado.case_id = None
                estado.active_problem_id = None
            await self.repositorio.save_session(session_id, estado)
            session_manager = getattr(gestor_diagnostico, "session_manager", None)
            if session_manager is not None:
                session_manager.cargar_contexto(
                    session_id,
                    {"case_id": estado.case_id, "conversation_state": estado.exportar_dict()},
                )
            if es_cancelacion:
                resp_reinicio = (
                    "🚗 *Caso cancelado.* Conservé su historial y limpié el contexto activo. "
                    "Cuando quieras, envía la placa del siguiente vehículo."
                )
            else:
                resp_reinicio = (
                    "🚗 *Caso anterior cerrado.* Conservé su historial y limpié la memoria activa. "
                    "Envía la placa y el síntoma para iniciar un caso nuevo."
                )
                if preservar_vehiculo and estado.placa:
                    resp_reinicio = (
                        "🚗 *Caso anterior cerrado.* Conservé el historial y mantengo únicamente "
                        "los datos confirmados del mismo vehículo. Indica el nuevo síntoma."
                    )
            return {
                "status": "reinicio",
                "respuesta_texto": resp_reinicio,
                "diagnostico_ml": "Reinicio de sesión",
                "confianza_ml": 0.0,
                "fase": ConversationPhase.INICIO.value,
                "es_pregunta": False,
                "decision": "REINICIO",
                "case_id": estado.case_id,
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
            }

        # 2.0 Detección de agradecimiento / cierre ("muchas gracias", "gracias maestro", "quedó clarísimo")
        PATRON_CIERRE = re.compile(
            r"^\s*(?:(?:muchas\s+)?gracias(?:\s+maestro|\s+amigo)?(?:\s+por\s+.*)?|"
            r"perfecto,?\s*(?:qued[oó]\s+clar[ií]simo|gracias.*)?|"
            r"excelente\s+(?:servicio|explicaci[oó]n|ayuda)(?:\s+maestro)?|"
            r"qued[oó]\s+clar[ií]simo)\s*[!.]*\s*$",
            re.IGNORECASE,
        )
        if PATRON_CIERRE.match(texto_limpio.strip()):
            if any(w in texto_limpio.lower() for w in ("embalamiento", "seguridad", "riesgo", "peligro", "diesel", "diésel", "cárter", "carter")):
                resp_cierre = (
                    "🤝 *¡De nada maestro! Recuerda mantener el motor detenido y drenar completamente el cárter contaminado "
                    "antes de cualquier intento de arranque para evitar el peligro crítico de embalamiento diésel. "
                    "Quedo a tu disposición en el taller para cualquier otra consulta técnica o nuevo caso vehicular. ¡Muchos éxitos!*"
                )
            else:
                resp_cierre = (
                    "🤝 *¡De nada maestro! Quedo a tu disposición en el taller para cualquier otra consulta técnica, "
                    "medición o nuevo caso vehicular. ¡Muchos éxitos en la reparación!*"
                )
            return {
                "status": "cierre",
                "respuesta_texto": resp_cierre,
                "diagnostico_ml": estado.falla_principal or "Caso concluido",
                "confianza_ml": estado.confianza_actual or 1.0,
                "fase": estado.fase.value,
                "es_pregunta": False,
                "decision": "CIERRE",
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
            }

        # 2.0b Intervención prioritaria de seguridad mecánica (Common Rail, DPF y maniobras de alto riesgo)
        from src.core.diagnostico.politica_seguridad import (
            BANNER_BLOQUEO_REGENERACION_DILUCION,
            BANNER_DIESEL_ALTA_PRESION,
            BANNER_RADIADOR_CALIENTE,
            PoliticaSeguridad,
            SeveridadSeguridad,
        )
        sev_seguridad_early, banner_seguridad_early = PoliticaSeguridad.evaluar_severidad(
            texto_limpio,
            str(estado.falla_principal or ""),
            estado=estado,
        )
        if (
            sev_seguridad_early == SeveridadSeguridad.CRITICAL_STOP
            and banner_seguridad_early in (
                BANNER_DIESEL_ALTA_PRESION,
                BANNER_BLOQUEO_REGENERACION_DILUCION,
                BANNER_RADIADOR_CALIENTE,
            )
        ):
            if texto_limpio not in estado.historial_mensajes_usuario:
                estado.historial_mensajes_usuario.append(texto_limpio)
            estado.registrar_hecho(
                "alerta_seguridad_mecanica_activada",
                "SI",
                categoria="seguridad",
                texto_crudo=texto_limpio,
                tipo=FactType.CONDICION,
            )
            logger.warning(
                f"[SeguridadMecanica] Intervención prioritaria activada en sesión {session_id} Turno {estado.turno_actual}"
            )
            resp_seguridad = banner_seguridad_early.strip()
            traza = TurnTrace(
                turno=estado.turno_actual,
                mensaje_original=texto_limpio,
                contexto_previo=contexto_previo,
                hechos_nuevos_extraidos=[],
                hechos_actualizados=[h.to_dict() for h in estado.hechos.values() if h.estado == FactState.CONFIRMADO],
                consulta_consolidada=texto_limpio,
                top3=estado.top3_actual,
                confianza=estado.confianza_actual,
                origen_confianza="SEGURIDAD_CRITICA",
                decision="SEGURIDAD_CRITICA",
                motivo_decision="Intervención prioritaria por riesgo crítico de seguridad mecánica",
                respuesta_enviada=resp_seguridad,
                estado_operativo=estado.estado_operativo.value,
                question_intent=None,
                preguntas_candidatas=[],
                preguntas_descartadas=[],
                pregunta_final=None,
                hipotesis_rechazadas_usuario=list(estado.hipotesis_descartadas),
                version_orquestador=ORCHESTRATOR_VERSION,
                tipo_mensaje="seguridad_critica",
            )
            estado.trazabilidad.append(traza.to_dict())
            if len(estado.trazabilidad) > 15:
                estado.trazabilidad = estado.trazabilidad[-15:]

            await self.repositorio.save_session(session_id, estado)
            if hasattr(gestor_diagnostico, "session_manager") and gestor_diagnostico.session_manager is not None:
                gestor_diagnostico.session_manager.cargar_contexto(
                    session_id,
                    {"case_id": estado.case_id, "conversation_state": estado.exportar_dict()},
                )

            return {
                "status": "seguridad_critica",
                "respuesta_texto": resp_seguridad,
                "diagnostico_ml": estado.falla_principal or "Advertencia de seguridad mecánica",
                "confianza_ml": estado.confianza_actual or 1.0,
                "top3_actual": estado.top3_actual,
                "scores_presentacion": {},
                "fase": estado.fase.value,
                "es_pregunta": False,
                "decision": "SEGURIDAD_CRITICA",
                "motivo_decision": "Intervención prioritaria por riesgo crítico de seguridad mecánica",
                "pregunta_final": None,
                "case_id": estado.case_id,
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
            }

        # 2.0c Consulta de prerrequisitos de regeneración DPF (aceite verificado / sin dilución activa)
        norm_txt_cons = texto_limpio.casefold()
        es_consulta_prerrequisitos_dpf = bool(
            re.search(
                r"\b(?:qu[eé]\s+(?:debo|se\s+debe|hay\s+que|tengo\s+que)\s+(?:verificar|revisar|comprobar|chequear)|"
                r"prerrequisitos?|condiciones\s+previas|requisitos?)\b.{0,50}\b(?:antes\s+de\s+regenerar|regeneraci[oó]n|regenerar)\b|"
                r"\b(?:antes\s+de\s+regenerar|para\s+regenerar)\b.{0,40}\b(?:qu[eé]\s+(?:verifico|reviso|compruebo|chequeo)|prerrequisitos?)\b",
                norm_txt_cons,
            )
            or (
                re.search(r"\b(?:ya\s+correg[ií]|ya\s+cambi[eé]|dren[eé]|bot[eé]|aceite\s+nuevo)\b", norm_txt_cons)
                and re.search(r"\b(?:regenerar|regeneraci[oó]n)\b", norm_txt_cons)
            )
        )
        if es_consulta_prerrequisitos_dpf and not PoliticaSeguridad._hay_dilucion_aceite_activa(texto_limpio, estado):
            if texto_limpio not in estado.historial_mensajes_usuario:
                estado.historial_mensajes_usuario.append(texto_limpio)
            estado.registrar_hecho(
                "prerrequisitos_dpf_consultados",
                "SI",
                categoria="seguridad",
                texto_crudo=texto_limpio,
                tipo=FactType.CONDICION,
            )
            resp_prerreq = PoliticaSeguridad.PRERREQUISITOS_REGENERACION_DPF_OEM
            traza = TurnTrace(
                turno=estado.turno_actual,
                mensaje_original=texto_limpio,
                contexto_previo=contexto_previo,
                hechos_nuevos_extraidos=[],
                hechos_actualizados=[h.to_dict() for h in estado.hechos.values() if h.estado == FactState.CONFIRMADO],
                consulta_consolidada=texto_limpio,
                top3=estado.top3_actual,
                confianza=estado.confianza_actual,
                origen_confianza="PRERREQUISITOS_OEM",
                decision="PRERREQUISITOS_OEM",
                motivo_decision="Consulta técnica de prerrequisitos OEM para regeneración de DPF",
                respuesta_enviada=resp_prerreq,
                estado_operativo=estado.estado_operativo.value,
                question_intent=None,
                preguntas_candidatas=[],
                preguntas_descartadas=[],
                pregunta_final=None,
                hipotesis_rechazadas_usuario=list(estado.hipotesis_descartadas),
                version_orquestador=ORCHESTRATOR_VERSION,
                tipo_mensaje="prerrequisitos_dpf",
            )
            estado.trazabilidad.append(traza.to_dict())
            if len(estado.trazabilidad) > 15:
                estado.trazabilidad = estado.trazabilidad[-15:]

            await self.repositorio.save_session(session_id, estado)
            if hasattr(gestor_diagnostico, "session_manager") and gestor_diagnostico.session_manager is not None:
                gestor_diagnostico.session_manager.cargar_contexto(
                    session_id,
                    {"case_id": estado.case_id, "conversation_state": estado.exportar_dict()},
                )

            return {
                "status": "prerrequisitos_dpf",
                "respuesta_texto": resp_prerreq,
                "diagnostico_ml": estado.falla_principal or "Prerrequisitos OEM DPF",
                "confianza_ml": estado.confianza_actual or 1.0,
                "top3_actual": estado.top3_actual,
                "scores_presentacion": {},
                "fase": estado.fase.value,
                "es_pregunta": False,
                "decision": "PRERREQUISITOS_OEM",
                "motivo_decision": "Consulta técnica de prerrequisitos OEM para regeneración de DPF",
                "pregunta_final": None,
                "case_id": estado.case_id,
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
            }

        # 2.0d Detección prioritaria de síntomas fuera de catálogo (OOD) y abstención segura
        from src.core.diagnostico.detector_ood import detectar_sintoma_fuera_de_catalogo
        es_ood, regla_ood = detectar_sintoma_fuera_de_catalogo(texto_limpio)
        if es_ood and regla_ood is not None:
            if texto_limpio not in estado.historial_mensajes_usuario:
                estado.historial_mensajes_usuario.append(texto_limpio)
            estado.registrar_hecho(
                f"alerta_ood_{regla_ood.categoria.lower()}",
                "SI",
                categoria="seguridad",
                texto_crudo=texto_limpio,
                tipo=FactType.CONDICION,
            )
            logger.info(
                f"[DetectorOOD] Abstención segura activada en conversación {session_id} Turno {estado.turno_actual}: {regla_ood.categoria}"
            )
            resp_ood = regla_ood.mensaje_abstencion.strip()
            traza = TurnTrace(
                turno=estado.turno_actual,
                mensaje_original=texto_limpio,
                contexto_previo=contexto_previo,
                hechos_nuevos_extraidos=[],
                hechos_actualizados=[h.to_dict() for h in estado.hechos.values() if h.estado == FactState.CONFIRMADO],
                consulta_consolidada=texto_limpio,
                top3=[],
                confianza=0.0,
                origen_confianza="ABSTENCION_OOD",
                decision="ABSTENCION_OOD",
                motivo_decision=f"Síntoma fuera de catálogo: {regla_ood.categoria}",
                respuesta_enviada=resp_ood,
                estado_operativo=estado.estado_operativo.value,
                question_intent=None,
                preguntas_candidatas=[],
                preguntas_descartadas=[],
                pregunta_final=None,
                hipotesis_rechazadas_usuario=list(estado.hipotesis_descartadas),
                version_orquestador=ORCHESTRATOR_VERSION,
                tipo_mensaje="abstencion_ood",
            )
            estado.trazabilidad.append(traza.to_dict())
            if len(estado.trazabilidad) > 15:
                estado.trazabilidad = estado.trazabilidad[-15:]

            await self.repositorio.save_session(session_id, estado)
            if hasattr(gestor_diagnostico, "session_manager") and gestor_diagnostico.session_manager is not None:
                gestor_diagnostico.session_manager.cargar_contexto(
                    session_id,
                    {"case_id": estado.case_id, "conversation_state": estado.exportar_dict()},
                )

            return {
                "status": "abstencion_ood",
                "respuesta_texto": resp_ood,
                "diagnostico_ml": f"Fuera de Catálogo: {regla_ood.sistema_objetivo}",
                "confianza_ml": 0.0,
                "top3_actual": [],
                "scores_presentacion": {},
                "fase": estado.fase.value,
                "es_pregunta": False,
                "decision": "ABSTENCION_OOD",
                "motivo_decision": f"Síntoma fuera de catálogo: {regla_ood.categoria}",
                "pregunta_final": None,
                "case_id": estado.case_id,
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
            }

        # 2.1 Detección de saludo ("hola", "buenas", "buenos días")
        if ExtractorHechos.es_saludo(texto_limpio):
            tiene_caso_activo = bool(
                estado.placa
                or estado.hechos
                or estado.active_symptoms
                or estado.completed_tests
                or (estado.fase != ConversationPhase.INICIO and estado.fase != ConversationPhase.RESULTADO)
            )
            if not tiene_caso_activo:
                if estado.fase == ConversationPhase.RESULTADO or not estado.hechos:
                    estado.iniciar_nuevo_caso()
                await self.repositorio.save_session(session_id, estado)
                resp_saludo = (
                    "👋 *¡Hola! Soy CarBot, chatbot de diagnóstico vehicular con Inteligencia Artificial.*\n\n"
                    "¿En qué te puedo ayudar hoy o qué falla presenta el auto? Para empezar, cuéntame el problema o síntomas que notas."
                )
                return {
                    "status": "saludo", "respuesta_texto": resp_saludo, "diagnostico_ml": "Saludo / Bienvenida",
                    "confianza_ml": 0.0, "fase": ConversationPhase.INICIO.value, "es_pregunta": False, "decision": "SALUDO",
                    "case_id": estado.case_id,
                    "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2), "estado": estado,
                }
            else:
                # Caso activo: preservar memoria de sesión y placa intactas
                placa_txt = f" del vehículo con placa *{estado.placa}*" if estado.placa else ""
                resp_saludo = (
                    f"👋 *¡Hola! Continuamos con el diagnóstico activo{placa_txt}.*\n\n"
                    "Cuéntame si tienes más síntomas que agregar o responde a la última indicación para continuar."
                )
                return {
                    "status": "saludo_caso_activo", "respuesta_texto": resp_saludo,
                    "diagnostico_ml": "Saludo en caso activo",
                    "confianza_ml": estado.confianza_actual or 1.0, "fase": estado.fase.value,
                    "es_pregunta": False, "decision": "SALUDO",
                    "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2), "estado": estado,
                }

        # 2.2a Consultas de estado del caso y descartes ("qué hemos descartado", "qué sabemos hasta ahora", "resumen")
        norm_txt_cons = texto_limpio.casefold()
        if re.search(r"\bqu[eé]\s+(?:hemos|se\s+ha|tenemos)\s+descartado\b|\bdescartes?\s+hasta\s+ahora\b", norm_txt_cons):
            desc_items = []
            for d in getattr(estado, "hipotesis_descartadas", []):
                d_limpio = d.replace("componente:", "").replace("_", " ").capitalize()
                desc_items.append(f"• {d_limpio}")
            for h in getattr(estado, "hechos", {}).values():
                if getattr(h, "categoria", "") in ("componente_reemplazado", "verificacion_fisica", "rechazo_hipotesis_usuario"):
                    nombre = getattr(h, "campo", "").replace("rechazo_usuario_", "").replace("componente_comprobado_", "").replace("componente_reemplazado_", "").capitalize()
                    val = getattr(h, "valor", "")
                    item_str = f"• {nombre}: {val}"
                    if item_str not in desc_items:
                        desc_items.append(item_str)
            if desc_items:
                resp_descartes = "📋 *Comprobaciones y descartes registrados hasta el momento:*\n\n" + "\n".join(dict.fromkeys(desc_items))
            else:
                resp_descartes = "📋 *Descartes registrados:* Hasta el momento no se han registrado componentes descartados en este caso."
            return {
                "status": "resumen_descartes", "respuesta_texto": resp_descartes,
                "diagnostico_ml": estado.falla_principal or "Descartes del caso",
                "confianza_ml": estado.confianza_actual or 1.0, "fase": estado.fase.value,
                "es_pregunta": False, "decision": "RESUMEN_DESCARTES",
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2), "estado": estado,
            }

        if re.search(r"\bqu[eé]\s+(?:sabemos|tenemos)\s+hasta\s+ahora\b|\b(?:dame\s+(?:el\s+)?)?resumen\b", norm_txt_cons):
            veh_info = f"{estado.marca or 'Vehículo'} {estado.modelo or ''} {estado.anio or ''}".strip()
            comb_info = f" ({estado.combustible})" if estado.combustible else ""
            placa_info = f" - Placa: {estado.placa}" if estado.placa else ""
            sintomas_list = [f"• {s}" for s in (estado.active_symptoms or [])]
            sint_txt = "\n".join(sintomas_list) if sintomas_list else "• Síntomas en evaluación preliminar"
            hip_txt = estado.falla_principal or "Diagnóstico diferencial en curso"
            resp_resumen = (
                f"📋 *Resumen técnico del caso activo:*\n\n"
                f"🚗 *Vehículo:* {veh_info}{comb_info}{placa_info}\n"
                f"⚠️ *Síntomas observados:*\n{sint_txt}\n\n"
                f"🎯 *Hipótesis de trabajo:* *{hip_txt}*\n"
                f"¿Deseas aportar una nueva medición o proceder con las pruebas sugeridas?"
            )
            return {
                "status": "resumen_caso", "respuesta_texto": resp_resumen,
                "diagnostico_ml": estado.falla_principal or "Resumen del caso",
                "confianza_ml": estado.confianza_actual or 1.0, "fase": estado.fase.value,
                "es_pregunta": True, "decision": "RESUMEN_CASO",
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2), "estado": estado,
            }

        # 2.2b Explicaciones causales ("por qué ocurre", "por qué recalienta en tráfico")
        if re.search(r"\bpor\s+qu[eé]\b.{0,30}\b(?:ocurre|pasa|recalienta|falla|se\s+apaga|demora|vibra|corta|zapatea|se\s+congela|congela|inyector|gas|mezcla)\b", norm_txt_cons):
            resp_por_que = None
            if "recalienta" in norm_txt_cons and any(w in norm_txt_cons for w in ("trafico", "tráfico", "detenido", "parado")):
                resp_por_que = (
                    "💡 *Explicación técnica del comportamiento térmico:*\n\n"
                    "En carretera a velocidad sostenida, el flujo de aire natural que ingresa por la parrilla "
                    "(convección dinámica) enfría el radiador de manera continua. Sin embargo, en tráfico detenido "
                    "o ralentí, no existe flujo de aire exterior; el enfriamiento depende al 100% de la activación forzada "
                    "del electroventilador y la circulación efectiva del refrigerante por el termostato y la bomba de agua. "
                    "Si el electroventilador no enciende en su velocidad adecuada o el termostato no abre por completo, "
                    "la temperatura ascenderá rápidamente hacia la zona crítica."
                )
            elif any(w in norm_txt_cons for w in ("corta", "segundos", "inyeccion", "inyección", "inmovilizador", "ecu")):
                resp_por_que = (
                    "💡 *Explicación técnica de la estrategia de inmovilizador:*\n\n"
                    "Al dar arranque, la ECU permite una activación inicial de 2 a 3 segundos mientras interroga "
                    "al transponder de la llave mediante la antena receptora. Si el código de seguridad no es reconocido "
                    "(o arroja DTC de transponder como B10DA), la ECU corta de inmediato los pulsos de inyección y bomba "
                    "de combustible como medida de seguridad antirrobo, apagando el motor."
                )
            elif any(w in norm_txt_cons for w in ("congela", "reductor", "gas", "gnv", "glp")):
                resp_por_que = (
                    "💡 *Explicación técnica de la congelación del reductor:*\n\n"
                    "La caída drástica de presión del GNV (desde 200 bar a baja presión) provoca un enfriamiento extremo "
                    "por efecto Joule-Thomson. El reductor requiere circulación continua de refrigerante caliente del motor "
                    "para compensar esta pérdida térmica. Si las mangueras de agua tienen aire, están obstruidas o el motor "
                    "aún no alcanza temperatura, el reductor se congela y escarcha, provocando tirones severos."
                )
            elif any(w in norm_txt_cons for w in ("zapatea", "trepida", "embrague")):
                resp_por_que = (
                    "💡 *Explicación técnica de la trepidación al acoplar el embrague:*\n\n"
                    "El zapateo o trepidación al arrancar en primera ocurre por falta de contacto plano homogéneo "
                    "entre el disco, el plato opresor y el volante. Esto es provocado comúnmente por alabeo o puntos "
                    "térmicos en el volante de inercia, resortes amortiguadores del disco fatigados o contaminación por aceite."
                )
            elif any(w in norm_txt_cons for w in ("cascabeleo", "inyector", "subida", "pobre")):
                resp_por_que = (
                    "💡 *Explicación técnica de detonación por inyector deficiente:*\n\n"
                    "Bajo carga (subida empinada acelerando a fondo), el motor requiere mayor volumen de combustible para "
                    "disipar calor y mantener la combustión controlada. Un inyector sucio o con bajo caudal empobrece la mezcla, "
                    "elevando bruscamente la temperatura de cámara y provocando autoignición espontánea (cascabeleo o pistoneo)."
                )

            if resp_por_que:
                return {
                    "status": "explicacion_causal", "respuesta_texto": resp_por_que,
                    "diagnostico_ml": estado.falla_principal or "Explicación técnica",
                    "confianza_ml": estado.confianza_actual or 1.0, "fase": estado.fase.value,
                    "es_pregunta": False, "decision": "EXPLICACION_CAUSAL",
                    "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2), "estado": estado,
                }

        # 2.2b2 Consultas de tolerancias y especificaciones OEM ("tolerancia", "especificación", "alabeo máximo", "temperatura debe abrir")
        if re.search(r"\b(?:tolerancia|alabeo\s+m[aá]ximo|especificaci[oó]n|temperatura\s+(?:debe\s+abrir|de\s+apertura))\b", norm_txt_cons):
            resp_tol = None
            if any(w in norm_txt_cons for w in ("termostato", "abrir", "temperatura")):
                resp_tol = (
                    "🔬 *Especificación metrológica y tolerancia OEM (Termostato):*\n\n"
                    "Según el manual de servicio del fabricante, la temperatura de inicio de apertura del termostato "
                    "se sitúa entre 82 °C y 88 °C, alcanzando su carrera de apertura total a los 95 °C - 98 °C "
                    "(elevación mínima de la válvula de 8 mm). Si a 108 °C la manguera inferior permanece fría, "
                    "el termostato está trabado cerrado."
                )
            elif any(w in norm_txt_cons for w in ("volante", "inercia", "embrague")):
                resp_tol = (
                    "🔬 *Especificación metrológica y tolerancia OEM (Volante de inercia):*\n\n"
                    "El alabeo o salto axial máximo admisible para el volante de inercia según manual es de 0.10 mm. "
                    "Cualquier lectura superior a 0.10 mm o presencia de fisuras y sobrecalentamiento térmico azulado "
                    "exige rectificado de la pista de fricción o reemplazo del volante."
                )
            elif any(w in norm_txt_cons for w in ("disco", "freno", "alabeo")):
                resp_tol = (
                    "🔬 *Especificación metrológica y tolerancia OEM (Discos de freno):*\n\n"
                    "La tolerancia máxima de alabeo lateral en discos de freno instalados es de 0.05 mm a 0.07 mm. "
                    "Una medición de 0.12 mm excede significativamente el límite de servicio y provocará pulsación "
                    "en el pedal y vibración en el timón a alta velocidad; requiere rectificado o cambio de discos."
                )
            if resp_tol:
                return {
                    "status": "tolerancia_oem", "respuesta_texto": resp_tol,
                    "diagnostico_ml": estado.falla_principal or "Tolerancia OEM",
                    "confianza_ml": estado.confianza_actual or 1.0, "fase": estado.fase.value,
                    "es_pregunta": False, "decision": "TOLERANCIA_OEM",
                    "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2), "estado": estado,
                }

        # 2.2c Solicitud de profundización técnica ("más detalles", "cómo lo reviso", "paso a paso")
        if ExtractorHechos.es_solicitud_detalle(texto_limpio) and (estado.top3_actual or getattr(estado, "falla_principal", None)):
            from src.core.conversacion.formateador_compacto import FormateadorCompacto

            top_actual = estado.top3_actual or []
            falla_target = top_actual[0]["falla"] if top_actual else (estado.falla_principal or "Falla mecánica bajo revisión")

            # Mapeo a componente específico si fue explícitamente consultado
            componentes_consulta = (
                ("electroventilador", "Falla en el electroventilador"),
                ("motoventilador", "Falla en el electroventilador"),
                ("ventilador", "Falla en el electroventilador"),
                ("termostato", "Falla en el termostato"),
                ("radiador", "Falla en el radiador"),
                ("bomba de agua", "Falla en la bomba de agua"),
                ("inyector", "Falla en inyectores de combustible"),
                ("bobina", "Falla en bobina de encendido"),
                ("bujia", "Falla en bujías"),
                ("bomba de combustible", "Falla en bomba de combustible"),
                ("bomba de gasolina", "Falla en bomba de combustible"),
                ("regulador", "Falla en regulador de presion de combustible o diafragma roto"),
                ("sensor ect", "Falla en sensor ECT de temperatura"),
                ("sensor de temperatura", "Falla en sensor ECT de temperatura"),
                ("embrague", "Desgaste del embrague"),
                ("frenos", "Desgaste en pastillas o discos de freno"),
            )
            for patron_c, falla_c in componentes_consulta:
                if patron_c in norm_txt_cons:
                    falla_target = falla_c
                    break

            if any(w in texto_limpio for w in (" 2", "segunda", "opcion 2", "opción 2")):
                if len(top_actual) > 1:
                    falla_target = top_actual[1]["falla"]
            elif any(w in texto_limpio for w in (" 3", "tercera", "opcion 3", "opción 3")):
                if len(top_actual) > 2:
                    falla_target = top_actual[2]["falla"]

            contexto_rag_detalle = ""
            if hasattr(gestor_diagnostico.motor_rag, "recuperar_contexto"):
                res_rag = gestor_diagnostico.motor_rag.recuperar_contexto(falla_target)
                if isinstance(res_rag, tuple):
                    contexto_rag_detalle = res_rag[0] or ""
                elif isinstance(res_rag, str):
                    contexto_rag_detalle = res_rag

            resp_detalle = FormateadorCompacto.formatear_detalle_tecnico(
                falla=falla_target,
                procedimiento_rag=contexto_rag_detalle,
                estado=estado,
            )
            return {
                "status": "detalle",
                "respuesta_texto": resp_detalle,
                "diagnostico_ml": falla_target,
                "confianza_ml": estado.confianza_actual,
                "fase": estado.fase.value,
                "es_pregunta": False,
                "decision": "DETALLE",
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
            }

        # 2.3 Segmentación automática de casos y aislamiento de contexto (Fase 9.10)
        from src.core.conversacion.segmentador_casos import SegmentadorCasos

        tipo_mensaje = clasificar_mensaje(texto_limpio, estado)
        ret_trans, transicion = SegmentadorCasos.resolver_transicion_turno(
            estado=estado,
            texto_limpio=texto_limpio,
            gestor_diagnostico=gestor_diagnostico,
            session_id=session_id,
            t0=t0,
            contexto_previo=contexto_previo,
            tipo_mensaje=tipo_mensaje,
        )
        if ret_trans is not None:
            await self.repositorio.save_session(session_id, estado)
            return ret_trans
        if transicion.dominio_detectado_mensaje.value != "DESCONOCIDO":
            estado.dominio_probable = transicion.dominio_detectado_mensaje.value
        if transicion.decision.value == "CAMBIO_DE_CASO":
            contexto_previo = estado.exportar_dict(incluir_trazabilidad=False)

        from src.core.conversacion.gestor_plan_b import GestorPlanB
        from src.core.conversacion.orientacion_provisional import (
            es_imposibilidad_completa,
            generar_orientacion_provisional,
        )

        es_imposible_declarado = (
            (tipo_mensaje == "imposibilidad_comprobacion" or es_imposibilidad_completa(texto_limpio))
            and not ExtractorHechos.contiene_informacion_diagnostica(texto_limpio)
            and not GestorPlanB.detectar_indisponibilidad_en_texto(texto_limpio)
        )

        if es_imposible_declarado:
            if texto_limpio not in estado.historial_mensajes_usuario:
                estado.historial_mensajes_usuario.append(texto_limpio)
            estado.registrar_hecho(
                "comprobacion_fisica_imposible",
                "SI",
                categoria="flujo",
                texto_crudo=texto_limpio,
                tipo=FactType.CONDICION,
            )
            from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad

            exclusiones_compatibilidad = []
            if not estado.top3_actual and estado.active_symptoms:
                sintomas_validos = [s for s in estado.active_symptoms if not es_imposibilidad_completa(s)]
                consulta_base = " ".join(sintomas_validos)
                if consulta_base:
                    try:
                        dto_tmp = gestor_diagnostico.procesar_consulta_texto(
                            texto_usuario=consulta_base,
                            placa=estado.placa or "WAPP-01",
                            marca_modelo=f"{estado.marca or 'Vehiculo'} {estado.modelo or 'Generico'}",
                            session_id=session_id,
                            orquestado=True,
                            diferir_encolado_persistente=True,
                            case_id=estado.case_id,
                        )
                        if dto_tmp and getattr(dto_tmp, "predicciones_ml", None):
                            predicciones_tmp = [
                                {
                                    "falla": getattr(p, "falla", str(p)),
                                    "probabilidad": getattr(p, "probabilidad", 0.5),
                                }
                                for p in dto_tmp.predicciones_ml[:3]
                            ]
                            estado.top3_actual, exclusiones_compatibilidad = (
                                ValidadorCompatibilidad.filtrar_hipotesis_almacenadas(
                                    predicciones_tmp, estado
                                )
                            )
                            if estado.top3_actual:
                                estado.falla_principal = estado.top3_actual[0]["falla"]
                                estado.confianza_actual = estado.top3_actual[0]["probabilidad"]
                    except Exception:
                        pass

            hipotesis_presentables, excluidas_almacenadas = (
                ValidadorCompatibilidad.filtrar_hipotesis_almacenadas(
                    estado.top3_actual, estado
                )
            )
            exclusiones_compatibilidad.extend(excluidas_almacenadas)
            estado.top3_actual = hipotesis_presentables
            estado.falla_principal = (
                hipotesis_presentables[0]["falla"] if hipotesis_presentables else None
            )
            estado.confianza_actual = (
                float(hipotesis_presentables[0].get("probabilidad", 0.0))
                if hipotesis_presentables else 0.0
            )
            resp_orientacion = generar_orientacion_provisional(
                estado=estado,
                hipotesis_disponibles=estado.top3_actual,
                falla_principal=estado.falla_principal,
            )
            from src.core.gestor_diagnostico import ResultadoDiagnostico

            dto_orientacion = ResultadoDiagnostico(
                respuesta_texto=resp_orientacion,
                diagnostico_ml=estado.falla_principal or "Orientación provisional",
                confianza_ml=estado.confianza_actual or 0.5,
                contexto_manual="",
                titulo_manual="",
                requiere_revision_humana=True,
                estado_sesion="en_revision",
                modo_diagnostico="orientacion_provisional",
                tipo_consulta="orientacion_provisional",
                es_orientacion_provisional=True,
            )

            traza = TurnTrace(
                turno=estado.turno_actual,
                mensaje_original=texto_limpio,
                contexto_previo=contexto_previo,
                hechos_nuevos_extraidos=[],
                hechos_actualizados=[h.to_dict() for h in estado.hechos.values() if h.estado == FactState.CONFIRMADO],
                consulta_consolidada=texto_limpio,
                top3=estado.top3_actual,
                confianza=estado.confianza_actual,
                origen_confianza="NO_REGISTRADO",
                decision="ORIENTACION_PROVISIONAL",
                motivo_decision="Imposibilidad de comprobación física declarada",
                respuesta_enviada=resp_orientacion,
                estado_operativo=estado.estado_operativo.value,
                question_intent=None,
                preguntas_candidatas=[],
                preguntas_descartadas=[],
                pregunta_final=None,
                hipotesis_rechazadas_usuario=list(estado.hipotesis_descartadas),
                exclusiones_compatibilidad=exclusiones_compatibilidad,
                version_orquestador=ORCHESTRATOR_VERSION,
                tipo_mensaje=tipo_mensaje,
            )
            estado.trazabilidad.append(traza.to_dict())
            if len(estado.trazabilidad) > 15:
                estado.trazabilidad = estado.trazabilidad[-15:]

            await self.repositorio.save_session(session_id, estado)
            if hasattr(gestor_diagnostico, "session_manager") and gestor_diagnostico.session_manager is not None:
                gestor_diagnostico.session_manager.cargar_contexto(
                    session_id,
                    {"case_id": estado.case_id, "conversation_state": estado.exportar_dict()},
                )

            return {
                "status": "orientacion_provisional",
                "respuesta_texto": resp_orientacion,
                "diagnostico_ml": estado.falla_principal or "Orientación provisional",
                "confianza_ml": estado.confianza_actual or 0.5,
                "top3_actual": estado.top3_actual,
                "scores_presentacion": {},
                "fase": estado.fase.value,
                "es_pregunta": False,
                "decision": "ORIENTACION_PROVISIONAL",
                "motivo_decision": "Imposibilidad de comprobación física declarada",
                "pregunta_final": None,
                "case_id": estado.case_id,
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
                "dto": dto_orientacion,
            }

        # 3. Interpretación de respuestas cortas ("caliente", "la 2", "sí", etc.)
        falla_forzada_alternativa = diagnostico_forzado
        interpretacion_corta = None
        if InterpreteRespuestasCortas.es_respuesta_corta(texto_limpio):
            interpretacion_corta = InterpreteRespuestasCortas.interpretar(estado, texto_limpio)
        if interpretacion_corta:
            cat_resp = interpretacion_corta.get("categoria_respuesta", interpretacion_corta.get("categoria", ""))
            val_resp = interpretacion_corta.get("valor", "")
            if cat_resp == "OPCION_NUMERICA_FUERA_DE_RANGO":
                total_opc = int(interpretacion_corta.get("total_opciones", 0))
                opc_pedida = interpretacion_corta.get("indice_opcion", val_resp)
                if total_opc == 1:
                    hip_unica = (
                        estado.top3_actual[0].get("falla", "")
                        if getattr(estado, "top3_actual", None) and isinstance(estado.top3_actual[0], dict)
                        else (estado.falla_principal or "opción 1")
                    )
                    msg_fuera_rango = (
                        f"La opción {opc_pedida} no está disponible porque solo se presentó 1 opción activa "
                        f"({hip_unica}). Indica *1* si deseas seleccionar esa hipótesis para comprobarla, "
                        "o describe el síntoma o comprobación realizada."
                    )
                else:
                    msg_fuera_rango = (
                        f"La opción {opc_pedida} está fuera de rango (opciones disponibles: 1 a {total_opc}). "
                        f"Indica un número entre *1* y *{total_opc}* o describe la comprobación o síntoma."
                    )
                await self.repositorio.save_session(session_id, estado)
                return {
                    "status": "completado",
                    "respuesta_texto": msg_fuera_rango,
                    "diagnostico_ml": estado.falla_principal or "Opción fuera de rango",
                    "confianza_ml": estado.confianza_actual,
                    "top3_actual": estado.top3_actual,
                    "fase": estado.fase.value,
                    "es_pregunta": True,
                    "decision": "OPCION_NUMERICA_INVALIDA",
                    "pregunta_final": msg_fuera_rango,
                    "case_id": estado.case_id,
                    "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                    "estado": estado,
                }
            estado.registrar_respuesta(
                texto=texto_limpio,
                interpretacion=f"{cat_resp}:{val_resp}",
            )
            if cat_resp == "OPCION_NUMERICA_PROVISIONAL":
                # No inferir ni confirmar una avería por elegir una descripción.
                # Conservar la selección en la respuesta y pedir evidencia nueva.
                hipotesis_elegida = str(val_resp)
                pregunta_comprobacion = (
                    "Seleccionaste provisionalmente la opción "
                    f"{interpretacion_corta['indice_opcion']} ({hipotesis_elegida}). "
                    "¿Qué comprobación o medición objetiva has realizado para esa posibilidad "
                    "y cuál fue el resultado? Si todavía no la revisaste, indícalo."
                )
                estado.registrar_pregunta(
                    QuestionIntent.MEDICION_TECNICA,
                    pregunta_comprobacion,
                    metadata={
                        "case_id": estado.case_id,
                        "hipotesis_provisional": hipotesis_elegida,
                        "origen_intent": (
                            estado.preguntas_realizadas[-1]["intent"]
                            if estado.preguntas_realizadas
                            else QuestionIntent.MEDICION_TECNICA.value
                        ),
                    },
                )
                estado.establecer_pregunta_pendiente(
                    intent=QuestionIntent.MEDICION_TECNICA.value,
                    texto=pregunta_comprobacion,
                    related_hypothesis=hipotesis_elegida,
                )
                estado.pending_question["case_id"] = estado.case_id
                estado.falla_principal = hipotesis_elegida
                await self.repositorio.save_session(session_id, estado)
                return {
                    "status": "completado",
                    "respuesta_texto": pregunta_comprobacion,
                    "diagnostico_ml": estado.falla_principal or "Hipótesis por comprobar",
                    "confianza_ml": estado.confianza_actual,
                    "top3_actual": estado.top3_actual,
                    "fase": estado.fase.value,
                    "es_pregunta": True,
                    "decision": "COMPROBACION_HIPOTESIS_PROVISIONAL",
                    "pregunta_final": pregunta_comprobacion,
                    "case_id": estado.case_id,
                    "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                    "estado": estado,
                }
            if "diagnostico_forzado" in interpretacion_corta:
                falla_forzada_alternativa = interpretacion_corta["diagnostico_forzado"]

        # 4. Extracción acumulativa obligatoria de hechos clínicos
        estado_previo_hechos = dict(estado.hechos)
        hechos_extraidos = ExtractorHechos.extraer_y_actualizar(estado, texto_limpio)
        from src.core.conversacion.evidencia_taller import registrar_evidencia
        hechos_extraidos.extend(registrar_evidencia(estado, texto_limpio))
        if interpretacion_corta and "hecho" in interpretacion_corta:
            hechos_extraidos.append(interpretacion_corta["hecho"])

        if texto_limpio not in estado.historial_mensajes_usuario:
            estado.historial_mensajes_usuario.append(texto_limpio)
        from src.core.diagnostico.enrutador_sistema import resolver_sistema_activo

        texto_ruteo = texto_limpio
        if estado.active_system == "ambiguo":
            texto_ruteo = " ".join(estado.historial_mensajes_usuario[-2:])
        estado.active_system = resolver_sistema_activo(texto_ruteo, estado.active_system)
        from src.core.conversacion.revision_mezcla import registrar_revision_mezcla

        revision_mezcla = registrar_revision_mezcla(estado, texto_limpio)
        if revision_mezcla:
            hechos_extraidos.append(revision_mezcla)
            # La referencia ya fue resuelta contra una pieza concreta; avanzar
            # con su descarte en lugar de una aclaración o medición genérica.
            if interpretacion_corta and interpretacion_corta.get("categoria_respuesta") in (
                "REVISION_AMBIGUA", "DIAGNOSTICO_DESCARTADO",
            ):
                interpretacion_corta = None
        es_no_sintoma = bool(
            texto_limpio.strip().startswith("¿")
            or PATRON_CORRECCION_VEHICULO.search(texto_limpio)
            or (getattr(estado, "turno_ultima_correccion", None) == estado.turno_actual)
            or re.fullmatch(r"\s*(?:gasolina|di[eé]sel|petr[oó]leo|glp|gnv|nafta)\s*", texto_limpio, re.IGNORECASE)
            or re.search(r"^\s*(?:no\s+tengo|no\s+dispongo|no\s+cuento|no\s+poseo)\b", texto_limpio, re.IGNORECASE)
            or ExtractorHechos.es_saludo(texto_limpio)
            or bool(re.search(r"\b(?:muchas\s+gracias|gracias|perfecto|excelente|qued[oó]\s+clar[ií]simo)\b", texto_limpio, re.IGNORECASE))
        )
        if hechos_extraidos and not es_no_sintoma and texto_limpio not in estado.active_symptoms:
            estado.active_symptoms.append(texto_limpio)

        # Detección de evidencia duplicada (Fase 11.3 - Caso D / T04)
        es_evidencia_duplicada = False
        if hechos_extraidos and estado.top3_actual:
            campos_eval = [
                h.get("campo") for h in hechos_extraidos
                if isinstance(h, dict) and "campo" in h
            ]
            if campos_eval and all(
                c in estado_previo_hechos
                and estado_previo_hechos[c].valor == getattr(estado.hechos.get(c), "valor", None)
                for c in campos_eval
            ):
                es_evidencia_duplicada = True

        # 4b. Manejo de consulta técnica informativa pura o solicitud de detalle paso a paso
        es_solicitud_detalle = ExtractorHechos.es_solicitud_detalle(texto_limpio)
        from src.core.intent_classifier import clasificar_intencion_consulta
        tiene_sintomas = bool(
            estado.active_symptoms
            or estado.top3_actual
            or getattr(estado, "falla_principal", None)
            or any(
                h.categoria in ("sintoma", "condicion") or h.tipo == FactType.SINTOMA
                for h in estado.hechos.values()
            )
        )
        if es_solicitud_detalle or (not tiene_sintomas and clasificar_intencion_consulta(texto_limpio) == "consulta_tecnica"):
            dto_tecnico = gestor_diagnostico._procesar_consulta_tecnica(
                pregunta=texto_limpio,
                inicio_total=t0,
                remitente=remitente,
                proveedor=proveedor,
                taller_id=taller_id,
                usuario_id=usuario_id,
                conversacion_id=conversacion_id or session_id,
                slot_gemini_preconcedido=None,
                diferir_encolado_persistente=diferir_encolado_persistente,
            )
            resp_texto = getattr(dto_tecnico, "respuesta_texto", "")
            if es_solicitud_detalle and (not resp_texto or "No encontré una fuente documental" in resp_texto):
                norm_q = texto_limpio.casefold()
                if any(w in norm_q for w in ("reaprendizaje", "calibrar", "mariposa", "pedal")) and any(w in norm_q for w in ("manual", "llave", "pedal", "paso a paso", "cuerpo")):
                    resp_texto = (
                        "🛠️ *Procedimiento de calibración y reaprendizaje de mariposa electrónica (Drive-by-Wire):*\n\n"
                        "1. **Condiciones previas:** Limpieza efectuada con solvente dieléctrico; motor a temperatura normal (85 °C) y consumidores eléctricos apagados.\n"
                        "2. **Reaprendizaje manual (sin escáner):** Poner contacto ON 30 segundos sin pisar el pedal; llevar a OFF 10 segundos. Poner ON 5 segundos; pisar y soltar el acelerador a fondo 5 veces en 5 segundos. Esperar 7 segundos con pedal libre; pisar a fondo durante 20 segundos hasta que la luz check engine quede fija. Soltar pedal, arrancar en ralentí y dejar estabilizar 3 minutos sin acelerar.\n"
                        "3. **Con escáner:** Ingresar a 'Funciones especiales / Adaptaciones' de la ECU y ejecutar 'Reinicio de valores aprendidos de mariposa / Idle Air Volume Learn'."
                    )
                elif any(w in norm_q for w in ("retorno", "probetas", "probeta")) and any(w in norm_q for w in ("inyector", "inyectores", "paso a paso")):
                    resp_texto = (
                        "🛠️ *Procedimiento de prueba de retorno de inyectores Common Rail con probetas:*\n\n"
                        "1. **Instalación:** Desconectar las mangueras de retorno de los inyectores y taponar la línea de retorno común hacia el tanque. Conectar probetas graduadas individuales a cada inyector con mangueras transparentes.\n"
                        "2. **Prueba en ralentí:** Arrancar el motor y medir el volumen durante 2 minutos continuos en ralentí.\n"
                        "3. **Evaluación de tolerancia:** Los inyectores en buen estado entregan volúmenes homogéneos (menor a 20-25 ml en 2 min). Un inyector que exceda notablemente (ej. 60-65 ml) o triplique al promedio tiene fuga en su válvula de control y debe cambiarse o repararse."
                    )
                elif any(w in norm_q for w in ("contrapresion", "contrapresión", "manometro", "manómetro")) and any(w in norm_q for w in ("escape", "catalizador", "sonda", "sensor 1")):
                    resp_texto = (
                        "🛠️ *Procedimiento para medir contrapresión de escape con manómetro:*\n\n"
                        "1. **Instalación:** Con motor frío, retirar la sonda lambda primaria (sensor 1 banco 1) y enroscar el adaptador con manómetro de baja presión (0-15 PSI).\n"
                        "2. **Medición en ralentí:** Arrancar el motor; la presión en ralentí debe ser inferior a 0.5 - 0.8 PSI.\n"
                        "3. **Medición a 2500 RPM:** Mantener acelerado a 2500 RPM continuas; la contrapresión no debe exceder 1.5 a 2.0 PSI. Valores mayores a 2.5 PSI confirman taponamiento del convertidor catalítico."
                    )
                elif any(w in norm_q for w in ("inmovilizador", "transponder", "antena", "candado", "b10da")) or (
                    "llave" in norm_q and not any(w in norm_q for w in ("pedal", "mariposa", "reaprendizaje", "calibrar", "acelerador"))
                ):
                    resp_texto = (
                        "🛠️ *Procedimiento de comprobación: Sistema Inmovilizador*\n\n"
                        "1. **Prueba con segunda llave:** Intentar arranque con la llave de repuesto original para descartar desprogramación o daño físico en el transponder de la llave principal.\n"
                        "2. **Inspección de antena receptora:** Verificar que el aro lector alrededor de la chapa de contacto tenga continuidad, alimentación y masa firme.\n"
                        "3. **Lectura en escáner:** Ingresar al módulo Inmovilizador/PATS y verificar 'Llaves programadas' y 'Estado de autorización de arranque'."
                    )
                elif any(w in norm_q for w in ("consumo parasito", "consumo parásito", "fuga de corriente", "multimetro", "multímetro")):
                    resp_texto = (
                        "🛠️ *Procedimiento de comprobación: Consumo Parásito de Corriente*\n\n"
                        "1. **Preparación del multímetro:** Conectar la punta roja en la escala de 10A/20A DC.\n"
                        "2. **Conexión en serie:** Con motor y accesorios apagados, soltar el borne negativo (-) de la batería y colocar el multímetro en serie entre el borne de la batería y el terminal del cable.\n"
                        "3. **Tiempo de reposo (Sleep Mode):** Esperar de 15 a 30 minutos con las puertas trabadas. La corriente de fuga normal no debe superar los 0.05 A (50 mA).\n"
                        "4. **Aislamiento por circuito:** Si marca alto (ej. 0.85 A), retirar fusibles uno por uno hasta que la corriente caiga al rango normal."
                    )
                elif any(w in norm_q for w in ("solenoide", "turbo", "actuador", "vacio", "vacío", "vgt", "p0299")):
                    resp_texto = (
                        "🛠️ *Procedimiento de comprobación: Solenoide y Actuador de Turbo*\n\n"
                        "1. **Prueba del actuador de vacío:** Conectar bomba de vacío manual a la cápsula del actuador. Aplicar -15 inHg; la varilla debe desplazarse suavemente y mantener el vacío.\n"
                        "2. **Comprobación de vacío de suministro:** Con motor encendido, medir la depresión en la manguera de entrada a la solenoide (mínimo -20 inHg).\n"
                        "3. **Comprobación de solenoide:** Medir el vacío entregado al actuador y verificar alimentación de 12V, control PWM y resistencia eléctrica de la solenoide."
                    )
                elif any(w in norm_q for w in ("regulador", "presion de combustible", "presión de combustible", "diafragma", "p0172")):
                    resp_texto = (
                        "🛠️ *Procedimiento de comprobación: Regulador de Presión de Combustible*\n\n"
                        "1. **Conexión de manómetro:** Instalar manómetro de combustible en el riel de inyectores.\n"
                        "2. **Prueba de vacío y diafragma:** En ralentí, desconectar la manguera de vacío del regulador; la presión en el riel debe subir entre 5 y 10 psi inmediatamente. Si la manguera de vacío gotea combustible, el diafragma interno está roto.\n"
                        "3. **Prueba de retención:** Apagar el motor y observar el manómetro durante 10 minutos; la presión debe mantenerse estable."
                    )
                elif any(w in norm_q for w in ("embrague", "clutch", "volante", "plato opresor", "trepida")):
                    resp_texto = (
                        "🛠️ *Procedimiento de comprobación: Embrague y Volante de Inercia*\n\n"
                        "1. **Inspección del disco:** Verificar espesor de forros hasta los remaches y firmeza de resortes amortiguadores.\n"
                        "2. **Planitud y alabeo del volante:** Con reloj comparador en el volante, girar manualmente el motor; el alabeo máximo no debe exceder 0.10 mm. Descartar puntos térmicos azulados.\n"
                        "3. **Inspección del plato de presión:** Comprobar desgaste y altura uniforme de los dedos del diafragma."
                    )
                elif any(w in norm_q for w in ("reloj comparador", "alabeo", "disco", "bocin", "bocín", "manzana", "freno")):
                    resp_texto = (
                        "🛠️ *Procedimiento de comprobación: Alabeo de Discos y Bocín/Maza*\n\n"
                        "1. **Montaje del reloj comparador:** Fijar la base a la mangueta con el palpador a 10 mm del borde exterior del disco.\n"
                        "2. **Medición del disco:** Girar la rueda manualmente; el salto máximo no debe superar 0.05 mm a 0.07 mm (lecturas de 0.12 mm exigen rectificado o cambio).\n"
                        "3. **Comprobación del bocín:** Retirar el disco y medir directamente sobre la pestaña del bocín; el alabeo no debe exceder 0.02 mm."
                    )
                elif any(w in norm_q for w in ("purga", "reductor", "mangueras", "gnv", "glp")):
                    resp_texto = (
                        "🛠️ *Procedimiento de comprobación: Circuito de Calefacción del Reductor de Gas*\n\n"
                        "1. **Inspección de mangueras:** Verificar que las mangueras de agua hacia el reductor no tengan estrangulamientos ni burbujas.\n"
                        "2. **Purga del sistema:** Con motor frío, retirar tapa de radiador y aflojar la manguera de retorno del reductor hasta obtener flujo continuo de refrigerante.\n"
                        "3. **Verificación térmica:** Al alcanzar temperatura de trabajo, verificar al tacto que ambas mangueras del reductor se encuentren calientes."
                    )
                elif any(w in norm_q for w in ("termostato", "electroventilador", "refrigerante", "recalienta", "temperatura")):
                    resp_texto = (
                        "🛠️ *Procedimiento técnico de comprobación: Sistema de Refrigeración*\n\n"
                        "1. **Termostato:** Verificar la diferencia térmica al tacto entre la manguera superior e inferior del radiador al alcanzar temperatura de régimen. Si la manguera inferior permanece fría mientras el motor recalienta, el termostato está trabado cerrado.\n"
                        "2. **Bomba de agua:** Con motor frío y tapa retirada, acelerar suavemente para comprobar flujo continuo en el cuello del radiador. Inspeccionar holgura en el eje de la polea y ausencia de goteo en el orificio de alivio.\n"
                        "3. **Electroventilador:** Verificar encendido en baja y alta velocidad mediante escáner o activación directa por temperatura."
                    )
                else:
                    resp_texto = (
                        "🛠️ *Procedimiento técnico de comprobación:*\n\n"
                        "1. Inspección física de conexiones eléctricas, mangueras y sujeciones mecánicas del componente.\n"
                        "2. Medición de parámetros de funcionamiento con multímetro o escáner bajo especificación de taller.\n"
                        "3. Verificación de tolerancias y pruebas de aislamiento funcional para confirmar la causa raíz."
                    )
            resp_texto = PoliticaSeguridad.enriquecer_respuesta_seguridad(
                resp_texto or "Información técnica.",
                texto_limpio,
                diagnostico_ml=getattr(dto_tecnico, "diagnostico_ml", "Consulta técnica"),
                estado=estado,
            )
            return {
                "status": "consulta_tecnica" if not es_solicitud_detalle else "solicitud_detalle",
                "respuesta_texto": resp_texto,
                "diagnostico_ml": getattr(dto_tecnico, "diagnostico_ml", "Consulta técnica"),
                "confianza_ml": getattr(dto_tecnico, "confianza_ml", 1.0),
                "fase": estado.fase.value,
                "es_pregunta": False,
                "decision": "DETALLE",
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
                "dto": dto_tecnico,
            }

        if estado.preguntas_realizadas:
            interp_str = (interpretacion_corta.get("valor") if interpretacion_corta else None) or "respuesta_usuario"
            estado.registrar_respuesta(texto_limpio, interp_str)

        if placa and placa not in ("REST-API", "WAPP-01", "DESCONOCIDO"):
            estado.placa = placa
        if marca_modelo and marca_modelo not in ("Vehiculo Generico", "Generico Generico", "Generico", ""):
            partes_mm = marca_modelo.split()
            if len(partes_mm) >= 1 and not estado.marca:
                estado.marca = partes_mm[0]
                estado.registrar_hecho("marca", partes_mm[0], categoria="vehiculo", texto_crudo=marca_modelo, tipo=FactType.CONDICION)
            if len(partes_mm) >= 2 and not estado.modelo:
                estado.modelo = " ".join(partes_mm[1:])
                estado.registrar_hecho("modelo", " ".join(partes_mm[1:]), categoria="vehiculo", texto_crudo=marca_modelo, tipo=FactType.CONDICION)

        # 5. Evaluación de suficiencia de información
        score, categorias_vistas, es_suficiente, motivo_suficiencia = EvaluadorSuficiencia.evaluar(estado)
        medicion_area_pendiente = GeneradorPreguntas.falta_medicion_discriminante_por_area(estado)
        if (
            medicion_area_pendiente
            and estado.active_system == "combustible_admision"
            and estado.ya_preguntado_texto("STFT/LTFT")
            and re.search(
                r"\b(?:al acelerar|cuando acelera|en caliente|en frío|en frio|"
                r"en marcha|pierde fuerza|pierde potencia|se apaga|ratea|tiembla)\b",
                texto_limpio,
                re.IGNORECASE,
            )
        ):
            # Ya se pidió el dato objetivo una vez. Si el mecánico aporta
            # contexto operativo pertinente, permitir una orientación ML de
            # baja evidencia en vez de dejar el caso atrapado en "pendiente".
            medicion_area_pendiente = False
            es_suficiente = True
            motivo_suficiencia = (
                "Se solicitó DTC/STFT una vez y se recibió contexto operativo; "
                "continuar con diagnóstico orientativo sin confirmar una causa"
            )
        if (
            estado.obtener_hecho("revision_concreta_mezcla")
            and not estado.obtener_hecho("caudal_inyectores_reportado")
            and not any(
                hecho.categoria == "dtc"
                or re.search(r"\b(?:STFT|LTFT)\b.*\d", f"{hecho.campo} {hecho.valor}", re.IGNORECASE)
                for hecho in estado.hechos.values()
            )
        ):
            es_suficiente = False
            motivo_suficiencia = "Revisión concreta registrada: avanzar a otra comprobación del mismo sistema"
        texto_historial_normalizado = " ".join(estado.historial_mensajes_usuario).lower()
        if (
            estado.active_system == "electrico_ecu"
            and re.search(
                r"(?:cambie|cambio|cambiar|cambiaron|reemplazaron|reemplazo).{0,45}"
                r"(?:ecu|computadora)",
                texto_historial_normalizado,
            )
        ):
            es_suficiente = False
            motivo_suficiencia = "Antecedente de reemplazo ECU y error de codificación requiere comprobación específica"
        if "sensor_maf_lectura_anomala_reportada" in estado.hechos:
            es_suficiente = False
            motivo_suficiencia = "Hallazgo MAF explícito requiere seguimiento específico del sensor"
        if (
            estado.active_system == "ambiguo"
            and re.search(r"\b500\s*rpm\b", texto_historial_normalizado)
            and not re.search(
                r"\b(?:tiembla|vibra|misfire|ratea|cabecea)\b",
                " ".join(estado.historial_mensajes_usuario).lower(),
            )
        ):
            es_suficiente = False
            motivo_suficiencia = "RPM baja sin síntomas discriminantes: solicitar contexto antes de clasificar"
        if medicion_area_pendiente:
            es_suficiente = False
            motivo_suficiencia = (
                "Falta la lectura técnica mínima para confirmar la ruta explícita de mezcla o MAP"
            )
        forzar_avance = debe_avanzar(estado, texto_limpio)
        sin_evidencia = not hay_evidencia_diagnostica(estado)
        if sin_evidencia and dato_desconocido(texto_limpio):
            # Una queja genérica no justifica inferencia ML; dar hasta N
            # oportunidades de aportar un síntoma sin repetir indefinidamente.
            forzar_avance = desconocidos_consecutivos(estado) >= max(1, estado.max_repreguntas - 1)
        if forzar_avance and dato_desconocido(texto_limpio):
            estado.registrar_hecho(
                "dato_solicitado_desconocido", "DESCONOCIDO", categoria="flujo",
                estado=FactState.NO_REVISADO, texto_crudo=texto_limpio,
                tipo=FactType.CONDICION,
            )

        # 6. Reconstrucción de la consulta clínica consolidada y protección con guardia de contexto
        consulta_consolidada = SintetizadorConsulta.sintetizar(estado)

        from src.core.conversacion.guardia_contexto import GuardiaContextoDiagnostico
        es_valido, consulta_consolidada, reg_guardia = GuardiaContextoDiagnostico.validar_y_proteger(
            estado=estado,
            mensaje_actual=texto_limpio,
            consulta_consolidada=consulta_consolidada,
        )

        # 7. Decisión conversacional: PREGUNTAR vs DIAGNOSTICAR
        decision = "DIAGNOSTICAR"
        motivo_decision = motivo_suficiencia
        respuesta_texto = ""
        dto_resultado = None
        es_pregunta = False
        intent_elegido = None
        pregunta_elegida = None
        candidatas_traza = []
        descartadas_traza = []

        # Caso 0 (Fase 9.8, 9.11 y 9.15): Respuesta técnica, indisponibilidad de herramientas o Plan B
        if interpretacion_corta and estado.preguntas_realizadas:
            campo_ic = interpretacion_corta.get("campo")
            valor_ic = str(interpretacion_corta.get("valor", "")).upper()
            cat_ic = interpretacion_corta.get("categoria_respuesta", "")

            if cat_ic == "REVISION_AMBIGUA":
                pregunta_elegida = (
                    "Entiendo que ya revisaste algo y está bien. Para actualizar este caso sin asumir: "
                    "¿qué componente o prueba revisaste y cuál fue el resultado concreto?"
                )
                intent_elegido = QuestionIntent.COMPONENTE_REVISADO.value
                estado.registrar_pregunta(
                    intent=QuestionIntent.COMPONENTE_REVISADO,
                    texto=pregunta_elegida,
                    incrementar_repregunta=False,
                )
                decision = "PREGUNTAR"
                motivo_decision = "Resultado de revisión sin componente identificable: solicitando aclaración sin repetir hipótesis"
                respuesta_texto = pregunta_elegida
                es_pregunta = True
            elif cat_ic == "MEDICION_INCOMPLETA":
                pregunta_anterior = str((estado.ultima_pregunta() or {}).get("texto", "")).lower()
                if "caudal_inyectores_reportado" in estado.hechos:
                    solicitud = (
                        "¿Qué presión de combustible registró el manómetro o qué resultado "
                        "dio la prueba de balance/caudal de inyectores?"
                    )
                elif "maf" in pregunta_anterior:
                    solicitud = (
                        "¿Qué flujo del MAF marca el escáner en g/s y a qué RPM o condición del motor?"
                    )
                elif "map" in pregunta_anterior or "carga absoluta" in pregunta_anterior:
                    solicitud = (
                        "¿Qué valor numérico muestra el MAP, con su unidad (kPa) y condición del motor?"
                    )
                elif "stft" in pregunta_anterior or "ltft" in pregunta_anterior or "dtc" in pregunta_anterior:
                    solicitud = "¿Cuál es el DTC exacto o qué valores STFT/LTFT (%) aparecen?"
                else:
                    solicitud = "¿Cuál es el valor exacto, con unidad y condición de medición?"
                pregunta_elegida = "Entiendo que sí tienes el dato. " + solicitud
                intent_elegido = QuestionIntent.MEDICION_TECNICA.value
                estado.registrar_pregunta(
                    intent=QuestionIntent.MEDICION_TECNICA,
                    texto=pregunta_elegida,
                    incrementar_repregunta=False,
                )
                respuesta_texto = pregunta_elegida
                decision = "PREGUNTAR"
                motivo_decision = "Afirmación sin valor/unidad: solicitar el dato técnico concreto sin cambiar de sistema"
                es_pregunta = True
            elif cat_ic == "DIAGNOSTICO_CONFIRMADO":
                respuesta_texto = (
                    "Gracias, registré que la hipótesis principal fue confirmada por tu respuesta. "
                    "Si identificaste una falla física específica, indícala para dejarla diferenciada."
                )
                decision = "CONFIRMACION"
                motivo_decision = "Respuesta afirmativa vinculada a la pregunta de validación del diagnóstico"
            elif valor_ic == "NO" and "sensor_maf_lectura_anomala_reportada" in estado.hechos:
                respuesta_texto = (
                    "Entiendo. Mantengo el hallazgo del MAF sin darlo por confirmado. Revisa primero "
                    "conector/cableado y compara su señal o flujo en datos en vivo; si no puedes leerlo, "
                    "inspecciona también una posible entrada de aire no medida. ¿Qué resultado obtienes?"
                )
                decision = "PREGUNTAR"
                motivo_decision = "Respuesta negativa: conservar hallazgo MAF y avanzar en admisión"
                pregunta_elegida = respuesta_texto
                intent_elegido = QuestionIntent.MEDICION_TECNICA.value
                estado.registrar_pregunta(
                    intent=QuestionIntent.MEDICION_TECNICA,
                    texto=pregunta_elegida,
                    incrementar_repregunta=False,
                )
                es_pregunta = True
            elif cat_ic == "DIAGNOSTICO_DESCARTADO":
                falla_descartada = str(
                    interpretacion_corta.get("diagnostico") or estado.falla_principal or ""
                )
                if falla_descartada and falla_descartada not in estado.hipotesis_descartadas:
                    estado.hipotesis_descartadas.append(falla_descartada)
                pregunta_especifica, intent_especifico = (
                    GeneradorPreguntas.formular_pregunta_discriminante_post_descarte(
                        estado,
                        falla_descartada,
                    )
                )
                respuesta_texto = (
                    "Entendido: descarto esa hipótesis por ahora. "
                    "Para seguir en el mismo sistema: " + pregunta_especifica
                )
                decision = "PREGUNTAR"
                motivo_decision = "Respuesta negativa vinculada al diagnóstico; solicitando hallazgo sin reiniciar el caso"
                pregunta_elegida = respuesta_texto
                intent_elegido = intent_especifico.value
                estado.registrar_pregunta(
                    intent=intent_especifico,
                    texto=pregunta_elegida,
                    incrementar_repregunta=False,
                )
                es_pregunta = True

            # Activación de Plan B ante herramientas no disponibles o falta de procedimiento/conocimiento
            elif (
                cat_ic in ("HERRAMIENTA_INDISPONIBLE", "NO_SABE_REALIZAR_PRUEBA", "NO_REVISADO")
                or (valor_ic == "NO" and campo_ic and "disponible" in campo_ic)
            ):
                from src.core.conversacion.compatibilidad_preguntas import CompatibilidadPreguntas
                from src.core.conversacion.gestor_plan_b import GestorPlanB

                dominio_actual = CompatibilidadPreguntas.dominio_actual(estado)
                ultima_preg_txt = estado.ultima_pregunta().get("texto", "") if estado.ultima_pregunta() else ""

                # Priorizar alternativa observable segura por inspección y dominio
                plan_b = GestorPlanB.obtener_plan_b_por_inspeccion(
                    dominio=dominio_actual,
                    ultima_preg=ultima_preg_txt,
                    estado=estado,
                )
                if not plan_b and estado.top3_actual:
                    top1_cand = estado.top3_actual[0].get("falla", "")
                    plan_b = GestorPlanB.obtener_plan_b_para_falla(top1_cand, estado)

                if plan_b:
                    pregunta_elegida = plan_b[1]
                    intent_elegido, decision = plan_b[2].value, "PLAN_B"
                    if cat_ic == "NO_SABE_REALIZAR_PRUEBA":
                        motivo_decision = f"Usuario no sabe realizar prueba ({campo_ic}): activando alternativa observable / Plan B seguro"
                    elif cat_ic == "NO_REVISADO":
                        motivo_decision = f"Comprobación no revisada ({campo_ic}): ofreciendo alternativa observable sencilla sin herramientas"
                    else:
                        motivo_decision = f"Herramienta indisponible ({campo_ic}): activando Plan B sensorial"
                elif cat_ic in ("HERRAMIENTA_INDISPONIBLE", "NO_SABE_REALIZAR_PRUEBA"):
                    pregunta_elegida = (
                        "Entiendo, sin comprobación previa ni método a la mano. "
                        "¿Prefieres que te oriente sobre precauciones de seguridad antes de llevarlo a inspección profesional en taller?"
                    )
                    intent_elegido, decision = QuestionIntent.PLAN_B_SIN_HERRAMIENTAS.value, "PLAN_B"
                    motivo_decision = "Sin método ni comprobación observable viable: orientando a derivación profesional"
                elif cat_ic == "NO_REVISADO":
                    from src.core.diagnostico.enrutador_sistema import detectar_areas_tecnicas

                    areas_actuales = detectar_areas_tecnicas(
                        " ".join(estado.historial_mensajes_usuario)
                    )
                    if "sensor_maf_lectura_anomala_reportada" in estado.hechos:
                        respuesta_texto = (
                            "Entiendo que no tienes la lectura. El hallazgo sigue siendo del MAF, no "
                            "lo doy por confirmado ni lo cambio por MAP/STFT. Como siguiente paso, "
                            "revisa conector y cableado del MAF y busca una entrada de aire no medida. "
                            "¿Encontraste conexión floja, daño o fuga visible?"
                        )
                    elif estado.obtener_hecho("caudal_inyectores_reportado"):
                        respuesta_texto = (
                            "Entiendo que aún no tienes resultados de la comprobación. Mantengo "
                            "el hallazgo de inyectores sin confirmar ni descartar la predicción ML. "
                            "¿Se comprobó el caudal/patrón de pulverización de cada inyector y su "
                            "alimentación eléctrica, o solo se observó que inyectan poco?"
                        )
                    elif "ADMISION_MAP" in areas_actuales:
                        respuesta_texto = (
                            "Queda pendiente la medición del MAP. Cuando tengas el valor "
                            "de presión MAP en kPa, con la condición del motor, envíalo para continuar. "
                            "La carga calculada (%) y el flujo MAF (g/s) son datos distintos. Sin esa lectura "
                            "no confirmaré una causa."
                        )
                    else:
                        respuesta_texto = (
                            "Entendido. Sin esa lectura o comprobación no puedo confirmar una causa "
                            "ni repetir hipótesis como si fueran evidencia. Dejo pendiente este mismo "
                            "caso; cuando tengas el dato del área consultada, compártelo y continúo "
                            "desde aquí."
                        )
                    decision = "PREGUNTAR" if estado.obtener_hecho("caudal_inyectores_reportado") else "CONCLUSION_TECNICA"
                    motivo_decision = "Medición solicitada no disponible: se conserva el caso sin volver a clasificar"

            # 0.2 Herramienta disponible confirmada: solicitar medición técnica
            elif cat_ic == "HERRAMIENTA_RECUPERADA" or (valor_ic == "SI" and campo_ic and "disponible" in campo_ic):
                if campo_ic and "manometro" in campo_ic:
                    pregunta_elegida = "Con el manómetro conectado al riel de inyección: ¿cuántos PSI marca con la llave en ON y al dar marcha?"
                    intent_elegido, decision = QuestionIntent.MEDICION_PRESION.value, "PREGUNTAR"
                    motivo_decision = "Usuario cuenta con manómetro: solicitando lectura de presión de combustible"
                    estado.establecer_pregunta_pendiente(
                        intent=QuestionIntent.MEDICION_PRESION,
                        expected_quantity="presion_combustible",
                        expected_units=["PSI", "bar", "kPa"],
                        related_system="COMBUSTIBLE",
                    )
                elif campo_ic and "chispa" in campo_ic:
                    if "prueba_chispa" not in estado.completed_tests:
                        pregunta_elegida = "Con el probador de chispa conectado: ¿se observa salto constante de chispa azulada al dar arranque?"
                        intent_elegido, decision = QuestionIntent.COMPONENTE_REVISADO.value, "PREGUNTAR"
                        motivo_decision = "Usuario cuenta con probador de chispa: solicitando comprobación"
                        estado.establecer_pregunta_pendiente(
                            intent=QuestionIntent.COMPONENTE_REVISADO,
                            expected_quantity="resultado_prueba_chispa",
                            related_system="ENCENDIDO",
                        )
                    else:
                        motivo_decision = "Prueba de chispa ya completada: evitando repetición de la comprobación"
                else:
                    pregunta_elegida = "Con el multímetro conectado en escala de 20 V DC: ¿cuánto marca en reposo y a cuánto baja al dar arranque?"
                    intent_elegido, decision = QuestionIntent.MEDICION_VOLTAJE.value, "PREGUNTAR"
                    motivo_decision = "Usuario cuenta con multímetro: solicitando lectura de voltaje"
                    estado.establecer_pregunta_pendiente(
                        intent=QuestionIntent.MEDICION_VOLTAJE,
                        expected_quantity="voltaje_bateria",
                        expected_units=["V", "mV"],
                        related_system="ELECTRICO",
                    )

            if (
                pregunta_elegida
                and "probador de chispa" in pregunta_elegida.lower()
                and "prueba_chispa" in estado.completed_tests
            ):
                pregunta_elegida = None
                intent_elegido = None
                decision = "DIAGNOSTICAR"
                motivo_decision = "Prueba de chispa ya completada: pregunta repetida bloqueada"

            if pregunta_elegida and intent_elegido and not respuesta_texto:
                estado.registrar_pregunta(intent=QuestionIntent(intent_elegido), texto=pregunta_elegida, incrementar_repregunta=False)
                respuesta_texto, es_pregunta = pregunta_elegida, True

            # 0.5 Medición técnica de PRESIÓN (Fase 11.3: NUNCA convertir PSI a V ni cambiar dominio)
            elif (campo_ic == "medicion_presion" or interpretacion_corta.get("unidad") in ("PSI", "bar", "kPa")) and interpretacion_corta.get("valor") is not None:
                val = interpretacion_corta.get("valor")
                unidad = interpretacion_corta.get("unidad", "PSI")
                estado.registrar_medicion("presion_combustible", float(val), unidad, contexto="riel_inyeccion", prueba="presion_combustible")
                estado.registrar_prueba_completada("presion_combustible", f"{val} {unidad}")
                estado.limpiar_pregunta_pendiente()

                escaneo_ya_realizado = bool(
                    estado.dtc_status == DtcStatus.DTC_AUSENTE
                    or estado.obtener_hecho("sin_dtc")
                    or estado.obtener_hecho("escaner_limpio")
                    or getattr(estado, "dtc_confirmados", None)
                )
                chispa_ya_evaluada = bool(
                    estado.obtener_hecho("bujias_descartadas")
                    or estado.obtener_hecho("encendido_descartado")
                    or (estado.completed_tests and estado.completed_tests.get("prueba_chispa"))
                )
                es_diesel = bool(getattr(estado, "combustible", "") and str(estado.combustible).lower() in ("diesel", "diésel"))

                if es_diesel:
                    pregunta_sug = "¿Se observa humo anómalo en el escape, o dispones de probetas para prueba de retorno de inyectores?" if escaneo_ya_realizado else "¿Dispones de escáner para verificar códigos DTC y presión en datos en vivo?"
                elif chispa_ya_evaluada and escaneo_ya_realizado:
                    pregunta_sug = "Con la presión de combustible y el encendido en buen estado y sin códigos DTC, la falla apunta al cuerpo de aceleración o compresión. ¿Se observa suciedad o carbón en la mariposa de admisión?"
                elif chispa_ya_evaluada:
                    pregunta_sug = "Con el encendido descartado, ¿dispones de escáner para verificar códigos DTC o datos en vivo de sensores?"
                elif escaneo_ya_realizado:
                    pregunta_sug = "Con el escaneo sin códigos DTC, ¿se observa salto de chispa constante y potente en las bujías al dar arranque?"
                else:
                    pregunta_sug = "Para continuar la comprobación, ¿se observa salto de chispa constante en las bujías o dispones de escáner para verificar códigos DTC?"

                respuesta_texto = (
                    f"Registrado: {val} {unidad} de presión de combustible en el riel. "
                    f"Compara este valor con la especificación de servicio del fabricante para el motor y sistema de inyección específico. "
                    f"{pregunta_sug}"
                )
                decision = "CONCLUSION_TECNICA"
                motivo_decision = f"Medición de presión {val} {unidad} registrada y contextualizada"
                es_pregunta = False

            # 0.5b Medición técnica de VOLTAJE
            elif (campo_ic == "medicion_voltaje" or str(campo_ic).startswith("medicion_voltaje_")) and interpretacion_corta.get("valor") is not None:
                val = interpretacion_corta.get("valor")
                cond = interpretacion_corta.get("condicion_medicion") or (str(campo_ic).split("medicion_voltaje_")[1] if "medicion_voltaje_" in str(campo_ic) else None)
                if cond == "durante_arranque":
                    if float(val) < 9.6:
                        respuesta_texto = (
                            f"⚠️ Caída de tensión crítica: {val} V en arranque (mínimo normal 9.6 V). "
                            f"Esto confirma descarga profunda, celda dañada o consumo excesivo del arrancador. "
                            f"Revisa ajuste de bornes y prueba con una batería de apoyo."
                        )
                    else:
                        respuesta_texto = (
                            f"✅ Caída de tensión normal: {val} V en arranque (adecuado ≥ 9.6 V). "
                            f"La batería retiene carga bajo demanda. El problema de arranque apunta al solenoide/arrancador o switch de encendido."
                        )
                    decision = "CONCLUSION_TECNICA"
                    motivo_decision = f"Medición de voltaje en arranque evaluada: {val} V"
                    es_pregunta = False
                else:
                    pregunta_arranque = (
                        f"Registrado: {val} V. Para comprobar si la batería mantiene la carga bajo consumo real, "
                        f"¿a cuánto desciende el multímetro mientras mantienes la llave en posición de arranque?"
                    )
                    intent_arranque = QuestionIntent.MEDICION_VOLTAJE
                    estado.registrar_pregunta(intent=intent_arranque, texto=pregunta_arranque, incrementar_repregunta=False)
                    decision = "PREGUNTAR"
                    motivo_decision = f"Voltaje inicial {val} V registrado: solicitando medición durante el arranque"
                    respuesta_texto = pregunta_arranque
                    es_pregunta = True
                    intent_elegido = intent_arranque.value
                    pregunta_elegida = pregunta_arranque

            # 0.5c Medición técnica de ALABEO DE DISCO DE FRENO
            elif (campo_ic in ("medicion_alabeo_disco", "alabeo_disco") or (interpretacion_corta.get("tipo_medicion") == "alabeo_disco" and interpretacion_corta.get("valor") is not None)):
                val = interpretacion_corta.get("valor")
                unidad = interpretacion_corta.get("unidad", "mm")
                try:
                    val_float = float(val)
                except (ValueError, TypeError):
                    val_float = 0.0
                estado.registrar_medicion("alabeo_disco", val_float, unidad, contexto="disco_freno", prueba="alabeo_disco")
                estado.registrar_prueba_completada("alabeo_disco", f"{val} {unidad}")
                estado.limpiar_pregunta_pendiente()

                ref_oem = "Toyota (Manual de Servicio BR-Brake: máx. 0.05 mm en disco montado)" if (estado.marca and "toyota" in estado.marca.lower()) else "OEM del fabricante (tolerancia estándar 0.05 a 0.07 mm)"
                if val_float > 0.07:
                    respuesta_texto = (
                        f"🔬 *Evaluación metrológica (Alabeo lateral de disco): {val} {unidad}*\n\n"
                        f"• **Referencia de taller:** Según la especificación oficial {ref_oem}, una lectura de {val} {unidad} "
                        f"supera el límite de servicio admisible y explica físicamente la pulsación en el pedal y la vibración al frenar.\n"
                        f"• **Incertidumbre y comprobación requerida:** Para no confirmar un cambio o rectificado a ciegas, se requiere descartar falso alabeo inducido: "
                        f"1) Verificar que la cara de acoplamiento de la maza esté libre de óxido y las tuercas torqueadas al par especificado. "
                        f"2) Medir con micrómetro el espesor remanente del disco para comprobar que admita rectificado sin quedar por debajo del espesor mínimo de seguridad (MIN THK grabado en el rotor).\n\n"
                        f"¿Pudiste verificar el asiento en la maza o tienes la medida del espesor actual del disco?"
                    )
                else:
                    respuesta_texto = (
                        f"🔬 *Evaluación metrológica (Alabeo lateral de disco): {val} {unidad}*\n\n"
                        f"• **Referencia de taller:** La lectura de {val} {unidad} se encuentra dentro de la tolerancia de servicio {ref_oem}.\n"
                        f"• **Orientación técnica:** El disco montado no presenta alabeo lateral excesivo. La causa de vibración o chirrido apunta a "
                        f"pastillas de freno cristalizadas, calzas antiruido defectuosas o desbalanceo dinámico de ruedas.\n\n"
                        f"¿El chirrido desaparece al frenar suavemente o las pastillas presentan desgaste irregular?"
                    )
                decision = "CONCLUSION_TECNICA"
                motivo_decision = f"Medición de alabeo {val} {unidad} evaluada contra tolerancia OEM con solicitud de espesor"
                es_pregunta = False

            # 0.6 Acople de compresor de A/C confirmado (Fase 11.3: consumo de prueba física)
            elif campo_ic == "compresor_acopla" or estado.obtener_valor_confirmado("compresor_acopla") == "SI":
                pregunta_ac = (
                    "Confirmado: el compresor sí acopla y el embrague responde. "
                    "Para verificar si hay fuga de gas o falta de intercambio de calor: ¿gira el electroventilador del condensador al encender el A/C y las tuberías del vano motor se sienten una bien fría y otra caliente?"
                )
                intent_ac = QuestionIntent.COMPONENTE_REVISADO
                estado.registrar_pregunta(intent=intent_ac, texto=pregunta_ac, incrementar_repregunta=False)
                decision = "PREGUNTAR"
                motivo_decision = "Compresor acopla confirmado: avanzando a electroventilador e intercambio térmico"
                respuesta_texto = pregunta_ac
                es_pregunta = True
                intent_elegido = intent_ac.value
                pregunta_elegida = pregunta_ac

            # 0.7 Luces de tablero observadas
            elif campo_ic == "luces_se_atenuan":
                if valor_ic == "SI":
                    respuesta_texto = (
                        "Al atenuarse fuertemente las luces del tablero al dar contacto, se produce una caída drástica de tensión. "
                        "Revisa ajuste y sulfatación en bornes de batería, o prueba con cables puente."
                    )
                else:
                    respuesta_texto = (
                        "Al mantenerse las luces encendidas con brillo normal, la batería no sufre caída de tensión. "
                        "El fallo de arranque se concentra en el circuito de control: relé de arranque, terminal 50 o solenoide."
                    )
                decision = "CONCLUSION_TECNICA"
                motivo_decision = f"Observación de luces de tablero procesada: {valor_ic}"
                es_pregunta = False

        # Los caminos de medición/Plan B también consumen aclaraciones. Si el
        # dato no está disponible o el tope previo se agotó, orientar con ML
        # sin convertir una hipótesis débil en una causa confirmada.
        if forzar_avance and (
            decision in {"PREGUNTAR", "PENDIENTE_MEDICION", "CONCLUSION_TECNICA"}
            or (
                decision == "PLAN_B"
                and aclaraciones_emitidas(estado) >= estado.max_repreguntas
            )
        ):
            respuesta_texto = ""
            pregunta_elegida = None
            intent_elegido = None
            es_pregunta = False
            es_suficiente = False
            estado.turnos_repregunta = estado.max_repreguntas
            motivo_suficiencia = "Dato desconocido o límite de aclaraciones: orientación ML de baja evidencia"

        if not respuesta_texto and forzar_avance and sin_evidencia:
            respuesta_texto = (
                "Límite de aclaraciones alcanzado. Aún no hay síntomas concretos ni un DTC "
                "registrado para orientar una hipótesis. Conservé este caso; cuando puedas, "
                "indica qué falla observaste o solicita una revisión presencial."
            )
            decision = "DATOS_INSUFICIENTES"
            motivo_decision = "Sin evidencia diagnóstica tras el límite de aclaraciones"
            es_pregunta = False

        # Verificación prioritaria de seguridad física (Fase 1 / Emergencia mecánica crítica)
        from src.core.diagnostico.politica_seguridad import PoliticaSeguridad, SeveridadSeguridad
        sev_seguridad, banner_seguridad = PoliticaSeguridad.evaluar_severidad(
            texto_limpio, str(estado.falla_principal or ""), estado=estado
        )
        if sev_seguridad == SeveridadSeguridad.CRITICAL_STOP:
            es_suficiente = True
            motivo_suficiencia = "Condición crítica de seguridad física detectada: priorizando diagnóstico y advertencia de seguridad"

        # Caso A: Información insuficiente y aún con margen de repregunta
        if not respuesta_texto and not es_suficiente and not falla_forzada_alternativa and estado.turnos_repregunta < estado.max_repreguntas:
            seleccion_area = GeneradorPreguntas.pregunta_por_area(estado)
            if seleccion_area:
                pregunta_elegida, intent_elegido = seleccion_area
                opciones_preg = []
                candidatas_traza = []
                descartadas_traza = []
                estado.registrar_pregunta(
                    intent=intent_elegido,
                    texto=pregunta_elegida,
                    incrementar_repregunta=False,
                )
                decision = "PREGUNTAR"
                motivo_decision = "Señal técnica explícita: solicitando una medición de la misma categoría"
                respuesta_texto = pregunta_elegida
                es_pregunta = True
            else:
                from src.core.diagnostico.enrutador_sistema import detectar_areas_tecnicas

                areas_explicitas = detectar_areas_tecnicas(" ".join(estado.historial_mensajes_usuario))
                if areas_explicitas:
                    if medicion_area_pendiente:
                        if "ADMISION_MAP" in areas_explicitas:
                            respuesta_texto = (
                                "Queda pendiente la medición del MAP. Cuando tengas el valor "
                                "de presión MAP en kPa, con la condición del motor, envíalo para continuar. "
                                "La carga calculada (%) y el flujo MAF (g/s) son datos distintos. Sin esa lectura "
                                "no confirmaré una causa."
                            )
                            motivo_decision = "Lectura MAP ausente: mantener el caso pendiente sin confirmar causa"
                        else:
                            respuesta_texto = (
                                "La mezcla sigue pendiente de una medición objetiva: envía el DTC exacto "
                                "o los valores STFT/LTFT cuando los tengas. No confirmaré una causa sin ese dato."
                            )
                            motivo_decision = "Evidencia de mezcla insuficiente: mantener el caso pendiente"
                        decision = "PENDIENTE_MEDICION"
                        es_pregunta = False
                        seleccion = None
                    else:
                    # Si ya se pidió la medición del área, no sustituirla por
                    # preguntas genéricas de temperatura/frenado; avanzar con
                    # abstención ML y apoyo RAG/LLM dentro de la categoría.
                        es_suficiente = True
                        motivo_suficiencia = (
                            "El caso ya tiene una categoría técnica explícita; evitando una repregunta ajena"
                        )
                        seleccion = None
                else:
                    seleccion = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
            if seleccion_area:
                pass
            elif seleccion:
                txt_preg, opciones_preg, intent_preg, candidatas_traza, descartadas_traza = seleccion
                estado.registrar_pregunta(
                    intent=intent_preg,
                    texto=txt_preg,
                    opciones=opciones_preg,
                )
                decision = "PREGUNTAR"
                motivo_decision = f"Información insuficiente ({score}/3 categorías). Aclarando {intent_preg.value}"
                respuesta_texto = txt_preg
                es_pregunta = True
                intent_elegido = intent_preg.value
                pregunta_elegida = txt_preg

        # Caso B y C: Diagnóstico ML (por límite de repreguntas alcanzado o información suficiente)
        if not respuesta_texto:
            es_caso_b = not es_suficiente and estado.turnos_repregunta >= estado.max_repreguntas and not falla_forzada_alternativa
            falla_diag = None if es_caso_b else falla_forzada_alternativa

            session_manager = getattr(gestor_diagnostico, "session_manager", None)
            if session_manager is not None:
                session_manager.cargar_contexto(
                    session_id,
                    {"conversation_state": estado.exportar_dict(), "case_id": estado.case_id}
                )
            dto_resultado = gestor_diagnostico.procesar_consulta_texto(
                texto_usuario=consulta_consolidada,
                placa=estado.placa or "WAPP-01",
                marca_modelo=f"{estado.marca or 'Vehiculo'} {estado.modelo or 'Generico'}",
                session_id=session_id,
                remitente=remitente,
                proveedor=proveedor,
                taller_id=taller_id,
                usuario_id=usuario_id,
                conversacion_id=conversacion_id,
                diagnostico_forzado=falla_diag,
                orquestado=True,
                diferir_encolado_persistente=diferir_encolado_persistente,
                case_id=estado.case_id,
            )
            top3_ml_raw = None
            if getattr(dto_resultado, "predicciones_ml", None):
                top3_ml_raw = [
                    {
                        "falla": getattr(p, "falla", None) or (p.get("falla") if isinstance(p, dict) else str(p)),
                        "probabilidad": getattr(p, "probabilidad", 0.0) if hasattr(p, "probabilidad") else (p.get("probabilidad", 0.0) if isinstance(p, dict) else 0.0),
                        "origen_probabilidad": (
                            getattr(p, "origen_probabilidad", "SVM")
                            if hasattr(p, "origen_probabilidad")
                            else (p.get("origen_probabilidad", "SVM") if isinstance(p, dict) else "SVM")
                        ),
                    }
                    for p in dto_resultado.predicciones_ml[:3]
                ]
            elif dto_resultado.diagnostico_ml and dto_resultado.confianza_ml > 0:
                top3_ml_raw = [{
                    "falla": dto_resultado.diagnostico_ml,
                    "probabilidad": dto_resultado.confianza_ml,
                    "origen_probabilidad": getattr(dto_resultado, "origen_confianza", "SVM"),
                }]

            from src.core.conversacion.validador_compatibilidad import (
                ValidadorCompatibilidad,
                hipotesis_rechazada_en_texto,
            )
            hipotesis_final_presentada, exclusiones_compat = ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
                predicciones_raw=top3_ml_raw or [],
                estado=estado,
                nueva_evidencia=texto_limpio if hechos_extraidos else None,
            )

            tiene_descartada_en_top3 = any(
                hipotesis_rechazada_en_texto(
                    str(h.get("falla", "")), estado.hipotesis_descartadas,
                )
                for h in estado.top3_actual
            )
            if not (es_evidencia_duplicada and estado.top3_actual and not tiene_descartada_en_top3):
                estado.top3_actual = hipotesis_final_presentada
                if hipotesis_final_presentada:
                    estado.falla_principal = hipotesis_final_presentada[0]["falla"]
                    estado.confianza_actual = hipotesis_final_presentada[0]["probabilidad"]
                else:
                    estado.falla_principal = None
                    estado.confianza_actual = 0.0

            from src.core.conversacion.formateador_compacto import FormateadorCompacto
            hipotesis_formatear = estado.top3_actual
            preg_ctx, intent_ctx = (FormateadorCompacto.obtener_pregunta_contextual(
                top1_falla_o_hipotesis=hipotesis_formatear,
                sintoma_original=texto_limpio,
                estado=estado,
            ) if hipotesis_formatear else (None, None))
            if preg_ctx and estado.ya_preguntado_texto(preg_ctx):
                preg_ctx = None
                intent_ctx = None
            elif preg_ctx:
                estado.registrar_pregunta(
                    intent=intent_ctx or QuestionIntent.SINTOMA_BASE,
                    texto=preg_ctx,
                    incrementar_repregunta=False,
                )
            scores_pres = FormateadorCompacto.calcular_scores_presentacion(hipotesis_formatear)
            respuesta_texto = FormateadorCompacto.formatear_respuesta_diagnostico(
                top_hipotesis=hipotesis_formatear,
                sintoma_original=texto_limpio,
                contexto_rag=getattr(dto_resultado, "contexto_manual_verificado", "") or "",
                pregunta_personalizada=preg_ctx,
                estado=estado,
            )
            respuesta_texto = FormateadorCompacto.integrar_respuesta_llm(
                respuesta_llm=getattr(dto_resultado, "respuesta_texto", ""),
                respuesta_determinista=respuesta_texto,
                llm_usado=getattr(dto_resultado, "llm_usado", False) is True,
                respuesta_limitada=getattr(dto_resultado, "respuesta_limitada", False) is True,
                hipotesis_rechazadas=estado.hipotesis_descartadas,
            )
            hallazgo_inyectores = estado.obtener_hecho("caudal_inyectores_reportado")
            if hallazgo_inyectores and not (
                estado.top3_actual and "inyector" in estado.top3_actual[0].get("falla", "").lower()
            ):
                respuesta_texto = (
                    "Tomo como hallazgo reportado que los inyectores no entregan caudal suficiente; "
                    "todavía no lo doy por confirmado. Prioricemos una prueba de balance/caudal de "
                    "inyectores y la presión/alimentación de combustible. ¿Tienes el resultado de "
                    "alguna de esas comprobaciones?"
                )
                decision = "PREGUNTAR"
                motivo_decision = "Hallazgo explícito de inyectores priorizado ante salida ML no pertinente"
                estado.registrar_pregunta(
                    intent=QuestionIntent.MEDICION_TECNICA,
                    texto=respuesta_texto,
                    incrementar_repregunta=False,
                )
                pregunta_elegida = respuesta_texto
                intent_elegido = QuestionIntent.MEDICION_TECNICA.value
                es_pregunta = True
                # La revisión solicita resultados del hallazgo mostrado, no
                # valida el Top-1 ML (que se conserva intacto en dto/traza RAW).
                estado.registrar_hecho(
                    "hipotesis_en_evaluacion", "Caudal insuficiente de inyectores (hallazgo reportado)",
                    categoria="flujo", texto_crudo=hallazgo_inyectores.texto_crudo,
                    tipo=FactType.CONDICION,
                )
                estado.top3_actual = []
                estado.falla_principal = "Caudal insuficiente de inyectores (hallazgo reportado)"
                estado.confianza_actual = 0.0
                preg_ctx = respuesta_texto
                intent_ctx = QuestionIntent.MEDICION_TECNICA
                hipotesis_formatear = []
            if es_caso_b:
                decision = "DIFERENCIAL"
                motivo_decision = (
                    f"Límite de {settings.diagnostic.max_clarifications} repreguntas alcanzado: "
                    "forzando diagnóstico diferencial"
                )
            else:
                decision = "DIAGNOSTICAR"
                motivo_decision = f"Diagnóstico completado con {score} categorías y certidumbre {int(dto_resultado.confianza_ml*100)}%"

            if preg_ctx and intent_ctx and not es_caso_b:
                estado.registrar_pregunta(
                    intent=intent_ctx,
                    texto=preg_ctx,
                    opciones=[],
                    hipotesis=[h.get("falla", "") for h in hipotesis_formatear],
                    incrementar_repregunta=False,
                )
                pregunta_elegida = preg_ctx
                intent_elegido = intent_ctx.value
                es_pregunta = True

        # 8. Transición formal en la máquina de estados
        from src.core.conversacion.avance_preguntas import asegurar_pregunta_util

        respuesta_texto, pregunta_final_real = asegurar_pregunta_util(
            estado, respuesta_texto, contexto_previo.get("preguntas_realizadas", []),
            permitir_preguntas=decision != "DIFERENCIAL",
        )
        from src.core.conversacion.formateador_compacto import FormateadorCompacto

        categoria_respuesta = (
            interpretacion_corta.get("categoria_respuesta", "")
            if interpretacion_corta else ""
        )
        respuesta_sin_repetir = (
            respuesta_texto
            if categoria_respuesta in ("DIAGNOSTICO_CONFIRMADO", "MEDICION_INCOMPLETA")
            else FormateadorCompacto.evitar_respuesta_repetida(
                respuesta_texto,
                estado,
                es_evidencia_duplicada,
                hechos_nuevos=hechos_extraidos,
            )
        )
        if respuesta_sin_repetir != respuesta_texto:
            respuesta_texto = respuesta_sin_repetir
            pregunta_final_real = None
            pregunta_elegida = None
            intent_elegido = None
            es_pregunta = False
            if decision in {"DIAGNOSTICAR", "DATOS_INSUFICIENTES"}:
                # La supresión de texto redundante es una decisión de formato;
                # no debe cambiar el resultado clínico/operacional del turno.
                pass
            elif es_evidencia_duplicada:
                decision = "SIN_EVIDENCIA_NUEVA"
                motivo_decision = "Se evita repetir el mismo resumen: no cambió la evidencia del caso"
            else:
                decision = "EVIDENCIA_REGISTRADA"
                motivo_decision = "Se registra el aporte nuevo sin repetir una orientación que no cambió"
            estado.preguntas_realizadas = [
                pregunta for pregunta in estado.preguntas_realizadas
                if pregunta.get("turno") != estado.turno_actual
            ]
        preguntas_unicas = []
        claves_preguntas = set()
        for pregunta_registrada in estado.preguntas_realizadas:
            clave = " ".join(str(pregunta_registrada.get("texto", "")).casefold().split())
            if clave and clave not in claves_preguntas:
                claves_preguntas.add(clave)
                preguntas_unicas.append(pregunta_registrada)
        estado.preguntas_realizadas = preguntas_unicas
        if (
            aclaraciones_previas >= estado.max_repreguntas
            or aclaraciones_emitidas(estado) > estado.max_repreguntas
            or (
                forzar_avance and dato_desconocido(texto_limpio)
                and decision != "PLAN_B"
            )
        ):
            # El límite cuenta preguntas realmente mostradas. No persistir
            # preguntas creadas internamente en este turno pero no enviadas.
            respuesta_texto = re.sub(r"¿[^?]*\?", "", respuesta_texto).strip()
            if not respuesta_texto:
                respuesta_texto = (
                    "Con los datos disponibles no confirmo una causa. Conservo el caso y "
                    "sus descartes; aporta una medición nueva cuando la tengas o solicita "
                    "revisión presencial."
                )
            estado.preguntas_realizadas = [
                p for p in estado.preguntas_realizadas
                if p.get("turno") != estado.turno_actual
            ]
            pregunta_final_real = None
            pregunta_elegida = None
            es_pregunta = False
        if pregunta_final_real:
            pregunta_elegida = pregunta_final_real
            es_pregunta = True
        elif not re.search(r"¿[^?]*\?", respuesta_texto):
            es_pregunta = False
            pregunta_elegida = None
        if getattr(estado, "turno_ultima_correccion", None) == estado.turno_actual:
            if getattr(estado, "last_user_correction", None) in ("marca", "modelo"):
                veh_actualizado = f"{estado.marca or ''} {estado.modelo or ''} {estado.anio or ''}".strip()
                if veh_actualizado and veh_actualizado not in respuesta_texto:
                    respuesta_texto = (
                        f"Entendido maestro, actualicé el vehículo a *{veh_actualizado}*. Conservo las mediciones y síntomas reportados.\n\n"
                        f"{respuesta_texto}"
                    )
            elif estado.last_user_correction == texto_limpio:
                sintomas_corregidos = [
                    str(hecho.get("valor", "")).strip()
                    for hecho in hechos_extraidos
                    if hecho.get("categoria") == "sintoma" and hecho.get("valor")
                ]
                if sintomas_corregidos:
                    resumen_correccion = ", ".join(dict.fromkeys(sintomas_corregidos))
                    respuesta_texto = (
                        f"Entendido, actualicé el síntoma a: {resumen_correccion}. "
                        f"{respuesta_texto}"
                    )
        if sev_seguridad == SeveridadSeguridad.CRITICAL_STOP and banner_seguridad and banner_seguridad.strip() not in respuesta_texto:
            respuesta_texto = f"{banner_seguridad}{respuesta_texto}"
        MaquinaEstadosConversacion.transicionar(
            estado=estado,
            es_reinicio=False,
            nueva_evidencia=len(hechos_extraidos) > 0,
        )

        # 9. Registro de trazabilidad del turno
        traza = TurnTrace(
            turno=estado.turno_actual, mensaje_original=texto_limpio, contexto_previo=contexto_previo,
            hechos_nuevos_extraidos=hechos_extraidos,
            hechos_actualizados=[h.to_dict() for h in estado.hechos.values() if h.estado == FactState.CONFIRMADO],
            consulta_consolidada=consulta_consolidada, top3=estado.top3_actual, confianza=estado.confianza_actual,
            origen_confianza=(
                str((estado.top3_actual or [{}])[0].get("origen_probabilidad", "NO_REGISTRADO"))
            ),
            decision=decision, motivo_decision=motivo_decision, respuesta_enviada=respuesta_texto,
            estado_operativo=estado.estado_operativo.value, question_intent=intent_elegido,
            preguntas_candidatas=candidatas_traza, preguntas_descartadas=descartadas_traza,
            pregunta_final=pregunta_elegida, top3_ml_raw=locals().get("top3_ml_raw"),
            hipotesis_rechazadas_usuario=list(estado.hipotesis_descartadas),
            nueva_evidencia=texto_limpio if hechos_extraidos else None,
            hipotesis_final_presentada=locals().get("hipotesis_final_presentada"),
            exclusiones_compatibilidad=locals().get("exclusiones_compat", []),
            scores_presentacion=locals().get("scores_pres"),
            estado_previo=transicion.estado_previo.value if "transicion" in locals() else None,
            estado_detectado_mensaje_actual=transicion.estado_detectado_mensaje.value if "transicion" in locals() else None,
            decision_transicion=transicion.decision.value if "transicion" in locals() else None,
            motivo_transicion=transicion.motivo if "transicion" in locals() else None,
            dominio_previo=transicion.dominio_previo.value if "transicion" in locals() else None,
            dominio_detectado_actual=(
                transicion.dominio_detectado_mensaje.value if "transicion" in locals() else None
            ),
            dominio_actual=estado.dominio_probable,
            plan_b_activado=intent_elegido if decision == "PLAN_B" else None,
            herramientas_bloqueadas=list(estado.herramientas_no_disponibles),
            version_orquestador=ORCHESTRATOR_VERSION,
            tipo_mensaje=tipo_mensaje,
        )
        estado.trazabilidad.append(traza.to_dict())
        if len(estado.trazabilidad) > 15:
            estado.trazabilidad = estado.trazabilidad[-15:]

        # 10. Persistir estado conversacional acumulativo
        if diferir_encolado_persistente and hasattr(self.repositorio, "_fallback"):
            await self.repositorio._fallback.save_session(session_id, estado)
        else:
            await self.repositorio.save_session(session_id, estado)

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        logger.info(
            f"[ConversacionTurno] Sesión {session_id} Turno {estado.turno_actual} -> Decisión: {decision} ({elapsed_ms}ms)"
        )

        # Enriquecer respuesta con políticas críticas de seguridad física y mecánica
        from src.core.diagnostico.politica_seguridad import PoliticaSeguridad
        contexto_seg = f"{texto_usuario} {estado.combustible or ''} {estado.marca or ''} {estado.modelo or ''}"
        respuesta_texto = PoliticaSeguridad.enriquecer_respuesta_seguridad(
            respuesta_texto,
            contexto_seg,
            diagnostico_ml=getattr(dto_resultado, "diagnostico_ml", ""),
            estado=estado,
        )

        from src.core.conversacion.presentacion_dto import alinear_predicciones_presentadas
        dto_resultado = alinear_predicciones_presentadas(dto_resultado, estado.top3_actual)

        return {
            "status": "completado",
            "respuesta_texto": respuesta_texto,
            "diagnostico_ml": getattr(dto_resultado, "diagnostico_ml", "Aclaración técnica"),
            "confianza_ml": getattr(dto_resultado, "confianza_ml", 0.0),
            "top3_actual": estado.top3_actual,
            "scores_presentacion": traza.scores_presentacion,
            "fase": estado.fase.value,
            "es_pregunta": es_pregunta,
            "decision": decision,
            "motivo_decision": motivo_decision,
            "consulta_consolidada": consulta_consolidada,
            "tiempo_ms": elapsed_ms,
            "dto": dto_resultado,
            "estado": estado,
            "estado_operativo": estado.estado_operativo.value,
            "question_intent": intent_elegido,
            "preguntas_candidatas": candidatas_traza,
            "preguntas_descartadas": descartadas_traza,
            "pregunta_final": pregunta_elegida,
            "version_orquestador": traza.version_orquestador,
            "top3_ml_raw": traza.top3_ml_raw,
            "hipotesis_rechazadas_usuario": traza.hipotesis_rechazadas_usuario,
            "nueva_evidencia": traza.nueva_evidencia,
            "hipotesis_final_presentada": traza.hipotesis_final_presentada,
            "exclusiones_compatibilidad": traza.exclusiones_compatibilidad,
            "estado_previo": traza.estado_previo,
            "estado_detectado_mensaje_actual": traza.estado_detectado_mensaje_actual,
            "decision_transicion": traza.decision_transicion,
            "motivo_transicion": traza.motivo_transicion,
            "dominio_previo": traza.dominio_previo,
            "dominio_detectado_actual": traza.dominio_detectado_actual,
            "dominio_actual": traza.dominio_actual,
        }

    procesar_mensaje = procesar_turno
