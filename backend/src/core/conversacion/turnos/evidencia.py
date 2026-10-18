"""Etapa evidencia; contexto por turno."""

from __future__ import annotations

import re
import time
from importlib import import_module as _importar

from src.core.conversacion.control_aclaraciones import (
    dato_desconocido,
    debe_avanzar,
    desconocidos_consecutivos,
    hay_evidencia_diagnostica,
)
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.models import FactState, FactType
from src.core.conversacion.suficiencia_informacion import EvaluadorSuficiencia


async def evidencia(self, turno):
    turno.es_solicitud_detalle = ExtractorHechos.es_solicitud_detalle(turno.texto_limpio)
    turno.clasificar_intencion_consulta = _importar(
        "src.core.intent_classifier"
    ).clasificar_intencion_consulta
    turno.es_consulta_tecnica = turno.clasificar_intencion_consulta(turno.texto_limpio) == "consulta_tecnica"
    turno.solicita_alternativas = bool(
        turno.interp_semantica
        and turno.interp_semantica.solicita_causas_alternativas
        or re.search(
            "\\b(?:otra[s]?\\s+causa[s]?|posibles?\\s+causa[s]?|hip[oó]tesis\\s+alternativa[s]?|qu[eé]\\s+(?:otras?|m[aá]s)\\s+puede\\s+ser|qu[eé]\\s+otra\\s+cosa|diferenciar(?:las)?|distinguir(?:las)?)\\b",
            turno.texto_limpio,
            re.IGNORECASE,
        )
    )
    turno.tiene_evidencia_mixta = bool(
        turno.hechos_extraidos
        and any(
            (
                isinstance(h, dict)
                and h.get("categoria")
                in ("sintoma", "medicion", "condicion", "comprobacion", "componente_reemplazado")
                for h in turno.hechos_extraidos
            )
        )
    )
    turno.tiene_caso_activo = bool(
        turno.estado.top3_actual
        or getattr(turno.estado, "falla_principal", None)
        or turno.estado.hechos
        or turno.estado.active_symptoms
    )
    turno.es_consulta_tecnica_pura = (
        turno.es_consulta_tecnica
        and (not turno.solicita_alternativas)
        and (not turno.tiene_evidencia_mixta)
        and (not turno.tiene_caso_activo)
    )
    if turno.es_solicitud_detalle or turno.es_consulta_tecnica_pura:
        turno.dto_tecnico = turno.gestor_diagnostico._procesar_consulta_tecnica(
            pregunta=turno.texto_limpio,
            inicio_total=turno.t0,
            remitente=turno.remitente,
            proveedor=turno.proveedor,
            taller_id=turno.taller_id,
            usuario_id=turno.usuario_id,
            conversacion_id=turno.conversacion_id or turno.session_id,
            slot_gemini_preconcedido=None,
            diferir_encolado_persistente=turno.diferir_encolado_persistente,
        )
        turno.resp_texto = getattr(turno.dto_tecnico, "respuesta_texto", "")
        if turno.es_solicitud_detalle and (
            not turno.resp_texto or "No encontré una fuente documental" in turno.resp_texto
        ):
            turno.norm_q = turno.texto_limpio.casefold()
            if any((w in turno.norm_q for w in ("reaprendizaje", "calibrar", "mariposa", "pedal"))) and any(
                (w in turno.norm_q for w in ("manual", "llave", "pedal", "paso a paso", "cuerpo"))
            ):
                turno.resp_texto = "🛠️ *Procedimiento de calibración y reaprendizaje de mariposa electrónica (Drive-by-Wire):*\n\n1. **Condiciones previas:** Limpieza efectuada con solvente dieléctrico; motor a temperatura normal (85 °C) y consumidores eléctricos apagados.\n2. **Reaprendizaje manual (sin escáner):** Poner contacto ON 30 segundos sin pisar el pedal; llevar a OFF 10 segundos. Poner ON 5 segundos; pisar y soltar el acelerador a fondo 5 veces en 5 segundos. Esperar 7 segundos con pedal libre; pisar a fondo durante 20 segundos hasta que la luz check engine quede fija. Soltar pedal, arrancar en ralentí y dejar estabilizar 3 minutos sin acelerar.\n3. **Con escáner:** Ingresar a 'Funciones especiales / Adaptaciones' de la ECU y ejecutar 'Reinicio de valores aprendidos de mariposa / Idle Air Volume Learn'."
            elif any((w in turno.norm_q for w in ("retorno", "probetas", "probeta"))) and any(
                (w in turno.norm_q for w in ("inyector", "inyectores", "paso a paso"))
            ):
                turno.resp_texto = "🛠️ *Procedimiento de prueba de retorno de inyectores Common Rail con probetas:*\n\n1. **Instalación:** Desconectar las mangueras de retorno de los inyectores y taponar la línea de retorno común hacia el tanque. Conectar probetas graduadas individuales a cada inyector con mangueras transparentes.\n2. **Prueba en ralentí:** Arrancar el motor y medir el volumen durante 2 minutos continuos en ralentí.\n3. **Evaluación de tolerancia:** Los inyectores en buen estado entregan volúmenes homogéneos (menor a 20-25 ml en 2 min). Un inyector que exceda notablemente (ej. 60-65 ml) o triplique al promedio tiene fuga en su válvula de control y debe cambiarse o repararse."
            elif any(
                (w in turno.norm_q for w in ("contrapresion", "contrapresión", "manometro", "manómetro"))
            ) and any((w in turno.norm_q for w in ("escape", "catalizador", "sonda", "sensor 1"))):
                turno.resp_texto = "🛠️ *Procedimiento para medir contrapresión de escape con manómetro:*\n\n1. **Instalación:** Con motor frío, retirar la sonda lambda primaria (sensor 1 banco 1) y enroscar el adaptador con manómetro de baja presión (0-15 PSI).\n2. **Medición en ralentí:** Arrancar el motor; la presión en ralentí debe ser inferior a 0.5 - 0.8 PSI.\n3. **Medición a 2500 RPM:** Mantener acelerado a 2500 RPM continuas; la contrapresión no debe exceder 1.5 a 2.0 PSI. Valores mayores a 2.5 PSI confirman taponamiento del convertidor catalítico."
            elif any(
                (w in turno.norm_q for w in ("inmovilizador", "transponder", "antena", "candado", "b10da"))
            ) or (
                "llave" in turno.norm_q
                and (
                    not any(
                        (
                            w in turno.norm_q
                            for w in ("pedal", "mariposa", "reaprendizaje", "calibrar", "acelerador")
                        )
                    )
                )
            ):
                turno.resp_texto = "🛠️ *Procedimiento de comprobación: Sistema Inmovilizador*\n\n1. **Prueba con segunda llave:** Intentar arranque con la llave de repuesto original para descartar desprogramación o daño físico en el transponder de la llave principal.\n2. **Inspección de antena receptora:** Verificar que el aro lector alrededor de la chapa de contacto tenga continuidad, alimentación y masa firme.\n3. **Lectura en escáner:** Ingresar al módulo Inmovilizador/PATS y verificar 'Llaves programadas' y 'Estado de autorización de arranque'."
            elif any(
                (
                    w in turno.norm_q
                    for w in (
                        "consumo parasito",
                        "consumo parásito",
                        "fuga de corriente",
                        "multimetro",
                        "multímetro",
                    )
                )
            ):
                turno.resp_texto = "🛠️ *Procedimiento de comprobación: Consumo Parásito de Corriente*\n\n1. **Preparación del multímetro:** Conectar la punta roja en la escala de 10A/20A DC.\n2. **Conexión en serie:** Con motor y accesorios apagados, soltar el borne negativo (-) de la batería y colocar el multímetro en serie entre el borne de la batería y el terminal del cable.\n3. **Tiempo de reposo (Sleep Mode):** Esperar de 15 a 30 minutos con las puertas trabadas. La corriente de fuga normal no debe superar los 0.05 A (50 mA).\n4. **Aislamiento por circuito:** Si marca alto (ej. 0.85 A), retirar fusibles uno por uno hasta que la corriente caiga al rango normal."
            elif any(
                (
                    w in turno.norm_q
                    for w in ("solenoide", "turbo", "actuador", "vacio", "vacío", "vgt", "p0299")
                )
            ):
                turno.resp_texto = "🛠️ *Procedimiento de comprobación: Solenoide y Actuador de Turbo*\n\n1. **Prueba del actuador de vacío:** Conectar bomba de vacío manual a la cápsula del actuador. Aplicar -15 inHg; la varilla debe desplazarse suavemente y mantener el vacío.\n2. **Comprobación de vacío de suministro:** Con motor encendido, medir la depresión en la manguera de entrada a la solenoide (mínimo -20 inHg).\n3. **Comprobación de solenoide:** Medir el vacío entregado al actuador y verificar alimentación de 12V, control PWM y resistencia eléctrica de la solenoide."
            elif any(
                (
                    w in turno.norm_q
                    for w in (
                        "regulador",
                        "presion de combustible",
                        "presión de combustible",
                        "diafragma",
                        "p0172",
                    )
                )
            ):
                turno.resp_texto = "🛠️ *Procedimiento de comprobación: Regulador de Presión de Combustible*\n\n1. **Conexión de manómetro:** Instalar manómetro de combustible en el riel de inyectores.\n2. **Prueba de vacío y diafragma:** En ralentí, desconectar la manguera de vacío del regulador; la presión en el riel debe subir entre 5 y 10 psi inmediatamente. Si la manguera de vacío gotea combustible, el diafragma interno está roto.\n3. **Prueba de retención:** Apagar el motor y observar el manómetro durante 10 minutos; la presión debe mantenerse estable."
            elif any(
                (w in turno.norm_q for w in ("embrague", "clutch", "volante", "plato opresor", "trepida"))
            ):
                turno.resp_texto = "🛠️ *Procedimiento de comprobación: Embrague y Volante de Inercia*\n\n1. **Inspección del disco:** Verificar espesor de forros hasta los remaches y firmeza de resortes amortiguadores.\n2. **Planitud y alabeo del volante:** Con reloj comparador en el volante, girar manualmente el motor; el alabeo máximo no debe exceder 0.10 mm. Descartar puntos térmicos azulados.\n3. **Inspección del plato de presión:** Comprobar desgaste y altura uniforme de los dedos del diafragma."
            elif any(
                (
                    w in turno.norm_q
                    for w in ("reloj comparador", "alabeo", "disco", "bocin", "bocín", "manzana", "freno")
                )
            ):
                turno.resp_texto = "🛠️ *Procedimiento de comprobación: Alabeo de Discos y Bocín/Maza*\n\n1. **Montaje del reloj comparador:** Fijar la base a la mangueta con el palpador a 10 mm del borde exterior del disco.\n2. **Medición del disco:** Girar la rueda manualmente; el salto máximo no debe superar 0.05 mm a 0.07 mm (lecturas de 0.12 mm exigen rectificado o cambio).\n3. **Comprobación del bocín:** Retirar el disco y medir directamente sobre la pestaña del bocín; el alabeo no debe exceder 0.02 mm."
            elif any((w in turno.norm_q for w in ("purga", "reductor", "mangueras", "gnv", "glp"))):
                turno.resp_texto = "🛠️ *Procedimiento de comprobación: Circuito de Calefacción del Reductor de Gas*\n\n1. **Inspección de mangueras:** Verificar que las mangueras de agua hacia el reductor no tengan estrangulamientos ni burbujas.\n2. **Purga del sistema:** Con motor frío, retirar tapa de radiador y aflojar la manguera de retorno del reductor hasta obtener flujo continuo de refrigerante.\n3. **Verificación térmica:** Al alcanzar temperatura de trabajo, verificar al tacto que ambas mangueras del reductor se encuentren calientes."
            elif any(
                (
                    w in turno.norm_q
                    for w in ("termostato", "electroventilador", "refrigerante", "recalienta", "temperatura")
                )
            ):
                turno.resp_texto = "🛠️ *Procedimiento técnico de comprobación: Sistema de Refrigeración*\n\n1. **Termostato:** Verificar la diferencia térmica al tacto entre la manguera superior e inferior del radiador al alcanzar temperatura de régimen. Si la manguera inferior permanece fría mientras el motor recalienta, el termostato está trabado cerrado.\n2. **Bomba de agua:** Con motor frío y tapa retirada, acelerar suavemente para comprobar flujo continuo en el cuello del radiador. Inspeccionar holgura en el eje de la polea y ausencia de goteo en el orificio de alivio.\n3. **Electroventilador:** Verificar encendido en baja y alta velocidad mediante escáner o activación directa por temperatura."
            else:
                turno.resp_texto = "🛠️ *Procedimiento técnico de comprobación:*\n\n1. Inspección física de conexiones eléctricas, mangueras y sujeciones mecánicas del componente.\n2. Medición de parámetros de funcionamiento con multímetro o escáner bajo especificación de taller.\n3. Verificación de tolerancias y pruebas de aislamiento funcional para confirmar la causa raíz."
        turno.resp_texto = turno.PoliticaSeguridad.enriquecer_respuesta_seguridad(
            turno.resp_texto or "Información técnica.",
            turno.texto_limpio,
            diagnostico_ml=getattr(turno.dto_tecnico, "diagnostico_ml", "Consulta técnica"),
            estado=turno.estado,
        )
        await self.repositorio.save_session(turno.session_id, turno.estado)
        return {
            "status": "consulta_tecnica" if not turno.es_solicitud_detalle else "solicitud_detalle",
            "respuesta_texto": turno.resp_texto,
            "diagnostico_ml": getattr(turno.dto_tecnico, "diagnostico_ml", "Consulta técnica"),
            "confianza_ml": getattr(turno.dto_tecnico, "confianza_ml", 1.0),
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "DETALLE",
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
            "dto": turno.dto_tecnico,
        }
    if turno.estado.preguntas_realizadas:
        turno.interp_str = (
            turno.interpretacion_corta.get("valor") if turno.interpretacion_corta else None
        ) or "respuesta_usuario"
        turno.estado.registrar_respuesta(turno.texto_limpio, turno.interp_str)
    if turno.placa and turno.placa not in ("REST-API", "WAPP-01", "DESCONOCIDO"):
        turno.estado.placa = turno.placa
    if turno.marca_modelo and turno.marca_modelo not in (
        "Vehiculo Generico",
        "Generico Generico",
        "Generico",
        "",
    ):
        turno.partes_mm = turno.marca_modelo.split()
        if len(turno.partes_mm) >= 1 and (not turno.estado.marca):
            turno.estado.marca = turno.partes_mm[0]
            turno.estado.registrar_hecho(
                "marca",
                turno.partes_mm[0],
                categoria="vehiculo",
                texto_crudo=turno.marca_modelo,
                tipo=FactType.CONDICION,
            )
        if len(turno.partes_mm) >= 2 and (not turno.estado.modelo):
            turno.estado.modelo = " ".join(turno.partes_mm[1:])
            turno.estado.registrar_hecho(
                "modelo",
                " ".join(turno.partes_mm[1:]),
                categoria="vehiculo",
                texto_crudo=turno.marca_modelo,
                tipo=FactType.CONDICION,
            )
    turno.score, turno.categorias_vistas, turno.es_suficiente, turno.motivo_suficiencia = (
        EvaluadorSuficiencia.evaluar(turno.estado)
    )
    if turno.interp_semantica and turno.interp_semantica.solicita_causas_alternativas:
        turno.es_suficiente = True
        turno.motivo_suficiencia = "Mecánico solicita hipótesis diferenciales y causas alternativas"
    turno.medicion_area_pendiente = GeneradorPreguntas.falta_medicion_discriminante_por_area(turno.estado)
    if (
        turno.medicion_area_pendiente
        and turno.estado.active_system == "combustible_admision"
        and turno.estado.ya_preguntado_texto("STFT/LTFT")
        and re.search(
            "\\b(?:al acelerar|cuando acelera|en caliente|en frío|en frio|en marcha|pierde fuerza|pierde potencia|se apaga|ratea|tiembla)\\b",
            turno.texto_limpio,
            re.IGNORECASE,
        )
    ):
        turno.medicion_area_pendiente = False
        turno.es_suficiente = True
        turno.motivo_suficiencia = "Se solicitó DTC/STFT una vez y se recibió contexto operativo; continuar con diagnóstico orientativo sin confirmar una causa"
    if (
        turno.estado.obtener_hecho("revision_concreta_mezcla")
        and (not turno.estado.obtener_hecho("caudal_inyectores_reportado"))
        and (
            not any(
                (
                    hecho.categoria == "dtc"
                    or re.search("\\b(?:STFT|LTFT)\\b.*\\d", f"{hecho.campo} {hecho.valor}", re.IGNORECASE)
                    for hecho in turno.estado.hechos.values()
                )
            )
        )
    ):
        turno.es_suficiente = False
        turno.motivo_suficiencia = (
            "Revisión concreta registrada: avanzar a otra comprobación del mismo sistema"
        )
    turno.texto_historial_normalizado = " ".join(turno.estado.historial_mensajes_usuario).lower()
    if turno.estado.active_system == "electrico_ecu" and re.search(
        "(?:cambie|cambio|cambiar|cambiaron|reemplazaron|reemplazo).{0,45}(?:ecu|computadora)",
        turno.texto_historial_normalizado,
    ):
        turno.es_suficiente = False
        turno.motivo_suficiencia = (
            "Antecedente de reemplazo ECU y error de codificación requiere comprobación específica"
        )
    if "sensor_maf_lectura_anomala_reportada" in turno.estado.hechos:
        turno.es_suficiente = False
        turno.motivo_suficiencia = "Hallazgo MAF explícito requiere seguimiento específico del sensor"
    if (
        turno.estado.active_system == "ambiguo"
        and re.search("\\b500\\s*rpm\\b", turno.texto_historial_normalizado)
        and (
            not re.search(
                "\\b(?:tiembla|vibra|misfire|ratea|cabecea)\\b",
                " ".join(turno.estado.historial_mensajes_usuario).lower(),
            )
        )
    ):
        turno.es_suficiente = False
        turno.motivo_suficiencia = (
            "RPM baja sin síntomas discriminantes: solicitar contexto antes de clasificar"
        )
    if turno.medicion_area_pendiente:
        turno.es_suficiente = False
        turno.motivo_suficiencia = (
            "Falta la lectura técnica mínima para confirmar la ruta explícita de mezcla o MAP"
        )
    turno.forzar_avance = debe_avanzar(turno.estado, turno.texto_limpio)
    turno.sin_evidencia = not hay_evidencia_diagnostica(turno.estado)
    if turno.sin_evidencia and dato_desconocido(turno.texto_limpio):
        turno.forzar_avance = desconocidos_consecutivos(turno.estado) >= max(
            1, turno.estado.max_repreguntas - 1
        )
    if turno.forzar_avance and dato_desconocido(turno.texto_limpio):
        turno.estado.registrar_hecho(
            "dato_solicitado_desconocido",
            "DESCONOCIDO",
            categoria="flujo",
            estado=FactState.NO_REVISADO,
            texto_crudo=turno.texto_limpio,
            tipo=FactType.CONDICION,
        )
