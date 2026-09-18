"""
DTC Lookup Service: Servicio estructurado de consulta exacta de códigos DTC.
Conecta a la base de datos de 18,805 registros (machine_learning/data/fuentes_abiertas/dtc_codes.db)
de forma aislada, sin indexar en FAISS ni alterar las probabilidades del clasificador C1.
Cumple con las Secciones 24, 25 y 26 del mandato técnico.
"""
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
DEFAULT_DB_PATH = PROJECT_ROOT / "machine_learning/data/fuentes_abiertas/dtc_codes.db"

class DTCLookupService:
    """Servicio desacoplado para normalización y búsqueda relacional de códigos OBD-II."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos DTC no encontrada en: {self.db_path}")
        self._pattern = re.compile(r"\b([PCBU][0-9A-F]{4})\b", re.IGNORECASE)

    def normalizar_codigo(self, raw_code: str) -> str:
        """Limpia y normaliza el código DTC a formato estándar ISO/SAE (e.g., 'p0301' -> 'P0301')."""
        return raw_code.strip().upper()

    def extraer_codigos(self, texto: str) -> List[str]:
        """Detecta y extrae todos los códigos DTC presentes en el texto del usuario."""
        if not texto:
            return []
        matches = self._pattern.findall(texto)
        codigos_unicos = []
        for m in matches:
            norm = self.normalizar_codigo(m)
            if norm not in codigos_unicos:
                codigos_unicos.append(norm)
        return codigos_unicos

    def lookup(self, code: str, make: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Realiza búsqueda relacional exacta de un código DTC."""
        norm_code = self.normalizar_codigo(code)
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        try:
            # Si se proporciona marca, buscar primero coincidencia de marca específica
            if make:
                make_upper = make.strip().upper()
                cursor.execute(
                    "SELECT code, manufacturer, description, type, locale, is_generic, source_file "
                    "FROM dtc_definitions WHERE code = ? AND manufacturer = ? LIMIT 1",
                    (norm_code, make_upper)
                )
                row = cursor.fetchone()
                if row:
                    return self._formatear_resultado(row)

            # Buscar coincidencia genérica estándar
            cursor.execute(
                "SELECT code, manufacturer, description, type, locale, is_generic, source_file "
                "FROM dtc_definitions WHERE code = ? ORDER BY is_generic DESC LIMIT 1",
                (norm_code,)
            )
            row = cursor.fetchone()
            if row:
                return self._formatear_resultado(row)
            return None
        finally:
            conn.close()

    def _formatear_resultado(self, row: tuple) -> Dict[str, Any]:
        return {
            "code": row[0],
            "manufacturer": row[1],
            "description": row[2],
            "type": row[3],
            "locale": row[4],
            "is_generic": bool(row[5]),
            "source": f"dtc_codes.db ({row[6] or 'generic'})",
            "evidence_note": (
                "El código DTC orienta el subsistema bajo supervisión electrónica OBD-II; "
                "no confirma avería mecánica intrínseca sin comprobación física previa."
            )
        }

    def detect_and_lookup(self, text: str, make: Optional[str] = None) -> List[Dict[str, Any]]:
        """Detecta todos los DTCs en el texto y devuelve la lista de evidencias estructuradas."""
        codes = self.extraer_codigos(text)
        results = []
        for c in codes:
            res = self.lookup(c, make=make)
            if res:
                results.append(res)
        return results
