"""Clave de caché aislada por taller, sesión, caso y contenido del estado."""

import hashlib
import json

from src.core.diagnostic_cache import diagnostico_cache


def generar_clave_contextual(texto, marca, placa, case_id, taller_id, session_id, estado):
    if not case_id:
        return None
    payload = estado.exportar_dict(incluir_trazabilidad=False) if estado else {}
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    ).hexdigest()
    return diagnostico_cache.generar_clave(
        sintoma=f"{texto}__t{taller_id or ''}__s{session_id or ''}__estado_{digest}",
        marca_modelo=marca or "",
        placa=placa or "",
        case_id=case_id,
    )
