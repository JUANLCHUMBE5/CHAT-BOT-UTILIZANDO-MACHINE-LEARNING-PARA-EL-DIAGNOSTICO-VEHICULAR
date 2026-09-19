"""Regresiones metodológicas Fase 11.5.1 para Ficha 2 (RDC)."""

from src.application.services.validacion_taller import calcular_detalles_campos_ficha2, resumir_fases


def _campos_base():
    return {
        "codigo_registro": 1,
        "fecha_atencion": "2026-09-19",
        "datos_generales_vehiculo": "Toyota Yaris 2020",
        "sintomas_reportados": "Vibración al frenar",
        "descripcion_sintoma": "El volante vibra al frenar a velocidad media",
        "sistema_afectado_probable": "Frenos",
        "diagnostico_confirmado": "Discos de freno alabeados",
        "tiempo_atencion_minutos": 25,
    }


def test_ficha2_ocho_de_ocho_es_registro_completo():
    completo, cantidad, detalles = calcular_detalles_campos_ficha2(**_campos_base())

    assert cantidad == 8
    assert completo == 1
    assert all(campo["completo"] for campo in detalles.values())


def test_ficha2_siete_de_ocho_es_registro_incompleto():
    campos = _campos_base()
    campos["sistema_afectado_probable"] = ""

    completo, cantidad, detalles = calcular_detalles_campos_ficha2(**campos)

    assert cantidad == 7
    assert completo == 0
    assert detalles["campo_6"]["completo"] is False


def test_ficha2_cero_de_ocho_es_registro_incompleto():
    campos = {clave: "" for clave in _campos_base()}

    completo, cantidad, detalles = calcular_detalles_campos_ficha2(**campos)

    assert cantidad == 0
    assert completo == 0
    assert not any(campo["completo"] for campo in detalles.values())


def test_rdc_pre_y_post_se_calculan_por_fase_sin_development_ni_regression():
    grupos_oficiales = [
        {"fase": "Pre-test", "total": 2, "aciertos": 1, "completos": 1, "minutos": 40},
        {"fase": "Post-test", "total": 2, "aciertos": 2, "completos": 2, "minutos": 20},
    ]

    resumen = resumir_fases(grupos_oficiales)

    assert resumen["registros_completos_pretest_porcentaje"] == 50.0
    assert resumen["registros_completos_posttest_porcentaje"] == 100.0
    assert resumen["casos_pretest"] == 2
    assert resumen["casos_posttest"] == 2
