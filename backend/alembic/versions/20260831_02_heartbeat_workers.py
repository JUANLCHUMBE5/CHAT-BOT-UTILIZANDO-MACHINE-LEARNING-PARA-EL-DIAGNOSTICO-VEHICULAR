"""Agregar heartbeat durable de workers.

Revision ID: 20260831_02
Revises: 20260831_01
Create Date: 2026-08-31
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260831_02"
down_revision: Union[str, None] = "20260831_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workers_sistema",
        sa.Column("id", sa.String(length=100), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("iniciado_en", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("ultimo_heartbeat", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "estado IN ('activo', 'detenido')",
            name=op.f("ck_workers_sistema_worker_sistema_estado_valido"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workers_sistema")),
    )
    op.create_index("ix_workers_sistema_ultimo_heartbeat", "workers_sistema", ["ultimo_heartbeat"])


def downgrade() -> None:
    op.drop_index("ix_workers_sistema_ultimo_heartbeat", table_name="workers_sistema")
    op.drop_table("workers_sistema")
