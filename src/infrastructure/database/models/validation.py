"""Casos experimentales usados para validar el diagnóstico en taller."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
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
        Identity(start=1),
        nullable=False,
        index=True,
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
    descripcion_sintoma: Mapped[str | None] = mapped_column(Text)
    vehiculo_anio: Mapped[int | None] = mapped_column(Integer)
    vehiculo_kilometraje: Mapped[int | None] = mapped_column(Integer)
    vehiculo_combustible: Mapped[str | None] = mapped_column(String(30))
    vehiculo_transmision: Mapped[str | None] = mapped_column(String(30))
    falla_real: Mapped[str] = mapped_column(Text, nullable=False)
    chatbot_prediccion: Mapped[str] = mapped_column(Text, nullable=False)
    sistema_afectado_probable: Mapped[str | None] = mapped_column(String(80))
    campos_completos: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_campos_completos: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    detalles_campos: Mapped[dict | None] = mapped_column(JSON)
    tiempo_diagnostico_minutos: Mapped[int] = mapped_column(Integer, nullable=False)
    prediccion_correcta: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    metodo_confirmacion: Mapped[str | None] = mapped_column(String(500))
    evidencia_ref: Mapped[str | None] = mapped_column(String(500))
    estado_registro: Mapped[str] = mapped_column(
        String(20), nullable=False, default="borrador", server_default=text("'borrador'")
    )
    sintoma_registrado_correctamente: Mapped[int | None] = mapped_column(Integer)
    validado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    fecha_validacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    normalizacion_correcta: Mapped[int | None] = mapped_column(Integer)
    extraccion_correcta: Mapped[int | None] = mapped_column(Integer)
    clasificacion_procesada: Mapped[int | None] = mapped_column(Integer)
    procesamiento_validado: Mapped[int | None] = mapped_column(Integer)
    tiempo_inferencia_ml_ms: Mapped[int | None] = mapped_column(Integer)
    tipo_registro: Mapped[str] = mapped_column(
        String(30), nullable=False, default="THESIS_POSTTEST", server_default=text("'THESIS_POSTTEST'"), index=True
    )
    conversacion_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversaciones.id", ondelete="SET NULL"), index=True
    )
    diagnostico_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("diagnosticos.id", ondelete="SET NULL"), index=True
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("fase IN ('Pre-test', 'Post-test', 'Piloto')", name="fase_valida"),
        CheckConstraint("tipo_registro IN ('DEVELOPMENT', 'REGRESSION', 'THESIS_PRETEST', 'THESIS_POSTTEST')", name="chk_validaciones_tipo_registro"),
        CheckConstraint("campos_completos IN (0, 1)", name="campos_completos_binario"),
        CheckConstraint("cantidad_campos_completos BETWEEN 0 AND 8", name="chk_validaciones_cantidad_campos_0_8"),
        CheckConstraint("prediccion_correcta IN (0, 1)", name="prediccion_correcta_binaria"),
        CheckConstraint("estado_registro IN ('borrador', 'verificado', 'excluido')", name="chk_validaciones_taller_estado_registro"),
        CheckConstraint("vehiculo_anio IS NULL OR vehiculo_anio BETWEEN 1950 AND 2100", name="chk_validaciones_vehiculo_anio"),
        CheckConstraint("vehiculo_kilometraje IS NULL OR vehiculo_kilometraje >= 0", name="chk_validaciones_vehiculo_km"),
        CheckConstraint(
            "tiempo_diagnostico_minutos BETWEEN 1 AND 600",
            name="tiempo_diagnostico_valido",
        ),
        CheckConstraint("length(placa_hash) = 64", name="placa_hash_longitud"),
    )
