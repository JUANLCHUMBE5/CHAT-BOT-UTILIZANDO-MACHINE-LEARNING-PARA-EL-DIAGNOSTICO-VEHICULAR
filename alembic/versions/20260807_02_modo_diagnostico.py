"""Añadir columna modo_diagnostico a la tabla de diagnosticos.

Revision ID: 20260807_02
Revises: 20260806_01
Create Date: 2026-08-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260807_02"
down_revision: Union[str, None] = "20260806_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "diagnosticos",
        sa.Column(
            "modo_diagnostico",
            sa.String(length=50),
            nullable=False,
            server_default="completo_ml_rag_llm",
        ),
    )
    op.create_check_constraint(
        "modo_diagnostico_valido",
        "diagnosticos",
        "modo_diagnostico IN ('completo_ml_rag_llm', 'diagnostico_degradado_ml_rag', 'en_cola_gemini', 'audio_espectral', 'saludo', 'baja_confianza', 'esperando_clarificacion')",
    )


def downgrade() -> None:
    op.drop_constraint("modo_diagnostico_valido", "diagnosticos", type_="check")
    op.drop_column("diagnosticos", "modo_diagnostico")
