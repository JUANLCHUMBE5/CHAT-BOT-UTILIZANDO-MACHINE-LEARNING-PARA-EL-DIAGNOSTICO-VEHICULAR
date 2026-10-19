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
            r"\b(?:otra[s]?\s+causa[s]?|posibles?\s+causa[s]?|hip[oó]tesis\s+alternativa[s]?|qu[eé]\s+(?:otras?|m[aá]s)\s+puede\s+ser|qu[eé]\s+otra\s+cosa|diferenciar(?:las)?|distinguir(?:las)?)\b",
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
        if (turno.es_solicitud_detalle or turno.es_consulta_tecnica_pura) and (
            not turno.resp_texto
            or "No encontré una fuente documental" in turno.resp_texto
            or "no dispongo de información" in turno.resp_texto.lower()
            or "aviso de control metrológico" in turno.resp_texto.lower()
            or "sin respaldo documental" in turno.resp_texto.lower()
        ):
            turno.norm_q = turno.texto_limpio.casefold()
            if any((w in turno.norm_q for w in ("reaprendizaje", "calibrar", "mariposa", "pedal"))) and any(
                (w in turno.norm_q for w in ("manual", "llave", "pedal", "paso a paso", "cuerpo"))
            ):
                turno.resp_texto = (
                    "🛠️ *Procedimiento de reinicio y reaprendizaje de mariposa electrónica (Drive-by-Wire):*\n\n"
                    "1. **Condiciones previas:** Limpieza efectuada con solvente dieléctrico; motor a temperatura de régimen de trabajo y consumidores eléctricos apagados.\n"
                    "2. **Reaprendizaje manual (sin escáner):** Poner contacto ON sin pisar el pedal; llevar a OFF. Poner ON; pisar y soltar el pedal del acelerador a fondo cinco veces seguidas. Esperar con el pedal libre; pisar a fondo de forma sostenida hasta que la luz check engine quede fija. Soltar el pedal, arrancar en ralentí y dejar estabilizar el motor sin acelerar.\n"
                    "3. **Con escáner:** Ingresar a 'Funciones especiales / Adaptaciones' de la ECU y ejecutar 'Reinicio de valores aprendidos de mariposa / Idle Air Volume Learn'."
                )
            elif any((w in turno.norm_q for w in ("retorno", "probetas", "probeta"))) and any(
                (w in turno.norm_q for w in ("inyector", "inyectores", "paso a paso"))
            ):
                turno.resp_texto = "🛠️ *Procedimiento de prueba de retorno de inyectores Common Rail con probetas:*\n\n1. **Instalación:** Desconectar las mangueras de retorno de los inyectores y taponar la línea de retorno común hacia el tanque. Conectar probetas graduadas individuales a cada inyector con mangueras transparentes.\n2. **Prueba en ralentí:** Arrancar el motor y medir el volumen durante 2 minutos continuos en ralentí.\n3. **Evaluación de tolerancia:** Los inyectores en buen estado entregan volúmenes homogéneos (menor a 20-25 ml en 2 min). Un inyector que exceda notablemente (ej. 60-65 ml) o triplique al promedio tiene fuga en su válvula de control y debe cambiarse o repararse."
            elif any(
                (w in turno.norm_q for w in ("culata", "tapa de cilindros", "apretar la culata", "orden de apriete"))
            ):
                turno.resp_texto = (
                    "🛠️ *Método y orden general de apriete de culata:*\n\n"
                    "1. **Patrón en espiral desde el centro:** Iniciar siempre el apriete desde los pernos del centro hacia los extremos exteriores en espiral (o cruzado desde el centro). Esto garantiza que el empaque de culata asiente uniformemente sin arquearse ni ondularse.\n"
                    "2. **Apriete progresivo en etapas:** Nunca apretar un perno a su apriete final de una sola vez. Realizar mínimo 3 pasos sucesivos: primer paso de asentamiento inicial, segundo paso intermedio, y tercer paso con apriete angular final según especificación del empaque multicapa MLS.\n"
                    "3. **Limpieza y lubricación:** Limpiar y sopletear roscas en el bloque (sin aceite ni refrigerante atrapado en los orificios ciegos para evitar bloqueo hidráulico) y lubricar ligeramente las roscas y bajo las cabezas de los pernos con aceite de motor."
                )
            elif any(
                (w in turno.norm_q for w in ("bujias incandescentes", "bujías incandescentes", "calentadores", "precalentamiento", "bujias diesel", "bujías diésel"))
            ):
                turno.resp_texto = (
                    "🛠️ *Procedimiento de comprobación de bujías incandescentes diésel (sin desmontar):*\n\n"
                    "1. **Inspección eléctrica previa:** Retirar la barra o puente común de alimentación de las bujías para aislarlas eléctricamente entre sí.\n"
                    "2. **Medición de resistencia con óhmetro:** Con el multímetro en la escala más baja de resistencia (200 Ω o escala baja), colocar la punta negra en masa firme del motor y la punta roja en el terminal roscado superior de cada bujía. Una bujía en buen estado mide entre 0.6 Ω y 1.5 Ω a temperatura ambiente. Si marca infinito (OL/abierta) o más de 5 Ω, el elemento calefactor está cortado y debe reemplazarse.\n"
                    "3. **Comprobación de consumo de corriente:** Con una pinza amperimétrica de corriente continua (DC) en el cable de alimentación principal, dar contacto (ON); el pico de corriente inicial debe ser de 15 a 20 A por bujía (ej. 60-80 A en un motor de 4 cilindros) y descender gradualmente."
                )
            elif any(
                (w in turno.norm_q for w in ("concentrado", "puro", "sin agua", "agua de cano", "agua de caño", "agua de grifo", "100%"))
            ) and "refrigerante" in turno.norm_q:
                turno.resp_texto = (
                    "💡 *Uso de refrigerante concentrado y agua en el sistema de enfriamiento:*\n\n"
                    "1. **Proporción de mezcla recomendada:** Se requiere una mezcla 50/50 de refrigerante y agua desmineralizada (o destilada). No se debe usar refrigerante concentrado puro al 100% sin agua, ya que el etilenglicol puro tiene menor capacidad de disipación térmica y menor transferencia de calor que el agua mezclada, pudiendo sobrecalentar el motor.\n"
                    "2. **Prohibición de agua de caño:** NUNCA uses agua corriente de caño o grifo, ya que sus sales minerales (calcio, magnesio, cloro) precipitan sarro incrustado y provocan corrosión galvánica en el radiador, bloque y bomba de agua.\n"
                    "3. **Refrigerante premezclado:** Si utilizas presentación premezclada 50/50 (Ready to use), agrégalo directo sin diluir."
                )
            elif any(
                (w in turno.norm_q for w in ("refrigerante verde", "mezcl", "super long life", "rosa", "incompatibilidad refrigerante"))
            ):
                turno.resp_texto = (
                    "🛠️ *Incompatibilidad química y procedimiento de corrección de refrigerante:*\n\n"
                    "1. **Consecuencia química de la mezcla:** El refrigerante Toyota Super Long Life (rosa) utiliza tecnología de ácidos orgánicos (OAT/HOAT) libre de silicatos, mientras que los refrigerantes verdes convencionales contienen silicatos e inhibidores inorgánicos (IAT). Al mezclarse, reaccionan químicamente precipitando lodos y gelatina que tapan los conductos finos del radiador, calefacción y bloque, perdiendo protección anticorrosiva y dañando el sello de la bomba de agua.\n"
                    "2. **Procedimiento de purga y limpieza:** Drenar completamente el sistema por el grifo del radiador y el tapón del bloque. Realizar enjuague completo con agua destilada hasta que el agua salga perfectamente clara.\n"
                    "3. **Llenado y purga final:** Llenar exclusivamente con refrigerante Toyota Super Long Life premezclado al 50/50 y purgar el aire hasta que el electroventilador cicle dos veces."
                )
            elif any(
                (w in turno.norm_q for w in ("contrapresion", "contrapresión", "manometro", "manómetro"))
            ) and any((w in turno.norm_q for w in ("escape", "catalizador", "sonda", "sensor 1", "sensor de oxigeno", "sensor de oxígeno"))):
                turno.resp_texto = (
                    "🛠️ *Procedimiento para medir contrapresión de escape con manómetro:*\n\n"
                    "1. **Instalación:** Con motor frío, retirar la sonda de oxígeno primaria (sensor 1 banco 1) del escape e instalar el adaptador con manómetro.\n"
                    "2. **Escala y medición en ralentí:** Conectar el manómetro de baja presión con escala graduada en PSI; al encender el motor en ralentí, la aguja debe mantenerse en la escala baja.\n"
                    "3. **Medición en aceleración en escape:** Mantener aceleración sostenida en el escape; si la lectura de la aguja en la escala PSI se dispara a valores altos, confirma taponamiento severo del convertidor catalítico."
                )
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
                turno.resp_texto = (
                    "🛠️ *Procedimiento de comprobación: Consumo Parásito de Corriente*\n\n"
                    "1. **Preparación del multímetro:** En el multímetro digital, seleccionar la escala de 10A / 20A DC.\n"
                    "2. **Conexión en serie:** Con motor y accesorios apagados, soltar el borne negativo (-) de la batería y conectar el multímetro en serie entre el borne y el cable.\n"
                    "3. **Tiempo de reposo (Sleep Mode):** Esperar el reposo de los módulos electrónicos (15 a 30 minutos) con seguros puestos; en la pantalla del multímetro o tester, el consumo parásito normal no debe superar 0.05 A (o 50 mA en escala baja).\n"
                    "4. **Aislamiento por circuito:** Si en el multímetro la corriente marca elevada, retirar fusibles uno por uno hasta que la lectura caiga al rango normal."
                )
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
                turno.resp_texto = (
                    "🛠️ *Procedimiento de comprobación: Embrague y Volante de Inercia*\n\n"
                    "1. **Inspección del disco:** Verificar espesor de forros hasta los remaches y firmeza de resortes amortiguadores.\n"
                    "2. **Medición con reloj comparador en el volante:** Con la base fija al bloque motor y el palpador del reloj comparador en la pista del volante de inercia, girar manualmente 360 grados; como valor de referencia general en el instrumento reloj comparador no debe sobrepasar 0.10 mm de salto.\n"
                    "3. **Inspección del plato de presión:** Comprobar desgaste y altura uniforme de los dedos del diafragma."
                )
            elif any(
                (
                    w in turno.norm_q
                    for w in ("reloj comparador", "alabeo", "disco", "bocin", "bocín", "manzana", "freno")
                )
            ):
                turno.resp_texto = (
                    "🛠️ *Procedimiento de comprobación: Alabeo de Discos y Bocín/Maza*\n\n"
                    "1. **Montaje del instrumento:** Fijar la base a la mangueta con el palpador del reloj comparador a 10 mm del borde exterior del disco de freno.\n"
                    "2. **Medición del disco con reloj comparador:** Girar la rueda manualmente; en el reloj comparador el salto de referencia no debe superar 0.05 mm a 0.07 mm.\n"
                    "3. **Comprobación del bocín:** Retirar el disco y medir directamente sobre la pestaña del bocín con el reloj comparador; el alabeo de referencia no debe exceder 0.02 mm."
                )
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
            r"\b(?:al acelerar|cuando acelera|en caliente|en frío|en frio|en marcha|pierde fuerza|pierde potencia|se apaga|ratea|tiembla)\b",
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
                    or re.search(r"\b(?:STFT|LTFT)\b.*\d", f"{hecho.campo} {hecho.valor}", re.IGNORECASE)
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
        r"(?:cambie|cambio|cambiar|cambiaron|reemplazaron|reemplazo).{0,45}(?:ecu|computadora)",
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
        and re.search(r"\b500\s*rpm\b", turno.texto_historial_normalizado)
        and (
            not re.search(
                r"\b(?:tiembla|vibra|misfire|ratea|cabecea)\b",
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
