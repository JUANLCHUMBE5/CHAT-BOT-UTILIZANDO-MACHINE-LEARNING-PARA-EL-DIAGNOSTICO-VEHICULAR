"""Contratos públicos del laboratorio local."""
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MensajeLabRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: f"lab_{uuid.uuid4().hex[:8]}")
    mensaje: str
    proveedor: str = "laboratorio"


class ComprobacionResult(BaseModel):
    criterio: str
    resultado: str  # APROBADO | FALLIDO | PENDIENTE
    evidencia: str


class MensajeLabResponse(BaseModel):
    session_id: str
    case_id: Optional[str]
    placa: Optional[str]
    vehiculo: Optional[str]
    respuesta_texto: str
    modo_diagnostico: str
    diagnostico_ml: Optional[str]
    confianza_ml: float
    contexto_manual: Optional[str]
    titulo_manual: Optional[str]
    similitud_rag: float
    tiempo_total_ms: float
    sintomas_confirmados: List[str]
    sintomas_negados: List[str]
    limitaciones: List[str]
    fase: str
    top3_actual: List[Dict[str, Any]]
    comprobaciones: List[ComprobacionResult]


