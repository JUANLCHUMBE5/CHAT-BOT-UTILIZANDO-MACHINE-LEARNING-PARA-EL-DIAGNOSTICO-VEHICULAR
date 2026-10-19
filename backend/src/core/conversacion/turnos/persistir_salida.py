"""Etapa persistir salida; contexto por turno."""

from __future__ import annotations

import re
import time
from importlib import import_module as _importar

from src.core.conversacion.control_aclaraciones import aclaraciones_emitidas, dato_desconocido
from src.core.conversacion.maquina_estados import MaquinaEstadosConversacion
from src.core.conversacion.models import FactState, TurnTrace
from src.core.logger import logger
from src.core.version import ORCHESTRATOR_VERSION


async def persistir_salida(self, turno):
    turno.asegurar_pregunta_util = _importar("src.core.conversacion.avance_preguntas").asegurar_pregunta_util
    turno.respuesta_texto, turno.pregunta_final_real = turno.asegurar_pregunta_util(
        turno.estado,
        turno.respuesta_texto,
        turno.contexto_previo.get("preguntas_realizadas", []),
        permitir_preguntas=turno.decision != "DIFERENCIAL",
    )
    turno.FormateadorCompacto = _importar("src.core.conversacion.formateador_compacto").FormateadorCompacto
    turno.categoria_respuesta = (
        turno.interpretacion_corta.get("categoria_respuesta", "") if turno.interpretacion_corta else ""
    )
    turno.respuesta_sin_repetir = (
        turno.respuesta_texto
        if turno.categoria_respuesta in ("DIAGNOSTICO_CONFIRMADO", "MEDICION_INCOMPLETA")
        else turno.FormateadorCompacto.evitar_respuesta_repetida(
            turno.respuesta_texto,
            turno.estado,
            turno.es_evidencia_duplicada,
            hechos_nuevos=turno.hechos_extraidos,
        )
    )
    if turno.respuesta_sin_repetir != turno.respuesta_texto:
        turno.respuesta_texto = turno.respuesta_sin_repetir
        turno.pregunta_final_real = None
        turno.pregunta_elegida = None
        turno.intent_elegido = None
        turno.es_pregunta = False
        if turno.decision in {"DIAGNOSTICAR", "DATOS_INSUFICIENTES"}:
            pass
        elif turno.es_evidencia_duplicada:
            turno.decision = "SIN_EVIDENCIA_NUEVA"
            turno.motivo_decision = "Se evita repetir el mismo resumen: no cambió la evidencia del caso"
        else:
            turno.decision = "EVIDENCIA_REGISTRADA"
            turno.motivo_decision = "Se registra el aporte nuevo sin repetir una orientación que no cambió"
        turno.estado.preguntas_realizadas = [
            pregunta
            for pregunta in turno.estado.preguntas_realizadas
            if pregunta.get("turno") != turno.estado.turno_actual
        ]
    turno.preguntas_unicas = []
    turno.claves_preguntas = set()
    for turno.pregunta_registrada in turno.estado.preguntas_realizadas:
        turno.clave = " ".join(str(turno.pregunta_registrada.get("texto", "")).casefold().split())
        if turno.clave and turno.clave not in turno.claves_preguntas:
            turno.claves_preguntas.add(turno.clave)
            turno.preguntas_unicas.append(turno.pregunta_registrada)
    turno.estado.preguntas_realizadas = turno.preguntas_unicas
    if (
        turno.aclaraciones_previas >= turno.estado.max_repreguntas
        or aclaraciones_emitidas(turno.estado) > turno.estado.max_repreguntas
        or (turno.forzar_avance and dato_desconocido(turno.texto_limpio) and (turno.decision != "PLAN_B"))
    ):
        turno.respuesta_texto = re.sub("¿[^?]*\\?", "", turno.respuesta_texto).strip()
        if not turno.respuesta_texto:
            turno.respuesta_texto = "Con los datos disponibles no confirmo una causa. Conservo el caso y sus descartes; aporta una medición nueva cuando la tengas o solicita revisión presencial."
        turno.estado.preguntas_realizadas = [
            p for p in turno.estado.preguntas_realizadas if p.get("turno") != turno.estado.turno_actual
        ]
        turno.pregunta_final_real = None
        turno.pregunta_elegida = None
        turno.es_pregunta = False
    if turno.pregunta_final_real:
        turno.pregunta_elegida = turno.pregunta_final_real
        turno.es_pregunta = True
    elif not re.search("¿[^?]*\\?", turno.respuesta_texto):
        turno.es_pregunta = False
        turno.pregunta_elegida = None
    if getattr(turno.estado, "turno_ultima_correccion", None) == turno.estado.turno_actual:
        if getattr(turno.estado, "last_user_correction", None) in ("marca", "modelo", "anio"):
            turno.veh_actualizado = (
                f"{turno.estado.marca or ''} {turno.estado.modelo or ''} {turno.estado.anio or ''}".strip()
            )
            if turno.veh_actualizado and turno.veh_actualizado not in turno.respuesta_texto:
                turno.respuesta_texto = f"Entendido maestro, actualicé el vehículo a *{turno.veh_actualizado}*. Conservo las mediciones y síntomas reportados.\n\n{turno.respuesta_texto}"
        elif turno.estado.last_user_correction == turno.texto_limpio:
            turno.sintomas_corregidos = [
                str(hecho.get("valor", "")).strip()
                for hecho in turno.hechos_extraidos
                if hecho.get("categoria") == "sintoma" and hecho.get("valor")
            ]
            if turno.sintomas_corregidos:
                turno.resumen_correccion = ", ".join(dict.fromkeys(turno.sintomas_corregidos))
                turno.respuesta_texto = (
                    f"Entendido, actualicé el síntoma a: {turno.resumen_correccion}. {turno.respuesta_texto}"
                )
    if not getattr(turno.estado, "banner_vehiculo_mostrado", False) and not getattr(turno.estado, "turno_ultima_correccion", None):
        marca = getattr(turno.estado, "marca", None)
        modelo = getattr(turno.estado, "modelo", None)
        anio = getattr(turno.estado, "anio", None)
        if marca or modelo:
            turno.veh_inicial = f"{marca or ''} {modelo or ''} {anio or ''}".strip()
            if turno.veh_inicial and (turno.veh_inicial not in turno.respuesta_texto):
                turno.respuesta_texto = f"🚗 *Vehículo identificado: {turno.veh_inicial}*\n\n{turno.respuesta_texto}"
                turno.estado.banner_vehiculo_mostrado = True
    if (
        turno.sev_seguridad == turno.SeveridadSeguridad.CRITICAL_STOP
        and turno.banner_seguridad
        and (turno.banner_seguridad.strip() not in turno.respuesta_texto)
    ):
        turno.respuesta_texto = f"{turno.banner_seguridad}{turno.respuesta_texto}"
    MaquinaEstadosConversacion.transicionar(
        estado=turno.estado, es_reinicio=False, nueva_evidencia=len(turno.hechos_extraidos) > 0
    )
    turno.traza = TurnTrace(
        turno=turno.estado.turno_actual,
        mensaje_original=turno.texto_limpio,
        contexto_previo=turno.contexto_previo,
        hechos_nuevos_extraidos=turno.hechos_extraidos,
        hechos_actualizados=[
            h.to_dict() for h in turno.estado.hechos.values() if h.estado == FactState.CONFIRMADO
        ],
        consulta_consolidada=turno.consulta_consolidada,
        top3=turno.estado.top3_actual,
        confianza=turno.estado.confianza_actual,
        origen_confianza=str(
            (turno.estado.top3_actual or [{}])[0].get("origen_probabilidad", "NO_REGISTRADO")
        ),
        decision=turno.decision,
        motivo_decision=turno.motivo_decision,
        respuesta_enviada=turno.respuesta_texto,
        estado_operativo=turno.estado.estado_operativo.value,
        question_intent=turno.intent_elegido,
        preguntas_candidatas=turno.candidatas_traza,
        preguntas_descartadas=turno.descartadas_traza,
        pregunta_final=turno.pregunta_elegida,
        top3_ml_raw=getattr(turno, "top3_ml_raw", None),
        hipotesis_rechazadas_usuario=list(turno.estado.hipotesis_descartadas),
        nueva_evidencia=turno.texto_limpio if turno.hechos_extraidos else None,
        hipotesis_final_presentada=getattr(turno, "hipotesis_final_presentada", None),
        exclusiones_compatibilidad=getattr(turno, "exclusiones_compat", []),
        scores_presentacion=getattr(turno, "scores_pres", {}),
        estado_previo=turno.transicion.estado_previo.value if getattr(turno, "transicion", None) else None,
        estado_detectado_mensaje_actual=turno.transicion.estado_detectado_mensaje.value
        if getattr(turno, "transicion", None)
        else None,
        decision_transicion=turno.transicion.decision.value if getattr(turno, "transicion", None) else None,
        motivo_transicion=turno.transicion.motivo if getattr(turno, "transicion", None) else None,
        dominio_previo=turno.transicion.dominio_previo.value if getattr(turno, "transicion", None) else None,
        dominio_detectado_actual=turno.transicion.dominio_detectado_mensaje.value
        if getattr(turno, "transicion", None)
        else None,
        dominio_actual=turno.estado.dominio_probable,
        plan_b_activado=turno.intent_elegido if turno.decision == "PLAN_B" else None,
        herramientas_bloqueadas=list(turno.estado.herramientas_no_disponibles),
        version_orquestador=ORCHESTRATOR_VERSION,
        tipo_mensaje=turno.tipo_mensaje,
    )
    turno.estado.trazabilidad.append(turno.traza.to_dict())
    if len(turno.estado.trazabilidad) > 15:
        turno.estado.trazabilidad = turno.estado.trazabilidad[-15:]
    if turno.diferir_encolado_persistente and hasattr(self.repositorio, "_fallback"):
        await self.repositorio._fallback.save_session(turno.session_id, turno.estado)
    else:
        await self.repositorio.save_session(turno.session_id, turno.estado)
    turno.elapsed_ms = round((time.perf_counter() - turno.t0) * 1000, 2)
    logger.info(
        f"[ConversacionTurno] Sesión {turno.session_id} Turno {turno.estado.turno_actual} -> Decisión: {turno.decision} ({turno.elapsed_ms}ms)"
    )
    turno.PoliticaSeguridad = _importar("src.core.diagnostico.politica_seguridad").PoliticaSeguridad
    turno.contexto_seg = f"{turno.texto_usuario} {turno.estado.combustible or ''} {turno.estado.marca or ''} {turno.estado.modelo or ''}"
    turno.respuesta_texto = turno.PoliticaSeguridad.enriquecer_respuesta_seguridad(
        turno.respuesta_texto,
        turno.contexto_seg,
        diagnostico_ml=getattr(turno.dto_resultado, "diagnostico_ml", ""),
        estado=turno.estado,
    )
    turno.alinear_predicciones_presentadas = _importar(
        "src.core.conversacion.presentacion_dto"
    ).alinear_predicciones_presentadas
    turno.dto_resultado = turno.alinear_predicciones_presentadas(
        turno.dto_resultado, turno.estado.top3_actual
    )
    return {
        "status": "completado",
        "respuesta_texto": turno.respuesta_texto,
        "diagnostico_ml": getattr(turno.dto_resultado, "diagnostico_ml", "Aclaración técnica"),
        "confianza_ml": getattr(turno.dto_resultado, "confianza_ml", 0.0),
        "top3_actual": turno.estado.top3_actual,
        "scores_presentacion": turno.traza.scores_presentacion,
        "fase": turno.estado.fase.value,
        "es_pregunta": turno.es_pregunta,
        "decision": turno.decision,
        "motivo_decision": turno.motivo_decision,
        "consulta_consolidada": turno.consulta_consolidada,
        "tiempo_ms": turno.elapsed_ms,
        "dto": turno.dto_resultado,
        "estado": turno.estado,
        "estado_operativo": turno.estado.estado_operativo.value,
        "question_intent": turno.intent_elegido,
        "preguntas_candidatas": turno.candidatas_traza,
        "preguntas_descartadas": turno.descartadas_traza,
        "pregunta_final": turno.pregunta_elegida,
        "version_orquestador": turno.traza.version_orquestador,
        "top3_ml_raw": turno.traza.top3_ml_raw,
        "hipotesis_rechazadas_usuario": turno.traza.hipotesis_rechazadas_usuario,
        "nueva_evidencia": turno.traza.nueva_evidencia,
        "hipotesis_final_presentada": turno.traza.hipotesis_final_presentada,
        "exclusiones_compatibilidad": turno.traza.exclusiones_compatibilidad,
        "estado_previo": turno.traza.estado_previo,
        "estado_detectado_mensaje_actual": turno.traza.estado_detectado_mensaje_actual,
        "decision_transicion": turno.traza.decision_transicion,
        "motivo_transicion": turno.traza.motivo_transicion,
        "dominio_previo": turno.traza.dominio_previo,
        "dominio_detectado_actual": turno.traza.dominio_detectado_actual,
        "dominio_actual": turno.traza.dominio_actual,
    }
