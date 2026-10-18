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
    areas_consulta: Optional[List[str]] = None,
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

    # 4. Descriptores neutros de subsistema
    # Evitan inyectar componentes específicos pre-juzgados (como termostato en refrigeración)
    # si el mecánico solo mencionó síntomas generales del sistema.
    terminos_area = {
        "INYECCION_MEZCLA": "inyección combustible mezcla sensor oxígeno fuel trim",
        "ADMISION_MAP": "admisión presión colector múltiple admisión vacio",
        "RALENTI": "ralentí marcha mínima estabilidad motor",
        "REFRIGERACION": "refrigeración circuito enfriamiento temperatura motor sobrecalentamiento",
        "ENCENDIDO": "encendido chispa combustión salto de chispa",
    }
    if areas_consulta:
        partes.extend(terminos_area[area] for area in areas_consulta if area in terminos_area)

    # 5. Top 3 candidatos del clasificador Level 2; al haber señal específica,
    # solo se añaden candidatos del mismo tema (sin alterar sus probabilidades).
    if top_fallas:
        if areas_consulta:
            from src.core.diagnostico.enrutador_sistema import falla_coincide_con_areas

            top_fallas = [
                item
                for item in top_fallas
                if falla_coincide_con_areas(
                    item.get("falla", "") if isinstance(item, dict) else getattr(item, "falla", str(item)),
                    areas_consulta,
                )
            ]
        nombres_fallas = []
        for item in top_fallas[:3]:
            f_nom = item.get("falla") if isinstance(item, dict) else getattr(item, "falla", str(item))
            if f_nom and f_nom not in nombres_fallas:
                nombres_fallas.append(f_nom)
        if nombres_fallas:
            partes.append(" ".join(nombres_fallas))

    # 6. Datos de vehículo si están disponibles
    if marca:
        partes.append(f"MARCA {marca}")
    if modelo:
        partes.append(f"MODELO {modelo}")

    return " ".join(partes)
