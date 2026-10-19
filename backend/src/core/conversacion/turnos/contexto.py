"""Contexto exclusivo de un turno, nunca compartido entre sesiones."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ContextoTurno:
    session_id: Any
    texto_usuario: Any
    gestor_diagnostico: Any
    placa: Any
    marca_modelo: Any
    proveedor: Any
    diagnostico_forzado: Any
    diferir_encolado_persistente: Any
    taller_id: Any
    usuario_id: Any
    conversacion_id: Any
    remitente: Any
