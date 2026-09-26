"""Convierte una revisión mecánica NHTSA en un dataset experimental trazable.

No entrena ni modifica el modelo oficial. Solo admite registros con revisión
mecánica explícita y etiquetas que pertenecen a la taxonomía limpia de CarBot.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = ROOT / "outputs" / "revision_mecanica_nhtsa_90_casos.xlsx"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
CANONICAL_DATASET = ROOT / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"
SHEET_NAMES = ("Revision mecanica", "Revision prioritaria")
XML_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
}
RE_CELL = re.compile(r"([A-Z]+)(\d+)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def column_index(reference: str) -> int:
    match = RE_CELL.fullmatch(reference)
    if not match:
        raise ValueError(f"Referencia de celda inválida: {reference}")
    letters = match.group(1)
    result = 0
    for letter in letters:
        result = result * 26 + ord(letter) - ord("A") + 1
    return result - 1


def cell_text(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.get("t")
    if cell_type == "s":
        value = cell.findtext("main:v", default="", namespaces=XML_NS)
        return shared_strings[int(value)] if value else ""
    if cell_type == "inlineStr":
        return "".join(cell.itertext())
    return cell.findtext("main:v", default="", namespaces=XML_NS)


def find_review_sheet(archive: zipfile.ZipFile) -> str:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        item.get("Id"): item.get("Target", "")
        for item in rels.findall("pkg:Relationship", XML_NS)
    }
    for sheet in workbook.findall("main:sheets/main:sheet", XML_NS):
        if sheet.get("name") in SHEET_NAMES:
            rel_id = sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            target = targets.get(rel_id, "")
            if target:
                normalized = target.lstrip("/")
                return normalized if normalized.startswith("xl/") else "xl/" + normalized
    raise ValueError(f"No se encontró una hoja de revisión válida: {SHEET_NAMES}")


def read_xlsx_rows(path: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared_strings = ["".join(item.itertext()) for item in root.findall("main:si", XML_NS)]
        sheet = ET.fromstring(archive.read(find_review_sheet(archive)))

    rows: dict[int, dict[int, str]] = {}
    for row in sheet.findall("main:sheetData/main:row", XML_NS):
        row_index = int(row.get("r", "0"))
        values: dict[int, str] = {}
        for cell in row.findall("main:c", XML_NS):
            reference = cell.get("r", "")
            values[column_index(reference)] = cell_text(cell, shared_strings).strip()
        rows[row_index] = values

    headers = rows.get(10, {})
    header_map = {value: column for column, value in headers.items() if value}
    required = {
        "ID", "Texto del caso", "Marca", "Modelo", "Año", "Componente reportado",
        "Etiqueta candidata (no confirmada)", "Etiqueta final validada", "Revisor",
        "Estado de revisión", "Confianza", "Observaciones",
    }
    missing = required - set(header_map)
    if missing:
        raise ValueError(f"Encabezados requeridos ausentes: {sorted(missing)}")

    result: list[dict[str, str]] = []
    for row_index in sorted(index for index in rows if index >= 11):
        row = rows[row_index]
        record = {name: row.get(column, "") for name, column in header_map.items()}
        if record.get("ID", "").strip():
            result.append(record)
    return result


def canonical_labels() -> set[str]:
    with CANONICAL_DATASET.open(encoding="utf-8-sig", newline="") as source:
        return {row["falla"].strip() for row in csv.DictReader(source) if row.get("falla", "").strip()}


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def prepare(records: list[dict[str, str]], labels: set[str]) -> tuple[list[dict[str, str]], dict[str, object]]:
    accepted: list[dict[str, str]] = []
    discards = Counter()
    seen: set[tuple[str, str]] = set()
    statuses = Counter()
    for record in records:
        status = record["Estado de revisión"].strip()
        statuses[status or "blank"] += 1
        if status != "reviewed_by_mechanic":
            discards["not_mechanically_reviewed"] += 1
            continue
        label = record["Etiqueta final validada"].strip()
        reviewer = record["Revisor"].strip()
        confidence = record["Confianza"].strip().lower()
        if not label or not reviewer:
            discards["missing_label_or_reviewer"] += 1
            continue
        if label not in labels:
            discards["label_not_in_canonical_taxonomy"] += 1
            continue
        if confidence not in {"high", "medium"}:
            discards["low_or_invalid_confidence"] += 1
            continue
        text = record["Texto del caso"].strip()
        fingerprint = (normalize(text), label)
        if fingerprint in seen:
            discards["duplicate_text_and_label"] += 1
            continue
        seen.add(fingerprint)
        accepted.append({
            "sintoma": text,
            "falla": label,
            "origen": "NHTSA_ODI_REVIEWED_BY_MECHANIC",
            "review_id": record["ID"].strip(),
            "reviewer": reviewer,
            "confidence": confidence,
            "candidate_label": record["Etiqueta candidata (no confirmada)"].strip(),
            "component_reported": record["Componente reportado"].strip(),
            "make": record["Marca"].strip(),
            "model": record["Modelo"].strip(),
            "model_year": record["Año"].strip(),
            "observations": record["Observaciones"].strip(),
        })
    report = {
        "records_read": len(records),
        "records_accepted": len(accepted),
        "status_distribution": dict(sorted(statuses.items())),
        "discard_reasons": dict(sorted(discards.items())),
        "policy": (
            "Solo reviewed_by_mechanic con etiqueta canónica, revisor y confianza high/medium "
            "pueden formar parte del experimento. No equivale a datos oficiales de tesis."
        ),
    }
    return accepted, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Excel devuelto por el revisor.")
    args = parser.parse_args()
    input_path = args.input.resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"No existe el Excel de revisión: {input_path}")

    records = read_xlsx_rows(input_path)
    accepted, report = prepare(records, canonical_labels())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report.update({
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(input_path),
        "input_sha256": sha256(input_path),
    })
    report_path = OUTPUT_DIR / "reporte_importacion_revision.json"
    dataset_path = OUTPUT_DIR / "dataset_nhtsa_revisado.csv"
    if accepted:
        with dataset_path.open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=list(accepted[0]))
            writer.writeheader()
            writer.writerows(accepted)
        report["dataset_output"] = str(dataset_path)
        report["dataset_sha256"] = sha256(dataset_path)
    else:
        # No se conserva un dataset previo si el Excel actual ya no cumple la regla.
        # Evita entrenar accidentalmente con una salida obsoleta.
        dataset_path.unlink(missing_ok=True)
        report["state"] = "blocked_pending_mechanical_review"
        report["dataset_output"] = None
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
