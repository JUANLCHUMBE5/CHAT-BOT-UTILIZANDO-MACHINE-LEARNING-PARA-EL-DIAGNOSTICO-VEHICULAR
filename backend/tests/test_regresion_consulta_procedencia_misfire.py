"""Regresiones para consultas de procedencia sin mutacion del diagnostico."""

import asyncio
import copy
from functools import wraps

import pytest

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState, QuestionIntent
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.conversacion.respuestas_cortas.interprete_intenciones import interpretar_respuesta_corta
from src.core.conversacion.respuestas_cortas.patrones_deteccion import PATRON_OPCION_NUMERICA

MENSAJE = ("No he indicado que el motor presente funcionamiento irregular ni misfire en este caso nuevo. "
           "¿De dónde obtuviste ese síntoma? ¿Fue mencionado por mí en este caso o proviene del diagnóstico anterior? "
           "No generes hipótesis ni modifiques los datos registrados.")

def ejecutar_async(func):
    """Ejecuta regresiones asíncronas sin depender de pytest-asyncio en CI."""
    @wraps(func)
    def wrapper():
        return asyncio.run(func())
    return wrapper


class RepositorioFalso:
    def __init__(self, estado):
        self.estado = estado
        self.guardados = 0
    async def get_session(self, session_id):
        return self.estado
    async def save_session(self, *args, **kwargs):
        self.guardados += 1

@ejecutar_async
async def test_consulta_misfire_no_modifica_estado():
    estado = ConversationState(session_id="misfire-consulta", case_id="caso-nuevo")
    estado.registrar_pregunta(QuestionIntent.CONFIRMACION_ALTERNATIVA, "¿Cuál hipótesis?", hipotesis=["Bobina", "Bujías"])
    estado.top3_actual = [{"falla": "Bobina", "probabilidad": 0.8}]
    anterior = copy.deepcopy(estado.exportar_dict())
    repositorio = RepositorioFalso(estado)
    resultado = await OrquestadorConversacion(repositorio).procesar_turno(estado.session_id, MENSAJE, gestor_diagnostico=None)
    assert resultado["decision"] == "CONSULTA_MEMORIA"
    assert estado.exportar_dict() == anterior
    assert repositorio.guardados == 0
    assert estado.obtener_hecho("falla_confirmada_usuario") is None

@pytest.mark.parametrize("texto", [MENSAJE, "¿De dónde salió el síntoma misfire?", "¿Por qué registraste misfire?"])
def test_detecta_consultas_de_procedencia(texto):
    assert ExtractorHechos.es_consulta_memoria(texto)

@pytest.mark.parametrize("texto", ["1", "la 1", "opción 2", "la primera"])
def test_opciones_validas(texto):
    assert PATRON_OPCION_NUMERICA.fullmatch(texto)

@pytest.mark.parametrize("texto", [MENSAJE, "la primera hipótesis, ¿de dónde salió?", "1 ¿por qué?", "No he elegido la 1"])
def test_consultas_no_son_opciones(texto):
    assert not PATRON_OPCION_NUMERICA.fullmatch(texto)

def test_opcion_solo_en_contexto_de_confirmacion():
    estado = ConversationState(session_id="sin-confirmacion")
    estado.registrar_pregunta(QuestionIntent.CODIGO_DTC, "¿Qué código aparece?", hipotesis=["Bobina"])
    interpretar_respuesta_corta(estado, "1")
    assert estado.obtener_hecho("falla_confirmada_usuario") is None

@pytest.mark.parametrize("intent", [QuestionIntent.DISCRIMINACION_TOP3, QuestionIntent.CONFIRMACION_ALTERNATIVA])
@pytest.mark.parametrize("texto,indice", [("1", 1), ("2", 2), ("3", 3), ("la primera", 1)])
def test_seleccion_provisional_sin_confirmar(intent, texto, indice):
    estado = ConversationState(session_id="opciones", case_id="caso-activo")
    estado.registrar_pregunta(intent, "Elige una opción", hipotesis=["Bobina", "Bujías", "Inyector"])
    anterior = copy.deepcopy(estado.exportar_dict())
    resultado = interpretar_respuesta_corta(estado, texto)
    assert resultado["categoria_respuesta"] == "OPCION_NUMERICA_PROVISIONAL"
    assert resultado["indice_opcion"] == indice
    assert "diagnostico_forzado" not in resultado
    assert estado.obtener_hecho("falla_confirmada_usuario") is None
    assert estado.exportar_dict() == anterior

@pytest.mark.parametrize("intent", [QuestionIntent.DISCRIMINACION_TOP3, QuestionIntent.CONFIRMACION_ALTERNATIVA])
def test_pregunta_respondida_no_permite_seleccion(intent):
    estado = ConversationState(session_id="respondida")
    estado.registrar_pregunta(intent, "Elige una opción", hipotesis=["Bobina", "Bujías"])
    estado.registrar_respuesta("2", "OPCION_NUMERICA_PROVISIONAL:Bujías")
    resultado = interpretar_respuesta_corta(estado, "1")
    assert not resultado or resultado.get("categoria_respuesta") != "OPCION_NUMERICA_PROVISIONAL"
    assert estado.obtener_hecho("falla_confirmada_usuario") is None

def test_pregunta_pendiente_de_otro_contexto_no_permite_seleccion():
    estado = ConversationState(session_id="caso-distinto", case_id="caso-nuevo")
    estado.registrar_pregunta(QuestionIntent.DISCRIMINACION_TOP3, "Elige", hipotesis=["Bobina"])
    estado.pending_question = {"intent": QuestionIntent.CODIGO_DTC.value, "texto": "¿Qué DTC?"}
    resultado = interpretar_respuesta_corta(estado, "1")
    assert not resultado or resultado.get("categoria_respuesta") != "OPCION_NUMERICA_PROVISIONAL"
    assert estado.obtener_hecho("falla_confirmada_usuario") is None

def test_consulta_tecnica_no_es_memoria():
    assert not ExtractorHechos.es_consulta_memoria("¿Por qué ocurre un misfire?")


class _GestorSinServicios:
    session_manager = None

@ejecutar_async
async def test_top3_opcion_dos_pide_evidencia_sin_confirmar():
    repo = InMemoryConversationRepository()
    estado = ConversationState(session_id="flujo-top3", case_id="caso-top3")
    estado.registrar_pregunta(
        QuestionIntent.DISCRIMINACION_TOP3, "Elige la situación que mejor describe el vehículo",
        opciones=["Falla A", "Falla B", "Falla C"], hipotesis=["Falla A", "Falla B", "Falla C"],
    )
    await repo.save_session(estado.session_id, estado)
    resultado = await OrquestadorConversacion(repo).procesar_turno(estado.session_id, "2", _GestorSinServicios())
    actual = await repo.get_session(estado.session_id)
    assert resultado["decision"] == "COMPROBACION_HIPOTESIS_PROVISIONAL"
    assert "Falla B" in resultado["respuesta_texto"]
    assert actual.ultima_pregunta()["intent"] == QuestionIntent.MEDICION_TECNICA.value
    assert actual.ultima_pregunta()["metadata"]["hipotesis_provisional"] == "Falla B"
    assert actual.pending_question["intent"] == QuestionIntent.MEDICION_TECNICA.value
    assert actual.pending_question["related_hypothesis"] == "Falla B"
    assert actual.pending_question["case_id"] == "caso-top3"
    assert actual.pending_question["texto"] == resultado["pregunta_final"]
    assert actual.obtener_hecho("falla_confirmada_usuario") is None
    assert actual.confianza_actual == 0.0
    assert len(actual.respuestas_obtenidas) == 1

@ejecutar_async
async def test_consulta_misfire_pr29_no_modifica_estado():
    repo = InMemoryConversationRepository()
    estado = ConversationState(session_id="misfire-pr29", case_id="caso-nuevo")
    estado.registrar_pregunta(
        QuestionIntent.DISCRIMINACION_TOP3, "Elige",
        opciones=["Misfire", "Combustible"], hipotesis=["Bobinas", "Inyectores"],
    )
    await repo.save_session(estado.session_id, estado)
    antes = copy.deepcopy(estado.exportar_dict())
    resultado = await OrquestadorConversacion(repo).procesar_turno(
        estado.session_id, "La 1: ¿cuál es el origen del misfire? No modifiques el diagnóstico.", _GestorSinServicios(),
    )
    assert resultado["decision"] == "CONSULTA_MEMORIA"
    assert (await repo.get_session(estado.session_id)).exportar_dict() == antes

@ejecutar_async
async def test_top3_seleccion_y_respuesta_evidencia_sin_confirmacion_automatica():
    repo = InMemoryConversationRepository()
    estado = ConversationState(session_id="evidencia-top3", case_id="caso-top3")
    estado.registrar_pregunta(
        QuestionIntent.DISCRIMINACION_TOP3, "Elige",
        opciones=["Batería", "Alternador"], hipotesis=["Batería descargada", "Alternador defectuoso"],
    )
    await repo.save_session(estado.session_id, estado)
    orquestador = OrquestadorConversacion(repo)
    seleccion = await orquestador.procesar_turno(estado.session_id, "2", _GestorSinServicios())
    assert seleccion["decision"] == "COMPROBACION_HIPOTESIS_PROVISIONAL"
    # La respuesta posterior debe pasar por la extracción ordinaria de hechos.
    # Requiere un gestor diagnóstico simulado integral para validar el resultado final.
    actual = await repo.get_session(estado.session_id)
    assert actual.ultima_pregunta()["intent"] == QuestionIntent.MEDICION_TECNICA.value
    assert actual.obtener_hecho("falla_confirmada_usuario") is None

@ejecutar_async
async def test_no_puedo_medir_no_confirma_ni_descarta_hipotesis():
    repo = InMemoryConversationRepository()
    estado = ConversationState(session_id="sin-medicion", case_id="caso-sin-medicion")
    estado.registrar_pregunta(
        QuestionIntent.DISCRIMINACION_TOP3, "Elige",
        opciones=["Batería", "Alternador"], hipotesis=["Batería descargada", "Alternador defectuoso"],
    )
    await repo.save_session(estado.session_id, estado)
    orquestador = OrquestadorConversacion(repo)
    seleccion = await orquestador.procesar_turno(estado.session_id, "2", _GestorSinServicios())
    assert seleccion["decision"] == "COMPROBACION_HIPOTESIS_PROVISIONAL"
    previo = await repo.get_session(estado.session_id)
    assert previo.pending_question["related_hypothesis"] == "Alternador defectuoso"
    assert previo.pending_question["case_id"] == "caso-sin-medicion"
    respuesta = await orquestador.procesar_turno(
        estado.session_id, "No puedo realizar esa medición", _GestorSinServicios(),
    )
    actual = await repo.get_session(estado.session_id)
    assert actual.case_id == "caso-sin-medicion"
    assert actual.obtener_hecho("falla_confirmada_usuario") is None
    assert "Alternador defectuoso" not in actual.hipotesis_descartadas
    assert respuesta["decision"] != "DIAGNOSTICO_FORZADO"

@ejecutar_async
async def test_top3_medicion_con_unidad_actualiza_hechos_y_conserva_caso():
    """Integra selección por orquestador, medición por intérprete y persistencia.

    El avance diagnóstico completo del segundo turno requiere un gestor real/simulado.
    """
    repo = InMemoryConversationRepository()
    estado = ConversationState(session_id="evidencia-medida", case_id="caso-medicion")
    estado.registrar_pregunta(
        QuestionIntent.DISCRIMINACION_TOP3, "Elige",
        opciones=["Batería", "Alternador"],
        hipotesis=["Batería descargada", "Alternador defectuoso"],
    )
    await repo.save_session(estado.session_id, estado)
    respuesta = await OrquestadorConversacion(repo).procesar_turno(
        estado.session_id, "2", _GestorSinServicios(),
    )
    assert respuesta["decision"] == "COMPROBACION_HIPOTESIS_PROVISIONAL"
    recuperado = await repo.get_session(estado.session_id)
    assert recuperado.pending_question["related_hypothesis"] == "Alternador defectuoso"
    assert recuperado.pending_question["case_id"] == "caso-medicion"
    assert len(recuperado.respuestas_obtenidas) == 1

    interpretacion = interpretar_respuesta_corta(recuperado, "El alternador marca 14.2 V")
    assert interpretacion is not None
    assert interpretacion["categoria_respuesta"] == "NUMERICO"
    recuperado.registrar_respuesta("El alternador marca 14.2 V", "NUMERICO")
    await repo.save_session(recuperado.session_id, recuperado)
    final = await repo.get_session(recuperado.session_id)
    assert final.case_id == "caso-medicion"
    assert final.obtener_hecho("medicion_voltaje_alternador") is not None
    assert final.obtener_hecho("falla_confirmada_usuario") is None
    assert "Alternador defectuoso" not in final.hipotesis_descartadas
    assert len(final.respuestas_obtenidas) == 2
    assert final.preguntas_realizadas[-1]["metadata"]["hipotesis_provisional"] == "Alternador defectuoso"
    assert final.pending_question is None


@ejecutar_async
async def test_top3_medicion_segundo_turno_por_orquestador_real():
    """La evidencia atraviesa dos turnos reales sin forzar una avería."""
    from types import SimpleNamespace

    class GestorDiagnosticoSimulado:
        session_manager = None

        def procesar_consulta_texto(self, **kwargs):
            assert kwargs.get("diagnostico_forzado") is None
            return SimpleNamespace(
                predicciones_ml=[], diagnostico_ml=None, confianza_ml=0.0,
                respuesta_texto="", llm_usado=False, respuesta_limitada=False,
                contexto_manual_verificado="",
            )

    repo = InMemoryConversationRepository()
    estado = ConversationState(session_id="medicion-e2e", case_id="caso-medicion-e2e")
    estado.registrar_pregunta(
        QuestionIntent.DISCRIMINACION_TOP3, "Elige una opción",
        opciones=["Batería", "Alternador"],
        hipotesis=["Batería descargada", "Alternador defectuoso"],
    )
    await repo.save_session(estado.session_id, estado)
    orquestador = OrquestadorConversacion(repo)
    gestor = GestorDiagnosticoSimulado()
    primero = await orquestador.procesar_turno(estado.session_id, "2", gestor)
    assert primero["decision"] == "COMPROBACION_HIPOTESIS_PROVISIONAL"
    segundo = await orquestador.procesar_turno(
        estado.session_id, "El alternador marca 14.2 V", gestor,
    )
    final = await repo.get_session(estado.session_id)
    assert segundo["decision"] != "DIAGNOSTICO_FORZADO"
    assert final.case_id == "caso-medicion-e2e"
    assert final.obtener_hecho("medicion_voltaje_alternador") is not None
    assert final.obtener_hecho("falla_confirmada_usuario") is None
    assert "Alternador defectuoso" not in final.hipotesis_descartadas
    assert len(final.respuestas_obtenidas) >= 2
