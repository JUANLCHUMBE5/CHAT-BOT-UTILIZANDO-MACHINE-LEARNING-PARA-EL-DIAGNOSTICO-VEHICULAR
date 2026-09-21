"""Separar síntesis LLM de las notas del mecánico.

Revision ID: 20260808_04
Revises: 20260808_03
Create Date: 2026-08-08
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260808_04"
down_revision: Union[str, None] = "20260808_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("diagnosticos", sa.Column("sintesis_llm", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("diagnosticos", "sintesis_llm")
