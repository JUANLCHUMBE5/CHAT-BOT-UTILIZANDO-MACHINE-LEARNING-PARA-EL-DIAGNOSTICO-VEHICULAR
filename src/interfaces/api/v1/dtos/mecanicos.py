"""Contratos HTTP para gestión de personal técnico."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

RolGestionable = Literal["mecanico", "jefe_taller", "administrador"]


class MecanicoCreateDTO(BaseModel):
    nombres: str = Field(max_length=120)
    username: Optional[str] = Field(default=None, max_length=60)
    telefono_whatsapp: str = Field(max_length=30)
    password: Optional[str] = Field(default=None, max_length=128)
    rol: RolGestionable = "mecanico"


class MecanicoUpdateDTO(BaseModel):
    nombres: Optional[str] = Field(default=None, max_length=120)
    username: Optional[str] = Field(default=None, max_length=60)
    telefono_whatsapp: Optional[str] = Field(default=None, max_length=30)
    password: Optional[str] = Field(default=None, max_length=128)


class CambiarRolDTO(BaseModel):
    nuevo_rol: RolGestionable
    password: Optional[str] = Field(default=None, max_length=128)


class MecanicoResponseDTO(BaseModel):
    id: str
    nombres: str
    username: Optional[str] = None
    telefono: str
    rol: str
    activo: bool
    bloqueado: bool
    fecha_registro: str
    total_diagnosticos: int
    ultimo_acceso: str


class RevocarAccesoResponseDTO(BaseModel):
    mensaje: str
    usuario_id: str
    nuevo_rol: str
    historial_conservado: bool
