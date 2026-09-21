"""Separación estricta de fases de investigación (Tesis) y trazabilidad completa.

Revision ID: 20260919_01
Revises: 20260912_01
Create Date: 2026-09-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260919_01"
down_revision: Union[str, None] = "20260912_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Nuevas columnas y restricciones en validaciones_taller
    op.add_column(
        "validaciones_taller",
        sa.Column(
            "tipo_registro",
            sa.String(length=30),
            nullable=False,
            server_default="THESIS_POSTTEST",
        ),
    )
    op.create_check_constraint(
        "chk_validaciones_tipo_registro",
        "validaciones_taller",
        "tipo_registro IN ('DEVELOPMENT', 'REGRESSION', 'THESIS_PRETEST', 'THESIS_POSTTEST')",
    )
    op.add_column(
        "validaciones_taller",
        sa.Column(
            "conversacion_id",
            sa.Uuid(),
            sa.ForeignKey("conversaciones.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "validaciones_taller",
        sa.Column(
            "diagnostico_id",
            sa.Uuid(),
            sa.ForeignKey("diagnosticos.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_validaciones_taller_tipo_registro"),
        "validaciones_taller",
        ["tipo_registro"],
        unique=False,
    )
    op.create_index(
        op.f("ix_validaciones_taller_conversacion_id"),
        "validaciones_taller",
        ["conversacion_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_validaciones_taller_diagnostico_id"),
        "validaciones_taller",
        ["diagnostico_id"],
        unique=False,
    )

    # 2. Nueva columna en diagnosticos para aislar desarrollo de registros oficiales
    op.add_column(
        "diagnosticos",
        sa.Column(
            "tipo_registro",
            sa.String(length=30),
            nullable=False,
            server_default="DEVELOPMENT",
        ),
    )
    op.create_check_constraint(
        "chk_diagnosticos_tipo_registro",
        "diagnosticos",
        "tipo_registro IN ('DEVELOPMENT', 'REGRESSION', 'THESIS_PRETEST', 'THESIS_POSTTEST')",
    )
    op.create_index(
        op.f("ix_diagnosticos_tipo_registro"),
        "diagnosticos",
        ["tipo_registro"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_diagnosticos_tipo_registro"), table_name="diagnosticos")
    op.drop_constraint("chk_diagnosticos_tipo_registro", "diagnosticos", type_="check")
    op.drop_column("diagnosticos", "tipo_registro")

    op.drop_index(op.f("ix_validaciones_taller_diagnostico_id"), table_name="validaciones_taller")
    op.drop_index(op.f("ix_validaciones_taller_conversacion_id"), table_name="validaciones_taller")
    op.drop_index(op.f("ix_validaciones_taller_tipo_registro"), table_name="validaciones_taller")
    op.drop_constraint("chk_validaciones_tipo_registro", "validaciones_taller", type_="check")
    op.drop_column("validaciones_taller", "diagnostico_id")
    op.drop_column("validaciones_taller", "conversacion_id")
    op.drop_column("validaciones_taller", "tipo_registro")
