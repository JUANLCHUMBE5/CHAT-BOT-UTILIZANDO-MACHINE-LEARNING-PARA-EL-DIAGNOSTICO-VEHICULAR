"""Trazabilidad de consumo externo y auditoría operativa."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, JSON, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.catalogs import Taller, Usuario
    from src.infrastructure.database.models.diagnostics import Diagnostico
    from src.infrastructure.database.models.messaging import Mensaje


JSONType = JSON().with_variant(JSONB(), "postgresql")


class UsoApi(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "uso_api"

    taller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("talleres.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    diagnostico_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("diagnosticos.id", ondelete="SET NULL"), index=True
    )
    mensaje_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("mensajes.id", ondelete="SET NULL"), index=True
    )
    proveedor: Mapped[str] = mapped_column(String(30), nullable=False)
    operacion: Mapped[str] = mapped_column(String(50), nullable=False)
    modelo: Mapped[str | None] = mapped_column(String(80))
    solicitud_externa_id: Mapped[str | None] = mapped_column(String(150), index=True)
    tokens_entrada: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    tokens_salida: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    unidades: Mapped[Decimal] = mapped_column(
        Numeric(14, 4), nullable=False, default=Decimal("0"), server_default=text("0")
    )
    costo_estimado: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), nullable=False, default=Decimal("0"), server_default=text("0")
    )
    moneda: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", server_default=text("'USD'")
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    taller: Mapped["Taller"] = relationship()
    diagnostico: Mapped["Diagnostico | None"] = relationship(back_populates="usos_api")
    mensaje: Mapped["Mensaje | None"] = relationship(back_populates="usos_api")

    __table_args__ = (
        CheckConstraint("proveedor IN ('meta', 'twilio', 'google', 'aws', 'local')", name="proveedor_valido"),
        CheckConstraint("tokens_entrada >= 0 AND tokens_salida >= 0", name="tokens_no_negativos"),
        CheckConstraint("unidades >= 0", name="unidades_no_negativas"),
        CheckConstraint("costo_estimado >= 0", name="costo_no_negativo"),
        CheckConstraint("length(moneda) = 3", name="moneda_iso_4217"),
    )


class Auditoria(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "auditoria"

    taller_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("talleres.id", ondelete="SET NULL"), index=True
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    accion: Mapped[str] = mapped_column(String(80), nullable=False)
    entidad: Mapped[str] = mapped_column(String(80), nullable=False)
    entidad_id: Mapped[uuid.UUID | None]
    detalles: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)
    ip_hash: Mapped[str | None] = mapped_column(String(64))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    taller: Mapped["Taller | None"] = relationship()
    usuario: Mapped["Usuario | None"] = relationship()

    __table_args__ = (
        CheckConstraint("ip_hash IS NULL OR length(ip_hash) = 64", name="ip_hash_longitud"),
    )
