"""Agregar cambio obligatorio de contraseña a usuarios.

Revision ID: 20260808_03
Revises: 20260808_02
Create Date: 2026-08-08
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260808_03"
down_revision: Union[str, None] = "20260808_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column(
            "debe_cambiar_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.execute(
        """
        UPDATE hipotesis_diagnostico
        SET evidencia = 'Fuente: No documentada. ' || COALESCE(evidencia, '')
        WHERE evidencia IS NULL OR evidencia NOT LIKE '%Fuente:%'
        """
    )


def downgrade() -> None:
    op.drop_column("usuarios", "debe_cambiar_password")
