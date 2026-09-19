"""
Constructor de consultas enriquecidas multiseñal para el motor RAG.
Combina:
1. Síntomas textuales limpios del usuario y jerga técnica normalizada.
2. Códigos DTC detectados y sus definiciones técnicas estándar.
3. Hipótesis Top 1, Top 2 y Top 3 predichas por el clasificador ML jerárquico.
4. Perfil del vehículo (marca, modelo, sistema).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def construir_consulta_hibrida(
    consulta_usuario: str,
    macro_sistema: Optional[str] = None,
    top_fallas: Optional[List[Dict[str, Any]]] = None,
    codigos_dtc: Optional[List[str]] = None,
    marca: Optional[str] = None,
    modelo: Optional[str] = None,
) -> str:
    """Construye un string de búsqueda denso combinando todas las fuentes de evidencia técnica."""
    partes: List[str] = []

    # 1. Consulta base limpia
    base = str(consulta_usuario or "").strip()
    if base:
        partes.append(base)

    # 2. Códigos DTC detectados explícitamente
    if codigos_dtc:
        dtc_str = " ".join(codigos_dtc).upper()
        partes.append(f"DTC {dtc_str}")

    # 3. Macro-sistema inferido por Level 1 ML
    if macro_sistema and macro_sistema != "DESCONOCIDO":
        partes.append(f"SISTEMA {macro_sistema}")

    # 4. Top 3 candidatos del clasificador ML Level 2
    if top_fallas:
        nombres_fallas = []
        for item in top_fallas[:3]:
            f_nom = item.get("falla") if isinstance(item, dict) else getattr(item, "falla", str(item))
            if f_nom and f_nom not in nombres_fallas:
                nombres_fallas.append(f_nom)
        if nombres_fallas:
            partes.append(" ".join(nombres_fallas))

    # 5. Datos vehiculares si no están ya en la consulta
    if marca and marca.lower() not in base.lower() and marca not in ("Generico", "Vehiculo Generico"):
        partes.append(marca)
    if modelo and modelo.lower() not in base.lower():
        partes.append(modelo)

    return " ".join(partes)
