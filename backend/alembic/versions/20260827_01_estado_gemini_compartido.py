"""Agregar estado y cooldown compartido de Gemini.

Revision ID: 20260827_01
Revises: 20260816_01
Create Date: 2026-08-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260827_01"
down_revision: Union[str, None] = "20260816_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cuotas_gemini_global",
        sa.Column("cooldown_hasta", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "cuotas_gemini_global",
        sa.Column("ultima_verificacion", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "cuotas_gemini_global",
        sa.Column("ultimo_exito", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "cuotas_gemini_global",
        sa.Column("ultimo_codigo_http", sa.SmallInteger(), nullable=True),
    )
    op.add_column(
        "cuotas_gemini_global",
        sa.Column("ultimo_error", sa.String(length=300), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cuotas_gemini_global", "ultimo_error")
    op.drop_column("cuotas_gemini_global", "ultimo_codigo_http")
    op.drop_column("cuotas_gemini_global", "ultimo_exito")
    op.drop_column("cuotas_gemini_global", "ultima_verificacion")
    op.drop_column("cuotas_gemini_global", "cooldown_hasta")
