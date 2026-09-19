"""Regresiones Fase 11.4 para flujo real mecanico -> CarBot."""

from __future__ import annotations

import pytest

from src.application.services import GestorDiagnostico
from src.core.conversacion.models import EstadoOperativo, FactState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository


@pytest.fixture
def gestor_real() -> GestorDiagnostico:
    return GestorDiagnostico()


@pytest.fixture
def orquestador() -> OrquestadorConversacion:
    return OrquestadorConversacion(repositorio=InMemoryConversationRepository())


@pytest.mark.anyio
async def test_arranque_frio_no_inventa_frenos_ni_vibracion(
    orquestador: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    msg = (
        "Hola, tengo un vehiculo en el taller. El cliente comenta que demora bastante "
        "en encender por las mananas. Una vez que logra encender, el motor funciona "
        "normal y no se prende ninguna luz de advertencia. Todavia no he revisado "
        "bateria, arranque ni sistema de combustible. Que deberia revisar primero?"
    )

    respuesta = await orquestador.procesar_mensaje(
        session_id="fase11_4_arranque_real",
        texto_usuario=msg,
        gestor_diagnostico=gestor_real,
    )

    estado = respuesta["estado"]
    texto = respuesta["respuesta_texto"].lower()

    assert estado.estado_operativo == EstadoOperativo.ARRANQUE
    assert estado.obtener_hecho("sintoma_demora_arranque") is not None
    testigo = estado.obtener_hecho("sintoma_testigo_check_engine")
    assert testigo is not None
    assert testigo.estado == FactState.AUSENTE_NEGADO
    assert "al acelerar con fuerza en carretera" not in texto
    assert "pedal de freno" not in texto
    assert "vibracion al frenar" not in texto


@pytest.mark.anyio
async def test_nuevo_vehiculo_con_sintomas_mismo_mensaje_no_hace_loop(
    orquestador: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    await orquestador.procesar_mensaje(
        session_id="fase11_4_nuevo_vehiculo",
        texto_usuario="El aire acondicionado no enfria, sopla aire tibio.",
        gestor_diagnostico=gestor_real,
    )

    msg = (
        "Hola, tengo otro vehiculo en el taller. El cliente indica que la temperatura "
        "del motor empieza a subir despues de unos minutos manejando. Tambien noto "
        "que esta perdiendo liquido refrigerante por la parte delantera. Todavia no "
        "he revisado el vehiculo ni se exactamente de donde viene la fuga. Que deberia revisar primero?"
    )

    respuesta = await orquestador.procesar_mensaje(
        session_id="fase11_4_nuevo_vehiculo",
        texto_usuario=msg,
        gestor_diagnostico=gestor_real,
    )

    estado = respuesta["estado"]
    texto = respuesta["respuesta_texto"].lower()
    consulta = respuesta.get("consulta_consolidada", "").lower()

    assert respuesta["decision"] == "DIAGNOSTICAR"
    assert respuesta.get("decision_transicion") == "CAMBIO_DE_CASO"
    assert estado.obtener_hecho("sintoma_sobrecalentamiento") is not None
    assert estado.obtener_hecho("sintoma_fuga_de_refrigerante") is not None
    assert "caso finalizado" not in texto
    assert "mismo vehiculo/caso" not in texto
    assert "compresor" not in consulta
    assert "aire acondicionado" not in consulta


@pytest.mark.anyio
async def test_reset_puro_sigue_siendo_transicion_controlada(
    orquestador: OrquestadorConversacion,
    gestor_real: GestorDiagnostico,
) -> None:
    await orquestador.procesar_mensaje(
        session_id="fase11_4_reset_puro",
        texto_usuario="El motor tironea al acelerar en subida.",
        gestor_diagnostico=gestor_real,
    )

    respuesta = await orquestador.procesar_mensaje(
        session_id="fase11_4_reset_puro",
        texto_usuario="tengo otro carro",
        gestor_diagnostico=gestor_real,
    )

    assert respuesta["decision"] == "REINICIO"
    assert "caso finalizado" in respuesta["respuesta_texto"].lower()

