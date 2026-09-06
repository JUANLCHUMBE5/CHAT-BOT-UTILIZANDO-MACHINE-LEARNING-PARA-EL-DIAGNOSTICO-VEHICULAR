"""Contratos HTTP para clientes y solicitudes de acceso."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ClienteResponseDTO(BaseModel):
    id: str
    nombres: str
    telefono: str
    tipo_identificador: str
    activo: bool
    bloqueado: bool
    fecha_registro: str
    ultima_interaccion: str
    tiene_solicitud_pendiente: bool = False
    solicitud_id: Optional[str] = None


class SolicitudAccesoResponseDTO(BaseModel):
    id: str
    usuario_id: str
    usuario_nombre: str
    telefono: str
    rol_solicitado: str
    estado: str
    solicitado_en: str
    revisado_por: Optional[str] = None
    revisado_en: Optional[str] = None
    observaciones: Optional[str] = None


class AprobarSolicitudResponseDTO(BaseModel):
    mensaje: str
    solicitud_id: str
    usuario_id: str
    nuevo_rol: str


class RechazarSolicitudDTO(BaseModel):
    motivo: Optional[str] = Field(default=None, max_length=500)
