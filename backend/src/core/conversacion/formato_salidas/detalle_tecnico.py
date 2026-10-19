"""Formateo de procedimientos técnicos paso a paso bajo demanda (Fase 9.3)."""

from __future__ import annotations

import re
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
    codigos = []
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
    # Los códigos orientativos son hipótesis del catálogo/RAG, nunca DTC observados.
    if estado is None or not codigos:
        dtcs_encontrados: list[str] = []
        if isinstance(procedimiento_rag, tuple):
            rag_txt = str(procedimiento_rag[0] or "")
        else:
            rag_txt = str(procedimiento_rag or "")
        if rag_txt:
            dtcs_encontrados.extend(re.findall(r"\b[PCBU]\d{4}\b", rag_txt, re.IGNORECASE))

        from src.core.taxonomy.catalogo_pruebas_taller import obtener_directriz_taller

        directriz = obtener_directriz_taller(falla)
        if directriz and not directriz.es_mecanica_pura and directriz.dtc_frecuente != "N/A":
            dtcs_encontrados.append(str(directriz.dtc_frecuente))

        dtcs_unicos = list(dict.fromkeys([d.upper() for d in dtcs_encontrados if d]))
        if dtcs_unicos:
            lineas.append(
                "Si realizas un escaneo, algunos códigos relacionados que podrían aparecer son: "
                + ", ".join(dtcs_unicos[:3])
                + ". Son posibilidades del catálogo; no se registran como códigos observados."
            )
    lineas.append("¿Deseas registrar el resultado de una comprobación disponible y segura?")
    return "\n".join(lineas)
