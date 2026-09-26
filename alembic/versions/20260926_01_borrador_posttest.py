"""Permite borradores POST sin inventar confirmación ni tiempo humano.

Revision ID: 20260926_01
Revises: 20260919_04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260926_01"
down_revision: Union[str, None] = "20260919_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("validaciones_taller", "falla_real", existing_type=sa.Text(), nullable=True)
    op.alter_column("validaciones_taller", "tiempo_diagnostico_minutos", existing_type=sa.Integer(), nullable=True)
    op.alter_column("validaciones_taller", "prediccion_correcta", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    # Un borrador sin confirmación debe resolverse o eliminarse antes de revertir.
    op.alter_column("validaciones_taller", "prediccion_correcta", existing_type=sa.Integer(), nullable=False)
    op.alter_column("validaciones_taller", "tiempo_diagnostico_minutos", existing_type=sa.Integer(), nullable=False)
    op.alter_column("validaciones_taller", "falla_real", existing_type=sa.Text(), nullable=False)
