"""Repositorio para control de cuota y sincronización atómica de RPM/RPD en PostgreSQL."""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Tuple

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.jobs import CuotaGeminiGlobal


class CuotaGeminiRepository:
    """Acceso atómico y sincronizado entre múltiples procesos para límites RPM y RPD en PostgreSQL."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def adquirir_slot_compartido(
        self, max_rpm: int = 12, max_rpd: int = 18
    ) -> Tuple[bool, str, int, int]:
        """
        Adquiere atómicamente un slot de Gemini compartido en PostgreSQL usando SELECT ... FOR UPDATE.
        Retorna (concedido: bool, motivo: str, solicitudes_hoy: int, solicitudes_minuto: int).
        """
        ahora_epoch_minuto = int(time.time() // 60)
        hoy = date.today()

        # Crear la fila singleton de forma segura incluso si arrancan varios workers.
        await self.session.execute(
            insert(CuotaGeminiGlobal)
            .values(
                id=1,
                fecha=hoy,
                solicitudes_hoy=0,
                solicitudes_minuto=0,
                minuto_epoch=ahora_epoch_minuto,
                actualizado_en=datetime.now(timezone.utc),
            )
            .on_conflict_do_nothing(index_elements=[CuotaGeminiGlobal.id])
        )

        # Bloquear y leer la fila única de cuotas globales (id=1)
        stmt = (
            select(CuotaGeminiGlobal)
            .where(CuotaGeminiGlobal.id == 1)
            .with_for_update()
        )
        res = await self.session.execute(stmt)
        cuota = res.scalar_one_or_none()

        if cuota is None:
            raise RuntimeError("No fue posible inicializar la cuota global de Gemini.")

        # 2. Reset diario si cambió la fecha
        if cuota.fecha != hoy:
            cuota.fecha = hoy
            cuota.solicitudes_hoy = 0

        # 3. Reset por minuto si cambió el minuto epoch
        if cuota.minuto_epoch != ahora_epoch_minuto:
            cuota.minuto_epoch = ahora_epoch_minuto
            cuota.solicitudes_minuto = 0

        # 4. Validar límite diario (RPD)
        if cuota.cooldown_hasta and cuota.cooldown_hasta > datetime.now(timezone.utc):
            segundos = max(
                1,
                int((cuota.cooldown_hasta - datetime.now(timezone.utc)).total_seconds()) + 1,
            )
            return (
                False,
                f"cooldown_activo ({segundos}s)",
                cuota.solicitudes_hoy,
                cuota.solicitudes_minuto,
            )
        if cuota.cooldown_hasta:
            cuota.cooldown_hasta = None

        if cuota.solicitudes_hoy >= max_rpd:
            return (
                False,
                f"rpd_excedido ({cuota.solicitudes_hoy}/{max_rpd} día)",
                cuota.solicitudes_hoy,
                cuota.solicitudes_minuto,
            )

        # 5. Validar límite por minuto (RPM)
        if cuota.solicitudes_minuto >= max_rpm:
            return (
                False,
                f"rpm_excedido ({cuota.solicitudes_minuto}/{max_rpm} min)",
                cuota.solicitudes_hoy,
                cuota.solicitudes_minuto,
            )

        # 6. Conceder slot e incrementar contadores
        cuota.solicitudes_hoy += 1
        cuota.solicitudes_minuto += 1
        cuota.actualizado_en = datetime.now(timezone.utc)
        await self.session.flush()

        return (
            True,
            "concedido",
            cuota.solicitudes_hoy,
            cuota.solicitudes_minuto,
        )

    async def registrar_resultado_externo(
        self,
        exitoso: bool,
        codigo_http: int | None = None,
        error: str | None = None,
        retry_after_segundos: int = 0,
    ) -> None:
        """Comparte entre workers el último resultado real y el cooldown indicado por Google."""
        ahora = datetime.now(timezone.utc)
        await self.session.execute(
            insert(CuotaGeminiGlobal)
            .values(id=1, fecha=date.today(), minuto_epoch=int(time.time() // 60))
            .on_conflict_do_nothing(index_elements=[CuotaGeminiGlobal.id])
        )
        res = await self.session.execute(
            select(CuotaGeminiGlobal)
            .where(CuotaGeminiGlobal.id == 1)
            .with_for_update()
        )
        cuota = res.scalar_one()
        cuota.ultima_verificacion = ahora
        cuota.ultimo_codigo_http = codigo_http
        cuota.actualizado_en = ahora
        if exitoso:
            cuota.ultimo_exito = ahora
            cuota.ultimo_error = None
            cuota.cooldown_hasta = None
        else:
            cuota.ultimo_error = (error or "Error no especificado")[:300]
            if retry_after_segundos > 0:
                nuevo_cooldown = ahora + timedelta(seconds=retry_after_segundos)
                if cuota.cooldown_hasta is None or nuevo_cooldown > cuota.cooldown_hasta:
                    cuota.cooldown_hasta = nuevo_cooldown
        await self.session.flush()

    async def obtener_estado_externo(self) -> dict[str, Any] | None:
        """Lee el estado externo compartido sin adquirir un slot de cuota."""
        res = await self.session.execute(
            select(CuotaGeminiGlobal).where(CuotaGeminiGlobal.id == 1)
        )
        cuota = res.scalar_one_or_none()
        if cuota is None:
            return None
        ahora = datetime.now(timezone.utc)
        return {
            "ultima_verificacion": cuota.ultima_verificacion,
            "ultimo_exito": cuota.ultimo_exito,
            "ultimo_codigo_http": cuota.ultimo_codigo_http,
            "ultimo_error": cuota.ultimo_error,
            "cooldown_segundos": (
                max(0, int((cuota.cooldown_hasta - ahora).total_seconds()) + 1)
                if cuota.cooldown_hasta and cuota.cooldown_hasta > ahora
                else 0
            ),
        }

    async def obtener_metricas_actuales(self) -> Tuple[int, int]:
        """Obtiene las solicitudes de hoy y del minuto actual sin bloquear."""
        ahora_epoch_minuto = int(time.time() // 60)
        hoy = date.today()

        stmt = select(CuotaGeminiGlobal).where(CuotaGeminiGlobal.id == 1)
        res = await self.session.execute(stmt)
        cuota = res.scalar_one_or_none()

        if not cuota:
            return (0, 0)

        sol_hoy = cuota.solicitudes_hoy if cuota.fecha == hoy else 0
        sol_min = cuota.solicitudes_minuto if cuota.minuto_epoch == ahora_epoch_minuto else 0
        return (sol_hoy, sol_min)
