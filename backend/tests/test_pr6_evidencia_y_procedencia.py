"""Contraejemplos independientes pre-merge: ninguna referencia de campo inventada."""
from types import SimpleNamespace

import pytest

from src.core.diagnostico.enrutador_sistema import detectar_areas_tecnicas, resolver_sistema_activo
from src.core.diagnostico.evidencia_proposicional import analizar_proposiciones, evidencia_afirmada
from src.core.diagnostico.models import PrediccionML
from src.core.diagnostico.procesador_texto.clasificacion_ml import ejecutar_clasificacion_ml


@pytest.mark.parametrize("texto", [
    "No hay falla en sensor ECT", "No presenta avería del sensor ECT",
    "Sin problemas de temperatura ni fallo de bobinas", "No hay misfire ni falla de bobinas",
    "No tengo pérdida de potencia, pero el rodamiento hace ruido",
])
def test_polaridad_no_promueve_menciones_negadas(texto):
    proposiciones = analizar_proposiciones(texto)
    assert proposiciones[0].estado == "NEGADO"
    if "ni" in texto:
        assert proposiciones[1].estado == "NEGADO"


def test_evidencia_separa_historico_pendiente_y_afirmado():
    texto = "Bujías nuevas. No puedo medir compresión. La caja hace ruido"
    assert [p.estado for p in analizar_proposiciones(texto)] == ["HISTORICO", "NO_COMPROBADO", "AFIRMADO"]
    assert evidencia_afirmada(texto) == "La caja hace ruido"


def test_negacion_no_oculta_anomalia_afirmada():
    assert evidencia_afirmada("No hay fuga en tanque y la manguera chorrea gasolina") == "la manguera chorrea gasolina"
    assert evidencia_afirmada("No comunica la ECU. No arranca. Sin chispa")


@pytest.mark.parametrize("texto,sistema", [
    ("caja CVT con aceite sobrecalentado y tirones", "transmision"),
    ("DPF saturado diesel en modo degradado", "combustible_admision"),
    ("rueda cruje al doblar la direccion", "suspension_direccion"),
])
def test_sistema_segun_componente_y_no_condicion_generica(texto, sistema):
    assert resolver_sistema_activo(texto) == sistema


def clasificar(texto):
    modelo = SimpleNamespace(predecir_top_fallas=lambda *a, **k: [
        {"falla": "Bateria descargada o bornes sulfatados", "probabilidad": .6},
        {"falla": "Juntas homocineticas o palieres danados", "probabilidad": .3},
        {"falla": "Falla en bujias o bobinas de encendido (misfire)", "probabilidad": .1},
    ])
    gestor = SimpleNamespace(modelo_ml=modelo, _purificar_sintoma_para_vectorizador_ml=lambda x: x,
                             _es_perdida_potencia_bajo_carga=lambda x: False)
    return ejecutar_clasificacion_ml(gestor, texto, None, None, detectar_areas_tecnicas(texto),
                                    resolver_sistema_activo(texto), None, False, False)


@pytest.mark.parametrize("texto,prohibida", [
    ("No hay falla en sensor ECT. La caja hace ruido", "ECT"),
    ("No hay misfire ni falla de bobinas. La caja hace ruido", "misfire"),
    ("Motor tiembla en ralenti, bujias nuevas y el problema continua", "inyector individual"),
    ("Bateria se descarga. Antecedente ECU. Aun no medi", "Corto electrico"),
])
def test_reglas_no_inventan_causas(texto, prohibida):
    resultado = clasificar(texto)
    assert prohibida not in resultado[0]


def test_dto_conserva_fuente_version_y_scores_sin_equivalerlos():
    pred = PrediccionML(falla="test", probabilidad=.9, raw_svm_score=.4,
                       operational_score=.9, calibrated_probability=.4,
                       prediction_source="SVM_DTC", model_version="c1", taxonomy_version="v2", class_id="C01")
    assert pred.origen_probabilidad == "SVM_DTC"
    assert pred.statistical_probability == .4
    assert pred.operational_score == .9
    assert pred.model_copy().model_dump() == pred.model_dump()


def test_regla_no_tiene_probabilidad_estadistica():
    pred = PrediccionML(falla="hipótesis", probabilidad=0, origen_probabilidad="REGLA")
    assert pred.statistical_probability is None
    assert pred.calibrated_probability is None


def test_benchmark_no_acepta_equivalencias_de_componentes():
    from scripts.evaluacion_generalizada_grupos_a_b_c_d import coincide
    assert not coincide("Inyectores sucios", "Sensor MAF")
    assert not coincide("Bateria descargada", "Alternador")
    assert coincide("Sensor MAF", "sensor maf")


def test_taxonomia_empaquetada_es_identica_y_no_simula_probabilidad():
    from src.core.diagnostico.taxonomia_sistemas import CLASES_ENTRENADAS_61, SUBAREAS_POR_CLASE
    from src.infrastructure.ml_contract import taxonomy
    assert set(taxonomy.CLASES_ENTRENADAS_61) == set(CLASES_ENTRENADAS_61)
    assert taxonomy.SUBAREAS_POR_CLASE == SUBAREAS_POR_CLASE
    result = taxonomy.construir_contrato_prediccion(class_label="hipotesis externa",
        raw_svm_score=0, calibrated_probability=.85, prediction_source="REGLA")
    assert result.calibrated_probability is None


@pytest.mark.parametrize("texto", ["plumas no se mueven", "cambie computadora y ahora no arranca"])
def test_anomalia_no_se_confunde_con_prueba_no_realizada(texto):
    assert evidencia_afirmada(texto)


def test_normalizacion_conserva_codigo_obd_exacto():
    from src.core.traductor_jerga import normalizar_jerga_peruana
    assert "p0301" in normalizar_jerga_peruana("DTC P0301 confirmado por escaner")
    assert "p0302" in normalizar_jerga_peruana("DTC P0302 confirmado por escaner")


def test_presentacion_sin_hipotesis_es_abstencion_persistible():
    from src.core.conversacion.presentacion_dto import alinear_predicciones_presentadas
    from src.core.diagnostico.models import ResultadoDiagnostico
    dto = ResultadoDiagnostico(respuesta_texto="pendiente", diagnostico_ml="hipotesis previa",
        confianza_ml=.4, contexto_manual="", titulo_manual="",
        predicciones_ml=[PrediccionML(falla="hipotesis previa", probabilidad=.4)])
    result = alinear_predicciones_presentadas(dto, [])
    assert result.diagnostico_ml == "Sin hipótesis compatible"
    assert result.motivo_abstencion == "SIN_HIPOTESIS_PRESENTABLE"
    assert result.predicciones_ml == []
    assert result.predicciones_ml_raw[0].falla == "hipotesis previa"
    assert ResultadoDiagnostico.model_validate(result.model_dump())
