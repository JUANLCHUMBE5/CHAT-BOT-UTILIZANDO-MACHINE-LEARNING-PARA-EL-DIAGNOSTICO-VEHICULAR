"""Formateo de procedimientos técnicos paso a paso bajo demanda (Fase 9.3)."""

from __future__ import annotations

import re
from typing import Any, Optional

from src.core.conversacion.formato_salidas.acciones_prioritarias import (
    simplificar_nombre_falla,
)
from src.core.taxonomy.catalogo_pruebas_taller import (
    obtener_directriz_taller,
)


def formatear_detalle_tecnico(
    falla: str,
    procedimiento_rag: str = "",
    titulo_manual: str = "",
    tolerancias_clave: str = "",
    estado: Optional[Any] = None,
) -> str:
    """Formatea la explicación técnica paso a paso bajo demanda ('más detalles')."""
    from src.core.conversacion.models import FactState

    falla_nom = simplificar_nombre_falla(falla)
    lineas = [f"📋 *Procedimiento de comprobación: {falla_nom}*\n"]

    if isinstance(procedimiento_rag, tuple):
        procedimiento_rag = procedimiento_rag[0] or ""
    procedimiento_rag = str(procedimiento_rag or "").strip()
    procedimiento_rag = re.sub(
        r"tolerancias\s+y\s+especificaciones\s+metrológicas\s+oem:?",
        "Valores del procedimiento técnico recuperado:",
        procedimiento_rag,
        flags=re.IGNORECASE,
    )
    procedimiento_rag = re.sub(
        r"especificaciones\s+metrológicas\s+oem:?",
        "valores del procedimiento técnico recuperado:",
        procedimiento_rag,
        flags=re.IGNORECASE,
    )

    dtcs_en_texto = list(dict.fromkeys(re.findall(r"\b[PCBU]\d{4}\b", procedimiento_rag, re.IGNORECASE)))

    directriz = obtener_directriz_taller(falla)
    if directriz and directriz.dtc_frecuente and directriz.dtc_frecuente != "N/A":
        for d in directriz.dtc_frecuente.split("/"):
            d_c = d.strip()
            if re.match(r"^[PCBU]\d{4}$", d_c, re.IGNORECASE) and d_c not in dtcs_en_texto:
                dtcs_en_texto.append(d_c)

    tiene_dtc_observado = False
    codigos_observados = []
    if estado:
        for h in getattr(estado, "hechos", {}).values():
            if getattr(h, "categoria", "") == "dtc" and getattr(h, "estado", None) == FactState.CONFIRMADO:
                tiene_dtc_observado = True
                codigos_observados.append(h.valor)

    if tiene_dtc_observado and codigos_observados:
        lineas.append(f"📡 *Código reportado por el escáner:* {', '.join(codigos_observados)}\n")
    elif dtcs_en_texto and not (directriz and directriz.es_mecanica_pura and not dtcs_en_texto):
        codigos_rel = ", ".join(dtcs_en_texto[:3])
        lineas.append(f"📡 *Si realizas un escaneo, algunos códigos relacionados que podrían aparecer son:* {codigos_rel}\n")

    if procedimiento_rag:
        pasos = []
        for p in procedimiento_rag.split("\n"):
            p_s = p.strip()
            if not p_s or p_s.startswith("#") or p_s.startswith("METADATOS:"):
                continue
            if re.match(r"^(código[^\n:]*|codigo[^\n:]*|dtc[^\n:]*|gravedad[^\n:]*|modelos compatibles[^\n:]*|síntomas[^\n:]*|sintomas[^\n:]*):", p_s, re.IGNORECASE):
                continue
            if "instrucciones paso a paso:" in p_s.lower():
                continue
            pasos.append(p_s)

        if pasos:
            lineas.append("\n".join(pasos[:8]))
        else:
            lineas.append(procedimiento_rag[:500])
    elif directriz:
        lineas.append(f"1. {directriz.prueba_sugerida}")
    else:
        lineas.append("1. Inspección metrológica de tolerancias según manual de servicio del fabricante.")

    if tolerancias_clave:
        lineas.append(f"\n🔬 *Tolerancias y valores nominales:* {tolerancias_clave}")

    lineas.append("\n¿Deseas registrar el resultado de alguna de estas pruebas?")
    return "\n".join(lineas)
