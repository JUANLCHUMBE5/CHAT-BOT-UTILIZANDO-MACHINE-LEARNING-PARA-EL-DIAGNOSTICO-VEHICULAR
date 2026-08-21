"""Construye un conjunto externo conservador desde Zenodo sin tocar el holdout.

La unidad de entrenamiento es el caso completo (todos sus síntomas juntos), no
cada síntoma aislado. Solo admite equivalencias taxonómicas ya auditadas y
excluye casos marcados como ambiguos.
"""

from __future__ import annotations

import csv
import hashlib
import json
import urllib.request
from pathlib import Path

import pandas as pd
from preparar_candidatos_zenodo import (
    COMBINACIONES_AMBIGUAS,
    DOI,
    LICENCIA,
    MAPEO_SEGURO,
    MD5_ESPERADO,
)
from traducir_candidatos_es_peru import TRADUCCIONES_ES_PERU

URL_FUENTE = (
    "https://zenodo.org/records/15626055/files/"
    "automotive_faults_aktc_obike_et_al.json?download=1"
)
RAIZ_ML = Path(__file__).resolve().parents[1]
RUTA_FUENTE = RAIZ_ML / "data" / "fuentes_abiertas" / "zenodo_15626055.json"
RUTA_BASE = RAIZ_ML / "data" / "dataset_sintomas_limpio.csv"
RUTA_SALIDA = RAIZ_ML / "data" / "dataset_externo_auditado.csv"
RUTA_REPORTE = RAIZ_ML / "data" / "reporte_dataset_externo.json"


def _md5(ruta: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(65536), b""):
            digest.update(bloque)
    return digest.hexdigest()


def _obtener_fuente() -> None:
    RUTA_FUENTE.parent.mkdir(parents=True, exist_ok=True)
    if not RUTA_FUENTE.exists() or _md5(RUTA_FUENTE) != MD5_ESPERADO:
        urllib.request.urlretrieve(URL_FUENTE, RUTA_FUENTE)
    checksum = _md5(RUTA_FUENTE)
    if checksum != MD5_ESPERADO:
        raise ValueError(
            f"Checksum Zenodo inválido: esperado={MD5_ESPERADO}, recibido={checksum}"
        )


def construir() -> dict[str, object]:
    _obtener_fuente()
    registros = json.loads(RUTA_FUENTE.read_text(encoding="utf-8"))
    if not isinstance(registros, list) or len(registros) != 99:
        raise ValueError("La fuente Zenodo no contiene los 99 casos esperados.")

    base = pd.read_csv(RUTA_BASE, encoding="utf-8")
    catalogo = (
        base[["codigo_falla", "falla", "sistema", "severidad"]]
        .drop_duplicates()
        .groupby("codigo_falla", as_index=False)
        .filter(lambda grupo: len(grupo) == 1)
        .set_index("codigo_falla")
    )

    filas: list[dict[str, str]] = []
    descartes = {
        "sin_mapeo_taxonomico": 0,
        "ambiguo": 0,
        "traduccion_incompleta": 0,
        "codigo_inconsistente": 0,
        "duplicado": 0,
    }
    vistos: set[tuple[str, str]] = set()

    for registro in registros:
        categoria = str(registro.get("category", "")).strip()
        subcategoria = str(registro.get("subcategory", "")).strip()
        sintomas_ingles = [str(s).strip() for s in registro.get("symptoms", []) if str(s).strip()]
        codigo = MAPEO_SEGURO.get((categoria, subcategoria), "")
        if not codigo:
            descartes["sin_mapeo_taxonomico"] += 1
            continue
        if any(
            (categoria, subcategoria, sintoma) in COMBINACIONES_AMBIGUAS
            for sintoma in sintomas_ingles
        ):
            descartes["ambiguo"] += 1
            continue
        traducciones = [TRADUCCIONES_ES_PERU.get(sintoma, "") for sintoma in sintomas_ingles]
        if not traducciones or any(not traduccion for traduccion in traducciones):
            descartes["traduccion_incompleta"] += 1
            continue
        if codigo not in catalogo.index:
            descartes["codigo_inconsistente"] += 1
            continue

        sintoma_compuesto = "; además, ".join(traducciones)
        clave = (sintoma_compuesto.casefold(), codigo)
        if clave in vistos:
            descartes["duplicado"] += 1
            continue
        vistos.add(clave)
        datos_clase = catalogo.loc[codigo]
        filas.append(
            {
                "sintoma": sintoma_compuesto,
                "falla": str(datos_clase["falla"]),
                "codigo_falla": codigo,
                "sistema": str(datos_clase["sistema"]),
                "severidad": str(datos_clase["severidad"]),
                "origen": "ZENODO_ACADEMICO",
                "doi": DOI,
                "licencia": LICENCIA,
                "estado_validacion": "AUDITADO_TAXONOMIA_NO_CASO_TALLER",
            }
        )

    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    campos = list(filas[0]) if filas else [
        "sintoma", "falla", "codigo_falla", "sistema", "severidad",
        "origen", "doi", "licencia", "estado_validacion",
    ]
    with RUTA_SALIDA.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(filas)

    reporte: dict[str, object] = {
        "fuente": f"https://doi.org/{DOI}",
        "licencia": LICENCIA,
        "checksum_md5": MD5_ESPERADO,
        "casos_fuente": len(registros),
        "casos_externos_admitidos": len(filas),
        "descartes": descartes,
        "regla_evaluacion": "Los casos externos solo pueden entrar al entrenamiento; nunca al holdout.",
    }
    RUTA_REPORTE.write_text(
        json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return reporte


if __name__ == "__main__":
    print(json.dumps(construir(), ensure_ascii=False, indent=2))
