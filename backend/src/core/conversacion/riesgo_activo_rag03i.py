"""Prioridad y persistencia de riesgo activo, trasladadas desde RAG-03I."""
import re
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.diagnostico.patrones_seguridad_fisica import detectar_riesgo_fisico


def banner_riesgo_actual(estado, texto):
    actual = detectar_riesgo_fisico(texto)
    if actual:
        return actual
    traza = estado.trazabilidad[-1] if estado.trazabilidad else {}
    persiste = (
        traza.get("decision") == "SEGURIDAD_CRITICA"
        and not ExtractorHechos.contiene_informacion_diagnostica(texto)
        and not ExtractorHechos.clasificar_solicitud_caso(texto)
        and not (
            "REGENERACIÓN" in str(traza.get("respuesta_enviada", "")).upper()
            and re.search(r"\b(?:dren[eé]|vaci[eé])\b", texto, re.I)
            and re.search(r"\baceite\s+nuevo\b", texto, re.I)
        )
    )
    return traza.get("respuesta_enviada") if persiste else None
