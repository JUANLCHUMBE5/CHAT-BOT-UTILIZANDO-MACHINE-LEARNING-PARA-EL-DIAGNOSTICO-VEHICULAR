"""Replay local real con red limitada a Gemini/Groq y estado solo en memoria.

No importa el webhook, no inicia workers ni usa repositorios PostgreSQL.
Produce un JSON de evidencia técnica, nunca registros oficiales de tesis.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import json
import os
import socket
import sys
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env", override=True)
os.environ.update(DATABASE_ENABLED="false", DATABASE_REQUIRED="false", TEST_DATABASE_URL="")
import src.config_bootstrap as bootstrap

bootstrap.cargar_variables_entorno = lambda *a, **k: False

HOSTS = {"generativelanguage.googleapis.com", "api.groq.com"}
PERMITTED_IPS = {
    item[4][0]
    for host in HOSTS
    for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
}
PERMITTED_ENDPOINTS = {(ip, 443) for ip in PERMITTED_IPS}
NETWORK = []


def socket_audit(event, args):
    if event == "socket.connect":
        address = args[1]
        if not isinstance(address, tuple) or (address[0], address[1]) not in PERMITTED_ENDPOINTS:
            NETWORK.append({"blocked": True, "kind": "socket"})
            raise RuntimeError("Red fuera de Gemini/Groq bloqueada por el replay aislado")


import requests

# Respetar el proxy HTTPS ya configurado en el entorno, si existe. El guard
# HTTP sigue comprobando el destino final, incluidos redirects y Meta.
for proxy in set(requests.utils.get_environ_proxies("https://api.groq.com").values()):
    parsed = urlparse(proxy)
    if parsed.hostname:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        PERMITTED_ENDPOINTS.update(
            (item[4][0], port) for item in socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
        )

original_send = requests.Session.send


def guarded_send(self, request, **kwargs):
    url = urlparse(request.url)
    if url.scheme != "https" or url.hostname not in HOSTS:
        NETWORK.append({"blocked": True, "kind": "http"})
        raise RuntimeError("Destino HTTP no permitido en prueba aislada")
    kwargs["allow_redirects"] = False
    started = time.perf_counter()
    record = {"provider": "gemini" if url.hostname.startswith("generative") else "groq"}
    NETWORK.append(record)
    try:
        response = original_send(self, request, **kwargs)
        record["http"] = response.status_code
        return response
    except Exception as exc:
        record["error_type"] = type(exc).__name__
        raise
    finally:
        record["duration_ms"] = round((time.perf_counter() - started) * 1000)


requests.Session.send = guarded_send

from src.config import settings
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.diagnostico.response_generator import generar_respuesta_con_metadatos
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.llm.groq_client import generar_respuesta_groq

settings.database.enabled = False
settings.database.required = False


def fingerprints():
    paths = [ROOT / ".env"]
    paths += list((ROOT / "machine_learning/models").rglob("*.pkl"))
    paths += list((ROOT / "machine_learning/models").rglob("*.joblib"))
    paths += list((ROOT / "machine_learning/manuals/candidates/v1/indexes").glob("*.index"))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


async def main():
    # El loop de Windows crea su socketpair interno antes de activar el cerrojo.
    sys.addaudithook(socket_audit)
    before = fingerprints()
    rows = defaultdict(list)
    with Path(sys.argv[1]).open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            rows[int(row["caso_id"])].append(row)
    gestor = GestorDiagnostico()
    # Evitar reintentos HTTP ocultos: se observa una sola solicitud por intento.
    gestor._http_session.mount("https://", requests.adapters.HTTPAdapter(max_retries=0))
    output = {
        "local_only": True, "database_enabled": False, "meta_whatsapp_sent": 0,
        "gemini_key_present": bool(settings.gemini_api_key),
        "groq_key_present": bool(settings.groq_api_key),
        "gemini_model": settings.gemini_model, "groq_model": settings.groq_model,
        "cases": [],
    }
    # Sonda independiente de Groq: el flujo normal solo lo usa como fallback.
    try:
        _, metadata = generar_respuesta_groq(
            "Responde en español en una frase: ante mezcla pobre con MAF irregular, "
            "indica comprobar conector y lectura MAF; no confirmes una falla.",
        )
        output["groq_probe"] = {"used": metadata.get("usado"), "model": metadata.get("modelo")}
    except Exception as exc:
        output["groq_probe"] = {"error_type": type(exc).__name__}
    # Identificar disponibilidad real sin cambiar .env ni producción.
    model_response = requests.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {settings.groq_api_key}"}, timeout=12,
    )
    output["groq_models_http"] = model_response.status_code
    available = []
    if model_response.status_code == 200:
        available = [item["id"] for item in model_response.json().get("data", [])]
    output["groq_available_model_ids"] = available
    candidate = next((m for m in (
        "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "openai/gpt-oss-20b",
    ) if m in available), None)
    if candidate:
        settings.groq_model = candidate
    output["groq_sandbox_model"] = settings.groq_model
    key_original = gestor.api_key
    gestor.api_key = ""
    try:
        _, metadata = generar_respuesta_con_metadatos(
            gestor, "Mezcla pobre; se reporta caudal insuficiente de inyectores.",
            "Inyectores en evaluación, no confirmados", "", proveedor="web",
        )
        output["fallback_gemini_off_sandbox"] = metadata
    finally:
        gestor.api_key = key_original
    for case_id, case_rows in sorted(rows.items()):
        flow = OrquestadorConversacion(InMemoryConversationRepository())
        session = f"isolated-alex-{case_id}-{time.time_ns()}"
        case = {"id": case_id, "name": case_rows[0]["nombre_caso"],
                "expected_system": case_rows[0]["sistema_esperado"],
                "criterion": case_rows[0]["criterio_ok"], "turns": []}
        for row in sorted(case_rows, key=lambda r: int(r["turno"])):
            start_http = len(NETWORK)
            started = time.perf_counter()
            try:
                result = await flow.procesar_turno(
                    session, row["texto"], gestor, placa=row["placa_ficticia"],
                    marca_modelo=row["vehiculo"], proveedor="web",
                    diferir_encolado_persistente=False,
                )
                state = result.get("estado")
                dto = result.get("dto")
                case["turns"].append({
                    "turn": int(row["turno"]), "input": row["texto"],
                    "response": result.get("respuesta_texto", ""),
                    "system": state.active_system if state else None,
                    "decision": result.get("decision"), "status": result.get("status"),
                    "top3": [dict(h) for h in state.top3_actual] if state else [],
                    "discarded": list(state.hipotesis_descartadas) if state else [],
                    "facts": list(state.hechos) if state else [],
                    "llm_used": bool(dto and dto.llm_usado),
                    "llm_model": dto.llm_modelo if dto else None,
                    "limited": dto.respuesta_limitada if dto else None,
                    "pipeline_response": dto.respuesta_texto if dto else None,
                    "ml_original": dto.diagnostico_ml if dto else None,
                    "shown_hypothesis": state.falla_principal if state else None,
                    "questions": [dict(p) for p in state.preguntas_realizadas] if state else [],
                    "rag_title": dto.titulo_manual if dto else None,
                    "rag_context_present": bool(dto and dto.contexto_manual),
                    "ml_time_ms": dto.tiempo_ml_ms if dto else None,
                    "rag_time_ms": dto.tiempo_rag_ms if dto else None,
                    "llm_time_ms": dto.tiempo_llm_ms if dto else None,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000),
                    "network": NETWORK[start_http:],
                })
            except Exception as exc:
                case["turns"].append({"turn": int(row["turno"]), "input": row["texto"],
                                      "error_type": type(exc).__name__, "network": NETWORK[start_http:]})
            print(f"CASE {case_id} TURN {row['turno']} DONE", flush=True)
        output["cases"].append(case)
    output["network"] = NETWORK
    output["protected_files_unchanged"] = before == fingerprints()
    target = ROOT / "docs/auditorias/local_alex_corregido_live_20261006_v3.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"REPORT={target}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
