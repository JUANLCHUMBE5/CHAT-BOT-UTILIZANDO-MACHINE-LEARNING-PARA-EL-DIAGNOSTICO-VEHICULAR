"""Casos experimentales usados para validar el diagnóstico en taller."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.base import Base, UUIDPrimaryKeyMixin


class ValidacionTaller(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "validaciones_taller"

    item: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        server_default=text("nextval('validaciones_taller_item_seq'::regclass)"),
    )
    origen_clave: Mapped[str | None] = mapped_column(String(64), unique=True)
    taller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("talleres.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    mecanico_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    fase: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    placa_enmascarada: Mapped[str] = mapped_column(String(15), nullable=False)
    placa_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    marca_modelo: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sintoma: Mapped[str] = mapped_column(Text, nullable=False)
    falla_real: Mapped[str] = mapped_column(Text, nullable=False)
    chatbot_prediccion: Mapped[str] = mapped_column(Text, nullable=False)
    campos_completos: Mapped[int] = mapped_column(Integer, nullable=False)
    tiempo_diagnostico_minutos: Mapped[int] = mapped_column(Integer, nullable=False)
    prediccion_correcta: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    metodo_confirmacion: Mapped[str | None] = mapped_column(String(500))
    evidencia_ref: Mapped[str | None] = mapped_column(String(500))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("fase IN ('Pre-test', 'Post-test', 'Piloto')", name="fase_valida"),
        CheckConstraint("campos_completos IN (0, 1)", name="campos_completos_binario"),
        CheckConstraint("prediccion_correcta IN (0, 1)", name="prediccion_correcta_binaria"),
        CheckConstraint(
            "tiempo_diagnostico_minutos BETWEEN 1 AND 600",
            name="tiempo_diagnostico_valido",
        ),
        CheckConstraint("length(placa_hash) = 64", name="placa_hash_longitud"),
    )
