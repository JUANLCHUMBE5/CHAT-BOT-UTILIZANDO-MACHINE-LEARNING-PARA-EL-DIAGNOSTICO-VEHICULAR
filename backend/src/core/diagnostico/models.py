"""Modelos de datos y DTOs para el flujo de diagnóstico vehicular."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class PrediccionML(BaseModel):
    falla: str
    probabilidad: float


class ResultadoDiagnostico(BaseModel):
    """DTO inmutable de respuesta de diagnóstico por solicitud (evita condiciones de carrera)."""
    respuesta_texto: str
    diagnostico_ml: str
    confianza_ml: float
    contexto_manual: str
    titulo_manual: str
    similitud_rag: float = 0.0
    requiere_revision_humana: bool = False
    estado_sesion: str = "completado"
    modo_diagnostico: str = "completo_ml_rag_llm"
    llm_usado: bool = False
    llm_modelo: Optional[str] = None
    tokens_entrada: int = 0
    tokens_salida: int = 0
    posicion_cola: int = 0
    tiempo_espera_cola: float = 0.0
    solicitud_id: Optional[str] = None
    sintoma_evaluado: str = ""
    predicciones_ml: List[PrediccionML] = Field(default_factory=list)
    predicciones_ml_raw: List[PrediccionML] = Field(default_factory=list)
    motivo_prioridad: str = ""
    respuesta_limitada: bool = False
    tiempo_ml_ms: int = 0
    tiempo_rag_ms: int = 0
    tiempo_llm_ms: int = 0
    tiempo_total_ms: int = 0
    desde_cache: bool = False
    tipo_consulta: str = "diagnostico"
