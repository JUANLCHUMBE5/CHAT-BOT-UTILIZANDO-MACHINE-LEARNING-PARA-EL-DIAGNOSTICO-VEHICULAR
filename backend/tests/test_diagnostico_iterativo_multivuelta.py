"""Pruebas multivuelta de diagnostico iterativo, no descarte prematuro y reevaluacion."""

import asyncio
from functools import wraps
from types import SimpleNamespace
import pytest

from src.core.conversacion.models import ConversationState, FactState, FactType, QuestionIntent
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.conversacion.respuestas_cortas.interprete_intenciones import interpretar_respuesta_corta
from src.core.conversacion.respuestas_cortas.patrones_deteccion import PATRON_NINGUNA_COINCIDE


def ejecutar_async(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper


class GestorDiagnosticoMock:
    session_manager = None

    def __init__(self):
        self.consultas = []

    def procesar_consulta_texto(self, **kwargs):
        self.consultas.append(kwargs)
        return SimpleNamespace(
            predicciones_ml=[
                {"falla": "Falla de encendido (bujias/bobinas)", "probabilidad": 0.65},
                {"falla": "Bomba de combustible defectuosa", "probabilidad": 0.25},
                {"falla": "Sensor de posicion de cigueñal (CKP)", "probabilidad": 0.10},
            ],
            diagnostico_ml="Falla de encendido (bujias/bobinas)",
            confianza_ml=0.65,
            respuesta_texto="Diagnostico basado en sintomas reportados.",
            llm_usado=False,
            respuesta_limitada=False,
            contexto_manual_verificado="",
        )


def test_patron_ninguna_coincide():
    textos_validos = [
        "ninguna",
        "ninguno",
        "ninguna coincide",
        "ninguna de las anteriores",
        "otra causa",
        "otra cosa",
        "otro motivo",
        "creo que ninguna coincide",
        "me parece que ninguna",
    ]
    for t in textos_validos:
        assert PATRON_NINGUNA_COINCIDE.search(t), f"Fallo en detectar: {t}"

    textos_no_validos = [
        "la 1",
        "si",
        "no arranca el motor",
        "falla en subida",
    ]
    for t in textos_no_validos:
        assert not PATRON_NINGUNA_COINCIDE.fullmatch(t), f"Falso positivo en: {t}"


def test_interpretacion_ninguna_coincide_top3():
    estado = ConversationState(session_id="test-ninguna-1", case_id="caso-1")
    estado.registrar_pregunta(
        intent=QuestionIntent.DISCRIMINACION_TOP3,
        texto="Elige entre las opciones 1, 2 o 3",
        opciones=["Falla A", "Falla B", "Falla C"],
        hipotesis=["Falla A", "Falla B", "Falla C"],
    )
    res = interpretar_respuesta_corta(estado, "ninguna coincide")
    assert res is not None
    assert res["categoria_respuesta"] == "OPCION_NINGUNA_COINCIDE"
    assert res["valor"] == "ninguna_coincide"
    hecho = estado.obtener_hecho("opciones_sugeridas_no_coinciden")
    assert hecho is not None
    assert hecho.estado == FactState.CONFIRMADO


@ejecutar_async
async def test_flujo_multivuelta_no_descarta_hipotesis_al_seleccionar_ninguna():
    repo = InMemoryConversationRepository()
    estado = ConversationState(session_id="multi-1", case_id="caso-multi-1")
    estado.top3_actual = [
        {"falla": "Falla de encendido (bujias/bobinas)", "probabilidad": 0.65},
        {"falla": "Bomba de combustible defectuosa", "probabilidad": 0.25},
        {"falla": "Sensor de posicion de cigueñal (CKP)", "probabilidad": 0.10},
    ]
    estado.falla_principal = "Falla de encendido (bujias/bobinas)"
    estado.confianza_actual = 0.65
    estado.registrar_pregunta(
        QuestionIntent.DISCRIMINACION_TOP3,
        "¿Cual de las siguientes situaciones describe mejor el comportamiento?",
        opciones=["Falla bujias", "Bomba combustible", "Sensor CKP"],
        hipotesis=["Falla bujias", "Bomba combustible", "Sensor CKP"],
    )
    await repo.save_session(estado.session_id, estado)

    orquestador = OrquestadorConversacion(repo)
    gestor = GestorDiagnosticoMock()

    # Turno 2: El mecánico responde "ninguna coincide"
    resp = await orquestador.procesar_turno(estado.session_id, "ninguna coincide", gestor)

    # 1. El bot no debe haber borrado el top3_actual ni renormalizado a cero
    assert resp["decision"] == "PREGUNTAR"
    assert "abiertas sin descartar" in resp["respuesta_texto"] or "considerado" in resp["respuesta_texto"]

    estado_guardado = await repo.get_session(estado.session_id)
    assert estado_guardado is not None
    assert len(estado_guardado.top3_actual) == 3
    assert estado_guardado.top3_actual[0]["falla"] == "Falla de encendido (bujias/bobinas)"
    assert estado_guardado.top3_actual[0]["probabilidad"] == 0.65
    assert len(estado_guardado.hipotesis_descartadas) == 0

    # Turno 3: El mecánico responde con un síntoma adicional
    resp2 = await orquestador.procesar_turno(estado.session_id, "Solo da chispa debil y huele a gasolina cruda", gestor)
    assert resp2 is not None
