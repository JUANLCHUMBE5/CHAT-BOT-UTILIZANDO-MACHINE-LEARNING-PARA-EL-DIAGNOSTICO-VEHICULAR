"""Casos de uso de monitoreo y administración de las colas internas."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository
from src.infrastructure.database.repositories.trabajo_sistema_repository import TrabajoSistemaRepository


def _uuid_opcional(valor: Any) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(valor)) if valor else None
    except ValueError:
        return None


class ServicioTrabajosSistema:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TrabajoSistemaRepository(session)

    async def metricas(self, taller_id: uuid.UUID) -> dict[str, Any]:
        metricas = await self.repo.obtener_metricas(taller_id)
        worker = await self.repo.obtener_worker_activo()
        return {
            **metricas,
            "worker_activo": worker is not None,
            "worker_id": worker.id if worker else None,
        }

    async def reintentar(
        self,
        trabajo_id: uuid.UUID,
        taller_id: uuid.UUID,
        usuario_id: Any,
    ) -> bool:
        actualizado = await self.repo.reintentar_fallido(trabajo_id, taller_id)
        if actualizado:
            await OperacionesRepository(self.session).registrar_auditoria(
                accion="reintentar_trabajo",
                entidad="trabajo_sistema",
                entidad_id=trabajo_id,
                taller_id=taller_id,
                usuario_id=_uuid_opcional(usuario_id),
            )
        return actualizado

    async def encolar_reentrenamiento(
        self,
        taller_id: uuid.UUID,
        usuario_id: Any,
        solicitado_por: str | None,
    ):
        clave = f"reentrenamiento:{taller_id}:{datetime.now(timezone.utc).date().isoformat()}"
        trabajo, creado = await self.repo.crear_trabajo(
            tipo="entrenamiento_modelo",
            cola="entrenamiento",
            payload={"solicitado_por": solicitado_por or str(usuario_id or "")},
            taller_id=taller_id,
            prioridad=10,
            clave_idempotencia=clave,
            max_intentos=2,
        )
        if creado:
            await OperacionesRepository(self.session).registrar_auditoria(
                accion="encolar_reentrenamiento",
                entidad="trabajo_sistema",
                entidad_id=trabajo.id,
                taller_id=taller_id,
                usuario_id=_uuid_opcional(usuario_id),
                detalles={"clave_idempotencia": clave},
            )
        return trabajo, creado
