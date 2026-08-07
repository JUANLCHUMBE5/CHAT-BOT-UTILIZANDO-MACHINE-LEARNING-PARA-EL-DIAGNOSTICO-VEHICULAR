"""Entidades del proceso de diagnóstico vehicular."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.infrastructure.database.models.catalogs import Taller, Usuario
    from src.infrastructure.database.models.messaging import Conversacion
    from src.infrastructure.database.models.operations import UsoApi


class Vehiculo(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vehiculos"

    taller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("talleres.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    registrado_por_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    placa_hash: Mapped[str | None] = mapped_column(String(64))
    placa_ultimos4: Mapped[str | None] = mapped_column(String(4))
    marca: Mapped[str] = mapped_column(String(80), nullable=False)
    modelo: Mapped[str] = mapped_column(String(100), nullable=False)
    anio: Mapped[int | None] = mapped_column(SmallInteger)
    motor: Mapped[str | None] = mapped_column(String(100))
    combustible: Mapped[str | None] = mapped_column(String(30))
    kilometraje: Mapped[int | None] = mapped_column(Integer)

    taller: Mapped["Taller"] = relationship(back_populates="vehiculos")
    registrado_por: Mapped["Usuario"] = relationship(back_populates="vehiculos_registrados")
    diagnosticos: Mapped[list["Diagnostico"]] = relationship(back_populates="vehiculo")

    __table_args__ = (
        CheckConstraint("anio IS NULL OR anio BETWEEN 1886 AND 2200", name="anio_valido"),
        CheckConstraint("kilometraje IS NULL OR kilometraje >= 0", name="kilometraje_no_negativo"),
        CheckConstraint("placa_hash IS NULL OR length(placa_hash) = 64", name="placa_hash_longitud"),
        UniqueConstraint("taller_id", "placa_hash", name="uq_vehiculos_taller_placa_hash"),
    )


class Diagnostico(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "diagnosticos"

    taller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("talleres.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    mecanico_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    vehiculo_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vehiculos.id", ondelete="SET NULL"), index=True
    )
    conversacion_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversaciones.id", ondelete="SET NULL"), index=True
    )
    sintoma_original: Mapped[str] = mapped_column(Text, nullable=False)
    sintoma_normalizado: Mapped[str | None] = mapped_column(Text)
    falla_predicha: Mapped[str | None] = mapped_column(String(200))
    confianza: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    fuente: Mapped[str] = mapped_column(String(20), nullable=False)
    modo_diagnostico: Mapped[str] = mapped_column(
        String(50), nullable=False, default="completo_ml_rag_llm", server_default=text("'completo_ml_rag_llm'")
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="generado", server_default=text("'generado'")
    )
    duracion_ms: Mapped[int | None] = mapped_column(Integer)
    conclusion_mecanico: Mapped[str | None] = mapped_column(Text)
    version_modelo_ml: Mapped[str | None] = mapped_column(String(80))
    version_corpus_rag: Mapped[str | None] = mapped_column(String(80))

    taller: Mapped["Taller"] = relationship(back_populates="diagnosticos")
    mecanico: Mapped["Usuario"] = relationship(back_populates="diagnosticos")
    vehiculo: Mapped["Vehiculo | None"] = relationship(back_populates="diagnosticos")
    conversacion: Mapped["Conversacion | None"] = relationship(back_populates="diagnosticos")
    hipotesis: Mapped[list["HipotesisDiagnostico"]] = relationship(
        back_populates="diagnostico", cascade="all, delete-orphan"
    )
    usos_api: Mapped[list["UsoApi"]] = relationship(back_populates="diagnostico")

    __table_args__ = (
        CheckConstraint("confianza IS NULL OR confianza BETWEEN 0 AND 1", name="confianza_rango"),
        CheckConstraint("duracion_ms IS NULL OR duracion_ms >= 0", name="duracion_no_negativa"),
        CheckConstraint("fuente IN ('ml', 'rag', 'gemini', 'hibrido', 'manual', 'regla')", name="fuente_valida"),
        CheckConstraint(
            "estado IN ('generado', 'en_revision', 'confirmado', 'descartado')",
            name="estado_valido",
        ),
        CheckConstraint(
            "modo_diagnostico IN ('completo_ml_rag_llm', 'diagnostico_degradado_ml_rag', 'en_cola_gemini', 'audio_espectral', 'saludo', 'baja_confianza', 'esperando_clarificacion')",
            name="modo_diagnostico_valido",
        ),
    )


class HipotesisDiagnostico(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "hipotesis_diagnostico"

    diagnostico_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("diagnosticos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    orden: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    falla_probable: Mapped[str] = mapped_column(String(200), nullable=False)
    confianza: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    evidencia: Mapped[str | None] = mapped_column(Text)
    prueba_recomendada: Mapped[str | None] = mapped_column(Text)
    resultado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pendiente", server_default=text("'pendiente'")
    )

    diagnostico: Mapped["Diagnostico"] = relationship(back_populates="hipotesis")

    __table_args__ = (
        CheckConstraint("orden > 0", name="orden_positivo"),
        CheckConstraint("confianza IS NULL OR confianza BETWEEN 0 AND 1", name="confianza_rango"),
        CheckConstraint(
            "resultado IN ('pendiente', 'confirmada', 'descartada')", name="resultado_valido"
        ),
        UniqueConstraint("diagnostico_id", "orden", name="uq_hipotesis_diagnostico_orden"),
    )
