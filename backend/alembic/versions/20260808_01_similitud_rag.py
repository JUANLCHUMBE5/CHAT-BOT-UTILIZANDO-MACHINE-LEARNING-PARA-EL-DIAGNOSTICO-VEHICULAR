"""Separar la similitud RAG de la confianza del modelo ML.

Revision ID: 20260808_01
Revises: 20260807_06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260808_01"
down_revision = "20260807_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "diagnosticos",
        sa.Column("similitud_rag", sa.Numeric(5, 4), nullable=True),
    )
    op.create_check_constraint(
        "similitud_rag_rango",
        "diagnosticos",
        "similitud_rag IS NULL OR similitud_rag BETWEEN 0 AND 1",
    )


def downgrade() -> None:
    op.drop_constraint("similitud_rag_rango", "diagnosticos", type_="check")
    op.drop_column("diagnosticos", "similitud_rag")
