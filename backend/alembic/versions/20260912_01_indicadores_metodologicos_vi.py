"""Añadir indicadores metodológicos de VI, estado_registro y tiempo ML.

Revision ID: 20260912_01
Revises: 20260901_02
Create Date: 2026-09-12
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260912_01"
down_revision: Union[str, None] = "20260901_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Nuevas columnas para validaciones_taller
    op.add_column(
        "validaciones_taller",
        sa.Column(
            "estado_registro",
            sa.String(length=20),
            nullable=False,
            server_default="borrador",
        ),
    )
    op.create_check_constraint(
        "chk_validaciones_taller_estado_registro",
        "validaciones_taller",
        "estado_registro IN ('borrador', 'verificado', 'excluido')",
    )

    # Indicador 1: Síntomas registrados correctamente
    op.add_column(
        "validaciones_taller",
        sa.Column("sintoma_registrado_correctamente", sa.SmallInteger(), nullable=True),
    )
    op.add_column(
        "validaciones_taller",
        sa.Column(
            "validado_por_id",
            sa.Uuid(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "validaciones_taller",
        sa.Column("fecha_validacion", sa.DateTime(timezone=True), nullable=True),
    )

    # Indicador 2: Datos procesados correctamente (etapas verificadas)
    op.add_column(
        "validaciones_taller",
        sa.Column("normalizacion_correcta", sa.SmallInteger(), nullable=True),
    )
    op.add_column(
        "validaciones_taller",
        sa.Column("extraccion_correcta", sa.SmallInteger(), nullable=True),
    )
    op.add_column(
        "validaciones_taller",
        sa.Column("clasificacion_procesada", sa.SmallInteger(), nullable=True),
    )
    op.add_column(
        "validaciones_taller",
        sa.Column("procesamiento_validado", sa.SmallInteger(), nullable=True),
    )

    # Telemetría ML directa
    op.add_column(
        "validaciones_taller",
        sa.Column("tiempo_inferencia_ml_ms", sa.Integer(), nullable=True),
    )

    # 2. Nueva columna en diagnosticos para persistir tiempo de inferencia ML
    op.add_column(
        "diagnosticos",
        sa.Column("tiempo_inferencia_ml_ms", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("diagnosticos", "tiempo_inferencia_ml_ms")
    op.drop_column("validaciones_taller", "tiempo_inferencia_ml_ms")
    op.drop_column("validaciones_taller", "procesamiento_validado")
    op.drop_column("validaciones_taller", "clasificacion_procesada")
    op.drop_column("validaciones_taller", "extraccion_correcta")
    op.drop_column("validaciones_taller", "normalizacion_correcta")
    op.drop_column("validaciones_taller", "fecha_validacion")
    op.drop_column("validaciones_taller", "validado_por_id")
    op.drop_column("validaciones_taller", "sintoma_registrado_correctamente")
    op.drop_constraint(
        "chk_validaciones_taller_estado_registro",
        "validaciones_taller",
        type_="check",
    )
    op.drop_column("validaciones_taller", "estado_registro")
