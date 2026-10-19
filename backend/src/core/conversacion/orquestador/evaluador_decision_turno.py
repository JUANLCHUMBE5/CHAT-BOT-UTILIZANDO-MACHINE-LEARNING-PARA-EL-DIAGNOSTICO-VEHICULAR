"""Evaluador de suficiencia de información y toma de decisiones del turno (PREGUNTAR vs DIAGNOSTICAR)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from src.core.conversacion.control_aclaraciones import (
    aclaraciones_emitidas,
    dato_desconocido,
    debe_avanzar,
    desconocidos_consecutivos,
    hay_evidencia_diagnostica,
)
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.models import ConversationState, FactState, FactType, QuestionIntent
from src.core.conversacion.suficiencia_informacion import EvaluadorSuficiencia
from src.core.diagnostico.politica_seguridad import PoliticaSeguridad, SeveridadSeguridad


class EvaluadorDecisionTurno:
    """Evalúa la suficiencia de hechos, gestiona respuestas de aclaración y decide el curso del turno."""

    @classmethod
    def evaluar_decision(
        cls,
        estado: ConversationState,
        texto_limpio: str,
        interpretacion_corta: Optional[Dict[str, Any]],
        diagnostico_forzado: Optional[str],
    ) -> Tuple[
        str,  # decision
        str,  # motivo_decision
        str,  # respuesta_texto
        bool,  # es_pregunta
        Optional[str],  # intent_elegido
        Optional[str],  # pregunta_elegida
        List[Dict[str, Any]],  # candidatas_traza
        List[Dict[str, Any]],  # descartadas_traza
        Optional[str],  # falla_forzada_alternativa
        Optional[Tuple[SeveridadSeguridad, Optional[str]]],  # seguridad
    ]:
        falla_forzada_alternativa = diagnostico_forzado

        # 1. Evaluación de suficiencia inicial
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
                texto_historial_normalizado,
            )
        ):
            es_suficiente = False
            motivo_suficiencia = "RPM baja sin síntomas discriminantes: solicitar contexto antes de clasificar"

        if medicion_area_pendiente:
            es_suficiente = False
            motivo_suficiencia = "Falta la lectura técnica mínima para confirmar la ruta explícita de mezcla o MAP"

        forzar_avance = debe_avanzar(estado, texto_limpio)
        sin_evidencia = not hay_evidencia_diagnostica(estado)
        if sin_evidencia and dato_desconocido(texto_limpio):
            forzar_avance = desconocidos_consecutivos(estado) >= max(1, estado.max_repreguntas - 1)

        if forzar_avance and dato_desconocido(texto_limpio):
            estado.registrar_hecho(
                "dato_solicitado_desconocido", "DESCONOCIDO", categoria="flujo",
                estado=FactState.NO_REVISADO, texto_crudo=texto_limpio,
                tipo=FactType.CONDICION,
            )

        decision = "DIAGNOSTICAR"
        motivo_decision = motivo_suficiencia
        respuesta_texto = ""
        es_pregunta = False
        intent_elegido = None
        pregunta_elegida = None
        candidatas_traza: List[Dict[str, Any]] = []
        descartadas_traza: List[Dict[str, Any]] = []

        # 2. Respuestas técnicas, indisponibilidad de herramientas o Plan B
        if interpretacion_corta and estado.preguntas_realizadas:
            resp_corta_res = cls._procesar_respuesta_corta_en_flujo(
                estado=estado,
                interpretacion_corta=interpretacion_corta,
            )
            if resp_corta_res:
                decision, motivo_decision, respuesta_texto, es_pregunta, intent_elegido, pregunta_elegida = resp_corta_res

        # Límite de aclaraciones / forzar avance
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

        # Verificación prioritaria de seguridad física
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
                pregunta_elegida, intent_obj = seleccion_area
                intent_elegido = intent_obj.value
                estado.registrar_pregunta(
                    intent=intent_obj,
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
                    else:
                        es_suficiente = True
                        motivo_suficiencia = (
                            "El caso ya tiene una categoría técnica explícita; evitando una repregunta ajena"
                        )
                else:
                    seleccion = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
                    if seleccion:
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

        return (
            decision,
            motivo_decision,
            respuesta_texto,
            es_pregunta,
            intent_elegido,
            pregunta_elegida,
            candidatas_traza,
            descartadas_traza,
            falla_forzada_alternativa,
            (sev_seguridad, banner_seguridad),
        )

    @classmethod
    def _procesar_respuesta_corta_en_flujo(
        cls,
        estado: ConversationState,
        interpretacion_corta: Dict[str, Any],
    ) -> Optional[Tuple[str, str, str, bool, Optional[str], Optional[str]]]:
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
            return (
                "PREGUNTAR",
                "Resultado de revisión sin componente identificable: solicitando aclaración sin repetir hipótesis",
                pregunta_elegida,
                True,
                intent_elegido,
                pregunta_elegida,
            )

        if cat_ic == "MEDICION_INCOMPLETA":
            pregunta_anterior = str((estado.ultima_pregunta() or {}).get("texto", "")).lower()
            if "caudal_inyectores_reportado" in estado.hechos:
                solicitud = (
                    "¿Qué presión de combustible registró el manómetro o qué resultado "
                    "dio la prueba de balance/caudal de inyectores?"
                )
            elif "maf" in pregunta_anterior:
                solicitud = "¿Qué flujo del MAF marca el escáner en g/s y a qué RPM o condición del motor?"
            elif "map" in pregunta_anterior or "carga absoluta" in pregunta_anterior:
                solicitud = "¿Qué valor numérico muestra el MAP, con su unidad (kPa) y condición del motor?"
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
            return (
                "PREGUNTAR",
                "Afirmación sin valor/unidad: solicitar el dato técnico concreto sin cambiar de sistema",
                pregunta_elegida,
                True,
                intent_elegido,
                pregunta_elegida,
            )

        if cat_ic == "DIAGNOSTICO_CONFIRMADO":
            respuesta_texto = (
                "Gracias, registré que la hipótesis principal fue confirmada por tu respuesta. "
                "Si identificaste una falla física específica, indícala para dejarla diferenciada."
            )
            return ("CONFIRMACION", "Respuesta afirmativa vinculada a la pregunta de validación del diagnóstico", respuesta_texto, False, None, None)

        if valor_ic == "NO" and "sensor_maf_lectura_anomala_reportada" in estado.hechos:
            respuesta_texto = (
                "Entiendo. Mantengo el hallazgo del MAF sin darlo por confirmado. Revisa primero "
                "conector/cableado y compara su señal o flujo en datos en vivo; si no puedes leerlo, "
                "inspecciona también una posible entrada de aire no medida. ¿Qué resultado obtienes?"
            )
            intent_elegido = QuestionIntent.MEDICION_TECNICA.value
            estado.registrar_pregunta(
                intent=QuestionIntent.MEDICION_TECNICA,
                texto=respuesta_texto,
                incrementar_repregunta=False,
            )
            return ("PREGUNTAR", "Respuesta negativa: conservar hallazgo MAF y avanzar en admisión", respuesta_texto, True, intent_elegido, respuesta_texto)

        if cat_ic == "DIAGNOSTICO_DESCARTADO":
            falla_descartada = str(interpretacion_corta.get("diagnostico") or estado.falla_principal or "")
            if falla_descartada and falla_descartada not in estado.hipotesis_descartadas:
                estado.hipotesis_descartadas.append(falla_descartada)
            pregunta_especifica, intent_especifico = (
                GeneradorPreguntas.formular_pregunta_discriminante_post_descarte(
                    estado, falla_descartada,
                )
            )
            respuesta_texto = (
                "Entendido: descarto esa hipótesis por ahora. "
                "Para seguir en el mismo sistema: " + pregunta_especifica
            )
            intent_elegido = intent_especifico.value
            estado.registrar_pregunta(
                intent=intent_especifico,
                texto=respuesta_texto,
                incrementar_repregunta=False,
            )
            return ("PREGUNTAR", "Respuesta negativa vinculada al diagnóstico; solicitando hallazgo sin reiniciar el caso", respuesta_texto, True, intent_elegido, respuesta_texto)

        # Plan B
        if (
            cat_ic in ("HERRAMIENTA_INDISPONIBLE", "NO_SABE_REALIZAR_PRUEBA", "NO_REVISADO")
            or (valor_ic == "NO" and campo_ic and "disponible" in campo_ic)
        ):
            from src.core.conversacion.compatibilidad_preguntas import CompatibilidadPreguntas
            from src.core.conversacion.gestor_plan_b import GestorPlanB

            dominio_actual = CompatibilidadPreguntas.dominio_actual(estado)
            ultima_preg_txt = estado.ultima_pregunta().get("texto", "") if estado.ultima_pregunta() else ""
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
                intent_elegido = plan_b[2].value
                decision = "PLAN_B"
                if cat_ic == "NO_SABE_REALIZAR_PRUEBA":
                    motivo_decision = f"Usuario no sabe realizar prueba ({campo_ic}): activando alternativa observable / Plan B seguro"
                elif cat_ic == "NO_REVISADO":
                    motivo_decision = f"Comprobación no revisada ({campo_ic}): ofreciendo alternativa observable sencilla sin herramientas"
                else:
                    motivo_decision = f"Herramienta indisponible ({campo_ic}): activando Plan B sensorial"
                estado.registrar_pregunta(intent=QuestionIntent(intent_elegido), texto=pregunta_elegida, incrementar_repregunta=False)
                return (decision, motivo_decision, pregunta_elegida, True, intent_elegido, pregunta_elegida)
            elif cat_ic in ("HERRAMIENTA_INDISPONIBLE", "NO_SABE_REALIZAR_PRUEBA"):
                pregunta_elegida = (
                    "Entiendo maestro. No insistiré en esa medición técnica; mantenemos la orientación provisional "
                    "sin confirmar la hipótesis hasta una revisión presencial. ¿Prefieres realizar una inspección visual "
                    "directa sencilla sin herramientas o derivarlo a taller especializado?"
                )
                intent_elegido = QuestionIntent.PLAN_B_SIN_HERRAMIENTAS.value
                estado.registrar_pregunta(intent=QuestionIntent(intent_elegido), texto=pregunta_elegida, incrementar_repregunta=False)
                return ("PLAN_B", "Sin método ni comprobación observable viable: orientando a derivación profesional", pregunta_elegida, True, intent_elegido, pregunta_elegida)
            elif cat_ic == "NO_REVISADO":
                from src.core.diagnostico.enrutador_sistema import detectar_areas_tecnicas
                areas_actuales = detectar_areas_tecnicas(" ".join(estado.historial_mensajes_usuario))
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
                return (decision, motivo_decision, respuesta_texto, decision == "PREGUNTAR", None, None)

        # Herramienta disponible
        if cat_ic == "HERRAMIENTA_RECUPERADA" or (valor_ic == "SI" and campo_ic and "disponible" in campo_ic):
            if campo_ic and "manometro" in campo_ic:
                pregunta_elegida = "Con el manómetro conectado al riel de inyección: ¿cuántos PSI marca con la llave en ON y al dar marcha?"
                intent_elegido = QuestionIntent.MEDICION_PRESION.value
                estado.establecer_pregunta_pendiente(
                    intent=QuestionIntent.MEDICION_PRESION,
                    expected_quantity="presion_combustible",
                    expected_units=["PSI", "bar", "kPa"],
                    related_system="COMBUSTIBLE",
                )
                estado.registrar_pregunta(intent=QuestionIntent(intent_elegido), texto=pregunta_elegida, incrementar_repregunta=False)
                return ("PREGUNTAR", "Usuario cuenta con manómetro: solicitando lectura de presión de combustible", pregunta_elegida, True, intent_elegido, pregunta_elegida)
            elif campo_ic and "chispa" in campo_ic:
                if "prueba_chispa" not in estado.completed_tests:
                    pregunta_elegida = "Con el probador de chispa conectado: ¿se observa salto constante de chispa azulada al dar arranque?"
                    intent_elegido = QuestionIntent.COMPONENTE_REVISADO.value
                    estado.establecer_pregunta_pendiente(
                        intent=QuestionIntent.COMPONENTE_REVISADO,
                        expected_quantity="resultado_prueba_chispa",
                        related_system="ENCENDIDO",
                    )
                    estado.registrar_pregunta(intent=QuestionIntent(intent_elegido), texto=pregunta_elegida, incrementar_repregunta=False)
                    return ("PREGUNTAR", "Usuario cuenta con probador de chispa: solicitando comprobación", pregunta_elegida, True, intent_elegido, pregunta_elegida)
            else:
                pregunta_elegida = "¿Qué voltaje (V) registras en reposo y cuánto cae durante el arranque? Indica el punto de medición."
                intent_elegido = QuestionIntent.MEDICION_VOLTAJE.value
                estado.establecer_pregunta_pendiente(
                    intent=QuestionIntent.MEDICION_VOLTAJE,
                    expected_quantity="voltaje_bateria",
                    expected_units=["V", "mV"],
                    related_system="ELECTRICO",
                )
                estado.registrar_pregunta(intent=QuestionIntent(intent_elegido), texto=pregunta_elegida, incrementar_repregunta=False)
                return ("PREGUNTAR", "Usuario cuenta con multímetro: solicitando lectura de voltaje", pregunta_elegida, True, intent_elegido, pregunta_elegida)

        # Medición de presión
        if (campo_ic == "medicion_presion" or interpretacion_corta.get("unidad") in ("PSI", "bar", "kPa")) and interpretacion_corta.get("valor") is not None:
            val = interpretacion_corta.get("valor")
            unidad = interpretacion_corta.get("unidad", "PSI")
            estado.registrar_medicion("presion_combustible", float(val), unidad, contexto="riel_inyeccion", prueba="presion_combustible")
            estado.registrar_prueba_completada("presion_combustible", f"{val} {unidad}")
            estado.limpiar_pregunta_pendiente()
            escaneo_ya_realizado = bool(
                estado.obtener_valor_confirmado("sin_dtc")
                or estado.obtener_valor_confirmado("escaner_limpio")
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
                pregunta_sug = "Con presión reportada y encendido revisado, sin códigos DTC, considera también admisión y compresión como hipótesis pendientes. ¿Se observa suciedad o carbón en la mariposa de admisión?"
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
            return ("CONCLUSION_TECNICA", f"Medición de presión {val} {unidad} registrada y contextualizada", respuesta_texto, False, None, None)

        # La ruta histórica comparte el mismo contrato de mediciones que las etapas.
        from src.core.conversacion.respuestas_cortas.seguimiento_mediciones import evaluar_lectura
        lectura = evaluar_lectura(estado, interpretacion_corta)
        if lectura is not None:
            return lectura

        # Acople de compresor A/C
        if campo_ic == "compresor_acopla" or estado.obtener_valor_confirmado("compresor_acopla") == "SI":
            pregunta_ac = (
                "Confirmado: el compresor sí acopla y el embrague responde. "
                "Para verificar si hay fuga de gas o falta de intercambio de calor: ¿gira el electroventilador del condensador al encender el A/C y las tuberías del vano motor se sienten una bien fría y otra caliente?"
            )
            intent_ac = QuestionIntent.COMPONENTE_REVISADO
            estado.registrar_pregunta(intent=intent_ac, texto=pregunta_ac, incrementar_repregunta=False)
            return ("PREGUNTAR", "Compresor acopla confirmado: avanzando a electroventilador e intercambio térmico", pregunta_ac, True, intent_ac.value, pregunta_ac)

        # Luces de tablero
        if campo_ic == "luces_se_atenuan":
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
            return ("CONCLUSION_TECNICA", f"Observación de luces de tablero procesada: {valor_ic}", respuesta_texto, False, None, None)

        return None
