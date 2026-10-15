"""Tres hilos sintéticos en memoria; --live autoriza únicamente Gemini (sin Meta/BD)."""

import asyncio
import hashlib
import json
import os
import socket
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
LIVE = "--live" in sys.argv

from dotenv import load_dotenv

load_dotenv(ROOT / ".env", override=True)
os.environ.update(DATABASE_ENABLED="false", DATABASE_REQUIRED="false", TEST_DATABASE_URL="")
import src.config_bootstrap as bootstrap

bootstrap.cargar_variables_entorno = lambda *a, **k: False

import requests

HOST = "generativelanguage.googleapis.com"
ENDPOINTS = set()
if LIVE:
    ENDPOINTS.update((r[4][0], 443) for r in socket.getaddrinfo(HOST, 443))
    for proxy in requests.utils.get_environ_proxies(f"https://{HOST}").values():
        parsed = urlparse(proxy)
        if parsed.hostname:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            ENDPOINTS.update((r[4][0], port) for r in socket.getaddrinfo(parsed.hostname, port))

NETWORK = []
SEND = requests.Session.send


def guarded_send(self, request, **kwargs):
    url = urlparse(request.url)
    if not LIVE or url.scheme != "https" or url.hostname != HOST or len(NETWORK) >= 15:
        raise RuntimeError("Destino o cuota no autorizado en sandbox")
    kwargs["allow_redirects"] = False
    record = {"provider": "gemini"}
    NETWORK.append(record)
    try:
        response = SEND(self, request, **kwargs)
        record["http"] = response.status_code
        return response
    except Exception as exc:
        record["error"] = type(exc).__name__
        raise


def audit(event, args):
    if event == "socket.connect":
        addr = args[1]
        if not isinstance(addr, tuple) or tuple(addr[:2]) not in ENDPOINTS:
            raise RuntimeError("Socket externo bloqueado por sandbox")


requests.Session.send = guarded_send

from src.config import settings
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.diagnostic_cache import diagnostico_cache
from src.core.gestor_diagnostico import GestorDiagnostico

settings.database.enabled = False
settings.database.required = False
settings.database.url = ""
settings.groq_api_key = ""
if not LIVE:
    settings.gemini_api_key = ""

MAZDA = ["El Mazda 3 empezó a recalentar.", "Es refrigeración, no es mezcla.",
         "El ventilador ya fue revisado y funciona."]
CASES = [
    ("Versa", "Nissan Versa 2016", [
        "Se prende el check y arroja mezcla pobre.", "Al acelerar y en caliente.",
        "No tengo DTC ni valores STFT/LTFT medidos todavía.",
        "Ya revisé el cuerpo de aceleración y está bien.",
        "Los injectores no inyectan lo suficiente.",
    ]),
    ("Mazda simple", "Mazda 3 2019", MAZDA),
    ("Mazda fuga", "Mazda 3 2019", MAZDA + ["Hay fuga de refrigerante y mancha en el piso."]),
]
if "--case" in sys.argv:
    selected = sys.argv[sys.argv.index("--case") + 1].casefold()
    CASES = [case for case in CASES if case[0].casefold() == selected]
    if not CASES:
        raise SystemExit("Caso de sandbox no reconocido")


def fingerprints():
    files = [ROOT / ".env"]
    for glob in ("machine_learning/models/**/*.pkl", "machine_learning/models/**/*.joblib",
                 "machine_learning/manuals/**/*.index"):
        files.extend(ROOT.glob(glob))
    return {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in files if f.is_file()}


async def main():
    sys.addaudithook(audit)  # Tras crear el loop de Windows, antes del gestor.
    before = fingerprints()
    manager = GestorDiagnostico()
    manager._registrar_en_tracker = lambda *a, **k: None
    manager._http_session.mount("https://", requests.adapters.HTTPAdapter(max_retries=0))
    if not LIVE:
        manager.api_key = ""
    captured = []
    original = manager._generar_respuesta_con_metadatos

    def observed(*args, **kwargs):
        record = {"query": kwargs.get("pregunta"),
                  "rag_chars": len(kwargs.get("contexto_manual", "")),
                  "rag_status": kwargs.get("titulo_manual"), "raw_llm": None}
        captured.append(record)
        text, meta = original(*args, **kwargs)
        record.update(raw_llm=text, metadata=meta)
        return text, meta

    manager._generar_respuesta_con_metadatos = observed
    output = {"scope": "LOCAL_SYNTHETIC_NOT_THESIS", "live": LIVE,
              "transport": "orchestrator_in_memory_not_webhook", "cases": [], "network": NETWORK}
    target = ROOT / "docs/auditorias" / f"fuga_llm_{'live' if LIVE else 'offline'}_{time.time_ns()}.json"

    def save():
        target.write_text(json.dumps(output, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    for index, (name, vehicle, messages) in enumerate(CASES):
        diagnostico_cache.limpiar()
        flow = OrquestadorConversacion(InMemoryConversationRepository())
        case = {"name": name, "turns": []}
        output["cases"].append(case)
        for turn, message in enumerate(messages, 1):
            if LIVE:
                await asyncio.sleep(6.1)
            n, c = len(NETWORK), len(captured)
            row = {"turn": turn, "input": message}
            try:
                result = await flow.procesar_turno(
                    f"sandbox-fuga-{index}", message, manager, placa=f"ZZZ{901 + index}",
                    marca_modelo=vehicle, proveedor="web", diferir_encolado_persistente=False,
                )
                state, dto = result.get("estado"), result.get("dto")
                row.update(final=result.get("respuesta_texto"), decision=result.get("decision"),
                           active_system=state.active_system if state else None,
                           rag_title=dto.titulo_manual if dto else None,
                           rag_recovered=bool(dto and dto.contexto_manual),
                           similarity=dto.similitud_rag if dto else None,
                           llm_used=bool(dto and dto.llm_usado),
                           limited=dto.respuesta_limitada if dto else None,
                           llm_calls=captured[c:], network=NETWORK[n:])
            except Exception as exc:
                row["error_type"] = type(exc).__name__
            case["turns"].append(row)
            save()
            print(f"{name} turn={turn} system={row.get('active_system')} calls={len(NETWORK)-n} "
                  f"error={row.get('error_type')}", flush=True)
    output["protected_files_unchanged"] = before == fingerprints()
    save()
    print(f"REPORT={target}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
