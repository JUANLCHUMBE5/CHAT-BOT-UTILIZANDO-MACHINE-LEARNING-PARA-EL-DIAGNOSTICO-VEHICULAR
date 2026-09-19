"""Pruebas unitarias de privacidad y despacho de la cola general."""

import json

import pytest

from src.application.jobs.system_worker import SystemWorker
from src.core.security import cifrar_texto_reversible
from src.infrastructure.database.models.jobs import TrabajoSistema
from src.infrastructure.database.repositories.trabajo_sistema_repository import TrabajoSistemaRepository


def test_payload_trabajo_se_guarda_cifrado_y_se_recupera_en_memoria():
    payload = {"remitente": "+51987654321", "texto_cliente": "el motor falla"}
    cifrado = cifrar_texto_reversible(json.dumps(payload))
    trabajo = TrabajoSistema(
        tipo="webhook_mensaje",
        cola="diagnosticos",
        payload_cifrado=cifrado,
    )

    assert "+51987654321" not in trabajo.payload_cifrado
    assert TrabajoSistemaRepository(None).obtener_payload(trabajo) == payload  # type: ignore[arg-type]


@pytest.mark.anyio
async def test_worker_despacha_webhook_sin_exponer_payload(monkeypatch):
    recibido = {}

    class WebhookFalso:
        def __init__(self, gestor):
            self.gestor = gestor

        async def procesar_mensaje(self, **payload):
            recibido.update(payload)
            return {"status": "completado", "tiempo_ms": 12}

    monkeypatch.setattr("src.application.jobs.system_worker.WebhookService", WebhookFalso)
    worker = SystemWorker(gestor=object())  # type: ignore[arg-type]
    resumen = await worker._procesar(
        "webhook_mensaje",
        {"remitente": "+51987654321", "meta_message_id": "wamid-test"},
    )

    assert recibido["meta_message_id"] == "wamid-test"
    assert json.loads(resumen)["status"] == "completado"
