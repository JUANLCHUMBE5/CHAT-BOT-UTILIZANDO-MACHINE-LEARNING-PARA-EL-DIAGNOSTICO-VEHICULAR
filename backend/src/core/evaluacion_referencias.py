"""Reglas de evaluabilidad; una coincidencia textual nunca acredita falla física."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def auditar_referencias(
    filas: Iterable[Mapping[str, Any]], clases_canonicas: Iterable[str],
) -> dict[str, Any]:
    filas = list(filas)
    clases = set(clases_canonicas)
    problemas = []
    for posicion, fila in enumerate(filas, 1):
        motivos = []
        if fila.get("falla") not in clases:
            motivos.append("etiqueta_no_canonica_requiere_mapeo_independiente")
        if fila.get("tipo_registro") not in {"THESIS_PRETEST", "THESIS_POSTTEST"}:
            motivos.append("no_es_muestra_oficial")
        for campo in ("case_id", "metodo_confirmacion", "evidencia_ref", "validado_por_id", "fecha_validacion"):
            if not str(fila.get(campo) or "").strip():
                motivos.append("falta_" + campo)
        if fila.get("estado_registro") != "verificado":
            motivos.append("revision_humana_pendiente")
        if motivos:
            problemas.append({"fila": posicion, "motivos": motivos})
    return {
        "denominador_original": len(filas), "filas_con_limitaciones": len(problemas),
        "limitaciones": problemas, "precision_clinica": None,
        "nota": "Este control valida datos declarados; no certifica una inspección física ni calcula exactitud.",
    }


def etiqueta_exacta(prediccion: str, referencia: str) -> bool:
    """La equivalencia exige IDs canónicos iguales, nunca substring o similitud léxica."""
    return prediccion == referencia
