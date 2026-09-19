"""Agregar trazabilidad auditable de Ficha 2 para los 8 campos obligatorios.

Revision ID: 20260919_02
Revises: 20260919_01
Create Date: 2026-09-19
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260919_02"
down_revision = "20260919_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("validaciones_taller", sa.Column("sistema_afectado_probable", sa.String(length=80), nullable=True))
    op.add_column(
        "validaciones_taller",
        sa.Column("cantidad_campos_completos", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("validaciones_taller", sa.Column("detalles_campos", sa.JSON(), nullable=True))
    op.create_check_constraint(
        "chk_validaciones_cantidad_campos_0_8",
        "validaciones_taller",
        "cantidad_campos_completos BETWEEN 0 AND 8",
    )


def downgrade() -> None:
    op.drop_constraint("chk_validaciones_cantidad_campos_0_8", "validaciones_taller", type_="check")
    op.drop_column("validaciones_taller", "detalles_campos")
    op.drop_column("validaciones_taller", "cantidad_campos_completos")
    op.drop_column("validaciones_taller", "sistema_afectado_probable")
