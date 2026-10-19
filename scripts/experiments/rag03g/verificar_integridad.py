"""Verificación de solo lectura de los ocho artefactos y paquete experimental."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def verificar(root):
    fixture = json.loads(
        (root / "backend/tests/fixtures/ml_42d607_integridad.json").read_text(
            encoding="utf-8"
        )
    )
    results = {}
    for rel, expected in fixture["artifacts"].items():
        data = (root / rel).read_bytes()
        raw = hashlib.sha256(data).hexdigest()
        if rel in fixture["canonical_text_lf"]:
            data = data.replace(b"\r\n", b"\n")
        actual = hashlib.sha256(data).hexdigest()
        results[rel] = dict(
            expected=expected, actual=actual, raw_sha256=raw, match=actual == expected
        )
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    sys.path.insert(0, str(ROOT / "backend"))
    from src.infrastructure.rag.paquete_experimental import (
        cargar_paquete,
        validar_vectores,
    )

    canonical = verificar(ROOT)
    corpus, vec, index, manifest = cargar_paquete(ROOT)
    ok, errors, reason = validar_vectores(corpus, vec, index, manifest, ROOT)
    result = dict(
        canonicos=canonical,
        experimental=dict(
            ok=ok, errors=errors, reason=reason, count=index.ntotal, dimension=index.d
        ),
        head=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        main=subprocess.check_output(
            ["git", "rev-parse", "main"], cwd=ROOT, text=True
        ).strip(),
        manifest=manifest,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if not ok or not all(x["match"] for x in canonical.values()):
        raise SystemExit("Integridad no acreditada")
    print("8/8 canónicos; " + reason)


if __name__ == "__main__":
    main()
