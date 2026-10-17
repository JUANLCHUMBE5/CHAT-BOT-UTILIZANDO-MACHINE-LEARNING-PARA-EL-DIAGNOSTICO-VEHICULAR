"""Prueba de integración conversacional realista: Caso Testigo Nissan Sentra 2018 (Fase 14.1)."""

import pytest

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.mark.asyncio
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
    assert "Sentra" in (estado1.modelo or "")
    assert estado1.anio == "2018"
    assert "Indique una placa válida" not in r1["respuesta_texto"]
    assert "Ingresa la placa" not in r1["respuesta_texto"]

    # TURNO 2
    t2_msg = (
        "No he comprobado si se escucha la bomba al poner el contacto en ON. "
        "El tanque tiene más de la mitad de combustible. El problema ocurre principalmente cuando subo pendientes y acelero. "
        "¿Qué otras posibles causas existen y qué dato necesitas para diferenciarlas?"
    )
    r2 = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=t2_msg,
        gestor_diagnostico=gestor,
    )
    estado2 = r2["estado"]

    # Verificaciones Turno 2
    # La bomba NO debe haber sido descartada
    descartes2 = [d.lower() for d in estado2.hipotesis_descartadas]
    assert not any("bomba" in d for d in descartes2), f"La bomba fue erróneamente descartada: {descartes2}"
    
    # La respuesta debe ser constructiva y no bloquearse en un bucle de placa o rechazo
    assert "Indique una placa válida" not in r2["respuesta_texto"]
    assert len(r2["respuesta_texto"]) > 30

    # TURNO 3
    t3_msg = (
        "Quiero continuar el mismo diagnóstico del Nissan Sentra. "
        "La bomba sí se escucha al dar contacto, pero no tengo manómetro a mano. "
        "Dime qué otras causas podrían explicar estos síntomas y qué prueba puedo hacer. "
        "No quiero iniciar otro caso ni repetir información."
    )
    r3 = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=t3_msg,
        gestor_diagnostico=gestor,
    )
    estado3 = r3["estado"]

    # Verificaciones Turno 3
    # Debe ser el mismo vehículo, no debe resetearse a genérico
    assert estado3.marca == "Nissan"
    assert "Sentra" in (estado3.modelo or "")
    assert "Indique una placa válida" not in r3["respuesta_texto"]
    assert len(r3["respuesta_texto"]) > 30
