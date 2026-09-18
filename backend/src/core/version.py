"""Módulo de telemetría y versionado en runtime para CarBot (Fase 9.10).

Garantiza paridad estricta de versiones y build tokens entre procesos API y Worker.
"""

from __future__ import annotations

import hashlib
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

APP_VERSION = "11.4.0"
ORCHESTRATOR_VERSION = "11.4.0"

_START_TIME = datetime.now(timezone.utc).isoformat()
_START_TIMESTAMP = time.time()


def _generar_code_build_id() -> str:
    """Genera un build ID determinista basado en el contenido del core conversacional."""
    hasher = hashlib.sha256()
    hasher.update(APP_VERSION.encode("utf-8"))
    hasher.update(ORCHESTRATOR_VERSION.encode("utf-8"))
    
    # Huella de archivos clave
    archivos_clave = [
        os.path.join(os.path.dirname(__file__), "conversacion", "models.py"),
        os.path.join(os.path.dirname(__file__), "conversacion", "orquestador_conversacion.py"),
        os.path.join(os.path.dirname(__file__), "conversacion", "segmentador_casos.py"),
        os.path.join(os.path.dirname(__file__), "conversacion", "extractor_hechos.py"),
        os.path.join(os.path.dirname(__file__), "conversacion", "generador_preguntas.py"),
        os.path.join(os.path.dirname(__file__), "conversacion", "compatibilidad_preguntas.py"),
        os.path.join(os.path.dirname(__file__), "conversacion", "gestor_plan_b.py"),
        os.path.join(os.path.dirname(__file__), "conversacion", "interprete_respuestas_cortas.py"),
        os.path.join(os.path.dirname(__file__), "conversacion", "detector_polaridad.py"),
    ]
    for ruta in archivos_clave:
        if os.path.exists(ruta):
            try:
                with open(ruta, "rb") as f:
                    hasher.update(f.read())
            except Exception:
                pass
    return hasher.hexdigest()[:16]


CODE_BUILD_ID = _generar_code_build_id()


def obtener_rag_version() -> str:
    """Retorna la versión de RAG activa configurada."""
    try:
        from src.config import settings
        return getattr(settings, "rag_version", os.getenv("CARBOT_RAG_VERSION", "candidate_v1"))
    except Exception:
        return os.getenv("CARBOT_RAG_VERSION", "candidate_v1")


def obtener_telemetria_proceso(rol: str = "api") -> Dict[str, Any]:
    """Retorna la telemetría en runtime del proceso actual."""
    return {
        "rol": rol,
        "app_version": APP_VERSION,
        "orchestrator_version": ORCHESTRATOR_VERSION,
        "code_build_id": CODE_BUILD_ID,
        "rag_version": obtener_rag_version(),
        "pid": os.getpid(),
        "start_time": _START_TIME,
        "start_timestamp": _START_TIMESTAMP,
        "python_version": sys.version.split()[0],
    }


def registrar_startup_log(rol: str = "api", puerto: Optional[int] = None) -> None:
    """Registra en el logger estándar el bloque obligatorio de inicio del proceso."""
    from src.core.logger import logger
    port_str = str(puerto) if puerto else ("8000" if rol in ("api", "backend") else "N/A")
    logger.info(
        "CARBOT STARTUP | ROL=%s | APP_VERSION=%s | ORCHESTRATOR_VERSION=%s | "
        "CODE_BUILD_ID=%s | RAG_VERSION=%s | PID=%s | PORT=%s",
        rol.upper(),
        APP_VERSION,
        ORCHESTRATOR_VERSION,
        CODE_BUILD_ID,
        obtener_rag_version(),
        os.getpid(),
        port_str,
    )


def verificar_paridad_runtime(api_build: Dict[str, Any], worker_build: Dict[str, Any]) -> bool:
    """Verifica si la API y el Worker ejecutan exactamente el mismo build y versión."""
    if not api_build or not worker_build:
        return False
    return (
        api_build.get("orchestrator_version") == worker_build.get("orchestrator_version")
        and api_build.get("code_build_id") == worker_build.get("code_build_id")
    )
