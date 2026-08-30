"""Bloqueo progresivo de intentos de autenticación fallidos."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import time
from typing import Any

from src.config import settings


class LoginAttemptStore:
    def __init__(self) -> None:
        self._local: dict[str, tuple[int, int]] = {}
        self._lock = asyncio.Lock()
        self._redis: Any = None

    def clave(self, username: str, ip: str) -> str:
        secreto = (settings.privacy_secret_key or settings.jwt_secret_key or "local-only").encode()
        dato = f"{username.strip().lower()}|{ip}".encode()
        return hmac.new(secreto, dato, hashlib.sha256).hexdigest()

    def _usa_redis(self) -> bool:
        return settings.rate_limit_storage_uri.startswith(("redis://", "rediss://"))

    def _cliente_redis(self):
        if self._redis is None:
            from redis.asyncio import Redis

            self._redis = Redis.from_url(settings.rate_limit_storage_uri, decode_responses=True)
        return self._redis

    async def permitido(self, clave: str) -> bool:
        if self._usa_redis():
            valor = await self._cliente_redis().get(f"carbot:login:{clave}")
            return int(valor or 0) < settings.login_max_failed_attempts
        async with self._lock:
            intentos, expira = self._local.get(clave, (0, 0))
            if expira <= int(time.time()):
                self._local.pop(clave, None)
                return True
            return intentos < settings.login_max_failed_attempts

    async def registrar_fallo(self, clave: str) -> None:
        if self._usa_redis():
            redis = self._cliente_redis()
            key = f"carbot:login:{clave}"
            async with redis.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, settings.login_lockout_seconds)
                await pipe.execute()
            return
        async with self._lock:
            intentos, _ = self._local.get(clave, (0, 0))
            self._local[clave] = (
                intentos + 1,
                int(time.time()) + settings.login_lockout_seconds,
            )

    async def limpiar(self, clave: str) -> None:
        if self._usa_redis():
            await self._cliente_redis().delete(f"carbot:login:{clave}")
            return
        async with self._lock:
            self._local.pop(clave, None)

    def reiniciar_local(self) -> None:
        self._local.clear()


login_attempt_store = LoginAttemptStore()
