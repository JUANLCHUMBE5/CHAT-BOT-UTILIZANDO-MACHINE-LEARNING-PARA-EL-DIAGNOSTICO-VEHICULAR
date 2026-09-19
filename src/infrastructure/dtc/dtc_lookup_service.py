"""Servicio de búsqueda offline de códigos de diagnóstico automotriz (DTC / OBD-II)."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import ML_ROOT


class DtcLookupService:
    """
    Adaptador de infraestructura de solo lectura para la base de datos local de 18,805 códigos DTC.
    Thread-safe y de ultra-baja latencia (< 0.5 ms).
    """

    def __init__(self, ruta_db: Optional[Path] = None):
        self.ruta_db = ruta_db or (ML_ROOT / "data" / "fuentes_abiertas" / "dtc_codes.db")
        self._disponible = self.ruta_db.exists()

    @property
    def disponible(self) -> bool:
        return self._disponible

    def consultar_codigo(self, codigo: str, marca: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Busca un código DTC (ej. 'P0301', 'P0171', 'P1135') por código y opcionalmente por marca.
        Devuelve información estructurada o None si no existe.
        """
        if not self._disponible:
            return None

        codigo_limpio = codigo.strip().upper()
        # Normalizar para buscar códigos estándar de 5 caracteres (ej. P0301)
        match = re.search(r"\b([PBCU]\d{4})\b", codigo_limpio)
        if match:
            codigo_limpio = match.group(1)

        try:
            # Conexión de solo lectura URI para máxima velocidad y seguridad concurrente
            uri = f"file:{self.ruta_db.as_posix()}?mode=ro"
            with sqlite3.connect(uri, uri=True, timeout=2.0) as conn:
                cursor = conn.cursor()

                # 1. Si se especificó marca, intentar buscar la definición específica del fabricante
                if marca:
                    marca_limpia = marca.strip().upper()
                    cursor.execute(
                        "SELECT code, manufacturer, description, type FROM dtc_definitions "
                        "WHERE code = ? AND UPPER(manufacturer) LIKE ? LIMIT 1;",
                        (codigo_limpio, f"%{marca_limpia}%"),
                    )
                    fila = cursor.fetchone()
                    if fila:
                        return {
                            "codigo": fila[0],
                            "marca": fila[1],
                            "descripcion": fila[2],
                            "categoria": fila[3],
                            "es_especifico_fabricante": True,
                        }

                # 2. Búsqueda estándar (genérico o cualquier marca)
                cursor.execute(
                    "SELECT code, manufacturer, description, type FROM dtc_definitions "
                    "WHERE code = ? ORDER BY CASE WHEN manufacturer = 'GENERIC' THEN 0 ELSE 1 END LIMIT 1;",
                    (codigo_limpio,),
                )
                fila = cursor.fetchone()
                if fila:
                    return {
                        "codigo": fila[0],
                        "marca": fila[1],
                        "descripcion": fila[2],
                        "categoria": fila[3],
                        "es_especifico_fabricante": (fila[1] != "GENERIC"),
                    }
        except Exception:
            return None

        return None

    def extraer_codigos_en_texto(self, texto: str) -> List[str]:
        """Detecta todos los códigos OBD-II presentes en el mensaje del usuario."""
        patron = r"\b([PBCU]\d{4})\b"
        return list(set(re.findall(patron, texto, re.IGNORECASE)))
