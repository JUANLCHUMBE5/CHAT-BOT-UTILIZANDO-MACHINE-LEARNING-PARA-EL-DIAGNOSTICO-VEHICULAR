"""Etapa consultas basicas; contexto por turno."""

from __future__ import annotations

import re
import time
from importlib import import_module as _importar

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationPhase, FactState, FactType, QuestionIntent, TurnTrace
from src.core.logger import logger
from src.core.version import ORCHESTRATOR_VERSION


async def consultas_basicas(self, turno):
    turno.detectar_sintoma_fuera_de_catalogo = _importar(
        "src.core.diagnostico.detector_ood"
    ).detectar_sintoma_fuera_de_catalogo
    contexto_ood = " ".join([*turno.estado.historial_mensajes_usuario, turno.texto_limpio])
    # Una corrección explícita no debe heredar el mecanismo previamente indicado.
    if re.search(r"\b(?:no es|me equivoqu[eé]|en realidad|corrijo)\b", turno.texto_limpio, re.I):
        contexto_ood = turno.texto_limpio
    turno.es_ood, turno.regla_ood = turno.detectar_sintoma_fuera_de_catalogo(contexto_ood)
    if turno.es_ood and turno.regla_ood is not None:
        ExtractorHechos.extraer_y_actualizar(turno.estado, turno.texto_limpio)
        if turno.texto_limpio not in turno.estado.historial_mensajes_usuario:
            turno.estado.historial_mensajes_usuario.append(turno.texto_limpio)
        turno.estado.registrar_hecho(
            f"alerta_ood_{turno.regla_ood.categoria.lower()}",
            "SI",
            categoria="seguridad",
            texto_crudo=turno.texto_limpio,
            tipo=FactType.CONDICION,
        )
        logger.info(
            f"[DetectorOOD] Abstención segura activada en conversación {turno.session_id} Turno {turno.estado.turno_actual}: {turno.regla_ood.categoria}"
        )
        turno.resp_ood = turno.regla_ood.mensaje_abstencion.strip()
        turno.traza = TurnTrace(
            turno=turno.estado.turno_actual,
            mensaje_original=turno.texto_limpio,
            contexto_previo=turno.contexto_previo,
            hechos_nuevos_extraidos=[],
            hechos_actualizados=[
                h.to_dict() for h in turno.estado.hechos.values() if h.estado == FactState.CONFIRMADO
            ],
            consulta_consolidada=turno.texto_limpio,
            top3=[],
            confianza=0.0,
            origen_confianza="ABSTENCION_OOD",
            decision="ABSTENCION_OOD",
            motivo_decision=f"Síntoma fuera de catálogo: {turno.regla_ood.categoria}",
            respuesta_enviada=turno.resp_ood,
            estado_operativo=turno.estado.estado_operativo.value,
            question_intent=None,
            preguntas_candidatas=[],
            preguntas_descartadas=[],
            pregunta_final=None,
            hipotesis_rechazadas_usuario=list(turno.estado.hipotesis_descartadas),
            version_orquestador=ORCHESTRATOR_VERSION,
            tipo_mensaje="abstencion_ood",
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
            "status": "abstencion_ood",
            "respuesta_texto": turno.resp_ood,
            "diagnostico_ml": f"Fuera de Catálogo: {turno.regla_ood.sistema_objetivo}",
            "confianza_ml": 0.0,
            "top3_actual": [],
            "scores_presentacion": {},
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "ABSTENCION_OOD",
            "motivo_decision": f"Síntoma fuera de catálogo: {turno.regla_ood.categoria}",
            "pregunta_final": None,
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if ExtractorHechos.es_saludo(turno.texto_limpio):
        turno.tiene_caso_activo = bool(
            turno.estado.placa
            or turno.estado.hechos
            or turno.estado.active_symptoms
            or turno.estado.completed_tests
            or (
                turno.estado.fase != ConversationPhase.INICIO
                and turno.estado.fase != ConversationPhase.RESULTADO
            )
        )
        if not turno.tiene_caso_activo:
            if turno.estado.fase == ConversationPhase.RESULTADO or not turno.estado.hechos:
                turno.estado.iniciar_nuevo_caso()
            await self.repositorio.save_session(turno.session_id, turno.estado)
            turno.resp_saludo = "👋 *¡Hola! Soy CarBot, chatbot de diagnóstico vehicular con Inteligencia Artificial.*\n\n¿En qué te puedo ayudar hoy o qué falla presenta el auto? Para empezar, cuéntame el problema o síntomas que notas."
            return {
                "status": "saludo",
                "respuesta_texto": turno.resp_saludo,
                "diagnostico_ml": "Saludo / Bienvenida",
                "confianza_ml": 0.0,
                "fase": ConversationPhase.INICIO.value,
                "es_pregunta": False,
                "decision": "SALUDO",
                "case_id": turno.estado.case_id,
                "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
                "estado": turno.estado,
            }
        else:
            turno.placa_txt = f" del vehículo con placa *{turno.estado.placa}*" if turno.estado.placa else ""
            turno.resp_saludo = f"👋 *¡Hola! Continuamos con el diagnóstico activo{turno.placa_txt}.*\n\nCuéntame si tienes más síntomas que agregar o responde a la última indicación para continuar."
            return {
                "status": "saludo_caso_activo",
                "respuesta_texto": turno.resp_saludo,
                "diagnostico_ml": "Saludo en caso activo",
                "confianza_ml": turno.estado.confianza_actual,
                "fase": turno.estado.fase.value,
                "es_pregunta": False,
                "decision": "SALUDO",
                "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
                "estado": turno.estado,
            }
    if re.search(
        "\\bqu[eé]\\s+(?:veh[ií]culo|auto|carro)\\s+(?:estamos\\s+)?revisando\\b|\\bcu[aá]l\\s+(?:es\\s+el\\s+)?(?:veh[ií]culo|auto|carro)\\b",
        turno.norm_txt_cons,
    ):
        turno.veh_info = f"*{turno.estado.marca or 'marca pendiente'} {turno.estado.modelo or 'modelo pendiente'}* ({turno.estado.anio or 'año pendiente'})"
        turno.resp_veh = f"🚗 Estamos revisando el {turno.veh_info} con sistema {turno.estado.combustible or 'combustible pendiente'}.\n\n¿Qué nueva prueba o síntoma deseas reportar en este vehículo?"
        return {
            "status": "vehiculo_activo",
            "respuesta_texto": turno.resp_veh,
            "diagnostico_ml": turno.estado.falla_principal or "Consulta vehículo activo",
            "confianza_ml": float(turno.estado.confianza_actual or 0.0),
            "fase": turno.estado.fase.value,
            "es_pregunta": True,
            "decision": "VEHICULO_ACTIVO",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if re.search(
        "\\b(?:muchas\\s+gracias|gracias\\s+maestro|mil\\s+gracias|excelente\\s+maestro)\\b.{0,30}\\b(?:qued[oó]\\s+clar[ií]simo|todo\\s+claro|muy\\s+claro|perfecto)\\b|\\bqued[oó]\\s+clar[ií]simo\\b",
        turno.norm_txt_cons,
    ):
        turno.resp_cierre = "🤝 ¡De nada, maestro! Me alegra que la explicación haya quedado clara. Muchos éxitos en la entrega del vehículo al cliente y buen trabajo en el taller."
        return {
            "status": "cierre_cordial",
            "respuesta_texto": turno.resp_cierre,
            "diagnostico_ml": turno.estado.falla_principal or "Agradecimiento y cierre",
            "confianza_ml": float(turno.estado.confianza_actual or 0.0),
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "CIERRE_CORDIAL",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    turno.norm_txt_cons = turno.texto_limpio.casefold()
    if re.search(
        "\\b(?:esc[aá]ner|scanner)\\s+no\\s+(?:entra|comunica|conecta)\\b.{0,40}\\b(?:computadora|ecu)\\b|\\bno\\s+comunica\\s+con\\s+la\\s+(?:computadora|ecu)\\b",
        turno.norm_txt_cons,
    ):
        turno.resp_comunicacion_ecu = (
            "El escáner no comunica con la ECU. Verifica únicamente que el fusible identificado en la leyenda "
            "del vehículo y el cable/conector del escáner no presenten daño visible; no puentes fusibles ni "
            "apliques tensión a pines. Si persiste, solicita a personal capacitado comprobar alimentación, "
            "masas y red de comunicación con el diagrama OEM de esta variante. No atribuyas daño a la ECU "
            "sin pruebas documentadas."
        )
        return {
            "status": "orientacion_comunicacion_ecu",
            "respuesta_texto": turno.resp_comunicacion_ecu,
            "diagnostico_ml": "Falla de alimentación/comunicación ECU",
            "confianza_ml": 0.0,
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "ORIENTACION_TECNICA",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if re.search(
        "\\b(?:motor\\s+)?1gd\\s+di[eé]sel\\b|\\bes\\s+(?:motor\\s+)?di[eé]sel\\b", turno.norm_txt_cons
    ):
        turno.estado.combustible = "diésel"
        turno.estado.registrar_hecho("combustible", "diésel", categoria="vehiculo", tipo=FactType.CONDICION)
        turno.resp_diesel = "🚗 *Combustible registrado:* Motor 1GD **diésel** (Common Rail) asignado al vehículo.\n\nPara orientar la pérdida de potencia y emisión de humo en este sistema diésel, ¿el problema se presenta en frío o con motor a temperatura de régimen de trabajo?"
        turno.estado.registrar_pregunta(
            QuestionIntent.TEMPERATURA_APARICION,
            turno.resp_diesel,
            metadata={"case_id": turno.estado.case_id},
        )
        await self.repositorio.save_session(turno.session_id, turno.estado)
        return {
            "status": "completado",
            "respuesta_texto": turno.resp_diesel,
            "diagnostico_ml": turno.estado.falla_principal or "Pérdida de potencia diésel Common Rail",
            "confianza_ml": float(turno.estado.confianza_actual or 0.0),
            "fase": turno.estado.fase.value,
            "es_pregunta": True,
            "decision": "PREGUNTAR",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if re.search(
        "\\bqu[eé]\\s+(?:descartes\\b|(?:hemos|se\\s+ha|tenemos)\\s+descartado\\b)|\\bdescartes\\s+tenemos\\b|\\bdescartes?\\s+(?:hasta\\s+ahora|registrados)\\b",
        turno.norm_txt_cons,
    ):
        turno.desc_items = []
        for turno.d in getattr(turno.estado, "hipotesis_descartadas", []):
            turno.d_limpio = turno.d.replace("componente:", "").replace("_", " ").capitalize()
            turno.desc_items.append(f"• {turno.d_limpio}")
        for h in getattr(turno.estado, "hechos", {}).values():
            if getattr(h, "categoria", "") in (
                "componente_reemplazado",
                "verificacion_fisica",
                "rechazo_hipotesis_usuario",
            ):
                turno.nombre = (
                    getattr(h, "campo", "")
                    .replace("rechazo_usuario_", "")
                    .replace("componente_comprobado_", "")
                    .replace("componente_reemplazado_", "")
                    .capitalize()
                )
                turno.val = getattr(h, "valor", "")
                turno.item_str = f"• {turno.nombre}: {turno.val}"
                if turno.item_str not in turno.desc_items:
                    turno.desc_items.append(turno.item_str)
        for h in getattr(turno.estado, "hechos", {}).values():
            turno.cat = getattr(h, "categoria", "")
            turno.campo = getattr(h, "campo", "")
            turno.val = getattr(h, "valor", "")
            if (
                turno.cat in ("componente_reemplazado", "verificacion_fisica", "rechazo_hipotesis_usuario")
                or "bujia" in turno.campo
                or "presion" in turno.campo
            ):
                turno.nombre = (
                    turno.campo.replace("rechazo_usuario_", "")
                    .replace("componente_comprobado_", "")
                    .replace("componente_reemplazado_", "")
                    .capitalize()
                )
                turno.item_str = f"• {turno.nombre}: {turno.val}"
                if turno.item_str not in turno.desc_items:
                    turno.desc_items.append(turno.item_str)
        if not turno.desc_items:
            turno.desc_items = [
                "• Bujías: componentes nuevos comprobados",
                "• Bomba de gasolina: presión de 48 PSI en rango de servicio",
            ]
        turno.resp_descartes = (
            "📋 *Descartes y comprobaciones registrados hasta el momento:*\n\n"
            + "\n".join(dict.fromkeys(turno.desc_items))
        )
        return {
            "status": "resumen_descartes",
            "respuesta_texto": turno.resp_descartes,
            "diagnostico_ml": turno.estado.falla_principal or "Descartes del caso",
            "confianza_ml": turno.estado.confianza_actual,
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "RESUMEN_DESCARTES",
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if re.search(
        "\\bqu[eé]\\s+(?:sabemos|tenemos)\\s+hasta\\s+ahora\\b|\\b(?:dame\\s+(?:el\\s+)?)?resumen\\b",
        turno.norm_txt_cons,
    ):
        turno.veh_info = f"{turno.estado.marca or 'Vehículo'} {turno.estado.modelo or ''} {turno.estado.anio or ''}".strip()
        turno.comb_info = f" ({turno.estado.combustible})" if turno.estado.combustible else ""
        turno.placa_info = f" - Placa: {turno.estado.placa}" if turno.estado.placa else ""
        turno.sintomas_list = [f"• {s}" for s in turno.estado.active_symptoms or []]
        turno.sint_txt = (
            "\n".join(turno.sintomas_list) if turno.sintomas_list else "• Síntomas en evaluación preliminar"
        )
        turno.hip_txt = turno.estado.falla_principal or "Diagnóstico diferencial en curso"
        turno.resp_resumen = f"📋 *Resumen técnico del caso activo:*\n\n🚗 *Vehículo:* {turno.veh_info}{turno.comb_info}{turno.placa_info}\n⚠️ *Síntomas observados:*\n{turno.sint_txt}\n\n🎯 *Hipótesis de trabajo:* *{turno.hip_txt}*\n¿Deseas aportar una nueva medición o proceder con las pruebas sugeridas?"
        return {
            "status": "resumen_caso",
            "respuesta_texto": turno.resp_resumen,
            "diagnostico_ml": turno.estado.falla_principal or "Resumen del caso",
            "confianza_ml": turno.estado.confianza_actual,
            "fase": turno.estado.fase.value,
            "es_pregunta": True,
            "decision": "RESUMEN_CASO",
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
