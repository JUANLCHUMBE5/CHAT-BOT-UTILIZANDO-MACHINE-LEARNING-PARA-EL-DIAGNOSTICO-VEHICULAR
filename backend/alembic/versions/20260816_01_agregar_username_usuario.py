"""Agregar columna username a la tabla usuarios.

Revision ID: 20260816_01
Revises: 20260815_04
Create Date: 2026-08-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260816_01"
down_revision: Union[str, None] = "20260815_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column(
            "username",
            sa.String(length=60),
            nullable=True,
        ),
    )
    op.create_index("ix_usuarios_username", "usuarios", ["username"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_usuarios_username", table_name="usuarios")
    op.drop_column("usuarios", "username")
