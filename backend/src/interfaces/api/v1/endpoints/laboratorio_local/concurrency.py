"""Exclusión por propietario/sesión para el laboratorio de un solo proceso."""
import asyncio
from contextlib import asynccontextmanager
from threading import RLock

_registro = {}
_guardia = RLock()


@asynccontextmanager
async def turno_exclusivo(gestor, session_key: str):
    """Serializa el turno completo y el reinicio; libera registros al terminar.

    Los gestores ya están aislados por taller/usuario. No es un bloqueo
    distribuido: esta aplicación local usa un proceso y memoria local.
    """
    clave = (id(gestor), id(asyncio.get_running_loop()), session_key)
    with _guardia:
        entrada = _registro.setdefault(clave, [asyncio.Lock(), 0])
        entrada[1] += 1
    try:
        async with entrada[0]:
            yield
    finally:
        with _guardia:
            entrada[1] -= 1
            if entrada[1] == 0:
                del _registro[clave]
