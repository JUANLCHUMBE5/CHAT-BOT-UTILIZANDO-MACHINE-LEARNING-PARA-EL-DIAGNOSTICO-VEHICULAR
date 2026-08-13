"""Entidades para identidades externas de mensajería y solicitudes de acceso."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.catalogs import Taller, Usuario


class IdentidadWhatsApp(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Identidad externa segura vinculada a un usuario.
    Guarda el hash HMAC-SHA256 del número, wa_id o user_id privado de Meta/Twilio,
    y el destinatario cifrado reversiblemente para envíos directos sin exponer texto plano.
    """
    __tablename__ = "identidades_whatsapp"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    proveedor: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="meta",
    )
    identificador_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )
    destinatario_cifrado: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    tipo_identificador: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="telefono",
    )
    ultimos4: Mapped[str | None] = mapped_column(
        String(4),
        nullable=True,
    )
    ultima_interaccion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    usuario: Mapped["Usuario"] = relationship(back_populates="identidades_whatsapp")

    __table_args__ = (
        CheckConstraint("proveedor IN ('meta', 'twilio', 'api')", name="ck_identidad_proveedor_valido"),
        CheckConstraint("tipo_identificador IN ('telefono', 'wa_id', 'user_id')", name="ck_identidad_tipo_valido"),
        CheckConstraint("length(identificador_hash) = 64", name="ck_identidad_hash_longitud"),
        CheckConstraint("ultimos4 IS NULL OR length(ultimos4) <= 4", name="ck_identidad_ultimos4_longitud"),
    )


class SolicitudAcceso(UUIDPrimaryKeyMixin, Base):
    """
    Solicitud de acceso creada cuando un cliente solicita autorización como mecánico.
    """
    __tablename__ = "solicitudes_acceso"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    taller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("talleres.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rol_solicitado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="mecanico",
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pendiente",
    )
    solicitado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    revisado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    revisado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    observaciones: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    usuario: Mapped["Usuario"] = relationship(
        foreign_keys=[usuario_id],
        back_populates="solicitudes_acceso",
    )
    taller: Mapped["Taller"] = relationship(
        foreign_keys=[taller_id],
        back_populates="solicitudes_acceso",
    )
    revisado_por: Mapped["Usuario | None"] = relationship(
        foreign_keys=[revisado_por_id],
    )

    __table_args__ = (
        CheckConstraint("estado IN ('pendiente', 'aprobada', 'rechazada')", name="ck_solicitud_estado_valido"),
        Index("ix_solicitudes_acceso_taller_estado", "taller_id", "estado"),
    )
