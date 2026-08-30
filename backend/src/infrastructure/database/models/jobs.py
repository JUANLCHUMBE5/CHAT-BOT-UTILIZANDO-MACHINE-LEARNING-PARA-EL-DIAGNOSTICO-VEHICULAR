"""Modelo ORM para la cola de trabajos persistente de Gemini y sincronización de cuotas."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.catalogs import Taller, Usuario
    from src.infrastructure.database.models.diagnostics import Diagnostico
    from src.infrastructure.database.models.messaging import Conversacion


class CuotaGeminiGlobal(Base):
    """Tabla para sincronización atómica de RPM y RPD entre múltiples procesos / servidores."""

    __tablename__ = "cuotas_gemini_global"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    fecha: Mapped[datetime] = mapped_column(
        Date, nullable=False, server_default=text("CURRENT_DATE")
    )
    solicitudes_hoy: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    solicitudes_minuto: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    minuto_epoch: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default=text("0")
    )
    cooldown_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ultima_verificacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ultimo_exito: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ultimo_codigo_http: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    ultimo_error: Mapped[str | None] = mapped_column(String(300), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )


class TrabajoGemini(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Modelo ORM para trabajos encolados de Gemini en PostgreSQL con privacidad estricta."""

    __tablename__ = "trabajos_gemini"

    diagnostico_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("diagnosticos.id", ondelete="SET NULL"), nullable=True, index=True
    )
    taller_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("talleres.id", ondelete="SET NULL"), nullable=True, index=True
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    conversacion_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversaciones.id", ondelete="SET NULL"), nullable=True, index=True
    )

    proveedor: Mapped[str] = mapped_column(
        String(20), nullable=False, default="meta", server_default=text("'meta'")
    )
    tipo_consulta: Mapped[str] = mapped_column(
        String(30), nullable=False, default="diagnostico", server_default=text("'diagnostico'")
    )
    remitente_cifrado: Mapped[str | None] = mapped_column(Text, nullable=True)

    sintoma: Mapped[str] = mapped_column(Text, nullable=False)
    diagnostico_ml: Mapped[str] = mapped_column(String(200), nullable=False)
    confianza_ml: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    contexto_manual: Mapped[str | None] = mapped_column(Text, nullable=True)
    titulo_manual: Mapped[str | None] = mapped_column(String(200), nullable=True)
    requiere_revision_humana: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )

    estado: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pendiente", server_default=text("'pendiente'")
    )
    intentos: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    disponible_desde: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_ultimo: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones relacionales
    diagnostico: Mapped["Diagnostico | None"] = relationship()
    taller: Mapped["Taller | None"] = relationship()
    usuario: Mapped["Usuario | None"] = relationship()
    conversacion: Mapped["Conversacion | None"] = relationship()

    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente', 'procesando', 'completado', 'pendiente_reintento', 'fallido')",
            name="trabajo_gemini_estado_valido",
        ),
        CheckConstraint(
            "proveedor IN ('meta', 'twilio', 'api')",
            name="trabajo_gemini_proveedor_valido",
        ),
        CheckConstraint(
            "tipo_consulta IN ('diagnostico', 'consulta_tecnica')",
            name="trabajo_gemini_tipo_consulta_valido",
        ),
        Index("ix_trabajos_gemini_estado_disponible", "estado", "disponible_desde", "bloqueado_hasta"),
    )
