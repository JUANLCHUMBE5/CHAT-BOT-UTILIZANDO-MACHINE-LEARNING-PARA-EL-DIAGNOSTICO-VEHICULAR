"""Registro de refresh tokens de un solo uso.

Redis se utiliza cuando ``RATE_LIMIT_STORAGE_URI`` apunta a Redis. El almacén
local existe únicamente para desarrollo y pruebas de un solo proceso.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from src.config import settings


class RefreshTokenStore:
    def __init__(self) -> None:
        self._local: dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._redis: Any = None

    def _usa_redis(self) -> bool:
        return settings.rate_limit_storage_uri.startswith(("redis://", "rediss://"))

    def _cliente_redis(self):
        if self._redis is None:
            from redis.asyncio import Redis

            self._redis = Redis.from_url(
                settings.rate_limit_storage_uri,
                decode_responses=True,
            )
        return self._redis

    @staticmethod
    def _datos(payload: dict[str, Any]) -> tuple[str, int]:
        jti = str(payload.get("jti", ""))
        expiracion = int(payload.get("exp", 0))
        if not jti or expiracion <= int(time.time()):
            raise ValueError("Refresh token sin identificador o vencido.")
        return jti, expiracion

    async def registrar(self, payload: dict[str, Any]) -> None:
        jti, expiracion = self._datos(payload)
        ttl = max(1, expiracion - int(time.time()))
        if self._usa_redis():
            await self._cliente_redis().set(f"carbot:refresh:{jti}", "active", ex=ttl)
            return
        async with self._lock:
            self._limpiar_local()
            self._local[jti] = expiracion

    async def rotar(
        self,
        anterior: dict[str, Any],
        nuevo: dict[str, Any],
    ) -> bool:
        jti_anterior, _ = self._datos(anterior)
        jti_nuevo, expiracion_nueva = self._datos(nuevo)
        ttl = max(1, expiracion_nueva - int(time.time()))
        if self._usa_redis():
            script = """
            if redis.call('GET', KEYS[1]) == 'active' then
                redis.call('DEL', KEYS[1])
                redis.call('SET', KEYS[2], 'active', 'EX', ARGV[1])
                return 1
            end
            return 0
            """
            resultado = await self._cliente_redis().eval(
                script,
                2,
                f"carbot:refresh:{jti_anterior}",
                f"carbot:refresh:{jti_nuevo}",
                ttl,
            )
            return bool(resultado)
        async with self._lock:
            self._limpiar_local()
            if self._local.pop(jti_anterior, None) is None:
                return False
            self._local[jti_nuevo] = expiracion_nueva
            return True

    async def revocar(self, payload: dict[str, Any]) -> None:
        jti, _ = self._datos(payload)
        if self._usa_redis():
            await self._cliente_redis().delete(f"carbot:refresh:{jti}")
            return
        async with self._lock:
            self._local.pop(jti, None)

    def _limpiar_local(self) -> None:
        ahora = int(time.time())
        expirados = [jti for jti, exp in self._local.items() if exp <= ahora]
        for jti in expirados:
            self._local.pop(jti, None)

    def reiniciar_local(self) -> None:
        self._local.clear()


refresh_token_store = RefreshTokenStore()
