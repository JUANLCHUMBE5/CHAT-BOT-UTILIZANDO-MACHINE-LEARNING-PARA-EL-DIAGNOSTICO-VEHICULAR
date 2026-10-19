# -*- coding: utf-8 -*-
"""Adaptador Canónico RAG-03C / D3 al Contrato Documental Único CarBot.

Reemplaza la implementación duplicada/divergente previa por una delegación directa
en la política documental unificada de src.infrastructure.rag (C02, A02, A03, A07, A09).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Localizar la raíz del proyecto buscando el directorio 'backend'
_curr = Path(__file__).resolve()
BACKEND_DIR = None
for parent in _curr.parents:
    if (parent / "backend" / "src").exists():
        BACKEND_DIR = parent / "backend"
        break

if BACKEND_DIR and str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.infrastructure.rag.controlador_especificaciones_oem import (
    COMPONENTES_SISTEMAS,
    PATRONES_SOLICITUD_EXACTA,
    clasificar_y_filtrar_oem,
    detectar_tipo_consulta,
    es_consulta_alta_tension,
    es_documento_bajo_voltaje,
    extraer_componente_principal,
    extraer_componentes_documento,
    normalizar,
)
from src.infrastructure.rag.contrato_documental import (
    EstadoDocumental,
    VehiculoConsulta,
    dictaminar_candidato_documental,
    proteger_salida_conversacional,
    verificar_compatibilidad_estructurada,
    verificar_presencia_cifra_y_trazabilidad,
)


def clasificar_y_filtrar_candidato_rag03c2(
    consulta: str,
    candidato: Dict[str, Any],
    vehiculo_consulta: str = "",
    sistema_consulta: str = "",
) -> Tuple[str, float, str]:
    """Adaptador de compatibilidad para scripts experimentales RAG-03C.2.

    Delega estrictamente en la política única del backend.
    """
    return clasificar_y_filtrar_oem(
        consulta=consulta,
        candidato=candidato,
        vehiculo_consulta=vehiculo_consulta,
        sistema_consulta=sistema_consulta,
    )
