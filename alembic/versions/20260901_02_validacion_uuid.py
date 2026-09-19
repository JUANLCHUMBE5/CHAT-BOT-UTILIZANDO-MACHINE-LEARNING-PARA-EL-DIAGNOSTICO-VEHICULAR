"""Separar el UUID técnico del item histórico del tracker.

Revision ID: 20260901_02
Revises: 20260901_01
Create Date: 2026-09-01
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260901_02"
down_revision: Union[str, None] = "20260901_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("validaciones_taller", sa.Column("id", sa.Uuid(), nullable=True))
    op.add_column("validaciones_taller", sa.Column("origen_clave", sa.String(length=64), nullable=True))
    op.execute("UPDATE validaciones_taller SET id = gen_random_uuid() WHERE id IS NULL")
    op.alter_column("validaciones_taller", "id", nullable=False)
    op.drop_constraint(op.f("pk_validaciones_taller"), "validaciones_taller", type_="primary")
    op.create_primary_key(op.f("pk_validaciones_taller"), "validaciones_taller", ["id"])
    op.create_index("ix_validaciones_taller_item", "validaciones_taller", ["item"])
    op.create_unique_constraint(
        op.f("uq_validaciones_taller_origen_clave"),
        "validaciones_taller",
        ["origen_clave"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("uq_validaciones_taller_origen_clave"),
        "validaciones_taller",
        type_="unique",
    )
    op.drop_index("ix_validaciones_taller_item", table_name="validaciones_taller")
    op.drop_constraint(op.f("pk_validaciones_taller"), "validaciones_taller", type_="primary")
    op.create_primary_key(op.f("pk_validaciones_taller"), "validaciones_taller", ["item"])
    op.drop_column("validaciones_taller", "origen_clave")
    op.drop_column("validaciones_taller", "id")
