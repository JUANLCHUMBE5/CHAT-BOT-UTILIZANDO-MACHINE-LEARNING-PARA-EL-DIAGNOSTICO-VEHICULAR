"""Manejo de consultas técnicas informativas y procedimientos de comprobación paso a paso."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState, FactType
from src.core.intent_classifier import clasificar_intencion_consulta


class ManejadorConsultasTecnicas:
    """Procesa consultas técnicas puras o solicitudes de procedimientos de comprobación de taller."""

    @classmethod
    def es_consulta_o_procedimiento(cls, texto_limpio: str, estado: ConversationState) -> bool:
        """Determina si el turno es una consulta técnica pura o procedimiento paso a paso."""
        es_solicitud_detalle = ExtractorHechos.es_solicitud_detalle(texto_limpio)
        tiene_sintomas = bool(
            estado.active_symptoms
            or estado.top3_actual
            or getattr(estado, "falla_principal", None)
            or any(
                h.categoria in ("sintoma", "condicion") or h.tipo == FactType.SINTOMA
                for h in estado.hechos.values()
            )
        )
        return es_solicitud_detalle or (
            not tiene_sintomas and clasificar_intencion_consulta(texto_limpio) == "consulta_tecnica"
        )

    @classmethod
    def procesar_consulta(
        cls,
        estado: ConversationState,
        texto_limpio: str,
        gestor_diagnostico: Any,
        session_id: str,
        t0: float,
        remitente: Optional[str] = None,
        proveedor: str = "meta",
        taller_id: Optional[str] = None,
        usuario_id: Optional[str] = None,
        conversacion_id: Optional[str] = None,
        diferir_encolado_persistente: bool = False,
    ) -> Dict[str, Any]:
        """Ejecuta la consulta técnica contra el gestor y retorna la respuesta con procedimiento OEM."""
        es_solicitud_detalle = ExtractorHechos.es_solicitud_detalle(texto_limpio)
        dto_tecnico = gestor_diagnostico._procesar_consulta_tecnica(
            pregunta=texto_limpio,
            inicio_total=t0,
            remitente=remitente,
            proveedor=proveedor,
            taller_id=taller_id,
            usuario_id=usuario_id,
            conversacion_id=conversacion_id or session_id,
            slot_gemini_preconcedido=None,
            diferir_encolado_persistente=diferir_encolado_persistente,
        )
        resp_texto = getattr(dto_tecnico, "respuesta_texto", "")
        if es_solicitud_detalle and (not resp_texto or "No encontré una fuente documental" in resp_texto):
            resp_texto = cls._obtener_procedimiento_respaldo(texto_limpio.casefold())

        if resp_texto and (estado.marca or estado.modelo):
            veh_str = f"{estado.marca or ''} {estado.modelo or ''}".strip()
            lineas = []
            for linea in resp_texto.split("\n"):
                if "Modelos Compatibles Frecuentes en Peru:" in linea:
                    lineas.append(f"Vehículo en Consulta: {veh_str}")
                else:
                    lineas.append(linea)
            resp_texto = "\n".join(lineas)

        return {
            "status": "consulta_tecnica" if not es_solicitud_detalle else "solicitud_detalle",
            "respuesta_texto": resp_texto or "Información técnica.",
            "diagnostico_ml": getattr(dto_tecnico, "diagnostico_ml", "Consulta técnica"),
            "confianza_ml": getattr(dto_tecnico, "confianza_ml", 1.0),
            "fase": estado.fase.value,
            "es_pregunta": False,
            "decision": "DETALLE",
            "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
            "estado": estado,
            "dto": dto_tecnico,
        }

    @classmethod
    def _obtener_procedimiento_respaldo(cls, norm_q: str) -> str:
        if any(w in norm_q for w in ("reaprendizaje", "calibrar", "mariposa", "pedal")) and any(w in norm_q for w in ("manual", "llave", "pedal", "paso a paso", "cuerpo")):
            return (
                "🛠️ *Procedimiento de calibración y reaprendizaje de mariposa electrónica (Drive-by-Wire):*\n\n"
                "1. **Condiciones previas:** Limpieza efectuada con solvente dieléctrico; motor a temperatura normal (85 °C) y consumidores eléctricos apagados.\n"
                "2. **Reaprendizaje manual (sin escáner):** Poner contacto ON 30 segundos sin pisar el pedal; llevar a OFF 10 segundos. Poner ON 5 segundos; pisar y soltar el acelerador a fondo 5 veces en 5 segundos. Esperar 7 segundos con pedal libre; pisar a fondo durante 20 segundos hasta que la luz check engine quede fija. Soltar pedal, arrancar en ralentí y dejar estabilizar 3 minutos sin acelerar.\n"
                "3. **Con escáner:** Ingresar a 'Funciones especiales / Adaptaciones' de la ECU y ejecutar 'Reinicio de valores aprendidos de mariposa / Idle Air Volume Learn'."
            )
        if any(w in norm_q for w in ("retorno", "probetas", "probeta")) and any(w in norm_q for w in ("inyector", "inyectores", "paso a paso")):
            return (
                "🛠️ *Procedimiento de prueba de retorno de inyectores Common Rail con probetas:*\n\n"
                "1. **Instalación:** Desconectar las mangueras de retorno de los inyectores y taponar la línea de retorno común hacia el tanque. Conectar probetas graduadas individuales a cada inyector con mangueras transparentes.\n"
                "2. **Prueba en ralentí:** Arrancar el motor y medir el volumen durante 2 minutos continuos en ralentí.\n"
                "3. **Evaluación de tolerancia:** Los inyectores en buen estado entregan volúmenes homogéneos (menor a 20-25 ml en 2 min). Un inyector que exceda notablemente (ej. 60-65 ml) o triplique al promedio tiene fuga en su válvula de control y debe cambiarse o repararse."
            )
        if any(w in norm_q for w in ("contrapresion", "contrapresión", "manometro", "manómetro")) and any(w in norm_q for w in ("escape", "catalizador", "sonda", "sensor 1")):
            return (
                "🛠️ *Procedimiento para medir contrapresión de escape con manómetro:*\n\n"
                "1. **Instalación:** Con motor frío, retirar la sonda lambda primaria (sensor 1 banco 1) y enroscar el adaptador con manómetro de baja presión (0-15 PSI).\n"
                "2. **Medición en ralentí:** Arrancar el motor; la presión en ralentí debe ser inferior a 0.5 - 0.8 PSI.\n"
                "3. **Medición a 2500 RPM:** Mantener acelerado a 2500 RPM continuas; la contrapresión no debe exceder 1.5 a 2.0 PSI. Valores mayores a 2.5 PSI confirman taponamiento del convertidor catalítico."
            )
        if any(w in norm_q for w in ("inmovilizador", "transponder", "antena", "candado", "b10da")) or (
            "llave" in norm_q and not any(w in norm_q for w in ("pedal", "mariposa", "reaprendizaje", "calibrar", "acelerador"))
        ):
            return (
                "🛠️ *Procedimiento de comprobación: Sistema Inmovilizador*\n\n"
                "1. **Prueba con segunda llave:** Intentar arranque con la llave de repuesto original para descartar desprogramación o daño físico en el transponder de la llave principal.\n"
                "2. **Inspección de antena receptora:** Verificar que el aro lector alrededor de la chapa de contacto tenga continuidad, alimentación y masa firme.\n"
                "3. **Lectura en escáner:** Ingresar al módulo Inmovilizador/PATS y verificar 'Llaves programadas' y 'Estado de autorización de arranque'."
            )
        if any(w in norm_q for w in ("consumo parasito", "consumo parásito", "fuga de corriente", "multimetro", "multímetro")):
            return (
                "🛠️ *Procedimiento de comprobación: Consumo Parásito de Corriente*\n\n"
                "1. **Preparación del multímetro:** Conectar la punta roja en la escala de 10A/20A DC.\n"
                "2. **Conexión en serie:** Con motor y accesorios apagados, soltar el borne negativo (-) de la batería y colocar el multímetro en serie entre el borne de la batería y el terminal del cable.\n"
                "3. **Tiempo de reposo (Sleep Mode):** Esperar de 15 a 30 minutos con las puertas trabadas. La corriente de fuga normal no debe superar los 0.05 A (50 mA).\n"
                "4. **Aislamiento por circuito:** Si marca alto (ej. 0.85 A), retirar fusibles uno por uno hasta que la corriente caiga al rango normal."
            )
        if any(w in norm_q for w in ("solenoide", "turbo", "actuador", "vacio", "vacío", "vgt", "p0299")):
            return (
                "🛠️ *Procedimiento de comprobación: Solenoide y Actuador de Turbo*\n\n"
                "1. **Prueba del actuador de vacío:** Conectar bomba de vacío manual a la cápsula del actuador. Aplicar -15 inHg; la varilla debe desplazarse suavemente y mantener el vacío.\n"
                "2. **Comprobación de vacío de suministro:** Con motor encendido, medir la depresión en la manguera de entrada a la solenoide (mínimo -20 inHg).\n"
                "3. **Comprobación de solenoide:** Medir el vacío entregado al actuador y verificar alimentación de 12V, control PWM y resistencia eléctrica de la solenoide."
            )
        if any(w in norm_q for w in ("regulador", "presion de combustible", "presión de combustible", "diafragma", "p0172")):
            return (
                "🛠️ *Procedimiento de comprobación: Regulador de Presión de Combustible*\n\n"
                "1. **Conexión de manómetro:** Instalar manómetro de combustible en el riel de inyectores.\n"
                "2. **Prueba de vacío y diafragma:** En ralentí, desconectar la manguera de vacío del regulador; la presión en el riel debe subir entre 5 y 10 psi inmediatamente. Si la manguera de vacío gotea combustible, el diafragma interno está roto.\n"
                "3. **Prueba de retención:** Apagar el motor y observar el manómetro durante 10 minutos; la presión debe mantenerse estable."
            )
        if any(w in norm_q for w in ("embrague", "clutch", "volante", "plato opresor", "trepida")):
            return (
                "🛠️ *Procedimiento de comprobación: Embrague y Volante de Inercia*\n\n"
                "1. **Inspección del disco:** Verificar espesor de forros hasta los remaches y firmeza de resortes amortiguadores.\n"
                "2. **Planitud y alabeo del volante:** Con reloj comparador en el volante, girar manualmente el motor; el alabeo máximo no debe exceder 0.10 mm. Descartar puntos térmicos azulados.\n"
                "3. **Inspección del plato de presión:** Comprobar desgaste y altura uniforme de los dedos del diafragma."
            )
        if any(w in norm_q for w in ("reloj comparador", "alabeo", "disco", "bocin", "bocín", "manzana", "freno")):
            return (
                "🛠️ *Procedimiento de comprobación: Alabeo de Discos y Bocín/Maza*\n\n"
                "1. **Montaje del reloj comparador:** Fijar la base a la mangueta con el palpador a 10 mm del borde exterior del disco.\n"
                "2. **Medición del disco:** Girar la rueda manualmente; el salto máximo no debe superar 0.05 mm a 0.07 mm (lecturas de 0.12 mm exigen rectificado o cambio).\n"
                "3. **Comprobación del bocín:** Retirar el disco y medir directamente sobre la pestaña del bocín; el alabeo no debe exceder 0.02 mm."
            )
        if any(w in norm_q for w in ("purga", "reductor", "mangueras", "gnv", "glp")):
            return (
                "🛠️ *Procedimiento de comprobación: Circuito de Calefacción del Reductor de Gas*\n\n"
                "1. **Inspección de mangueras:** Verificar que las mangueras de agua hacia el reductor no tengan estrangulamientos ni burbujas.\n"
                "2. **Purga del sistema:** Con motor frío, retirar tapa de radiador y aflojar la manguera de retorno del reductor hasta obtener flujo continuo de refrigerante.\n"
                "3. **Verificación térmica:** Al alcanzar temperatura de trabajo, verificar al tacto que ambas mangueras del reductor se encuentren calientes."
            )
        if any(w in norm_q for w in ("termostato", "electroventilador", "refrigerante", "recalienta", "temperatura")):
            return (
                "🛠️ *Procedimiento técnico de comprobación: Sistema de Refrigeración*\n\n"
                "1. **Termostato:** Verificar la diferencia térmica al tacto entre la manguera superior e inferior del radiador al alcanzar temperatura de régimen. Si la manguera inferior permanece fría mientras el motor recalienta, el termostato está trabado cerrado.\n"
                "2. **Bomba de agua:** Con motor frío y tapa retirada, acelerar suavemente para comprobar flujo continuo en el cuello del radiador. Inspeccionar holgura en el eje de la polea y ausencia de goteo en el orificio de alivio.\n"
                "3. **Electroventilador:** Verificar encendido en baja y alta velocidad mediante escáner o activación directa por temperatura."
            )
        return (
            "🛠️ *Procedimiento técnico de comprobación:*\n\n"
            "1. Inspección física de conexiones eléctricas, mangueras y sujeciones mecánicas del componente.\n"
            "2. Medición de parámetros de funcionamiento con multímetro o escáner bajo especificación de taller.\n"
            "3. Verificación de tolerancias y pruebas de aislamiento funcional para confirmar la causa raíz."
        )
