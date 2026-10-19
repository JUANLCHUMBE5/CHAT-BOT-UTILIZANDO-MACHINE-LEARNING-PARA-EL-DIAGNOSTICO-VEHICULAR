"""Runner offline reproducible: red denegada salvo dos puertos de pruebas.

Uso: python ejecutar.py --out DIR [--db] pytest tests/...
     python ejecutar.py --out DIR benchmark
"""

import argparse
import asyncio
import faulthandler
import importlib.util
import inspect
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
DB = "postgresql+asyncpg://carbot_test:isolated_rag03g_tests_only@127.0.0.1:55439/carbot_rag03g_test"


def entorno(out, db=False):
    sys.dont_write_bytecode = True
    # Ignorar cualquier credencial heredada antes de cargar config.
    for key in list(os.environ):
        if any(
            w in key for w in ("GEMINI", "GROQ", "META_", "WHATSAPP", "TWILIO", "AWS_")
        ):
            os.environ[key] = ""
    os.environ.update(
        ENVIRONMENT="test",
        CARBOT_BLOCK_DOTENV="1",
        DATABASE_ENABLED=str(db).lower(),
        DATABASE_REQUIRED=str(db).lower(),
        DATABASE_URL=DB if db else "",
        TEST_DATABASE_URL=DB if db else "",
        DATABASE_POOL_SIZE="0",
        REDIS_URL="redis://127.0.0.1:56389/0" if db else "",
        RATE_LIMIT_STORAGE_URI="redis://127.0.0.1:56389/1" if db else "memory://",
        CARBOT_RAG_VERSION="candidate_v1",
        GROQ_CHAT_ENABLED="false",
        GROQ_AUDIO_ENABLED="false",
        QUEUE_EMBEDDED_WORKER="false",
        TRACKER_CSV_PATH=str(out / "tracker_demo.csv"),
        JWT_SECRET_KEY="isolated_test_key_for_rag03g_123456789",
        PRIVACY_SECRET_KEY="isolated_test_privacy_for_rag03g_123456789",
        META_APP_SECRET="isolated_rag03g_test_secret",
        META_VERIFY_TOKEN="ci_meta_verify_token",
        MPLCONFIGDIR=str(out / "matplotlib"),
        PYTHONDONTWRITEBYTECODE="1",
    )
    os.environ.update(
        OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1"
    )

    def guard(event, args):
        if event == "subprocess.Popen" and any(
            w in str(args).lower()
            for w in ("entrenar_modelo", "training/entrenar", "training\\entrenar")
        ):
            raise RuntimeError("RAG03G_CANONICAL_TRAINING_BLOCKED")
        if event == "open":
            path, mode, flags = args
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int)
                and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
            )
            if writing and isinstance(path, (str, bytes, os.PathLike)):
                p = Path(path).resolve()
                if str(p).upper() in ("NUL", r"\\.\NUL"):
                    return
                if "__pycache__" in str(p) or str(p).endswith(".pyc"):
                    return
                if p.is_relative_to(ROOT / "machine_learning") or not (
                    p.is_relative_to(ROOT) or p.is_relative_to(out)
                ):
                    raise RuntimeError("RAG03G_WRITE_BLOCKED " + str(p))
        if event == "socket.connect":
            address = args[1]
            if any(f.function == "_fallback_socketpair" for f in inspect.stack()):
                return
            if (
                db
                and isinstance(address, tuple)
                and address[0] in ("127.0.0.1", "::1")
                and address[1] in (55439, 56389)
            ):
                return
            raise RuntimeError("RAG03G_NETWORK_BLOCKED " + str(address))

    sys.addaudithook(guard)
    tempfile.tempdir = str(out)
    sys.path.insert(0, str(ROOT / "backend"))
    os.chdir(ROOT / "backend")


def main():
    global DB
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--db", action="store_true")
    parser.add_argument("--e2e-db", action="store_true")
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument(
        "mode", choices=["pytest", "benchmark", "rag", "package", "migrate", "e2e"]
    )
    args, extra = parser.parse_known_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.e2e_db:
        DB = DB.replace("carbot_rag03g_test", "carbot_rag03g_e2e_test")
    entorno(out, args.db)
    if args.e2e_db:
        os.environ["REDIS_URL"] = "redis://127.0.0.1:56389/4"
        os.environ["RATE_LIMIT_STORAGE_URI"] = "redis://127.0.0.1:56389/5"
    if args.mode == "pytest":
        os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        faulthandler.dump_traceback_later(45, repeat=True)
        print("Inicio pytest aislado; db=" + str(args.db), flush=True)
        import pytest

        cov = None
        if args.coverage:
            import coverage

            cov = coverage.Coverage(
                source=[str(ROOT / "backend/src")],
                data_file=str(out / ".coverage"),
                timid=False,
            )
            cov.start()
        pytest_args = [
            "-q",
            "-p",
            "no:cacheprovider",
            "-p",
            "anyio.pytest_plugin",
        ]
        if importlib.util.find_spec("pytest_asyncio") is not None:
            pytest_args.extend(["-p", "pytest_asyncio.plugin"])
        pytest_args.extend(
            [
                "-m",
                "not real_gemini",
                "--basetemp=" + str(out / "tmp"),
                "--junitxml=" + str(out / "pytest.xml"),
                *extra,
            ]
        )
        rc = pytest.main(pytest_args)
        if cov:
            cov.stop()
            cov.save()
            cov.json_report(outfile=str(out / "coverage.json"))
            cov.report()
        (out / "exit.json").write_text(json.dumps({"exit": int(rc)}), encoding="utf-8")
        raise SystemExit(rc)
    if args.mode == "benchmark":
        ns = runpy.run_path(
            str(
                ROOT
                / "backend/tests/calidad_conversacional/auditoria_rag03d_benchmark.py"
            ),
            run_name="rag03g_benchmark",
        )
        result = asyncio.run(ns["ejecutar_benchmark_completo"](guardar_archivos=False))
        (out / "benchmark.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    elif args.mode == "rag":
        ns = runpy.run_path(
            str(
                ROOT
                / "machine_learning/rag/experimentos/rag03c/ejecutar_rag03c2_final.py"
            ),
            run_name="rag03g_rag",
        )
        for key, name in [
            ("BENCHMARK_100_QUERIES", "100"),
            ("PRUEBAS_ADVERSARIALES_30", "30"),
        ]:
            result = ns["evaluar_suite"](ns[key], nombre_suite="desarrollo_" + name)
            (out / ("rag_" + name + ".json")).write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print("RAG", name, result["precision_at_1_total"])
    elif args.mode == "package":
        from src.infrastructure.rag.paquete_experimental import cargar_paquete

        corpus, vec, idx, manifest = cargar_paquete(ROOT)
        print(
            json.dumps(
                {
                    "n": len(corpus),
                    "ntotal": idx.ntotal,
                    "d": idx.d,
                    "version": manifest["version"],
                }
            )
        )
    elif args.mode == "migrate":
        from alembic.config import Config
        from alembic import command

        if not args.db:
            raise ValueError("--db requerido")
        command.upgrade(Config("alembic.ini"), "head")
    elif args.mode == "e2e":
        if not args.db:
            raise ValueError("--db requerido")
        ns = runpy.run_path(str(ROOT / "scripts/experiments/rag03g/simular_e2e.py"))
        asyncio.run(ns["simular"](out))


if __name__ == "__main__":
    main()
