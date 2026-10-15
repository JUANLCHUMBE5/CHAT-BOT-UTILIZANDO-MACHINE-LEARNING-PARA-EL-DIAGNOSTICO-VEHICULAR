"""Regresiones de los mensajes reales auditados, sin proveedores externos."""

from __future__ import annotations

import pytest

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas
from src.core.conversacion.models import ConversationState, FactState, QuestionIntent
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository


class _SessionManagerMock:
    def cargar_contexto(self, *_args: object, **_kwargs: object) -> None:
        return None


class _GestorMock:
    session_manager = _SessionManagerMock()


def _estado(texto: str) -> ConversationState:
    estado = ConversationState(session_id="regresion")
    ExtractorHechos.extraer_y_actualizar(estado, texto)
    return estado


@pytest.mark.parametrize(
    "texto",
    [
        "No presenta pérdida de potencia.",
        "Mi vehículo no tiene pérdida de potencia y funciona normal.",
        "Sin pérdida de fuerza; solo demora en arrancar.",
    ],
)
def test_negaciones_de_potencia_no_se_registran_como_sintoma_positivo(texto: str) -> None:
    hecho = _estado(texto).obtener_hecho("sintoma_pérdida_de_potencia")
    assert hecho is not None
    assert hecho.estado == FactState.AUSENTE_NEGADO


def test_correccion_reemplaza_sintoma_previo_y_conserva_demora_numerica() -> None:
    estado = ConversationState(session_id="correccion")
    ExtractorHechos.extraer_y_actualizar(estado, "Pierde potencia al acelerar.")

    ExtractorHechos.extraer_y_actualizar(
        estado,
        "No, entendiste mal. Mi vehículo NO tiene pérdida de potencia. "
        "El único problema es que demora unos 5 segundos en arrancar cuando está frío.",
    )

    potencia = estado.obtener_hecho("sintoma_pérdida_de_potencia")
    demora = estado.obtener_hecho("sintoma_demora_arranque")
    assert potencia is not None and potencia.estado == FactState.AUSENTE_NEGADO
    assert demora is not None and demora.estado == FactState.CONFIRMADO


@pytest.mark.anyio
async def test_consulta_memoria_con_nuevo_diagnostico_no_reinicia_ni_muta_estado() -> None:
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    estado = ConversationState(session_id="memoria", case_id="caso-activo")
    estado.registrar_hecho("sintoma_demora_arranque", "demora en arrancar", categoria="sintoma")
    estado.registrar_hecho(
        "sintoma_pérdida_de_potencia",
        "pérdida de potencia",
        categoria="sintoma",
        estado=FactState.AUSENTE_NEGADO,
    )
    await repo.save_session("memoria", estado)
    antes = estado.exportar_dict()

    respuesta = await orquestador.procesar_turno(
        session_id="memoria",
        texto_usuario=(
            "¿Cuál es el síntoma principal que tienes registrado para mi vehículo? "
            "Indica también qué síntomas te dije que NO presenta. "
            "No generes un nuevo diagnóstico todavía."
        ),
        gestor_diagnostico=_GestorMock(),
    )

    despues = await repo.get_session("memoria")
    assert respuesta["decision"] == "CONSULTA_MEMORIA"
    assert respuesta["case_id"] == "caso-activo"
    assert despues is not None and despues.exportar_dict() == antes


@pytest.mark.anyio
async def test_consulta_memoria_tiene_precedencia_sobre_imposibilidad_y_devuelve_hechos_tecnicos() -> None:
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    estado = ConversationState(
        session_id="corolla-memoria",
        case_id="corolla-activo",
        marca="Toyota",
        modelo="Corolla",
        anio="2015",
        motor="1.8",
        combustible="Gasolina",
    )
    estado.registrar_hecho("sintoma_demora_arranque", "demora cinco segundos en arrancar", categoria="sintoma")
    estado.registrar_hecho(
        "sintoma_pérdida_de_potencia",
        "pérdida de potencia",
        categoria="sintoma",
        estado=FactState.AUSENTE_NEGADO,
    )
    estado.bloquear_herramienta("probador de bobinas")
    await repo.save_session(estado.session_id, estado)
    antes = estado.exportar_dict()

    respuesta = await orquestador.procesar_turno(
        session_id=estado.session_id,
        texto_usuario=(
            "No puedo comprobar bobinas por falta de herramientas; consulta la memoria "
            "sin generar un diagnóstico nuevo."
        ),
        gestor_diagnostico=_GestorMock(),
    )

    despues = await repo.get_session(estado.session_id)
    texto = respuesta["respuesta_texto"].lower()
    assert respuesta["decision"] == "CONSULTA_MEMORIA"
    assert "toyota corolla 2015 1.8 gasolina" in texto
    assert "demora cinco segundos" in texto
    assert "pérdida de potencia" in texto or "perdida de potencia" in texto
    assert "probador de bobinas" in texto
    assert "common rail" not in texto
    assert "taller especializado" not in texto
    assert despues is not None and despues.exportar_dict() == antes


@pytest.mark.anyio
async def test_orientacion_excluye_common_rail_almacenado_para_gasolina() -> None:
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    estado = ConversationState(
        session_id="corolla-orientacion",
        case_id="corolla-orientacion-activo",
        combustible="Gasolina",
        active_system="arranque",
        active_symptoms=["Demora cinco segundos en arrancar en frío."],
        top3_actual=[
            {
                "falla": "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)",
                "probabilidad": 0.82,
                "origen_probabilidad": "SVM",
            }
        ],
    )
    estado.registrar_hecho("combustible", "Gasolina", categoria="vehiculo")
    await repo.save_session(estado.session_id, estado)

    respuesta = await orquestador.procesar_turno(
        session_id=estado.session_id,
        texto_usuario="No puedo comprobar las bobinas por falta de herramientas.",
        gestor_diagnostico=_GestorMock(),
    )

    texto = respuesta["respuesta_texto"].lower()
    assert respuesta["decision"] == "ORIENTACION_PROVISIONAL"
    assert "common rail" not in texto
    assert "diésel" not in texto and "diesel" not in texto
    assert "taller especializado" not in texto
    assert respuesta["estado"].top3_actual == []
    assert respuesta["estado"].trazabilidad[-1]["exclusiones_compatibilidad"][0]["motivo"] == (
        "INCOMPATIBLE_CON_HECHO_CONFIRMADO"
    )


def test_mensaje_multidato_extrae_vehiculo_sintoma_y_negacion() -> None:
    estado = _estado(
        "Mi placa es ABC-1234, tengo un Toyota Corolla 2015 1.8 gasolina. "
        "Demora cinco segundos en arrancar por las mañanas, pero después funciona "
        "normalmente y no pierde potencia."
    )

    assert (estado.placa, estado.marca, estado.modelo, estado.anio, estado.motor, estado.combustible) == (
        "ABC-1234", "Toyota", "Corolla", "2015", "1.8", "Gasolina"
    )
    assert estado.obtener_hecho("sintoma_demora_arranque") is not None
    potencia = estado.obtener_hecho("sintoma_pérdida_de_potencia")
    assert potencia is not None and potencia.estado == FactState.AUSENTE_NEGADO

@pytest.mark.anyio
async def test_consulta_misfire_durante_seleccion_pendiente_es_solo_lectura() -> None:
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    estado = ConversationState(session_id="misfire", case_id="caso-misfire")
    estado.registrar_pregunta(
        intent=QuestionIntent.DISCRIMINACION_TOP3,
        texto="Responde indicando el número que describe mejor el comportamiento.",
        opciones=["Falla de encendido", "Combustible"],
        hipotesis=["Falla en bujías o bobinas (misfire)", "Falla de combustible"],
    )
    await repo.save_session(estado.session_id, estado)
    antes = estado.exportar_dict()

    respuesta = await orquestador.procesar_turno(
        session_id=estado.session_id,
        texto_usuario="La 1: ¿cuál es el origen del misfire? No modifiques el diagnóstico.",
        gestor_diagnostico=_GestorMock(),
    )

    despues = await repo.get_session(estado.session_id)
    assert respuesta["decision"] == "CONSULTA_MEMORIA"
    assert despues is not None and despues.exportar_dict() == antes
    assert despues.obtener_hecho("falla_confirmada_usuario") is None


def test_seleccion_numerica_valida_sigue_seleccionando_y_pregunta_invalida_no() -> None:
    estado = ConversationState(session_id="seleccion-valida")
    estado.registrar_pregunta(
        intent=QuestionIntent.DISCRIMINACION_TOP3,
        texto="Elige una opción.",
        opciones=["Uno", "Dos"],
        hipotesis=["Hipótesis uno", "Hipótesis dos"],
    )
    assert InterpreteRespuestasCortas.interpretar(estado, "opción 1")["valor"] == "Hipótesis uno"

    sin_pregunta = ConversationState(session_id="sin-pregunta")
    sin_pregunta.registrar_pregunta(
        intent=QuestionIntent.GENERAL,
        texto="¿Qué lectura observas?",
        opciones=[],
        hipotesis=["Hipótesis uno", "Hipótesis dos"],
    )
    assert InterpreteRespuestasCortas.interpretar(sin_pregunta, "opción 1") is None


@pytest.mark.anyio
async def test_reinicio_no_asigna_confianza_de_clasificacion() -> None:
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    estado = ConversationState(session_id="reinicio", case_id="caso-anterior")
    await repo.save_session(estado.session_id, estado)

    respuesta = await orquestador.procesar_turno(
        session_id=estado.session_id,
        texto_usuario="nuevo caso",
        gestor_diagnostico=_GestorMock(),
    )

    assert respuesta["decision"] == "REINICIO"
    assert respuesta["confianza_ml"] == 0.0
    assert respuesta["case_id"] != "caso-anterior"

