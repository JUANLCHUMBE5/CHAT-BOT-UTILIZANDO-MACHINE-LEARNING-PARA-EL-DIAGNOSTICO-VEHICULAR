"""Carga determinista de configuracion antes de importar ``src.config``."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def cargar_variables_entorno(dotenv_path: Path | None = None) -> bool:
    """Carga ``.env`` con prioridad local sin pisar secretos de produccion.

    En desarrollo, el archivo del proyecto sustituye variables antiguas
    heredadas de Windows. En produccion, las variables inyectadas por AWS/ECS
    conservan prioridad sobre cualquier archivo local.
    """

    # Los runners E2E aislados declaran esta barrera antes de importar la
    # configuración. Así ni un `.env` copiado accidentalmente en una imagen de
    # prueba puede reintroducir claves de proveedores externos.
    if os.getenv("CARBOT_BLOCK_DOTENV", "").strip().lower() in {"1", "true", "yes"}:
        return False

    entorno_inicial = os.getenv("ENVIRONMENT", "development").strip().lower()
    es_produccion = entorno_inicial in {"production", "prod"}
    ruta = dotenv_path or PROJECT_ROOT / ".env"
    return load_dotenv(dotenv_path=ruta, override=not es_produccion)
