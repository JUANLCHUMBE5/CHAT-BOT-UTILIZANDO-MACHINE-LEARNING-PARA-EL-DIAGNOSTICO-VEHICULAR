"""Prueba de integración conversacional realista: Caso Testigo Nissan Sentra 2018 (Fase 14.1)."""

import pytest

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.mark.anyio
async def test_conversacion_testigo_nissan_sentra_3_turnos(monkeypatch):
    """
    Verifica que el orquestador conversacional con comprensión semántica:
    1. Interprete 'NEUVO CASO' y capture 'Nissan Sentra 2018' sin bloquearse por placa.
    2. En el turno 2, entienda que 'No he comprobado' NO es descarte de la bomba, registre el tanque a medio nivel,
       reconozca la solicitud de causas alternativas y devuelva una orientación diferencial.
    3. En el turno 3, respete la intención de continuar el caso sin reiniciarlo ni pedir placa de nuevo.
    """
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    repo = InMemoryConversationRepository()
    gestor.conversation_repo = repo
    orquestador = OrquestadorConversacion(repositorio=repo)
    session_id = "test_nissan_sentra_fase14_1"

    # TURNO 1
    t1_msg = (
        "NEUVO CASO. Tengo un Nissan Sentra 2018 automático. Cuando acelero para subir una pendiente, "
        "el motor pierde fuerza y empieza a tironear. En terreno plano funciona mejor. "
        "No tengo ninguna luz de advertencia encendida en el tablero. ¿Qué podría estar pasando?"
    )
    r1 = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=t1_msg,
        gestor_diagnostico=gestor,
    )
    estado1 = r1["estado"]

    # Verificaciones Turno 1
    assert estado1.marca == "Nissan"
    assert estado1.modelo == "Sentra"
    assert str(estado1.anio) == "2018"
    assert len(estado1.active_symptoms) > 0 or estado1.active_system is not None
    assert r1.get("respuesta_texto") is not None
    assert len(r1.get("respuesta_texto")) > 20

    # TURNO 2
    t2_msg = (
        "No he comprobado la presión de la bomba de combustible. "
        "Lo que sí noté es que el tanque está a más de la mitad y en bajada o plano no falla tanto. "
        "¿Qué otras causas podrían ser y qué dato necesitas para diferenciarlas?"
    )
    r2 = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=t2_msg,
        gestor_diagnostico=gestor,
    )
    estado2 = r2["estado"]

    # Verificaciones Turno 2
    # La bomba de combustible NO debe haberse descartado (el mecánico dijo 'no he comprobado')
    assert "bomba_combustible" not in estado2.hipotesis_descartadas
    assert "presion_combustible" not in estado2.hipotesis_descartadas
    # Hecho registrado en el estado acumulativo
    assert len(estado2.hechos) >= 1 or len(estado2.hechos_historicos) >= 1

    # Respuesta atiende la duda de otras causas y no es un saludo inicial
    resp2 = r2.get("respuesta_texto", "")
    assert "hola" not in resp2.lower()[:30]
    assert len(resp2) > 40

    # TURNO 3
    t3_msg = (
        "Quiero continuar con este mismo caso, no reiniciar. "
        "Por favor indícame qué prueba rápida puedo hacer primero en el taller para no cambiar piezas a ciegas."
    )
    r3 = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=t3_msg,
        gestor_diagnostico=gestor,
    )
    estado3 = r3["estado"]

    # Verificaciones Turno 3
    assert estado3.case_id == estado1.case_id  # Mantiene el mismo caso
    assert estado3.marca == "Nissan"  # Preserva el vehículo
    assert estado3.modelo == "Sentra"
    resp3 = r3.get("respuesta_texto", "")
    assert "placa" not in resp3.lower()[:50]  # No pide placa ni vuelve a saludar
    assert "hola" not in resp3.lower()[:30]
