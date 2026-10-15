"""Compatibilidad de un procedimiento auxiliar sin convertirlo en diagnóstico."""

from src.core.diagnostico.enrutador_sistema import detectar_areas_tecnicas


def procedimiento_apoya_hipotesis(hipotesis: str, titulo: str, meta: dict) -> bool:
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
