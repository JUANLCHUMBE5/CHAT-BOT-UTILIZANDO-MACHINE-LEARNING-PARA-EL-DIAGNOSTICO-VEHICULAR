"""Comprueba archivos oficiales y oráculos frente a RAG-03H, sin reconstruirlos."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BASE = "50ae3a6eaafb42cbb627afe5cdf61ac5bc083a7c"
ORACULOS = [
    "backend/tests/calidad_conversacional/auditoria_rag03d_benchmark.py",
    "backend/tests/calidad_conversacional/criterios_seguridad.py",
    "backend/tests/calidad_conversacional/benchmark_rag03/escenarios_desarrollo.json",
    "backend/tests/calidad_conversacional/benchmark_rag03/modelos.py",
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads((ROOT / "backend/tests/fixtures/ml_42d607_integridad.json").read_text(encoding="utf-8"))
    paths = set(fixture["artifacts"]) | set(ORACULOS)
    # También se protege TODO machine_learning versionado, no solo ocho archivos.
    tracked = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE, "machine_learning"], cwd=ROOT, text=True)
    paths.update(tracked.splitlines())
    result = {}
    for rel in sorted(paths):
        expected = subprocess.check_output(["git", "show", f"{BASE}:{rel}"], cwd=ROOT)
        actual = (ROOT / rel).read_bytes()
        # Git puede materializar texto CRLF; registrar hash crudo y comparación LF.
        same = actual == expected
        try:
            actual.decode("utf-8")
            expected.decode("utf-8")
            text_lf = True
        except UnicodeDecodeError:
            text_lf = False
        equivalent = same or (text_lf and actual.replace(b"\r\n", b"\n") == expected.replace(b"\r\n", b"\n"))
        result[rel] = dict(sha256=sha(actual), base_sha256=sha(expected), bytes_identicos=same, equivalente_git=equivalent)
    sys.path.insert(0, str(ROOT / "backend"))
    from src.infrastructure.rag.paquete_experimental import cargar_paquete, validar_vectores

    corpus, vectorizador, indice, manifiesto = cargar_paquete(ROOT)
    ok, errores, motivo = validar_vectores(corpus, vectorizador, indice, manifiesto, ROOT)
    salida = dict(base=BASE, archivos=result, canonicos_ocho={p: result[p] for p in fixture["artifacts"]},
                  experimental=dict(ok=ok, errores=errores, motivo=motivo, documentos=len(corpus),
                                    vectores=indice.ntotal, dimensiones=indice.d))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(salida, indent=2), encoding="utf-8")
    assert all(x["equivalente_git"] for x in result.values()), "Cambió un artefacto u oráculo protegido"
    assert ok and len(corpus) == indice.ntotal == 256 and indice.d == 35240
    print(f"Integridad: {len(result)} archivos; ocho canónicos intactos; {motivo}")


if __name__ == "__main__":
    main()
