"""Runner offline con bases desechables; comparte el bloqueo de red de RAG-03G."""

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("runner_aislado", ROOT / "scripts/experiments/rag03g/ejecutar.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
database = "carbot_rag03i_e2e_test" if "--e2e-db" in sys.argv else "carbot_test"
runner.DB = f"postgresql+asyncpg://carbot_app:isolated_rag03i_tests_only@127.0.0.1:55439/{database}"

if __name__ == "__main__":
    runner.main()
