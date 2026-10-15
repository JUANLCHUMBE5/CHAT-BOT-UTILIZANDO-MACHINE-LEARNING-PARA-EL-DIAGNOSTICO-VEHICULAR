"""Resumen de solo lectura del estado conversacional para el mecánico."""

from __future__ import annotations

from typing import Any

from src.core.conversacion.models import FactState


def _unicos(valores: list[str]) -> str:
    return ", ".join(dict.fromkeys(valor for valor in valores if valor)) or "ninguno registrado"


def generar_resumen_memoria(estado: Any) -> str:
    """Describe hechos persistidos sin inferir, clasificar ni modificar el estado."""
    vehiculo = " ".join(
        str(valor)
        for valor in (
            getattr(estado, "marca", None),
            getattr(estado, "modelo", None),
            getattr(estado, "anio", None),
            getattr(estado, "motor", None),
            getattr(estado, "combustible", None),
        )
        if valor
    ) or "sin perfil completo"
    hechos = list(getattr(estado, "hechos", {}).values())
    presentes = _unicos([
        str(hecho.valor) for hecho in hechos
        if hecho.categoria == "sintoma" and hecho.estado == FactState.CONFIRMADO
    ])
    negados = _unicos([
        str(hecho.valor) for hecho in hechos
        if hecho.categoria in {"sintoma", "polaridad"}
        and hecho.estado == FactState.AUSENTE_NEGADO
    ])
    dtc = _unicos([
        str(hecho.valor) for hecho in hechos
        if hecho.categoria == "dtc" and hecho.estado == FactState.CONFIRMADO
    ])
    mediciones = _unicos([
        str(valor.get("formato") or f"{valor.get('valor')} {valor.get('unidad', '')}".strip())
        for valor in getattr(estado, "measurements", {}).values()
        if isinstance(valor, dict) and valor.get("valor") is not None
    ])
    limitaciones = _unicos([
        *[str(valor) for valor in getattr(estado, "herramientas_no_disponibles", [])],
        *[str(valor) for valor in getattr(estado, "tools_unavailable", [])],
        *[str(valor.get("prueba")) for valor in getattr(estado, "pruebas_no_disponibles", []) if isinstance(valor, dict)],
    ])
    return (
        "*Memoria técnica registrada*\n"
        f"Vehículo: {vehiculo}.\n"
        f"Síntomas confirmados: {presentes}.\n"
        f"Síntomas negados: {negados}.\n"
        f"DTC: {dtc}.\n"
        f"Mediciones: {mediciones}.\n"
        f"Limitaciones registradas: {limitaciones}.\n"
        "Consulta de solo lectura: no generé hipótesis ni modifiqué el diagnóstico."
    )
