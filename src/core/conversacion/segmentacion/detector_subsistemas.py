"""Detección y clasificación de subsistemas automotrices a partir de texto y estado."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from src.core.conversacion.segmentacion.tipos import SubsistemaVehicular

if TYPE_CHECKING:
    from src.core.conversacion.models import ConversationState


def detectar_subsistema_texto(texto: str) -> SubsistemaVehicular:
    """Clasifica el subsistema automotriz primario al que alude el texto."""
    txt = (texto or "").lower()
    modificador_clima = bool(
        re.search(r"\bcon\s+(?:el\s+)?(?:a/c|aire\s+acondicionado|clima)\s+encendido\b", txt)
        and not re.search(r"\b(no\s+enfr[ií]a|sale\s+aire\s+caliente|compresor|falla|problema)\b", txt)
    )
    if re.search(
        r"\b(no\s+(?:quiso\s+|llega\s+a\s+)?(?:arranca|arrancar|prende|prender|enciende|encender)|"
        r"(?:demora|tarda|cuesta)\s+(?:(?:bastante|mucho|demasiado|varios\s+segundos|un\s+poco)\s+)?(?:en\s+)?(?:arrancar|prender|encender)|"
        r"le\s+cuesta\s+(?:arrancar|prender|encender)|"
        r"da\s+marcha\s+(?:bastante|un\s+rato|varios\s+segundos)|"
        r"dificultad\s+(?:de|para|al)\s+arranc(?:ar|e)|arranque\s+(?:largo|en\s+fr[ií]o|pesado)|"
        r"(?:por|en)\s+las\s+mañanas\s+(?:demora|tarda|le\s+cuesta)|"
        r"demora\s+por\s+las\s+mañanas|tarda\s+en\s+la\s+mañana|"
        r"clic\s+seco|chasquido|solenoide|motor\s+de\s+arranque|dar\s+arranque|dar\s+marcha|al\s+dar\s+marcha|doy\s+marcha|al\s+arrancar|llave)\b",
        txt,
    ):
        return SubsistemaVehicular.ARRANQUE
    es_transmision = bool(
        re.search(
            r"\b(caja(?:\s+de\s+cambios|\s+autom[aá]tica)?|transmisi[oó]n|embrague|clutch|"
            r"volante\s+(?:de\s+inercia|motor|bimasa)|"
            r"disco\s+(?:de\s+embrague|gastado|con\s+remaches)|remaches\s+(?:rozando|del\s+disco)|"
            r"bomb[ií]n\s+(?:esclavo|hidr[aá]ulico)|bomba\s+de\s+embrague|"
            r"alabeo\b.{0,30}\bvolante|\bvolante\b.{0,30}\balabeo|"
            r"palanca(?:\s+de\s+cambios)?|selector(?:\s+de\s+marchas)?|cambio(?:s)?|"
            r"(?:meter|pasar|cambiar|enganchar|seleccionar)\s+marcha|marcha\s+atr[aá]s|primera\s+marcha|segunda\s+marcha|tercera\s+marcha|"
            r"junta(?:s)?\s+homocin[eé]tica(?:s)?|palier(?:es)?|semieje(?:s)?|"
            r"patina\s+el\s+embrague|embrague\s+patinando|patina\s+en\s+subida|patea\s+la\s+caja|"
            r"zapatea(?:\s+feo)?\s+al\s+arrancar|trepidaci[oó]n|zapateo|"
            r"pedal\s+vibra\s+cuando\s+lo\s+suelto|pedal\s+de\s+embrague|"
            r"no\s+entra\s+(?:segunda|cambio)|reversa|retroceso)\b",
            txt,
        ) or (
            re.search(r"\b(acopla(?:r|miento)?|engancha(?:r)?)\b", txt)
            and not re.search(r"\b(compresor|clima|a/c|aire)\b", txt)
        ) or bool(
            re.search(
                r"\b(?:revoluciones\s+suben|rpm\s+suben)\b.{0,45}\bno\s+avanza\b|"
                r"\bno\s+avanza\b.{0,45}\b(?:revoluciones\s+suben|rpm\s+suben)\b",
                txt,
            )
        )
    )
    if es_transmision and not re.search(r"\b(al\s+frenar|frenando|pastillas?\s+de\s+freno)\b", txt):
        return SubsistemaVehicular.TRANSMISION

    freno_negado = bool(
        re.search(r"\b(al\s+frenar|frenando|cuando\s+freno)\s*,?\s*no\b", txt)
        or re.search(r"\bno\s+(?:frena|vibra|se\s+va|hace\s+ruido)\s+(?:al\s+frenar|cuando\s+freno)\b", txt)
        or re.search(r"\bal\s+frenar\s+no\s+vibra\b", txt)
    )
    tiene_freno_positivo = bool(
        re.search(r"\b(pedal\s+(?:se\s+hunde|esponjoso|duro)|frena\s+(?:disparejo|mal|largo)|chillido\s+al\s+frenar|pastillas?|disco(?:s)?\s+de\s+freno)\b", txt)
        and not freno_negado
    ) or (bool(re.search(r"\b(disco(?:s)?|alabeo)\b", txt)) and not es_transmision and not freno_negado)
    if ((re.search(r"\b(freno|frenar|frenando|frenos|pedal\s+de\s+freno)\b", txt) and not freno_negado) or tiene_freno_positivo) and not es_transmision:
        return SubsistemaVehicular.FRENOS
    if not modificador_clima and re.search(
        r"\b(aire\s+acondicionado|climatizaci[oó]n|compresor|no\s+enfr[ií]a|"
        r"sale\s+aire\s+(?:caliente|tibio|ambiente)|gas\s+r134a|refrigerante\s+r134a|r134a)\b",
        txt,
    ):
        return SubsistemaVehicular.CLIMATIZACION
    if re.search(
        r"\b(recalienta|recalentar|recalntar|refrigeraci[oó]n|refrigerante|"
        r"temperatura\s+(?:del\s+motor\s+)?(?:sube|subiendo)|sube\s+la\s+temperatura)\b", txt,
    ) and not re.search(r"\b(caja|transmisi[oó]n|embrague|clutch)\b", txt):
        return SubsistemaVehicular.MARCHA_MOTOR
    if es_transmision:
        return SubsistemaVehicular.TRANSMISION
    if re.search(r"\b(suspensi[oó]n|amortiguador(?:es)?|r[oó]tulas?|terminal(?:es)?|baches|pistas?\s+irregulares|rompemuelles|golpe\s+en\s+la\s+rueda)\b", txt):
        return SubsistemaVehicular.SUSPENSION
    if re.search(r"\b(alternador|bater[ií]a\s+descargada|voltaje|mult[ií]metro|luces\s+parpadean|fusible)\b", txt):
        return SubsistemaVehicular.ELECTRICO
    if re.search(
        r"\b(pierde\s+fuerza|perdia\s+fuerza|se\s+ahoga|no\s+jala|misfire|ratea|cabecea|tironea|acelerar|"
        r"en\s+carretera|a\s+\d+\s*km/h|se\s+calienta|sobrecalienta|hierve|refrigerante|humo\s+blanco|"
        r"buj[ií]as?|bobinas?|inyector(?:es)?|fuga\s+de\s+(?:l[ií]quido|agua|refrigerante)|"
        r"temperatura\s+(?:del\s+motor\s+)?(?:est[aá]\s+)?subiendo|sube\s+la\s+temperatura|"
        r"calentamiento|radiador)\b",
        txt,
    ):
        return SubsistemaVehicular.MARCHA_MOTOR
    return SubsistemaVehicular.DESCONOCIDO


def obtener_subsistema_estado(estado: ConversationState) -> SubsistemaVehicular:
    """Determina el subsistema dominante del caso clínico activo en memoria."""
    from src.core.conversacion.models import EstadoOperativo, FactState

    # 1. Por hechos confirmados
    for campo, hecho in estado.hechos.items():
        if hecho.estado != FactState.CONFIRMADO:
            continue
        c_low = campo.lower().replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o").replace("ú", "u")
        v_low = str(hecho.valor).lower().replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o").replace("ú", "u")
        if any(k in c_low or k in v_low for k in ("freno", "pastilla", "disco")):
            return SubsistemaVehicular.FRENOS
        if any(k in c_low or k in v_low for k in ("motor_arranca", "ruido_arranque", "evento", "arranque", "demora_arranque", "solenoide")):
            return SubsistemaVehicular.ARRANQUE
        if any(k in c_low or k in v_low for k in ("caja", "embrague", "transmision")):
            return SubsistemaVehicular.TRANSMISION
        if any(k in c_low or k in v_low for k in ("suspension", "amortiguador", "bache", "rotula")):
            return SubsistemaVehicular.SUSPENSION
        if any(k in c_low or k in v_low for k in ("alternador", "voltaje", "bateria")):
            return SubsistemaVehicular.ELECTRICO
        if any(k in c_low or k in v_low for k in ("climatizacion", "aire acondicionado", "r134a")):
            return SubsistemaVehicular.CLIMATIZACION
        if any(k in c_low or k in v_low for k in ("potencia", "misfire", "sobrecalentamiento", "humo", "refrigerante")):
            return SubsistemaVehicular.MARCHA_MOTOR

    # 2. Por hipótesis principal previa si existe
    falla_p = (getattr(estado, "falla_principal", None) or (estado.top3_actual[0]["falla"] if estado.top3_actual else "")).lower()
    falla_p = falla_p.replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o").replace("ú", "u")
    if "freno" in falla_p or "disco" in falla_p:
        return SubsistemaVehicular.FRENOS
    if "arranque" in falla_p or "solenoide" in falla_p:
        return SubsistemaVehicular.ARRANQUE
    if "bateria" in falla_p or "alternador" in falla_p:
        return SubsistemaVehicular.ELECTRICO
    if "caja" in falla_p or "embrague" in falla_p or "transmision" in falla_p:
        return SubsistemaVehicular.TRANSMISION
    if "suspension" in falla_p or "amortiguador" in falla_p or "rotula" in falla_p:
        return SubsistemaVehicular.SUSPENSION
    if "aire acondicionado" in falla_p or "climatizacion" in falla_p or "r134a" in falla_p:
        return SubsistemaVehicular.CLIMATIZACION
    if any(k in falla_p for k in ("bujia", "bobina", "refrigerante", "culata", "inyeccion", "termostato")):
        return SubsistemaVehicular.MARCHA_MOTOR

    # 3. Por EstadoOperativo
    if estado.estado_operativo == EstadoOperativo.ARRANQUE:
        return SubsistemaVehicular.ARRANQUE
    if estado.estado_operativo == EstadoOperativo.FRENADO:
        return SubsistemaVehicular.FRENOS
    if estado.estado_operativo in (EstadoOperativo.MARCHA, EstadoOperativo.RALENTI):
        return SubsistemaVehicular.MARCHA_MOTOR

    # 4. Por dominio_probable si está registrado
    if getattr(estado, "dominio_probable", None):
        dom = str(estado.dominio_probable).strip().upper()
        for sub in SubsistemaVehicular:
            if sub.value == dom or sub.name == dom:
                return sub

    return SubsistemaVehicular.DESCONOCIDO


def es_sintoma_coexistente(sub1: SubsistemaVehicular, sub2: SubsistemaVehicular, texto: str) -> bool:
    """Determina si dos síntomas corresponden al mismo vehículo/diagnóstico integral."""
    if sub1 == sub2:
        return True
    if {sub1, sub2} == {SubsistemaVehicular.FRENOS, SubsistemaVehicular.SUSPENSION}:
        return True
    if {sub1, sub2} == {SubsistemaVehicular.MARCHA_MOTOR, SubsistemaVehicular.ELECTRICO}:
        return True
    if {sub1, sub2} == {SubsistemaVehicular.ARRANQUE, SubsistemaVehicular.ELECTRICO}:
        return True
    if {sub1, sub2} == {SubsistemaVehicular.ARRANQUE, SubsistemaVehicular.MARCHA_MOTOR}:
        return True
    if {sub1, sub2} == {SubsistemaVehicular.MARCHA_MOTOR, SubsistemaVehicular.TRANSMISION}:
        return True
    txt = texto.lower()
    if {sub1, sub2} == {SubsistemaVehicular.TRANSMISION, SubsistemaVehicular.FRENOS} and re.search(
        r"\b(l[ií]quido|dot\s*[34]|dep[oó]sito|circuito|compart|bomba\s+principal)\b", txt
    ):
        return True
    if {sub1, sub2} == {SubsistemaVehicular.FRENOS, SubsistemaVehicular.MARCHA_MOTOR} and re.search(
        r"\b(apaga|apag[oó]|calado|ralent[ií]|rpm|revoluciones|tiembla|tironea|ahoga|fuga\s+de\s+vac[ií]o|booster|servofreno|deten|sem[aá]foro)\b",
        txt,
    ):
        return True
    if re.search(r"\b(tambi[eé]n|adem[aá]s|junto\s+con|aparte\s+de\s+eso)\b", txt):
        return True
    return False
