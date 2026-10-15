"""Persistencia y recuperación de sesiones conversacionales REST entre reinicios.

Garantiza continuidad de contexto (case_id, síntomas, perfil y hechos técnicos)
en Redis y PostgreSQL con aislamiento estricto por taller y usuario.
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional

from src.core.logger import logger

_REDIS_CLIENT: Any = None
_REDIS_LOOP: Optional[asyncio.AbstractEventLoop] = None


def _obtener_redis_url() -> str:
    redis_url = os.getenv("REDIS_URL", "").strip()
    if redis_url.startswith(("redis://", "rediss://")):
        return redis_url
    from src.config import settings

    rate_uri = getattr(settings, "rate_limit_storage_uri", "").strip()
    if rate_uri.startswith(("redis://", "rediss://")):
        return rate_uri
    return ""


def _cliente_redis():
    global _REDIS_CLIENT, _REDIS_LOOP
    try:
        loop_actual = asyncio.get_running_loop()
    except RuntimeError:
        loop_actual = None

    if _REDIS_CLIENT is None or _REDIS_LOOP != loop_actual or (_REDIS_LOOP is not None and _REDIS_LOOP.is_closed()):
        url = _obtener_redis_url()
        if not url:
            return None
        try:
            from redis.asyncio import Redis

            _REDIS_CLIENT = Redis.from_url(url, decode_responses=True)
            _REDIS_LOOP = loop_actual
        except Exception as exc:
            logger.debug("[SessionPersistence] Redis no disponible: %s", exc)
            return None
    return _REDIS_CLIENT


async def recuperar_contexto_sesion_redis(sesion_efectiva: str) -> Optional[Dict[str, Any]]:
    """Recupera el contexto de sesión desde Redis si está disponible."""
    client = _cliente_redis()
    if client is None:
        return None
    try:
        raw = await asyncio.wait_for(client.get(f"carbot:rest:session:{sesion_efectiva}"), timeout=0.8)
        if raw:
            return json.loads(raw)
    except Exception as exc:
        logger.debug("[SessionPersistence] Error al leer sesión de Redis (%s): %s", sesion_efectiva, exc)
    return None


async def guardar_contexto_sesion_redis(
    sesion_efectiva: str, contexto: Dict[str, Any], ttl_segundos: int = 1800
) -> None:
    """Guarda el contexto de sesión en Redis con tiempo de expiración."""
    client = _cliente_redis()
    if client is None or not contexto:
        return
    try:
        raw = json.dumps(contexto, ensure_ascii=False)
        await asyncio.wait_for(client.set(f"carbot:rest:session:{sesion_efectiva}", raw, ex=ttl_segundos), timeout=0.8)
    except Exception as exc:
        logger.debug("[SessionPersistence] Error al persistir sesión en Redis (%s): %s", sesion_efectiva, exc)


async def sincronizar_sesion_desde_persistencia(
    gestor: Any,
    sesion_efectiva: str,
    contexto_db: Optional[Dict[str, Any]] = None,
) -> bool:
    """Restaura en gestor.session_manager el estado de la sesión si no existe en memoria."""
    if gestor.session_manager.obtener_sesion(sesion_efectiva) is not None:
        return True

    # 1. Intentar Redis primero para máxima velocidad
    ctx = await recuperar_contexto_sesion_redis(sesion_efectiva)

    # 2. Si no está en Redis, recuperar de PostgreSQL (contexto_db)
    if not ctx and contexto_db:
        sesiones_guardadas = contexto_db.get("sesiones")
        if isinstance(sesiones_guardadas, dict) and sesion_efectiva in sesiones_guardadas:
            ctx = sesiones_guardadas[sesion_efectiva]
        elif contexto_db.get("session_id") == sesion_efectiva:
            ctx = contexto_db

    if ctx and isinstance(ctx, dict):
        gestor.session_manager.cargar_contexto(sesion_efectiva, ctx)
        logger.info("[SessionPersistence] Sesión REST %s recuperada de persistencia.", sesion_efectiva)
        return True

    return False


async def persistir_sesion_en_almacenes(
    gestor: Any,
    sesion_efectiva: str,
    conversacion: Optional[Any] = None,
    case_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Exporta la sesión y la preserva simultáneamente en Redis y conversacion.contexto."""
    ctx = gestor.session_manager.exportar_contexto(sesion_efectiva)
    if not ctx:
        return None

    if case_id and not ctx.get("case_id"):
        ctx["case_id"] = case_id

    # 1. Persistir en Redis
    await guardar_contexto_sesion_redis(sesion_efectiva, ctx)

    # 2. Persistir en PostgreSQL a través de conversacion.contexto
    if conversacion is not None:
        contexto_actual = dict(conversacion.contexto or {})
        sesiones = dict(contexto_actual.get("sesiones") or {})
        sesiones[sesion_efectiva] = ctx
        contexto_actual["sesiones"] = sesiones
        if case_id:
            contexto_actual["case_id"] = case_id
        conversacion.contexto = contexto_actual

    return ctx
