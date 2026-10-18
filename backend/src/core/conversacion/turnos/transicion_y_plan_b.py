"""Etapa transicion y plan b; contexto por turno."""

from __future__ import annotations

import time
from importlib import import_module as _importar

from src.core.conversacion.clasificador_mensajes import clasificar_mensaje
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas
from src.core.conversacion.models import FactState, FactType, QuestionIntent, TurnTrace
from src.core.version import ORCHESTRATOR_VERSION


async def transicion_y_plan_b(self, turno):
    turno.SegmentadorCasos = _importar("src.core.conversacion.segmentador_casos").SegmentadorCasos
    turno.tipo_mensaje = clasificar_mensaje(turno.texto_limpio, turno.estado)
    turno.ret_trans, turno.transicion = turno.SegmentadorCasos.resolver_transicion_turno(
        estado=turno.estado,
        texto_limpio=turno.texto_limpio,
        gestor_diagnostico=turno.gestor_diagnostico,
        session_id=turno.session_id,
        t0=turno.t0,
        contexto_previo=turno.contexto_previo,
        tipo_mensaje=turno.tipo_mensaje,
    )
    if turno.ret_trans is not None:
        await self.repositorio.save_session(turno.session_id, turno.estado)
        return turno.ret_trans
    if turno.transicion.dominio_detectado_mensaje.value != "DESCONOCIDO":
        turno.estado.dominio_probable = turno.transicion.dominio_detectado_mensaje.value
    if turno.transicion.decision.value == "CAMBIO_DE_CASO":
        turno.contexto_previo = turno.estado.exportar_dict(incluir_trazabilidad=False)
    turno.GestorPlanB = _importar("src.core.conversacion.gestor_plan_b").GestorPlanB
    turno.es_imposibilidad_completa = _importar(
        "src.core.conversacion.orientacion_provisional"
    ).es_imposibilidad_completa
    turno.generar_orientacion_provisional = _importar(
        "src.core.conversacion.orientacion_provisional"
    ).generar_orientacion_provisional
    turno.es_imposible_declarado = (
        (
            turno.tipo_mensaje == "imposibilidad_comprobacion"
            or turno.es_imposibilidad_completa(turno.texto_limpio)
        )
        and (not ExtractorHechos.contiene_informacion_diagnostica(turno.texto_limpio))
        and (not turno.GestorPlanB.detectar_indisponibilidad_en_texto(turno.texto_limpio))
    )
    if turno.es_imposible_declarado:
        if turno.texto_limpio not in turno.estado.historial_mensajes_usuario:
            turno.estado.historial_mensajes_usuario.append(turno.texto_limpio)
        turno.estado.registrar_hecho(
            "comprobacion_fisica_imposible",
            "SI",
            categoria="flujo",
            texto_crudo=turno.texto_limpio,
            tipo=FactType.CONDICION,
        )
        turno.ValidadorCompatibilidad = _importar(
            "src.core.conversacion.validador_compatibilidad"
        ).ValidadorCompatibilidad
        turno.exclusiones_compatibilidad = []
        if not turno.estado.top3_actual and turno.estado.active_symptoms:
            turno.sintomas_validos = [
                s for s in turno.estado.active_symptoms if not turno.es_imposibilidad_completa(s)
            ]
            turno.consulta_base = " ".join(turno.sintomas_validos)
            if turno.consulta_base:
                try:
                    turno.dto_tmp = turno.gestor_diagnostico.procesar_consulta_texto(
                        texto_usuario=turno.consulta_base,
                        placa=turno.estado.placa or "WAPP-01",
                        marca_modelo=f"{turno.estado.marca or 'Vehiculo'} {turno.estado.modelo or 'Generico'}",
                        session_id=turno.session_id,
                        orquestado=True,
                        diferir_encolado_persistente=True,
                        case_id=turno.estado.case_id,
                    )
                    if turno.dto_tmp and getattr(turno.dto_tmp, "predicciones_ml", None):
                        turno.predicciones_tmp = [
                            {
                                "falla": getattr(p, "falla", str(p)),
                                "probabilidad": getattr(p, "probabilidad", 0.5),
                            }
                            for p in turno.dto_tmp.predicciones_ml[:3]
                        ]
                        turno.estado.top3_actual, turno.exclusiones_compatibilidad = (
                            turno.ValidadorCompatibilidad.filtrar_hipotesis_almacenadas(
                                turno.predicciones_tmp, turno.estado
                            )
                        )
                        if turno.estado.top3_actual:
                            turno.estado.falla_principal = turno.estado.top3_actual[0]["falla"]
                            turno.estado.confianza_actual = turno.estado.top3_actual[0]["probabilidad"]
                except Exception:
                    pass
        turno.hipotesis_presentables, turno.excluidas_almacenadas = (
            turno.ValidadorCompatibilidad.filtrar_hipotesis_almacenadas(
                turno.estado.top3_actual, turno.estado
            )
        )
        turno.exclusiones_compatibilidad.extend(turno.excluidas_almacenadas)
        turno.estado.top3_actual = turno.hipotesis_presentables
        turno.estado.falla_principal = (
            turno.hipotesis_presentables[0]["falla"] if turno.hipotesis_presentables else None
        )
        turno.estado.confianza_actual = (
            float(turno.hipotesis_presentables[0].get("probabilidad", 0.0))
            if turno.hipotesis_presentables
            else 0.0
        )
        turno.resp_orientacion = turno.generar_orientacion_provisional(
            estado=turno.estado,
            hipotesis_disponibles=turno.estado.top3_actual,
            falla_principal=turno.estado.falla_principal,
        )
        turno.ResultadoDiagnostico = _importar("src.core.gestor_diagnostico").ResultadoDiagnostico
        turno.dto_orientacion = turno.ResultadoDiagnostico(
            respuesta_texto=turno.resp_orientacion,
            diagnostico_ml=turno.estado.falla_principal or "Orientación provisional",
            confianza_ml=turno.estado.confianza_actual,
            contexto_manual="",
            titulo_manual="",
            requiere_revision_humana=True,
            estado_sesion="en_revision",
            modo_diagnostico="orientacion_provisional",
            tipo_consulta="orientacion_provisional",
            es_orientacion_provisional=True,
        )
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
            origen_confianza="NO_REGISTRADO",
            decision="ORIENTACION_PROVISIONAL",
            motivo_decision="Imposibilidad de comprobación física declarada",
            respuesta_enviada=turno.resp_orientacion,
            estado_operativo=turno.estado.estado_operativo.value,
            question_intent=None,
            preguntas_candidatas=[],
            preguntas_descartadas=[],
            pregunta_final=None,
            hipotesis_rechazadas_usuario=list(turno.estado.hipotesis_descartadas),
            exclusiones_compatibilidad=turno.exclusiones_compatibilidad,
            version_orquestador=ORCHESTRATOR_VERSION,
            tipo_mensaje=turno.tipo_mensaje,
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
            "status": "orientacion_provisional",
            "respuesta_texto": turno.resp_orientacion,
            "diagnostico_ml": turno.estado.falla_principal or "Orientación provisional",
            "confianza_ml": turno.estado.confianza_actual,
            "top3_actual": turno.estado.top3_actual,
            "scores_presentacion": {},
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "ORIENTACION_PROVISIONAL",
            "motivo_decision": "Imposibilidad de comprobación física declarada",
            "pregunta_final": None,
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
            "dto": turno.dto_orientacion,
        }
    turno.falla_forzada_alternativa = turno.diagnostico_forzado
    turno.interpretacion_corta = None
    if InterpreteRespuestasCortas.es_respuesta_corta(turno.texto_limpio):
        turno.interpretacion_corta = InterpreteRespuestasCortas.interpretar(turno.estado, turno.texto_limpio)
    if turno.interpretacion_corta:
        turno.cat_resp = turno.interpretacion_corta.get(
            "categoria_respuesta", turno.interpretacion_corta.get("categoria", "")
        )
        turno.val_resp = turno.interpretacion_corta.get("valor", "")
        if turno.cat_resp == "REVISION_AMBIGUA":
            turno.msg_ambiguo = "¿Qué componente específico revisaste y cuál fue el resultado o medición obtenida? Detalla la comprobación realizada para orientar el diagnóstico sin descartes apresurados."
            turno.estado.registrar_pregunta(
                QuestionIntent.MEDICION_TECNICA,
                turno.msg_ambiguo,
                metadata={"case_id": turno.estado.case_id, "origen": "revision_ambigua"},
            )
            await self.repositorio.save_session(turno.session_id, turno.estado)
            return {
                "status": "completado",
                "respuesta_texto": turno.msg_ambiguo,
                "diagnostico_ml": turno.estado.falla_principal or "Revisión ambigua",
                "confianza_ml": turno.estado.confianza_actual,
                "top3_actual": turno.estado.top3_actual,
                "fase": turno.estado.fase.value,
                "es_pregunta": True,
                "decision": "PREGUNTAR",
                "pregunta_final": turno.msg_ambiguo,
                "case_id": turno.estado.case_id,
                "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
                "estado": turno.estado,
            }
        if turno.cat_resp == "OPCION_NUMERICA_FUERA_DE_RANGO":
            turno.total_opc = int(turno.interpretacion_corta.get("total_opciones", 0))
            turno.opc_pedida = turno.interpretacion_corta.get("indice_opcion", turno.val_resp)
            if turno.total_opc == 1:
                turno.hip_unica = (
                    turno.estado.top3_actual[0].get("falla", "")
                    if getattr(turno.estado, "top3_actual", None)
                    and isinstance(turno.estado.top3_actual[0], dict)
                    else turno.estado.falla_principal or "opción 1"
                )
                turno.msg_fuera_rango = f"La opción {turno.opc_pedida} no está disponible porque solo se presentó 1 opción activa ({turno.hip_unica}). Indica *1* si deseas seleccionar esa hipótesis para comprobarla, o describe el síntoma o comprobación realizada."
            else:
                turno.msg_fuera_rango = f"La opción {turno.opc_pedida} está fuera de rango (opciones disponibles: 1 a {turno.total_opc}). Indica un número entre *1* y *{turno.total_opc}* o describe la comprobación o síntoma."
            await self.repositorio.save_session(turno.session_id, turno.estado)
            return {
                "status": "completado",
                "respuesta_texto": turno.msg_fuera_rango,
                "diagnostico_ml": turno.estado.falla_principal or "Opción fuera de rango",
                "confianza_ml": turno.estado.confianza_actual,
                "top3_actual": turno.estado.top3_actual,
                "fase": turno.estado.fase.value,
                "es_pregunta": True,
                "decision": "OPCION_NUMERICA_INVALIDA",
                "pregunta_final": turno.msg_fuera_rango,
                "case_id": turno.estado.case_id,
                "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
                "estado": turno.estado,
            }
        turno.estado.registrar_respuesta(
            texto=turno.texto_limpio, interpretacion=f"{turno.cat_resp}:{turno.val_resp}"
        )
        if turno.cat_resp == "OPCION_NUMERICA_PROVISIONAL":
            turno.hipotesis_elegida = str(turno.val_resp)
            turno.pregunta_comprobacion = f"Seleccionaste provisionalmente la opción {turno.interpretacion_corta['indice_opcion']} ({turno.hipotesis_elegida}). ¿Qué comprobación o medición objetiva has realizado para esa posibilidad y cuál fue el resultado? Si todavía no la revisaste, indícalo."
            turno.estado.registrar_pregunta(
                QuestionIntent.MEDICION_TECNICA,
                turno.pregunta_comprobacion,
                metadata={
                    "case_id": turno.estado.case_id,
                    "hipotesis_provisional": turno.hipotesis_elegida,
                    "origen_intent": turno.estado.preguntas_realizadas[-1]["intent"]
                    if turno.estado.preguntas_realizadas
                    else QuestionIntent.MEDICION_TECNICA.value,
                },
            )
            turno.estado.establecer_pregunta_pendiente(
                intent=QuestionIntent.MEDICION_TECNICA.value,
                texto=turno.pregunta_comprobacion,
                related_hypothesis=turno.hipotesis_elegida,
            )
            turno.estado.pending_question["case_id"] = turno.estado.case_id
            turno.estado.falla_principal = turno.hipotesis_elegida
            await self.repositorio.save_session(turno.session_id, turno.estado)
            return {
                "status": "completado",
                "respuesta_texto": turno.pregunta_comprobacion,
                "diagnostico_ml": turno.estado.falla_principal or "Hipótesis por comprobar",
                "confianza_ml": turno.estado.confianza_actual,
                "top3_actual": turno.estado.top3_actual,
                "fase": turno.estado.fase.value,
                "es_pregunta": True,
                "decision": "COMPROBACION_HIPOTESIS_PROVISIONAL",
                "pregunta_final": turno.pregunta_comprobacion,
                "case_id": turno.estado.case_id,
                "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
                "estado": turno.estado,
            }
        if "diagnostico_forzado" in turno.interpretacion_corta:
            turno.falla_forzada_alternativa = turno.interpretacion_corta["diagnostico_forzado"]
