"""Carga determinista de configuracion antes de importar ``src.config``."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def cargar_variables_entorno(dotenv_path: Path | None = None) -> bool:
    """Carga ``.env`` con prioridad local sin pisar secretos de produccion.

    En desarrollo, el archivo del proyecto sustituye variables antiguas
    heredadas de Windows. En produccion, las variables inyectadas por AWS/ECS
    conservan prioridad sobre cualquier archivo local.
    """

    entorno_inicial = os.getenv("ENVIRONMENT", "development").strip().lower()
    es_produccion = entorno_inicial in {"production", "prod"}
    ruta = dotenv_path or PROJECT_ROOT / ".env"
    return load_dotenv(dotenv_path=ruta, override=not es_produccion)
