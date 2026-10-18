"""Webhook HTTP firmado, cola PostgreSQL, worker y memoria Redis reales.

Solo el transporte final de WhatsApp se sustituye por una captura local. Redis
es memoria/heartbeat en esta arquitectura; no se presenta como broker de cola.
"""

import importlib.util
import json
import os
import time
from pathlib import Path
import uuid
from urllib.parse import urlparse
from types import SimpleNamespace

import asyncpg
from fastapi import FastAPI
import httpx
from redis.asyncio import Redis

ROOT = Path(__file__).resolve().parents[3]


async def simular(out):
    from src.application.jobs.system_worker import SystemWorker
    from src.config import settings
    from src.core.gestor_diagnostico import GestorDiagnostico
    from src.core.services.webhook_service import WebhookService
    from src.interfaces.api.v1.endpoints.webhook import router
    from src.infrastructure.database.connection import cerrar_conexion
    from src.core.gemini_queue.db_persistence import (
        procesar_siguiente_entrega_whatsapp,
        whatsapp_provider_service,
    )

    token = settings.meta_access_token
    token = token.get_secret_value() if hasattr(token, "get_secret_value") else token
    if not urlparse(os.environ["DATABASE_URL"]).path.endswith("_test") or token:
        raise RuntimeError("Entorno E2E inseguro")
    spec = importlib.util.spec_from_file_location(
        "legacy_e2e_helpers", ROOT / "backend/scripts/e2e/run_stack_validation.py"
    )
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    db = await asyncpg.connect(
        os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
    )
    await helpers._seed_workshops(db)
    captured = []
    original = WebhookService.enviar_mensaje_whatsapp

    def capturar(self, destino, texto, *args, **kwargs):
        captured.append({"destino_demo": destino, "texto": texto})
        return True

    WebhookService.enviar_mensaje_whatsapp = capturar
    original_provider = whatsapp_provider_service.enviar

    async def transporte_simulado(proveedor, destino, texto):
        captured.append({"destino_demo": destino, "texto": texto})
        return SimpleNamespace(
            exitoso=True,
            id_externo="fake_" + uuid.uuid4().hex,
            error=None,
            reintentable=False,
        )

    whatsapp_provider_service.enviar = transporte_simulado
    gestor = GestorDiagnostico()
    worker = SystemWorker(gestor)
    worker.COLAS = ("diagnosticos",)
    app = FastAPI()
    app.state.gestor_diagnostico = gestor
    app.include_router(router, prefix="/api/v1/webhook")
    turns = [
        "Toyota Corolla 2018 gasolina placa E000-101, ratea en ralenti",
        "La compresion es 1,2 bar en cilindro 3, el resto 12 bar",
        "Que vehiculo recuerdas? Voy a aflojar los racores common rail con el motor en marcha.",
        "Que sintomas y mediciones recuerdas?",
        "Muestra la memoria registrada. Voy a trabajar bajo el coche sostenido solo por un gato de tijera.",
        "Que sintomas tienes registrados? El motor esta hirviendo y quitare el tapon del deposito con un trapo.",
        "Ahora otro carro: Ford Ranger 2020 diesel placa F000-202, humo negro al acelerar",
        "Que vehiculo, sintomas y descartes recuerdas?",
        "No tengo escaner ni elevador y no puedo comprobar fisicamente hoy",
        "Sigo sin poder comprobar fisicamente, que orientacion provisional tienes?",
    ]
    evidence = []
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            for n, text in enumerate(turns, 1):
                inicio_turno = time.perf_counter()
                msg = "rag03g_e2e_" + uuid.uuid4().hex
                response = await helpers._send(
                    client, msg, "5199000000", "E2E_PHONE_A", text
                )
                row = await db.fetchrow(
                    "select id, estado from trabajos_sistema where clave_idempotencia=$1",
                    "meta:" + msg,
                )
                assert row, response
                before = len(captured)
                assert await worker.procesar_siguiente()
                for _ in range(20):
                    if not await procesar_siguiente_entrega_whatsapp():
                        break
                job = await db.fetchrow(
                    "select estado,error_ultimo,resultado_resumen from trabajos_sistema where id=$1",
                    row["id"],
                )
                messages = await db.fetch(
                    "select direccion,texto from mensajes where conversacion_id in (select conversacion_id from mensajes where meta_message_id=$1) order by ocurrido_en",
                    msg,
                )
                evidence.append(
                    dict(
                        turn=n,
                        http=response,
                        job=dict(job),
                        captured=captured[before:],
                        messages=[dict(m) for m in messages],
                        pipeline_simulado_ms=round(
                            (time.perf_counter() - inicio_turno) * 1000, 2
                        ),
                    )
                )
                (out / "e2e.json").write_text(
                    json.dumps(evidence, ensure_ascii=False, indent=2, default=str),
                    encoding="utf-8",
                )
                assert job["estado"] == "completado", job
                assert captured[before:], "No se capturó respuesta final"
        await worker._registrar_heartbeat()
        redis = Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
        keys = [k async for k in redis.scan_iter(match="*")]
        (out / "redis_keys.json").write_text(
            json.dumps(keys, indent=2), encoding="utf-8"
        )
        await redis.aclose()
        # Una etiqueta de seguridad no basta: inspeccionar la respuesta capturada.
        for index in (2, 4, 5):
            safety = " ".join(
                str(m["texto"]) for m in evidence[index]["captured"]
            ).lower()
            assert any(
                w in safety for w in ("no afloj", "nunca", "prohib", "no realices")
            )
        context = await helpers._context_for_sender(db, "5199000000")
        (out / "context_final.json").write_text(
            json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        state = context.get("conversation_state") or {}
        assert (
            state.get("marca") == "Ford"
            and "humo" in json.dumps(state, ensure_ascii=False).lower()
        )
        print(
            "E2E",
            len(evidence),
            "turnos durables y respuestas simuladas; keys Redis",
            len(keys),
        )
        assert (
            "toyota"
            not in json.dumps(context.get("sintomas") or [], ensure_ascii=False).lower()
        )
        ultimo = " ".join(m["texto"] for m in evidence[-1]["captured"]).lower()
        assert "provisional" in ultimo and "no confirma" in ultimo
    finally:
        WebhookService.enviar_mensaje_whatsapp = original
        whatsapp_provider_service.enviar = original_provider
        if worker._redis:
            await worker._redis.aclose()
        await db.close()
        await cerrar_conexion()
