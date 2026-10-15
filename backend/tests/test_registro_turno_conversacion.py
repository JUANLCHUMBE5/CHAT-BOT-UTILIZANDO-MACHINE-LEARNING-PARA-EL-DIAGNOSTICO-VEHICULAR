from src.application.services.registro_turno_conversacion import registrar_turno_en_contexto


def test_registra_turno_consumido_por_retorno_anticipado_una_sola_vez():
    contexto, registrado = registrar_turno_en_contexto(
        {},
        message_id="m-ventilador",
        texto="El ventilador de alta sí funciona al activar el aire acondicionado.",
        session_id="s-1",
    )
    assert registrado
    assert contexto["conversation_state"]["turno_actual"] == 1
    assert contexto["conversation_state"]["historial_mensajes_usuario"] == [
        "El ventilador de alta sí funciona al activar el aire acondicionado."
    ]

    repetido, registrado_de_nuevo = registrar_turno_en_contexto(
        contexto,
        message_id="m-ventilador",
        texto="El ventilador de alta sí funciona al activar el aire acondicionado.",
        session_id="s-1",
    )
    assert not registrado_de_nuevo
    assert repetido["conversation_state"]["turno_actual"] == 1


def test_reconcilia_turno_guardado_por_ruta_terminal_sin_duplicar_el_texto():
    contexto, registrado = registrar_turno_en_contexto(
        {
            "conversation_state": {
                "session_id": "s-1",
                "turno_actual": 0,
                "historial_mensajes_usuario": ["El ventilador no activa la baja."],
            }
        },
        message_id="m-seguridad",
        texto="El ventilador no activa la baja.",
        session_id="s-1",
    )

    assert registrado
    assert contexto["conversation_state"]["historial_mensajes_usuario"] == [
        "El ventilador no activa la baja."
    ]
    assert contexto["conversation_state"]["turno_actual"] == 1
