"""Contratos de métricas operativas y ejecutivas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ResumenMetricasResponseDTO(BaseModel):
    diagnosticos_hoy: int
    diagnosticos_semana: int
    diagnosticos_mes: int
    diagnosticos_realizados: int = 0
    diagnosticos_pendientes: int = 0
    porcentaje_confirmados: int
    tiempo_promedio_ms: int
    tiempo_inferencia_ml_ms: Optional[int] = None
    distribucion_modos: List[Dict[str, Any]]
    actividad_diaria: List[Dict[str, Any]]
    fallas_frecuentes: List[Dict[str, Any]]


class MetricasColaResponseDTO(BaseModel):
    total: int
    pendientes: int
    procesando: int
    fallidos: int
    espera_promedio_ms: int
    worker_activo: bool
    worker_id: Optional[str] = None
    ultima_actividad: Optional[datetime] = None
    por_cola: List[Dict[str, Any]]
    consultado_en: datetime


class TrabajoFallidoDTO(BaseModel):
    id: uuid.UUID
    tipo: str
    cola: str
    intentos: int
    max_intentos: int
    error: Optional[str]
    creado_en: datetime
    actualizado_en: datetime
