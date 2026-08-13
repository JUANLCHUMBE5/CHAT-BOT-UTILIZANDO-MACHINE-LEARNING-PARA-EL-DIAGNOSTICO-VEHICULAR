import os
from pathlib import Path

from src.config_bootstrap import cargar_variables_entorno


def test_env_local_reemplaza_credencial_antigua_de_windows(tmp_path: Path, monkeypatch):
    archivo = tmp_path / ".env"
    archivo.write_text('META_ACCESS_TOKEN="token_nuevo_local"\n', encoding="utf-8")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("META_ACCESS_TOKEN", "token_antiguo_windows")

    cargar_variables_entorno(archivo)

    assert os.environ["META_ACCESS_TOKEN"] == "token_nuevo_local"


def test_produccion_conserva_credencial_inyectada(tmp_path: Path, monkeypatch):
    archivo = tmp_path / ".env"
    archivo.write_text('META_ACCESS_TOKEN="token_archivo_local"\n', encoding="utf-8")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("META_ACCESS_TOKEN", "token_inyectado_aws")

    cargar_variables_entorno(archivo)

    assert os.environ["META_ACCESS_TOKEN"] == "token_inyectado_aws"
