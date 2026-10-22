"""Orientación técnica y prudente en casos de abstención o sin hipótesis ML."""

from __future__ import annotations

import re
from typing import Any, Optional


def formatear_orientacion_abstencion(
    sintoma_original: str = "",
    estado: Optional[Any] = None,
) -> str:
    """Genera orientación técnica sin inventar porcentajes cuando el clasificador no tiene hipótesis."""
    dominio = str(getattr(estado, "dominio_probable", "") or "").upper()
    sistema = str(getattr(estado, "active_system", "") or "").lower()
    sintomas = " ".join(getattr(estado, "active_symptoms", []) or []).lower()
    pruebas = getattr(estado, "completed_tests", {}) or {}

    descripcion = f"{sintoma_original} {sintomas}".casefold()
    if (
        re.search(r"\b(?:pendientes?|subidas?|bajo carga)\b", descripcion)
        and re.search(r"\b(?:pierde|pérdida|perdida|tironea|tironeo)\b", descripcion)
    ):
        return (
            "La pérdida de fuerza bajo carga sigue pendiente de comprobación; no confirma una bomba averiada. "
            "El diferencial incluye alimentación de combustible, admisión/encendido y transmisión. "
            "El nivel del tanque no demuestra caudal ni presión suficientes. Para distinguirlas sin prueba de ruta: "
            "¿las RPM suben sin que aumente la velocidad, o también caen y el motor tironea? "
            "Conserva los datos ya reportados y verifica las pruebas específicas según el manual aplicable, "
            "sin sustituir piezas ni asumir umbrales OEM."
        )

    if sistema == "encendido" and ("tiembla" in sintomas or "misfire" in sintomas):
        return (
            "🔧 *Orientación de encendido, aún sin causa ML priorizable.* "
            "Con el temblor reportado, comprueba bujías y bobinas con una prueba "
            "de chispa adecuada y revisa el ralentí. La causa queda pendiente de "
            "medición; no atribuyo porcentaje ni confirmación física."
        )

    if dominio == "SUSPENSION" or sistema in {"suspension_direccion", "suspension"} or (
        sistema in {"", "ambiguo"}
        and re.search(r"\b(?:baches?|pistas? irregulares|golpeteo)\b", sintomas)
    ):
        return (
            "🔧 *Suspensión/dirección: sin hipótesis ML priorizable por ahora.* "
            "Si el ruido aparece en baches, realiza una inspección física "
            "de bujes, rótulas y bieletas con el vehículo asegurado; no afirmo cuál pieza falló ni "
            "atribuyo un porcentaje sin respaldo del modelo."
        )

    if dominio == "CLIMATIZACION" and pruebas.get("acople_compresor") == "SI":
        return (
            "🔧 *Sin hipótesis ML pertinente por ahora.* Ya registré que el compresor "
            "acopla; no repetiré esa prueba. El siguiente paso es comprobar si funciona "
            "el electroventilador y medir la presión del circuito con equipo adecuado "
            "según la especificación del vehículo. No atribuyo un porcentaje ni una "
            "causa sin respaldo del modelo."
        )

    if estado and (
        (
            getattr(estado, "obtener_hecho", lambda k: None)("caida_tension_excesiva")
            and estado.obtener_hecho("caida_tension_excesiva").valor == "NO"
        )
        or (
            getattr(estado, "obtener_hecho", lambda k: None)("voltaje_arranque_normal")
            and estado.obtener_hecho("voltaje_arranque_normal").valor == "SI"
        )
    ):
        v_arr = estado.obtener_hecho("medicion_voltaje_durante_arranque")
        v_arr_str = v_arr.valor if v_arr else "≥9.6 V"
        return (
            f"🔧 *Evidencia técnica registrada:* Con voltaje adecuado y {v_arr_str} al dar marcha, "
            f"la caída de tensión es normal (≥9.6 V), lo que descarta batería descargada o fuga parásita. "
            f"Para continuar la comprobación, verifique la señal en el terminal 50 del solenoide, "
            f"el relé de arranque y el estado mecánico del arrancador."
        )

    es_refrigeracion = (
        sistema in {"refrigeracion", "enfriamiento"}
        or any(k in sintomas for k in ("recalienta", "sobrecalentamiento", "hierve", "temperatura", "electroventilador", "ventilador"))
        or (
            estado
            and any(
                "refrigeracion" in str(getattr(h, "campo", "")).lower()
                or "sobrecalentamiento" in str(getattr(h, "campo", "")).lower()
                for h in (getattr(estado, "hechos", {}).values())
            )
        )
    )
    if es_refrigeracion:
        hist_str = " ".join(getattr(estado, "historial_mensajes_usuario", []) or []).lower()
        texto_eval = f"{sintomas} {hist_str} {(sintoma_original or '').lower()}"

        # Caso A: Prueba directa de 12V al electroventilador donde no gira
        probado_12v_muerto = bool(
            re.search(
                r"(?:12\s*v|directo|bater[ií]a).{0,40}(?:electro|ventilador|motor).{0,40}(?:no\s+gira|muerto|no\s+arranca|no\s+prende|no\s+activa|sin\s+respuesta|trabad|quemad)",
                texto_eval,
            )
            or re.search(
                r"(?:electro|ventilador|motor).{0,40}(?:no\s+gira|muerto|no\s+arranca|no\s+prende|no\s+activa|trabad|quemad).{0,40}(?:12\s*v|directo)",
                texto_eval,
            )
        )
        if probado_12v_muerto:
            tiene_fusible_ok = "probado_fusible" in (getattr(estado, "hechos", {}) or {}) or "fusible" in texto_eval
            detalle_fus = " (fusible y relé reportados en buen estado)" if tiene_fusible_ok else ""
            return (
                "🔧 *Orientación técnica de refrigeración (sin porcentaje SVM):*\n\n"
                f"1. **Comprobación física registrada:** Se registró la prueba directa del electroventilador con 12 V sin respuesta de giro{detalle_fus}.\n"
                "2. **Aislamiento de componentes:**\n"
                "   - *Alimentación y Masa:* Asegurar que la prueba directa a 12 V conecte positivo y masa firme directamente en los terminales del motor (o verificar continuidad a chasis en el conector) para descartar una línea de masa abierta.\n"
                "   - *Motor del electroventilador:* Con +12 V y masa presentes en sus bornes, la falta de giro apunta a falla interna en el motor (desgaste de escobillas/carbones, bobinado abierto o trabamiento del eje).\n"
                "   - *Circuito de mando:* No descartar el circuito de mando (relé, cableado y señal de ECU/sensor ECT) sin prueba de señal; al sustituir el motor, debe verificarse que el sistema de mando active el ventilador automáticamente.\n"
                "3. **Comprobación del termostato:** Comprobar la apertura del termostato según la especificación del manual de servicio del fabricante para este vehículo (verificando la reducción del diferencial térmico entre mangueras al abrir) para descartar sobrecalentamiento secundario. No asumir temperaturas genéricas sin consultar el manual OEM.\n\n"
                "⚠️ *Seguridad:* No abrir la tapa del radiador ni del depósito de expansión mientras el motor permanezca caliente por riesgo de quemaduras por vapor presurizado."
            )

        # Caso B: Electroventilador no enciende en caliente
        electro_no_activa = bool(
            re.search(r"(?:electro|ventilador).{0,40}(?:no\s+prende|no\s+activa|no\s+enciende|no\s+gira|apagado)", texto_eval)
        )
        if electro_no_activa:
            return (
                "🔧 *Orientación técnica de refrigeración (sin porcentaje SVM):*\n\n"
                "1. **Evidencia registrada:** El electroventilador no enciende al sobrepasar la temperatura de régimen normal.\n"
                "2. **Procedimiento de descarte metrológico:** Para aislar entre motor, alimentación, masa y mando: 1) Probar el motor aplicando 12 V y masa directa a sus terminales; 2) Si no gira, el motor está inoperativo; si gira, verificar fusible de potencia, relé y señal de activación de la ECU/sensor ECT en escáner.\n"
                "3. **Comprobación complementaria:** Verificar ausencia de fugas y evaluar si la manguera inferior calienta al abrir el termostato según la especificación del manual OEM.\n\n"
                "⚠️ *Seguridad:* Evite circular con temperatura elevada para proteger el empaque de culata."
            )

        # Caso C: Mangueras con diferencial térmico
        mangueras_dif = bool(
            re.search(r"(?:manguera|tubo).{0,35}(?:arriba|superior).{0,35}(?:caliente|hirviendo).{0,35}(?:abajo|inferior).{0,35}(?:fr[ií]a|tibia)", texto_eval)
            or re.search(r"(?:manguera|tubo).{0,35}(?:abajo|inferior).{0,35}(?:fr[ií]a|tibia)", texto_eval)
        )
        if mangueras_dif:
            return (
                "🔧 *Orientación técnica de refrigeración (sin porcentaje SVM):*\n\n"
                "1. **Evidencia registrada:** Manguera superior caliente con manguera inferior fría o tibia.\n"
                "2. **Conclusión técnica:** Esta disparidad térmica apunta a restricción de flujo: termostato trabado cerrado o pérdida de caudal en la bomba de agua (turbina desprendida).\n"
                "3. **Siguiente paso:** Inspeccionar la apertura del termostato o retirarlo para prueba hidrotérmica antes de reemplazar otros componentes.\n\n"
                "⚠️ *Seguridad:* Dejar enfriar el circuito antes de desacoplar mangueras o carcasas."
            )

        # Caso D: Sobrecalentamiento general
        return (
            "🔧 *Orientación técnica de refrigeración (sin porcentaje SVM):*\n\n"
            "1. **Síntoma registrado:** Sobrecalentamiento vehicular en evaluación técnica.\n"
            "2. **Puntos clave de comprobación física:** En averías térmicas no se debe emitir un diagnóstico concluyente sin descartar físicamente: a) Activación del electroventilador (o prueba directa con 12 V); b) Apertura del termostato (diferencial térmico entre mangueras); c) Fugas externas o purga de aire en el circuito.\n"
            "3. **Siguiente paso:** Aporte el resultado de la prueba del electroventilador o el estado de las mangueras para focalizar la causa.\n\n"
            "⚠️ *Seguridad:* No abrir el circuito de refrigerante presurizado en caliente."
        )

    mediciones_registradas = [
        str(h.valor) for h in getattr(estado, "hechos", {}).values()
        if getattr(h, "categoria", "") == "medicion" and getattr(h, "valor", None)
    ]
    if mediciones_registradas:
        resumen_med = ", ".join(dict.fromkeys(mediciones_registradas))
        return (
            f"Conservo las mediciones registradas ({resumen_med}). "
            "No tengo una hipótesis ML compatible con la evidencia y los descartes de este caso. "
            "Se requiere revisión técnica antes de proponer otra falla; puedes aportar el resultado de una prueba pendiente."
        )

    return (
        "No tengo una hipótesis ML compatible con la evidencia y los descartes de este caso. "
        "Conservo las comprobaciones registradas. Se requiere revisión técnica antes de "
        "proponer otra falla; puedes aportar el resultado de una prueba pendiente."
    )
