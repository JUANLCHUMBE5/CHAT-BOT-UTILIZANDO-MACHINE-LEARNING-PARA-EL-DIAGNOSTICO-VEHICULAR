"""Revocación de access tokens JWT hasta su vencimiento natural."""

from __future__ import annotations

import threading
import time
from typing import Any

from src.config import settings


class AccessTokenStore:
    """Mantiene una lista de JTI revocados en Redis o en memoria para pruebas."""

    def __init__(self) -> None:
        self._local: dict[str, int] = {}
        self._lock = threading.RLock()
        self._redis: Any = None

    def _usa_redis(self) -> bool:
        return settings.rate_limit_storage_uri.startswith(("redis://", "rediss://"))

    def _cliente_redis(self):
        if self._redis is None:
            from redis import Redis

            self._redis = Redis.from_url(settings.rate_limit_storage_uri, decode_responses=True)
        return self._redis

    @staticmethod
    def _datos(payload: dict[str, Any]) -> tuple[str, int]:
        jti = str(payload.get("jti", ""))
        expiracion = int(payload.get("exp", 0))
        if not jti or expiracion <= int(time.time()):
            raise ValueError("Access token sin identificador o vencido.")
        return jti, expiracion

    def revocar(self, payload: dict[str, Any]) -> None:
        jti, expiracion = self._datos(payload)
        ttl = max(1, expiracion - int(time.time()))
        if self._usa_redis():
            self._cliente_redis().set(f"carbot:access:revoked:{jti}", "1", ex=ttl)
            return
        with self._lock:
            self._limpiar_local()
            self._local[jti] = expiracion

    def esta_revocado(self, payload: dict[str, Any]) -> bool:
        jti = str(payload.get("jti", ""))
        if not jti:
            return True
        if self._usa_redis():
            return bool(self._cliente_redis().exists(f"carbot:access:revoked:{jti}"))
        with self._lock:
            self._limpiar_local()
            return jti in self._local

    def _limpiar_local(self) -> None:
        ahora = int(time.time())
        for jti in [clave for clave, exp in self._local.items() if exp <= ahora]:
            self._local.pop(jti, None)

    def reiniciar_local(self) -> None:
        with self._lock:
            self._local.clear()


access_token_store = AccessTokenStore()
