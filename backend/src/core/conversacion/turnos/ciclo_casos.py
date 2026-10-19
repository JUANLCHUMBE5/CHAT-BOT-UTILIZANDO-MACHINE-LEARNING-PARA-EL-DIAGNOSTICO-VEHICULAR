"""Etapa ciclo casos; contexto por turno."""

from __future__ import annotations

import re
import time
import uuid

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationPhase, FactState, FactType, TurnTrace
from src.core.version import ORCHESTRATOR_VERSION


async def ciclo_casos(self, turno):
    turno.solicitud_caso = ExtractorHechos.clasificar_solicitud_caso(turno.texto_limpio)
    if turno.solicitud_caso and turno.solicitud_caso.get("accion") == "reanudar":
        turno.case_id_objetivo = turno.solicitud_caso.get("case_id")
        if not turno.case_id_objetivo and turno.solicitud_caso.get("caso_anterior"):
            turno.case_id_objetivo = next(
                (
                    caso.get("case_id")
                    for caso in reversed(turno.estado.hechos_historicos)
                    if caso.get("case_id") and caso.get("case_id") != turno.estado.case_id
                ),
                None,
            )
        if turno.case_id_objetivo and turno.estado.restaurar_caso_archivado(str(turno.case_id_objetivo)):
            await self.repositorio.save_session(turno.session_id, turno.estado)
            turno.session_manager = getattr(turno.gestor_diagnostico, "session_manager", None)
            if turno.session_manager is not None:
                turno.session_manager.cargar_contexto(
                    turno.session_id,
                    {"case_id": turno.estado.case_id, "conversation_state": turno.estado.exportar_dict()},
                )
            return {
                "status": "caso_reanudado",
                "respuesta_texto": "Retomé exclusivamente el caso anterior solicitado. Su contexto queda aislado del caso que acabamos de cerrar.",
                "diagnostico_ml": "Caso anterior reanudado",
                "confianza_ml": turno.estado.confianza_actual,
                "fase": turno.estado.fase.value,
                "es_pregunta": False,
                "decision": "REANUDAR_CASO",
                "case_id": turno.estado.case_id,
                "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
                "estado": turno.estado,
            }
        return {
            "status": "reanudar_no_encontrado",
            "respuesta_texto": "No encontré ese caso en el historial de esta conversación. Indica el case_id o solicita retomar el caso anterior disponible. No cambié el caso activo.",
            "diagnostico_ml": "Caso histórico no encontrado",
            "confianza_ml": 0.0,
            "fase": turno.estado.fase.value,
            "es_pregunta": True,
            "decision": "ACLARAR_REANUDACION",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if turno.solicitud_caso and turno.solicitud_caso.get("accion") in ("nuevo_caso", "cancelar"):
        es_frase_reinicio_pura = bool(
            re.fullmatch(
                r"\s*(?:otro\s+(?:carro|auto|veh[ií]culo)|nuevo\s+caso|nuevo\s+diagn[oó]stico|empecemos\s+con\s+otro|empezar\s+de\s+nuevo|cancelar(?:\s+caso)?|reiniciar)\s*[!.]*\s*",
                turno.texto_limpio,
                re.IGNORECASE,
            )
        )
        if not es_frase_reinicio_pura and (
            ExtractorHechos.contiene_informacion_diagnostica(turno.texto_limpio)
            or any(
                (
                    w in turno.texto_limpio.lower()
                    for w in (
                        "ahora tengo",
                        "placa",
                        "falla",
                        "suena",
                        "vibra",
                    )
                )
            )
        ):
            turno.estado.iniciar_nuevo_caso(str(uuid.uuid4()), preservar_vehiculo=False)
            await self.repositorio.save_session(turno.session_id, turno.estado)
            turno.session_manager = getattr(turno.gestor_diagnostico, "session_manager", None)
            if turno.session_manager is not None:
                turno.session_manager.cargar_contexto(
                    turno.session_id,
                    {"case_id": turno.estado.case_id, "conversation_state": turno.estado.exportar_dict()},
                )
        else:
            turno.es_cancelacion = turno.solicitud_caso["accion"] == "cancelar"
            turno.preservar_vehiculo = bool(
                turno.solicitud_caso.get("preservar_vehiculo")
                and any((turno.estado.placa, turno.estado.marca, turno.estado.modelo))
            )
            turno.estado.iniciar_nuevo_caso(
                None if turno.es_cancelacion else str(uuid.uuid4()),
                preservar_vehiculo=turno.preservar_vehiculo,
            )
            if turno.es_cancelacion:
                turno.estado.case_id = None
                turno.estado.active_problem_id = None
            await self.repositorio.save_session(turno.session_id, turno.estado)
            turno.session_manager = getattr(turno.gestor_diagnostico, "session_manager", None)
            if turno.session_manager is not None:
                turno.session_manager.cargar_contexto(
                    turno.session_id,
                    {"case_id": turno.estado.case_id, "conversation_state": turno.estado.exportar_dict()},
                )
            if turno.es_cancelacion:
                turno.resp_reinicio = "🚗 *Caso cancelado.* Conservé su historial y limpié el contexto activo. Cuando quieras, envía la placa del siguiente vehículo."
            else:
                turno.resp_reinicio = "🚗 *Caso anterior cerrado.* Conservé su historial y limpié la memoria activa. Envía la placa y el síntoma para iniciar un caso nuevo."
                if turno.preservar_vehiculo and turno.estado.placa:
                    turno.resp_reinicio = "🚗 *Caso anterior cerrado.* Conservé el historial y mantengo únicamente los datos confirmados del mismo vehículo. Indica el nuevo síntoma."
            return {
                "status": "reinicio",
                "respuesta_texto": turno.resp_reinicio,
                "diagnostico_ml": "Reinicio de sesión",
                "confianza_ml": 0.0,
                "fase": ConversationPhase.INICIO.value,
                "es_pregunta": False,
                "decision": "REINICIO",
                "case_id": turno.estado.case_id,
                "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
                "estado": turno.estado,
            }
    turno.PATRON_CIERRE = re.compile(
        r"^\s*(?:(?:muchas\s+)?gracias(?:\s+maestro|\s+amigo)?(?:\s+por\s+.*)?|perfecto,?\s*(?:qued[oó]\s+clar[ií]simo|gracias.*)?|excelente\s+(?:servicio|explicaci[oón]|ayuda)(?:\s+maestro)?|qued[oó]\s+clar[ií]simo)\s*[!.]*\s*$",
        re.IGNORECASE,
    )
    if turno.PATRON_CIERRE.match(turno.texto_limpio.strip()):
        if any(
            (
                w in turno.texto_limpio.lower()
                for w in (
                    "embalamiento",
                    "seguridad",
                    "riesgo",
                    "peligro",
                    "diesel",
                    "diésel",
                    "cárter",
                    "carter",
                )
            )
        ):
            turno.resp_cierre = "🤝 *¡De nada maestro! Recuerda mantener el motor detenido y drenar completamente el cárter contaminado antes de cualquier intento de arranque para evitar el peligro crítico de embalamiento diésel. Quedo a tu disposición en el taller para cualquier otra consulta técnica o nuevo caso vehicular. ¡Muchos éxitos!*"
        else:
            turno.resp_cierre = "🤝 *¡De nada maestro! Quedo a tu disposición en el taller para cualquier otra consulta técnica, medición o nuevo caso vehicular. ¡Muchos éxitos en la reparación!*"
        if turno.texto_limpio not in turno.estado.historial_mensajes_usuario:
            turno.estado.historial_mensajes_usuario.append(turno.texto_limpio)
        turno.estado.turno_actual += 1
        return {
            "status": "cierre",
            "respuesta_texto": turno.resp_cierre,
            "diagnostico_ml": turno.estado.falla_principal or "Caso concluido",
            "confianza_ml": turno.estado.confianza_actual,
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "CIERRE",
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    turno.es_caso_freno = bool(
        getattr(turno.estado, "sistema_sospechoso", "") == "frenos"
        or any(("freno" in str(s).lower() for s in getattr(turno.estado, "active_symptoms", []) or []))
        or any(
            (
                "freno" in m.lower()
                and any((w in m.lower() for w in ("piso", "fondo", "liquido", "líquido", "rueda")))
                for m in turno.estado.historial_mensajes_usuario
            )
        )
    )
    if turno.es_caso_freno and re.search(
        r"\b(?:sacar(?:lo)?\s+a\s+(?:probar\s+a\s+)?(?:la\s+)?pista|probar\s+(?:en\s+|a\s+la\s+)?pista|circular|rodar\s+en\s+calle|manejar\s+as[ií])\b",
        turno.texto_limpio.casefold(),
    ):
        if turno.texto_limpio not in turno.estado.historial_mensajes_usuario:
            turno.estado.historial_mensajes_usuario.append(turno.texto_limpio)
        turno.estado.turno_actual += 1
        turno.resp_freno_persiste = "🛑 *RATIFICACIÓN CRÍTICA DE SEGURIDAD VIAL: PROHIBIDO CIRCULAR O PROBAR EN PISTA*\n\n⚠️ **ADVERTENCIA:** Con el pedal de freno yéndose al piso y fuga de líquido por la rueda, el vehículo se encuentra **totalmente inoperable y sin capacidad de detención segura**.\n\n🚫 **PROHIBICIÓN ESTRICTA:** Es correcto y obligatorio NO sacarlo a la pista ni intentar pruebas de ruta. Sacarlo a rodar representa un riesgo inminente de colisión catastrófica.\n\n🔧 **ACCIÓN REQUERIDA:** La inspección y purga debe realizarse exclusivamente en el taller sobre elevador o caballetes, revisando cilindro de rueda, calipers, mangueras flexibles y bomba principal."
        return {
            "status": "seguridad_critica",
            "respuesta_texto": turno.resp_freno_persiste,
            "diagnostico_ml": "Pérdida crítica de frenos - Prohibición de circular",
            "confianza_ml": 1.0,
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "SEGURIDAD_CRITICA",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    turno.norm_txt_cons = turno.texto_limpio.casefold()
    turno.es_consulta_prerrequisitos_dpf = bool(
        re.search(
            r"\b(?:qu[eé]\s+(?:debo|se\s+debe|hay\s+que|tengo\s+que)\s+(?:verificar|revisar|comprobar|chequear|tener)|prerrequisitos?|condiciones\s+previas|requisitos?|condiciones)\b.{0,50}\b(?:antes\s+de\s+regenerar|regeneraci[oó]n|regenerar|listas)\b|\b(?:antes\s+de\s+regenerar|para\s+regenerar|regenerar\s+el\s+dpf)\b.{0,40}\b(?:qu[eé]\s+(?:verifico|reviso|compruebo|chequeo|condiciones)|prerrequisitos?|condiciones)\b",
            turno.norm_txt_cons,
        )
        or (
            re.search(
                r"\b(?:ya\s+correg[ií]|ya\s+cambi[eé]|dren[eé]|bot[eé]|aceite\s+nuevo)\b",
                turno.norm_txt_cons,
            )
            and re.search(r"\b(?:regenerar|regeneraci[oó]n)\b", turno.norm_txt_cons)
        )
    )
    if turno.es_consulta_prerrequisitos_dpf and (
        not turno.PoliticaSeguridad._hay_dilucion_aceite_activa(turno.texto_limpio, turno.estado)
    ):
        ExtractorHechos.extraer_y_actualizar(turno.estado, turno.texto_limpio)
        if turno.texto_limpio not in turno.estado.historial_mensajes_usuario:
            turno.estado.historial_mensajes_usuario.append(turno.texto_limpio)
        if turno.texto_limpio not in turno.estado.active_symptoms:
            turno.estado.active_symptoms.append(turno.texto_limpio)
        turno.estado.registrar_hecho(
            "prerrequisitos_dpf_consultados",
            "SI",
            categoria="seguridad",
            texto_crudo=turno.texto_limpio,
            tipo=FactType.CONDICION,
        )
        turno.resp_prerreq = turno.PoliticaSeguridad.PRERREQUISITOS_REGENERACION_DPF_OEM
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
            origen_confianza="PRERREQUISITOS_OEM",
            decision="PRERREQUISITOS_OEM",
            motivo_decision="Consulta técnica de prerrequisitos OEM para regeneración de DPF",
            respuesta_enviada=turno.resp_prerreq,
            estado_operativo=turno.estado.estado_operativo.value,
            question_intent=None,
            preguntas_candidatas=[],
            preguntas_descartadas=[],
            pregunta_final=None,
            hipotesis_rechazadas_usuario=list(turno.estado.hipotesis_descartadas),
            version_orquestador=ORCHESTRATOR_VERSION,
            tipo_mensaje="prerrequisitos_dpf",
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
            "status": "prerrequisitos_dpf",
            "respuesta_texto": turno.resp_prerreq,
            "diagnostico_ml": turno.estado.falla_principal or "Prerrequisitos OEM DPF",
            "confianza_ml": turno.estado.confianza_actual,
            "top3_actual": turno.estado.top3_actual,
            "scores_presentacion": {},
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "PRERREQUISITOS_OEM",
            "motivo_decision": "Consulta técnica de prerrequisitos OEM para regeneración de DPF",
            "pregunta_final": None,
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
