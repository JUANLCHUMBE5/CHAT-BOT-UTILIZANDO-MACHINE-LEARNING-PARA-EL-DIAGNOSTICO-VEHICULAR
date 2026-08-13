"""Registra versiones reproducibles de ML y corpus RAG.

Revision ID: 20260807_06
Revises: 20260807_05
"""

import sqlalchemy as sa
from alembic import op

revision = "20260807_06"
down_revision = "20260807_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("diagnosticos", sa.Column("version_modelo_ml", sa.String(80), nullable=True))
    op.add_column("diagnosticos", sa.Column("version_corpus_rag", sa.String(80), nullable=True))


def downgrade() -> None:
    op.drop_column("diagnosticos", "version_corpus_rag")
    op.drop_column("diagnosticos", "version_modelo_ml")
