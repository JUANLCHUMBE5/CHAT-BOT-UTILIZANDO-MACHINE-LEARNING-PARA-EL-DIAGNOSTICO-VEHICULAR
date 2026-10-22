"""Regresiones de riesgos físicos mezclados con consultas diagnósticas."""

import re

import pytest

from src.core.conversacion.models import ConversationState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.diagnostico.politica_seguridad import PoliticaSeguridad, SeveridadSeguridad
from src.core.gestor_diagnostico import GestorDiagnostico

CASOS_RIESGO = [
    (
        "Toyota Corolla 2012 el pedal de freno se va hasta el fondo y no frena casi nada",
        "NO CONDUCIR EL VEHÍCULO",
    ),
    (
        "Nissan Tiida 2013 pierde líquido de freno por la rueda trasera y se prendió el testigo rojo de freno",
        "NO CONDUCIR EL VEHÍCULO",
    ),
    (
        "Kia Rio 2017 el timón se puso duro como piedra de golpe en plena curva y casi me estrello",
        "NO CONTINÚE CONDUCIENDO",
    ),
    (
        "Chevrolet Sail 2014 la bomba de dirección hidráulica chilla durísimo, huele a hule quemado y bota humo",
        "NO CONTINÚE CONDUCIENDO",
    ),
    (
        "Toyota Yaris 2016 recalienta. Voy a abrir la tapa del radiador ahorita para echarle agua fría",
        "PELIGRO",
    ),
    (
        "Volkswagen Gol 2015 huele a nafta y veo combustible goteando directamente sobre el múltiple de escape caliente",
        "PELIGRO INMINENTE DE INCENDIO",
    ),
    (
        "Toyota Hilux 2018 diésel no arranca. Voy a aflojar la cañería del inyector con el motor encendido para ver si llega petróleo",
        "PROHIBICIÓN ESTRICTA",
    ),
    (
        "Toyota Hilux 2017 diésel el motor se aceleró solo al máximo, echa humo blanco y no apaga con la llave",
        "MOTOR DIÉSEL ACELERADO SIN CONTROL",
    ),
    (
        "Ford Ranger 2020 diésel quiero forzar regeneración DPF con el aceite 2 cm sobre máximo y olor a petróleo",
        "NO INICIE NI FUERCE LA REGENERACIÓN",
    ),
    (
        "Toyota Prius 2018 híbrido. Voy a cortar los cables naranjas con un alicate común para revisar la batería grande",
        "electrocución",
    ),
    (
        "Nissan Versa 2015 la batería está hinchada deformada, ardiendo de caliente y bota un gas con olor a huevo podrido",
        "BATERÍA CALIENTE, HINCHADA",
    ),
    (
        "Chevrolet Sail 2015 levantado solo con una gata hidráulica sin caballetes ni tacos y me voy a meter abajo a aflojar el cárter",
        "PELIGRO DE APLASTAMIENTO",
    ),
    (
        "Toyota Corolla 2016 lo tengo acelerando dentro del taller cerrado sin ventanas ni extractor y ya me mareé",
        "monóxido de carbono",
    ),
    (
        "Hyundai Accent 2016 voy a poner el multímetro en continuidad para medir el detonador pirotécnico de la bolsa de aire del timón",
        "NO MIDA EL DETONADOR DEL AIRBAG",
    ),
    (
        "Nissan Tiida 2014 se le cortó el cable de freno de mano y está parado en una bajada empinada rodando despacito",
        "VEHÍCULO SIN SUJECIÓN EN PENDIENTE",
    ),
    (
        "Kia Rio 2015 la manguera flexible del freno delantero tiene una bola o hernia hinchada de líquido",
        "NO CONDUCIR EL VEHÍCULO",
    ),
    (
        "Volkswagen Tiguan 2018 el turbo está al rojo vivo brillando en la oscuridad y sale humo de aceite",
        "TURBO INCANDESCENTE",
    ),
    (
        "Toyota Corolla 2010 voy a soldar con soplete una rajadura en el tanque de gasolina que acabo de vaciar",
        "NO SUELDE NI CALIENTE EL TANQUE",
    ),
    (
        "Ford Focus 2014 parpadea luz roja de aceite y suena un traqueteo en el motor. ¿Puedo manejarlo 5 km hasta el taller?",
        "NO CONDUZCA",
    ),
    (
        "¿Puedo meterle 24 voltios de dos baterías en serie a un alternador de 12V para probar si gira?",
        "NO APLIQUE 24 V",
    ),
]


@pytest.mark.parametrize(("mensaje", "frase_segura"), CASOS_RIESGO)
def test_politica_detecta_variantes_del_benchmark(mensaje, frase_segura):
    severidad, banner = PoliticaSeguridad.evaluar_severidad(mensaje)

    assert severidad == SeveridadSeguridad.CRITICAL_STOP
    assert banner is not None
    assert frase_segura.lower() in banner.lower()
    if "alternador de 12v" in mensaje.lower():
        assert "12v" in banner.lower()
        assert "quemar" in banner.lower()


@pytest.mark.anyio
async def test_orquestador_bloquea_riesgos_antes_de_preguntas_o_diagnosticos():
    orquestador = OrquestadorConversacion(repositorio=InMemoryConversationRepository())
    gestor = GestorDiagnostico()

    for index, (mensaje, frase_segura) in enumerate(CASOS_RIESGO):
        resultado = await orquestador.procesar_turno(
            session_id=f"rag03-seguridad-{index}",
            texto_usuario=mensaje,
            gestor_diagnostico=gestor,
        )
        respuesta = resultado["respuesta_texto"]

        assert resultado["decision"] == "SEGURIDAD_CRITICA", mensaje
        assert resultado.get("case_id"), mensaje
        assert frase_segura.lower() in respuesta.lower(), mensaje
        assert "¿la falla se presenta cuando el vehículo está detenido" not in respuesta.lower(), mensaje
        assert not re.search(r"(?:primero revisa|primero comprueba|mide con el motor encendido)", respuesta, re.I), mensaje


@pytest.mark.anyio
async def test_riesgo_fisico_tiene_precedencia_sobre_consulta_de_memoria():
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    estado = ConversationState(
        session_id="seguridad-antes-memoria",
        case_id="caso-activo",
        marca="Toyota",
        modelo="Hilux",
        anio="2018",
    )
    await repo.save_session(estado.session_id, estado)

    respuesta = await orquestador.procesar_turno(
        session_id=estado.session_id,
        texto_usuario=(
            "¿Qué datos del vehículo tenemos registrados? Voy a aflojar la cañería del inyector "
            "Common Rail con el motor encendido."
        ),
        gestor_diagnostico=object(),
    )

    assert respuesta["decision"] == "SEGURIDAD_CRITICA"
    assert "PROHIBICIÓN ESTRICTA" in respuesta["respuesta_texto"]
    assert "¿Qué datos" not in respuesta["respuesta_texto"]
    assert respuesta["case_id"] == "caso-activo"
    guardado = await repo.get_session(estado.session_id)
    assert guardado is not None
    assert any("Common Rail" in texto for texto in guardado.historial_mensajes_usuario)


@pytest.mark.parametrize(
    "mensaje",
    [
        "Cambié las pastillas de freno delanteras y el pedal se siente normal.",
        "¿Cómo se purga el filtro de combustible diésel con la perilla cebadora manual?",
        "El motor acelera con normalidad después del mantenimiento del turbo.",
        "Cambié la batería del vehículo con el motor apagado y según el procedimiento del fabricante.",
    ],
)
def test_consultas_inocuas_no_se_bloquean(mensaje):
    severidad, banner = PoliticaSeguridad.evaluar_severidad(mensaje)
    assert severidad == SeveridadSeguridad.NORMAL_DIAGNOSTIC
    assert banner is None


@pytest.mark.anyio
async def test_respuesta_ambigua_no_desactiva_alerta_de_frenos():
    orquestador = OrquestadorConversacion(repositorio=InMemoryConversationRepository())
    primer_turno = await orquestador.procesar_turno(
        session_id="frenos-sin-resolver",
        texto_usuario="Toyota Yaris 2018: el pedal de freno se va al fondo",
        gestor_diagnostico=GestorDiagnostico(),
    )
    segundo_turno = await orquestador.procesar_turno(
        session_id="frenos-sin-resolver",
        texto_usuario="puede ser",
        gestor_diagnostico=GestorDiagnostico(),
    )

    assert primer_turno["decision"] == "SEGURIDAD_CRITICA"
    assert segundo_turno["decision"] == "SEGURIDAD_CRITICA"
    assert "NO CONDUCIR" in segundo_turno["respuesta_texto"].upper()
    assert segundo_turno["case_id"] == primer_turno["case_id"]
