"""Crear esquema relacional inicial de CarBot.

Revision ID: 20260806_01
Revises: None
Create Date: 2026-08-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260806_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("codigo", sa.String(30), nullable=False),
        sa.Column("nombre", sa.String(80), nullable=False),
        sa.Column("descripcion", sa.String(250), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint("codigo", name="uq_roles_codigo"),
    )
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
            {"id": 1, "codigo": "administrador", "nombre": "Administrador", "descripcion": "Administra el taller y sus usuarios."},
            {"id": 2, "codigo": "mecanico", "nombre": "Mecánico", "descripcion": "Registra y confirma diagnósticos."},
            {"id": 3, "codigo": "supervisor", "nombre": "Supervisor", "descripcion": "Revisa diagnósticos y métricas."},
        ],
    )

    op.create_table(
        "talleres",
        sa.Column("nombre", sa.String(160), nullable=False),
        sa.Column("ruc", sa.String(11), nullable=True),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.Column("direccion", sa.String(250), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("ruc IS NULL OR length(ruc) = 11", name=op.f("ck_talleres_ruc_longitud")),
        sa.PrimaryKeyConstraint("id", name="pk_talleres"),
        sa.UniqueConstraint("ruc", name="uq_talleres_ruc"),
    )

    op.create_table(
        "usuarios",
        sa.Column("taller_id", sa.Uuid(), nullable=False),
        sa.Column("rol_id", sa.SmallInteger(), nullable=False),
        sa.Column("nombres", sa.String(120), nullable=False),
        sa.Column("apellidos", sa.String(120), nullable=True),
        sa.Column("whatsapp_hash", sa.String(64), nullable=False),
        sa.Column("whatsapp_ultimos4", sa.String(4), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("length(whatsapp_hash) = 64", name=op.f("ck_usuarios_whatsapp_hash_longitud")),
        sa.CheckConstraint("length(whatsapp_ultimos4) = 4", name=op.f("ck_usuarios_whatsapp_ultimos4_longitud")),
        sa.ForeignKeyConstraint(["rol_id"], ["roles.id"], name="fk_usuarios_rol_id_roles", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["taller_id"], ["talleres.id"], name="fk_usuarios_taller_id_talleres", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_usuarios"),
        sa.UniqueConstraint("taller_id", "id", name="uq_usuarios_taller_id_id"),
        sa.UniqueConstraint("whatsapp_hash", name="uq_usuarios_whatsapp_hash"),
    )
    op.create_index("ix_usuarios_rol_id", "usuarios", ["rol_id"])
    op.create_index("ix_usuarios_taller_id", "usuarios", ["taller_id"])

    op.create_table(
        "vehiculos",
        sa.Column("taller_id", sa.Uuid(), nullable=False),
        sa.Column("registrado_por_id", sa.Uuid(), nullable=False),
        sa.Column("placa_hash", sa.String(64), nullable=True),
        sa.Column("placa_ultimos4", sa.String(4), nullable=True),
        sa.Column("marca", sa.String(80), nullable=False),
        sa.Column("modelo", sa.String(100), nullable=False),
        sa.Column("anio", sa.SmallInteger(), nullable=True),
        sa.Column("motor", sa.String(100), nullable=True),
        sa.Column("combustible", sa.String(30), nullable=True),
        sa.Column("kilometraje", sa.Integer(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("anio IS NULL OR anio BETWEEN 1886 AND 2200", name=op.f("ck_vehiculos_anio_valido")),
        sa.CheckConstraint("kilometraje IS NULL OR kilometraje >= 0", name=op.f("ck_vehiculos_kilometraje_no_negativo")),
        sa.CheckConstraint("placa_hash IS NULL OR length(placa_hash) = 64", name=op.f("ck_vehiculos_placa_hash_longitud")),
        sa.ForeignKeyConstraint(["registrado_por_id"], ["usuarios.id"], name="fk_vehiculos_registrado_por_id_usuarios", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["taller_id"], ["talleres.id"], name="fk_vehiculos_taller_id_talleres", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_vehiculos"),
        sa.UniqueConstraint("taller_id", "placa_hash", name="uq_vehiculos_taller_placa_hash"),
    )
    op.create_index("ix_vehiculos_registrado_por_id", "vehiculos", ["registrado_por_id"])
    op.create_index("ix_vehiculos_taller_id", "vehiculos", ["taller_id"])

    op.create_table(
        "conversaciones",
        sa.Column("taller_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("canal", sa.String(20), server_default=sa.text("'whatsapp'"), nullable=False),
        sa.Column("estado", sa.String(20), server_default=sa.text("'abierta'"), nullable=False),
        sa.Column("iniciada_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ultimo_mensaje_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ventana_servicio_hasta", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cerrada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("canal IN ('whatsapp', 'api', 'web')", name=op.f("ck_conversaciones_canal_valido")),
        sa.CheckConstraint("estado IN ('abierta', 'cerrada', 'expirada')", name=op.f("ck_conversaciones_estado_valido")),
        sa.CheckConstraint("ultimo_mensaje_en >= iniciada_en", name=op.f("ck_conversaciones_fechas_validas")),
        sa.ForeignKeyConstraint(["taller_id"], ["talleres.id"], name="fk_conversaciones_taller_id_talleres", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="fk_conversaciones_usuario_id_usuarios", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_conversaciones"),
    )
    op.create_index("ix_conversaciones_taller_id", "conversaciones", ["taller_id"])
    op.create_index("ix_conversaciones_usuario_id", "conversaciones", ["usuario_id"])

    op.create_table(
        "mensajes",
        sa.Column("conversacion_id", sa.Uuid(), nullable=False),
        sa.Column("taller_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("meta_message_id", sa.String(150), nullable=False),
        sa.Column("direccion", sa.String(10), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("categoria_cobro", sa.String(20), server_default=sa.text("'servicio'"), nullable=False),
        sa.Column("texto", sa.Text(), nullable=True),
        sa.Column("estado_entrega", sa.String(20), server_default=sa.text("'recibido'"), nullable=False),
        sa.Column("costo_estimado", sa.Numeric(12, 6), server_default=sa.text("0"), nullable=False),
        sa.Column("moneda", sa.String(3), server_default=sa.text("'PEN'"), nullable=False),
        sa.Column("ocurrido_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("direccion IN ('entrada', 'salida')", name=op.f("ck_mensajes_direccion_valida")),
        sa.CheckConstraint("tipo IN ('texto', 'audio', 'imagen', 'documento', 'sistema')", name=op.f("ck_mensajes_tipo_valido")),
        sa.CheckConstraint("categoria_cobro IN ('servicio', 'utilidad', 'autenticacion', 'marketing')", name=op.f("ck_mensajes_categoria_cobro_valida")),
        sa.CheckConstraint("estado_entrega IN ('recibido', 'pendiente', 'enviado', 'entregado', 'leido', 'fallido')", name=op.f("ck_mensajes_estado_entrega_valido")),
        sa.CheckConstraint("costo_estimado >= 0", name=op.f("ck_mensajes_costo_no_negativo")),
        sa.CheckConstraint("length(moneda) = 3", name=op.f("ck_mensajes_moneda_iso_4217")),
        sa.ForeignKeyConstraint(["conversacion_id"], ["conversaciones.id"], name="fk_mensajes_conversacion_id_conversaciones", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["taller_id"], ["talleres.id"], name="fk_mensajes_taller_id_talleres", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="fk_mensajes_usuario_id_usuarios", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_mensajes"),
        sa.UniqueConstraint("meta_message_id", name="uq_mensajes_meta_message_id"),
    )
    op.create_index("ix_mensajes_conversacion_id", "mensajes", ["conversacion_id"])
    op.create_index("ix_mensajes_taller_id", "mensajes", ["taller_id"])
    op.create_index("ix_mensajes_usuario_id", "mensajes", ["usuario_id"])

    op.create_table(
        "diagnosticos",
        sa.Column("taller_id", sa.Uuid(), nullable=False),
        sa.Column("mecanico_id", sa.Uuid(), nullable=False),
        sa.Column("vehiculo_id", sa.Uuid(), nullable=True),
        sa.Column("conversacion_id", sa.Uuid(), nullable=True),
        sa.Column("sintoma_original", sa.Text(), nullable=False),
        sa.Column("sintoma_normalizado", sa.Text(), nullable=True),
        sa.Column("falla_predicha", sa.String(200), nullable=True),
        sa.Column("confianza", sa.Numeric(5, 4), nullable=True),
        sa.Column("fuente", sa.String(20), nullable=False),
        sa.Column("estado", sa.String(20), server_default=sa.text("'generado'"), nullable=False),
        sa.Column("duracion_ms", sa.Integer(), nullable=True),
        sa.Column("conclusion_mecanico", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("confianza IS NULL OR confianza BETWEEN 0 AND 1", name=op.f("ck_diagnosticos_confianza_rango")),
        sa.CheckConstraint("duracion_ms IS NULL OR duracion_ms >= 0", name=op.f("ck_diagnosticos_duracion_no_negativa")),
        sa.CheckConstraint("fuente IN ('ml', 'rag', 'gemini', 'hibrido', 'manual')", name=op.f("ck_diagnosticos_fuente_valida")),
        sa.CheckConstraint("estado IN ('generado', 'en_revision', 'confirmado', 'descartado')", name=op.f("ck_diagnosticos_estado_valido")),
        sa.ForeignKeyConstraint(["conversacion_id"], ["conversaciones.id"], name="fk_diagnosticos_conversacion_id_conversaciones", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["mecanico_id"], ["usuarios.id"], name="fk_diagnosticos_mecanico_id_usuarios", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["taller_id"], ["talleres.id"], name="fk_diagnosticos_taller_id_talleres", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["vehiculo_id"], ["vehiculos.id"], name="fk_diagnosticos_vehiculo_id_vehiculos", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_diagnosticos"),
    )
    op.create_index("ix_diagnosticos_conversacion_id", "diagnosticos", ["conversacion_id"])
    op.create_index("ix_diagnosticos_mecanico_id", "diagnosticos", ["mecanico_id"])
    op.create_index("ix_diagnosticos_taller_id", "diagnosticos", ["taller_id"])
    op.create_index("ix_diagnosticos_vehiculo_id", "diagnosticos", ["vehiculo_id"])

    op.create_table(
        "hipotesis_diagnostico",
        sa.Column("diagnostico_id", sa.Uuid(), nullable=False),
        sa.Column("orden", sa.SmallInteger(), nullable=False),
        sa.Column("falla_probable", sa.String(200), nullable=False),
        sa.Column("confianza", sa.Numeric(5, 4), nullable=True),
        sa.Column("evidencia", sa.Text(), nullable=True),
        sa.Column("prueba_recomendada", sa.Text(), nullable=True),
        sa.Column("resultado", sa.String(20), server_default=sa.text("'pendiente'"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("orden > 0", name=op.f("ck_hipotesis_diagnostico_orden_positivo")),
        sa.CheckConstraint("confianza IS NULL OR confianza BETWEEN 0 AND 1", name=op.f("ck_hipotesis_diagnostico_confianza_rango")),
        sa.CheckConstraint("resultado IN ('pendiente', 'confirmada', 'descartada')", name=op.f("ck_hipotesis_diagnostico_resultado_valido")),
        sa.ForeignKeyConstraint(["diagnostico_id"], ["diagnosticos.id"], name="fk_hipotesis_diagnostico_diagnostico_id_diagnosticos", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_hipotesis_diagnostico"),
        sa.UniqueConstraint("diagnostico_id", "orden", name="uq_hipotesis_diagnostico_orden"),
    )
    op.create_index("ix_hipotesis_diagnostico_diagnostico_id", "hipotesis_diagnostico", ["diagnostico_id"])

    op.create_table(
        "uso_api",
        sa.Column("taller_id", sa.Uuid(), nullable=False),
        sa.Column("diagnostico_id", sa.Uuid(), nullable=True),
        sa.Column("mensaje_id", sa.Uuid(), nullable=True),
        sa.Column("proveedor", sa.String(30), nullable=False),
        sa.Column("operacion", sa.String(50), nullable=False),
        sa.Column("modelo", sa.String(80), nullable=True),
        sa.Column("solicitud_externa_id", sa.String(150), nullable=True),
        sa.Column("tokens_entrada", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("tokens_salida", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("unidades", sa.Numeric(14, 4), server_default=sa.text("0"), nullable=False),
        sa.Column("costo_estimado", sa.Numeric(12, 6), server_default=sa.text("0"), nullable=False),
        sa.Column("moneda", sa.String(3), server_default=sa.text("'USD'"), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("proveedor IN ('meta', 'google', 'aws', 'local')", name=op.f("ck_uso_api_proveedor_valido")),
        sa.CheckConstraint("tokens_entrada >= 0 AND tokens_salida >= 0", name=op.f("ck_uso_api_tokens_no_negativos")),
        sa.CheckConstraint("unidades >= 0", name=op.f("ck_uso_api_unidades_no_negativas")),
        sa.CheckConstraint("costo_estimado >= 0", name=op.f("ck_uso_api_costo_no_negativo")),
        sa.CheckConstraint("length(moneda) = 3", name=op.f("ck_uso_api_moneda_iso_4217")),
        sa.ForeignKeyConstraint(["diagnostico_id"], ["diagnosticos.id"], name="fk_uso_api_diagnostico_id_diagnosticos", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["mensaje_id"], ["mensajes.id"], name="fk_uso_api_mensaje_id_mensajes", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["taller_id"], ["talleres.id"], name="fk_uso_api_taller_id_talleres", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_uso_api"),
    )
    op.create_index("ix_uso_api_diagnostico_id", "uso_api", ["diagnostico_id"])
    op.create_index("ix_uso_api_mensaje_id", "uso_api", ["mensaje_id"])
    op.create_index("ix_uso_api_solicitud_externa_id", "uso_api", ["solicitud_externa_id"])
    op.create_index("ix_uso_api_taller_id", "uso_api", ["taller_id"])

    op.create_table(
        "auditoria",
        sa.Column("taller_id", sa.Uuid(), nullable=True),
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("accion", sa.String(80), nullable=False),
        sa.Column("entidad", sa.String(80), nullable=False),
        sa.Column("entidad_id", sa.Uuid(), nullable=True),
        sa.Column("detalles", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ip_hash", sa.String(64), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("ip_hash IS NULL OR length(ip_hash) = 64", name=op.f("ck_auditoria_ip_hash_longitud")),
        sa.ForeignKeyConstraint(["taller_id"], ["talleres.id"], name="fk_auditoria_taller_id_talleres", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], name="fk_auditoria_usuario_id_usuarios", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_auditoria"),
    )
    op.create_index("ix_auditoria_taller_id", "auditoria", ["taller_id"])
    op.create_index("ix_auditoria_usuario_id", "auditoria", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_auditoria_usuario_id", table_name="auditoria")
    op.drop_index("ix_auditoria_taller_id", table_name="auditoria")
    op.drop_table("auditoria")
    op.drop_index("ix_uso_api_taller_id", table_name="uso_api")
    op.drop_index("ix_uso_api_solicitud_externa_id", table_name="uso_api")
    op.drop_index("ix_uso_api_mensaje_id", table_name="uso_api")
    op.drop_index("ix_uso_api_diagnostico_id", table_name="uso_api")
    op.drop_table("uso_api")
    op.drop_index("ix_hipotesis_diagnostico_diagnostico_id", table_name="hipotesis_diagnostico")
    op.drop_table("hipotesis_diagnostico")
    op.drop_index("ix_diagnosticos_vehiculo_id", table_name="diagnosticos")
    op.drop_index("ix_diagnosticos_taller_id", table_name="diagnosticos")
    op.drop_index("ix_diagnosticos_mecanico_id", table_name="diagnosticos")
    op.drop_index("ix_diagnosticos_conversacion_id", table_name="diagnosticos")
    op.drop_table("diagnosticos")
    op.drop_index("ix_mensajes_usuario_id", table_name="mensajes")
    op.drop_index("ix_mensajes_taller_id", table_name="mensajes")
    op.drop_index("ix_mensajes_conversacion_id", table_name="mensajes")
    op.drop_table("mensajes")
    op.drop_index("ix_conversaciones_usuario_id", table_name="conversaciones")
    op.drop_index("ix_conversaciones_taller_id", table_name="conversaciones")
    op.drop_table("conversaciones")
    op.drop_index("ix_vehiculos_taller_id", table_name="vehiculos")
    op.drop_index("ix_vehiculos_registrado_por_id", table_name="vehiculos")
    op.drop_table("vehiculos")
    op.drop_index("ix_usuarios_taller_id", table_name="usuarios")
    op.drop_index("ix_usuarios_rol_id", table_name="usuarios")
    op.drop_table("usuarios")
    op.drop_table("talleres")
    op.drop_table("roles")
