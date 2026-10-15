"""Modelo de hechos diagnósticos estructurados y trazabilidad clínica."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.core.conversacion.state_models.enums import FactState, FactType


@dataclass
class DiagnosticFact:
    """Hecho diagnóstico estructurado con trazabilidad y estado clínico."""
    campo: str
    valor: str
    estado: FactState = FactState.CONFIRMADO
    turno_origen: int = 1
    confianza: float = 1.0
    texto_crudo: Optional[str] = None
    categoria: str = "sintoma"
    tipo: FactType = FactType.SINTOMA
    procedencia: str = "inferred"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "campo": self.campo,
            "valor": self.valor,
            "estado": self.estado.value,
            "turno_origen": self.turno_origen,
            "confianza": round(self.confianza, 2),
            "texto_crudo": self.texto_crudo,
            "categoria": self.categoria,
            "tipo": self.tipo.value,
            "procedencia": self.procedencia,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> DiagnosticFact:
        raw_tipo = d.get("tipo", "SINTOMA")
        if isinstance(raw_tipo, FactType):
            tipo_val = raw_tipo
        else:
            try:
                tipo_val = FactType(str(raw_tipo))
            except (ValueError, TypeError):
                tipo_val = FactType.SINTOMA
        raw_estado = d.get("estado", "CONFIRMADO")
        if isinstance(raw_estado, FactState):
            estado_val = raw_estado
        else:
            try:
                estado_val = FactState(str(raw_estado))
            except (ValueError, TypeError):
                estado_val = FactState.CONFIRMADO
        return cls(
            campo=d["campo"],
            valor=d["valor"],
            estado=estado_val,
            turno_origen=d.get("turno_origen", 1),
            confianza=float(d.get("confianza", 1.0)),
            texto_crudo=d.get("texto_crudo"),
            categoria=d.get("categoria", "sintoma"),
            tipo=tipo_val,
            procedencia=d.get("procedencia", "inferred"),
        )
