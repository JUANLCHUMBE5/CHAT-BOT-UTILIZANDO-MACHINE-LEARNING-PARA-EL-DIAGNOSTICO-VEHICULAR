"""Stress conversacional sintético local: memoria y trazabilidad por turno."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.core.conversacion.models import ConversationState, FactType, QuestionIntent
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository

MENSAJES_SIN_HERRAMIENTA = (
    "No tengo escáner",
    "No cuento con manómetro",
    "No sé obtener STFT/LTFT",
    "No puedo leer esa medición por ahora",
    "No tengo el dato todavía",
    "Sin herramientas para comprobarlo hoy",
)


def _gestor_sintetico():
    falla = "Inyectores sucios o filtro de combustible obstruido"
    resultado = SimpleNamespace(
        respuesta_texto="Orientación sintética pendiente de comprobación.",
        diagnostico_ml=falla,
        confianza_ml=0.34,
        origen_confianza="SVM",
        predicciones_ml=[
            SimpleNamespace(falla=falla, probabilidad=0.34, origen_probabilidad="SVM"),
            SimpleNamespace(
                falla="Bomba de gasolina quemada o con baja presión",
                probabilidad=0.19,
                origen_probabilidad="SVM",
            ),
        ],
        contexto_manual="",
        contexto_manual_verificado="",
        titulo_manual="Corpus sintético no validado",
        llm_usado=False,
        respuesta_limitada=True,
    )
    gestor = SimpleNamespace(session_manager=None, procesar_consulta_texto=MagicMock(return_value=resultado))
    return gestor


@pytest.mark.anyio
@pytest.mark.parametrize("cantidad_turnos", [10, 20, 30])
async def test_memoria_y_traza_se_conservan_en_hilos_largos_sinteticos(cantidad_turnos):
    session_id = f"t05-versa-{cantidad_turnos}"
    case_id = f"case-{cantidad_turnos}"
    repo = InMemoryConversationRepository()
    estado = ConversationState(
        session_id=session_id,
        case_id=case_id,
        active_problem_id=f"problem-{cantidad_turnos}",
        active_system="combustible_admision",
        placa="TST000",
        marca="Nissan",
        modelo="Versa",
    )
    estado.active_symptoms.append("Nissan Versa presenta mezcla pobre al acelerar")
    estado.historial_mensajes_usuario.append("Nissan Versa presenta mezcla pobre al acelerar")
    estado.registrar_hecho(
        "mezcla_pobre_reportada",
        "mezcla pobre al acelerar",
        categoria="sintoma",
        tipo=FactType.SINTOMA,
    )
    estado.registrar_pregunta(
        QuestionIntent.MEDICION_TECNICA,
        "¿Qué DTC o valores STFT/LTFT muestra el escáner?",
        hipotesis=["Mezcla pobre en sistema de admisión"],
    )
    await repo.save_session(session_id, estado)

    gestor = _gestor_sintetico()
    flujo = OrquestadorConversacion(repo)
    trazas_vistas = []

    for indice in range(cantidad_turnos):
        mensaje = MENSAJES_SIN_HERRAMIENTA[indice % len(MENSAJES_SIN_HERRAMIENTA)]
        resultado = await flujo.procesar_turno(session_id, mensaje, gestor, proveedor="sandbox_local")
        estado_turno = resultado["estado"]
        assert estado_turno.case_id == case_id
        assert estado_turno.active_system == "combustible_admision"
        assert estado_turno.obtener_hecho("mezcla_pobre_reportada") is not None

        traza = estado_turno.trazabilidad[-1]
        assert traza["mensaje_original"] == mensaje
        assert traza["tipo_mensaje"]
        assert isinstance(traza["hechos_actualizados"], list)
        assert isinstance(traza["top3"], list)
        assert traza["respuesta_enviada"].strip()
        assert traza["contexto_previo"]["case_id"] == case_id
        trazas_vistas.append(traza)

    assert len(trazas_vistas) == cantidad_turnos
    preguntas = [
        " ".join(traza["pregunta_final"].casefold().split())
        for traza in trazas_vistas
        if traza.get("pregunta_final")
    ]
    assert len(preguntas) == len(set(preguntas))
    estado_final = await repo.get_session(session_id)
    assert estado_final.case_id == case_id
    assert estado_final.turno_actual == cantidad_turnos
    assert len(estado_final.preguntas_realizadas) <= estado_final.max_repreguntas
