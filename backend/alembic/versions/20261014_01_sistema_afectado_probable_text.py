"""Conservar íntegramente las etiquetas diagnósticas en la ficha automática.

Revision ID: 20261014_01
Revises: 20261010_01
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261014_01"
down_revision = "20261010_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "validaciones_taller",
        "sistema_afectado_probable",
        existing_type=sa.String(length=80),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    bind = op.get_bind()
    has_long_labels = bind.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM validaciones_taller "
            "WHERE length(sistema_afectado_probable) > 80)"
        )
    ).scalar_one()
    if has_long_labels:
        raise RuntimeError(
            "No se puede reducir sistema_afectado_probable a VARCHAR(80): "
            "hay etiquetas más largas y el downgrade perdería datos."
        )
    op.alter_column(
        "validaciones_taller",
        "sistema_afectado_probable",
        existing_type=sa.Text(),
        type_=sa.String(length=80),
        existing_nullable=True,
    )
