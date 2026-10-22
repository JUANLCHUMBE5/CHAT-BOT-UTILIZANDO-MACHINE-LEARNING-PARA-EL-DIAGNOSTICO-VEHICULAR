"""Orden de inspección por síntomas observados, sin recalibrar el Linear SVM."""

from __future__ import annotations

import re
from typing import Any

from src.core.conversacion.aislamiento_subsistemas import normalizar

CRITERIO_REBOTE = "INSPECCION_SUSPENSION_POR_REBOTE"


def _rebote_reportado(texto: str) -> bool:
    """No toma una pregunta hipotética o una negación por un síntoma observado."""
    for clausula in re.split(r"[.;!?]", normalizar(texto)):
        if re.search(r"\b(?:puede|podria|podrian|si acaso)\b", clausula):
            continue
        if re.search(
            r"\b(?:no|sin|nunca|niega)\s+(?:(?:se|hay|presenta|tiene|siente|percibe|ningun|ninguna)\s+){0,3}"
            r"(?:rebot\w*|oscil\w*)\b", clausula,
        ):
            continue
        if re.search(r"\b(?:rebota\w*|rebotando|rebote\s+excesivo|oscilacion\s+excesiva)\b", clausula):
            return True
    return False


def ordenar_inspeccion(candidatas: list[dict[str, Any]], estado: Any) -> list[dict[str, Any]]:
    """Prioriza revisión de amortiguación sin descartar transmisión ni inventar porcentajes.

    Recibe solo candidatas ya admitidas por compatibilidad/descarte. La traza RAW
    conserva el orden del modelo. La ausencia de candidatas no genera hipótesis nuevas.
    """
    mensajes = list(getattr(estado, "historial_mensajes_usuario", []) or [])
    if not candidatas or not mensajes:
        return candidatas
    texto = normalizar(" ".join(mensajes))
    if not re.search(r"\b(?:baches?|rompemuelles|desniveles|irregularidades)\b", texto):
        return candidatas
    ultimo_rebote = next((m for m in reversed(mensajes) if re.search(r"\b(?:rebot\w*|oscil\w*)\b", normalizar(m))), "")
    if not _rebote_reportado(ultimo_rebote):
        return candidatas
    # No desplazar una queja mixta o indicios específicos de transmisión/tracción.
    if re.search(
        r"\b(?:aceler\w*|traccion|homocinetic\w*|palier\w*|"
        r"girar|girando|doblar|doblando|fren\w*|pedal)\b", texto,
    ):
        return candidatas
    preferidas, restantes = [], []
    for candidata in candidatas:
        falla = normalizar(str(candidata.get("falla", "")))
        if re.search(r"\b(?:amortiguador\w*|bujes?\s+de\s+suspension)\b", falla):
            preferidas.append(dict(candidata))
        else:
            restantes.append(dict(candidata))
    if not preferidas or not restantes or candidatas[0] == preferidas[0]:
        return candidatas
    preferidas[0]["criterio_presentacion"] = CRITERIO_REBOTE
    return preferidas + restantes


def sincronizar_prioridad(resultado: dict[str, Any]) -> None:
    """Mantiene el menú del DTO en el mismo orden que WhatsApp, conservando RAW."""
    estado = resultado.get("estado")
    top = getattr(estado, "top3_actual", [])
    dto = resultado.get("dto")
    if not top or top[0].get("criterio_presentacion") != CRITERIO_REBOTE or dto is None:
        return
    por_falla = {p.falla: p for p in dto.predicciones_ml}
    if any(c["falla"] not in por_falla for c in top):
        return
    resultado["dto"] = dto.model_copy(update={
        "respuesta_texto": resultado["respuesta_texto"],
        "diagnostico_ml": top[0]["falla"],
        "confianza_ml": top[0]["probabilidad"],
        "predicciones_ml": [por_falla[c["falla"]].model_copy() for c in top],
        "predicciones_ml_raw": dto.predicciones_ml_raw or list(dto.predicciones_ml),
        "motivo_prioridad": CRITERIO_REBOTE,
        "es_orientacion_provisional": True,
        "requiere_revision_humana": True,
    })
    resultado["diagnostico_ml"] = top[0]["falla"]
    resultado["confianza_ml"] = top[0]["probabilidad"]
