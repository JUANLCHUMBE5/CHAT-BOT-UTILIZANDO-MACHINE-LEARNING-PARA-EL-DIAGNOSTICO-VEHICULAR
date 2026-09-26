"""Genera una muestra estratificada para revisión mecánica humana.

Las etiquetas generadas aquí son candidatas por componente, no ground truth.
"""
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "machine_learning" / "data" / "experimental_nhtsa" / "nhtsa_complaints_unlabeled.jsonl"
OUT = ROOT / "machine_learning" / "data" / "experimental_nhtsa" / "muestra_revision_mecanica.jsonl"
PER_STRATUM = 50
SEED = 42


def candidate(component: str) -> str:
    c = component.upper()
    if "BRAKE" in c: return "FRENOS"
    if "STEER" in c: return "DIRECCION"
    if "SUSPENSION" in c or "WHEEL" in c or "TIRE" in c or "AXLE" in c: return "SUSPENSION_CHASIS"
    if "TRANSMISSION" in c or "POWER TRAIN" in c: return "TRANSMISION"
    if "DIESEL" in c or "PARTICULATE" in c or "DPF" in c: return "MOTOR_DIESEL_DPF"
    if "ENGINE" in c or "FUEL" in c: return "MOTOR"
    if "AIR CONDITION" in c or "CLIMATE" in c or "HVAC" in c: return "CLIMATIZACION"
    if "ELECTRICAL" in c: return "ELECTRICO_ELECTRONICO"
    return "REVISAR_MANUALMENTE"


def main() -> None:
    rng = random.Random(SEED)
    buckets: dict[str, list[dict]] = defaultdict(list)
    seen: set[str] = set()
    with SOURCE.open(encoding="utf-8") as src:
        for line in src:
            row = json.loads(line)
            text = " ".join(row.get("text", "").split())
            if len(text) < 40:
                continue
            # Las campañas y reclamos administrativos se conservan en el archivo
            # experimental, pero no deben ocupar el primer lote de un mecánico.
            if row.get("content_type") == "administrative_or_campaign":
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            strat = candidate(row.get("component_reported", ""))
            item = {"text": text, "make": row.get("make"), "model": row.get("model"),
                    "model_year": row.get("model_year"), "component_reported": row.get("component_reported"),
                    "candidate_label": strat, "label": None,
                    "label_source": "nhtsa_component_weak_candidate",
                    "content_type": row.get("content_type", "unknown"),
                    "text_quality": (
                        "high_symptom_detail"
                        if row.get("content_type") == "symptom_detail_candidate"
                        else "general_symptom_description"
                    ),
                    "review_status": "pending_mechanical_review"}
            bucket = buckets[strat]
            if len(bucket) < PER_STRATUM:
                bucket.append(item)
            else:
                bucket[rng.randrange(PER_STRATUM)] = item
    records = [x for key in sorted(buckets) for x in buckets[key]]
    OUT.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in records) + "\n", encoding="utf-8")
    print(f"[OK] muestra={len(records)} estratos={dict((k, len(v)) for k,v in sorted(buckets.items()))}")


if __name__ == "__main__":
    main()
