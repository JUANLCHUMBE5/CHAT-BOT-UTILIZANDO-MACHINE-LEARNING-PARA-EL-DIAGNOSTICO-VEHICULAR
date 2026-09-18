"""Admite correcciones reales de taller como candidatos, nunca como entrenamiento automático."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ALIASES = {
    "sintoma": ("sintoma", "Sintoma_Reportado"),
    "falla_real": ("falla_real", "Falla_Confirmada_Fisica"),
    "estado": ("estado_registro", "Estado_Registro"),
    "metodo": ("metodo_confirmacion", "Metodo_Confirmacion"),
    "evidencia": ("evidencia_ref", "Evidencia_Referencia"),
    "validador": ("validado_por_id", "Validador_ID"),
    "fecha_validacion": ("fecha_validacion", "Fecha_Validacion"),
    "origen": ("origen_dato", "Origen_Dato"),
}
ORIGENES_PROHIBIDOS = {"demo", "sintetico", "sintetico_aumentado", "maqueta", "prueba"}
CLASES_PRIORITARIAS_VALIDACION = {
    "Bomba de gasolina quemada o con baja presion",
    "Falla en termostato o motoventilador de radiador",
    "Fuga en mangueras de refrigerante o radiador picado",
    "Cuerpo de aceleracion o valvula IAC sucia",
    "Falla en bombin o bomba hidraulica de embrague",
}


def _valor(fila: dict[str, str], campo: str) -> str:
    return next((str(fila.get(alias) or "").strip() for alias in ALIASES[campo] if fila.get(alias)), "")


def seleccionar_correcciones_confirmadas(
    filas: list[dict[str, str]], fallas_canonicas: set[str]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Separa candidatos admisibles y rechazados con una razón auditable."""
    admitidas: list[dict[str, str]] = []
    rechazadas: list[dict[str, str]] = []
    vistos: set[tuple[str, str]] = set()

    for numero, fila in enumerate(filas, start=1):
        sintoma = _valor(fila, "sintoma")
        falla = _valor(fila, "falla_real")
        origen = _valor(fila, "origen").lower()
        razones = []
        if _valor(fila, "estado").lower() != "verificado":
            razones.append("estado_no_verificado")
        if not _valor(fila, "metodo"):
            razones.append("sin_metodo_confirmacion")
        if not _valor(fila, "evidencia"):
            razones.append("sin_evidencia")
        if not _valor(fila, "validador") or not _valor(fila, "fecha_validacion"):
            razones.append("sin_revision_responsable")
        if origen in ORIGENES_PROHIBIDOS:
            razones.append("origen_demo_o_sintetico")
        if falla not in fallas_canonicas:
            razones.append("falla_fuera_taxonomia")
        if len(sintoma) < 10:
            razones.append("sintoma_insuficiente")

        clave = (sintoma.casefold(), falla.casefold())
        if clave in vistos:
            razones.append("duplicado")
        if razones:
            rechazadas.append({"fila": str(numero), "razones": "|".join(razones)})
            continue

        vistos.add(clave)
        admitidas.append(
            {
                "sintoma": sintoma,
                "falla": falla,
                "origen_dato": "taller_validado_candidato",
                "metodo_confirmacion": _valor(fila, "metodo"),
                "evidencia_ref": _valor(fila, "evidencia"),
                "validado_por_id": _valor(fila, "validador"),
                "fecha_validacion": _valor(fila, "fecha_validacion"),
                "estado_admision": "candidato_revision_ml",
                "prioridad_validacion": "alta" if falla in CLASES_PRIORITARIAS_VALIDACION else "normal",
            }
        )
    return admitidas, rechazadas


def preparar(entrada: Path, taxonomia: Path, salida: Path, reporte: Path) -> dict:
    with entrada.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(line for line in archivo if not line.startswith("#")))
    with taxonomia.open(encoding="utf-8-sig", newline="") as archivo:
        fallas = {fila["falla"].strip() for fila in csv.DictReader(archivo)}

    admitidas, rechazadas = seleccionar_correcciones_confirmadas(filas, fallas)
    salida.parent.mkdir(parents=True, exist_ok=True)
    campos = list(admitidas[0]) if admitidas else [
        "sintoma", "falla", "origen_dato", "metodo_confirmacion", "evidencia_ref",
        "validado_por_id", "fecha_validacion", "estado_admision", "prioridad_validacion",
    ]
    with salida.open("w", encoding="utf-8-sig", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(admitidas)
    resumen = {
        "evaluados": len(filas),
        "candidatos_admitidos": len(admitidas),
        "rechazados": len(rechazadas),
        "promocion_automatica": False,
        "rechazos": rechazadas,
    }
    reporte.write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    return resumen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("entrada", type=Path)
    parser.add_argument("salida", type=Path)
    parser.add_argument("--taxonomia", type=Path, default=Path("data/dataset_sintomas_limpio.csv"))
    parser.add_argument("--reporte", type=Path, default=Path("data/candidatos_revision/reporte_taller.json"))
    args = parser.parse_args()
    print(json.dumps(preparar(args.entrada, args.taxonomia, args.salida, args.reporte), indent=2))


if __name__ == "__main__":
    main()
