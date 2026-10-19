"""Sonda adicional de salida real del worker; transporte WhatsApp sustituido."""

import asyncio
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import uuid

ROOT = Path(__file__).resolve().parents[3]
RESULT = (ROOT / sys.argv[1]).resolve()
RESULT.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location(
    "audit_runner", ROOT / "scripts/experiments/rag03g/ejecutar.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
runner.DB = "postgresql+asyncpg://carbot_app:isolated_rag03i_tests_only@127.0.0.1:55439/carbot_rag03i_e2e_test"
runner.entorno(RESULT, True)
os.environ["REDIS_URL"] = "redis://127.0.0.1:56389/4"
os.environ["RATE_LIMIT_STORAGE_URI"] = "redis://127.0.0.1:56389/5"


async def main():
    import asyncpg
    import httpx
    from fastapi import FastAPI
    from src.application.jobs.system_worker import SystemWorker
    from src.core.gestor_diagnostico import GestorDiagnostico
    from src.core.gemini_queue.db_persistence import (
        procesar_siguiente_entrega_whatsapp,
        whatsapp_provider_service,
    )
    from src.interfaces.api.v1.endpoints.webhook import router
    from src.infrastructure.database.connection import cerrar_conexion
    from src.config import settings

    token = settings.meta_access_token
    token = token.get_secret_value() if hasattr(token, "get_secret_value") else token
    assert not token and runner.DB.endswith("_test")
    spec = importlib.util.spec_from_file_location(
        "e2e_helpers", ROOT / "backend/scripts/e2e/run_stack_validation.py"
    )
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    db = await asyncpg.connect(
        runner.DB.replace("postgresql+asyncpg://", "postgresql://")
    )
    captured = []

    async def fake(proveedor, destino, texto):
        captured.append(texto)
        return SimpleNamespace(
            exitoso=True,
            id_externo="audit_" + uuid.uuid4().hex,
            error=None,
            reintentable=False,
        )

    original = whatsapp_provider_service.enviar
    whatsapp_provider_service.enviar = fake
    g = GestorDiagnostico()
    worker = SystemWorker(g)
    worker.COLAS = ("diagnosticos",)
    app = FastAPI()
    app.state.gestor_diagnostico = g
    app.include_router(router, prefix="/api/v1/webhook")
    evidence = []
    turns = [
        "Ahora otro carro: Toyota Yaris 2018 gasolina placa T000-303, ratea en ralentí",
        "¿Qué vehículo recuerdas? La temperatura está en zona roja y sale vapor.",
        "¿Cómo compruebo el disco de freno con reloj comparador paso a paso?",
    ]
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            for text in turns:
                msg = "audit_h_" + uuid.uuid4().hex
                http = await helpers._send(
                    client, msg, "51980000001", "E2E_PHONE_A", text
                )
                row = await db.fetchrow(
                    "select id from trabajos_sistema where clave_idempotencia=$1",
                    "meta:" + msg,
                )
                assert row
                start = len(captured)
                assert await worker.procesar_siguiente()
                for _ in range(20):
                    if not await procesar_siguiente_entrega_whatsapp():
                        break
                job = await db.fetchrow(
                    "select estado,error_ultimo,resultado_resumen from trabajos_sistema where id=$1",
                    row["id"],
                )
                evidence.append(
                    dict(
                        input=text, http=http, job=dict(job), captured=captured[start:]
                    )
                )
                (RESULT / "resultado.json").write_text(
                    json.dumps(evidence, ensure_ascii=False, indent=2, default=str),
                    encoding="utf-8",
                )
                assert job["estado"] == "completado" and captured[start:]
                if "zona roja" in text:
                    final = " ".join(captured[start:]).lower()
                    assert "motor" in final and any(
                        p in final for p in ("det", "apaga")
                    )
                    assert "no abras" in final or "no abra" in final
                assert "0.05" not in " ".join(captured[start:])

        print("3 turnos del webhook y worker capturados para revision de contenido")
    finally:
        whatsapp_provider_service.enviar = original
        if worker._redis:
            await worker._redis.aclose()
        await db.close()
        await cerrar_conexion()


asyncio.run(main())
