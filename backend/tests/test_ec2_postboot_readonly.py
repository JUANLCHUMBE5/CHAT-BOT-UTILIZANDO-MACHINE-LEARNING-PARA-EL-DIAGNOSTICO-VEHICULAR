"""Post-boot auditor regressions; never contacts AWS, SSH or Docker."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "postboot_auditor", ROOT / "scripts/operations/ec2/inspect_running.py"
)
auditor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(auditor)


def test_logs_return_counts_without_personal_data_or_tokens():
    result = auditor.log_signals("ERROR token=private phone=999888777\nWARNING timeout\n")
    assert result == {"lines_examined": 2, "error": 1, "warning": 1, "timeout": 1, "oom": 0}
    assert "private" not in json.dumps(result)
    assert "999888777" not in json.dumps(result)


def test_container_metadata_omits_environment_and_raw_command():
    raw = {
        "Id": "test-id",
        "Image": "image-id",
        "Config": {"Env": ["TOKEN=private"], "Cmd": ["sh", "-c", "alembic upgrade head; secret"]},
        "State": {"Status": "running"},
        "Mounts": [],
        "HostConfig": {"RestartPolicy": {"Name": "unless-stopped"}},
    }
    result = auditor.container_metadata(raw, {"Config": {"Labels": {}}})
    assert result["startup_runs_migrations"] is True
    assert result["restart_policy"] == "unless-stopped"
    assert "private" not in json.dumps(result)
    assert "secret" not in json.dumps(result)


def test_nonzero_command_does_not_expose_process_output(monkeypatch):
    monkeypatch.setattr(
        auditor.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="secret", stderr="password"),
    )
    assert auditor.command(["false"]) == {"ok": False, "reason": "nonzero_exit", "exit_code": 1}


def test_invalid_health_json_is_sanitized(monkeypatch):
    monkeypatch.setattr(auditor, "command", lambda *args, **kwargs: {"ok": True, "value": "<html>secret"})
    assert auditor.health("http://localhost") == {"ok": False, "reason": "invalid_health_json"}


def test_frontend_http_error_is_not_marked_healthy(monkeypatch):
    monkeypatch.setattr(auditor, "command", lambda *args, **kwargs: {"ok": True, "value": "503"})
    assert auditor.frontend_status() == {"ok": False, "http_status": 503}


def test_missing_model_is_not_marked_healthy(monkeypatch):
    monkeypatch.setattr(
        auditor,
        "command",
        lambda *args, **kwargs: {"ok": True, "value": '{"models_loaded":false,"missing_artifact":true}'},
    )
    assert auditor.inspect_models()["ok"] is False


def test_auditor_issues_no_restart_migration_or_mutation(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=1, stdout="", stderr="suppressed")

    monkeypatch.setattr(auditor.subprocess, "run", fake_run)
    report = auditor.main()
    assert report["read_only"] is True
    assert report["automatic_actions"] == []
    assert calls
    for args in calls:
        assert not (args[0] == "docker" and args[1] in {"restart", "start", "stop", "rm", "run", "pull"})
        assert "upgrade" not in args
        if "psql" in " ".join(args):
            assert "SELECT version_num FROM alembic_version" in " ".join(args)
            assert "PGOPTIONS=-c default_transaction_read_only=on" in args


def test_missing_rag_returns_absence_without_creating_artifacts(tmp_path):
    from src.infrastructure.motor_rag import MotorRAG

    # The autouse fixture already creates a temporary tracker CSV; preserve it too.
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir() if path.is_file()}
    rag = MotorRAG(manual_path=str(tmp_path / "missing.txt"), rag_version="baseline_f8_3")
    _, _, similarity, metadata = rag.recuperar_procedimiento_hibrido("procedimiento de taller")
    assert similarity == 0.0
    assert metadata == {}
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir() if path.is_file()} == before
