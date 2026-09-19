"""Worker independiente para trabajos durables de CarBot."""

from __future__ import annotations

import asyncio
import json
import os
import socket
import sys
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services import GestorDiagnostico
from src.application.services.whatsapp import WebhookService
from src.config import PROJECT_ROOT, settings
from src.core.logger import logger
from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.repositories.trabajo_sistema_repository import TrabajoSistemaRepository


class SystemWorker:
    """Consume trabajos generales usando bloqueos recuperables y reintentos."""

    COLAS = ("diagnosticos", "audio", "notificaciones", "entrenamiento")

    def __init__(self, gestor: GestorDiagnostico | None = None) -> None:
        self.gestor = gestor or GestorDiagnostico()
        self.worker_id = f"{socket.gethostname()}:{os.getpid()}"
        self._corriendo = False
        self._redis: Any = None
        self._ultimo_heartbeat = 0.0
        self._ultima_limpieza = 0.0

    async def _registrar_heartbeat(self) -> None:
        ahora = time.monotonic()
        if ahora - self._ultimo_heartbeat < 5:
            return
        self._ultimo_heartbeat = ahora
        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            async with session.begin():
                await TrabajoSistemaRepository(session).registrar_heartbeat(self.worker_id)
        if not settings.rate_limit_storage_uri.startswith(("redis://", "rediss://")):
            return
        try:
            if self._redis is None:
                from redis.asyncio import Redis

                self._redis = Redis.from_url(settings.rate_limit_storage_uri, decode_responses=True)
            await self._redis.set("carbot:worker:sistema:heartbeat", self.worker_id, ex=15)
        except Exception as exc:
            logger.debug("No se pudo actualizar heartbeat del worker: %s", exc)

    async def _limpiar_payloads_expirados(self) -> None:
        ahora = time.monotonic()
        if ahora - self._ultima_limpieza < 3600:
            return
        self._ultima_limpieza = ahora
        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            async with session.begin():
                eliminados = await TrabajoSistemaRepository(session).purgar_payloads_expirados()
        if eliminados:
            logger.info("[System Worker] Se purgaron %s payloads expirados.", eliminados)

    async def _procesar(self, tipo: str, payload: dict[str, Any]) -> str:
        if tipo == "webhook_mensaje":
            resultado = await WebhookService(self.gestor).procesar_mensaje(**payload)
            return json.dumps(
                {"status": resultado.get("status", "procesado"), "tiempo_ms": resultado.get("tiempo_ms")},
                ensure_ascii=False,
            )
        if tipo == "diagnostico_api":
            dto = await asyncio.to_thread(
                self.gestor.procesar_consulta_texto,
                payload["sintoma"],
                placa=payload.get("placa") or "REST-API",
                marca_modelo=payload.get("marca_modelo") or "Vehículo genérico",
                session_id=payload.get("session_id"),
                proveedor="api",
            )
            return json.dumps(
                {
                    "falla_predicha": dto.diagnostico_ml,
                    "confianza": round(dto.confianza_ml * 100, 2),
                    "similitud_rag": round(dto.similitud_rag * 100, 2),
                    "modo": dto.modo_diagnostico,
                    "requiere_revision_humana": dto.requiere_revision_humana,
                },
                ensure_ascii=False,
            )
        if tipo == "entrenamiento_modelo":
            script = PROJECT_ROOT / "machine_learning" / "training" / "entrenar_modelo.py"
            proceso = await asyncio.create_subprocess_exec(
                sys.executable,
                str(script),
                cwd=str(PROJECT_ROOT),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proceso.communicate(), timeout=1800)
            except TimeoutError:
                proceso.kill()
                await proceso.wait()
                raise RuntimeError("El reentrenamiento superó el límite de 30 minutos.")
            if proceso.returncode != 0:
                detalle = stderr.decode("utf-8", errors="replace")[-800:]
                raise RuntimeError(f"Reentrenamiento fallido: {detalle}")
            self.gestor = GestorDiagnostico()
            salida = stdout.decode("utf-8", errors="replace")[-800:]
            return json.dumps({"status": "modelo_actualizado", "detalle": salida}, ensure_ascii=False)
        raise ValueError(f"Tipo de trabajo no soportado por este worker: {tipo}")

    async def procesar_siguiente(self) -> bool:
        engine = obtener_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            async with session.begin():
                repo = TrabajoSistemaRepository(session)
                trabajo = await repo.reclamar_siguiente(self.worker_id, self.COLAS)
            if trabajo is None:
                return False

            try:
                payload = TrabajoSistemaRepository(session).obtener_payload(trabajo)
                resumen = await self._procesar(trabajo.tipo, payload)
                async with session.begin():
                    await TrabajoSistemaRepository(session).marcar_completado(trabajo.id, resumen)
                logger.info("[System Worker] Trabajo %s completado (%s).", trabajo.id, trabajo.tipo)
            except Exception as exc:
                async with session.begin():
                    estado = await TrabajoSistemaRepository(session).marcar_error(trabajo, str(exc))
                logger.error(
                    "[System Worker] Trabajo %s terminó en %s: %s",
                    trabajo.id,
                    estado,
                    type(exc).__name__,
                )
            return True

    async def run(self) -> None:
        self._corriendo = True
        logger.info("[System Worker] Iniciado con ID %s.", self.worker_id)
        while self._corriendo:
            try:
                await self._registrar_heartbeat()
                await self._limpiar_payloads_expirados()
                procesado = await self.procesar_siguiente()
                if not procesado:
                    await asyncio.sleep(max(0.1, settings.queue_poll_interval_ms / 1000))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("[System Worker] Error recuperable del ciclo: %s", type(exc).__name__)
                await asyncio.sleep(2)

    async def detener(self) -> None:
        self._corriendo = False
        try:
            async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
                async with session.begin():
                    await TrabajoSistemaRepository(session).registrar_heartbeat(self.worker_id, "detenido")
        except Exception:
            pass
        if self._redis is not None:
            await self._redis.aclose()
