"""Regresiones de dominio, aislamiento y preguntas aplicables de Fase 9.13."""

from __future__ import annotations

import pytest

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.models import (
    ConversationPhase,
    ConversationState,
    EstadoOperativo,
    QuestionIntent,
)
from src.core.conversacion.segmentador_casos import (
    DecisionTransicion,
    SegmentadorCasos,
    SubsistemaVehicular,
)

MENSAJE_TRANSMISION = (
    "Hola, tengo un problema con mi carro automático. Cuando pongo la palanca en D entra normal, "
    "pero cuando paso a R demora unos segundos en enganchar. A veces tengo que acelerar un poquito "
    "para que recién entre la reversa y cuando entra da un golpe. Hacia adelante los cambios se "
    "sienten normales. No aparece ninguna luz de advertencia en el tablero y todavía no he revisado nada."
)


def _seleccion(dominio: str, mensaje: str) -> tuple[ConversationState, tuple]:
    estado = ConversationState(session_id=f"fase913-{dominio}", case_id=f"case-{dominio}")
    estado.dominio_probable = dominio
    ExtractorHechos.extraer_y_actualizar(estado, mensaje)
    seleccion = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    assert seleccion is not None
    return estado, seleccion


def test_incidente_real_cambia_de_caso_y_no_hereda_interrogatorio() -> None:
    estado = ConversationState(session_id="incidente-913", case_id="case-motor")
    estado.fase = ConversationPhase.RESULTADO
    estado.estado_operativo = EstadoOperativo.MARCHA
    estado.dominio_probable = SubsistemaVehicular.MARCHA_MOTOR.value
    estado.registrar_hecho("sintoma_misfire", "misfire y pérdida de potencia")
    estado.top3_actual = [{"falla": "Falla en bujías o bobinas", "probabilidad": 0.70}]
    estado.falla_principal = "Falla en bujías o bobinas"
    estado.registrar_pregunta(QuestionIntent.TEMPERATURA_APARICION, "¿Falla en frío o caliente?")
    estado.respuestas_obtenidas.append({"texto": "en ambos"})
    estado.historial_mensajes_usuario.append("tironea y pierde potencia")
    estado.bloquear_herramienta("probador_chispa")
    estado.bloquear_prueba("prueba_chispa", "probador_chispa")

    resultado = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario=MENSAJE_TRANSMISION,
        estado_detectado_mensaje=EstadoOperativo.MARCHA,
        seniales_mensaje={"senial_marcha": True},
        seniales_heredadas={"senial_marcha": True},
    )
    assert resultado.decision == DecisionTransicion.CAMBIO_DE_CASO
    SegmentadorCasos.archivar_y_limpiar_caso(estado, resultado.nuevo_case_id)

    assert estado.case_id != "case-motor"
    assert estado.preguntas_realizadas == []
    assert estado.respuestas_obtenidas == []
    assert estado.herramientas_no_disponibles == []
    assert estado.pruebas_no_disponibles == []
    assert estado.historial_mensajes_usuario == []
    assert estado.top3_actual == []
    assert estado.falla_principal is None
    assert estado.hechos == {}
    assert estado.hechos_historicos[-1]["preguntas_realizadas"]
    assert estado.hechos_historicos[-1]["historial_mensajes_usuario"] == [
        "tironea y pierde potencia"
    ]


def test_transmision_descarta_pregunta_termica_de_motor_antes_del_score() -> None:
    estado, seleccion = _seleccion("TRANSMISION", MENSAJE_TRANSMISION)
    pregunta, _, intent, candidatas, descartadas = seleccion

    assert estado.dominio_probable == "TRANSMISION"
    assert intent == QuestionIntent.COMPONENTE_REVISADO
    assert "ATF" in pregunta
    termicas_motor = [
        c for c in candidatas
        if c["intent"] == QuestionIntent.TEMPERATURA_APARICION.value
        and c["dominio_pregunta"] == "MARCHA_MOTOR"
    ]
    assert termicas_motor and all(not c["aplicable"] for c in termicas_motor)
    assert any(
        d["motivo"] == "INCOMPATIBLE_DOMINIO"
        and d["score_information_gain"] == 50
        for d in descartadas
    )


@pytest.mark.parametrize(
    ("dominio", "mensaje", "texto_prohibido"),
    [
        ("FRENOS", "El volante vibra fuerte únicamente al frenar.", "temperatura de trabajo"),
        ("ARRANQUE", "Al girar la llave solo hace clic y no arranca.", "carretera"),
        ("CLIMATIZACION", "El aire acondicionado no enfría y el compresor no acopla.", "al frenar"),
    ],
)
def test_pregunta_seleccionada_no_cruza_dominios(
    dominio: str,
    mensaje: str,
    texto_prohibido: str,
) -> None:
    _, seleccion = _seleccion(dominio, mensaje)
    pregunta = seleccion[0].lower()
    assert texto_prohibido not in pregunta


def test_motor_con_falla_termica_si_permite_pregunta_de_temperatura() -> None:
    _, seleccion = _seleccion(
        "MARCHA_MOTOR",
        "El motor tironea y pierde fuerza al acelerar, todavía no se revisó nada.",
    )
    pregunta, _, intent, _, _ = seleccion
    assert intent == QuestionIntent.TEMPERATURA_APARICION
    assert "temperatura de trabajo" in pregunta.lower()


def test_transmision_termica_se_permite_si_el_diferencial_la_justifica() -> None:
    estado = ConversationState(session_id="transmision-termica", case_id="case-transmision")
    estado.dominio_probable = "TRANSMISION"
    estado.registrar_hecho(
        "componente_revisado",
        "nivel ATF revisado",
        categoria="antecedente",
    )
    estado.top3_actual = [
        {"falla": "Degradación o viscosidad incorrecta del aceite de caja ATF", "probabilidad": 0.62}
    ]

    seleccion = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    assert seleccion is not None
    pregunta, _, intent, candidatas, _ = seleccion
    assert intent == QuestionIntent.TEMPERATURA_APARICION
    assert "transmisión está fría" in pregunta
    assert sum(1 for c in candidatas if c["aplicable"] and c["pregunta"] == pregunta) == 1


def test_aire_acondicionado_encendido_es_modificador_no_nueva_averia() -> None:
    assert (
        SegmentadorCasos.detectar_subsistema_texto("Se nota más con el aire acondicionado encendido")
        == SubsistemaVehicular.DESCONOCIDO
    )


def test_medicion_electrica_pertenece_al_mismo_caso_de_arranque() -> None:
    assert SegmentadorCasos.es_sintoma_coexistente(
        SubsistemaVehicular.ARRANQUE,
        SubsistemaVehicular.ELECTRICO,
        "La batería mide 12.6 V y los bornes están limpios.",
    )
