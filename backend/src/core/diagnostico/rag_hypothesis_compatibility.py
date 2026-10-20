"""Compatibilidad de un procedimiento auxiliar sin convertirlo en diagnóstico."""

from src.core.diagnostico.enrutador_sistema import detectar_areas_tecnicas
from src.core.diagnostico.taxonomia_sistemas import FALLA_A_SISTEMA

_SISTEMAS_AFINES = {
    ("INSTRUMENTAL", "MOTOR"),
    ("MOTOR", "INSTRUMENTAL"),
    ("TRANSMISION", "MOTOR"),
    ("MOTOR", "TRANSMISION"),
    ("SUSPENSION", "DIRECCION"),
    ("DIRECCION", "SUSPENSION"),
    ("SUSPENSION_CHASIS", "DIRECCION"),
    ("DIRECCION", "SUSPENSION_CHASIS"),
    ("SUSPENSION", "SUSPENSION_CHASIS"),
    ("SUSPENSION_CHASIS", "SUSPENSION"),
}


def procedimiento_apoya_hipotesis(hipotesis: str, titulo: str, meta: dict) -> bool:
    if not hipotesis or not titulo:
        return False

    sistema_hipotesis = FALLA_A_SISTEMA.get(hipotesis)
    sistema_doc = (meta.get("sistema") or meta.get("system") or "").strip().upper()

    # Si ambos tienen sistema definido y son incompatibles (no iguales ni afines), rechazar
    if sistema_hipotesis and sistema_doc:
        son_compatibles = (
            sistema_hipotesis == sistema_doc
            or (sistema_hipotesis, sistema_doc) in _SISTEMAS_AFINES
        )
        if not son_compatibles:
            return False

    falla_documental = meta.get("falla")
    if not falla_documental or hipotesis == falla_documental:
        return True
    if meta.get("knowledge_type") not in {"PROCEDURAL", "TRANSVERSAL"}:
        return False
    # Compartir MOTOR no basta: deben coincidir las áreas técnicas de la
    # hipótesis, del título del procedimiento y de su etiqueta documental.
    return bool(
        set(detectar_areas_tecnicas(hipotesis))
        & set(detectar_areas_tecnicas(titulo))
        & set(detectar_areas_tecnicas(str(falla_documental)))
    )
