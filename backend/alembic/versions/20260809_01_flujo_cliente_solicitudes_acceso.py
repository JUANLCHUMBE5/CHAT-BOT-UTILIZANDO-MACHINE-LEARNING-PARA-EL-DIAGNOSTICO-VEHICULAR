"""Agregar rol cliente, datos de taller, identidades_whatsapp y solicitudes_acceso.

Revision ID: 20260809_01
Revises: 20260808_04
Create Date: 2026-08-09
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260809_01"
down_revision: Union[str, None] = "20260808_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Insertar rol cliente (id: 4) si no existe
    roles = sa.table(
        "roles",
        sa.column("id", sa.SmallInteger()),
        sa.column("codigo", sa.String()),
        sa.column("nombre", sa.String()),
        sa.column("descripcion", sa.String()),
    )
    op.bulk_insert(
        roles,
        [
            {
                "id": 4,
                "codigo": "cliente",
                "nombre": "Cliente",
                "descripcion": "Cliente del taller. Consultas generales, citas y solicitud de acceso.",
            },
        ],
    )

    # 2. Agregar campos a talleres
    op.add_column("talleres", sa.Column("horario_atencion", sa.String(length=200), nullable=True))
    op.add_column("talleres", sa.Column("servicios", sa.String(length=1000), nullable=True))
    op.add_column("talleres", sa.Column("google_maps_url", sa.String(length=500), nullable=True))
    op.add_column("talleres", sa.Column("telefono_id_meta", sa.String(length=50), nullable=True))
    op.create_index("ix_talleres_telefono_id_meta", "talleres", ["telefono_id_meta"], unique=True)

    # 3. Crear tabla identidades_whatsapp
    op.create_table(
        "identidades_whatsapp",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("proveedor", sa.String(length=20), server_default="meta", nullable=False),
        sa.Column("identificador_hash", sa.String(length=64), nullable=False),
        sa.Column("destinatario_cifrado", sa.Text(), nullable=True),
        sa.Column("tipo_identificador", sa.String(length=20), server_default="telefono", nullable=False),
        sa.Column("ultimos4", sa.String(length=4), nullable=True),
        sa.Column("ultima_interaccion", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("proveedor IN ('meta', 'twilio', 'api')", name="ck_identidad_proveedor_valido"),
        sa.CheckConstraint("tipo_identificador IN ('telefono', 'wa_id', 'user_id')", name="ck_identidad_tipo_valido"),
        sa.CheckConstraint("length(identificador_hash) = 64", name="ck_identidad_hash_longitud"),
        sa.CheckConstraint("ultimos4 IS NULL OR length(ultimos4) <= 4", name="ck_identidad_ultimos4_longitud"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="fk_identidades_usuario_id_usuarios", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_identidades_whatsapp"),
    )
    op.create_index("ix_identidades_whatsapp_identificador_hash", "identidades_whatsapp", ["identificador_hash"], unique=True)
    op.create_index("ix_identidades_whatsapp_usuario_id", "identidades_whatsapp", ["usuario_id"], unique=False)

    # 4. Crear tabla solicitudes_acceso
    op.create_table(
        "solicitudes_acceso",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("taller_id", sa.Uuid(), nullable=False),
        sa.Column("rol_solicitado", sa.String(length=30), server_default="mecanico", nullable=False),
        sa.Column("estado", sa.String(length=20), server_default="pendiente", nullable=False),
        sa.Column("solicitado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("revisado_por_id", sa.Uuid(), nullable=True),
        sa.Column("revisado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.CheckConstraint("estado IN ('pendiente', 'aprobada', 'rechazada')", name="ck_solicitud_estado_valido"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="fk_solicitudes_usuario_id_usuarios", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["taller_id"], ["talleres.id"], name="fk_solicitudes_taller_id_talleres", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["revisado_por_id"], ["usuarios.id"], name="fk_solicitudes_revisado_por_id_usuarios", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_solicitudes_acceso"),
    )
    op.create_index("ix_solicitudes_acceso_revisado_por_id", "solicitudes_acceso", ["revisado_por_id"], unique=False)
    op.create_index("ix_solicitudes_acceso_taller_estado", "solicitudes_acceso", ["taller_id", "estado"], unique=False)
    op.create_index("ix_solicitudes_acceso_taller_id", "solicitudes_acceso", ["taller_id"], unique=False)
    op.create_index("ix_solicitudes_acceso_usuario_id", "solicitudes_acceso", ["usuario_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_solicitudes_acceso_usuario_id", table_name="solicitudes_acceso")
    op.drop_index("ix_solicitudes_acceso_taller_id", table_name="solicitudes_acceso")
    op.drop_index("ix_solicitudes_acceso_taller_estado", table_name="solicitudes_acceso")
    op.drop_index("ix_solicitudes_acceso_revisado_por_id", table_name="solicitudes_acceso")
    op.drop_table("solicitudes_acceso")

    op.drop_index("ix_identidades_whatsapp_usuario_id", table_name="identidades_whatsapp")
    op.drop_index("ix_identidades_whatsapp_identificador_hash", table_name="identidades_whatsapp")
    op.drop_table("identidades_whatsapp")

    op.drop_index("ix_talleres_telefono_id_meta", table_name="talleres")
    op.drop_column("talleres", "telefono_id_meta")
    op.drop_column("talleres", "google_maps_url")
    op.drop_column("talleres", "servicios")
    op.drop_column("talleres", "horario_atencion")

    op.execute("DELETE FROM roles WHERE id = 4")
