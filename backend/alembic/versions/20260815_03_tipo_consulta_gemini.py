"""Distinguir diagnósticos de consultas técnicas en la cola Gemini.

Revision ID: 20260815_03
Revises: 20260815_02
Create Date: 2026-08-15
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260815_03"
down_revision: Union[str, None] = "20260815_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "trabajos_gemini",
        sa.Column(
            "tipo_consulta",
            sa.String(length=30),
            nullable=False,
            server_default="diagnostico",
        ),
    )
    op.create_check_constraint(
        "trabajo_gemini_tipo_consulta_valido",
        "trabajos_gemini",
        "tipo_consulta IN ('diagnostico', 'consulta_tecnica')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "trabajo_gemini_tipo_consulta_valido",
        "trabajos_gemini",
        type_="check",
    )
    op.drop_column("trabajos_gemini", "tipo_consulta")
