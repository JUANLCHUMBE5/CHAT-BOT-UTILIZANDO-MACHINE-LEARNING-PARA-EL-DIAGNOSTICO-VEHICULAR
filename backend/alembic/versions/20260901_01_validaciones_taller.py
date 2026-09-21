"""Persistir el tracker experimental en PostgreSQL.

Revision ID: 20260901_01
Revises: 20260831_02
Create Date: 2026-09-01
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260901_01"
down_revision: Union[str, None] = "20260831_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "validaciones_taller",
        sa.Column("item", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("taller_id", sa.Uuid(), nullable=False),
        sa.Column("mecanico_id", sa.Uuid(), nullable=True),
        sa.Column("fase", sa.String(length=20), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("placa_enmascarada", sa.String(length=15), nullable=False),
        sa.Column("placa_hash", sa.String(length=64), nullable=False),
        sa.Column("marca_modelo", sa.String(length=100), nullable=False),
        sa.Column("sintoma", sa.Text(), nullable=False),
        sa.Column("falla_real", sa.Text(), nullable=False),
        sa.Column("chatbot_prediccion", sa.Text(), nullable=False),
        sa.Column("campos_completos", sa.Integer(), nullable=False),
        sa.Column("tiempo_diagnostico_minutos", sa.Integer(), nullable=False),
        sa.Column("prediccion_correcta", sa.Integer(), nullable=False),
        sa.Column("metodo_confirmacion", sa.String(length=500), nullable=True),
        sa.Column("evidencia_ref", sa.String(length=500), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "campos_completos IN (0, 1)",
            name=op.f("ck_validaciones_taller_campos_completos_binario"),
        ),
        sa.CheckConstraint(
            "fase IN ('Pre-test', 'Post-test', 'Piloto')",
            name=op.f("ck_validaciones_taller_fase_valida"),
        ),
        sa.CheckConstraint(
            "length(placa_hash) = 64",
            name=op.f("ck_validaciones_taller_placa_hash_longitud"),
        ),
        sa.CheckConstraint(
            "prediccion_correcta IN (0, 1)",
            name=op.f("ck_validaciones_taller_prediccion_correcta_binaria"),
        ),
        sa.CheckConstraint(
            "tiempo_diagnostico_minutos BETWEEN 1 AND 600",
            name=op.f("ck_validaciones_taller_tiempo_diagnostico_valido"),
        ),
        sa.ForeignKeyConstraint(
            ["mecanico_id"],
            ["usuarios.id"],
            name=op.f("fk_validaciones_taller_mecanico_id_usuarios"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["taller_id"],
            ["talleres.id"],
            name=op.f("fk_validaciones_taller_taller_id_talleres"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("item", name=op.f("pk_validaciones_taller")),
    )
    op.create_index("ix_validaciones_taller_fecha", "validaciones_taller", ["fecha"])
    op.create_index("ix_validaciones_taller_fase", "validaciones_taller", ["fase"])
    op.create_index("ix_validaciones_taller_marca_modelo", "validaciones_taller", ["marca_modelo"])
    op.create_index("ix_validaciones_taller_mecanico_id", "validaciones_taller", ["mecanico_id"])
    op.create_index("ix_validaciones_taller_placa_hash", "validaciones_taller", ["placa_hash"])
    op.create_index(
        "ix_validaciones_taller_prediccion_correcta",
        "validaciones_taller",
        ["prediccion_correcta"],
    )
    op.create_index("ix_validaciones_taller_taller_id", "validaciones_taller", ["taller_id"])


def downgrade() -> None:
    op.drop_index("ix_validaciones_taller_taller_id", table_name="validaciones_taller")
    op.drop_index("ix_validaciones_taller_prediccion_correcta", table_name="validaciones_taller")
    op.drop_index("ix_validaciones_taller_placa_hash", table_name="validaciones_taller")
    op.drop_index("ix_validaciones_taller_mecanico_id", table_name="validaciones_taller")
    op.drop_index("ix_validaciones_taller_marca_modelo", table_name="validaciones_taller")
    op.drop_index("ix_validaciones_taller_fase", table_name="validaciones_taller")
    op.drop_index("ix_validaciones_taller_fecha", table_name="validaciones_taller")
    op.drop_table("validaciones_taller")
