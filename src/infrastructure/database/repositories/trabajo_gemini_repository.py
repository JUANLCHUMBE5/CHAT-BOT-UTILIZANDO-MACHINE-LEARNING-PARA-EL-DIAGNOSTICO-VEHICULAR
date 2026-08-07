"""Repositorio para la persistencia, consumo seguro y transiciones de estado de trabajos_gemini en PostgreSQL."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Sequence
import uuid

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import cifrar_texto_reversible, descifrar_texto_reversible
from src.infrastructure.database.models.jobs import TrabajoGemini


class TrabajoGeminiRepository:
    """Acceso a datos asíncrono para la cola persistente de trabajos Gemini."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def crear_trabajo(
        self,
        sintoma: str,
        diagnostico_ml: str,
        confianza_ml: Optional[float | Decimal] = None,
        contexto_manual: Optional[str] = None,
        titulo_manual: Optional[str] = None,
        requiere_revision_humana: bool = False,
        remitente: Optional[str] = None,
        proveedor: str = "meta",
        taller_id: Optional[uuid.UUID] = None,
        usuario_id: Optional[uuid.UUID] = None,
        conversacion_id: Optional[uuid.UUID] = None,
        diagnostico_id: Optional[uuid.UUID] = None,
        trabajo_id: Optional[uuid.UUID] = None,
    ) -> TrabajoGemini:
        """Crea un nuevo trabajo persistente cifrando el remitente para proteger la privacidad."""
        conf_decimal = Decimal(str(round(float(confianza_ml), 4))) if confianza_ml is not None else None
        remitente_cifrado = cifrar_texto_reversible(remitente) if remitente else None

        trabajo = TrabajoGemini(
            id=trabajo_id or uuid.uuid4(),
            diagnostico_id=diagnostico_id,
            taller_id=taller_id,
            usuario_id=usuario_id,
            conversacion_id=conversacion_id,
            proveedor=proveedor or "meta",
            remitente_cifrado=remitente_cifrado,
            sintoma=sintoma,
            diagnostico_ml=diagnostico_ml,
            confianza_ml=conf_decimal,
            contexto_manual=contexto_manual,
            titulo_manual=titulo_manual,
            requiere_revision_humana=requiere_revision_humana,
            estado="pendiente",
            intentos=0,
            disponible_desde=datetime.now(timezone.utc),
        )
        self.session.add(trabajo)
        await self.session.flush()
        return trabajo

    async def obtener_por_id(self, trabajo_id: uuid.UUID) -> Optional[TrabajoGemini]:
        """Obtiene un trabajo por su UUID."""
        stmt = select(TrabajoGemini).where(TrabajoGemini.id == trabajo_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def obtener_siguiente_pendiente_bloqueado(
        self, bloqueo_segundos: int = 60
    ) -> Optional[TrabajoGemini]:
        """
        Obtiene y bloquea de forma atómica el siguiente trabajo pendiente usando FOR UPDATE SKIP LOCKED.
        Evita colisiones entre múltiples workers en background.
        """
        ahora = datetime.now(timezone.utc)
        stmt = (
            select(TrabajoGemini)
            .where(
                TrabajoGemini.disponible_desde <= ahora,
                or_(
                    and_(
                        TrabajoGemini.estado.in_(("pendiente", "pendiente_reintento")),
                        or_(TrabajoGemini.bloqueado_hasta.is_(None), TrabajoGemini.bloqueado_hasta < ahora),
                    ),
                    and_(
                        TrabajoGemini.estado == "procesando",
                        TrabajoGemini.bloqueado_hasta < ahora,
                    ),
                ),
            )
            .order_by(TrabajoGemini.disponible_desde.asc(), TrabajoGemini.creado_en.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        res = await self.session.execute(stmt)
        trabajo = res.scalar_one_or_none()

        if trabajo:
            trabajo.estado = "procesando"
            trabajo.intentos += 1
            trabajo.bloqueado_hasta = ahora + timedelta(seconds=bloqueo_segundos)
            await self.session.flush()

        return trabajo

    async def marcar_completado(self, trabajo_id: uuid.UUID) -> bool:
        """Marca el trabajo como completado con éxito."""
        stmt = (
            update(TrabajoGemini)
            .where(TrabajoGemini.id == trabajo_id)
            .values(
                estado="completado",
                bloqueado_hasta=None,
                actualizado_en=datetime.now(timezone.utc),
            )
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0

    async def marcar_fallido(self, trabajo_id: uuid.UUID, error_mensaje: str) -> bool:
        """Marca el trabajo como fallido definitivamente."""
        stmt = (
            update(TrabajoGemini)
            .where(TrabajoGemini.id == trabajo_id)
            .values(
                estado="fallido",
                error_ultimo=error_mensaje[:1000] if error_mensaje else None,
                bloqueado_hasta=None,
                actualizado_en=datetime.now(timezone.utc),
            )
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0

    async def marcar_reintento(
        self, trabajo_id: uuid.UUID, espera_segundos: int = 15, error_mensaje: Optional[str] = None
    ) -> bool:
        """Marca el trabajo para reintento con backoff."""
        nueva_fecha = datetime.now(timezone.utc) + timedelta(seconds=espera_segundos)
        stmt = (
            update(TrabajoGemini)
            .where(TrabajoGemini.id == trabajo_id)
            .values(
                estado="pendiente_reintento",
                disponible_desde=nueva_fecha,
                bloqueado_hasta=None,
                error_ultimo=error_mensaje[:1000] if error_mensaje else None,
                actualizado_en=datetime.now(timezone.utc),
            )
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0

    async def posponer_por_cuota(
        self, trabajo_id: uuid.UUID, espera_segundos: int = 5, motivo: Optional[str] = None
    ) -> bool:
        """Devuelve un trabajo a espera sin cobrar un intento de API no realizado."""
        nueva_fecha = datetime.now(timezone.utc) + timedelta(seconds=espera_segundos)
        stmt = (
            update(TrabajoGemini)
            .where(TrabajoGemini.id == trabajo_id)
            .values(
                estado="pendiente_reintento",
                intentos=TrabajoGemini.intentos - 1,
                disponible_desde=nueva_fecha,
                bloqueado_hasta=None,
                error_ultimo=motivo[:1000] if motivo else None,
                actualizado_en=datetime.now(timezone.utc),
            )
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0

    async def listar_pendientes(self, limite: int = 50) -> Sequence[TrabajoGemini]:
        """Lista los trabajos pendientes o en reintento."""
        stmt = (
            select(TrabajoGemini)
            .where(TrabajoGemini.estado.in_(("pendiente", "pendiente_reintento", "procesando")))
            .order_by(TrabajoGemini.creado_en.asc())
            .limit(limite)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()

    def descifrar_remitente(self, trabajo: TrabajoGemini) -> Optional[str]:
        """Descifra en memoria el número del remitente para su entrega."""
        if not trabajo.remitente_cifrado:
            return None
        return descifrar_texto_reversible(trabajo.remitente_cifrado)
