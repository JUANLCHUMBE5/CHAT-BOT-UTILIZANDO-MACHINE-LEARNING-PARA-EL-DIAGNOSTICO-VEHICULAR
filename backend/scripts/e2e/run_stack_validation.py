"""Validación HTTP E2E de conversaciones aislada para Docker Compose en CI.

Los datos son sintéticos de regresión y no son evidencia de trabajo de campo.
El ejecutor no conoce ni carga credenciales de producción: exige que Gemini,
Groq y Meta estén deshabilitados antes de enviar los webhooks firmados de prueba.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import hmac
import json
import os
import re
import statistics
import time
import uuid
from pathlib import Path
from typing import Any

import asyncpg
import httpx

from src.core.conversacion.models import ConversationState
from tests.calidad_conversacional.casos_congelados import (
    CASOS_CONGELADOS,
    validar_casos_congelados,
)

API_URL = os.getenv("E2E_API_URL", "http://api:8000/api/v1/webhook/meta")
DATABASE_URL = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
META_SECRET = os.environ["META_APP_SECRET"]
ARTIFACT = Path("/artifacts/metricas_e2e.json")


def _require_safe_environment() -> None:
    forbidden = ("GEMINI_API_KEY", "GROQ_API_KEY", "META_ACCESS_TOKEN")
    configured = [key for key in forbidden if os.getenv(key)]
    if (
        configured
        or os.getenv("GROQ_CHAT_ENABLED", "").lower() != "false"
        or os.getenv("CARBOT_BLOCK_DOTENV", "").lower() != "true"
    ):
        raise RuntimeError(f"El entorno E2E no aisló proveedores externos: {configured}")


def _payload(message_id: str, sender: str, phone_id: str, text: str) -> bytes:
    return json.dumps(
        {
            "entry": [{"changes": [{"value": {
                "metadata": {"phone_number_id": phone_id},
                "contacts": [{"wa_id": sender, "profile": {"name": "E2E Mecánico"}}],
                "messages": [{"id": message_id, "from": sender, "type": "text", "text": {"body": text}}],
            }}]}]
        },
        separators=(",", ":"),
    ).encode("utf-8")


async def _send(client: httpx.AsyncClient, message_id: str, sender: str, phone_id: str, text: str) -> dict[str, Any]:
    raw = _payload(message_id, sender, phone_id, text)
    signature = "sha256=" + hmac.new(META_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    started = time.perf_counter()
    response = await client.post(
        API_URL,
        content=raw,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature},
        timeout=30,
    )
    if response.is_error:
        raise RuntimeError(
            f"Webhook E2E devolvió {response.status_code}: {response.text[:500]}"
        )
    body = response.json()
    body["latencia_http_ms"] = round((time.perf_counter() - started) * 1000, 2)
    return body


async def _wait_job(db: asyncpg.Connection, job_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        row = await db.fetchrow(
            """SELECT estado, error_ultimo, intentos, creado_en, iniciado_en, completado_en
                 FROM trabajos_sistema WHERE id = $1::uuid""",
            job_id,
        )
        if row and row["estado"] == "completado":
            return dict(row)
        if row and row["estado"] == "fallido":
            raise RuntimeError(f"Trabajo {job_id} falló: {row['error_ultimo']}")
        await asyncio.sleep(0.25)
    raise TimeoutError(f"El trabajo {job_id} no terminó en 180 segundos")


def _write_progress(turns: list[dict[str, Any]]) -> None:
    """Conserva trazabilidad incluso si falla un turno intermedio."""
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(
        json.dumps({"trazabilidad_turnos": turns}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


async def _seed_workshops(db: asyncpg.Connection) -> None:
    for suffix, workshop_id in (("A", "00000000-0000-0000-0000-0000000000a1"), ("B", "00000000-0000-0000-0000-0000000000b1")):
        await db.execute(
            """INSERT INTO talleres (id, nombre, telefono_id_meta, activo, creado_en, actualizado_en)
               VALUES ($1::uuid, $2, $3, true, now(), now())
               ON CONFLICT (telefono_id_meta) DO NOTHING""",
            workshop_id, f"Taller E2E {suffix}", f"E2E_PHONE_{suffix}",
        )

    mechanic_role = await db.fetchval("SELECT id FROM roles WHERE codigo = 'mecanico'")
    if mechanic_role is None:
        raise RuntimeError("La migración E2E no creó el rol mecanico")
    senders = {
        "E2E_PHONE_A": [*(f"51990000{index:02d}" for index in range(len(CASOS_CONGELADOS))), "51980000001", "51981111111"],
        "E2E_PHONE_B": ["51982222222"],
    }
    for phone_id, workshop_senders in senders.items():
        workshop_id = await db.fetchval("SELECT id FROM talleres WHERE telefono_id_meta = $1", phone_id)
        for sender in workshop_senders:
            identity = _identity_hash(sender)
            user_id = uuid.uuid5(uuid.NAMESPACE_URL, f"carbot-e2e:{sender}")
            await db.execute(
                """INSERT INTO usuarios
                   (id, taller_id, rol_id, nombres, username, whatsapp_hash, whatsapp_ultimos4, activo,
                    bloqueado, debe_cambiar_password, creado_en, actualizado_en)
                   VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, true, false, false, now(), now())
                   ON CONFLICT (whatsapp_hash) DO NOTHING""",
                str(user_id), workshop_id, mechanic_role, f"Mecánico E2E {sender[-4:]}",
                f"e2e_{sender}", identity, sender[-4:],
            )
            conversation_id = uuid.uuid5(uuid.NAMESPACE_URL, f"carbot-e2e-conversation:{sender}")
            plate = f"E{sender[-3:]}-101"
            await db.execute(
                """INSERT INTO conversaciones
                   (id, taller_id, usuario_id, canal, estado, iniciada_en, ultimo_mensaje_en,
                    ventana_servicio_hasta, contexto, creado_en, actualizado_en)
                   VALUES ($1::uuid, $2::uuid, $3::uuid, 'whatsapp', 'abierta', now(), now(),
                           now() + interval '24 hours', $4::jsonb, now(), now())
                   ON CONFLICT (id) DO NOTHING""",
                str(conversation_id), workshop_id, str(user_id),
                json.dumps({"placa": plate, "placa_posttest": plate}),
            )


def _identity_hash(sender: str) -> str:
    privacy = os.environ["PRIVACY_SECRET_KEY"].encode()
    normalized = "".join(char for char in sender if char.isdigit())
    return hmac.new(privacy, f"telefono:{normalized}".encode(), hashlib.sha256).hexdigest()


async def _context_for_sender(db: asyncpg.Connection, sender: str) -> dict[str, Any]:
    # El hash reproduce la forma documentada de identidad (telefono:<solo dígitos>).
    identity = _identity_hash(sender)
    row = await db.fetchrow(
        """SELECT c.contexto
             FROM conversaciones c
             JOIN identidades_whatsapp i ON i.usuario_id = c.usuario_id
            WHERE i.identificador_hash = $1
            ORDER BY c.actualizado_en DESC LIMIT 1""",
        identity,
    )
    if not row:
        raise AssertionError(f"No existe conversación persistida para {sender}")
    context = row["contexto"] or {}
    if isinstance(context, str):
        context = json.loads(context)
    if not isinstance(context, dict):
        raise AssertionError("El contexto persistido no es un objeto JSON")
    return context


async def _inbound_texts_for_sender(db: asyncpg.Connection, sender: str) -> list[str]:
    identity = _identity_hash(sender)
    rows = await db.fetch(
        """SELECT m.texto
             FROM mensajes m
             JOIN conversaciones c ON c.id = m.conversacion_id
             JOIN identidades_whatsapp i ON i.usuario_id = c.usuario_id
            WHERE i.identificador_hash = $1 AND m.direccion = 'entrada'
            ORDER BY m.ocurrido_en ASC""",
        identity,
    )
    return [str(row["texto"] or "") for row in rows]


def _normalized(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).casefold()


def _state_for_evaluation(context: dict[str, Any]) -> ConversationState:
    serialized = context.get("conversation_state") or context.get("estado_conversacion") or context
    if not isinstance(serialized, dict):
        raise AssertionError("conversation_state persistido no es un objeto JSON")
    return ConversationState.from_dict(serialized)


def _evidence_text(state: ConversationState) -> str:
    """Representación canónica de toda la evidencia estructurada persistida.

    No depende de que los valores numéricos se serialicen como 9 o 9.0 ni de
    que una medición histórica deje de ser la última del mismo tipo.
    """
    values: list[str] = []
    for fact in state.hechos.values():
        values.extend((fact.campo, fact.valor, fact.texto_crudo or ""))
    for measurement in state.measurements.values():
        if isinstance(measurement, dict):
            values.extend(str(measurement.get(key, "")) for key in ("formato", "valor", "unidad", "contexto"))
    return " ".join(values).casefold()


def _contains_expected(evidence: str, expected: str) -> bool:
    tokens = re.findall(r"[a-záéíóúüñ]+|\d+(?:\.\d+)?", expected.casefold())
    return all(token in evidence for token in tokens)


async def _run_frozen_cases(db: asyncpg.Connection) -> dict[str, Any]:
    validar_casos_congelados()
    results = []
    latencies = []
    turn_trace: list[dict[str, Any]] = []
    async with httpx.AsyncClient() as client:
        for index, case in enumerate(CASOS_CONGELADOS):
            sender = f"51990000{index:02d}"
            for turn, message in enumerate(case["turnos"], start=1):
                message_id = f"{case['id']}-{turn}"
                result = await _send(client, message_id, sender, "E2E_PHONE_A", message)
                job = await _wait_job(db, result["trabajo_id"])
                inbound = await db.fetchrow(
                    "SELECT id FROM mensajes WHERE meta_message_id = $1 AND direccion = 'entrada'",
                    message_id,
                )
                state_after_turn = _state_for_evaluation(await _context_for_sender(db, sender))
                history = state_after_turn.historial_mensajes_usuario
                trace = {
                    "caso": case["id"],
                    "turno": turn,
                    "message_id": message_id,
                    "trabajo_id": result["trabajo_id"],
                    "trabajo": job,
                    "mensaje_entrada_persistido": inbound is not None,
                    "turnos_en_conversation_state": state_after_turn.turno_actual,
                    "mensaje_en_historial": message in history,
                }
                turn_trace.append(trace)
                _write_progress(turn_trace)
                if inbound is None:
                    raise AssertionError(f"Mensaje aceptado sin fila de entrada: {message_id}")
                if message not in history:
                    raise AssertionError(
                        "Trabajo completado sin actualizar ConversationState: "
                        f"message_id={message_id}; trabajo_id={result['trabajo_id']}"
                    )
                if state_after_turn.turno_actual != turn:
                    raise AssertionError(
                        "Trabajo completado con contador de ConversationState inconsistente: "
                        f"message_id={message_id}; esperado={turn}; "
                        f"actual={state_after_turn.turno_actual}"
                    )
                latencies.append(result["latencia_http_ms"])
            context = await _context_for_sender(db, sender)
            state = _state_for_evaluation(context)
            evidence = _evidence_text(state)
            facts = {fact: _contains_expected(evidence, fact) for fact in case["hechos"]}
            measurements = {
                f"{value} {unit}": any(
                    isinstance(measurement, dict)
                    and float(measurement.get("valor", float("nan"))) == value
                    and str(measurement.get("unidad", "")).casefold() == unit.casefold()
                    for measurement in state.measurements.values()
                )
                for value, unit in case["mediciones"]
            }
            vehicle = {field: str(getattr(state, field, "")).casefold() == str(value).casefold() for field, value in case["vehiculo"].items()}
            results.append({
                "id": case["id"], "turnos": len(case["turnos"]), "hechos": facts,
                "mediciones": measurements, "vehiculo": vehicle,
                "estado_persistido": state.exportar_dict(incluir_trazabilidad=False),
                "diagnostico_presentado": {
                    "top3": state.top3_actual,
                    "ultima_traza": state.trazabilidad[-1] if state.trazabilidad else None,
                },
            })

        duplicate = await _send(client, "E2E-DUPLICADO-1", "51980000001", "E2E_PHONE_A", "Duplicado controlado P0301")
        await _wait_job(db, duplicate["trabajo_id"])
        duplicate_response = await _send(client, "E2E-DUPLICADO-1", "51980000001", "E2E_PHONE_A", "Duplicado controlado P0301")
        if duplicate_response["estado_interno"] != "duplicado":
            raise AssertionError("El webhook duplicado no fue reconocido")

    def total_ok(field: str) -> tuple[int, int]:
        values = [ok for case in results for ok in case[field].values()]
        return sum(values), len(values)

    facts_ok, facts_total = total_ok("hechos")
    measures_ok, measures_total = total_ok("mediciones")
    vehicle_ok, vehicle_total = total_ok("vehiculo")
    output = {
        "casos": results,
        "turnos": sum(case["turnos"] for case in results),
        "retencion_hechos": {"numerador": facts_ok, "denominador": facts_total},
        "retencion_mediciones": {"numerador": measures_ok, "denominador": measures_total},
        "consistencia_vehiculo": {"numerador": vehicle_ok, "denominador": vehicle_total},
        "idempotencia": {"duplicado_reconocido": True},
        "latencia_http_ms": {"muestras": len(latencies), "promedio": round(statistics.fmean(latencies), 2), "maximo": round(max(latencies), 2)},
    }
    output["trazabilidad_turnos"] = turn_trace
    return output


async def _run_concurrency(db: asyncpg.Connection) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        requests = [
            _send(client, "E2E-A-1", "51981111111", "E2E_PHONE_A", "Toyota gasolina P0301, compresión 180 psi."),
            _send(client, "E2E-B-1", "51982222222", "E2E_PHONE_B", "Ranger diésel P2463, diferencial DPF 38 kPa."),
        ]
        responses = await asyncio.gather(*requests)
        for response in responses:
            await _wait_job(db, response["trabajo_id"])
        state_before = _state_for_evaluation(await _context_for_sender(db, "51981111111"))
        # Llegada tardía y orden de llegada inverso: ambos turnos se conservan.
        late = await _send(client, "E2E-A-3", "51981111111", "E2E_PHONE_A", "Medición tardía: 14.1 V de carga.")
        early = await _send(client, "E2E-A-2", "51981111111", "E2E_PHONE_A", "Antes medí 180 psi parejo.")
        await _wait_job(db, late["trabajo_id"])
        await _wait_job(db, early["trabajo_id"])

    context_a = _normalized(await _context_for_sender(db, "51981111111"))
    context_b = _normalized(await _context_for_sender(db, "51982222222"))
    if "ranger" in context_a or "p2463" in context_a or "toyota" in context_b or "p0301" in context_b:
        raise AssertionError("Se detectó contaminación entre talleres")
    inbound_texts = "\n".join(await _inbound_texts_for_sender(db, "51981111111"))
    if "14.1 V" not in inbound_texts or "180 psi" not in inbound_texts:
        raise AssertionError("Los mensajes fuera de orden no fueron persistidos")
    state_after = _state_for_evaluation(await _context_for_sender(db, "51981111111"))
    required_messages = ("Medición tardía: 14.1 V de carga.", "Antes medí 180 psi parejo.")
    if state_after.case_id != state_before.case_id:
        raise AssertionError("Los mensajes tardíos cambiaron el case_id")
    if state_after.turno_actual != 3:
        raise AssertionError("No se contabilizaron los tres mensajes concurrentes")
    if any(state_after.historial_mensajes_usuario.count(text) != 1 for text in required_messages):
        raise AssertionError("Mensaje tardío ausente o duplicado en ConversationState")
    return {
        "mensajes_fuera_de_orden_en_historial": True,
        "case_id_conservado": True,
        "turnos_contabilizados": state_after.turno_actual,
        "talleres": 2,
        "contaminacion_cruzada": False,
        "mensajes_fuera_de_orden_persistidos": True,
    }


async def _run_continuity(db: asyncpg.Connection, servicio: str) -> dict[str, Any]:
    sender = "5199000000"
    before = _normalized(await _context_for_sender(db, sender))
    required = ("corolla", "p0301", "180", "bobina")
    missing = [item for item in required if item not in before]
    if missing:
        raise AssertionError(
            "La memoria no sobrevivió el reinicio de servicios; "
            f"faltan={missing}; contexto={before[:1000]}"
        )
    async with httpx.AsyncClient() as client:
        response = await _send(client, f"E2E-CONTINUIDAD-{servicio}-{uuid.uuid4().hex}", sender, "E2E_PHONE_A", "Continúo: la compresión de 180 psi sigue pareja.")
        await _wait_job(db, response["trabajo_id"])
    after = _normalized(await _context_for_sender(db, sender))
    if not all(item in after for item in required):
        raise AssertionError("El turno posterior al reinicio perdió hechos técnicos")
    return {"servicio_reiniciado": servicio, "memoria_y_continuidad": True}


async def main(phase: str, servicio: str | None = None) -> None:
    _require_safe_environment()
    db = await asyncpg.connect(DATABASE_URL)
    try:
        if phase == "initial":
            await _seed_workshops(db)
            output = {"naturaleza": "regresion_e2e_sintetica_no_oficial", "proveedores_externos": "bloqueados_por_configuracion", "conversaciones": await _run_frozen_cases(db), "concurrencia": await _run_concurrency(db)}
        else:
            if servicio is None:
                raise ValueError("Continuidad exige identificar el servicio reiniciado")
            output = {"naturaleza": "regresion_e2e_sintetica_no_oficial",
                      f"continuidad_post_reinicio_{servicio}": await _run_continuity(db, servicio)}
        existing = json.loads(ARTIFACT.read_text(encoding="utf-8")) if ARTIFACT.exists() else {}
        existing.update(output)
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        print(json.dumps(output, ensure_ascii=False, indent=2, default=str))
        if phase == "initial":
            metrics = output["conversaciones"]
            facts = metrics["retencion_hechos"]
            measurements = metrics["retencion_mediciones"]
            if facts["numerador"] / facts["denominador"] < 0.95 or (
                measurements["numerador"] / measurements["denominador"] < 0.95
            ):
                raise AssertionError(
                    "Retención E2E insuficiente: "
                    f"hechos={facts['numerador']}/{facts['denominador']}; "
                    f"mediciones={measurements['numerador']}/{measurements['denominador']}"
                )
    finally:
        await db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("initial", "continuity"), required=True)
    parser.add_argument("--restart-service", choices=("api", "worker", "redis", "postgres"))
    args = parser.parse_args()
    asyncio.run(main(args.phase, args.restart_service))
