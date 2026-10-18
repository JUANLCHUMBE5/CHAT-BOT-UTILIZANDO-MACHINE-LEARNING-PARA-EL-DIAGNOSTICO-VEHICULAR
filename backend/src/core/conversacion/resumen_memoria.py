"""Resumen de solo lectura del estado conversacional para el mecánico."""

from __future__ import annotations

from typing import Any

from src.core.conversacion.models import FactState


def _unicos(valores: list[str]) -> str:
    return ", ".join(dict.fromkeys(valor for valor in valores if valor)) or "ninguno registrado"


def generar_resumen_memoria(estado: Any) -> str:
    """Describe hechos persistidos sin inferir, clasificar ni modificar el estado."""
    partes_veh = [
        str(valor)
        for valor in (
            getattr(estado, "marca", None),
            getattr(estado, "modelo", None),
            getattr(estado, "anio", None),
            getattr(estado, "motor", None),
            getattr(estado, "combustible", None),
        )
        if valor
    ]
    vehiculo_base = " ".join(partes_veh)
    placa = getattr(estado, "placa", None)
    if placa and vehiculo_base:
        vehiculo = f"{vehiculo_base}, placa {placa}"
    elif placa:
        vehiculo = f"placa {placa}"
    elif vehiculo_base:
        vehiculo = vehiculo_base
    else:
        vehiculo = "sin perfil completo"

    hechos = list(getattr(estado, "hechos", {}).values())
    sintomas_extra = [str(s).replace("_", " ") for s in (getattr(estado, "active_symptoms", []) or []) if s]
    if getattr(estado, "sintoma_principal", None):
        sintomas_extra.append(str(estado.sintoma_principal).replace("_", " "))
    for s in getattr(estado, "sintomas_observados", []) or []:
        if s:
            sintomas_extra.append(str(s).replace("_", " "))

    hechos_sintomas = [
        str(hecho.valor).replace("_", " ")
        for hecho in hechos
        if hecho.categoria == "sintoma" and hecho.estado == FactState.CONFIRMADO
    ]
    presentes = _unicos([*hechos_sintomas, *sintomas_extra])

    negados = _unicos(
        [
            str(hecho.valor)
            for hecho in hechos
            if hecho.categoria in {"sintoma", "polaridad", "sistema_normal"}
            and hecho.estado == FactState.AUSENTE_NEGADO
        ]
    )
    dtc = _unicos(
        [
            str(hecho.valor)
            for hecho in hechos
            if hecho.categoria == "dtc" and hecho.estado == FactState.CONFIRMADO
        ]
    )
    mediciones = _unicos(
        [
            str(valor.get("formato") or f"{valor.get('valor')} {valor.get('unidad', '')}".strip())
            for valor in getattr(estado, "measurements", {}).values()
            if isinstance(valor, dict) and valor.get("valor") is not None
        ]
    )
    lim_raw = [
        *[str(valor).replace("_", " ") for valor in getattr(estado, "herramientas_no_disponibles", [])],
        *[str(valor).replace("_", " ") for valor in getattr(estado, "tools_unavailable", [])],
        *[
            str(valor.get("prueba", "")).replace("_", " ")
            for valor in getattr(estado, "pruebas_no_disponibles", [])
            if isinstance(valor, dict)
        ],
        *[str(h.valor) for h in hechos if h.categoria == "limitacion"],
    ]
    lim_unicos = []
    for v in dict.fromkeys(v for v in lim_raw if v):
        if any(v != otro and v in otro for otro in lim_raw):
            continue
        lim_unicos.append(v)
    limitaciones = ", ".join(lim_unicos) or "ninguna registrada"

    duracion_hecho = next(
        (str(h.valor) for h in hechos if h.campo == "duracion_problema" or h.categoria == "duracion"),
        None,
    )

    descartes_list = [
        str(h.replace("componente:", "").replace("_", " ").capitalize())
        for h in getattr(estado, "hipotesis_descartadas", [])
    ]
    for h in hechos:
        if getattr(h, "categoria", "") in (
            "componente_reemplazado",
            "rechazo_hipotesis_usuario",
        ) or "bujia" in getattr(h, "campo", ""):
            nombre = getattr(h, "campo", "").replace("componente_reemplazado_", "").capitalize()
            val = getattr(h, "valor", "")
            item_str = f"{nombre}: {val}"
            if item_str not in descartes_list:
                descartes_list.append(item_str)
    descartes = ", ".join(descartes_list) or "ninguno registrado"

    lineas = [
        "*Memoria técnica registrada*",
        f"Vehículo: {vehiculo}.",
        f"Síntomas confirmados: {presentes}.",
        f"Síntomas negados: {negados}.",
        f"Descartes registrados: {descartes}.",
    ]
    if duracion_hecho:
        lineas.append(f"Duración: {duracion_hecho}.")
    lineas.extend(
        [
            f"DTC: {dtc}.",
            f"Mediciones: {mediciones}.",
            f"Limitaciones registradas: {limitaciones}.",
            "Consulta de solo lectura: no generé hipótesis ni modifiqué el diagnóstico.",
        ]
    )
    return "\n".join(lineas)
