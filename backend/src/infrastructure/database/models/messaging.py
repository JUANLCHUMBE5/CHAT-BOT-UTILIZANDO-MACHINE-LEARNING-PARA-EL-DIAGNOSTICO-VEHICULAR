"""Entidades para conversaciones y mensajes de WhatsApp."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.catalogs import Taller, Usuario
    from src.infrastructure.database.models.diagnostics import Diagnostico
    from src.infrastructure.database.models.operations import UsoApi


class Conversacion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversaciones"

    taller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("talleres.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    canal: Mapped[str] = mapped_column(
        String(20), nullable=False, default="whatsapp", server_default=text("'whatsapp'")
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="abierta", server_default=text("'abierta'")
    )
    iniciada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ultimo_mensaje_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ventana_servicio_hasta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cerrada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    taller: Mapped["Taller"] = relationship()
    usuario: Mapped["Usuario"] = relationship(back_populates="conversaciones")
    mensajes: Mapped[list["Mensaje"]] = relationship(
        back_populates="conversacion", cascade="all, delete-orphan"
    )
    diagnosticos: Mapped[list["Diagnostico"]] = relationship(back_populates="conversacion")

    __table_args__ = (
        CheckConstraint("canal IN ('whatsapp', 'api', 'web')", name="canal_valido"),
        CheckConstraint("estado IN ('abierta', 'cerrada', 'expirada')", name="estado_valido"),
        CheckConstraint("ultimo_mensaje_en >= iniciada_en", name="fechas_validas"),
    )


class Mensaje(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "mensajes"

    conversacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversaciones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    taller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("talleres.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    meta_message_id: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    direccion: Mapped[str] = mapped_column(String(10), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    categoria_cobro: Mapped[str] = mapped_column(
        String(20), nullable=False, default="servicio", server_default=text("'servicio'")
    )
    texto: Mapped[str | None] = mapped_column(Text)
    estado_entrega: Mapped[str] = mapped_column(
        String(20), nullable=False, default="recibido", server_default=text("'recibido'")
    )
    costo_estimado: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), nullable=False, default=Decimal("0"), server_default=text("0")
    )
    moneda: Mapped[str] = mapped_column(
        String(3), nullable=False, default="PEN", server_default=text("'PEN'")
    )
    ocurrido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Outbox durable para entregas Meta/Twilio. El destinatario nunca se guarda en texto plano.
    proveedor: Mapped[str | None] = mapped_column(String(20), index=True)
    destinatario_cifrado: Mapped[str | None] = mapped_column(Text)
    id_externo: Mapped[str | None] = mapped_column(String(150), index=True)
    intentos_entrega: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    disponible_entrega_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    bloqueado_entrega_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_entrega: Mapped[str | None] = mapped_column(Text)

    conversacion: Mapped["Conversacion"] = relationship(back_populates="mensajes")
    taller: Mapped["Taller"] = relationship()
    usuario: Mapped["Usuario | None"] = relationship(back_populates="mensajes")
    usos_api: Mapped[list["UsoApi"]] = relationship(back_populates="mensaje")

    __table_args__ = (
        CheckConstraint("direccion IN ('entrada', 'salida')", name="direccion_valida"),
        CheckConstraint("tipo IN ('texto', 'audio', 'imagen', 'documento', 'sistema')", name="tipo_valido"),
        CheckConstraint(
            "categoria_cobro IN ('servicio', 'utilidad', 'autenticacion', 'marketing')",
            name="categoria_cobro_valida",
        ),
        CheckConstraint(
            "estado_entrega IN ('recibido', 'pendiente', 'enviado', 'entregado', 'leido', 'fallido', 'pendiente_reintento')",
            name="estado_entrega_valido",
        ),
        CheckConstraint("costo_estimado >= 0", name="costo_no_negativo"),
        CheckConstraint("length(moneda) = 3", name="moneda_iso_4217"),
        CheckConstraint(
            "proveedor IS NULL OR proveedor IN ('meta', 'twilio', 'api')",
            name="mensaje_proveedor_valido",
        ),
        Index(
            "ix_mensajes_outbox_entrega",
            "direccion",
            "estado_entrega",
            "disponible_entrega_en",
            "bloqueado_entrega_hasta",
        ),
    )
