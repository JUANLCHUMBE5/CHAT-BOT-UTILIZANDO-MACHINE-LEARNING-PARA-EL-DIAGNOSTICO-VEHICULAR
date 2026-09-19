"""Agregar cola durable general de trabajos del sistema.

Revision ID: 20260831_01
Revises: 20260827_01
Create Date: 2026-08-31
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260831_01"
down_revision: Union[str, None] = "20260827_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trabajos_sistema",
        sa.Column("taller_id", sa.Uuid(), nullable=True),
        sa.Column("tipo", sa.String(length=40), nullable=False),
        sa.Column("cola", sa.String(length=30), nullable=False),
        sa.Column("prioridad", sa.SmallInteger(), server_default=sa.text("50"), nullable=False),
        sa.Column("clave_idempotencia", sa.String(length=180), nullable=True),
        sa.Column("payload_cifrado", sa.Text(), nullable=False),
        sa.Column("resultado_resumen", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(length=30), server_default=sa.text("'pendiente'"), nullable=False),
        sa.Column("intentos", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("max_intentos", sa.Integer(), server_default=sa.text("4"), nullable=False),
        sa.Column("disponible_desde", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("worker_id", sa.String(length=100), nullable=True),
        sa.Column("iniciado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_ultimo", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "estado IN ('pendiente', 'procesando', 'completado', 'pendiente_reintento', 'fallido', 'cancelado')",
            name=op.f("ck_trabajos_sistema_trabajo_sistema_estado_valido"),
        ),
        sa.CheckConstraint(
            "prioridad BETWEEN 0 AND 100",
            name=op.f("ck_trabajos_sistema_trabajo_sistema_prioridad_valida"),
        ),
        sa.CheckConstraint(
            "max_intentos BETWEEN 1 AND 20",
            name=op.f("ck_trabajos_sistema_trabajo_sistema_max_intentos_valido"),
        ),
        sa.ForeignKeyConstraint(
            ["taller_id"], ["talleres.id"], name=op.f("fk_trabajos_sistema_taller_id_talleres"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trabajos_sistema")),
        sa.UniqueConstraint("clave_idempotencia", name=op.f("uq_trabajos_sistema_clave_idempotencia")),
    )
    op.create_index(op.f("ix_trabajos_sistema_taller_id"), "trabajos_sistema", ["taller_id"])
    op.create_index(
        "ix_trabajos_sistema_cola_estado_disponible",
        "trabajos_sistema",
        ["cola", "estado", "disponible_desde", "prioridad"],
    )


def downgrade() -> None:
    op.drop_index("ix_trabajos_sistema_cola_estado_disponible", table_name="trabajos_sistema")
    op.drop_index(op.f("ix_trabajos_sistema_taller_id"), table_name="trabajos_sistema")
    op.drop_table("trabajos_sistema")
