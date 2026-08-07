"""Agrega outbox durable para mensajes Meta y Twilio.

Revision ID: 20260807_05
Revises: 20260807_04
"""

import sqlalchemy as sa
from alembic import op


revision = "20260807_05"
down_revision = "20260807_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("mensajes", sa.Column("proveedor", sa.String(20), nullable=True))
    op.add_column("mensajes", sa.Column("destinatario_cifrado", sa.Text(), nullable=True))
    op.add_column("mensajes", sa.Column("id_externo", sa.String(150), nullable=True))
    op.add_column("mensajes", sa.Column("intentos_entrega", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("mensajes", sa.Column("disponible_entrega_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column("mensajes", sa.Column("bloqueado_entrega_hasta", sa.DateTime(timezone=True), nullable=True))
    op.add_column("mensajes", sa.Column("error_entrega", sa.Text(), nullable=True))
    op.create_check_constraint(
        "mensaje_proveedor_valido", "mensajes",
        "proveedor IS NULL OR proveedor IN ('meta', 'twilio', 'api')",
    )
    op.create_index("ix_mensajes_proveedor", "mensajes", ["proveedor"])
    op.create_index("ix_mensajes_id_externo", "mensajes", ["id_externo"])
    op.create_index(
        "ix_mensajes_outbox_entrega", "mensajes",
        ["direccion", "estado_entrega", "disponible_entrega_en", "bloqueado_entrega_hasta"],
    )
    op.drop_constraint("proveedor_valido", "uso_api", type_="check")
    op.create_check_constraint(
        "proveedor_valido", "uso_api",
        "proveedor IN ('meta', 'twilio', 'google', 'aws', 'local')",
    )


def downgrade() -> None:
    op.drop_constraint("proveedor_valido", "uso_api", type_="check")
    op.create_check_constraint(
        "proveedor_valido", "uso_api",
        "proveedor IN ('meta', 'google', 'aws', 'local')",
    )
    op.drop_index("ix_mensajes_outbox_entrega", table_name="mensajes")
    op.drop_index("ix_mensajes_id_externo", table_name="mensajes")
    op.drop_index("ix_mensajes_proveedor", table_name="mensajes")
    op.drop_constraint("mensaje_proveedor_valido", "mensajes", type_="check")
    for columna in (
        "error_entrega", "bloqueado_entrega_hasta", "disponible_entrega_en",
        "intentos_entrega", "id_externo", "destinatario_cifrado", "proveedor",
    ):
        op.drop_column("mensajes", columna)
