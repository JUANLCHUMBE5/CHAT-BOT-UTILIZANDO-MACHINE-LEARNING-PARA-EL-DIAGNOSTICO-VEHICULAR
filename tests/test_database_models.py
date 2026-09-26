from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import configure_mappers

from src.core.security import hash_identificador_persistencia
from src.infrastructure.database import Base

TABLAS_ESPERADAS = {
    "auditoria",
    "conversaciones",
    "cuotas_gemini_global",
    "diagnosticos",
    "hipotesis_diagnostico",
    "identidades_whatsapp",
    "mensajes",
    "roles",
    "solicitudes_acceso",
    "talleres",
    "trabajos_gemini",
    "trabajos_sistema",
    "uso_api",
    "usuarios",
    "validaciones_taller",
    "vehiculos",
    "workers_sistema",
}


def test_modelos_registran_el_esquema_completo():
    configure_mappers()
    assert set(Base.metadata.tables) == TABLAS_ESPERADAS


def test_esquema_puede_crearse_y_eliminarse_en_una_base_temporal():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)
    assert set(inspect(engine).get_table_names()) == TABLAS_ESPERADAS

    Base.metadata.drop_all(engine)
    assert inspect(engine).get_table_names() == []


def test_identificadores_sensibles_no_se_guardan_en_texto_plano():
    columnas_usuario = set(Base.metadata.tables["usuarios"].columns.keys())
    columnas_vehiculo = set(Base.metadata.tables["vehiculos"].columns.keys())

    assert "whatsapp_hash" in columnas_usuario
    assert "numero_whatsapp" not in columnas_usuario
    assert "placa_hash" in columnas_vehiculo
    assert "placa" not in columnas_vehiculo


def test_mensaje_meta_es_idempotente_por_restriccion_unica():
    tabla = Base.metadata.tables["mensajes"]
    columnas_unicas = {
        tuple(constraint.columns.keys())
        for constraint in tabla.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert ("meta_message_id",) in columnas_unicas


def test_alembic_tiene_una_sola_revision_head():
    config = Config("alembic.ini")
    scripts = ScriptDirectory.from_config(config)

    assert len(scripts.get_heads()) == 1
    # Las migraciones de soporte PILOT/Ficha 2 extienden la cadena de 20260912_01.
    # Esta aserción detecta una regresión de revisión, además de ramificaciones.
    assert scripts.get_current_head() == "20260926_01"


def test_hash_persistencia_normaliza_telefono_y_placa():
    telefono = hash_identificador_persistencia("whatsapp:+51 999-888-777", "telefono")
    mismo_telefono = hash_identificador_persistencia("51999888777", "telefono")
    placa = hash_identificador_persistencia("abc-123", "placa")
    misma_placa = hash_identificador_persistencia("ABC 123", "placa")

    assert len(telefono) == 64
    assert telefono == mismo_telefono
    assert placa == misma_placa
    assert telefono != placa
