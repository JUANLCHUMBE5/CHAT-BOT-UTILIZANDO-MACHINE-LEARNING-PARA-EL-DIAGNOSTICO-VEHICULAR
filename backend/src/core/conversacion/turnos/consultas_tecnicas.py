"""Etapa consultas tecnicas; contexto por turno."""

from __future__ import annotations

import re
import time
from importlib import import_module as _importar

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.infrastructure.rag.contrato_documental import proteger_salida_conversacional


async def consultas_tecnicas(self, turno):
    if re.search(
        "\\bpor\\s+qu[eé]\\b.{0,30}\\b(?:ocurre|pasa|recalienta|falla|se\\s+apaga|demora|vibra|corta|zapatea|se\\s+congela|congela|inyector|gas|mezcla)\\b",
        turno.norm_txt_cons,
    ):
        turno.resp_por_que = None
        if "recalienta" in turno.norm_txt_cons and any(
            (w in turno.norm_txt_cons for w in ("trafico", "tráfico", "detenido", "parado"))
        ):
            turno.resp_por_que = "💡 *Explicación técnica del comportamiento térmico:*\n\nEn carretera a velocidad sostenida, el flujo de aire natural que ingresa por la parrilla (convección dinámica) enfría el radiador de manera continua. Sin embargo, en tráfico detenido o ralentí, no existe flujo de aire exterior; el enfriamiento depende al 100% de la activación forzada del electroventilador y la circulación efectiva del refrigerante por el termostato y la bomba de agua. Si el electroventilador no enciende en su velocidad adecuada o el termostato no abre por completo, la temperatura ascenderá rápidamente hacia la zona crítica."
        elif any(
            (
                w in turno.norm_txt_cons
                for w in ("corta", "segundos", "inyeccion", "inyección", "inmovilizador", "ecu")
            )
        ):
            turno.resp_por_que = "💡 *Explicación técnica de la estrategia de inmovilizador:*\n\nAl dar arranque, la ECU permite una activación inicial de 2 a 3 segundos mientras interroga al transponder de la llave mediante la antena receptora. Si el código de seguridad no es reconocido (o arroja DTC de transponder como B10DA), la ECU corta de inmediato los pulsos de inyección y bomba de combustible como medida de seguridad antirrobo, apagando el motor."
        elif any((w in turno.norm_txt_cons for w in ("congela", "reductor", "gas", "gnv", "glp"))):
            turno.resp_por_que = "💡 *Explicación técnica de la congelación del reductor:*\n\nLa caída drástica de presión del GNV (desde 200 bar a baja presión) provoca un enfriamiento extremo por efecto Joule-Thomson. El reductor requiere circulación continua de refrigerante caliente del motor para compensar esta pérdida térmica. Si las mangueras de agua tienen aire, están obstruidas o el motor aún no alcanza temperatura, el reductor se congela y escarcha, provocando tirones severos."
        elif any((w in turno.norm_txt_cons for w in ("zapatea", "trepida", "embrague"))):
            turno.resp_por_que = "💡 *Explicación técnica de la trepidación al acoplar el embrague:*\n\nEl zapateo o trepidación al arrancar en primera ocurre por falta de contacto plano homogéneo entre el disco, el plato opresor y el volante. Esto es provocado comúnmente por alabeo o puntos térmicos en el volante de inercia, resortes amortiguadores del disco fatigados o contaminación por aceite."
        elif any((w in turno.norm_txt_cons for w in ("cascabeleo", "inyector", "subida", "pobre"))):
            turno.resp_por_que = "💡 *Explicación técnica de detonación por inyector deficiente:*\n\nBajo carga (subida empinada acelerando a fondo), el motor requiere mayor volumen de combustible para disipar calor y mantener la combustión controlada. Un inyector sucio o con bajo caudal empobrece la mezcla, elevando bruscamente la temperatura de cámara y provocando autoignición espontánea (cascabeleo o pistoneo)."
        if turno.resp_por_que:
            if turno.texto_limpio not in turno.estado.historial_mensajes_usuario:
                turno.estado.historial_mensajes_usuario.append(turno.texto_limpio)
            turno.estado.turno_actual += 1
            return {
                "status": "explicacion_causal",
                "respuesta_texto": turno.resp_por_que,
                "diagnostico_ml": turno.estado.falla_principal or "Explicación técnica",
                "confianza_ml": turno.estado.confianza_actual,
                "fase": turno.estado.fase.value,
                "es_pregunta": False,
                "decision": "EXPLICACION_CAUSAL",
                "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
                "estado": turno.estado,
            }
    if re.search(
        "\\b(?:toleran[sc]ia|alabeo\\s+m[aá]ximo|especificaci[oó]n|temperatura\\s+(?:debe\\s+abrir|de\\s+apertura))\\b",
        turno.norm_txt_cons,
    ):
        turno.corpus_val = bool(
            getattr(getattr(turno.gestor_diagnostico, "motor_rag", None), "corpus_validado", False)
        )
        ExtractorHechos.extraer_y_actualizar(turno.estado, turno.texto_limpio)
        if turno.texto_limpio not in turno.estado.historial_mensajes_usuario:
            turno.estado.historial_mensajes_usuario.append(turno.texto_limpio)
        turno.estado.turno_actual += 1
        turno.vehiculo_str = f"{getattr(turno.estado, 'marca', '') or ''} {getattr(turno.estado, 'modelo', '') or ''} {getattr(turno.estado, 'anio', '') or ''}".strip()
        turno.resp_seg, turno.conf_seg, turno.fue_interceptada = proteger_salida_conversacional(
            respuesta_propuesta="",
            vehiculo_str=turno.vehiculo_str,
            consulta_usuario=turno.texto_limpio,
            corpus_validado=turno.corpus_val,
            especificacion_autorizada=False,
        )
        return {
            "status": "tolerancia_oem"
            if turno.corpus_val and (not turno.fue_interceptada)
            else "tolerancia_no_validada",
            "respuesta_texto": turno.resp_seg,
            "diagnostico_ml": turno.estado.falla_principal or "Tolerancia OEM",
            "confianza_ml": turno.conf_seg,
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "TOLERANCIA_OEM"
            if turno.corpus_val and (not turno.fue_interceptada)
            else "ABSTENCION_OEM_TOLERANCIA",
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if re.search(
        "\\bbuj[ií]as?\\b.{0,50}\\b(?:gasolina|nafta|3\\s+electrodos)\\b.{0,50}\\bdi[eé]sel\\b|\\bdi[eé]sel\\b.{0,50}\\bbuj[ií]as?\\b.{0,50}\\b(?:gasolina|nafta|3\\s+electrodos)\\b",
        turno.norm_txt_cons,
    ) or re.search(
        "\\bbuj[ií]as?\\s+(?:de\\s+)?(?:gasolina|3\\s+electrodos)\\b.{0,50}\\bdi[eé]sel\\b",
        turno.norm_txt_cons,
    ):
        turno.resp_incomp_diesel = "🚫 *Incompatibilidad física y técnica total: Bujías de gasolina en motor diésel*\n\n• **Incompatibilidad absoluta:** Es totalmente **incompatible**. Los motores **diésel** (como el Toyota 1KD-FTV) funcionan por autoencendido por compresión y NO utilizan bujías de **chispa** ni disponen de rosca ni sistema para alojarlas.\n• **Componente del motor diésel:** Lo único que equipa son bujías de precalentamiento (calentadores o glow plugs), cuya función es exclusivamente entibiar la cámara en frío, no producir chispa."
        if turno.texto_limpio not in turno.estado.historial_mensajes_usuario:
            turno.estado.historial_mensajes_usuario.append(turno.texto_limpio)
        turno.estado.turno_actual += 1
        return {
            "status": "incompatibilidad_tecnica",
            "respuesta_texto": turno.resp_incomp_diesel,
            "diagnostico_ml": "Incompatibilidad: Bujías en motor diésel",
            "confianza_ml": float(turno.estado.confianza_actual or 0.0),
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "INCOMPATIBILIDAD_TECNICA",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if re.search(
        "\\b24\\s*v(?:oltios)?\\b.{0,60}\\b12\\s*v(?:oltios)?\\b|\\b(?:meter|conectar|probar)\\b.{0,40}\\b24\\s*v(?:oltios)?\\b.{0,50}\\balternador\\b",
        turno.norm_txt_cons,
    ):
        turno.resp_incomp_24v = "⚡ *Incompatibilidad eléctrica crítica: 24V en alternador de 12V*\n\n• **Riesgo inminente:** Conectar 24 voltios a un alternador o componente de **12V** va a **quemar** instantáneamente el regulador electrónico de voltaje y perforar los diodos rectificadores por avalancha de sobretensión.\n• **Regla de taller:** Para probar si un alternador de 12V gira o genera campo, debe alimentarse estrictamente con una fuente o batería de 12V."
        if turno.texto_limpio not in turno.estado.historial_mensajes_usuario:
            turno.estado.historial_mensajes_usuario.append(turno.texto_limpio)
        turno.estado.turno_actual += 1
        return {
            "status": "incompatibilidad_tecnica",
            "respuesta_texto": turno.resp_incomp_24v,
            "diagnostico_ml": "Incompatibilidad: 24V en sistema 12V",
            "confianza_ml": float(turno.estado.confianza_actual or 0.0),
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "INCOMPATIBILIDAD_TECNICA",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if re.search(
        "\\bpurgo\\b.{0,40}\\b(?:mangueras?|reductor|gas|gnv)\\b|\\b(?:mangueras?|reductor|gas|gnv)\\b.{0,40}\\bpurgo\\b|\\bpurga\\s+(?:de\\s+)?(?:las\\s+)?mangueras\\s+de\\s+agua\\s+del\\s+reductor\\b",
        turno.norm_txt_cons,
    ):
        turno.resp_purga_gnv = "🔧 *Procedimiento de purga de calefacción del reductor de gas GNV:*\n\nPara evitar que el **reductor** se congele por falta de circulación o bolsas de aire en el circuito de refrigerante:\n1. **Conexión en circuito:** Verificar que las **mangueras** de agua del reductor provengan de la calefacción de cabina con abrazaderas bien ajustadas.\n2. **Procedimiento de purga:** Con el motor frío y apagado, afloja la abrazadera de la manguera de retorno del reductor (la más alta). Rellena refrigerante en el radiador o depósito hasta que se complete la **purga** con un chorro continuo de refrigerante sin burbujas por la conexión.\n3. **Conexión y apriete:** Reconecta de inmediato la manguera y aprieta la abrazadera.\n4. **Encendido:** Enciende el motor hasta que alcance temperatura de régimen (85-90 °C) y confirma que ambas mangueras del reductor se sientan calientes al tacto."
        if turno.texto_limpio not in turno.estado.historial_mensajes_usuario:
            turno.estado.historial_mensajes_usuario.append(turno.texto_limpio)
        turno.estado.turno_actual += 1
        return {
            "status": "procedimiento_purga",
            "respuesta_texto": turno.resp_purga_gnv,
            "diagnostico_ml": "Procedimiento purga reductor GNV",
            "confianza_ml": float(turno.estado.confianza_actual or 0.0),
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "PROCEDIMIENTO_TECNICO",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if ExtractorHechos.es_solicitud_detalle(turno.texto_limpio) and (
        turno.estado.top3_actual or getattr(turno.estado, "falla_principal", None)
    ):
        turno.FormateadorCompacto = _importar(
            "src.core.conversacion.formateador_compacto"
        ).FormateadorCompacto
        turno.top_actual = turno.estado.top3_actual or []
        turno.falla_target = (
            turno.top_actual[0]["falla"]
            if turno.top_actual
            else turno.estado.falla_principal or "Falla mecánica bajo revisión"
        )
        turno.componentes_consulta = (
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
        for turno.patron_c, turno.falla_c in turno.componentes_consulta:
            if turno.patron_c in turno.norm_txt_cons:
                turno.falla_target = turno.falla_c
                break
        if any((w in turno.texto_limpio for w in (" 2", "segunda", "opcion 2", "opción 2"))):
            if len(turno.top_actual) > 1:
                turno.falla_target = turno.top_actual[1]["falla"]
        elif any((w in turno.texto_limpio for w in (" 3", "tercera", "opcion 3", "opción 3"))):
            if len(turno.top_actual) > 2:
                turno.falla_target = turno.top_actual[2]["falla"]
        turno.contexto_rag_detalle = ""
        if hasattr(turno.gestor_diagnostico.motor_rag, "recuperar_contexto"):
            turno.res_rag = turno.gestor_diagnostico.motor_rag.recuperar_contexto(turno.falla_target)
            if isinstance(turno.res_rag, tuple):
                turno.contexto_rag_detalle = turno.res_rag[0] or ""
            elif isinstance(turno.res_rag, str):
                turno.contexto_rag_detalle = turno.res_rag
        turno.resp_detalle = turno.FormateadorCompacto.formatear_detalle_tecnico(
            falla=turno.falla_target, procedimiento_rag=turno.contexto_rag_detalle, estado=turno.estado
        )
        return {
            "status": "detalle",
            "respuesta_texto": turno.resp_detalle,
            "diagnostico_ml": turno.falla_target,
            "confianza_ml": turno.estado.confianza_actual,
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "DETALLE",
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
