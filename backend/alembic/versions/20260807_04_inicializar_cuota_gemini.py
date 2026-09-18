"""Inicializa de forma idempotente la fila singleton de cuota Gemini.

Revision ID: 20260807_04
Revises: 20260807_03
"""

from alembic import op

revision = "20260807_04"
down_revision = "20260807_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO cuotas_gemini_global
            (id, fecha, solicitudes_hoy, solicitudes_minuto, minuto_epoch, actualizado_en)
        VALUES
            (1, CURRENT_DATE, 0, 0, 0, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    # La fila contiene estado operativo; eliminarla durante un downgrade no es seguro.
    pass
