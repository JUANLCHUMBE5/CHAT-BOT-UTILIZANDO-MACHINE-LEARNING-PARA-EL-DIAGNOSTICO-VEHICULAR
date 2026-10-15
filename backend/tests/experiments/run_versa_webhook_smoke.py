"""Ejecuta el smoke webhook de Versa en la imagen runtime, sin instalar pytest."""

import asyncio
import sys
import types
from pathlib import Path


class _Marks:
    @staticmethod
    def anyio(function):
        return function

    @staticmethod
    def parametrize(*_args, **_kwargs):
        return lambda function: function


sys.modules["pytest"] = types.SimpleNamespace(mark=_Marks())
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_gate_placa_aislado import (  # noqa: E402
    WEBHOOK_TRACE,
    test_placa_sintoma_cancelar_nueva_placa_sin_bd_ni_envio,
    test_versa_webhook_placa_y_contexto_llegan_a_diagnostico_sin_meta,
)


class _MonkeyPatch:
    @staticmethod
    def setattr(target, name, value):
        setattr(target, name, value)


print("START_MAZDA_WEBHOOK_1", flush=True)
asyncio.run(test_placa_sintoma_cancelar_nueva_placa_sin_bd_ni_envio(
    _MonkeyPatch(), "El auto recalienta",
))
print("RAG_MAZDA_WEBHOOK", WEBHOOK_TRACE)
print("START_MAZDA_WEBHOOK_2", flush=True)
asyncio.run(test_placa_sintoma_cancelar_nueva_placa_sin_bd_ni_envio(
    _MonkeyPatch(), "El motor se calienta y pierde refrigerante",
))
print("RAG_MAZDA_WEBHOOK", WEBHOOK_TRACE)
print("START_VERSA_WEBHOOK", flush=True)
asyncio.run(test_versa_webhook_placa_y_contexto_llegan_a_diagnostico_sin_meta(_MonkeyPatch()))
print("RAG_VERSA_WEBHOOK", WEBHOOK_TRACE)
print("WEBHOOK_VERSA_SMOKE_OK")
