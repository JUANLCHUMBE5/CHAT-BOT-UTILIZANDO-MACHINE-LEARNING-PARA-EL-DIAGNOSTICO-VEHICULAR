"""Orientación provisional segura y manejo de imposibilidad de comprobaciones físicas."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, List, Optional


def _normalizar(texto: str) -> str:
    sin_tildes = "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", texto or "")
        if not unicodedata.combining(caracter)
    )
    return re.sub(r"\s+", " ", sin_tildes.strip().lower())


PATRONES_IMPOSIBILIDAD_FISICA = (
    r"\b(?:sigo|seguimos|continuo|continuamos)\s+sin\s+(?:poder|posibilidad\s+de)\s+(?:comprobar|medir|verificar|revisar|probar)\b",
    r"\bno\s+(?:puedo|podemos|tengo\s+forma\s+de|tengo\s+como)\s+(?:realizar|hacer|efectuar|ejecutar)?\s*(?:m[aá]s\s+|ninguna\s+|ningun\s+)?(?:comprobaciones?|pruebas?|revisiones?|mediciones?|inspecciones?|desarmes?)\b",
    r"\b(?:no|ni|tampoco)\s+(?:puedo|podemos|tengo\s+como)\s+(?:revisar|comprobar|probar|medir|desmontar|desarmar|verificar)\b",
    r"\b(?:imposible|no\s+es\s+posible)\s+(?:realizar|hacer|revisar|comprobar)\s+(?:comprobaciones?|pruebas?)\b",
    r"\b(?:no|ni|tampoco)\s+(?:puedo|podemos)\s+desmontar\s+(?:las?\s+)?ruedas?\b",
    r"\b(?:no|ni|tampoco)\s+(?:puedo|podemos|tengo\s+c[oó]mo)\s+verificar(?:lo)?\b",
    r"\b(?:no|ni|tampoco)\s+tengo\s+(?:un\s+)?(?:reloj\s+comparador|esc[aá]ner|scanner|mult[ií]metro|man[oó]metro|herramientas?)\b",
    r"\bno\s+puedo\s+(?:hacer|realizar)\s+ninguna\s+prueba\b",
    r"\b(?:no|ni)\s+(?:puedo\s+)?desarmar\s+nada\b",
)

PATRONES_SIN_MAS_SINTOMAS = (
    r"\bno\s+(?:puedo|podemos)\b[^.!?]{0,80}\b(?:confirmar|aportar|dar|agregar|indicar)\s+(?:m[aá]s\s+|mas\s+)?s[ií]ntomas?(?:\s+adicionales?)?\b",
    r"\b(?:no\s+(?:puedo|podemos)|ni|tampoco)\s+(?:puedo\s+)?(?:confirmar|aportar|dar|agregar|indicar)\s+(?:m[aá]s\s+|mas\s+)?s[ií]ntomas?(?:\s+adicionales?)?\b",
    r"\bno\s+tengo\s+(?:m[aá]s\s+|mas\s+)?(?:s[ií]ntomas?|datos?|informaci[oó]n|detalles?)\b",
    r"\bno\s+s[eé]\s+(?:m[aá]s|nada\s+m[aá]s)\b",
    r"\bno\s+hay\s+(?:m[aá]s\s+|mas\s+)?s[ií]ntomas?\b",
    r"\bes\s+todo\s+lo\s+que\s+(?:s[eé]|tengo|siento|veo|pasa|ocurre|noto)\b",
    r"\bno\s+puedo\s+aportar\s+nada\s+m[aá]s\b",
)

PATRONES_FEEDBACK = (
    r"\b(?:fue|estuvo)\s+(?:correcta?|util|de\s+ayuda|bien|buena|mala|incorrecta?)\b",
    r"\b(?:me\s+sirvi[oó]|me\s+ayud[oó]|muchas\s+gracias|gracias|excelente|perfecto)\b",
    r"\b(?:no\s+me\s+sirvi[oó]|no\s+me\s+ayud[oó]|no\s+ayud[oó]|mala\s+atenci[oó]n)\b",
    r"\b(?:buena|mala)\s+(?:respuesta|orientaci[oó]n|explicaci[oó]n)\b",
)


def es_imposibilidad_comprobacion_fisica(texto: str) -> bool:
    """Detecta si el usuario indica que no puede realizar comprobaciones físicas."""
    norm = _normalizar(texto)
    return any(re.search(patron, norm) for patron in PATRONES_IMPOSIBILIDAD_FISICA)


def es_sin_mas_sintomas(texto: str) -> bool:
    """Detecta si el usuario indica que no puede confirmar ni aportar más síntomas."""
    norm = _normalizar(texto)
    return any(re.search(patron, norm) for patron in PATRONES_SIN_MAS_SINTOMAS)


def es_imposibilidad_completa(texto: str) -> bool:
    """Detecta imposibilidad física, ausencia de más síntomas o ambas condiciones juntas."""
    norm = _normalizar(texto)
    if es_imposibilidad_comprobacion_fisica(norm):
        return True
    if es_sin_mas_sintomas(norm):
        return True
    return False


def es_feedback_conversacional(texto: str) -> bool:
    """Detecta si la respuesta es una evaluación o feedback del servicio/orientación."""
    norm = _normalizar(texto)
    return any(re.search(patron, norm) for patron in PATRONES_FEEDBACK)


def es_sistema_frenos(estado: Any) -> bool:
    """Determina si el caso actual corresponde o involucra al sistema de frenos."""
    active_sys = (getattr(estado, "active_system", "") or "").lower()
    if any(cl in active_sys for cl in ("embrague", "clutch", "transmision")):
        return False
    if "freno" in active_sys:
        return True

    textos_evaluar = []
    if hasattr(estado, "active_symptoms") and estado.active_symptoms:
        textos_evaluar.extend(estado.active_symptoms)
    if hasattr(estado, "historial_mensajes_usuario") and estado.historial_mensajes_usuario:
        textos_evaluar.extend(estado.historial_mensajes_usuario)
    if hasattr(estado, "falla_principal") and estado.falla_principal:
        textos_evaluar.append(str(estado.falla_principal))

    texto_unido = " ".join(textos_evaluar).lower()
    if any(cl in texto_unido for cl in ("embrague", "clutch")) and not any(
        f in texto_unido for f in ("freno", "frenar", "frenada", "caliper", "cáliper", "pastilla")
    ):
        return False

    terminos_frenos = (
        "freno",
        "frenar",
        "frenada",
        "pastilla",
        "disco de freno",
        "caliper",
        "cáliper",
        "alabeo",
        "chirrido al frenar",
        "liquido de frenos",
        "líquido de frenos",
        "bomba de freno",
    )
    if any(term in texto_unido for term in terminos_frenos):
        return True

    if re.search(r"\bpedal\s+de\s+freno\b", texto_unido) or re.search(
        r"\bdisco\s+(?:de\s+)?freno\b", texto_unido
    ):
        return True

    return False


def generar_orientacion_provisional(
    estado: Any,
    hipotesis_disponibles: Optional[List[dict]] = None,
    falla_principal: Optional[str] = None,
) -> str:
    """Construye una orientación provisional segura para un mecánico."""
    # 1. No insistir en comprobaciones declaradas imposibles
    partes: list[str] = [
        "Entendido. Al no ser posible realizar comprobaciones físicas ni confirmar síntomas "
        "adicionales en este momento, no insistiré en pruebas pendientes. Esta orientación es "
        "provisional y no confirma una falla."
    ]

    # 2. Resumen de síntomas limpios
    sintomas = []
    for s in getattr(estado, "active_symptoms", []) or []:
        if s and not es_imposibilidad_completa(s):
            sintomas.append(s.strip())

    sintomas_txt = "; ".join(sintomas[:2]) if sintomas else "los síntomas observados"

    # 3. Orientación preliminar con datos disponibles (sin confirmar)
    candidatas = list(hipotesis_disponibles or getattr(estado, "top3_actual", []) or [])
    h1 = falla_principal or (candidatas[0].get("falla") if candidatas else None)
    h2 = candidatas[1].get("falla") if len(candidatas) > 1 else None
    h3 = candidatas[2].get("falla") if len(candidatas) > 2 else None

    if h1:
        txt_hipotesis = f"*{h1}*"
        if h2 and h2 != h1:
            txt_hipotesis += f" (y como alternativa técnica: *{h2}*)"
        if h3 and h3 not in (h1, h2):
            txt_hipotesis += f"; tercera hipótesis pendiente: *{h3}*"
        partes.append(
            f"Con los datos recopilados ({sintomas_txt}), la orientación preliminar apunta a {txt_hipotesis}, "
            "quedando solo como hipótesis de trabajo para la revisión presencial. No confirma una falla ni justifica "
            "reemplazar piezas sin verificación física."
        )
    else:
        area = getattr(estado, "active_system", "") or "el sistema en evaluación"
        partes.append(
            f"Con los datos recopilados ({sintomas_txt}), la orientación preliminar se concentra en "
            f"{area}, manteniéndose sin confirmar al carecer de mediciones físicas."
        )

    # 4. El interlocutor es mecánico: conservar la limitación y sugerir solo
    # una comprobación alternativa segura (inspección visual/física directa).
    historial = getattr(estado, "historial_mensajes_usuario", []) or []
    if historial and es_imposibilidad_completa(historial[-1]):
        partes.append(
            "Mantengo el caso pendiente hasta que puedas realizar una comprobación segura "
            "o una revisión presencial. No te pediré efectuar una prueba que hoy no puedes realizar."
        )
    elif getattr(estado, "active_system", "") in {"encendido", "arranque"}:
        partes.append(
            "Dejo registrada la limitación de herramienta. Procede mediante **inspección** visual de bujías, chispa y "
            "conexiones físicas directas; si no dispones de escáner ni multímetro, conserva el caso pendiente "
            "sin sustituir piezas ni confirmar una causa."
        )
    else:
        partes.append(
            "Dejo registrada la limitación de herramienta. Procede mediante **inspección** visual y física de los "
            "componentes periféricos o continúa solo cuando exista una comprobación segura y pertinente disponible; "
            "no confirmes una causa ni sustituyas piezas con la evidencia actual."
        )

    if es_sistema_frenos(estado):
        partes.append(
            "⚠️ *Atención en seguridad:* Al tratarse del sistema de frenos, la revisión presencial "
            "en taller es indispensable y prioritaria antes de continuar circulando, para descartar "
            "desgaste crítico o riesgo de pérdida de frenado."
        )

    # 5. Preservación del caso
    partes.append("Conservo registrados los datos del vehículo, síntomas y descartes de este caso.")

    return "\n\n".join(partes)
