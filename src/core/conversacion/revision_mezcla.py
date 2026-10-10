"""Revisiones concretas que permiten avanzar sin repetir el gate de mezcla."""

import re
import unicodedata

from src.core.conversacion.models import ConversationState, FactType, QuestionIntent


def _normalizar(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )


def registrar_revision_mezcla(estado: ConversationState, texto: str) -> dict | None:
    """Vincula un resultado normal a una pieza explícita o a un único punto solicitado."""
    if estado.active_system != "combustible_admision":
        return None
    normalizado = _normalizar(texto)
    if "?" in normalizado or re.search(
        r"\bno\s+(?:esta(?:n)?\s+(?:bien|normal)|es\s+correct[oa]|(?:lo\s+)?revis[ea])\b",
        normalizado,
    ):
        return None
    revisada = bool(re.search(r"\b(?:revis[eao]|chequee?|cheque|probe|comprobe)\b", normalizado))
    normal = bool(re.search(r"\b(?:esta(?:n)?\s+bien|correct[oa]s?|normal|descartad[oa])\b", normalizado))
    referencia = bool(re.search(r"\b(?:eso|esa\s+parte|lo|la)\b", normalizado))
    if not (normal or (revisada and referencia)):
        return None
    patrones = (
        ("cuerpo_aceleracion", r"\bcuerpo(?:\s+de\s+aceleracion)?\b|\biac\b"),
        ("maf", r"\bmaf\b"),
        ("inyectores", r"\b(?:inyectores?|injectores?)\b"),
        ("presion_combustible", r"presion\s+(?:de\s+)?combustible"),
        ("vacio", r"fuga(?:s)?\s+de\s+vacio|entrada\s+de\s+aire"),
    )
    componente = next((nombre for nombre, patron in patrones if re.search(patron, normalizado)), None)
    hipotesis = ""
    if componente is None and referencia:
        pregunta = estado.ultima_pregunta() or {}
        candidatos = pregunta.get("hipotesis") or []
        if (
            len(candidatos) == 1
            and pregunta.get("intent") in (
                QuestionIntent.CONFIRMACION_ALTERNATIVA.value,
                QuestionIntent.COMPONENTE_REVISADO.value,
            )
        ):
            candidato = candidatos[0]
            hipotesis = str(candidato.get("falla", "") if isinstance(candidato, dict) else candidato)
            componente = next(
                (nombre for nombre, patron in patrones if re.search(patron, _normalizar(hipotesis))), None
            )
    if componente is None:
        return None
    # Una revisión nombrada solo se descarta si el usuario declara resultado normal.
    if not normal and not hipotesis:
        return None
    estado.registrar_hecho(
        f"revision_normal_{componente}", "revisión normal reportada por el mecánico",
        categoria="componente_descartado", texto_crudo=texto, tipo=FactType.CONDICION,
    )
    if componente == "cuerpo_aceleracion":
        hipotesis = "Cuerpo de aceleración o válvula IAC sucia"
    if hipotesis and hipotesis not in estado.hipotesis_descartadas:
        estado.hipotesis_descartadas.append(hipotesis)
    hecho = estado.registrar_hecho(
        "revision_concreta_mezcla", componente, categoria="inspeccion",
        texto_crudo=texto, tipo=FactType.CONDICION,
    )
    return hecho.to_dict()


def siguiente_comprobacion(estado: ConversationState) -> str | None:
    """Avanza por comprobaciones del mismo sistema sin asignar una falla ni confianza."""
    opciones = (
        ("maf", "¿La lectura de flujo del MAF cambia al acelerar, o se queda fija/irregular?"),
        ("vacio", "¿Se comprobó una entrada de aire no medida en mangueras y uniones de admisión?"),
        ("inyectores", "¿Se comprobó el balance/caudal de los inyectores?"),
        ("presion_combustible", "¿Se comprobó la presión de combustible frente a la especificación del vehículo?"),
    )
    for componente, pregunta in opciones:
        if estado.obtener_hecho(f"revision_normal_{componente}") is None and not estado.ya_preguntado_texto(pregunta):
            return pregunta
    return None
