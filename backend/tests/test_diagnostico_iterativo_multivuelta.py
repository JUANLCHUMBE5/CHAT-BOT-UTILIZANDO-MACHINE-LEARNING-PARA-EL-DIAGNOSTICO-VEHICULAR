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


@ejecutar_async
async def test_interpretacion_opcion_4_ninguna_coincide():
    estado = ConversationState(session_id="test-opc4", case_id="caso-opc4")
    estado.registrar_pregunta(
        intent=QuestionIntent.DISCRIMINACION_TOP3,
        texto="1. Bujias\n2. Bomba\n3. CKP\n4. Ninguna coincide",
        opciones=["Bujias", "Bomba", "CKP"],
        hipotesis=["Bujias", "Bomba", "CKP"],
    )
    # Usuario envía opción "4"
    res = interpretar_respuesta_corta(estado, "4")
    assert res is not None
    assert res["categoria_respuesta"] == "OPCION_NINGUNA_COINCIDE"
    assert res["indice_opcion"] == 4
    hecho = estado.obtener_hecho("opciones_sugeridas_no_coinciden")
    assert hecho is not None
    assert hecho.valor == "ninguna_coincide"

    # Opción "5" fuera de rango
    res_invalido = interpretar_respuesta_corta(estado, "5")
    assert res_invalido is not None
    assert res_invalido["categoria_respuesta"] == "OPCION_NUMERICA_FUERA_DE_RANGO"
    assert res_invalido["total_opciones"] == 4


@ejecutar_async
async def test_ciclo_completo_reevaluacion_svm_multivuelta():
    repo = InMemoryConversationRepository()
    estado = ConversationState(session_id="multi-reeval-1", case_id="caso-reeval-1")
    estado.top3_actual = [
        {"falla": "Falla de encendido (bujias/bobinas)", "probabilidad": 0.60},
        {"falla": "Bomba de combustible defectuosa", "probabilidad": 0.25},
        {"falla": "Sensor de posicion de cigueñal (CKP)", "probabilidad": 0.15},
    ]
    estado.falla_principal = "Falla de encendido (bujias/bobinas)"
    estado.confianza_actual = 0.60
    estado.registrar_pregunta(
        QuestionIntent.DISCRIMINACION_TOP3,
        "¿Cuál de las siguientes situaciones describe mejor el comportamiento?\n1. Bujías\n2. Bomba\n3. CKP\n4. Ninguna",
        opciones=["Falla bujias", "Bomba combustible", "Sensor CKP"],
        hipotesis=["Falla bujias", "Bomba combustible", "Sensor CKP"],
    )
    await repo.save_session(estado.session_id, estado)

    # Gestor dinámico que simula cambio de predicciones tras nueva evidencia
    class GestorReevaluacionMock:
        def __init__(self):
            self.turnos_ejecutados = 0

        def procesar_consulta_texto(self, **kwargs):
            self.turnos_ejecutados += 1
            # Tras aportar evidencia de presión de combustible (nueva evidencia)
            return SimpleNamespace(
                predicciones_ml=[
                    {"falla": "Bomba de combustible defectuosa", "probabilidad": 0.70},
                    {"falla": "Falla de encendido (bujias/bobinas)", "probabilidad": 0.20},
                    {"falla": "Filtro de combustible obstruido", "probabilidad": 0.10},
                ],
                diagnostico_ml="Bomba de combustible defectuosa",
                confianza_ml=0.70,
                respuesta_texto="Reevaluación diagnóstica con base en la presión de combustible medida.",
                llm_usado=True,
                respuesta_limitada=False,
                contexto_manual_verificado="Manual OEM: Presión mínima de línea 3.5 bar en riel.",
            )

    gestor = GestorReevaluacionMock()
    orquestador = OrquestadorConversacion(repo)

    # 1. El mecánico indica opción 4 (ninguna coincide)
    r1 = await orquestador.procesar_turno(estado.session_id, "4", gestor)
    assert r1["decision"] == "PREGUNTAR"
    assert "abiertas sin descartar" in r1["respuesta_texto"] or "considerado" in r1["respuesta_texto"]

    # 2. El mecánico aporta evidencia técnica nueva relevante:
    r2 = await orquestador.procesar_turno(
        estado.session_id,
        "El motor pierde fuerza en subida y tiembla bastante al acelerar",
        gestor,
    )
    assert r2 is not None
    assert gestor.turnos_ejecutados == 1  # procesar_consulta_texto fue invocado con SVM/RAG
    assert r2.get("top3_previo") is not None
    assert r2.get("cambio_ranking") is True
    assert r2["diagnostico_ml"] == "Bomba de combustible defectuosa"
