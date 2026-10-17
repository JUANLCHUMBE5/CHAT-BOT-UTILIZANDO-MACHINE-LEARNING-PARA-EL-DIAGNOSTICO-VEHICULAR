"""Conserva la inferencia original y alinea el DTO con las hipótesis presentables."""

from src.core.diagnostico.models import PrediccionML, ResultadoDiagnostico


def alinear_predicciones_presentadas(dto, hipotesis):
    if not isinstance(dto, ResultadoDiagnostico):
        return dto
    raw = dto.predicciones_ml_raw or dto.predicciones_ml
    originales = {item.falla: item.model_dump() for item in dto.predicciones_ml}
    presentables = [PrediccionML(**{**originales.get(item.get("falla"), {}), **item}) for item in hipotesis]
    update_data = {
        "predicciones_ml_raw": [item.model_copy(deep=True) for item in raw],
        "predicciones_ml": presentables,
    }
    if hipotesis:
        update_data["diagnostico_ml"] = hipotesis[0].get("falla")
        update_data["confianza_ml"] = float(hipotesis[0].get("probabilidad", 0.0))
    else:
        update_data["diagnostico_ml"] = "Sin hipótesis compatible"
        update_data["motivo_abstencion"] = "SIN_HIPOTESIS_PRESENTABLE"
        update_data["requiere_revision_humana"] = True
        update_data["confianza_ml"] = 0.0
    return dto.model_copy(update=update_data)
