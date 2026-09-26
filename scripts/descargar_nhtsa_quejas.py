"""Descarga quejas NHTSA reproducibles para auditoría y dataset experimental.

Las quejas son evidencia textual, no diagnósticos confirmados. Se guardan fuera
del dataset congelado y requieren etiquetado antes de entrenar un modelo.
"""

import argparse
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "machine_learning" / "data" / "fuentes_abiertas" / "nhtsa_complaints"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--make", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--year", required=True, type=int)
    args = parser.parse_args()
    query = urllib.parse.urlencode({"make": args.make, "model": args.model, "modelYear": args.year})
    url = f"https://api.nhtsa.gov/complaints/complaintsByVehicle?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "CarBot-research/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.load(response)
    DEST.mkdir(parents=True, exist_ok=True)
    name = f"{args.year}_{args.make}_{args.model}".lower().replace(" ", "_")
    output = DEST / f"{name}.json"
    output.write_text(json.dumps({"source": "NHTSA", "url": url,
                                  "downloaded_at": datetime.now(timezone.utc).isoformat(),
                                  "license_note": "Public NHTSA complaint data; verify terms before redistribution.",
                                  "data": payload}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {output} ({len(payload.get('results', []))} quejas)")


if __name__ == "__main__":
    main()
