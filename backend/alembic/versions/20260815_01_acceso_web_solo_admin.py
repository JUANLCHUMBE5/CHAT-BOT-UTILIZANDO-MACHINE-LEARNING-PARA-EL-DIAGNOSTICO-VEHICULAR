"""Eliminar credenciales web de usuarios no administrativos.

Revision ID: 20260815_01
Revises: 20260809_01
Create Date: 2026-08-15
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260815_01"
down_revision: Union[str, None] = "20260809_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Los mecánicos y clientes se autentican por su número de WhatsApp, no por contraseña."""
    op.execute(
        """
        UPDATE usuarios
        SET password_hash = NULL,
            debe_cambiar_password = FALSE
        WHERE rol_id NOT IN (
            SELECT id FROM roles WHERE codigo IN ('administrador', 'admin')
        )
        """
    )


def downgrade() -> None:
    # Los hashes eliminados no deben reconstruirse ni recuperarse.
    pass
