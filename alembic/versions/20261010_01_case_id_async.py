"""Vincula trabajos y salidas asíncronas con el caso diagnóstico activo.

Revision ID: 20261010_01
Revises: 20260926_01
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20261010_01"
down_revision: Union[str, None] = "20260926_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "trabajos_gemini",
        sa.Column("case_id", sa.Uuid(as_uuid=False), nullable=True),
    )
    op.create_index("ix_trabajos_gemini_case_id", "trabajos_gemini", ["case_id"])
    op.add_column("mensajes", sa.Column("case_id", sa.Uuid(as_uuid=False), nullable=True))
    op.create_index("ix_mensajes_case_id", "mensajes", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_mensajes_case_id", table_name="mensajes")
    op.drop_column("mensajes", "case_id")
    op.drop_index("ix_trabajos_gemini_case_id", table_name="trabajos_gemini")
    op.drop_column("trabajos_gemini", "case_id")
