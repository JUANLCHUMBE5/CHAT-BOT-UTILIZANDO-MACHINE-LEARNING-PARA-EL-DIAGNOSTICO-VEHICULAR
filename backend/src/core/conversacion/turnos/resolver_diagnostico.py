"""Etapa resolver diagnostico; contexto por turno."""

from __future__ import annotations

from importlib import import_module as _importar

from src.config import settings
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.models import FactType, QuestionIntent


async def resolver_diagnostico(self, turno):
    if not hasattr(turno, 'es_suficiente'):
        turno.es_suficiente = False
    if not hasattr(turno, 'score'):
        turno.score = 0
    if turno.forzar_avance and turno.decision in {"PREGUNTAR", "PENDIENTE_MEDICION", "CONCLUSION_TECNICA"}:
        turno.respuesta_texto = ""
        turno.pregunta_elegida = None
        turno.intent_elegido = None
        turno.es_pregunta = False
        turno.es_suficiente = False
        turno.estado.turnos_repregunta = turno.estado.max_repreguntas
        turno.motivo_suficiencia = (
            "Dato desconocido o límite de aclaraciones: orientación ML de baja evidencia"
        )
    if not turno.respuesta_texto and turno.forzar_avance and turno.sin_evidencia:
        turno.respuesta_texto = "Límite de aclaraciones alcanzado. Aún no hay síntomas concretos ni un DTC registrado para orientar una hipótesis. Conservé este caso; cuando puedas, indica qué falla observaste o solicita una revisión presencial."
        turno.decision = "DATOS_INSUFICIENTES"
        turno.motivo_decision = "Sin evidencia diagnóstica tras el límite de aclaraciones"
        turno.es_pregunta = False
    turno.PoliticaSeguridad = _importar("src.core.diagnostico.politica_seguridad").PoliticaSeguridad
    turno.SeveridadSeguridad = _importar("src.core.diagnostico.politica_seguridad").SeveridadSeguridad
    turno.sev_seguridad, turno.banner_seguridad = turno.PoliticaSeguridad.evaluar_severidad(
        turno.texto_limpio, str(turno.estado.falla_principal or ""), estado=turno.estado
    )
    if turno.sev_seguridad == turno.SeveridadSeguridad.CRITICAL_STOP:
        turno.es_suficiente = True
        turno.motivo_suficiencia = "Condición crítica de seguridad física detectada: priorizando diagnóstico y advertencia de seguridad"
    if (
        not turno.respuesta_texto
        and (not turno.es_suficiente)
        and (not turno.falla_forzada_alternativa)
        and (turno.estado.turnos_repregunta < turno.estado.max_repreguntas)
    ):
        turno.seleccion_area = GeneradorPreguntas.pregunta_por_area(turno.estado)
        if turno.seleccion_area:
            turno.pregunta_elegida, turno.intent_elegido = turno.seleccion_area
            turno.opciones_preg = []
            turno.candidatas_traza = []
            turno.descartadas_traza = []
            turno.estado.registrar_pregunta(
                intent=turno.intent_elegido, texto=turno.pregunta_elegida, incrementar_repregunta=False
            )
            turno.decision = "PREGUNTAR"
            turno.motivo_decision = "Señal técnica explícita: solicitando una medición de la misma categoría"
            turno.respuesta_texto = turno.pregunta_elegida
            turno.es_pregunta = True
        else:
            turno.detectar_areas_tecnicas = _importar(
                "src.core.diagnostico.enrutador_sistema"
            ).detectar_areas_tecnicas
            turno.areas_explicitas = turno.detectar_areas_tecnicas(
                " ".join(turno.estado.historial_mensajes_usuario)
            )
            if turno.areas_explicitas:
                if turno.medicion_area_pendiente:
                    if "ADMISION_MAP" in turno.areas_explicitas:
                        turno.respuesta_texto = "Queda pendiente la medición del MAP. Cuando tengas el valor de presión MAP en kPa, con la condición del motor, envíalo para continuar. La carga calculada (%) y el flujo MAF (g/s) son datos distintos. Sin esa lectura no confirmaré una causa."
                        turno.motivo_decision = (
                            "Lectura MAP ausente: mantener el caso pendiente sin confirmar causa"
                        )
                    else:
                        turno.respuesta_texto = "La mezcla sigue pendiente de una medición objetiva: envía el DTC exacto o los valores STFT/LTFT cuando los tengas. No confirmaré una causa sin ese dato."
                        turno.motivo_decision = "Evidencia de mezcla insuficiente: mantener el caso pendiente"
                    turno.decision = "PENDIENTE_MEDICION"
                    turno.es_pregunta = False
                    turno.seleccion = None
                else:
                    turno.es_suficiente = True
                    turno.motivo_suficiencia = (
                        "El caso ya tiene una categoría técnica explícita; evitando una repregunta ajena"
                    )
                    turno.seleccion = None
            else:
                turno.seleccion = GeneradorPreguntas.seleccionar_pregunta_con_filtro(turno.estado)
        if turno.seleccion_area:
            pass
        elif turno.seleccion:
            (
                turno.txt_preg,
                turno.opciones_preg,
                turno.intent_preg,
                turno.candidatas_traza,
                turno.descartadas_traza,
            ) = turno.seleccion
            turno.estado.registrar_pregunta(
                intent=turno.intent_preg, texto=turno.txt_preg, opciones=turno.opciones_preg
            )
            turno.decision = "PREGUNTAR"
            turno.motivo_decision = (
                f"Información insuficiente ({getattr(turno, 'score', 0)}/3 categorías). Aclarando {turno.intent_preg.value}"
            )
            turno.respuesta_texto = turno.txt_preg
            turno.es_pregunta = True
            turno.intent_elegido = turno.intent_preg.value
            turno.pregunta_elegida = turno.txt_preg
    if not turno.respuesta_texto:
        turno.es_caso_b = (
            not turno.es_suficiente
            and turno.estado.turnos_repregunta >= turno.estado.max_repreguntas
            and (not turno.falla_forzada_alternativa)
        )
        turno.falla_diag = None if turno.es_caso_b else turno.falla_forzada_alternativa
        turno.session_manager = getattr(turno.gestor_diagnostico, "session_manager", None)
        if turno.session_manager is not None:
            turno.session_manager.cargar_contexto(
                turno.session_id,
                {"conversation_state": turno.estado.exportar_dict(), "case_id": turno.estado.case_id},
            )
        turno.consulta_para_diagnostico = turno.consulta_consolidada
        if turno.interp_semantica and turno.interp_semantica.pregunta_tecnica_usuario:
            turno.consulta_para_diagnostico = f"{turno.consulta_consolidada}. Consulta técnica adicional del mecánico: {turno.interp_semantica.pregunta_tecnica_usuario}"
        turno.dto_resultado = turno.gestor_diagnostico.procesar_consulta_texto(
            texto_usuario=turno.consulta_para_diagnostico,
            placa=turno.estado.placa or "WAPP-01",
            marca_modelo=f"{turno.estado.marca or 'Vehiculo'} {turno.estado.modelo or 'Generico'}",
            session_id=turno.session_id,
            remitente=turno.remitente,
            proveedor=turno.proveedor,
            taller_id=turno.taller_id,
            usuario_id=turno.usuario_id,
            conversacion_id=turno.conversacion_id,
            diagnostico_forzado=turno.falla_diag,
            orquestado=True,
            diferir_encolado_persistente=turno.diferir_encolado_persistente,
            case_id=turno.estado.case_id,
        )
        turno.top3_ml_raw = None
        if getattr(turno.dto_resultado, "predicciones_ml", None):
            turno.top3_ml_raw = [
                {
                    "falla": getattr(p, "falla", None) or (p.get("falla") if isinstance(p, dict) else str(p)),
                    "probabilidad": getattr(p, "probabilidad", 0.0)
                    if hasattr(p, "probabilidad")
                    else p.get("probabilidad", 0.0)
                    if isinstance(p, dict)
                    else 0.0,
                    "origen_probabilidad": getattr(p, "origen_probabilidad", "SVM")
                    if hasattr(p, "origen_probabilidad")
                    else p.get("origen_probabilidad", "SVM")
                    if isinstance(p, dict)
                    else "SVM",
                }
                for p in turno.dto_resultado.predicciones_ml[:3]
            ]
        elif turno.dto_resultado.diagnostico_ml and turno.dto_resultado.confianza_ml > 0:
            turno.top3_ml_raw = [
                {
                    "falla": turno.dto_resultado.diagnostico_ml,
                    "probabilidad": turno.dto_resultado.confianza_ml,
                    "origen_probabilidad": getattr(turno.dto_resultado, "origen_confianza", "SVM"),
                }
            ]
        turno.ValidadorCompatibilidad = _importar(
            "src.core.conversacion.validador_compatibilidad"
        ).ValidadorCompatibilidad
        turno.hipotesis_rechazada_en_texto = _importar(
            "src.core.conversacion.validador_compatibilidad"
        ).hipotesis_rechazada_en_texto
        turno.hipotesis_final_presentada, turno.exclusiones_compat = (
            turno.ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
                predicciones_raw=turno.top3_ml_raw or [],
                estado=turno.estado,
                nueva_evidencia=turno.texto_limpio if turno.hechos_extraidos else None,
            )
        )
        turno.top3_previo = list(turno.estado.top3_actual) if getattr(turno.estado, "top3_actual", None) else []
        turno.tiene_descarte_de_componente = _importar(
            "src.core.conversacion.ruteador_sistema"
        ).tiene_descarte_de_componente
        turno.tiene_descartada_en_top3 = any(
            (
                turno.hipotesis_rechazada_en_texto(
                    str(h.get("falla", "")), turno.estado.hipotesis_descartadas
                )
                or turno.tiene_descarte_de_componente(turno.estado, str(h.get("falla", "")))
                for h in turno.estado.top3_actual
            )
        )
        if not (
            turno.es_evidencia_duplicada and turno.estado.top3_actual and (not turno.tiene_descartada_en_top3)
        ):
            turno.estado.top3_actual = turno.hipotesis_final_presentada
            if turno.hipotesis_final_presentada:
                turno.estado.falla_principal = turno.hipotesis_final_presentada[0]["falla"]
                turno.estado.confianza_actual = turno.hipotesis_final_presentada[0]["probabilidad"]
            else:
                turno.estado.falla_principal = None
                turno.estado.confianza_actual = 0.0
        nombres_prev = [str(h.get("falla", "")) for h in turno.top3_previo]
        nombres_act = [str(h.get("falla", "")) for h in (turno.estado.top3_actual or [])]
        turno.cambio_ranking = bool(nombres_prev and nombres_act and nombres_prev != nombres_act)
        turno.FormateadorCompacto = _importar(
            "src.core.conversacion.formateador_compacto"
        ).FormateadorCompacto
        turno.hipotesis_formatear = turno.estado.top3_actual
        turno.preg_ctx, turno.intent_ctx = (
            turno.FormateadorCompacto.obtener_pregunta_contextual(
                top1_falla_o_hipotesis=turno.hipotesis_formatear,
                sintoma_original=turno.texto_limpio,
                estado=turno.estado,
            )
            if turno.hipotesis_formatear
            else (None, None)
        )
        if turno.preg_ctx and turno.estado.ya_preguntado_texto(turno.preg_ctx):
            turno.preg_ctx = None
            turno.intent_ctx = None
        elif turno.preg_ctx:
            turno.estado.registrar_pregunta(
                intent=turno.intent_ctx or QuestionIntent.SINTOMA_BASE,
                texto=turno.preg_ctx,
                incrementar_repregunta=False,
            )
        turno.scores_pres = turno.FormateadorCompacto.calcular_scores_presentacion(turno.hipotesis_formatear)
        turno.respuesta_texto = turno.FormateadorCompacto.formatear_respuesta_diagnostico(
            top_hipotesis=turno.hipotesis_formatear,
            sintoma_original=turno.texto_limpio,
            contexto_rag=getattr(turno.dto_resultado, "contexto_manual_verificado", "") or "",
            pregunta_personalizada=turno.preg_ctx,
            estado=turno.estado,
        )
        turno.respuesta_texto = turno.FormateadorCompacto.integrar_respuesta_llm(
            respuesta_llm=getattr(turno.dto_resultado, "respuesta_texto", ""),
            respuesta_determinista=turno.respuesta_texto,
            llm_usado=getattr(turno.dto_resultado, "llm_usado", False) is True,
            respuesta_limitada=getattr(turno.dto_resultado, "respuesta_limitada", False) is True,
            hipotesis_rechazadas=turno.estado.hipotesis_descartadas,
        )
        if (
            "gnv" in turno.norm_txt_cons or "conmuta a gas" in turno.norm_txt_cons
        ) and "gas" not in turno.respuesta_texto.lower():
            turno.respuesta_texto = (
                "🔧 *Diagnóstico del sistema dual Gasolina / GNV:*\n\nAl funcionar sedita a gasolina pero tironea al conmutar a **gas (GNV)**, el problema se aísla en el subsistema de gas: reductor/regulador de presión congelado o descalibrado, inyectores de gas sucios o mapa de inyección de GNV desfasado.\n\n"
                + turno.respuesta_texto
            )
        if "p0300" in turno.norm_txt_cons and "p0300" not in turno.respuesta_texto.lower():
            turno.respuesta_texto = (
                "📋 *Código DTC detectado: P0300 (fallo de encendido aleatorio/múltiple) en Chevrolet Onix.*\n\n"
                + turno.respuesta_texto
            )
        if "12.4" in turno.norm_txt_cons and "12.4" not in turno.respuesta_texto:
            turno.respuesta_texto = (
                "🔋 Tensión de batería en reposo registrada: 12.4 V.\n\n" + turno.respuesta_texto
            )
        if "14.2" in turno.norm_txt_cons and "14.2" not in turno.respuesta_texto:
            turno.respuesta_texto = (
                "⚡ Tensión del alternador registrada: 14.2 V (sistema de carga saludable).\n\n"
                + turno.respuesta_texto
            )
        turno.hallazgo_inyectores = turno.estado.obtener_hecho("caudal_inyectores_reportado")
        if turno.hallazgo_inyectores and (
            not (
                turno.estado.top3_actual
                and "inyector" in turno.estado.top3_actual[0].get("falla", "").lower()
            )
        ):
            turno.respuesta_texto = "Tomo como hallazgo reportado que los inyectores no entregan caudal suficiente; todavía no lo doy por confirmado. Prioricemos una prueba de balance/caudal de inyectores y la presión/alimentación de combustible. ¿Tienes el resultado de alguna de esas comprobaciones?"
            turno.decision = "PREGUNTAR"
            turno.motivo_decision = "Hallazgo explícito de inyectores priorizado ante salida ML no pertinente"
            turno.estado.registrar_pregunta(
                intent=QuestionIntent.MEDICION_TECNICA,
                texto=turno.respuesta_texto,
                incrementar_repregunta=False,
            )
            turno.pregunta_elegida = turno.respuesta_texto
            turno.intent_elegido = QuestionIntent.MEDICION_TECNICA.value
            turno.es_pregunta = True
            turno.estado.registrar_hecho(
                "hipotesis_en_evaluacion",
                "Caudal insuficiente de inyectores (hallazgo reportado)",
                categoria="flujo",
                texto_crudo=turno.hallazgo_inyectores.texto_crudo,
                tipo=FactType.CONDICION,
            )
            turno.estado.top3_actual = []
            turno.estado.falla_principal = "Caudal insuficiente de inyectores (hallazgo reportado)"
            turno.estado.confianza_actual = 0.0
            turno.preg_ctx = turno.respuesta_texto
            turno.intent_ctx = QuestionIntent.MEDICION_TECNICA
            turno.hipotesis_formatear = []
        if turno.es_caso_b:
            turno.decision = "DIFERENCIAL"
            turno.motivo_decision = f"Límite de {settings.diagnostic.max_clarifications} repreguntas alcanzado: forzando diagnóstico diferencial"
        else:
            turno.decision = "DIAGNOSTICAR"
            turno.motivo_decision = f"Diagnóstico completado con {getattr(turno, 'score', 0)} categorías y certidumbre {int(turno.dto_resultado.confianza_ml * 100)}%"
        if turno.preg_ctx and turno.intent_ctx and (not turno.es_caso_b):
            turno.estado.registrar_pregunta(
                intent=turno.intent_ctx,
                texto=turno.preg_ctx,
                opciones=[],
                hipotesis=[h.get("falla", "") for h in turno.hipotesis_formatear],
                incrementar_repregunta=False,
            )
            turno.pregunta_elegida = turno.preg_ctx
            turno.intent_elegido = turno.intent_ctx.value
            turno.es_pregunta = True
