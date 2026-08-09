import pytest

from src.infrastructure import aws_secrets


def test_aws_secrets_desactivado_no_hace_llamadas(monkeypatch):
    monkeypatch.setenv("AWS_SECRETS_ENABLED", "false")
    monkeypatch.setattr(
        aws_secrets,
        "cargar_secretos_aws",
        lambda *_: pytest.fail("No debio consultar AWS"),
    )
    aws_secrets.aplicar_secretos_aws()


def test_aws_secrets_habilitado_exige_nombre(monkeypatch):
    monkeypatch.setenv("AWS_SECRETS_ENABLED", "true")
    monkeypatch.delenv("AWS_SECRETS_NAME", raising=False)
    with pytest.raises(RuntimeError, match="AWS_SECRETS_NAME"):
        aws_secrets.aplicar_secretos_aws()


def test_aws_secrets_aplica_solo_configuracion_permitida(monkeypatch):
    monkeypatch.setenv("AWS_SECRETS_ENABLED", "true")
    monkeypatch.setenv("AWS_SECRETS_NAME", "carbot/test")
    monkeypatch.setattr(
        aws_secrets,
        "cargar_secretos_aws",
        lambda *_: {"GEMINI_API_KEY": "valor-solo-prueba"},
    )
    aws_secrets.aplicar_secretos_aws()
    assert __import__("os").environ["GEMINI_API_KEY"] == "valor-solo-prueba"
