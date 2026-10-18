"""Clasificación de intenciones de control, detección de placas e inferencia operativa."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Optional, Tuple

from src.core.conversacion.detector_polaridad import DetectorPolaridad
from src.core.conversacion.extraccion_hechos.patrones_hechos import (
    PATRON_CAUSAL_INYECCION,
    PATRON_CLIC_UNICO,
    PATRON_CLICS_REPETIDOS,
    PATRON_DEMORA_ARRANQUE,
    PATRON_DTC,
    PATRON_GIRO_LLAVE,
    PATRON_HALLAZGO_MAF,
    PATRON_MEDICION,
    PATRON_MEZCLA_REPORTADA,
    PATRON_NO_ARRANCA,
    PATRON_PLACA_EXPLICITA,
    PATRON_PLACA_FORMATO,
    PATRONES_REINICIO,
    PATRONES_SALUDO,
    PATRONES_SOLICITUD_DETALLE,
)
from src.core.conversacion.models import (
    ConversationState,
    EstadoOperativo,
    FactState,
)


def es_saludo(texto: str) -> bool:
    """Determina si el usuario envió únicamente un saludo de cortesía."""
    if not texto:
        return False
    return any(p.match(texto.strip()) for p in PATRONES_SALUDO)


def es_solicitud_detalle(texto: str) -> bool:
    """Determina si el usuario solicita más detalles o el procedimiento técnico de comprobación."""
    if not texto:
        return False
    return any(p.search(texto.strip()) for p in PATRONES_SOLICITUD_DETALLE)


PALABRAS_NO_PLACA = {
    "FUE", "ERA", "SON", "DIO", "HAY", "IBA", "VEO", "LOS", "LAS", "CON", "SIN",
    "POR", "DEL", "UNA", "UNO", "MAS", "MUY", "TAN", "QUE", "CADA", "SOLO",
    "DESDE", "HASTA", "ENTRE", "SOBRE", "TRAS", "HACIA", "COMO", "PERO", "PARA",
    "BIEN", "MAL", "SUBE", "BAJA", "SALE", "PONE", "LLEVA", "LLEVO", "VIENE", "VINO",
    "CIL", "CILINDRO", "CILINDROS", "KILOMETROS", "HORAS", "DIAS", "MINUTOS", "SEGUNDOS",
}


def extraer_placa(texto: str) -> Optional[str]:
    """Extrae la placa vehicular peruana asegurando no confundirla con códigos DTC ni lecturas físicas."""
    if not texto:
        return None
    m_exp = PATRON_PLACA_EXPLICITA.search(texto)
    if m_exp:
        candidato = m_exp.group(1).upper().replace(" ", "-")
        if not re.match(r"^[PBUCpbuc][0-3][0-9A-Fa-f]{3}$", candidato):
            if "-" not in candidato and len(candidato) == 6:
                candidato = f"{candidato[:3]}-{candidato[3:]}"
            return candidato
    for m in PATRON_PLACA_FORMATO.finditer(texto):
        candidato = m.group(1).upper().replace(" ", "-")
        prefix = candidato.split("-")[0]
        if prefix in PALABRAS_NO_PLACA:
            continue
        end_idx = m.end()
        resto = texto[end_idx : end_idx + 20].lower()
        if re.match(
            r"^\s*(?:kg|g|ma|a|v|mv|psi|bar|kpa|rpm|grados?|°|c|f|ohm|km|km/h|ms|mm|ml|%|volts?|amperios?|minutos?|horas?|segundos?|cuadras?|metros?|litros?)\b",
            resto,
        ):
            continue
        start_idx = m.start()
        prev = texto[max(0, start_idx - 15) : start_idx].lower().strip()
        if re.search(r"\b(?:a\s+los|en|de|por|con|sin|sube\s+a|baja\s+a|marca|mide|dio|fue|era)\s*$", prev):
            continue
        if not re.match(r"^[PBUCpbuc][0-3][0-9A-Fa-f]{3}$", candidato):
            return candidato
    return None


def es_reinicio_solicitado(texto: str) -> bool:
    """Determina si el usuario solicita afirmativamente iniciar un caso nuevo."""
    if not texto:
        return False
    if _es_mencion_no_destructiva(texto):
        return False
    if any(p.search(texto) for p in PATRONES_REINICIO):
        return True
    txt = "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )
    return bool(
        re.search(
            r"\b(otro\s+(?:carro|auto|vehiculo|veh.culo|caso|cliente)|"
            r"(?:nuevo|neuvo)\s+(?:caso|diagnostico|auto|carro|vehiculo)|"
            r"diagnostico\s+(?:nuevo|neuvo)|caso\s+(?:nuevo|neuvo)|"
            r"iniciar\s+(?:un\s+)?(?:diagnostico\s+nuevo|nuevo\s+diagnostico|nuevo\s+caso|neuvo\s+caso|caso\s+nuevo)|"
            r"cerrar\s+(?:el\s+)?diagnostico\s+anterior|"
            r"vamos\s+con\s+otro\s+cliente|termine\s+ese|tengo\s+uno\s+(?:nuevo|neuvo))\b",
            txt,
        )
    )


def _es_mencion_no_destructiva(texto: str) -> bool:
    """Evita tratar como orden una acción citada, negada, condicional o ambigua."""
    normalizado = "".join(
        c for c in unicodedata.normalize("NFD", texto.casefold())
        if unicodedata.category(c) != "Mn"
    )
    if re.search(r"^\s*(?:\?|por\s+que\b|que\s+significa\b|como\s+se\b)", normalizado):
        return True
    if re.search(r'["«“].{0,60}\b(?:nuevo\s+caso|nuevo\s+diagnostico|reiniciar|cerrar)\b', normalizado):
        return True
    if re.search(
        r"\b(?:no|tampoco|nunca|jamas)\s+(?:(?:es|son|hay|tengo|existe|se\s+trata\s+de|"
        r"quiero|deseo|necesito|busco|pido|solicito|voy\s+a|vamos\s+a|vayas\s+a|debes?|hay\s+que)\s+)?"
        r"(?:(?:iniciar|inicies|empezar|empieces|abrir|abras|generar|generes|hacer|hagas|"
        r"crear|crees|cambiar|cambies|reiniciar|reinicies|cerrar|cierres|borrar|borres)\s+)?"
        r"(?:un\s+|una\s+|el\s+|al\s+)?(?:otro|otra|nuevo|nueva)?\s*"
        r"(?:caso|diagnostico|problema|consulta|carro|vehiculo|auto)\b",
        normalizado,
    ):
        return True
    if re.search(
        r"\b(?:no\s+se\s+si|dudo\s+si|me\s+pregunto\s+si|en\s+vez\s+de|antes\s+de|sin)\s+"
        r"(?:iniciar|empezar|abrir|generar|hacer|crear|cambiar|reiniciar|cerrar)\b",
        normalizado,
    ):
        return True
    if re.search(
        r"\b(?:su|un|el|mi)?\s*otro\s+(?:auto|carro|vehiculo).{0,80}\b(?:pero|aunque|sin embargo|estamos|revisando|este)\b",
        normalizado,
    ):
        return True
    return bool(re.search(
        r"\b(?:no\s+(?:generes|inicies|cierres|reinicies|cambies|abras|borres)|"
        r"sin\s+(?:generar|cerrar|reiniciar|iniciar|abrir)|"
        r"(?:menciona|dije|dice|palabra|termino)\s+(?:nuevo\s+diagnostico|cerrar|reiniciar))\b",
        normalizado,
    ))


def es_consulta_memoria(texto: str) -> bool:
    """Reconoce preguntas de memoria sin convertirlas en una orden de caso ni confundir preguntas diagnósticas."""
    if not texto:
        return False
    normalizado = "".join(
        c for c in unicodedata.normalize("NFD", texto.casefold())
        if unicodedata.category(c) != "Mn"
    )
    # Si el usuario pide causas alternativas, preguntas para diferenciar o diagnóstico, NO es una consulta pasiva de memoria
    if re.search(
        r"\b(?:otra\s+causa|otras\s+causas|posibles\s+causas|explicar\s+estos\s+sintomas|diferenci\w*|pregunta\s+concreta|que\s+podria\s+estar|que\s+puede\s+ser)\b",
        normalizado,
    ):
        return False

    if re.search(r"\b(?:de\s+donde|de\s+que\s+(?:caso|diagnostico)|por\s+que)\b.{0,100}\b(?:obtuviste|salio|registraste|mencionaste|proviene)\b", normalizado):
        return True
    if re.search(r"\b(?:cual\s+es\s+el\s+origen|de\s+donde\s+(?:salio|viene|proviene))\b.{0,100}\b(?:misfire|sintoma|hipotesis|falla)\b", normalizado):
        return True
    if re.search(r"\b(?:fue\s+mencionado|proviene\s+del\s+diagnostico\s+anterior)\b", normalizado):
        return True
    return bool(re.search(
        r"\b(?:que|cual|cuales|indica|muestra|resume|consulta|consultar)\b.{0,80}"
        r"\b(?:registrad[oa]s?|memoria|recuerdas|guardad[oa]s?)\b",
        normalizado,
    ))


def es_cancelacion_solicitada(texto: str) -> bool:
    """Distingue cancelar/cerrar el caso de continuar con un caso nuevo."""
    if not texto:
        return False
    return bool(PATRONES_REINICIO[0].fullmatch(texto.strip()))


def clasificar_solicitud_caso(texto: str) -> Dict[str, Any] | None:
    """Reconoce comandos explícitos de caso nuevo o reanudación, no alusiones vagas."""
    if not texto:
        return None
    normalizado = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto.casefold())
        if unicodedata.category(caracter) != "Mn"
    )
    limpio = " ".join(normalizado.split())

    if _es_mencion_no_destructiva(texto):
        return None

    if re.fullmatch(r"(?:quiero\s+)?cancelar(?:(?:\s+el)?\s+(?:caso|diagnostico|consulta))?[.!]*", limpio):
        return {"accion": "cancelar", "preservar_vehiculo": False}

    patron_uuid = (
        r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    )
    reanudar = re.search(
        rf"\b(?:retomar|reanudar|continuar|volver\s+a)\s+(?:el\s+)?"
        rf"(?:caso|diagnostico)(?:\s+(?:anterior|previo))?(?:\s+{patron_uuid})?\b",
        limpio,
    )
    if reanudar:
        objetivo = reanudar.group(1)
        return {
            "accion": "reanudar",
            "case_id": objetivo,
            "caso_anterior": "anterior" in reanudar.group(0) or "previo" in reanudar.group(0),
        }

    mismo_vehiculo = bool(
        re.search(r"\b(?:mismo|misma)\s+(?:vehiculo|carro|auto|coche|placa)\b", limpio)
        or re.search(r"\bcon\s+la\s+misma\s+placa\b", limpio)
    )
    otro_vehiculo = bool(
        re.search(r"\b(?:otro|otra)\s+(?:vehiculo|carro|auto|coche)\b", limpio)
        or re.search(r"\bcambio\s+de\s+vehiculo\b", limpio)
    )
    nuevo_caso = bool(
        re.search(
            r"\b(?:nuevo|neuvo|otro)\s+(?:caso|diagnostico|problema)\b|"
            r"\b(?:falla|problema)\s+diferente\b|"
            r"\btengo\s+otra\s+(?:falla|consulta)\b|"
            r"\ben\s+el\s+mismo\s+vehiculo[, ]+ahora\s+"
            r"(?:el\s+)?(?:problema|falla)\s+es\b|"
            r"\b(?:cambiemos|pasemos)\s+(?:a\s+)?otro\s+caso\b|"
            r"\b(?:empezar|empecemos|comenzar|comencemos|iniciar|iniciemos)\s+"
            r"(?:un\s+)?(?:caso\s+completamente\s+nuevo|caso\s+nuevo|diagnostico\s+nuevo|todo\s+)?(?:de\s+nuevo|desde\s+cero)?\b|"
            r"\breiniciar\s+(?:el\s+)?(?:caso|diagnostico)\b|"
            r"\botro\s+(?:vehiculo|carro|auto|coche)\b|"
            r"\b(?:tengo|llego|lleg[oó])\s+(?:un\s+)?otro\s+"
            r"(?:vehiculo|carro|auto|coche|caso|problema)\b|"
            r"\b(?:olvida|olvidemos)\s+lo\s+anterior\b|"
            r"^\s*(?:nuevo|neuvo)[.!]*\s*$",
            limpio,
        )
    )
    if nuevo_caso:
        return {
            "accion": "nuevo_caso",
            "preservar_vehiculo": mismo_vehiculo and not otro_vehiculo,
            "otro_vehiculo": otro_vehiculo,
        }
    return None


def contiene_informacion_diagnostica(texto: str) -> bool:
    """Detecta si un mensaje de nuevo caso ya incluye sintomas, pruebas o mediciones."""
    if not texto:
        return False
    patrones = [
        PATRON_NO_ARRANCA,
        PATRON_GIRO_LLAVE,
        PATRON_CLIC_UNICO,
        PATRON_CLICS_REPETIDOS,
        PATRON_DEMORA_ARRANQUE,
        PATRON_DTC,
        PATRON_MEDICION,
        PATRON_MEZCLA_REPORTADA,
        PATRON_CAUSAL_INYECCION,
        PATRON_HALLAZGO_MAF,
        re.compile(
            r"\b(?:aire\s+acondicionado|climatizaci[o\u00f3]n|compresor|no\s+enfr[i\u00ed]a)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(recalienta|recalentar|recalntar|se\s+calienta|temperatura\s+(?:del\s+motor\s+)?(?:sube|empieza\s+a\s+subir|alta)|"
            r"pierde\s+(?:agua|refrigerante|l[i\u00ed]quido|fuerza|potencia)|fuga|gotea|"
            r"no\s+enfr[i\u00ed]a|sale\s+aire\s+(?:caliente|tibio)|"
            r"vibra|vibraci[o\u00f3]n|vibraciones|tiembla|jalonea|tironea|tironear|tirones|cascabelea|cascabeleo|"
            r"no\s+jala|sin\s+fuerza|se\s+(?:me\s+)?apaga|se\s+apag[o\u00f3]|no\s+acelera|al\s+acelerar|"
            r"humo\s+(?:negro|blanco|azul)|consume\s+(?:aceite|refrigerante)|"
            r"luz\s+de\s+(?:advertencia|falla|check|motor)|"
            r"demora\s+en\s+(?:enganchar|entrar|acoplar)|reversa|"
            r"golpe|golpes|ruido|ruidos|zumbido|chillido|chirrido|frena|freno|frenos|frena\s+mal|pedal|volante|"
            r"suspensi[o\u00f3]n|bache|baches|amortiguador|amortiguadores|buje|bujes|r[o\u00f3]tula|r[o\u00f3]tulas)\b",
            re.IGNORECASE,
        ),
    ]
    return any(p.search(texto) for p in patrones)


def inferir_estado_operativo(
    estado: ConversationState,
    texto_usuario: str,
) -> Tuple[EstadoOperativo, bool, Dict[str, Any]]:
    """Infiere el EstadoOperativo contextual con prioridad de evidencia temporal (Fase 9.10)."""
    texto_l = texto_usuario.lower()
    hechos_confirmados = {
        k: h.valor for k, h in estado.hechos.items() if h.estado == FactState.CONFIRMADO
    }

    es_no_arranca_comp = bool(
        re.search(
            r"\b(?:electroventilador|motoventilador|ventilador|electro|compresor)\s+(?:no\s+)",
            texto_l,
        )
    )
    arranque_actual = bool(
        (PATRON_NO_ARRANCA.search(texto_l) and not es_no_arranca_comp)
        or PATRON_GIRO_LLAVE.search(texto_l)
        or PATRON_DEMORA_ARRANQUE.search(texto_l)
    )
    frenado_actual = bool(
        re.search(r"\b(al\s+frenar|frenando|cuando\s+fren[ao]|frena(ndo)?|pedal\s+de\s+freno|al\s+pisar\s+el\s+(?:pedal\s+de\s+)?freno)\b", texto_l)
        and not DetectorPolaridad.es_condicion_negada(r"\b(al\s+frenar|frenando|cuando\s+fren[ao]|al\s+pisar\s+el\s+(?:pedal\s+de\s+)?freno|frena)\b", texto_l)
    )
    ralenti_actual = bool(
        re.search(r"\b(en\s+ralent[ií]|en\s+el\s+sem[aá]foro|detenido(\s+en\s+ralent[ií])?|en\s+neutro|parado\s+esperando)\b", texto_l)
        and not DetectorPolaridad.es_condicion_negada(r"\b(en\s+ralent[ií]|detenido|en\s+neutro)\b", texto_l)
    )
    marcha_actual = bool(
        re.search(
            r"\b(en\s+carretera|a\s+\d+\s*km/h|circulando|en\s+marcha|andando|anda|al\s+andar|a\s+velocidad|"
            r"acelerando|al\s+acelerar|bajo\s+aceleraci[oó]n|acelerando\s+con\s+fuerza|voy\s+a\s+\d+|cuando\s+voy\s+a|manejando|al\s+manejar|"
            r"despu[eés]\s+de\s+\d+\s+minutos|pistas?\s+irregulares?|baches?|trocha|calamina|empedrado)\b",
            texto_l,
        )
    )
    estacionado_actual = bool(
        re.search(r"\b(estacionado|parqueado)\b", texto_l)
        and not arranque_actual
        and not marcha_actual
    )

    arranque_heredado = bool(
        hechos_confirmados.get("motor_arranca") == "NO"
        or hechos_confirmados.get("ruido_arranque") in ("clic_unico", "clics_repetidos")
        or hechos_confirmados.get("evento") == "giro_llave"
        or "sintoma_motor_no_arranca" in hechos_confirmados
        or "sintoma_demora_arranque" in hechos_confirmados
        or "sintoma_chasquido_de_arranque_clac" in hechos_confirmados
    )
    frenado_heredado = bool(
        hechos_confirmados.get("condicion_operacion") == "al frenar"
        or "sintoma_anomalía_en_frenos" in hechos_confirmados
        or "sintoma_anomalia_en_frenos" in hechos_confirmados
    )
    ralenti_heredado = bool(hechos_confirmados.get("condicion_operacion") == "detenido en ralentí")
    marcha_heredada = bool(
        hechos_confirmados.get("condicion_operacion") in ("en carretera a velocidad", "al acelerar bajo carga")
    )

    metadata = {
        "seniales_mensaje": {
            "senial_arranque": arranque_actual,
            "senial_frenado": frenado_actual,
            "senial_ralenti": ralenti_actual,
            "senial_marcha": marcha_actual,
            "senial_estacionado": estacionado_actual,
            "es_contradictorio_interno": arranque_actual and (marcha_actual or frenado_actual),
        },
        "seniales_heredadas": {
            "senial_arranque": arranque_heredado,
            "senial_frenado": frenado_heredado,
            "senial_ralenti": ralenti_heredado,
            "senial_marcha": marcha_heredada,
        },
        "estado_previo": estado.estado_operativo,
    }

    if arranque_actual and (marcha_actual or frenado_actual):
        metadata["estado_detectado_mensaje_actual"] = EstadoOperativo.ARRANQUE
        return EstadoOperativo.ARRANQUE, True, metadata

    if frenado_actual:
        metadata["estado_detectado_mensaje_actual"] = EstadoOperativo.FRENADO
        return EstadoOperativo.FRENADO, False, metadata
    if marcha_actual:
        metadata["estado_detectado_mensaje_actual"] = EstadoOperativo.MARCHA
        return EstadoOperativo.MARCHA, False, metadata
    if ralenti_actual:
        metadata["estado_detectado_mensaje_actual"] = EstadoOperativo.RALENTI
        return EstadoOperativo.RALENTI, False, metadata
    if arranque_actual:
        metadata["estado_detectado_mensaje_actual"] = EstadoOperativo.ARRANQUE
        return EstadoOperativo.ARRANQUE, False, metadata
    if estacionado_actual:
        metadata["estado_detectado_mensaje_actual"] = EstadoOperativo.ESTACIONADO
        return EstadoOperativo.ESTACIONADO, False, metadata

    metadata["estado_detectado_mensaje_actual"] = EstadoOperativo.DESCONOCIDO
    if arranque_heredado:
        return EstadoOperativo.ARRANQUE, False, metadata
    if frenado_heredado:
        return EstadoOperativo.FRENADO, False, metadata
    if ralenti_heredado:
        return EstadoOperativo.RALENTI, False, metadata
    if marcha_heredada:
        return EstadoOperativo.MARCHA, False, metadata

    return EstadoOperativo.DESCONOCIDO, False, metadata
