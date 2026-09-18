"""Registro de telemetría de diagnósticos para análisis y trazabilidad del taller."""

from __future__ import annotations

import csv
import datetime
import os
import threading
import time

from src.config import settings
from src.core.logger import logger
from src.core.security import anonimizar_identificador

_tracker_lock = threading.Lock()


def registrar_en_tracker(
    placa: str,
    marca_modelo: str,
    sintoma: str,
    diagnostico_ml: str,
    campos_completos: int = 1,
) -> None:
    """Registra el evento de diagnóstico de forma anónima y segura en data/tracker_diagnosticos.csv."""
    try:
        tracker_path = settings.paths.tracker_csv
        os.makedirs(os.path.dirname(tracker_path), exist_ok=True)

        nueva_fila = [
            time.time_ns(),
            "Post-test",
            datetime.date.today().isoformat(),
            anonimizar_identificador(placa),
            marca_modelo or "Generico",
            sintoma,
            diagnostico_ml,
            diagnostico_ml,
            campos_completos,
            1,
            1,
        ]
        encabezado = [
            "item", "fase", "fecha", "placa", "marca_modelo", "sintoma",
            "falla_real", "chatbot_prediccion", "campos_completos",
            "tiempo_diagnostico_minutos", "prediccion_correcta",
        ]

        with _tracker_lock:
            archivo_nuevo = not os.path.exists(tracker_path) or os.path.getsize(tracker_path) == 0
            with open(tracker_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if archivo_nuevo:
                    writer.writerow(encabezado)
                writer.writerow(nueva_fila)
    except Exception as e:
        logger.warning(f"No se pudo registrar en tracker CSV: {e}")
