"""Contratos HTTP del flujo de diagnóstico."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ActualizarEstadoDTO(BaseModel):
    nuevo_estado: Literal["generado", "en_revision", "confirmado", "descartado"]
    notas_mecanico: Optional[str] = Field(default=None, max_length=4000)


class PrediccionMLDTO(BaseModel):
    orden: int
    falla: str
    probabilidad: float


class EtapaProcesamientoDTO(BaseModel):
    clave: str
    nombre: str
    estado: str
    duracion_ms: int = 0
    detalle: Optional[str] = None


class ItemDiagnosticoDTO(BaseModel):
    id: str
    sintoma_original: str
    sintoma_normalizado: str
    falla_predicha: str
    confianza: float
    similitud_rag: float = 0.0
    modo_diagnostico: str
    estado: str
    fuente: str
    mecanico_id: str
    mecanico_nombre: str
    cliente_nombre: str = "Cliente WhatsApp"
    cliente_telefono: Optional[str] = None
    placa_vehiculo: str
    marca_modelo: str
    fecha_hora: str
    duracion_ms: int
    procedimiento_rag: str
    fuente_manual: Optional[str] = None
    version_corpus_rag: Optional[str] = None
    tiempo_gravedad: str
    sintesis_llm: Optional[str] = None
    notas_mecanico: Optional[str] = None
    fecha_confirmacion: Optional[str] = None
    predicciones_ml: List[PrediccionMLDTO] = Field(default_factory=list)
    etapas_procesamiento: List[EtapaProcesamientoDTO] = Field(default_factory=list)
    version_modelo_ml: Optional[str] = None
    llm_usado: bool = False
    llm_modelo: Optional[str] = None
    tokens_entrada: int = 0
    tokens_salida: int = 0
    desde_cache: bool = False
