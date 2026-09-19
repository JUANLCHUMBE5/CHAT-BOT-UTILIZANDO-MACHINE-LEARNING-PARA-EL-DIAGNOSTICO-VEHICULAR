"""Agregar subcampos auditables de Ficha 2 para vehiculo y descripcion.

Revision ID: 20260919_03
Revises: 20260919_02
Create Date: 2026-09-19
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260919_03"
down_revision = "20260919_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("validaciones_taller", sa.Column("descripcion_sintoma", sa.Text(), nullable=True))
    op.add_column("validaciones_taller", sa.Column("vehiculo_anio", sa.Integer(), nullable=True))
    op.add_column("validaciones_taller", sa.Column("vehiculo_kilometraje", sa.Integer(), nullable=True))
    op.add_column("validaciones_taller", sa.Column("vehiculo_combustible", sa.String(length=30), nullable=True))
    op.add_column("validaciones_taller", sa.Column("vehiculo_transmision", sa.String(length=30), nullable=True))
    op.create_check_constraint(
        "chk_validaciones_vehiculo_anio",
        "validaciones_taller",
        "vehiculo_anio IS NULL OR vehiculo_anio BETWEEN 1950 AND 2100",
    )
    op.create_check_constraint(
        "chk_validaciones_vehiculo_km",
        "validaciones_taller",
        "vehiculo_kilometraje IS NULL OR vehiculo_kilometraje >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("chk_validaciones_vehiculo_km", "validaciones_taller", type_="check")
    op.drop_constraint("chk_validaciones_vehiculo_anio", "validaciones_taller", type_="check")
    op.drop_column("validaciones_taller", "vehiculo_transmision")
    op.drop_column("validaciones_taller", "vehiculo_combustible")
    op.drop_column("validaciones_taller", "vehiculo_kilometraje")
    op.drop_column("validaciones_taller", "vehiculo_anio")
    op.drop_column("validaciones_taller", "descripcion_sintoma")
