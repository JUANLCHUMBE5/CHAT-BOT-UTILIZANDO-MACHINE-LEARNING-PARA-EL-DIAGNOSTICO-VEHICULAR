"""
diagnostic_cache.py
Módulo de Caché en Memoria LRU de Alta Velocidad para Diagnósticos Vehiculares Frecuentes.
Permite responder en < 5ms a consultas idénticas o repetidas entre múltiples mecánicos,
ahorrando cuota de Gemini API y evitando embotellamientos en el taller.
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class EntradaCache:
    clave_hash: str
    valor: Any
    timestamp_creacion: float
    ttl_segundos: float

    def esta_expirada(self) -> bool:
        if self.ttl_segundos <= 0:
            return False
        return (time.time() - self.timestamp_creacion) > self.ttl_segundos


class DiagnosticoLRUCache:
    """
    Caché LRU thread-safe con expiración por TTL (Time-To-Live).
    Optimiza drásticamente la latencia para talleres con múltiples trabajadores.
    """

    def __init__(self, capacidad_maxima: int = 1000, ttl_default_segundos: float = 3600.0):
        self.capacidad_maxima = capacidad_maxima
        self.ttl_default_segundos = ttl_default_segundos
        self._cache: OrderedDict[str, EntradaCache] = OrderedDict()
        self._lock = threading.Lock()
        self._hits: int = 0
        self._misses: int = 0

    @staticmethod
    def generar_clave(sintoma: str, marca_modelo: str = "", placa: str = "") -> str:
        """Genera un hash SHA-256 normalizado para la clave de consulta."""
        normalizado = f"{sintoma.strip().lower()}|{marca_modelo.strip().lower()}"
        return hashlib.sha256(normalizado.encode("utf-8")).hexdigest()

    def obtener(self, clave_hash: str) -> Optional[Any]:
        """Obtiene un resultado de caché si existe y no ha expirado."""
        with self._lock:
            if clave_hash not in self._cache:
                self._misses += 1
                return None

            entrada = self._cache[clave_hash]
            if entrada.esta_expirada():
                del self._cache[clave_hash]
                self._misses += 1
                return None

            # Mover al final (más recientemente usado)
            self._cache.move_to_end(clave_hash)
            self._hits += 1
            return entrada.valor

    def guardar(self, clave_hash: str, valor: Any, ttl_segundos: Optional[float] = None) -> None:
        """Guarda un resultado en caché aplicando política de desalojo LRU."""
        ttl = ttl_segundos if ttl_segundos is not None else self.ttl_default_segundos
        with self._lock:
            if clave_hash in self._cache:
                self._cache.move_to_end(clave_hash)
            elif len(self._cache) >= self.capacidad_maxima:
                # Desalojar el elemento menos recientemente usado (primer elemento)
                self._cache.popitem(last=False)

            self._cache[clave_hash] = EntradaCache(
                clave_hash=clave_hash,
                valor=valor,
                timestamp_creacion=time.time(),
                ttl_segundos=ttl
            )

    def limpiar(self) -> None:
        """Limpia la caché por completo."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def obtener_metricas(self) -> dict[str, Any]:
        """Retorna estadísticas de rendimiento de la caché."""
        with self._lock:
            total = self._hits + self._misses
            tasa_acierto = (self._hits / total * 100.0) if total > 0 else 0.0
            return {
                "elementos_actuales": len(self._cache),
                "capacidad_maxima": self.capacidad_maxima,
                "hits": self._hits,
                "misses": self._misses,
                "tasa_acierto_pct": round(tasa_acierto, 2)
            }


# Instancia Singleton global para el backend
diagnostico_cache = DiagnosticoLRUCache(capacidad_maxima=2000, ttl_default_segundos=7200.0)
