"""Contratos del seguimiento experimental de taller."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import AliasChoices, BaseModel, Field

FaseEvaluacion = Literal["Pre-test", "Post-test", "Piloto"]
EstadoRegistro = Literal["borrador", "verificado", "excluido"]


class CasoValidacionDTO(BaseModel):
    item: int
    fase: str
    fecha: str
    placa_enmascarada: str
    placa_hash: str
    marca_modelo: str
    sintoma: str
    descripcion_sintoma: Optional[str] = None
    vehiculo_anio: Optional[int] = None
    vehiculo_kilometraje: Optional[int] = None
    vehiculo_combustible: Optional[str] = None
    vehiculo_transmision: Optional[str] = None
    falla_real: str
    chatbot_prediccion: str
    sistema_afectado_probable: Optional[str] = None
    campos_completos: int
    cantidad_campos_completos: int = 0
    detalles_campos: Optional[Dict[str, Any]] = None
    tiempo_diagnostico_minutos: int
    prediccion_correcta: int
    taller_id: Optional[str] = None
    mecanico_id: Optional[str] = None
    metodo_confirmacion: Optional[str] = "Inspección Visual en Elevador"
    evidencia_ref: Optional[str] = None
    estado_registro: str = "borrador"
    tipo_registro: Optional[str] = "THESIS_POSTTEST"
    conversacion_id: Optional[str] = None
    diagnostico_id: Optional[str] = None
    sintoma_registrado_correctamente: Optional[int] = None
    validado_por_id: Optional[str] = None
    fecha_validacion: Optional[str] = None
    normalizacion_correcta: Optional[int] = None
    extraccion_correcta: Optional[int] = None
    clasificacion_procesada: Optional[int] = None
    procesamiento_validado: Optional[int] = None
    tiempo_inferencia_ml_ms: Optional[int] = None


class CrearCasoValidacionDTO(BaseModel):
    fase: FaseEvaluacion = Field(default="Post-test")
    fecha: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    placa: str = Field(min_length=3, max_length=15)
    marca_modelo: str = Field(min_length=2, max_length=100)
    sintoma: str = Field(min_length=5, max_length=2000)
    descripcion_sintoma: Optional[str] = Field(default=None, max_length=2000)
    vehiculo_anio: Optional[int] = Field(default=None, ge=1950, le=2100)
    vehiculo_kilometraje: Optional[int] = Field(default=None, ge=0)
    vehiculo_combustible: Optional[str] = Field(default=None, max_length=30)
    vehiculo_transmision: Optional[str] = Field(default=None, max_length=30)
    falla_real: str = Field(min_length=3, max_length=1000)
    # Mantiene compatibilidad con registros existentes; en pre-test representa la hipótesis manual.
    chatbot_prediccion: str = Field(
        min_length=3, max_length=1000,
        validation_alias=AliasChoices("prediccion_inicial", "chatbot_prediccion"),
    )
    sistema_afectado_probable: Optional[str] = Field(default=None, max_length=80)
    campos_completos: int = Field(ge=0, le=1)
    tiempo_diagnostico_minutos: int = Field(ge=1, le=600)
    prediccion_correcta: int = Field(ge=0, le=1)
    metodo_confirmacion: Optional[str] = Field(default="Inspección Visual + Escáner OBD", max_length=500)
    evidencia_ref: Optional[str] = Field(default=None, max_length=500)
    estado_registro: EstadoRegistro = Field(default="borrador")
    tipo_registro: Optional[Literal["DEVELOPMENT", "REGRESSION", "THESIS_PRETEST", "THESIS_POSTTEST"]] = None
    conversacion_id: Optional[str] = None
    diagnostico_id: Optional[str] = None
    sintoma_registrado_correctamente: Optional[int] = Field(default=None, ge=0, le=1)
    normalizacion_correcta: Optional[int] = Field(default=None, ge=0, le=1)
    extraccion_correcta: Optional[int] = Field(default=None, ge=0, le=1)
    clasificacion_procesada: Optional[int] = Field(default=None, ge=0, le=1)
    procesamiento_validado: Optional[int] = Field(default=None, ge=0, le=1)
    tiempo_inferencia_ml_ms: Optional[int] = Field(default=None, ge=0)


class MetricasVariableIndependienteDTO(BaseModel):
    indicador1_sintomas_correctos_pct: Optional[float] = None
    indicador2_procesamiento_correcto_pct: Optional[float] = None
    indicador3_exactitud_ml_pct: Optional[float] = None
    casos_verificados_evaluados: int = 0
    nota_metodologica: str = "Cálculo exclusivo sobre casos con estado verificado con confirmación física en taller."


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
    casos_verificados: int = 0
    total_casos_verificados: int = 0
    total_casos_borrador: int = 0
    porcentaje_sintomas_correctos: Optional[float] = None
    porcentaje_datos_procesados_correctos: Optional[float] = None
    exactitud_modelo_validada: Optional[float] = None
    variable_independiente: Optional[MetricasVariableIndependienteDTO] = None
    distribucion_marcas: List[Dict[str, Any]]
    top_fallas_reales: List[Dict[str, Any]]
    nota_metodologica: str = (
        "Comparación descriptiva de registros guardados por taller y período. "
        "Los casos Piloto y en borrador se excluyen de los indicadores oficiales pre-test y post-test."
    )
