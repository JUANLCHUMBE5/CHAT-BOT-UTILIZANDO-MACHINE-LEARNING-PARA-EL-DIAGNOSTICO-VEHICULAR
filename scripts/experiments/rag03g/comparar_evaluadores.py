"""Mismo runtime, escenarios históricos públicos y tres criterios. No es holdout."""

import argparse
import asyncio
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import types

from ejecutar import ROOT, entorno


async def comparar(out):
    path = ROOT / "backend/tests/calidad_conversacional/auditoria_rag03d_benchmark.py"
    summary = {}
    scenario_hash = None
    for label, commit in [
        ("original", "1858be4e"),
        ("rag03f", "3fa09f4e"),
        ("rag03g", None),
    ]:
        if commit:
            source = subprocess.check_output(
                [
                    "git",
                    "show",
                    f"{commit}:backend/tests/calidad_conversacional/auditoria_rag03d_benchmark.py",
                ],
                cwd=ROOT,
            )
            module = types.ModuleType("criterios_" + label)
            module.__file__ = str(path)
            sys.modules[module.__name__] = module
            exec(compile(source, str(path), "exec"), module.__dict__)
            ns = module.__dict__
        else:
            source = path.read_bytes()
            ns = runpy.run_path(str(path), run_name="criterios_rag03g")
        cases = [asdict(c) for c in ns["construir_escenarios_auditoria"]()]
        digest = hashlib.sha256(
            json.dumps(cases, sort_keys=True, ensure_ascii=True).encode()
        ).hexdigest()
        if scenario_hash is not None and digest != scenario_hash:
            raise ValueError(
                "Los escenarios u oráculos históricos difieren; comparación detenida"
            )
        scenario_hash = digest
        result = await ns["ejecutar_benchmark_completo"](guardar_archivos=False)
        (out / (label + ".json")).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary[label] = {
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "scenarios_sha256": digest,
            **{
                k: result.get(k)
                for k in (
                    "total_escenarios",
                    "total_pass",
                    "total_fail",
                    "tiempo_total_segundos",
                )
            },
        }
    (out / "comparacion.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, type=Path)
    out = p.parse_args().out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    entorno(out)
    asyncio.run(comparar(out))


if __name__ == "__main__":
    main()
