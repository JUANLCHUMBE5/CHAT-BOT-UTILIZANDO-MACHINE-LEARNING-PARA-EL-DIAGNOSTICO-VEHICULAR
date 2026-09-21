"""Soporte formal para PILOT, blindaje contra contaminación y telemetría técnica.

Revision ID: 20260919_04
Revises: 20260919_03
Create Date: 2026-09-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260919_04"
down_revision: Union[str, None] = "20260919_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Actualizar CheckConstraint de tipo_registro en validaciones_taller para incluir 'PILOT'
    op.drop_constraint("chk_validaciones_tipo_registro", "validaciones_taller", type_="check")
    op.create_check_constraint(
        "chk_validaciones_tipo_registro",
        "validaciones_taller",
        "tipo_registro IN ('DEVELOPMENT', 'PILOT', 'REGRESSION', 'THESIS_PRETEST', 'THESIS_POSTTEST')",
    )

    # 2. Modificar server_default para evitar que registros por defecto se etiqueten como THESIS_*
    op.alter_column(
        "validaciones_taller",
        "tipo_registro",
        server_default="DEVELOPMENT",
    )

    # 3. Actualizar CheckConstraint de tipo_registro en diagnosticos para incluir 'PILOT'
    op.drop_constraint("chk_diagnosticos_tipo_registro", "diagnosticos", type_="check")
    op.create_check_constraint(
        "chk_diagnosticos_tipo_registro",
        "diagnosticos",
        "tipo_registro IN ('DEVELOPMENT', 'PILOT', 'REGRESSION', 'THESIS_PRETEST', 'THESIS_POSTTEST')",
    )

    # 4. Columnas opcionales de telemetría técnica en validaciones_taller
    op.add_column("validaciones_taller", sa.Column("inicio_sistema_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("validaciones_taller", sa.Column("fin_sistema_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("validaciones_taller", sa.Column("duracion_sistema_segundos", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("validaciones_taller", "duracion_sistema_segundos")
    op.drop_column("validaciones_taller", "fin_sistema_at")
    op.drop_column("validaciones_taller", "inicio_sistema_at")

    op.drop_constraint("chk_diagnosticos_tipo_registro", "diagnosticos", type_="check")
    op.create_check_constraint(
        "chk_diagnosticos_tipo_registro",
        "diagnosticos",
        "tipo_registro IN ('DEVELOPMENT', 'REGRESSION', 'THESIS_PRETEST', 'THESIS_POSTTEST')",
    )

    op.alter_column(
        "validaciones_taller",
        "tipo_registro",
        server_default="THESIS_POSTTEST",
    )

    op.drop_constraint("chk_validaciones_tipo_registro", "validaciones_taller", type_="check")
    op.create_check_constraint(
        "chk_validaciones_tipo_registro",
        "validaciones_taller",
        "tipo_registro IN ('DEVELOPMENT', 'REGRESSION', 'THESIS_PRETEST', 'THESIS_POSTTEST')",
    )
