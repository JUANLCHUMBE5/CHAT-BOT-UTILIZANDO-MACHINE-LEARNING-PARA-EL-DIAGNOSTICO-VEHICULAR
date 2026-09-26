"""Crea un lote pequeño de TSB para revisión técnica y de licencia.

Nunca construye FAISS ni modifica el RAG oficial. Un TSB seleccionado permanece
inelegible para indexación hasta tener aprobación documental y técnica explícita.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "machine_learning" / "data" / "experimental_nhtsa" / "nhtsa_tsbs_rag_candidates.jsonl"
OUT_DIR = Path(__file__).resolve().parent / "rag_candidates"
OUT = OUT_DIR / "lote_revision_tsb_nhtsa.csv"
REPORT = OUT_DIR / "reporte_lote_tsb_nhtsa.json"
PER_SYSTEM = 10
SYSTEMS = ("FRENOS", "MOTOR", "TRANSMISION", "SUSPENSION_CHASIS", "DIRECCION", "CLIMATIZACION", "ELECTRICO")


def classify(component: str) -> str:
    text = component.upper()
    if "BRAKE" in text:
        return "FRENOS"
    if "STEER" in text:
        return "DIRECCION"
    if any(word in text for word in ("SUSPENSION", "WHEEL", "TIRE")):
        return "SUSPENSION_CHASIS"
    if any(word in text for word in ("TRANSMISSION", "POWER TRAIN", "CLUTCH", "AXLE", "DRIVELINE")):
        return "TRANSMISION"
    if any(word in text for word in ("AIR CONDITION", "CLIMATE", "HVAC", "HEATER", "DEFROST")):
        return "CLIMATIZACION"
    if any(word in text for word in ("ELECTRICAL", "BATTERY", "ALTERNATOR", "ELECTRONIC")):
        return "ELECTRICO"
    return "MOTOR"


def text_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.casefold().split()).encode("utf-8")).hexdigest()


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"No existe el archivo experimental: {SOURCE}")
    selected: dict[str, list[dict[str, str]]] = {system: [] for system in SYSTEMS}
    seen: set[tuple[str, str]] = set()
    scanned = 0
    rejected = Counter()
    with SOURCE.open(encoding="utf-8") as source:
        for line in source:
            scanned += 1
            row = json.loads(line)
            if row.get("rag_status") != "candidate_requires_license_review":
                rejected["non_procedural_document"] += 1
                continue
            bulletin = row.get("bulletin_number", "").strip()
            text = row.get("text", "").strip()
            if not bulletin or len(text) < 120:
                rejected["missing_bulletin_or_short_text"] += 1
                continue
            system = classify(f"{row.get('component', '')} {row.get('subsystem', '')}")
            if len(selected[system]) >= PER_SYSTEM:
                continue
            identity = (bulletin.casefold(), text_hash(text))
            if identity in seen:
                rejected["duplicate_bulletin_text"] += 1
                continue
            seen.add(identity)
            selected[system].append({
                "review_id": f"NHTSA-TSB-{system}-{len(selected[system]) + 1:02d}",
                "system_candidate": system,
                "bulletin_number": bulletin,
                "document_type": row.get("document_type", ""),
                "make": row.get("make", ""),
                "model": row.get("model", ""),
                "model_year": row.get("model_year", ""),
                "component": row.get("component", ""),
                "subsystem": row.get("subsystem", ""),
                "text": text,
                "source_file": row.get("source_file", ""),
                "source": "NHTSA_TSB_PUBLIC_DATA",
                "license_review_status": "pending_license_review",
                "technical_review_status": "pending_technical_review",
                "eligible_for_faiss": "NO",
                "reviewer": "",
                "observations": "",
            })
            if all(len(items) >= PER_SYSTEM for items in selected.values()):
                break

    records = [record for system in SYSTEMS for record in selected[system]]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = list(records[0]) if records else []
    with OUT.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    report = {
        "source": str(SOURCE),
        "scanned_records": scanned,
        "selected_records": len(records),
        "selected_by_system": {system: len(items) for system, items in selected.items()},
        "discard_reasons": dict(rejected),
        "invariant": "No se construyó índice FAISS ni se modificó el corpus RAG oficial.",
        "next_step": "Revisión individual de licencia y contenido técnico antes de cualquier indexación candidata.",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
