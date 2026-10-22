"""Verificación de hechos conocidos y precondiciones de preguntas automotrices."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional, Tuple

from src.core.conversacion.diccionario_automotriz import normalizar_jerga_automotriz
from src.core.conversacion.models import (
    DtcStatus,
    EstadoOperativo,
    FactState,
    QuestionIntent,
)

if TYPE_CHECKING:
    from src.core.conversacion.models import ConversationState


def permite_caracterizar_ruido_suspension(
    estado: ConversationState,
    texto_pregunta: Optional[str] = None,
) -> bool:
    """Permite precisar un ruido ya reportado, sin repetir una pregunta de presencia."""
    condicion = str(estado.obtener_valor_confirmado("condicion_operacion") or "").lower()
    dominio = str(getattr(estado, "dominio_probable", "") or "").upper()
    condicion_bache = "bache" in condicion or "irregular" in condicion
    if dominio != "SUSPENSION" or not condicion_bache:
        return False
    if estado.ya_preguntado(QuestionIntent.PRESENCIA_RUIDO):
        return False
    if texto_pregunta is None:
        return True

    texto = texto_pregunta.lower()
    return any(
        marcador in texto
        for marcador in ("golpe seco", "rebote", "cascabeleo", "crujido al comprimir")
    )


def already_known(intent: QuestionIntent, estado: ConversationState) -> bool:
    """Determina si la información requerida ya está confirmada o abordada en el estado conversacional."""
    if intent in (
        QuestionIntent.TEMPERATURA_APARICION,
        QuestionIntent.TEMPERATURA_MOTOR_EN_MARCHA,
        QuestionIntent.TEMPERATURA_AMBIENTAL_ARRANQUE,
    ):
        return (
            estado.obtener_hecho("temperatura") is not None
            or estado.obtener_hecho("temperatura_arranque") is not None
            or any(h.categoria == "temperatura" for h in estado.hechos.values())
            or estado.ya_preguntado(QuestionIntent.TEMPERATURA_APARICION)
        )

    if intent == QuestionIntent.CONDICION_OPERACION:
        if estado.estado_operativo in (
            EstadoOperativo.ARRANQUE,
            EstadoOperativo.RALENTI,
            EstadoOperativo.MARCHA,
            EstadoOperativo.FRENADO,
            EstadoOperativo.ESTACIONADO,
        ):
            return True
        return (
            estado.obtener_hecho("condicion_operacion") is not None
            or any(
                w in str(h.valor).lower()
                for h in estado.hechos.values()
                if h.categoria == "condicion"
                for w in ("ralenti", "ralentí", "en_marcha", "acelerar", "frenado")
            )
            or estado.ya_preguntado(QuestionIntent.CONDICION_OPERACION)
        )

    if intent in (QuestionIntent.COMPORTAMIENTO_ARRANQUE, QuestionIntent.CAIDA_TENSION_ARRANQUE):
        return bool(
            estado.obtener_hecho("giro_motor") is not None
            and estado.obtener_hecho("luces_se_atenuan") is not None
        )

    if intent == QuestionIntent.ACLARACION_CONTRADICCION:
        return estado.ya_preguntado(QuestionIntent.ACLARACION_CONTRADICCION)

    if intent == QuestionIntent.CODIGO_DTC:
        return (
            estado.dtc_status in (DtcStatus.DTC_OBSERVADO, DtcStatus.DTC_DESCONOCIDO, DtcStatus.DTC_AUSENTE)
            or any(h.categoria == "dtc" for h in estado.hechos.values())
            or estado.obtener_hecho("sin_dtc") is not None
            or estado.obtener_hecho("sin_dtc_reportado") is not None
            or estado.obtener_hecho("escaner_limpio") is not None
            or any("sin_dtc" in k.lower() or "escaner_limpio" in k.lower() for k in estado.hechos.keys())
            or estado.obtener_hecho("sintoma_testigo_check_engine") is not None
            or estado.obtener_hecho("codigo_dtc") is not None
            or estado.obtener_hecho("escaner_disponible") is not None
            or any("check" in k.lower() or "testigo" in k.lower() for k in estado.hechos.keys())
            or estado.ya_preguntado(QuestionIntent.CODIGO_DTC)
        )

    if intent == QuestionIntent.COMPONENTE_REVISADO:
        return any(
            h.categoria in ("componente_descartado", "antecedente", "inspeccion")
            and h.estado == FactState.CONFIRMADO
            for h in estado.hechos.values()
        )

    if intent == QuestionIntent.PRESENCIA_RUIDO:
        return (
            estado.obtener_hecho("ruido_anomalo") is not None
            or any("ruido" in k.lower() for k in estado.hechos.keys())
            or estado.ya_preguntado(QuestionIntent.PRESENCIA_RUIDO)
        )

    if intent == QuestionIntent.DISPONIBILIDAD_HERRAMIENTA:
        return bool(
            estado.tools_available
            or estado.tools_unavailable
            or estado.herramientas_no_disponibles
            or any(h.categoria == "herramienta" for h in estado.hechos.values())
            or estado.ya_preguntado(QuestionIntent.DISPONIBILIDAD_HERRAMIENTA)
        )

    if intent in (QuestionIntent.MEDICION_VOLTAJE, QuestionIntent.MEDICION_PRESION, QuestionIntent.MEDICION_TECNICA):
        return bool(
            estado.measurements
            or any(h.categoria == "medicion" for h in estado.hechos.values())
            or (intent == QuestionIntent.MEDICION_VOLTAJE and "multimetro" in estado.herramientas_no_disponibles)
            or (intent == QuestionIntent.MEDICION_PRESION and "manometro" in estado.herramientas_no_disponibles)
        )

    return False


def pregunta_por_area(
    estado: ConversationState,
) -> Optional[Tuple[str, QuestionIntent]]:
    """Elige una pregunta técnica del área explícita antes de preguntas genéricas."""
    from src.core.diagnostico.enrutador_sistema import detectar_areas_tecnicas

    from src.core.conversacion.evidencia_observada import pregunta_observacion, subsistema_observado

    pregunta_especifica = pregunta_observacion(estado)
    if pregunta_especifica and not any(
        p.get("texto") == pregunta_especifica for p in estado.preguntas_realizadas
    ):
        sistema = next((s for texto in reversed(estado.historial_mensajes_usuario)
                        if (s := subsistema_observado(texto))), None)
        intent = (QuestionIntent.CONDICION_OPERACION if sistema in (None, "direccion")
                  else QuestionIntent.MEDICION_TECNICA)
        return pregunta_especifica, intent

    historial_original = " ".join(estado.historial_mensajes_usuario).lower()
    historial = normalizar_jerga_automotriz(historial_original)
    areas = detectar_areas_tecnicas(historial)
    texto = historial.lower()
    mediciones = " ".join(
        f"{getattr(hecho, 'campo', '')} {getattr(hecho, 'valor', '')}"
        for hecho in estado.hechos.values()
        if getattr(hecho, "categoria", "") == "medicion"
    ).lower()
    pregunta_anterior = (estado.ultima_pregunta() or {}).get("texto", "").lower()

    if (
        estado.active_system == "refrigeracion"
        and len(estado.historial_mensajes_usuario) == 1
        and re.fullmatch(r"\s*(?:se\s+)?calienta\s*", historial_original)
    ):
        return (
            "¿Se calienta detenido en ralentí, en carretera o en ambas condiciones?",
            QuestionIntent.CONDICION_OPERACION,
        )

    if (
        estado.active_system == "ambiguo"
        and re.search(r"\bno\s+tiembla\b", historial_original)
        and re.search(r"\b(?:minimo\s+bajo|ralenti\s+bajo|500\s*rpm)\b", historial_original)
    ):
        return (
            "Entendido: no hay temblor y el mínimo está bajo. ¿El ralentí se mantiene estable, "
            "fluctúa o llega a apagarse?",
            QuestionIntent.MEDICION_TECNICA,
        )

    if (
        estado.active_system == "ambiguo"
        and re.search(r"\b500\s*rpm\b", historial_original)
        and not re.search(r"\b(?:tiembla|vibra|misfire|ratea|cabecea)\b", historial_original)
    ):
        return (
            "500 RPM por sí solo no identifica la causa. ¿El motor tiembla, fluctúa o se apaga, "
            "o solo mantiene el mínimo bajo? ¿Hay testigo Check Engine?",
            QuestionIntent.MEDICION_TECNICA,
        )

    correccion_mezcla_en_refrigeracion = (
        estado.active_system == "refrigeracion"
        and re.search(r"\bno\s+(?:es\s+)?(?:de\s+)?(?:me|mes)cla\b", texto)
    )
    if correccion_mezcla_en_refrigeracion:
        return (
            "Entendido: seguimos en refrigeración. ¿El electroventilador del radiador se activa "
            "cuando la temperatura empieza a subir en tráfico?",
            QuestionIntent.TEMPERATURA_MOTOR_EN_MARCHA,
        )

    if not areas and estado.active_system != "electrico_ecu":
        return None

    if any(
        campo == "sensor_maf_lectura_anomala_reportada"
        for campo in estado.hechos
    ) or re.search(r"\bmaf\b.{0,55}\b(?:lecturas? raras?|valores? raros?|no mide bien)\b", texto):
        return (
            "El hallazgo apunta al sensor MAF. ¿Qué lectura de flujo de aire muestra el escáner "
            "en datos en vivo y en qué condición del motor?",
            QuestionIntent.MEDICION_TECNICA,
        )

    if "ELECTRICO_ECU" in areas and re.search(
        r"(?:cambie|cambio|cambiar|cambiaron|reemplazaron|reemplazo).{0,45}(?:ecu|computadora)|"
        r"(?:error|falla)\s+(?:de\s+)?codificaci[oón]",
        texto,
    ):
        if estado.ya_preguntado_texto("qué mensaje/código exacto aparece al codificar"):
            if re.search(r"error\s+(?:de\s+)?codificaci[oón]", estado.historial_mensajes_usuario[-1]):
                return (
                    "Ya indicaste que el escáner se comunica y reporta codificación. "
                    "¿Cuál es el código o texto exacto de ese error?",
                    QuestionIntent.MEDICION_TECNICA,
                )
            return None
        return (
            "Ese antecedente orienta a verificar compatibilidad del número de parte, codificación "
            "y aprendizaje del inmovilizador; no confirma que la ECU esté dañada. ¿El número de "
            "parte coincide con el vehículo y qué mensaje/código exacto aparece al codificar?",
            QuestionIntent.MEDICION_TECNICA,
        )

    if "INYECCION_MEZCLA" in areas:
        if (
            estado.obtener_hecho("revision_concreta_mezcla")
            and not estado.obtener_hecho("caudal_inyectores_reportado")
        ):
            from src.core.conversacion.revision_mezcla import siguiente_comprobacion

            siguiente = siguiente_comprobacion(estado)
            if siguiente:
                return (
                    "Tomo en cuenta la revisión y dejo esa pieza descartada por ahora. " + siguiente,
                    QuestionIntent.MEDICION_TECNICA,
                )
            return None
        if re.search(
            r"\b(?:inyectores?|injectores?)\b.{0,45}\b(?:no\s+inyectan?|inyectan?\s+poco)\b",
            texto,
            re.IGNORECASE,
        ):
            return None
        if re.search(r"\bstft\b|\bltft\b|ajuste(?:s)?\s+de\s+combustible", texto + " " + mediciones):
            return None
        if estado.ya_preguntado_texto("STFT/LTFT") or "stft/ltft" in pregunta_anterior:
            return None
        if estado.obtener_valor_confirmado("sin_dtc") or estado.obtener_valor_confirmado("escaner_limpio"):
            return (
                "Dado que no hay códigos DTC activos, ¿qué valores de ajuste de combustible STFT/LTFT muestra el escáner en datos en vivo? Si no los tienes, indícalo.",
                QuestionIntent.MEDICION_TECNICA,
            )
        return (
            "¿Qué DTC exacto y qué valores STFT/LTFT muestra el escáner? Si no tienes los ajustes de combustible, comparte solo el DTC.",
            QuestionIntent.MEDICION_TECNICA,
        )

    if "ADMISION_MAP" in areas:
        if re.search(r"\b\d+(?:[.,]\d+)?\s*(?:kpa|psi|v|voltios)?\b", mediciones):
            return None
        if (
            estado.ya_preguntado_texto("valor exacto de carga absoluta/MAP")
            or "valor exacto de carga absoluta/map" in pregunta_anterior
        ):
            return None
        return (
            "¿Qué valor exacto de carga absoluta/MAP muestra el escáner, con qué unidad "
            "y en qué condición del motor? Distingue presión MAP (kPa), carga calculada (%) "
            "y flujo MAF (g/s): son datos diferentes, no equivalentes.",
            QuestionIntent.MEDICION_TECNICA,
        )

    if "RALENTI" in areas and not re.search(r"\b\d{2,4}\s*rpm\b", texto + " " + mediciones):
        if "a cuántas rpm" not in pregunta_anterior:
            return (
                "¿A cuántas RPM queda el motor en ralentí, según el escáner?",
                QuestionIntent.MEDICION_TECNICA,
            )
    return None


def falta_medicion_discriminante_por_area(estado: ConversationState) -> bool:
    """No diagnostica mezcla/MAP con síntomas generales cuando falta la lectura clave."""
    from src.core.diagnostico.enrutador_sistema import detectar_areas_tecnicas

    historial = normalizar_jerga_automotriz(" ".join(estado.historial_mensajes_usuario))
    areas = detectar_areas_tecnicas(historial)
    if estado.active_system == "refrigeracion":
        return False
    if "sensor_maf_lectura_anomala_reportada" in estado.hechos:
        return False
    if "INYECCION_MEZCLA" in areas:
        if estado.obtener_hecho("revision_concreta_mezcla"):
            return False
        if re.search(
            r"\b(?:inyectores?|injectores?)\b.{0,45}\b(?:no\s+inyectan?|inyectan?\s+poco)\b",
            historial,
            re.IGNORECASE,
        ):
            return False
        tiene_dtc = bool(
            re.search(r"\bP0(?:171|172)\b", historial, re.IGNORECASE)
            or estado.dtc_status == DtcStatus.DTC_OBSERVADO
            or any(hecho.categoria == "dtc" for hecho in estado.hechos.values())
        )
        tiene_trim = bool(
            re.search(r"\b(?:STFT|LTFT)\s*[:=]?\s*[+-]?\d+(?:[.,]\d+)?\s*%", historial, re.IGNORECASE)
            or any(
                re.search(r"\b(?:STFT|LTFT)\b.*[+-]?\d", f"{hecho.campo} {hecho.valor}", re.IGNORECASE)
                for hecho in estado.hechos.values()
                if hecho.categoria == "medicion"
            )
        )
        return not (tiene_dtc or tiene_trim)
    if "ADMISION_MAP" in areas:
        patron_lectura_map = (
            r"(?:carga\s+absoluta|sensor\s+MAP|\bMAP\b).{0,60}"
            r"\b\d+(?:[.,]\d+)?\s*(?:kPa|psi|V|voltios?)\b|"
            r"\b\d+(?:[.,]\d+)?\s*(?:kPa|psi|V|voltios?)\b.{0,60}"
            r"(?:carga\s+absoluta|sensor\s+MAP|\bMAP\b)"
        )
        return not bool(re.search(patron_lectura_map, historial, re.IGNORECASE))
    return False


obtener_siguiente_pregunta_tecnica = pregunta_por_area
