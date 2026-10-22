"""Separación conservadora de problemas de frenos y suspensión del mismo vehículo."""

from __future__ import annotations

import re
import unicodedata


def normalizar(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def sistemas_descritos(texto: str) -> set[str]:
    texto = normalizar(texto)
    sistemas = set()
    if re.search(r"\b(?:frenos?|frenar|pedal|caliper|servofreno)\b", texto):
        sistemas.add("frenos")
    # Una rueda o un ruido, por sí solos, no identifican un subsistema.
    if re.search(r"\b(?:amortiguadores?|rotulas?|bieletas?|suspension|tren delantero)\b", texto) or (
        re.search(r"\b(?:baches?|rompemuelles|desniveles)\b", texto)
        and re.search(r"\b(?:golp\w*|clac|rebot\w*|oscil\w*)\b", texto)
    ):
        sistemas.add("suspension")
    return sistemas


def hay_pedal_critico(texto: str) -> bool:
    texto = normalizar(texto)
    return bool(re.search(
        r"\bpedal\b.{0,100}\b(?:se hunde|al fondo|hasta el fondo|al piso|yendose al piso)\b",
        texto,
    )) and not bool(re.search(r"\b(?:no|ya no)\s+se\s+hunde\b", texto))


def separar_problema(estado, mensaje: str) -> bool:
    """Solo bifurca descripciones inequívocas; las consultas mixtas conservan contexto."""
    actuales = sistemas_descritos(mensaje)
    # Mencionar una pieza para preguntar por ella no constituye otro problema.
    if not re.search(
        r"\b(?:golp\w*|clac|rebot\w*|oscil\w*|vibr\w*|esponjos\w*|se hunde|chirr\w*)\b",
        normalizar(mensaje),
    ):
        return False
    previos = sistemas_descritos(" ".join([
        *estado.active_symptoms, *estado.historial_mensajes_usuario,
    ]))
    if len(previos) > 1:
        # Una sesión del incidente puede estar ya contaminada. No usar esa
        # mezcla como motivo para seguir concatenando: contrastar la hipótesis
        # activa con la descripción inequívoca del nuevo problema.
        diagnostico_activo = sistemas_descritos(str(estado.falla_principal or ""))
        if len(diagnostico_activo) == 1:
            previos = diagnostico_activo
    if len(actuales) != 1 or len(previos) != 1 or actuales == previos:
        return False
    if not estado.case_id:
        return False
    estado.iniciar_nuevo_caso(preservar_vehiculo=True)
    estado.active_system = next(iter(actuales))
    return True


def advertencia_freno_archivado(estado) -> str:
    """El riesgo vial histórico no se convierte en evidencia para el nuevo diagnóstico."""
    if estado is None or not any((estado.placa, estado.marca, estado.modelo)):
        return ""
    for caso in reversed(estado.hechos_historicos):
        if any(caso.get(k) != getattr(estado, k) for k in ("placa", "marca", "modelo", "anio")):
            continue
        texto = " ".join(caso.get("historial_mensajes_usuario", []))
        if hay_pedal_critico(texto):
            return (
                "Advertencia pendiente del caso anterior de frenos: se reportó hundimiento del pedal. "
                "No circules ni hagas pruebas de ruta hasta que un profesional verifique la seguridad "
                "del frenado; solicita traslado seguro. Esto no confirma una fuga ni explica el nuevo "
                "problema actual.\n\n"
            )
    return ""
