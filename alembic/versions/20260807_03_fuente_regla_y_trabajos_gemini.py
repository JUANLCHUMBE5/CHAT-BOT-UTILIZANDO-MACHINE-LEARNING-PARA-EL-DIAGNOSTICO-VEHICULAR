"""Permitir fuente regla en diagnosticos, estado_entrega pendiente_reintento, crear tabla trabajos_gemini y cuotas_gemini_global.

Revision ID: 20260807_03
Revises: 20260807_02
Create Date: 2026-08-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260807_03"
down_revision: Union[str, None] = "20260807_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Actualizar CheckConstraint fuente_valida en tabla diagnosticos
    op.drop_constraint("fuente_valida", "diagnosticos", type_="check")
    op.create_check_constraint(
        "fuente_valida",
        "diagnosticos",
        "fuente IN ('ml', 'rag', 'gemini', 'hibrido', 'manual', 'regla')",
    )

    # 2. Actualizar CheckConstraint estado_entrega_valido en tabla mensajes
    op.drop_constraint("estado_entrega_valido", "mensajes", type_="check")
    op.create_check_constraint(
        "estado_entrega_valido",
        "mensajes",
        "estado_entrega IN ('recibido', 'pendiente', 'enviado', 'entregado', 'leido', 'fallido', 'pendiente_reintento')",
    )

    # 3. Crear tabla cuotas_gemini_global para sincronización de RPM y RPD multi-proceso / multi-instancia
    op.create_table(
        "cuotas_gemini_global",
        sa.Column("id", sa.SmallInteger(), primary_key=True, default=1),
        sa.Column("fecha", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("solicitudes_hoy", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("solicitudes_minuto", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("minuto_epoch", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # 4. Crear tabla trabajos_gemini para la cola persistente con remitente cifrado (privacidad estricta)
    op.create_table(
        "trabajos_gemini",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("diagnostico_id", sa.UUID(), sa.ForeignKey("diagnosticos.id", ondelete="SET NULL"), nullable=True),
        sa.Column("taller_id", sa.UUID(), sa.ForeignKey("talleres.id", ondelete="SET NULL"), nullable=True),
        sa.Column("usuario_id", sa.UUID(), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("conversacion_id", sa.UUID(), sa.ForeignKey("conversaciones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("proveedor", sa.String(length=20), nullable=False, server_default="meta"),
        sa.Column("remitente_cifrado", sa.Text(), nullable=True),
        sa.Column("sintoma", sa.Text(), nullable=False),
        sa.Column("diagnostico_ml", sa.String(length=200), nullable=False),
        sa.Column("confianza_ml", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("contexto_manual", sa.Text(), nullable=True),
        sa.Column("titulo_manual", sa.String(length=200), nullable=True),
        sa.Column("requiere_revision_humana", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="pendiente"),
        sa.Column("intentos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("disponible_desde", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_ultimo", sa.Text(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("estado IN ('pendiente', 'procesando', 'completado', 'pendiente_reintento', 'fallido')", name="trabajo_gemini_estado_valido"),
        sa.CheckConstraint("proveedor IN ('meta', 'twilio', 'api')", name="trabajo_gemini_proveedor_valido"),
    )
    op.create_index("ix_trabajos_gemini_diagnostico_id", "trabajos_gemini", ["diagnostico_id"])
    op.create_index("ix_trabajos_gemini_taller_id", "trabajos_gemini", ["taller_id"])
    op.create_index("ix_trabajos_gemini_usuario_id", "trabajos_gemini", ["usuario_id"])
    op.create_index("ix_trabajos_gemini_conversacion_id", "trabajos_gemini", ["conversacion_id"])
    op.create_index("ix_trabajos_gemini_estado_disponible", "trabajos_gemini", ["estado", "disponible_desde", "bloqueado_hasta"])


def downgrade() -> None:
    op.drop_index("ix_trabajos_gemini_estado_disponible", table_name="trabajos_gemini")
    op.drop_index("ix_trabajos_gemini_conversacion_id", table_name="trabajos_gemini")
    op.drop_index("ix_trabajos_gemini_usuario_id", table_name="trabajos_gemini")
    op.drop_index("ix_trabajos_gemini_taller_id", table_name="trabajos_gemini")
    op.drop_index("ix_trabajos_gemini_diagnostico_id", table_name="trabajos_gemini")
    op.drop_table("trabajos_gemini")
    op.drop_table("cuotas_gemini_global")

    op.drop_constraint("estado_entrega_valido", "mensajes", type_="check")
    op.create_check_constraint(
        "estado_entrega_valido",
        "mensajes",
        "estado_entrega IN ('recibido', 'pendiente', 'enviado', 'entregado', 'leido', 'fallido')",
    )

    op.drop_constraint("fuente_valida", "diagnosticos", type_="check")
    op.create_check_constraint(
        "fuente_valida",
        "diagnosticos",
        "fuente IN ('ml', 'rag', 'gemini', 'hibrido', 'manual')",
    )
