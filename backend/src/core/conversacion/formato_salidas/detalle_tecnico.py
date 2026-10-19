"""Formateo de procedimientos técnicos paso a paso bajo demanda (Fase 9.3)."""

from __future__ import annotations

from typing import Any, Optional

from src.core.conversacion.formato_salidas.acciones_prioritarias import (
    simplificar_nombre_falla,
)


def formatear_detalle_tecnico(
    falla: str,
    procedimiento_rag: str = "",
    titulo_manual: str = "",
    tolerancias_clave: str = "",
    estado: Optional[Any] = None,
) -> str:
    """Formatea la explicación técnica paso a paso bajo demanda ('más detalles')."""
    falla_nom = simplificar_nombre_falla(falla)
    lineas = [f"📋 *Procedimiento de comprobación: {falla_nom}*\n"]
    if estado:
        codigos = list(dict.fromkeys(
            h.valor for h in estado.hechos.values()
            if h.categoria == "dtc" and h.estado.value == "CONFIRMADO"
        ))
        if codigos:
            lineas.append("📡 *Código reportado por el escáner:* " + ", ".join(codigos))
    # El conocimiento recuperado conserva su utilidad como búsqueda, pero una
    # plantilla sin validación no puede convertirse en un procedimiento OEM.
    from src.core.conversacion.formato_salidas.orientacion_segura import orientar_sin_manual

    lineas.append(orientar_sin_manual(falla_nom))
    return "\n".join(lineas)
