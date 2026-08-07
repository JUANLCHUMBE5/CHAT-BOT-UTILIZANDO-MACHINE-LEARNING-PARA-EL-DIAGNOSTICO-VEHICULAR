"""Entidades de talleres, roles y usuarios autorizados."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, SmallInteger, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.diagnostics import Diagnostico, Vehiculo
    from src.infrastructure.database.models.messaging import Conversacion, Mensaje


class Taller(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "talleres"

    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    ruc: Mapped[str | None] = mapped_column(String(11), unique=True)
    telefono: Mapped[str | None] = mapped_column(String(30))
    direccion: Mapped[str | None] = mapped_column(String(250))
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="taller")
    vehiculos: Mapped[list["Vehiculo"]] = relationship(back_populates="taller")
    diagnosticos: Mapped[list["Diagnostico"]] = relationship(back_populates="taller")

    __table_args__ = (
        CheckConstraint("ruc IS NULL OR length(ruc) = 11", name="ruc_longitud"),
    )


class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    codigo: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(250))

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")


class Usuario(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "usuarios"

    taller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("talleres.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    rol_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    nombres: Mapped[str] = mapped_column(String(120), nullable=False)
    apellidos: Mapped[str | None] = mapped_column(String(120))
    whatsapp_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    whatsapp_ultimos4: Mapped[str] = mapped_column(String(4), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    taller: Mapped["Taller"] = relationship(back_populates="usuarios")
    rol: Mapped["Rol"] = relationship(back_populates="usuarios")
    vehiculos_registrados: Mapped[list["Vehiculo"]] = relationship(back_populates="registrado_por")
    diagnosticos: Mapped[list["Diagnostico"]] = relationship(back_populates="mecanico")
    conversaciones: Mapped[list["Conversacion"]] = relationship(back_populates="usuario")
    mensajes: Mapped[list["Mensaje"]] = relationship(back_populates="usuario")

    __table_args__ = (
        CheckConstraint("length(whatsapp_hash) = 64", name="whatsapp_hash_longitud"),
        CheckConstraint("length(whatsapp_ultimos4) = 4", name="whatsapp_ultimos4_longitud"),
        UniqueConstraint("taller_id", "id", name="uq_usuarios_taller_id_id"),
    )
