"""Regresiones de identidad y persistencia de fichas de desarrollo por caso."""
import uuid
from types import SimpleNamespace

from sqlalchemy import Text

from src.application.services.borrador_consulta import (
    case_id_sesion_activa,
    clave_borrador,
    construir_statement_borrador_consulta,
)


def _diag(diagnostico_id="diag-1", conversacion_id="conv-1", taller_id="taller-1"):
    return SimpleNamespace(id=diagnostico_id, conversacion_id=conversacion_id, taller_id=taller_id)


def _vehiculo(placa_hash="a" * 64):
    return SimpleNamespace(placa_hash=placa_hash)


def test_mismo_caso_misma_clave_aunque_cambie_diagnostico():
    assert clave_borrador(_diag("diag-1"), _vehiculo(), "case-1") == clave_borrador(
        _diag("diag-2"), _vehiculo(), "case-1"
    )


def test_caso_nuevo_no_reutiliza_ficha():
    assert clave_borrador(_diag(), _vehiculo(), "case-1") != clave_borrador(
        _diag(), _vehiculo(), "case-2"
    )


def test_no_cruza_vehiculos_conversaciones_ni_talleres():
    base = clave_borrador(_diag(), _vehiculo(), "case-1")
    assert base != clave_borrador(_diag(), _vehiculo("b" * 64), "case-1")
    assert base != clave_borrador(_diag(conversacion_id="conv-2"), _vehiculo(), "case-1")
    assert base != clave_borrador(_diag(taller_id="taller-2"), _vehiculo(), "case-1")


def test_sin_case_id_fallback_por_diagnostico():
    assert clave_borrador(_diag("diag-1"), _vehiculo()) == "auto:diag-1"
    assert clave_borrador(_diag("diag-1"), _vehiculo()) != clave_borrador(
        _diag("diag-2"), _vehiculo()
    )


def test_rest_usa_case_id_real_de_sesion_y_no_el_session_id():
    case_id = str(uuid.uuid4())
    gestor = SimpleNamespace(
        session_manager=SimpleNamespace(
            obtener_sesion=lambda session_id: SimpleNamespace(case_id=case_id)
        )
    )

    assert case_id_sesion_activa(gestor, "session-abc") == case_id


def test_rest_no_inventa_case_id_si_la_sesion_no_tiene_uno_valido():
    gestor = SimpleNamespace(
        session_manager=SimpleNamespace(
            obtener_sesion=lambda session_id: SimpleNamespace(case_id=None)
        )
    )
    gestor_case_invalido = SimpleNamespace(
        session_manager=SimpleNamespace(
            obtener_sesion=lambda session_id: SimpleNamespace(case_id="session-abc")
        )
    )

    assert case_id_sesion_activa(gestor, "session-abc") is None
    assert case_id_sesion_activa(gestor_case_invalido, "session-abc") is None
    assert case_id_sesion_activa(gestor, None) is None


def test_etiqueta_sistema_acepta_etiquetas_diagnosticas_completas():
    """El campo admite etiquetas C1 sin truncarlas al antiguo límite de 80 caracteres."""
    from src.infrastructure.database.models.validation import ValidacionTaller

    assert isinstance(ValidacionTaller.__table__.columns["sistema_afectado_probable"].type, Text)


def test_borrador_envia_etiqueta_svm_completa_al_insert():
    etiqueta = (
        "Falla de descarbonizacion e inyeccion directa GDI "
        "(acumulacion de carbon en valvulas)"
    )
    assert len(etiqueta) > 80

    diagnostico = SimpleNamespace(
        id=uuid.uuid4(),
        taller_id=uuid.uuid4(),
        mecanico_id=uuid.uuid4(),
        conversacion_id=uuid.uuid4(),
        sintoma_original="arranque irregular",
        sintoma_normalizado="arranque irregular",
        falla_predicha=etiqueta,
        tiempo_inferencia_ml_ms=12,
        duracion_ms=250,
    )
    vehiculo = SimpleNamespace(
        placa_hash="a" * 64,
        placa_ultimos4="1234",
        marca="Toyota",
        modelo="Corolla",
        anio=2015,
        kilometraje=100_000,
        combustible="gasolina",
    )

    statement = construir_statement_borrador_consulta(
        diagnostico, vehiculo, case_id="case-1"
    )
    values = {column.name: bind.value for column, bind in statement._values.items()}
    assert values["chatbot_prediccion"] == etiqueta
    assert values["sistema_afectado_probable"] == etiqueta


def test_upsert_ignora_borradores_verificados_y_preserva_campos_humanos():

    diagnostico = SimpleNamespace(
        id=uuid.uuid4(),
        taller_id=uuid.uuid4(),
        mecanico_id=uuid.uuid4(),
        conversacion_id=uuid.uuid4(),
        sintoma_original="",
        sintoma_normalizado=None,
        falla_predicha=None,
        tiempo_inferencia_ml_ms=None,
        duracion_ms=None,
    )
    vehiculo = SimpleNamespace(
        placa_hash="b" * 64,
        placa_ultimos4="5678",
        marca="Generico",
        modelo="Generico",
        anio=None,
        kilometraje=None,
        combustible=None,
    )

    statement = construir_statement_borrador_consulta(
        diagnostico, vehiculo, case_id="case-2"
    )
    clause = statement._post_values_clause
    set_columns = {column for column, _ in clause.update_values_to_set}
    assert "falla_real" not in set_columns
    assert "prediccion_correcta" not in set_columns
    assert "metodo_confirmacion" not in set_columns
    assert "evidencia_ref" not in set_columns
    assert "diagnostico_id" in set_columns
    assert "estado_registro" not in set_columns
    assert "tipo_registro" not in set_columns

    compiled_where = str(clause.update_whereclause)
    assert "estado_registro" in compiled_where
    assert "tipo_registro" in compiled_where
    assert "placa_hash" in compiled_where

