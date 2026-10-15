"""Genera un dataset candidato y auditable a partir de dos guias de GemaCar.

El resultado modela relaciones multicausa para revision mecanica y uso futuro en
RAG. No modifica el dataset de entrenamiento ni convierte una causa posible en
un diagnostico confirmado.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = DATA_DIR / "candidatos_revision"

try:
    from training.datasets.gemacar_grupos import FUENTES, GRUPOS
except ImportError:
    from machine_learning.training.datasets.gemacar_grupos import FUENTES, GRUPOS



def sha256_archivo(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(65536), b""):
            digest.update(bloque)
    return digest.hexdigest()


def cargar_taxonomia(ruta: Path) -> dict[str, tuple[str, str]]:
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        filas = csv.DictReader(archivo)
        taxonomia: dict[str, tuple[str, str]] = {}
        for fila in filas:
            codigo = fila["codigo_falla"].strip()
            taxonomia[codigo] = (fila["falla"].strip(), fila["sistema"].strip())
    if not taxonomia:
        raise ValueError("La taxonomia canonica esta vacia.")
    return taxonomia


def verificar_fuente(ruta: Path | None, fuente: str) -> tuple[str, bool]:
    esperado = FUENTES[fuente]["sha256"]
    if ruta is None:
        return esperado, False
    obtenido = sha256_archivo(ruta)
    if obtenido != esperado:
        raise ValueError(f"SHA-256 inesperado para {fuente}: {obtenido}")
    return obtenido, True


def preparar(
    salida: Path,
    reporte: Path,
    taxonomia_path: Path,
    fuente_general: Path | None = None,
    fuente_potencia: Path | None = None,
) -> dict[str, object]:
    taxonomia = cargar_taxonomia(taxonomia_path)
    hashes = {
        "fallas_comunes": verificar_fuente(fuente_general, "fallas_comunes"),
        "perdida_potencia": verificar_fuente(fuente_potencia, "perdida_potencia"),
    }
    filas: list[dict[str, str]] = []
    vistos: set[tuple[str, str, str, str]] = set()
    conteo = Counter()

    for grupo in GRUPOS:
        fuente = FUENTES[grupo.fuente]
        for causa_nombre, codigo, estado in grupo.causas:
            clave = (grupo.fuente, grupo.sintoma, grupo.condicion, causa_nombre)
            if clave in vistos:
                raise ValueError(f"Relacion duplicada: {clave}")
            vistos.add(clave)
            if codigo and codigo not in taxonomia:
                raise ValueError(f"Codigo canonico desconocido: {codigo}")
            falla_canonica, sistema_canonico = taxonomia.get(codigo, ("", ""))
            conteo[estado] += 1
            filas.append(
                {
                    "id_candidato": f"GEM-{len(filas) + 1:04d}",
                    "sintoma": grupo.sintoma,
                    "condicion": grupo.condicion,
                    "causa_candidata": causa_nombre,
                    "revision_inicial": grupo.revision,
                    "pregunta_aclaracion": grupo.pregunta,
                    "urgencia_fuente": grupo.urgencia,
                    "sistema_fuente": grupo.sistema,
                    "codigo_canonico_propuesto": codigo,
                    "falla_canonica_propuesta": falla_canonica,
                    "sistema_canonico": sistema_canonico,
                    "estado_mapeo": estado,
                    "decision_revision": "PENDIENTE_MECANICO",
                    "validado_por_mecanico": "NO",
                    "apto_entrenamiento": "NO",
                    "uso_recomendado_actual": "CANDIDATO_RAG_Y_REVISION",
                    "fuente": fuente["titulo"],
                    "url_fuente": fuente["url"],
                    "seccion_fuente": grupo.seccion,
                    "fecha_consulta": "2026-09-02",
                    "licencia_fuente": "NO_DECLARADA",
                    "sha256_texto_fuente": hashes[grupo.fuente][0],
                    "observaciones_revision": "",
                }
            )

    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)

    resumen: dict[str, object] = {
        "tipo_dataset": "CONOCIMIENTO_MULTICAUSA_CANDIDATO",
        "generado_el": "2026-09-02",
        "registros": len(filas),
        "sintomas_unicos": len({fila["sintoma"] for fila in filas}),
        "causas_unicas": len({fila["causa_candidata"] for fila in filas}),
        "conteo_estado_mapeo": dict(sorted(conteo.items())),
        "fuentes": {
            clave: {
                "url": FUENTES[clave]["url"],
                "sha256": valor[0],
                "archivo_verificado": valor[1],
                "licencia": "NO_DECLARADA",
            }
            for clave, valor in hashes.items()
        },
        "duplicados_exactos": 0,
        "incorporado_al_entrenamiento": False,
        "motivo": (
            "La fuente es secundaria, no declara licencia reutilizable y las relaciones son "
            "multicausa. Requiere permiso y validacion por mecanico."
        ),
    }
    reporte.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    return resumen


def generar_derivados(
    candidatos_path: Path,
    entrenamiento_path: Path,
    rag_path: Path,
) -> dict[str, int]:
    """Crea derivados seguros: casos univocos para ML y conocimiento multicausa para RAG."""
    with candidatos_path.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))

    grupos: dict[tuple[str, str, str, str], list[dict[str, str]]] = {}
    for fila in filas:
        clave = (
            fila["fuente"],
            fila["seccion_fuente"],
            fila["sintoma"],
            fila["condicion"],
        )
        grupos.setdefault(clave, []).append(fila)

    entrenamiento: list[dict[str, str]] = []
    secciones_rag: list[str] = []
    for (fuente, seccion, sintoma, condicion), relaciones in grupos.items():
        estados = {fila["estado_mapeo"] for fila in relaciones}
        codigos = {
            fila["codigo_canonico_propuesto"]
            for fila in relaciones
            if fila["codigo_canonico_propuesto"]
        }
        if estados == {"MAPEO_PROPUESTO"} and len(codigos) == 1:
            representativa = relaciones[0]
            entrenamiento.append(
                {
                    "sintoma": f"{sintoma}; {condicion}",
                    "falla": representativa["falla_canonica_propuesta"],
                    "codigo_falla": representativa["codigo_canonico_propuesto"],
                    "sistema": representativa["sistema_canonico"],
                    "severidad": representativa["urgencia_fuente"].lower(),
                    "origen": "GEMACAR_WEB_EXPERIMENTAL",
                    "url_fuente": representativa["url_fuente"],
                    "licencia": representativa["licencia_fuente"],
                    "estado_validacion": "FUENTE_SECUNDARIA_NO_VALIDADA_POR_MECANICO",
                }
            )

        posibles = [
            fila["causa_candidata"]
            for fila in relaciones
            if fila["estado_mapeo"] not in {"DESCARTAR_NO_FALLA", "REQUIERE_DESCARTE"}
        ]
        descartes = [
            fila["causa_candidata"]
            for fila in relaciones
            if fila["estado_mapeo"] == "REQUIERE_DESCARTE"
        ]
        normales = [
            fila["causa_candidata"]
            for fila in relaciones
            if fila["estado_mapeo"] == "DESCARTAR_NO_FALLA"
        ]
        representativa = relaciones[0]
        cuerpo = [
            f"=== ORIENTACION SECUNDARIA NO VALIDADA: {seccion.upper()} ===",
            "Estado: fuente web secundaria; pendiente de validacion mecanica.",
            f"Sintoma: {sintoma}.",
            f"Condicion: {condicion}.",
        ]
        if posibles:
            cuerpo.append(f"Causas posibles a diferenciar: {'; '.join(posibles)}.")
        if descartes:
            cuerpo.append(f"Factores no concluyentes que deben descartarse: {'; '.join(descartes)}.")
        if normales:
            cuerpo.append(f"Condiciones que pueden ser normales: {'; '.join(normales)}.")
        cuerpo.extend(
            [
                f"Revision inicial: {representativa['revision_inicial']}",
                f"Pregunta de aclaracion: {representativa['pregunta_aclaracion']}",
                f"Urgencia orientativa: {representativa['urgencia_fuente']}.",
                (
                    "Regla de seguridad: no confirmar una pieza ni ordenar un reemplazo sin "
                    "pruebas fisicas, codigos y mediciones del fabricante."
                ),
                f"Fuente secundaria: {fuente}.",
                f"URL: {representativa['url_fuente']}",
            ]
        )
        secciones_rag.append("\n".join(cuerpo))

    entrenamiento_path.parent.mkdir(parents=True, exist_ok=True)
    with entrenamiento_path.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(entrenamiento[0]))
        escritor.writeheader()
        escritor.writerows(entrenamiento)

    rag_path.parent.mkdir(parents=True, exist_ok=True)
    rag_path.write_text("\n\n".join(secciones_rag) + "\n", encoding="utf-8")
    return {
        "registros_ml_experimentales": len(entrenamiento),
        "secciones_rag_secundarias": len(secciones_rag),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fuente-general", type=Path)
    parser.add_argument("--fuente-potencia", type=Path)
    parser.add_argument(
        "--salida",
        type=Path,
        default=OUTPUT_DIR / "gemacar_sintomas_causas_candidatas.csv",
    )
    parser.add_argument(
        "--reporte",
        type=Path,
        default=OUTPUT_DIR / "gemacar_sintomas_causas_reporte.json",
    )
    parser.add_argument(
        "--taxonomia",
        type=Path,
        default=DATA_DIR / "dataset_sintomas_limpio.csv",
    )
    parser.add_argument(
        "--salida-entrenamiento",
        type=Path,
        default=DATA_DIR / "dataset_gemacar_experimental.csv",
    )
    parser.add_argument(
        "--salida-rag",
        type=Path,
        default=ROOT / "manuals/generales/orientacion_secundaria_gemacar.txt",
    )
    args = parser.parse_args()
    resumen = preparar(
        salida=args.salida,
        reporte=args.reporte,
        taxonomia_path=args.taxonomia,
        fuente_general=args.fuente_general,
        fuente_potencia=args.fuente_potencia,
    )
    resumen.update(generar_derivados(args.salida, args.salida_entrenamiento, args.salida_rag))
    args.reporte.write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
