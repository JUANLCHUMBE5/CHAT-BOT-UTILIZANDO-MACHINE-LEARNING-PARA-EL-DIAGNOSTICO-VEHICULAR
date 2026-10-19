"""Interpretación de lecturas sin convertirlas en umbrales ni fallas confirmadas."""

from src.core.conversacion.models import QuestionIntent


def evaluar_lectura(estado, interpretacion):
    """Devuelve el contrato de decisión existente, o None si no es esta magnitud."""
    campo = str(interpretacion.get("campo") or "")
    valor = interpretacion.get("valor")
    if valor is None:
        return None
    if campo.startswith("medicion_voltaje"):
        recientes = {
            (m["valor"], m.get("contexto") or "condición pendiente")
            for m in estado.measurements.values()
            if m.get("unidad") == "V" and m.get("turno") == estado.turno_actual
        }
        if len(recientes) > 1:
            detalle = "; ".join(f"{v:g} V ({c})" for v, c in sorted(recientes, key=lambda x: str(x[1])))
            respuesta = (
                f"Lecturas reportadas: {detalle}. Mantengo cada condición por separado. "
                "Sin límites OEM validados no confirman ni descartan batería, alternador o arrancador/solenoide. "
                "Comprueba punto de toma, bornes, masa y consumidores antes de atribuir una causa."
            )
            return ("CONCLUSION_TECNICA", "Mediciones múltiples preservadas", respuesta, False, None, None)
        condicion = interpretacion.get("condicion_medicion") or campo.removeprefix("medicion_voltaje_")
        estado.registrar_medicion("voltaje_" + condicion, float(valor), "V", contexto=condicion, prueba="voltaje")
        if condicion == "durante_arranque":
            respuesta = (
                f"Registrado: {valor} V en arranque. Esta lectura aislada no confirma descarga, "
                "celda dañada ni defecto del arrancador. Compara con el manual aplicable y comprueba "
                "bornes, masa y caída de tensión bajo las mismas condiciones, con equipo adecuado."
            )
            return ("CONCLUSION_TECNICA", "Lectura observada sin límite OEM validado", respuesta, False, None, None)
        if condicion in ("motor_encendido", "motor_en_marcha", "carga", "ralenti"):
            respuesta = (
                f"Registrado: {valor} V con motor en marcha. No confirma por sí solo la falla del alternador. "
                "Registra consumidores, régimen y punto de toma y contrasta con el manual aplicable."
            )
            return ("CONCLUSION_TECNICA", "Lectura de carga pendiente de contraste", respuesta, False, None, None)
        contexto = "en reposo" if condicion == "reposo" else "con condición de medición pendiente de precisar"
        pregunta = (
            f"Registrado: {valor} V {contexto}; una batería nueva o bornes limpios no prueban su respuesta bajo carga. "
            "¿A cuánto desciende el multímetro mientras mantienes la llave en posición de arranque?"
        )
        intent = QuestionIntent.MEDICION_VOLTAJE
        estado.registrar_pregunta(intent=intent, texto=pregunta, incrementar_repregunta=False)
        return ("PREGUNTAR", "Falta lectura bajo carga", pregunta, True, intent.value, pregunta)
    if campo in ("medicion_alabeo_disco", "alabeo_disco") or interpretacion.get("tipo_medicion") == "alabeo_disco":
        unidad = interpretacion.get("unidad", "mm")
        estado.registrar_medicion("alabeo_disco", float(valor), unidad, contexto="disco_freno", prueba="alabeo_disco")
        estado.registrar_prueba_completada("alabeo_disco", f"{valor} {unidad}")
        estado.limpiar_pregunta_pendiente()
        respuesta = (
            f"Alabeo de disco reportado: {valor} {unidad}. No dispongo del límite OEM validado para esta variante; "
            "no autoriza rectificado ni sustitución. Verifica asiento y limpieza de la maza, montaje del instrumento "
            "y espesor remanente contra el manual aplicable. ¿Qué espesor mediste y en qué superficie tomaste el alabeo?"
        )
        return ("CONCLUSION_TECNICA", "Medición preservada sin autorización de intervención", respuesta, True, None, None)
    return None
