"""Repositorio de la cola durable general de CarBot."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import and_, case, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.security import cifrar_texto_reversible, descifrar_texto_reversible
from src.infrastructure.database.models.jobs import TrabajoSistema, WorkerSistema


class TrabajoSistemaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def contar_pendientes(
        self,
        cola: Optional[str] = None,
        taller_id: Optional[uuid.UUID] = None,
    ) -> int:
        filtros = [TrabajoSistema.estado.in_(("pendiente", "pendiente_reintento", "procesando"))]
        if cola:
            filtros.append(TrabajoSistema.cola == cola)
        if taller_id:
            filtros.append(TrabajoSistema.taller_id == taller_id)
        resultado = await self.session.execute(select(func.count(TrabajoSistema.id)).where(*filtros))
        return int(resultado.scalar() or 0)

    async def registrar_heartbeat(self, worker_id: str, estado: str = "activo") -> None:
        ahora = datetime.now(timezone.utc)
        worker = await self.session.get(WorkerSistema, worker_id)
        if worker is None:
            self.session.add(
                WorkerSistema(
                    id=worker_id,
                    estado=estado,
                    iniciado_en=ahora,
                    ultimo_heartbeat=ahora,
                )
            )
        else:
            worker.estado = estado
            worker.ultimo_heartbeat = ahora
        await self.session.flush()

    async def obtener_worker_activo(self, tolerancia_segundos: int = 20) -> Optional[WorkerSistema]:
        limite = datetime.now(timezone.utc) - timedelta(seconds=tolerancia_segundos)
        resultado = await self.session.execute(
            select(WorkerSistema)
            .where(WorkerSistema.estado == "activo", WorkerSistema.ultimo_heartbeat >= limite)
            .order_by(WorkerSistema.ultimo_heartbeat.desc())
            .limit(1)
        )
        return resultado.scalar_one_or_none()

    async def purgar_payloads_expirados(self) -> int:
        limite = datetime.now(timezone.utc) - timedelta(days=settings.queue_payload_retention_days)
        resultado = await self.session.execute(
            update(TrabajoSistema)
            .where(
                TrabajoSistema.estado.in_(("completado", "fallido", "cancelado")),
                TrabajoSistema.actualizado_en < limite,
                TrabajoSistema.payload_cifrado != "",
            )
            .values(payload_cifrado="", actualizado_en=datetime.now(timezone.utc))
        )
        return int(resultado.rowcount or 0)

    async def crear_trabajo(
        self,
        *,
        tipo: str,
        cola: str,
        payload: dict[str, Any],
        taller_id: Optional[uuid.UUID] = None,
        prioridad: int = 50,
        clave_idempotencia: Optional[str] = None,
        max_intentos: Optional[int] = None,
    ) -> tuple[TrabajoSistema, bool]:
        """Crea un trabajo cifrado; retorna el existente cuando la clave ya fue recibida."""
        if clave_idempotencia:
            existente = await self.session.execute(
                select(TrabajoSistema).where(TrabajoSistema.clave_idempotencia == clave_idempotencia)
            )
            trabajo_existente = existente.scalar_one_or_none()
            if trabajo_existente:
                return trabajo_existente, False

        pendientes = await self.contar_pendientes(cola)
        if pendientes >= settings.queue_max_pending:
            raise OverflowError(f"La cola {cola} alcanzó su capacidad máxima.")
        if taller_id:
            pendientes_taller = await self.contar_pendientes(cola, taller_id)
            if pendientes_taller >= settings.queue_max_pending_per_taller:
                raise OverflowError(f"El taller alcanzó el límite de trabajos pendientes en {cola}.")

        payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        trabajo = TrabajoSistema(
            tipo=tipo,
            cola=cola,
            taller_id=taller_id,
            prioridad=max(0, min(100, prioridad)),
            clave_idempotencia=clave_idempotencia,
            payload_cifrado=cifrar_texto_reversible(payload_json),
            max_intentos=max(1, min(20, max_intentos or settings.queue_job_max_attempts)),
            estado="pendiente",
            disponible_desde=datetime.now(timezone.utc),
        )
        if clave_idempotencia:
            try:
                async with self.session.begin_nested():
                    self.session.add(trabajo)
                    await self.session.flush()
            except IntegrityError:
                existente = await self.session.execute(
                    select(TrabajoSistema).where(
                        TrabajoSistema.clave_idempotencia == clave_idempotencia
                    )
                )
                trabajo_existente = existente.scalar_one()
                return trabajo_existente, False
        else:
            self.session.add(trabajo)
            await self.session.flush()
        return trabajo, True

    def obtener_payload(self, trabajo: TrabajoSistema) -> dict[str, Any]:
        return json.loads(descifrar_texto_reversible(trabajo.payload_cifrado))

    async def reclamar_siguiente(
        self,
        worker_id: str,
        colas: tuple[str, ...],
    ) -> Optional[TrabajoSistema]:
        ahora = datetime.now(timezone.utc)
        stmt = (
            select(TrabajoSistema)
            .where(
                TrabajoSistema.cola.in_(colas),
                TrabajoSistema.disponible_desde <= ahora,
                or_(
                    and_(
                        TrabajoSistema.estado.in_(("pendiente", "pendiente_reintento")),
                        or_(TrabajoSistema.bloqueado_hasta.is_(None), TrabajoSistema.bloqueado_hasta < ahora),
                    ),
                    and_(TrabajoSistema.estado == "procesando", TrabajoSistema.bloqueado_hasta < ahora),
                ),
            )
            .order_by(TrabajoSistema.prioridad.desc(), TrabajoSistema.disponible_desde.asc(), TrabajoSistema.creado_en.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        resultado = await self.session.execute(stmt)
        trabajo = resultado.scalar_one_or_none()
        if trabajo:
            trabajo.estado = "procesando"
            trabajo.intentos += 1
            trabajo.worker_id = worker_id
            trabajo.iniciado_en = ahora
            trabajo.bloqueado_hasta = ahora + timedelta(seconds=settings.queue_job_lock_seconds)
            await self.session.flush()
        return trabajo

    async def marcar_completado(self, trabajo_id: uuid.UUID, resumen: str = "") -> None:
        ahora = datetime.now(timezone.utc)
        await self.session.execute(
            update(TrabajoSistema)
            .where(TrabajoSistema.id == trabajo_id)
            .values(
                estado="completado",
                resultado_resumen=resumen[:1000] or None,
                payload_cifrado="",
                bloqueado_hasta=None,
                completado_en=ahora,
                actualizado_en=ahora,
                error_ultimo=None,
            )
        )

    async def marcar_error(self, trabajo: TrabajoSistema, error: str) -> str:
        """Aplica backoff 5s, 30s, 120s y finalmente envía a fallidos."""
        ahora = datetime.now(timezone.utc)
        esperas = (5, 30, 120)
        agotado = trabajo.intentos >= trabajo.max_intentos
        estado = "fallido" if agotado else "pendiente_reintento"
        espera = esperas[min(max(trabajo.intentos - 1, 0), len(esperas) - 1)]
        await self.session.execute(
            update(TrabajoSistema)
            .where(TrabajoSistema.id == trabajo.id)
            .values(
                estado=estado,
                disponible_desde=ahora if agotado else ahora + timedelta(seconds=espera),
                bloqueado_hasta=None,
                completado_en=ahora if agotado else None,
                actualizado_en=ahora,
                error_ultimo=(error or "Error no especificado")[:1000],
            )
        )
        return estado

    async def reintentar_fallido(self, trabajo_id: uuid.UUID, taller_id: uuid.UUID) -> bool:
        resultado = await self.session.execute(
            update(TrabajoSistema)
            .where(
                TrabajoSistema.id == trabajo_id,
                TrabajoSistema.taller_id == taller_id,
                TrabajoSistema.estado == "fallido",
            )
            .values(
                estado="pendiente",
                intentos=0,
                disponible_desde=datetime.now(timezone.utc),
                bloqueado_hasta=None,
                completado_en=None,
                error_ultimo=None,
            )
        )
        return bool(resultado.rowcount)

    async def listar_fallidos(self, taller_id: uuid.UUID, limite: int = 50):
        resultado = await self.session.execute(
            select(TrabajoSistema)
            .where(TrabajoSistema.taller_id == taller_id, TrabajoSistema.estado == "fallido")
            .order_by(TrabajoSistema.actualizado_en.desc())
            .limit(limite)
        )
        return resultado.scalars().all()

    async def obtener_para_taller(self, trabajo_id: uuid.UUID, taller_id: uuid.UUID) -> Optional[TrabajoSistema]:
        resultado = await self.session.execute(
            select(TrabajoSistema).where(
                TrabajoSistema.id == trabajo_id,
                TrabajoSistema.taller_id == taller_id,
            )
        )
        return resultado.scalar_one_or_none()

    async def obtener_metricas(self, taller_id: uuid.UUID) -> dict[str, Any]:
        ahora = datetime.now(timezone.utc)
        resultado = await self.session.execute(
            select(
                func.count(TrabajoSistema.id).label("total"),
                func.sum(case((TrabajoSistema.estado.in_(("pendiente", "pendiente_reintento")), 1), else_=0)).label("pendientes"),
                func.sum(case((TrabajoSistema.estado == "procesando", 1), else_=0)).label("procesando"),
                func.sum(case((TrabajoSistema.estado == "fallido", 1), else_=0)).label("fallidos"),
                func.avg(
                    case(
                        (
                            TrabajoSistema.iniciado_en.isnot(None),
                            func.extract("epoch", TrabajoSistema.iniciado_en - TrabajoSistema.creado_en) * 1000,
                        ),
                        else_=None,
                    )
                ).label("espera_promedio_ms"),
                func.max(TrabajoSistema.iniciado_en).label("ultima_actividad"),
            ).where(or_(TrabajoSistema.taller_id == taller_id, TrabajoSistema.taller_id.is_(None)))
        )
        fila = resultado.one()
        por_cola_resultado = await self.session.execute(
            select(TrabajoSistema.cola, TrabajoSistema.estado, func.count(TrabajoSistema.id))
            .where(
                or_(TrabajoSistema.taller_id == taller_id, TrabajoSistema.taller_id.is_(None)),
                TrabajoSistema.estado.in_(("pendiente", "pendiente_reintento", "procesando", "fallido")),
            )
            .group_by(TrabajoSistema.cola, TrabajoSistema.estado)
        )
        return {
            "total": int(fila.total or 0),
            "pendientes": int(fila.pendientes or 0),
            "procesando": int(fila.procesando or 0),
            "fallidos": int(fila.fallidos or 0),
            "espera_promedio_ms": int(fila.espera_promedio_ms or 0),
            "ultima_actividad": fila.ultima_actividad,
            "por_cola": [
                {"cola": cola, "estado": estado, "cantidad": cantidad}
                for cola, estado, cantidad in por_cola_resultado.all()
            ],
            "consultado_en": ahora,
        }
