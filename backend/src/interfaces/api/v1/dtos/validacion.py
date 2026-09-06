"""Contratos del seguimiento experimental de taller."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import AliasChoices, BaseModel, Field

FaseEvaluacion = Literal["Pre-test", "Post-test", "Piloto"]


class CasoValidacionDTO(BaseModel):
    item: int
    fase: str
    fecha: str
    placa_enmascarada: str
    placa_hash: str
    marca_modelo: str
    sintoma: str
    falla_real: str
    chatbot_prediccion: str
    campos_completos: int
    tiempo_diagnostico_minutos: int
    prediccion_correcta: int
    taller_id: Optional[str] = None
    mecanico_id: Optional[str] = None
    metodo_confirmacion: Optional[str] = "Inspección Visual en Elevador"
    evidencia_ref: Optional[str] = None


class CrearCasoValidacionDTO(BaseModel):
    fase: FaseEvaluacion = Field(default="Post-test")
    fecha: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    placa: str = Field(min_length=3, max_length=15)
    marca_modelo: str = Field(min_length=2, max_length=100)
    sintoma: str = Field(min_length=5, max_length=2000)
    falla_real: str = Field(min_length=3, max_length=1000)
    # Mantiene compatibilidad con registros existentes; en pre-test representa la hipótesis manual.
    chatbot_prediccion: str = Field(
        min_length=3, max_length=1000,
        validation_alias=AliasChoices("prediccion_inicial", "chatbot_prediccion"),
    )
    campos_completos: int = Field(ge=0, le=1)
    tiempo_diagnostico_minutos: int = Field(ge=1, le=600)
    prediccion_correcta: int = Field(ge=0, le=1)
    metodo_confirmacion: Optional[str] = Field(default="Inspección Visual + Escáner OBD", max_length=500)
    evidencia_ref: Optional[str] = Field(default=None, max_length=500)


class MetricasValidacionResponseDTO(BaseModel):
    registros_completos_pretest_porcentaje: float = 0.0
    registros_completos_posttest_porcentaje: float = 0.0
    total_casos: int
    total_aciertos: int
    total_desaciertos: int
    tasa_acierto_global_porcentaje: float
    casos_pretest: int
    tasa_acierto_pretest_porcentaje: float
    tiempo_promedio_pretest_min: float
    casos_posttest: int
    tasa_acierto_posttest_porcentaje: float
    tiempo_promedio_posttest_min: float
    reduccion_tiempo_porcentaje: float
    distribucion_marcas: List[Dict[str, Any]]
    top_fallas_reales: List[Dict[str, Any]]
    nota_metodologica: str = (
        "Comparación descriptiva de registros guardados por taller y período. "
        "Los casos Piloto se excluyen de los indicadores pre-test y post-test."
    )
