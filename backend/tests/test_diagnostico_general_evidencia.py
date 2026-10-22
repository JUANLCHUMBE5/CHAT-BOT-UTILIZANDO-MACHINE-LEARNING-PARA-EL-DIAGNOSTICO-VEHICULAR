"""Regresiones por contratos de evidencia y componentes; sin cambiar artefactos ML."""

from types import SimpleNamespace

import pytest

from src.core.conversacion.evidencia_observada import pregunta_observacion, subsistema_observado
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.formato_salidas.acciones_prioritarias import (
    extraer_accion_prioritaria,
    generar_pregunta_contextual,
)
from src.core.conversacion.models import ConversationState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta
from src.core.diagnostico.confianza_resultado import describir_confianza
from src.core.diagnostico.semantic_purifier import purificar_sintoma_para_vectorizador_ml
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.mark.parametrize('componente', ['inyector individual', 'inyector cilindro 3', 'inyectores'])
def test_solenoide_no_equivale_a_arrancador(componente):
    falla = f'Falla en circuito o solenoide de {componente}'
    accion = extraer_accion_prioritaria(falla)
    pregunta, _ = generar_pregunta_contextual(falla)
    assert 'inyector' in accion
    assert 'terminal 50' not in accion
    assert 'manómetro' not in pregunta
    assert 'diagrama' in accion


def test_arrancador_conserva_comprobacion_propia():
    assert 'terminal 50' in extraer_accion_prioritaria('Motor de arranque defectuoso')


@pytest.mark.parametrize('texto', [
    'El escáner registra señal baja del pedal de acelerador',
    'Encontré circuito abierto en el sensor TPS',
    'El sensor APP presenta señal intermitente',
])
def test_observacion_no_desaparece_antes_del_svm(texto):
    estado = ConversationState(session_id='evidencia')
    ExtractorHechos.extraer_y_actualizar(estado, 'El motor tiembla en ralentí')
    estado.historial_mensajes_usuario = ['El motor tiembla en ralentí', texto]
    limpio = purificar_sintoma_para_vectorizador_ml(SintetizadorConsulta.sintetizar(estado))
    assert texto.lower() in limpio.lower()
    assert subsistema_observado(texto) == 'senal_electrica'


@pytest.mark.parametrize('texto', ['El vehículo cabecea', 'El carro vibra', 'Se sacude'])
def test_vibracion_ambigua_se_caracteriza(texto):
    estado = ConversationState(session_id='ambiguo')
    estado.historial_mensajes_usuario = [texto]
    pregunta = pregunta_observacion(estado)
    assert 'detenido' in pregunta and 'desplazarse' in pregunta


@pytest.mark.parametrize('texto,esperado', [
    ('Toyota Corolla 2020, timón duro', 'dirección'),
    ('Renault Logan, velocímetro no levanta', 'tablero'),
    ('Kia Soluto, señal baja del pedal de acelerador', 'DTC'),
])
def test_preguntas_especificas_por_subsistema(texto, esperado):
    estado = ConversationState(session_id='pregunta')
    estado.historial_mensajes_usuario = [texto]
    assert esperado in pregunta_observacion(estado)


@pytest.mark.parametrize('texto,modelo', [('Kia Soluto 2025','Soluto'), ('Renault Logan 2020','Logan'), ('Kia Rio 2018','Rio')])
def test_perfil_sin_placas_fabricadas(texto, modelo):
    estado = ConversationState(session_id='perfil')
    ExtractorHechos.extraer_y_actualizar(estado, texto)
    assert estado.modelo == modelo
    assert estado.placa is None


@pytest.mark.parametrize('decision', ['PREGUNTAR','SEGURIDAD_CRITICA','PENDIENTE_MEDICION'])
def test_cero_no_es_probabilidad_de_diagnostico(decision):
    meta = describir_confianza({'decision':decision,'confianza_ml':0})
    assert meta['valor_svm'] is None
    assert meta['estado'] == 'sin_estimacion'


def test_estimacion_y_prioridad_operativa_separadas():
    dto = SimpleNamespace(predicciones_svm_raw=[SimpleNamespace(falla='A', probabilidad=.30)])
    meta = describir_confianza({'dto':dto,'diagnostico_ml':'A','confianza_ml':.94,'decision':'DIAGNOSTICAR'})
    assert meta['valor_svm'] == .30
    assert meta['valor_operativo'] == .94
    assert not meta['diagnostico_confirmado_fisicamente']


@pytest.mark.anyio
async def test_evidencia_nueva_del_componente_cambia_la_siguiente_pregunta():
    repo = InMemoryConversationRepository()
    o = OrquestadorConversacion(repositorio=repo)
    g = GestorDiagnostico()
    await o.procesar_turno('general-pedal', 'Kia Soluto 2025, el vehículo cabecea', g)
    r = await o.procesar_turno('general-pedal', 'En el escáner aparece señal baja del pedal de acelerador', g)
    assert 'DTC' in r['respuesta_texto']
    assert 'bujías' not in r['respuesta_texto']
    assert r['confianza']['estado'] == 'sin_estimacion'
    assert 'pedal' in r['estado'].obtener_hecho('observacion_tecnica_actual').valor


@pytest.mark.parametrize('texto', [
    'El carro tiembla al acelerar en subida',
    'El carro se sacude al soltar el embrague',
    'El piso vibra en carretera a velocidad constante',
])
def test_no_repreguntar_condicion_si_ya_fue_reportada(texto):
    estado = ConversationState(session_id='condicion-conocida')
    estado.historial_mensajes_usuario = [texto]
    assert pregunta_observacion(estado) is None


def test_metadatos_se_actualizan_al_copiar_dto():
    from src.core.diagnostico.models import PrediccionML, ResultadoDiagnostico

    dto = ResultadoDiagnostico(
        respuesta_texto='Hipótesis pendiente',diagnostico_ml='A',confianza_ml=.94,
        contexto_manual='',titulo_manual='',
        predicciones_svm_raw=[PrediccionML(falla='A',probabilidad=.30)],
    )
    assert dto.model_dump()['confianza_detalle']['valor_svm'] == .30
    copia = dto.model_copy(update={'diagnostico_ml':'Sin hipótesis compatible', 'confianza_ml':0.0})
    assert copia.model_dump()['confianza_detalle']['valor_svm'] is None
