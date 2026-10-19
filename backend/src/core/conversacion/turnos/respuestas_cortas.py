"""Etapa respuestas cortas; contexto por turno."""

from __future__ import annotations

from importlib import import_module as _importar

from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.models import QuestionIntent
from src.core.conversacion.respuestas_cortas.seguimiento_mediciones import evaluar_lectura


async def respuestas_cortas(self, turno):
    if turno.interpretacion_corta and (
        turno.estado.preguntas_realizadas
        or turno.interpretacion_corta.get("categoria_respuesta")
        in ("HERRAMIENTA_INDISPONIBLE", "NO_SABE_REALIZAR_PRUEBA")
    ):
        turno.campo_ic = turno.interpretacion_corta.get("campo")
        turno.valor_ic = str(turno.interpretacion_corta.get("valor", "")).upper()
        turno.cat_ic = turno.interpretacion_corta.get("categoria_respuesta", "")
        if turno.cat_ic == "REVISION_AMBIGUA":
            turno.pregunta_elegida = "Entiendo que ya revisaste algo y está bien. Para actualizar este caso sin asumir: ¿qué componente o prueba revisaste y cuál fue el resultado concreto?"
            turno.intent_elegido = QuestionIntent.COMPONENTE_REVISADO.value
            turno.estado.registrar_pregunta(
                intent=QuestionIntent.COMPONENTE_REVISADO,
                texto=turno.pregunta_elegida,
                incrementar_repregunta=False,
            )
            turno.decision = "PREGUNTAR"
            turno.motivo_decision = "Resultado de revisión sin componente identificable: solicitando aclaración sin repetir hipótesis"
            turno.respuesta_texto = turno.pregunta_elegida
            turno.es_pregunta = True
        elif turno.cat_ic == "MEDICION_INCOMPLETA":
            turno.pregunta_anterior = str((turno.estado.ultima_pregunta() or {}).get("texto", "")).lower()
            if "caudal_inyectores_reportado" in turno.estado.hechos:
                turno.solicitud = "¿Qué presión de combustible registró el manómetro o qué resultado dio la prueba de balance/caudal de inyectores?"
            elif "maf" in turno.pregunta_anterior:
                turno.solicitud = (
                    "¿Qué flujo del MAF marca el escáner en g/s y a qué RPM o condición del motor?"
                )
            elif "map" in turno.pregunta_anterior or "carga absoluta" in turno.pregunta_anterior:
                turno.solicitud = (
                    "¿Qué valor numérico muestra el MAP, con su unidad (kPa) y condición del motor?"
                )
            elif (
                "stft" in turno.pregunta_anterior
                or "ltft" in turno.pregunta_anterior
                or "dtc" in turno.pregunta_anterior
            ):
                turno.solicitud = "¿Cuál es el DTC exacto o qué valores STFT/LTFT (%) aparecen?"
            else:
                turno.solicitud = "¿Cuál es el valor exacto, con unidad y condición de medición?"
            turno.pregunta_elegida = "Entiendo que sí tienes el dato. " + turno.solicitud
            turno.intent_elegido = QuestionIntent.MEDICION_TECNICA.value
            turno.estado.registrar_pregunta(
                intent=QuestionIntent.MEDICION_TECNICA,
                texto=turno.pregunta_elegida,
                incrementar_repregunta=False,
            )
            turno.respuesta_texto = turno.pregunta_elegida
            turno.decision = "PREGUNTAR"
            turno.motivo_decision = (
                "Afirmación sin valor/unidad: solicitar el dato técnico concreto sin cambiar de sistema"
            )
            turno.es_pregunta = True
        elif turno.cat_ic == "DIAGNOSTICO_CONFIRMADO":
            turno.respuesta_texto = "Gracias, registré que la hipótesis principal fue confirmada por tu respuesta. Si identificaste una falla física específica, indícala para dejarla diferenciada."
            turno.decision = "CONFIRMACION"
            turno.motivo_decision = (
                "Respuesta afirmativa vinculada a la pregunta de validación del diagnóstico"
            )
        elif turno.valor_ic == "NO" and "sensor_maf_lectura_anomala_reportada" in turno.estado.hechos:
            turno.respuesta_texto = "Entiendo. Mantengo el hallazgo del MAF sin darlo por confirmado. Revisa primero conector/cableado y compara su señal o flujo en datos en vivo; si no puedes leerlo, inspecciona también una posible entrada de aire no medida. ¿Qué resultado obtienes?"
            turno.decision = "PREGUNTAR"
            turno.motivo_decision = "Respuesta negativa: conservar hallazgo MAF y avanzar en admisión"
            turno.pregunta_elegida = turno.respuesta_texto
            turno.intent_elegido = QuestionIntent.MEDICION_TECNICA.value
            turno.estado.registrar_pregunta(
                intent=QuestionIntent.MEDICION_TECNICA,
                texto=turno.pregunta_elegida,
                incrementar_repregunta=False,
            )
            turno.es_pregunta = True
        elif turno.cat_ic == "DIAGNOSTICO_DESCARTADO":
            turno.falla_descartada = str(
                turno.interpretacion_corta.get("diagnostico") or turno.estado.falla_principal or ""
            )
            if turno.falla_descartada and turno.falla_descartada not in turno.estado.hipotesis_descartadas:
                turno.estado.hipotesis_descartadas.append(turno.falla_descartada)
            turno.pregunta_especifica, turno.intent_especifico = (
                GeneradorPreguntas.formular_pregunta_discriminante_post_descarte(
                    turno.estado, turno.falla_descartada
                )
            )
            turno.respuesta_texto = (
                "Entendido: descarto esa hipótesis por ahora. Para seguir en el mismo sistema: "
                + turno.pregunta_especifica
            )
            turno.decision = "PREGUNTAR"
            turno.motivo_decision = (
                "Respuesta negativa vinculada al diagnóstico; solicitando hallazgo sin reiniciar el caso"
            )
            turno.pregunta_elegida = turno.respuesta_texto
            turno.intent_elegido = turno.intent_especifico.value
            turno.estado.registrar_pregunta(
                intent=turno.intent_especifico, texto=turno.pregunta_elegida, incrementar_repregunta=False
            )
            turno.es_pregunta = True
        elif turno.cat_ic in ("HERRAMIENTA_INDISPONIBLE", "NO_SABE_REALIZAR_PRUEBA", "NO_REVISADO") or (
            turno.valor_ic == "NO" and turno.campo_ic and ("disponible" in turno.campo_ic)
        ):
            turno.CompatibilidadPreguntas = _importar(
                "src.core.conversacion.compatibilidadpreguntas" if False else "src.core.conversacion.compatibilidad_preguntas"
            ).CompatibilidadPreguntas
            turno.GestorPlanB = _importar("src.core.conversacion.gestor_plan_b").GestorPlanB
            turno.dominio_actual = turno.CompatibilidadPreguntas.dominio_actual(turno.estado)
            turno.ultima_preg_txt = (
                turno.estado.ultima_pregunta().get("texto", "") if turno.estado.ultima_pregunta() else ""
            )
            turno.plan_b = turno.GestorPlanB.obtener_plan_b_por_inspeccion(
                dominio=turno.dominio_actual, ultima_preg=turno.ultima_preg_txt, estado=turno.estado
            )
            if not turno.plan_b and turno.estado.top3_actual:
                turno.top1_cand = turno.estado.top3_actual[0].get("falla", "")
                turno.plan_b = turno.GestorPlanB.obtener_plan_b_para_falla(turno.top1_cand, turno.estado)
            if turno.plan_b:
                turno.pregunta_elegida = turno.plan_b[1]
                turno.intent_elegido, turno.decision = (turno.plan_b[2].value, "PLAN_B")
                if turno.cat_ic == "NO_SABE_REALIZAR_PRUEBA":
                    turno.motivo_decision = f"Usuario no sabe realizar prueba ({turno.campo_ic}): activando alternativa observable / Plan B seguro"
                elif turno.cat_ic == "NO_REVISADO":
                    turno.motivo_decision = f"Comprobación no revisada ({turno.campo_ic}): ofreciendo alternativa observable sencilla sin herramientas"
                else:
                    turno.motivo_decision = (
                        f"Herramienta indisponible ({turno.campo_ic}): activando Plan B sensorial"
                    )
            elif turno.cat_ic in ("HERRAMIENTA_INDISPONIBLE", "NO_SABE_REALIZAR_PRUEBA"):
                turno.pregunta_elegida = (
                    "Entiendo maestro. No insistiré en esa medición técnica; mantenemos la orientación provisional "
                    "sin confirmar la hipótesis hasta una revisión presencial. ¿Prefieres realizar una inspección visual "
                    "directa sencilla sin herramientas o derivarlo a taller especializado?"
                )
                turno.intent_elegido, turno.decision = (
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS.value,
                    "PLAN_B",
                )
                turno.motivo_decision = (
                    "Sin método ni comprobación observable viable: orientando a derivación profesional"
                )
            elif turno.cat_ic == "NO_REVISADO":
                turno.detectar_areas_tecnicas = _importar(
                    "src.core.diagnostico.enrutador_sistema"
                ).detectar_areas_tecnicas
                turno.areas_actuales = turno.detectar_areas_tecnicas(
                    " ".join(turno.estado.historial_mensajes_usuario)
                )
                if "sensor_maf_lectura_anomala_reportada" in turno.estado.hechos:
                    turno.respuesta_texto = "Entiendo que no tienes la lectura. El hallazgo sigue siendo del MAF, no lo doy por confirmado ni lo cambio por MAP/STFT. Como siguiente paso, revisa conector y cableado del MAF y busca una entrada de aire no medida. ¿Encontraste conexión floja, daño o fuga visible?"
                elif turno.estado.obtener_hecho("caudal_inyectores_reportado"):
                    turno.respuesta_texto = "Entiendo que aún no tienes resultados de la comprobación. Mantengo el hallazgo de inyectores sin confirmar ni descartar la predicción ML. ¿Se comprobó el caudal/patrón de pulverización de cada inyector y su alimentación eléctrica, o solo se observó que inyectan poco?"
                elif "ADMISION_MAP" in turno.areas_actuales:
                    turno.respuesta_texto = "Queda pendiente la medición del MAP. Cuando tengas el valor de presión MAP en kPa, con la condición del motor, envíalo para continuar. La carga calculada (%) y el flujo MAF (g/s) son datos distintos. Sin esa lectura no confirmaré una causa."
                else:
                    turno.respuesta_texto = "Entendido. Sin esa lectura o comprobación no puedo confirmar una causa ni repetir hipótesis como si fueran evidencia. Dejo pendiente este mismo caso; cuando tengas el dato del área consultada, compártelo y continúo desde aquí."
                turno.decision = (
                    "PREGUNTAR"
                    if turno.estado.obtener_hecho("caudal_inyectores_reportado")
                    else "CONCLUSION_TECNICA"
                )
                turno.motivo_decision = (
                    "Medición solicitada no disponible: se conserva el caso sin volver a clasificar"
                )
        elif turno.cat_ic == "HERRAMIENTA_RECUPERADA" or (
            turno.valor_ic == "SI" and turno.campo_ic and ("disponible" in turno.campo_ic)
        ):
            if turno.campo_ic and "manometro" in turno.campo_ic:
                turno.pregunta_elegida = "Con el manómetro conectado al riel de inyección: ¿cuántos PSI marca con la llave en ON y al dar marcha?"
                turno.intent_elegido, turno.decision = (QuestionIntent.MEDICION_PRESION.value, "PREGUNTAR")
                turno.motivo_decision = (
                    "Usuario cuenta con manómetro: solicitando lectura de presión de combustible"
                )
                turno.estado.establecer_pregunta_pendiente(
                    intent=QuestionIntent.MEDICION_PRESION,
                    expected_quantity="presion_combustible",
                    expected_units=["PSI", "bar", "kPa"],
                    related_system="COMBUSTIBLE",
                )
            elif turno.campo_ic and "chispa" in turno.campo_ic:
                if "prueba_chispa" not in turno.estado.completed_tests:
                    turno.pregunta_elegida = "Con el probador de chispa conectado: ¿se observa salto constante de chispa azulada al dar arranque?"
                    turno.intent_elegido, turno.decision = (
                        QuestionIntent.COMPONENTE_REVISADO.value,
                        "PREGUNTAR",
                    )
                    turno.motivo_decision = "Usuario cuenta con probador de chispa: solicitando comprobación"
                    turno.estado.establecer_pregunta_pendiente(
                        intent=QuestionIntent.COMPONENTE_REVISADO,
                        expected_quantity="resultado_prueba_chispa",
                        related_system="ENCENDIDO",
                    )
                else:
                    turno.motivo_decision = (
                        "Prueba de chispa ya completada: evitando repetición de la comprobación"
                    )
            else:
                turno.pregunta_elegida = "Con el multímetro en tensión continua y un rango adecuado al circuito: ¿cuánto marca en reposo y a cuánto baja al dar arranque?"
                turno.intent_elegido, turno.decision = (QuestionIntent.MEDICION_VOLTAJE.value, "PREGUNTAR")
                turno.motivo_decision = "Usuario cuenta con multímetro: solicitando lectura de voltaje"
                turno.estado.establecer_pregunta_pendiente(
                    intent=QuestionIntent.MEDICION_VOLTAJE,
                    expected_quantity="voltaje_bateria",
                    expected_units=["V", "mV"],
                    related_system="ELECTRICO",
                )
        if (
            turno.pregunta_elegida
            and "probador de chispa" in turno.pregunta_elegida.lower()
            and ("prueba_chispa" in turno.estado.completed_tests)
        ):
            turno.pregunta_elegida = None
            turno.intent_elegido = None
            turno.decision = "DIAGNOSTICAR"
            turno.motivo_decision = "Prueba de chispa ya completada: pregunta repetida bloqueada"
        if turno.pregunta_elegida and turno.intent_elegido and (not turno.respuesta_texto):
            turno.estado.registrar_pregunta(
                intent=QuestionIntent(turno.intent_elegido),
                texto=turno.pregunta_elegida,
                incrementar_repregunta=False,
            )
            turno.respuesta_texto, turno.es_pregunta = (turno.pregunta_elegida, True)
        elif (
            turno.campo_ic == "medicion_presion"
            or turno.interpretacion_corta.get("unidad") in ("PSI", "bar", "kPa")
        ) and turno.interpretacion_corta.get("valor") is not None:
            turno.val = turno.interpretacion_corta.get("valor")
            turno.unidad = turno.interpretacion_corta.get("unidad", "PSI")
            turno.estado.registrar_medicion(
                "presion_combustible",
                float(turno.val),
                turno.unidad,
                contexto="riel_inyeccion",
                prueba="presion_combustible",
            )
            turno.estado.registrar_prueba_completada("presion_combustible", f"{turno.val} {turno.unidad}")
            turno.estado.limpiar_pregunta_pendiente()
            turno.escaneo_ya_realizado = bool(
                turno.estado.obtener_valor_confirmado("sin_dtc")
                or turno.estado.obtener_valor_confirmado("escaner_limpio")
                or getattr(turno.estado, "dtc_confirmados", None)
            )
            turno.chispa_ya_evaluada = bool(
                turno.estado.obtener_hecho("bujias_descartadas")
                or turno.estado.obtener_hecho("encendido_descartado")
                or (turno.estado.completed_tests and turno.estado.completed_tests.get("prueba_chispa"))
            )
            turno.es_diesel = bool(
                getattr(turno.estado, "combustible", "")
                and str(turno.estado.combustible).lower() in ("diesel", "diésel")
            )
            if turno.es_diesel:
                turno.pregunta_sug = (
                    "¿Se observa humo anómalo en el escape, o dispones de probetas para prueba de retorno de inyectores?"
                    if turno.escaneo_ya_realizado
                    else "¿Dispones de escáner para verificar códigos DTC y presión en datos en vivo?"
                )
            elif turno.chispa_ya_evaluada and turno.escaneo_ya_realizado:
                turno.pregunta_sug = "Con presión reportada y encendido revisado, sin códigos DTC, considera también admisión y compresión como hipótesis pendientes. ¿Se observa suciedad o carbón en la mariposa de admisión?"
            elif turno.chispa_ya_evaluada:
                turno.pregunta_sug = "Con el encendido descartado, ¿dispones de escáner para verificar códigos DTC o datos en vivo de sensores?"
            elif turno.escaneo_ya_realizado:
                turno.pregunta_sug = "Con el escaneo sin códigos DTC, ¿se observa salto de chispa constante y potente en las bujías al dar arranque?"
            else:
                turno.pregunta_sug = "Para continuar la comprobación, ¿se observa salto de chispa constante en las bujías o dispones de escáner para verificar códigos DTC?"
            if any(
                (
                    w in turno.norm_txt_cons
                    for w in ("empapada", "empapadas", "mojada", "mojadas", "ahogado", "ahogando")
                )
            ):
                turno.respuesta_texto = f'Registrado: {turno.val} {turno.unidad} de presión de combustible. Las bujías mojadas reportadas orientan a considerar inyector con fuga, encendido insuficiente o exceso de combustible; no confirman una causa ni descartan alimentación sin contrastar con el manual. ¿Cómo se comprobó el encendido y bajo qué condición se tomó la presión?'
            else:
                turno.respuesta_texto = f"Registrado: {turno.val} {turno.unidad} de presión de combustible en el riel. Compara este valor con la especificación de servicio del fabricante para el motor y sistema de inyección específico. {turno.pregunta_sug}"
            turno.decision = "CONCLUSION_TECNICA"
            turno.motivo_decision = (
                f"Medición de presión {turno.val} {turno.unidad} registrada y contextualizada"
            )
            turno.es_pregunta = False
        elif (resultado_lectura := evaluar_lectura(turno.estado, turno.interpretacion_corta)) is not None:
            (
                turno.decision, turno.motivo_decision, turno.respuesta_texto,
                turno.es_pregunta, turno.intent_elegido, turno.pregunta_elegida,
            ) = resultado_lectura
        elif (
            turno.campo_ic == "compresor_acopla"
            or turno.estado.obtener_valor_confirmado("compresor_acopla") == "SI"
        ):
            turno.pregunta_ac = "Confirmado: el compresor sí acopla y el embrague responde. Para verificar si hay fuga de gas o falta de intercambio de calor: ¿gira el electroventilador del condensador al encender el A/C y las tuberías del vano motor se sienten una bien fría y otra caliente?"
            turno.intent_ac = QuestionIntent.COMPONENTE_REVISADO
            turno.estado.registrar_pregunta(
                intent=turno.intent_ac, texto=turno.pregunta_ac, incrementar_repregunta=False
            )
            turno.decision = "PREGUNTAR"
            turno.motivo_decision = (
                "Compresor acopla confirmado: avanzando a electroventilador e intercambio térmico"
            )
            turno.respuesta_texto = turno.pregunta_ac
            turno.es_pregunta = True
            turno.intent_elegido = turno.intent_ac.value
            turno.pregunta_elegida = turno.pregunta_ac
        elif turno.campo_ic == "luces_se_atenuan":
            if turno.valor_ic == "SI":
                turno.respuesta_texto = "Al atenuarse fuertemente las luces del tablero al dar contacto, se produce una caída drástica de tensión. Revisa ajuste y sulfatación en bornes de batería, o prueba con cables puente."
            else:
                turno.respuesta_texto = 'La observación de luces es una pista, no una medición de voltaje ni una prueba de capacidad de batería. Mantén como alternativas conexiones, batería y circuito de arrancador/solenoide; requiere comprobación con equipo adecuado, sin puentear terminales.'
            turno.decision = "CONCLUSION_TECNICA"
            turno.motivo_decision = f"Observación de luces de tablero procesada: {turno.valor_ic}"
            turno.es_pregunta = False
