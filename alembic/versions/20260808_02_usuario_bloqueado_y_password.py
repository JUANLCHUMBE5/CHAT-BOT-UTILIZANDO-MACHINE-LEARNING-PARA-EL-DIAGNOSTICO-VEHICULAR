"""Añadir columnas password_hash y bloqueado a la tabla usuarios.

Revision ID: 20260808_02
Revises: 20260807_03
Create Date: 2026-08-08
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260808_02"
down_revision: Union[str, None] = "20260808_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column("password_hash", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "usuarios",
        sa.Column("bloqueado", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("usuarios", "bloqueado")
    op.drop_column("usuarios", "password_hash")
