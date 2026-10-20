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
    r"\b(?:todav[ií]a|a[uú]n)\s+no\s+(?:he\s+)?(?:realizado|hecho|revisado|comprobado|verificado)\b",
    r"\b(?:sin|no\s+tengo)\s+herramientas?\b",
    r"\bqu[eé]\s+(?:puedo|podemos|se\s+puede)\s+(?:revisar|hacer|ver)(?:\s+visualmente)?\b",
    r"\b(?:inspecci[oó]n|revisi[oó]n|comprobaci[oó]n)\s+visual\s+segura\b",
)

PATRONES_SIN_MAS_SINTOMAS = (
    r"\bno\s+(?:puedo|podemos)\b[^.!?]{0,80}\b(?:confirmar|aportar|dar|agregar|indicar)\s+(?:m[aá]s\s+|mas\s+)?s[ií]ntomas?(?:\s+adicionales?)?\b",
    r"\b(?:no\s+(?:puedo|podemos)|ni|tampoco)\s+(?:puedo\s+)?(?:confirmar|aportar|dar|agregar|indicar)\s+(?:m[aá]s\s+|mas\s+)?s[ií]ntomas?(?:\s+adicionales?)?\b",
    r"\bno\s+tengo\s+(?:m[aá]s\s+|mas\s+)?(?:s[ií]ntomas?|datos?|informaci[oó]n|detalles?)\b",
    r"\bno\s+s[eé]\s+(?:m[aás]|nada\s+m[aá]s)\b",
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


def es_sintoma_mecanico_valido(s: str) -> bool:
    """Verifica que el texto represente un síntoma mecánico genuino y no una palabra de control."""
    if not s or not isinstance(s, str):
        return False
    norm = _normalizar(s)
    if not norm:
        return False
    # Excluir palabras de control afirmativas, negativas o de menú
    if norm in {
        "si", "s", "no", "correcto", "negativo", "exacto", "falso", "incorrecto", "incorrecta", "fue incorrecto", "fue incorrecta", "fue correcto", "fue correcta", "esta bien", "esta mal",
        "1", "2", "3", "primera", "segunda", "tercera", "primero", "segundo", "tercero",
        "opcion 1", "opcion 2", "opcion 3", "la 1", "la 2", "la 3",
        "la primera", "la 1ra", "la segunda", "la 2da", "la tercera", "la 3ra",
        "el primero", "el segundo", "el tercero", "ninguna", "no se", "ok", "vale",
    }:
        return False
    # Excluir si solo contiene números o referencias a opciones
    if re.fullmatch(r"(?:la\s+|el\s+)?(?:primera?|segunda?|tercera?|[1-9](?:ra|da|ro)?|[1-9])", norm):
        return False
    # Excluir imposibilidad o sin más síntomas
    if es_imposibilidad_completa(s):
        return False
    # Excluir saludos o agradecimientos
    if norm in {"hola", "buenas", "buenos dias", "buenas tardes", "gracias", "muchas gracias"}:
        return False
    return True


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


def obtener_orientacion_visual_segura(estado: Any = None, falla: str | None = None) -> list[str]:
    """Genera comprobaciones visuales externas, pertinentes y 100% seguras sin herramientas ni desmontajes."""
    es_frenos = False
    if estado is not None and es_sistema_frenos(estado):
        es_frenos = True
    elif falla and any(k in falla.lower() for k in ("freno", "cilindro maestro", "pastilla", "disco", "caliper", "cáliper", "pedal")):
        es_frenos = True
    elif estado is not None:
        textos = []
        if hasattr(estado, "active_symptoms") and estado.active_symptoms:
            textos.extend(estado.active_symptoms)
        if hasattr(estado, "sintoma_principal") and estado.sintoma_principal:
            textos.append(estado.sintoma_principal)
        if any(any(k in str(t).lower() for k in ("freno", "pedal", "pastilla", "disco", "liquido de freno", "esponjoso")) for t in textos):
            es_frenos = True

    guias = []
    if es_frenos:
        guias.append(
            "🔍 *Inspección visual externa segura (vehículo apagado y estacionado en terreno plano):*\n"
            "1. *Nivel de líquido de frenos:* Con el vehículo apagado, abre el capó y observa a través del "
            "depósito translúcido si el líquido se encuentra entre las líneas MIN y MAX (sin abrir la tapa "
            "ni retirarla para evitar introducir humedad o aire al circuito).\n"
            "2. *Fugas externas visibles:* Revisa visualmente el piso debajo del vehículo y la cara interna "
            "de las ruedas y neumáticos en busca de goteos o manchas de fluido, así como las uniones visibles de la bomba de frenos.\n"
            "3. *Seguridad prioritaria:* No conduzcas el vehículo para reproducir síntomas con el pedal esponjoso, "
            "ni intentes purgas o desmontajes sin herramientas y capacitación especializada."
        )
        return guias

    falla_lower = (falla or "").lower()
    sintomas_str = " ".join(getattr(estado, "active_symptoms", []) or []).lower() if estado else ""
    if any(k in falla_lower or k in sintomas_str for k in ("refrigera", "temperatura", "recalienta", "radiador")):
        guias.append(
            "🔍 *Inspección visual externa segura (motor totalmente frío y apagado):*\n"
            "1. *Depósito de reserva:* Revisa a través del plástico translúcido que el nivel de refrigerante esté entre MIN y MAX (sin abrir la tapa ni el sistema con motor caliente).\n"
            "2. *Mangueras y radiador:* Observa si hay marcas blancas, verdes o goteos visibles en mangueras externas o en el suelo.\n"
            "3. *Seguridad:* No intentes desmontar piezas ni abrir tapas a presión sin herramientas ni protección."
        )
        return guias

    if any(k in falla_lower or k in sintomas_str for k in ("bateria", "batería", "alternador", "arranque")):
        guias.append(
            "🔍 *Inspección visual externa segura (motor apagado y sin llave en contacto):*\n"
            "1. *Bornes de batería:* Observa si presentan sulfatación blanquecina o terminales flojos.\n"
            "2. *Correa de accesorios:* Verifica visualmente que no presente grietas notorias sin manipular piezas.\n"
            "3. *Seguridad:* No manipules bornes ni cableado sin herramientas aisladas."
        )
        return guias

    guias.append(
        "🔍 *Inspección visual externa segura (vehículo apagado y estacionado con freno de mano):*\n"
        "1. *Revisión exterior:* Con el motor apagado, realiza una inspección visual directa del componente y conectores accesibles a simple vista.\n"
        "2. *Inspección de fluidos:* Revisa si existen manchas de fluidos en el piso o conexiones sueltas sin desmontar piezas ni forzar componentes.\n"
        "3. *Seguridad:* Si no dispones de herramientas adecuadas, mantén el vehículo detenido hasta contar con el equipo de diagnóstico necesario."
    )
    return guias


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

    # 2. Resumen de síntomas limpios (filtrando estrictamente palabras de control)
    sintomas = [
        s.strip() for s in getattr(estado, "active_symptoms", []) or []
        if es_sintoma_mecanico_valido(s)
    ]

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

    # 4. Proporcionar comprobaciones visuales concretas y seguras sin herramientas
    guias_visuales = obtener_orientacion_visual_segura(estado, falla=h1)
    if guias_visuales:
        partes.extend(guias_visuales)
    else:
        partes.append(
            "Dejo registrada la limitación de herramienta. Continúa solo cuando exista una "
            "comprobación segura y pertinente disponible; no confirmes una causa ni sustituyas piezas "
            "con la evidencia actual."
        )

    historial = getattr(estado, "historial_mensajes_usuario", []) or []
    if historial and es_imposibilidad_completa(historial[-1]):
        partes.append(
            "Mantengo el caso pendiente hasta que puedas realizar una comprobación segura "
            "o una revisión presencial. No te pediré efectuar una prueba que hoy no puedes realizar."
        )

    if es_sistema_frenos(estado) and not any("Atención en seguridad" in p for p in partes):
        partes.append(
            "⚠️ *Atención en seguridad:* Al tratarse del sistema de frenos, la revisión presencial "
            "en taller es indispensable y prioritaria antes de continuar circulando, para descartar "
            "desgaste crítico o riesgo de pérdida de frenado."
        )

    # 5. Preservación del caso
    partes.append("Conservo registrados los datos del vehículo, síntomas y descartes de este caso.")

    return "\n\n".join(partes)
