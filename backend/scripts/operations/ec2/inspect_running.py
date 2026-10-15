"""Read-only post-boot checks. Run via SSH only after the owner confirms boot.

Reports metadata and aggregate log signals; never returns logs, environment values,
customer rows or raw subprocess errors. No restart, migration, cleanup or DML.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from typing import Any

CONTAINERS = {
    "api": "carbot-backend-api-1",
    "worker": "carbot-backend-worker-1",
    "postgres": "carbot-backend-postgres-1",
    "redis": "carbot-backend-redis-1",
    "frontend": "carbot-frontend",
}


def command(args: list[str], timeout: int = 12) -> dict[str, Any]:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return {"ok": False, "reason": "unavailable_or_timeout"}
    if result.returncode:
        return {"ok": False, "reason": "nonzero_exit", "exit_code": result.returncode}
    return {"ok": True, "value": result.stdout.strip(), "stderr": result.stderr}


def log_signals(text: str) -> dict[str, int]:
    """Only aggregate counts leave the server, including when logs contain secrets."""
    lines = text.lower().splitlines()
    return {
        "lines_examined": len(lines),
        **{term: sum(term in line for line in lines) for term in ("error", "warning", "timeout", "oom")},
    }


def container_metadata(raw: dict[str, Any], image: dict[str, Any]) -> dict[str, Any]:
    config = raw.get("Config", {})
    args = config.get("Cmd") or []
    joined = " ".join(str(arg) for arg in args).lower()
    revision = (image.get("Config", {}).get("Labels") or {}).get("org.opencontainers.image.revision")
    return {
        "id": raw["Id"],
        "state": raw.get("State", {}).get("Status"),
        "health": raw.get("State", {}).get("Health", {}).get("Status"),
        "restart_policy": raw.get("HostConfig", {}).get("RestartPolicy", {}).get("Name"),
        "image_id": raw.get("Image"),
        "image_digests": image.get("RepoDigests", []),
        "oci_revision": revision if revision and re.fullmatch(r"[0-9a-f]{40}", revision) else None,
        "startup_runs_migrations": "alembic" in joined and "upgrade" in joined,
        "worker_kind": "celery"
        if "celery" in joined
        else ("postgres_queue" if "src.application.jobs.worker" in joined else None),
        "mounts": [
            {"type": m["Type"], "name": m.get("Name"), "destination": m["Destination"], "rw": m["RW"]}
            for m in raw.get("Mounts", [])
        ],
        "networks": sorted(raw.get("NetworkSettings", {}).get("Networks", {})),
    }


def safe_value(result: dict[str, Any]) -> dict[str, Any]:
    """Drop stderr even for explicitly safe metadata commands."""
    return {key: value for key, value in result.items() if key != "stderr"}


def inspect_container(name: str) -> dict[str, Any]:
    result = command(["docker", "inspect", name])
    if not result["ok"]:
        return safe_value(result)
    try:
        raw = json.loads(result["value"])[0]
        image_result = command(["docker", "image", "inspect", raw["Image"]])
        if not image_result["ok"]:
            return safe_value(image_result)
        metadata = container_metadata(raw, json.loads(image_result["value"])[0])
    except (ValueError, KeyError, IndexError, TypeError):
        return {"ok": False, "reason": "invalid_docker_metadata"}
    logs = command(["docker", "logs", "--since", "15m", "--tail", "100", name])
    metadata["recent_log_signals"] = log_signals(logs.get("value", "") + logs.get("stderr", ""))
    metadata["logs_available"] = logs["ok"]
    return {"ok": True, **metadata}


def health(url: str) -> dict[str, Any]:
    result = command(["curl", "--connect-timeout", "3", "--max-time", "8", "-fsS", url])
    if not result["ok"]:
        return safe_value(result)
    try:
        status = json.loads(result["value"]).get("status")
    except (ValueError, AttributeError):
        return {"ok": False, "reason": "invalid_health_json"}
    return {
        "ok": status in ("alive", "ready"),
        "status": status if status in ("alive", "ready") else "unexpected",
    }


def inspect_models() -> dict[str, Any]:
    code = r"""
import hashlib,json,warnings
from pathlib import Path
warnings.filterwarnings('ignore')
base=Path('/app/machine_learning')
expected={'models/c1_fase10_final/modelo_diagnostico_c1.pkl':'24747fb7d3d465227efbd1376084886b92e5333dd12f0e1b380c0c612585608c','models/c1_fase10_final/vectorizador_c1.pkl':'060d0728733499d263f76408b2e99ddb5a56e5dd0f3a006bfa51548397aa96c7'}
out={'hashes':{},'models_loaded':False,'rag_index_available':False}
for name,digest in expected.items():
    p=base/name
    if not p.is_file(): out['missing_artifact']=True;print(json.dumps(out));raise SystemExit(0)
    out['hashes'][name]=hashlib.sha256(p.read_bytes()).hexdigest()
if any(out['hashes'][name]!=digest for name,digest in expected.items()):
    out['unexpected_model_hash']=True;print(json.dumps(out));raise SystemExit(0)
import joblib
model=joblib.load(base/'models/c1_fase10_final/modelo_diagnostico_c1.pkl')
vectorizer=joblib.load(base/'models/c1_fase10_final/vectorizador_c1.pkl')
out.update(models_loaded=True,classes=len(model.classes_),features_match=model.n_features_in_==len(vectorizer.vocabulary_))
import os
version=os.environ.get('CARBOT_RAG_VERSION','baseline_f8_3').lower()
out['configured_rag']='candidate_v1' if version in ('candidate_v1','v1','rag_candidato_v1') else 'baseline'
rel='manuals/candidates/v1/indexes/indice_faiss_v1.index' if out['configured_rag']=='candidate_v1' else 'manuals/indice_faiss.index'
p=base/rel
if p.is_file():
    import faiss
    index=faiss.read_index(str(p))
    out.update(rag_index_available=True,rag_dimension=index.d,rag_documents=index.ntotal,rag_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
out['index_written_or_rebuilt']=False
print(json.dumps(out))
"""
    result = command(["docker", "exec", CONTAINERS["api"], "python", "-c", code], timeout=30)
    if not result["ok"]:
        return safe_value(result)
    try:
        payload = json.loads(result["value"])
        return {"ok": bool(payload.get("models_loaded") and payload.get("features_match")), **payload}
    except (ValueError, TypeError):
        return {"ok": False, "reason": "invalid_model_check_result"}


def internal_connectivity() -> dict[str, Any]:
    code = r"""
import asyncio,json,os
async def main():
    out={}
    try:
        import asyncpg
        c=await asyncpg.connect(host=os.environ['POSTGRES_HOST'],port=int(os.environ.get('POSTGRES_PORT','5432')),user=os.environ['POSTGRES_USER'],password=os.environ['POSTGRES_PASSWORD'],database=os.environ['POSTGRES_DB'],timeout=5,server_settings={'default_transaction_read_only':'on'})
        out['postgres_select_1']=await c.fetchval('SELECT 1')==1
        await c.close()
    except Exception:
        out['postgres_select_1']=False
    try:
        import redis.asyncio as redis
        client=redis.from_url(os.environ['REDIS_URL'],socket_connect_timeout=3,socket_timeout=3)
        out['redis_ping']=bool(await client.ping())
        await client.aclose()
    except Exception:
        out['redis_ping']=False
    print(json.dumps(out))
asyncio.run(main())
"""
    result = command(["docker", "exec", CONTAINERS["api"], "python", "-c", code], timeout=15)
    if not result["ok"]:
        return safe_value(result)
    try:
        return json.loads(result["value"])
    except ValueError:
        return {"ok": False, "reason": "invalid_connectivity_result"}


def frontend_status() -> dict[str, Any]:
    result = command(
        [
            "curl",
            "--connect-timeout",
            "3",
            "--max-time",
            "8",
            "-s",
            "-o",
            "/dev/null",
            "-w",
            "%{http_code}",
            "http://127.0.0.1/",
        ]
    )
    if not result["ok"]:
        return safe_value(result)
    try:
        code = int(result["value"])
    except ValueError:
        return {"ok": False, "reason": "invalid_http_status"}
    return {"ok": 200 <= code < 400, "http_status": code}


def main() -> dict[str, Any]:
    report: dict[str, Any] = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "read_only": True}
    checks = {
        "cpu": ["nproc"],
        "memory": ["free", "-m"],
        "disk": ["df", "-B1", "/"],
        "inodes": ["df", "-i", "/"],
        "devices": ["lsblk", "-b", "-o", "NAME,SIZE,FSTYPE,MOUNTPOINT"],
        "docker_active": ["systemctl", "is-active", "docker"],
        "docker_enabled": ["systemctl", "is-enabled", "docker"],
        "nginx_active": ["systemctl", "is-active", "nginx"],
        "nginx_enabled": ["systemctl", "is-enabled", "nginx"],
        "postgres_ready": [
            "docker",
            "exec",
            CONTAINERS["postgres"],
            "sh",
            "-c",
            'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"',
        ],
        "redis": ["docker", "exec", CONTAINERS["redis"], "redis-cli", "ping"],
        "alembic": [
            "docker",
            "exec",
            "-e",
            "PGOPTIONS=-c default_transaction_read_only=on",
            CONTAINERS["postgres"],
            "sh",
            "-c",
            'psql -X -At -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" '
            '-c "SELECT version_num FROM alembic_version"',
        ],
        "frontend_http": [
            "curl",
            "--connect-timeout",
            "3",
            "--max-time",
            "8",
            "-s",
            "-o",
            "/dev/null",
            "-w",
            "%{http_code}",
            "http://127.0.0.1/",
        ],
    }
    report["checks"] = {name: safe_value(command(args)) for name, args in checks.items()}
    report["containers"] = {name: inspect_container(container) for name, container in CONTAINERS.items()}
    report["live"] = health("http://127.0.0.1:8000/health/live")
    report["ready"] = health("http://127.0.0.1:8000/health/ready")
    report["models"] = inspect_models()
    report["internal_connectivity"] = internal_connectivity()
    report["checks"]["frontend_http"] = frontend_status()
    report["automatic_actions"] = []
    return report


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
