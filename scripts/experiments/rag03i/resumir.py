"""Materializa resultados reales de JUnit y benchmark, sin modificar oráculos."""

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def leer_suite(path):
    tree = ET.parse(path)
    casos = {}
    for caso in tree.iter("testcase"):
        clave = caso.get("classname", "") + "::" + caso.get("name", "")
        error = caso.find("failure")
        if error is None:
            error = caso.find("error")
        skip = caso.find("skipped")
        casos[clave] = dict(
            estado="FAIL" if error is not None else ("SKIP" if skip is not None else "PASS"),
            mensaje=error.get("message") if error is not None else None,
            detalle=error.text if error is not None else None,
        )
    return dict(suites=[s.attrib for s in tree.iter("testsuite")], casos=casos)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("evidencias", type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    out = args.evidencias.resolve()
    resultado = {}
    for nombre in ("suite-final", "seguridad-definitiva", "regresiones-definitivas", "agentes-final"):
        resultado[nombre] = leer_suite(out / nombre / "pytest.xml")
    benchmark = json.loads((out / "benchmark-definitivo/benchmark.json").read_text(encoding="utf-8"))
    resultado["benchmark"] = {k: benchmark[k] for k in ("total_escenarios", "total_pass", "total_fail", "tiempo_total_segundos")}
    resultado["fallos_benchmark"] = [caso for caso in benchmark["detalles"] if not caso["resultado_global_pass"]]
    if args.baseline:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        resultado["comparacion_17"] = {
            fallo["id"]: resultado["suite-final"]["casos"].get(fallo["id"], {"estado": "NO_EJECUTADO"})
            for fallo in baseline["backend-completo"]["failures"]
        }
    (out / "resumen-final.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    manifiesto = {
        str(path.relative_to(out)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(out.rglob("*"))
        if path.is_file() and path.suffix in (".json", ".xml", ".log", ".txt")
        and "tmp" not in path.relative_to(out).parts and path.name != "manifiesto-evidencias.json"
    }
    (out / "manifiesto-evidencias.json").write_text(json.dumps(manifiesto, indent=2), encoding="utf-8")
    print(resultado["benchmark"])
    print(resultado["suite-final"]["suites"])


if __name__ == "__main__":
    main()
