"""Manejo de contexto de combustible (GNV, GLP, Gasolina) y pérdidas de potencia."""

from __future__ import annotations

from typing import Optional

from src.core.diagnostico.models import ResultadoDiagnostico
from src.core.fuel_context_parser import extraer_contexto_combustible

__all__ = [
    "es_perdida_potencia_bajo_carga",
    "texto_modo_combustible",
    "resultado_solicitud_combustible",
    "extraer_contexto_combustible",
]


def es_perdida_potencia_bajo_carga(texto: str) -> bool:
    """Detecta si el síntoma describe pérdida de potencia específicamente bajo carga o aceleración."""
    limpio = texto.lower()
    sistemas_no_combustible = (
        "freno", "frenar", "frenada", "pastilla", "zapata", "disco", "liquido de freno",
        "pedal de freno", "pedal se hunde", "bomba de freno", "servofreno", "booster",
        "timon", "timón", "cremallera", "rotula", "rótula", "amortiguador", "palier",
        "homocinetica", "homocinética", "zumbido", "rodaje", "rodamiento", "llanta", "aro",
        "embrague", "clutch", "disco de embrague", "collarin", "patina el embrague",
        "recalienta", "hierve", "culata", "bateria", "alternador"
    )
    if any(term in limpio for term in sistemas_no_combustible):
        return False

    sintomas = (
        "pierde fuerza", "pierde potencia", "perdida de fuerza", "perdida de potencia",
        "pérdida de fuerza", "pérdida de potencia",
        "sin fuerza", "se aguanta", "no acelera", "no responde al acelerar",
        "tirones al acelerar", "tironea al acelerar", "jalonea al acelerar",
    )
    carga = ("aceler", "subida", "velocidad", "carga", "corriendo", "carretera")
    return any(sintoma in limpio for sintoma in sintomas) and any(valor in limpio for valor in carga)


def texto_modo_combustible(combustible: str, modo: str) -> str:
    """Genera texto descriptivo del modo de falla según combustible."""
    descripciones = {
        "solo_gas": f"La falla ocurre solo usando {combustible}; en gasolina funciona bien.",
        "solo_gasolina": "La falla ocurre solo usando gasolina; con gas funciona bien.",
        "ambos": "La falla ocurre tanto usando gasolina como usando gas.",
    }
    return f"Combustible confirmado: {combustible}. {descripciones.get(modo, '')}"


def resultado_solicitud_combustible(
    sesion, combustible: Optional[str] = None
) -> ResultadoDiagnostico:
    """Genera el resultado que solicita aclaración sobre el tipo de combustible."""
    if combustible in {"GNV", "GLP"}:
        pregunta = f"🔎 ¿Falla solo en *{combustible}*, en gasolina o en ambos?"
    else:
        pregunta = "🔎 ¿Usa *GNV*, *GLP* o gasolina? ¿En cuál presenta la falla?"
    return ResultadoDiagnostico(
        respuesta_texto=pregunta,
        diagnostico_ml="Pendiente de comparar el modo de combustible",
        confianza_ml=0.0,
        contexto_manual="",
        titulo_manual="",
        requiere_revision_humana=True,
        estado_sesion="esperando_combustible",
        modo_diagnostico="esperando_clarificacion",
        sintoma_evaluado=sesion.consulta_combustible_pendiente or "",
        tipo_consulta="aclaracion",
    )
