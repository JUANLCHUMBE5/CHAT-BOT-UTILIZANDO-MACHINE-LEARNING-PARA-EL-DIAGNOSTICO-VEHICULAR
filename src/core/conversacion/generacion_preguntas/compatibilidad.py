"""Validación de compatibilidad y control de repetición de preguntas en el turno."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional, Tuple

from src.core.conversacion.compatibilidad_preguntas import CompatibilidadPreguntas
from src.core.conversacion.generacion_preguntas.known_checker import (
    already_known,
    permite_caracterizar_ruido_suspension,
)
from src.core.conversacion.models import (
    DtcStatus,
    EstadoOperativo,
    QuestionIntent,
)

if TYPE_CHECKING:
    from src.core.conversacion.models import ConversationState


def puede_preguntar(intent: QuestionIntent, estado: ConversationState) -> bool:
    """Verifica si es válido formular una pregunta sin caer en repetición ni violar el límite."""
    if estado.turnos_repregunta >= estado.max_repreguntas:
        return False
    if already_known(intent, estado) and not (
        intent == QuestionIntent.PRESENCIA_RUIDO
        and permite_caracterizar_ruido_suspension(estado)
    ):
        return False
    veces = estado.veces_preguntado(intent)
    if veces >= 2:
        return False
    if veces == 1 and len(estado.respuestas_obtenidas) >= 1:
        return False
    return True


def es_pregunta_compatible(
    intent: QuestionIntent,
    texto_pregunta: str,
    estado: ConversationState,
) -> Tuple[bool, Optional[str]]:
    """Valida que la pregunta candidata sea compatible con el estado operativo y hechos conocidos."""
    texto_l = texto_pregunta.lower()

    # 0. Aclaración de contradicción
    if intent == QuestionIntent.ACLARACION_CONTRADICCION:
        if estado.veces_preguntado(intent) >= 1 and len(estado.respuestas_obtenidas) >= 1:
            return False, "PREGUNTA_REPETIDA"
        return True, None

    # 1. PREGUNTA_REPETIDA
    if any(p.get("texto", "").strip().lower() == texto_pregunta.strip().lower() for p in estado.preguntas_realizadas):
        return False, "PREGUNTA_REPETIDA"
    if intent != QuestionIntent.COMPONENTE_REVISADO:
        veces = estado.veces_preguntado(intent)
        if veces >= 2:
            return False, "PREGUNTA_REPETIDA"
        if veces == 1 and len(estado.respuestas_obtenidas) >= 1:
            return False, "PREGUNTA_REPETIDA"
    else:
        veces = estado.veces_preguntado(intent)
        if veces >= 3:
            return False, "PREGUNTA_REPETIDA"

    # 2. INTENT_YA_RESUELTO
    if intent == QuestionIntent.CONDICION_OPERACION and (
        estado.estado_operativo != EstadoOperativo.DESCONOCIDO
        or estado.obtener_hecho("condicion_operacion") is not None
        or estado.ya_preguntado(QuestionIntent.CONDICION_OPERACION)
    ):
        return False, "INTENT_YA_RESUELTO"
    if intent == QuestionIntent.TEMPERATURA_APARICION and (
        estado.obtener_hecho("temperatura") is not None
        or any(h.categoria == "temperatura" for h in estado.hechos.values())
        or estado.ya_preguntado(QuestionIntent.TEMPERATURA_APARICION)
    ):
        return False, "INTENT_YA_RESUELTO"
    if intent == QuestionIntent.CODIGO_DTC and already_known(QuestionIntent.CODIGO_DTC, estado):
        return False, "INTENT_YA_RESUELTO"
    if (
        intent == QuestionIntent.PRESENCIA_RUIDO
        and already_known(QuestionIntent.PRESENCIA_RUIDO, estado)
        and not permite_caracterizar_ruido_suspension(estado, texto_pregunta)
    ):
        return False, "INTENT_YA_RESUELTO"

    # 3. Aplicabilidad semántica por dominio
    compatible_dominio, motivo_dominio = CompatibilidadPreguntas.validar(
        intent, texto_pregunta, estado
    )
    if not compatible_dominio:
        return False, motivo_dominio

    # 4. HECHO_YA_CONOCIDO
    if re.search(r"\b(ralent[ií]|en\s+marcha|aceleraci[oó]n\s+en\s+marcha)\b", texto_l):
        if estado.estado_operativo != EstadoOperativo.DESCONOCIDO or estado.obtener_hecho("condicion_operacion") is not None:
            return False, "HECHO_YA_CONOCIDO"
    if re.search(r"\b(check\s+engine|testigo\s+encendido|testigo\s+en\s+el\s+tablero)\b", texto_l):
        if (
            estado.obtener_hecho("sintoma_testigo_check_engine") is not None
            or estado.dtc_status in (DtcStatus.DTC_OBSERVADO, DtcStatus.DTC_DESCONOCIDO)
            or any("check" in k.lower() or "testigo" in k.lower() for k in estado.hechos.keys())
        ):
            return False, "HECHO_YA_CONOCIDO"
    if ("clic" in texto_l or "metralleta" in texto_l or "chasquido" in texto_l) and estado.obtener_hecho("ruido_arranque") is not None:
        return False, "HECHO_YA_CONOCIDO"
    if "luces" in texto_l and estado.obtener_hecho("luces_se_atenuan") is not None:
        return False, "HECHO_YA_CONOCIDO"
    if "intento de girar" in texto_l and estado.obtener_hecho("giro_motor") is not None:
        return False, "HECHO_YA_CONOCIDO"
    if ("compresor" in texto_l or "clic" in texto_l or "acopla" in texto_l) and (
        estado.ya_comprobado_o_respondido("acople_compresor")
        or estado.completed_tests.get("acople_compresor") is not None
        or estado.obtener_hecho("compresor_acopla") is not None
    ):
        return False, "HECHO_YA_CONOCIDO"
    if "electroventilador" in texto_l and (
        estado.ya_comprobado_o_respondido("electroventilador_condensador")
        or estado.completed_tests.get("electroventilador_condensador") is not None
    ):
        return False, "HECHO_YA_CONOCIDO"

    # 5. INCOMPATIBLE_ESTADO_OPERATIVO
    if estado.estado_operativo == EstadoOperativo.ARRANQUE:
        if re.search(
            r"\b(ralent[ií]|carretera|freno|frenar|acelerar\s+con\s+fuerza|"
            r"a\s+alta\s+velocidad|en\s+marcha|al\s+acelerar\s+bajo\s+carga)\b",
            texto_l,
        ):
            return False, "INCOMPATIBLE_ESTADO_OPERATIVO"

    elif estado.estado_operativo == EstadoOperativo.FRENADO:
        palabras_arranque = ("al arrancar", "primer arranque", "no arranca", "al girar la llave", "dar arranque")
        if any(w in texto_l for w in palabras_arranque):
            return False, "INCOMPATIBLE_ESTADO_OPERATIVO"

    elif estado.estado_operativo == EstadoOperativo.MARCHA:
        palabras_arranque = ("al arrancar", "primer arranque", "no arranca", "al girar la llave", "dar arranque")
        if any(w in texto_l for w in palabras_arranque):
            return False, "INCOMPATIBLE_ESTADO_OPERATIVO"

    elif estado.estado_operativo == EstadoOperativo.RALENTI:
        if "freno" in texto_l or "frenar" in texto_l:
            return False, "INCOMPATIBLE_ESTADO_OPERATIVO"

    # 6. PRECONDICIONES LOGICAS DE PREGUNTA
    if (
        "temperatura de trabajo normal" in texto_l
        or "después de que el motor alcanza" in texto_l
        or "en caliente tras andar" in texto_l
    ):
        if (
            estado.obtener_hecho("motor_arranca")
            and estado.obtener_hecho("motor_arranca").valor == "NO"
            and not estado.tiene_antecedente_motor_en_marcha()
        ):
            return False, "PRECONDICION_NO_CUMPLIDA: REQUIERE_MOTOR_EN_MARCHA"

    if intent == QuestionIntent.CONDICION_OPERACION:
        if (
            estado.obtener_hecho("motor_arranca")
            and estado.obtener_hecho("motor_arranca").valor == "NO"
            and not estado.tiene_antecedente_motor_en_marcha()
        ):
            return False, "PRECONDICION_NO_CUMPLIDA: REQUIERE_MOTOR_EN_MARCHA"

    # Regla de Tesis: Averías mecánicas puras sin control electrónico nunca sugieren escaneo DTC
    if intent == QuestionIntent.CODIGO_DTC:
        hechos_mecanicos_puros = (
            "desbalanceo", "desalineacion", "desalineación", "alabeo", "pastillas",
            "rotula", "rótula", "bieleta", "embrague patinando", "anomalía en frenos",
            "buje", "bujes", "trapecio", "amortiguador",
        )
        historial_completo = " ".join(estado.historial_mensajes_usuario).lower()
        hechos_str = " ".join(f"{h.campo} {h.valor}" for h in estado.hechos.values()).lower()
        if any(m in historial_completo or m in hechos_str for m in hechos_mecanicos_puros):
            if not any(e in historial_completo or e in hechos_str for e in ("check", "testigo", "abs", "esc", "esp", "sensor", "dtc")):
                return False, "INCOMPATIBLE_AVERIA_MECANICA_PURA"

    return True, None
