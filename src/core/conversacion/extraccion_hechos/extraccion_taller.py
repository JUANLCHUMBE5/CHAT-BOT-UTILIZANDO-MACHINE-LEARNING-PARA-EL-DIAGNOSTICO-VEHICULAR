"""Orquestador de comprobaciones de taller y mediciones instrumentales (Clean Architecture).

Delega la extracción a submódulos especializados por responsabilidad única (SRP):
- `mediciones_instrumentales`: magnitudes físicas, sensores y compensadores.
- `comprobaciones_mecanicas`: pruebas físicas, descarte de componentes y antecedentes.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.core.conversacion.extraccion_hechos.comprobaciones_mecanicas import (
    extraer_comprobaciones_mecanicas,
)
from src.core.conversacion.extraccion_hechos.mediciones_instrumentales import (
    extraer_mediciones_instrumentales,
)
from src.core.conversacion.models import ConversationState


def extraer_comprobaciones_taller(
    estado: ConversationState,
    texto_usuario: str,
    texto_normalizado: str,
) -> List[Dict[str, Any]]:
    """Extrae tanto mediciones instrumentales como comprobaciones mecánicas y descartes."""
    hechos_totales: List[Dict[str, Any]] = []

    # 1. Mediciones instrumentales y cuantitativas
    hechos_med = extraer_mediciones_instrumentales(estado, texto_usuario, texto_normalizado)
    hechos_totales.extend(hechos_med)

    # 2. Comprobaciones mecánicas, pruebas físicas y piezas descartadas
    hechos_mec = extraer_comprobaciones_mecanicas(estado, texto_usuario, texto_normalizado)
    hechos_totales.extend(hechos_mec)

    return hechos_totales


__all__ = [
    "extraer_comprobaciones_mecanicas",
    "extraer_comprobaciones_taller",
    "extraer_mediciones_instrumentales",
]
