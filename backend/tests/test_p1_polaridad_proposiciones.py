"""Contraejemplos P1: negación por proposición y alertas independientes."""
import pytest

from src.core.conversacion.detector_polaridad import DetectorPolaridad
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState, FactState
from src.core.diagnostico.politica_seguridad import PoliticaSeguridad, SeveridadSeguridad


@pytest.mark.parametrize('verbo', ['tengo', 'tiene', 'tenemos', 'presento', 'presenta', 'presentamos', 'hay'])
@pytest.mark.parametrize('sintoma', ['problemas al acelerar', 'pérdida de potencia', 'vibraciones en el volante'])
def test_negaciones_flexiones(verbo, sintoma):
    hechos = DetectorPolaridad.extraer_sintomas(f'No {verbo} {sintoma}.')
    assert hechos
    assert all(h[2] == FactState.AUSENTE_NEGADO for h in hechos)


@pytest.mark.parametrize('conector', ['y', 'pero', 'aunque', 'además', ','])
def test_sintomas_independientes(conector):
    hechos = DetectorPolaridad.extraer_sintomas(
        f'No tengo pérdida de potencia {conector} el volante vibra.'
    )
    polaridades = {nombre: estado for _, nombre, estado in hechos}
    assert polaridades['pérdida de potencia'] == FactState.AUSENTE_NEGADO
    assert polaridades['vibración'] == FactState.CONFIRMADO


@pytest.mark.parametrize('texto', ['Quizás tengo pérdida de potencia.', 'No sé si hay vibraciones.'])
def test_incierto_no_es_confirmacion(texto):
    assert not any(h[2] == FactState.CONFIRMADO for h in DetectorPolaridad.extraer_sintomas(texto))


@pytest.mark.parametrize('conector', ['y', 'pero', 'aunque', ',', '.'])
@pytest.mark.parametrize('peligro', ['chorrea gasolina', 'gotea combustible', 'pierde nafta', 'bota gasolina'])
def test_fuga_activa_no_se_cancela(conector, peligro):
    for texto in [
        f'No hay fuga en el tanque {conector} la manguera {peligro}.',
        f'La manguera {peligro} {conector} no hay fuga en el tanque.',
    ]:
        severidad, banner = PoliticaSeguridad.evaluar_severidad(texto)
        assert severidad == SeveridadSeguridad.CRITICAL_STOP
        assert banner


@pytest.mark.parametrize('texto', [
    'No hay fuga de gasolina.', 'La manguera no chorrea gasolina.',
    'No gotea combustible y no pierde gasolina.', 'Sin olor fuerte a gasolina.',
    'La fuga de gasolina no existe.',
])
def test_fuga_negada_no_alerta(texto):
    assert PoliticaSeguridad.evaluar_severidad(texto)[0] != SeveridadSeguridad.CRITICAL_STOP


def test_correccion_multiturno_no_contamina_memoria():
    estado = ConversationState(session_id='p1-local', case_id='p1-caso')
    ExtractorHechos.extraer_y_actualizar(estado, 'Tiene pérdida de potencia.')
    ExtractorHechos.extraer_y_actualizar(estado, 'No tengo pérdida de potencia. El volante vibra.')
    assert estado.es_hecho_negado('sintoma_pérdida_de_potencia')
    assert estado.es_hecho_confirmado('sintoma_vibración')
    assert estado.case_id == 'p1-caso'


@pytest.mark.parametrize('texto', [
    'No hay fuga en el tanque y manguera de gasolina rota.',
    'No hay fuga en el tanque, charco de gasolina.',
    'La manguera chorrea gasolina y la fuga del tanque no existe.',
])
def test_componentes_y_eventos_independientes(texto):
    assert PoliticaSeguridad.evaluar_severidad(texto)[0] == SeveridadSeguridad.CRITICAL_STOP


def test_lista_de_sintomas_negados():
    hechos = DetectorPolaridad.extraer_sintomas('No tengo vibraciones ni pérdida de potencia.')
    assert len(hechos) == 2
    assert all(h[2] == FactState.AUSENTE_NEGADO for h in hechos)


def test_pregunta_no_confirma_sintoma():
    assert not any(h[2] == FactState.CONFIRMADO for h in DetectorPolaridad.extraer_sintomas(
        '¿Tengo pérdida de potencia al acelerar?'
    ))


@pytest.mark.parametrize('conector', ['ni', 'y'])
def test_lista_nominal_negada_en_orden_inverso(conector):
    hechos = DetectorPolaridad.extraer_sintomas(f'No tengo pérdida de potencia {conector} vibraciones.')
    assert len(hechos) == 2
    assert all(h[2] == FactState.AUSENTE_NEGADO for h in hechos)
