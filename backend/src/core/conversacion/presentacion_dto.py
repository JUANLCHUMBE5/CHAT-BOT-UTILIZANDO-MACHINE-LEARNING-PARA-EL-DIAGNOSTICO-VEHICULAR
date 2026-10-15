"""Conserva la inferencia original y alinea el DTO con las hipótesis presentables."""

from src.core.diagnostico.models import PrediccionML, ResultadoDiagnostico


def alinear_predicciones_presentadas(dto, hipotesis):
    if not isinstance(dto, ResultadoDiagnostico):
        return dto
    raw = dto.predicciones_ml_raw or dto.predicciones_ml
    return dto.model_copy(update={
        "predicciones_ml_raw": [item.model_copy(deep=True) for item in raw],
        "predicciones_ml": [PrediccionML(**item) for item in hipotesis],
    })
