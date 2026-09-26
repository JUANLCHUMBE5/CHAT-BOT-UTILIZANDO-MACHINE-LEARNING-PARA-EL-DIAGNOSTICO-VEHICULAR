"""Selecciona 10 casos por estrato para revisión mecánica inicial."""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "machine_learning/data/experimental_nhtsa/muestra_revision_mecanica.jsonl"
dst = ROOT / "machine_learning/data/experimental_nhtsa/lote_revision_mecanica_90.csv"
buckets = defaultdict(list)
for line in src.open(encoding="utf-8"):
    row = json.loads(line)
    key = row["candidate_label"]
    if len(buckets[key]) < 10:
        buckets[key].append(row)

fields = ["review_id", "text", "make", "model", "model_year", "component_reported",
          "candidate_label", "content_type", "text_quality", "label_final", "reviewer",
          "review_status", "confidence", "observations"]
with dst.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    i = 1
    for key in sorted(buckets):
        for row in buckets[key]:
            writer.writerow({"review_id": f"NHTSA-REV-{i:03d}", "text": row["text"],
                             "make": row.get("make", ""), "model": row.get("model", ""),
                             "model_year": row.get("model_year", ""),
                             "component_reported": row.get("component_reported", ""),
                             "candidate_label": key,
                             "content_type": row.get("content_type", "unknown"),
                             "text_quality": row.get("text_quality", "unknown"),
                             "label_final": "", "reviewer": "",
                             "review_status": "pending_mechanical_review", "confidence": "",
                             "observations": ""})
            i += 1
print(f"[OK] lote={i-1} archivo={dst}")
