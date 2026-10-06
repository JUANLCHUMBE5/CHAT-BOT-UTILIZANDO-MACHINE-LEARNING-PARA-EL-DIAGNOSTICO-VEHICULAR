"""Abstracciones e implementaciones de repositorio para persistencia de ConversationState."""

from __future__ import annotations

import asyncio
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional

from src.core.conversacion.models import ConversationState
from src.core.logger import logger
from src.infrastructure.database.connection import database_configurada, obtener_engine


class ConversationStateRepository(ABC):
    """Interfaz abstracta para el almacenamiento persistente de estados conversacionales."""

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[ConversationState]:
        """Recupera el estado conversacional activo por session_id."""
        raise NotImplementedError

    @abstractmethod
    async def save_session(self, session_id: str, state: ConversationState) -> None:
        """Guarda un estado conversacional nuevo."""
        raise NotImplementedError

    @abstractmethod
    async def update_session(self, session_id: str, state: ConversationState) -> None:
        """Actualiza un estado conversacional existente."""
        raise NotImplementedError

    @abstractmethod
    async def close_session(self, session_id: str) -> None:
        """Cierra o elimina la sesión."""
        raise NotImplementedError

    @abstractmethod
    async def reset_session(self, session_id: str) -> ConversationState:
        """Reinicia el estado conversacional a valores limpios."""
        raise NotImplementedError

    @abstractmethod
    async def finalizar_caso(
        self, session_id: str, nuevo_case_id: Optional[str] = None
    ) -> ConversationState:
        """Finaliza formalmente el case_id activo y limpia hechos para el siguiente caso."""
        raise NotImplementedError


class InMemoryConversationRepository(ConversationStateRepository):
    """Almacenamiento en memoria thread-safe con expiración TTL."""

    def __init__(self, ttl_seconds: int = 1800):
        self._sesiones: Dict[str, ConversationState] = {}
        self.ttl_seconds = ttl_seconds
        self._lock = threading.RLock()

    def _limpiar_expiradas(self) -> None:
        ahora = time.time()
        expiradas = [
            sid for sid, s in self._sesiones.items()
            if (ahora - s.updated_at) > self.ttl_seconds
        ]
        for sid in expiradas:
            self._sesiones.pop(sid, None)

    async def get_session(self, session_id: str) -> Optional[ConversationState]:
        with self._lock:
            self._limpiar_expiradas()
            return self._sesiones.get(session_id)

    async def save_session(self, session_id: str, state: ConversationState) -> None:
        with self._lock:
            self._limpiar_expiradas()
            state.updated_at = time.time()
            self._sesiones[session_id] = state

    async def update_session(self, session_id: str, state: ConversationState) -> None:
        await self.save_session(session_id, state)

    async def close_session(self, session_id: str) -> None:
        with self._lock:
            self._sesiones.pop(session_id, None)

    async def reset_session(self, session_id: str) -> ConversationState:
        with self._lock:
            state = self._sesiones.get(session_id)
            if state:
                state.reiniciar()
            else:
                state = ConversationState(session_id=session_id)
                self._sesiones[session_id] = state
            return state

    async def finalizar_caso(
        self, session_id: str, nuevo_case_id: Optional[str] = None
    ) -> ConversationState:
        with self._lock:
            state = self._sesiones.get(session_id)
            if state:
                state.iniciar_nuevo_caso(nuevo_case_id)
            else:
                state = ConversationState(session_id=session_id)
                state.iniciar_nuevo_caso(nuevo_case_id)
            self._sesiones[session_id] = state
            return state


class PostgresConversationRepository(ConversationStateRepository):
    """Persistencia en PostgreSQL mediante el campo JSONB contexto de la tabla conversaciones."""

    def __init__(self, in_memory_fallback: Optional[InMemoryConversationRepository] = None):
        self._fallback = in_memory_fallback or InMemoryConversationRepository()

    async def get_session(self, session_id: str) -> Optional[ConversationState]:
        if not database_configurada():
            return await self._fallback.get_session(session_id)

        try:
            from sqlalchemy import select
            from sqlalchemy.ext.asyncio import AsyncSession

            from src.infrastructure.database.models.messaging import Conversacion

            engine = obtener_engine()
            async with AsyncSession(engine, expire_on_commit=False) as session:
                import uuid
                try:
                    conv_id = uuid.UUID(session_id)
                except ValueError:
                    # Si no es UUID válido de BD, usar fallback en memoria
                    return await self._fallback.get_session(session_id)

                res = await session.execute(
                    select(Conversacion.contexto).where(Conversacion.id == conv_id)
                )
                contexto = res.scalar_one_or_none()
                if contexto and isinstance(contexto, dict):
                    if contexto.get("caso_finalizado"):
                        # El caso fue cerrado formalmente: limpiar memoria para evitar contaminar
                        await self._fallback.close_session(session_id)
                        return None
                    if "conversation_state" in contexto and isinstance(contexto["conversation_state"], dict):
                        st = ConversationState.from_dict(contexto["conversation_state"])
                        st.session_id = session_id
                        placa = contexto.get("placa_posttest") or contexto.get("placa")
                        if placa and not st.placa:
                            st.placa = placa
                        return st
                    if "hechos" in contexto:
                        st = ConversationState.from_dict(contexto)
                        st.session_id = session_id
                        placa = contexto.get("placa_posttest") or contexto.get("placa")
                        if placa and not st.placa:
                            st.placa = placa
                        return st

                    # Caso con placa, datos del vehículo o case_id activo sin hechos serializados aún
                    placa = contexto.get("placa_posttest") or contexto.get("placa")
                    case_id = contexto.get("case_id")
                    perfil = contexto.get("perfil_vehiculo") or {}
                    if placa or case_id or perfil:
                        mem = await self._fallback.get_session(session_id)
                        if mem is not None:
                            if placa and not mem.placa:
                                mem.placa = placa
                            if case_id and not mem.case_id:
                                mem.case_id = case_id
                            return mem
                        st = ConversationState(session_id=session_id)
                        if case_id:
                            st.case_id = case_id
                        if placa:
                            st.placa = placa
                        if isinstance(perfil, dict):
                            st.marca = perfil.get("marca")
                            st.modelo = perfil.get("modelo")
                            st.anio = perfil.get("anio")
                        await self._fallback.save_session(session_id, st)
                        return st

                mem = await self._fallback.get_session(session_id)
                return mem
        except Exception as exc:
            logger.warning(f"[PostgresConversationRepository] Error al leer sesión {session_id}: {exc}")
            return await self._fallback.get_session(session_id)

    async def save_session(self, session_id: str, state: ConversationState) -> None:
        await self._fallback.save_session(session_id, state)
        if not database_configurada():
            return

        try:
            from sqlalchemy import select, update
            from sqlalchemy.ext.asyncio import AsyncSession

            from src.infrastructure.database.models.messaging import Conversacion

            engine = obtener_engine()
            async with AsyncSession(engine, expire_on_commit=False) as session:
                import uuid
                try:
                    conv_id = uuid.UUID(session_id)
                except ValueError:
                    return

                async def _ejecutar_guardado():
                    async with session.begin():
                        res = await session.execute(
                            select(Conversacion.contexto).where(Conversacion.id == conv_id)
                        )
                        ctx = dict(res.scalar_one_or_none() or {})
                        ctx["conversation_state"] = state.exportar_dict()
                        ctx["case_id"] = state.case_id
                        if state.placa:
                            ctx["placa"] = state.placa
                            ctx["placa_posttest"] = state.placa
                        await session.execute(
                            update(Conversacion)
                            .where(Conversacion.id == conv_id)
                            .values(contexto=ctx)
                        )

                await asyncio.wait_for(_ejecutar_guardado(), timeout=3.0)
        except asyncio.TimeoutError:
            logger.debug(f"[PostgresConversationRepository] Guardado en BD diferido para sesión {session_id}")
        except Exception as exc:
            logger.warning(f"[PostgresConversationRepository] Error al guardar sesión {session_id}: {exc}")

    async def update_session(self, session_id: str, state: ConversationState) -> None:
        await self.save_session(session_id, state)

    async def close_session(self, session_id: str) -> None:
        await self._fallback.close_session(session_id)

    async def reset_session(self, session_id: str) -> ConversationState:
        state = await self._fallback.reset_session(session_id)
        await self.save_session(session_id, state)
        return state

    async def finalizar_caso(
        self, session_id: str, nuevo_case_id: Optional[str] = None
    ) -> ConversationState:
        state = await self._fallback.finalizar_caso(session_id, nuevo_case_id)
        if database_configurada():
            try:
                from sqlalchemy import select, update
                from sqlalchemy.ext.asyncio import AsyncSession

                from src.infrastructure.database.models.messaging import Conversacion

                engine = obtener_engine()
                async with AsyncSession(engine, expire_on_commit=False) as session:
                    import uuid
                    try:
                        conv_id = uuid.UUID(session_id)
                    except ValueError:
                        return state

                    async with session.begin():
                        res = await session.execute(
                            select(Conversacion.contexto).where(Conversacion.id == conv_id)
                        )
                        ctx = dict(res.scalar_one_or_none() or {})
                        ctx.pop("conversation_state", None)
                        ctx.pop("estado_conversacion", None)
                        ctx.pop("validacion_diagnostico", None)
                        ctx["caso_finalizado"] = True
                        ctx["case_id"] = state.case_id
                        await session.execute(
                            update(Conversacion)
                            .where(Conversacion.id == conv_id)
                            .values(contexto=ctx)
                        )
            except Exception as exc:
                logger.warning(f"[PostgresConversationRepository] Error al finalizar caso {session_id}: {exc}")
        return state
