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
    assert "caso anterior cerrado" in respuesta["respuesta_texto"].lower()


@pytest.mark.anyio
async def test_cancelar_y_nuevo_caso_no_hereda_sistema_activo_main(monkeypatch) -> None:
    """El reinicio explícito debe limpiar el ruteo del caso anterior."""
    from src.config import settings
    from src.core.conversacion.models import ConversationState

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "groq_chat_enabled", False)

    repositorio = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repositorio)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None

    estado = ConversationState(session_id="local_cancelar_nuevo_caso")
    estado.case_id = "case-anterior"
    estado.active_system = "refrigeracion"
    estado.active_symptoms = ["recalentamiento"]
    estado.historial_mensajes_usuario = ["Mazda: se recalienta en carretera"]
    await repositorio.save_session(estado.session_id, estado)
    case_anterior = estado.case_id

    cancelacion = await orquestador.procesar_mensaje(
        session_id=estado.session_id,
        texto_usuario="Cancelar",
        gestor_diagnostico=gestor,
        proveedor="web",
    )
    assert cancelacion["decision"] == "REINICIO"
    estado_tras_cancelar = await repositorio.get_session(estado.session_id)
    assert estado_tras_cancelar is not None
    assert estado_tras_cancelar.active_system is None

    respuesta = await orquestador.procesar_mensaje(
        session_id=estado.session_id,
        texto_usuario="Nuevo caso",
        gestor_diagnostico=gestor,
        proveedor="web",
    )

    estado_nuevo = await repositorio.get_session(estado.session_id)
    assert respuesta["decision"] == "REINICIO"
    assert estado_nuevo is not None
    assert estado_nuevo.case_id != case_anterior
    assert estado_nuevo.active_system is None
    assert estado_nuevo.active_symptoms == []
    assert estado_nuevo.historial_mensajes_usuario == []

    caso_b = await orquestador.procesar_mensaje(
        session_id=estado.session_id,
        texto_usuario="Nissan Versa: mezcla pobre en el escáner",
        gestor_diagnostico=gestor,
        proveedor="web",
    )
    assert caso_b["estado"].active_system == "combustible_admision"
    assert all("recalentamiento" not in sintoma.lower() for sintoma in caso_b["estado"].active_symptoms)


@pytest.mark.anyio
@pytest.mark.parametrize("comando", ["Cancelar", "Nuevo", "Nuevo caso"])
async def test_comando_nuevo_sin_caso_abierto_es_idempotente_main(comando: str) -> None:
    """Los dos alias de nuevo reinician sin clasificar el comando como síntoma."""
    repositorio = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repositorio)
    gestor = GestorDiagnostico(gemini_api_key="")

    primera = await orquestador.procesar_mensaje(
        session_id=f"local_{comando.replace(' ', '_')}",
        texto_usuario=comando,
        gestor_diagnostico=gestor,
        proveedor="web",
    )
    segunda = await orquestador.procesar_mensaje(
        session_id=f"local_{comando.replace(' ', '_')}",
        texto_usuario=comando,
        gestor_diagnostico=gestor,
        proveedor="web",
    )

    assert primera["decision"] == "REINICIO"
    assert segunda["decision"] == "REINICIO"
    texto_respuesta = segunda["respuesta_texto"].lower()
    if comando == "Cancelar":
        assert "caso cancelado" in texto_respuesta
    else:
        assert "caso anterior cerrado" in texto_respuesta
    estado = await repositorio.get_session(f"local_{comando.replace(' ', '_')}")
    assert estado is not None
    assert estado.active_system is None
    assert estado.active_symptoms == []
    assert estado.historial_mensajes_usuario == []


@pytest.mark.anyio
@pytest.mark.parametrize("comando", ["Cancelar", "Nuevo"])
async def test_reinicio_deja_gate_listo_para_placa_del_siguiente_auto_main(comando: str) -> None:
    from types import SimpleNamespace

    from src.core.conversacion.models import ConversationState
    from src.core.services.webhook.diagnostic_workflow import TechnicalDiagnosticWorkflow
    from src.core.session_manager import SessionManager

    estado = ConversationState(session_id="local_gate_placa_cancelar")
    estado.case_id = "case-mazda-anterior"
    estado.placa = "OLD123"
    estado.active_system = "refrigeracion"
    estado.active_symptoms = ["recalentamiento"]
    estado.historial_mensajes_usuario = ["Mazda: se recalienta en carretera"]

    conversacion = SimpleNamespace(
        id="local_gate_placa_cancelar",
        contexto={
            "placa": "OLD123",
            "placa_posttest": "OLD123",
            "posttest_placa_pendiente": False,
            "preplate_pending_input": "síntoma viejo",
            "validacion_diagnostico": {"etapa": "esperando_confirmacion"},
            "conversation_state": estado.exportar_dict(),
        },
    )
    gestor = SimpleNamespace(session_manager=SessionManager())

    resultado = await TechnicalDiagnosticWorkflow.preparar(
        gestor=gestor,
        conversacion=conversacion,
        usuario=None,
        remitente="local-only",
        proveedor="web",
        tipo_mensaje="text",
        texto_cliente=comando,
        audio_id="",
        placa="OLD123",
        marca_modelo="Mazda 3",
    )

    estado_limpio = conversacion.contexto["conversation_state"]
    assert resultado.dto.tipo_consulta == "reinicio"
    assert conversacion.contexto["posttest_placa_pendiente"] is True
    assert "placa" not in conversacion.contexto
    assert "placa_posttest" not in conversacion.contexto
    assert "preplate_pending_input" not in conversacion.contexto
    assert "validacion_diagnostico" not in conversacion.contexto
    assert estado_limpio["active_system"] is None
    assert estado_limpio["active_symptoms"] == []
    assert estado_limpio["historial_mensajes_usuario"] == []
    if comando == "Cancelar":
        assert "caso cancelado" in resultado.dto.respuesta_texto.lower()
    else:
        assert "caso anterior cerrado" in resultado.dto.respuesta_texto.lower()
    assert "envía" in resultado.dto.respuesta_texto.lower()
    assert "placa" in resultado.dto.respuesta_texto.lower()


@pytest.mark.anyio
@pytest.mark.parametrize("entrada", ["", "   ", "😀🙏", "4", "menu", "menú"])
async def test_entrada_vacia_emoji_o_menu_no_se_clasifica_como_falla_main(entrada: str) -> None:
    repositorio = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repositorio)

    respuesta = await orquestador.procesar_mensaje(
        session_id=f"local_entrada_no_diagnostica_{repr(entrada)}",
        texto_usuario=entrada,
        gestor_diagnostico=object(),
        proveedor="web",
    )

    assert respuesta["decision"] == "PEDIR_TEXTO"
    assert respuesta["diagnostico_ml"] == "Entrada insuficiente"
    assert respuesta["estado"].historial_mensajes_usuario == []


@pytest.mark.anyio
async def test_saludo_inicial_no_se_clasifica_como_falla_main() -> None:
    orquestador = OrquestadorConversacion(repositorio=InMemoryConversationRepository())

    respuesta = await orquestador.procesar_mensaje(
        session_id="local_saludo_sin_diagnostico",
        texto_usuario="Hola",
        gestor_diagnostico=object(),
        proveedor="web",
    )

    assert respuesta["decision"] == "SALUDO"
    assert respuesta["diagnostico_ml"] == "Saludo / Bienvenida"


@pytest.mark.anyio
async def test_replay_mazda_completo_conserva_refrigeracion_y_filtra_top3_fuera_de_tema_main(
    monkeypatch,
) -> None:
    from src.config import settings
    from src.core.diagnostico.enrutador_sistema import respuesta_menciona_causa_fuera_de_sistema

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None
    flujo = OrquestadorConversacion(repositorio=InMemoryConversationRepository())
    mensajes = [
        "El carro empezó a recalentar",
        "En todo momento cuando calienta",
        "Calienta",
        "Si en el escaner la temperatura llega a 80 c y ya empieza a calentar",
        "Es un problema de refrigeración no de mezcla",
    ]
    respuestas = []

    for mensaje in mensajes:
        salida = await flujo.procesar_mensaje(
            session_id="replay_mazda_ruteo_local",
            texto_usuario=mensaje,
            gestor_diagnostico=gestor,
            proveedor="web",
        )
        respuestas.append(salida["respuesta_texto"].lower())
        assert salida["estado"].active_system == "refrigeracion"
        assert not respuesta_menciona_causa_fuera_de_sistema(
            "refrigeracion", salida["respuesta_texto"]
        )

    assert "termostato" in respuestas[-1] or "refrigerante" in respuestas[-1]
    assert not any("sensor de ox" in texto or "llanta" in texto or "embrague" in texto for texto in respuestas)


@pytest.mark.anyio
async def test_replay_versa_no_repite_pregunta_ni_reintroduce_iac_tras_hallazgo_inyectores_main(
    monkeypatch,
) -> None:
    from src.config import settings

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None
    flujo = OrquestadorConversacion(repositorio=InMemoryConversationRepository())
    mensajes = [
        "Tengo mezcla pobre y el motor pierde fuerza",
        "El IAC ya lo revisé y está bien",
        "Encontré que los inyectores no inyectan lo suficiente",
        "Sí",
    ]
    salidas = []

    for mensaje in mensajes:
        salida = await flujo.procesar_mensaje(
            session_id="replay_versa_ruteo_local",
            texto_usuario=mensaje,
            gestor_diagnostico=gestor,
            proveedor="web",
        )
        salidas.append(salida)
        assert salida["estado"].active_system == "combustible_admision"

    preguntas_dtc = [
        pregunta
        for pregunta in salidas[-1]["estado"].preguntas_realizadas
        if "stft/ltft" in pregunta.get("texto", "").lower()
    ]
    respuesta_final = salidas[-1]["respuesta_texto"].lower()
    assert len(preguntas_dtc) == 1
    respuesta_hallazgo = salidas[-2]["respuesta_texto"].lower()
    assert "inyector" in respuesta_hallazgo
    assert "iac" not in respuesta_hallazgo and "cuerpo de aceleración" not in respuesta_hallazgo
    assert "qué componente o prueba revisaste" not in respuesta_final
    assert "manómetro" in respuesta_final


@pytest.mark.anyio
async def test_replay_versa_del_zip_prioriza_hallazgo_inyectores_ante_medicion_pendiente_main(monkeypatch) -> None:
    """Reproduce el tramo crítico redactado de Alex: mezcla -> hallazgo -> No."""
    from src.config import settings

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None
    flujo = OrquestadorConversacion(repositorio=InMemoryConversationRepository())
    session_id = "alex_zip_versa_hallazgo_inyectores"
    turnos_iniciales = [
        "Se me prende el check del motor y arroja mezcla pobre",
        "En ralenti",
        "Por ejemplo ahora que esta caliente sigue con el dtc presente",
        "Si se conecto el scaner y arroja mezcla pobre en el sistema",
        "Ya lo revise y eso esta bien",
        "Encontré que los injectores no inyectan lo suficiente",
    ]

    for turno in turnos_iniciales:
        resultado = await flujo.procesar_mensaje(
            session_id=session_id,
            texto_usuario=turno,
            marca_modelo="Nissan Versa",
            gestor_diagnostico=gestor,
            proveedor="web",
        )

    estado = resultado["estado"]
    respuesta = resultado["respuesta_texto"].lower()
    assert estado.active_system == "combustible_admision"
    assert estado.obtener_hecho("caudal_inyectores_reportado") is not None
    assert resultado["decision"] != "PENDIENTE_MEDICION"
    assert "pendiente de una medición objetiva" not in respuesta
    assert "envía el dtc exacto" not in respuesta
    assert "inyector" in respuesta

    resultado_no = await flujo.procesar_mensaje(
        session_id=session_id,
        texto_usuario="No",
        marca_modelo="Nissan Versa",
        gestor_diagnostico=gestor,
        proveedor="web",
    )
    texto_no = resultado_no["respuesta_texto"].lower()
    assert resultado_no["decision"] == "PREGUNTAR"
    assert resultado_no["estado"].active_system == "combustible_admision"
    assert "inyector" in texto_no
    assert "caudal" in texto_no or "pulverización" in texto_no
    assert "stft/ltft" not in texto_no
    assert "cascabeleo" not in texto_no and "humo" not in texto_no
    assert "iac" not in texto_no and "cuerpo de aceleración" not in texto_no


@pytest.mark.anyio
async def test_revision_generica_descarta_hipotesis_activa_sin_repetirla_main() -> None:
    from src.core.conversacion.models import ConversationState, QuestionIntent

    repositorio = InMemoryConversationRepository()
    flujo = OrquestadorConversacion(repositorio=repositorio)
    estado = ConversationState(session_id="alex_revision_iac_activa")
    estado.active_system = "combustible_admision"
    estado.falla_principal = "Cuerpo de aceleración o válvula IAC sucia"
    estado.top3_actual = [
        {"falla": estado.falla_principal, "probabilidad": 0.83},
        {"falla": "Inyectores obstruidos", "probabilidad": 0.12},
    ]
    estado.historial_mensajes_usuario = ["Nissan Versa: mezcla pobre en el escáner"]
    estado.registrar_pregunta(
        QuestionIntent.CONFIRMACION_ALTERNATIVA,
        "¿Has podido verificar este punto? ¿Fue correcta la hipótesis principal? Sí / No",
        hipotesis=[estado.falla_principal],
    )
    await repositorio.save_session(estado.session_id, estado)

    respuesta = await flujo.procesar_turno(
        estado.session_id,
        "Ya lo revisé y eso está bien",
        object(),
        proveedor="web",
    )

    assert respuesta["decision"] == "PREGUNTAR"
    assert estado.falla_principal in estado.hipotesis_descartadas
    assert "cuerpo de aceleración" not in respuesta["respuesta_texto"].lower()
    assert "iac" not in respuesta["respuesta_texto"].lower()


@pytest.mark.anyio
async def test_replay_yaris_tiembla_minimo_500_rpm_permanece_en_encendido_main(monkeypatch) -> None:
    from src.config import settings

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None
    flujo = OrquestadorConversacion(repositorio=InMemoryConversationRepository())
    turnos = [
        "El vehículo tiembla en todo momento y el mínimo está en 500 rpm",
        "Detenido en ralentí",
        "Sí",
    ]
    salidas = []

    for turno in turnos:
        salida = await flujo.procesar_mensaje(
            session_id="replay_yaris_500rpm_local",
            texto_usuario=turno,
            marca_modelo="Toyota Yaris 2023",
            gestor_diagnostico=gestor,
            proveedor="web",
        )
        salidas.append(salida)
        assert salida["estado"].active_system == "encendido"

    texto = " ".join(s["respuesta_texto"].lower() for s in salidas)
    assert "sin hipótesis ml" not in texto
    assert "bujía" in texto or "bujia" in texto or "bobina" in texto


@pytest.mark.anyio
async def test_replay_chevrolet_map_sin_lectura_deja_medicion_pendiente_main(monkeypatch) -> None:
    from src.config import settings

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None
    flujo = OrquestadorConversacion(repositorio=InMemoryConversationRepository())
    turnos = [
        "Tengo problemas con la carga absoluta, está fuera de rango",
        "Detenido en ralentí y andando también se siente una pérdida de potencia",
        "No",
    ]
    salidas = []

    for turno in turnos:
        salida = await flujo.procesar_mensaje(
            session_id="replay_chevrolet_map_local",
            texto_usuario=turno,
            marca_modelo="Chevrolet Joy 2020",
            gestor_diagnostico=gestor,
            proveedor="web",
        )
        salidas.append(salida)

    final = salidas[-1]["respuesta_texto"].lower()
    assert "pendiente la medición del map" in final
    assert "no confirmaré una causa" in final
    assert "confirma" not in salidas[-1]["decision"].lower()


@pytest.mark.anyio
async def test_no_descarta_hipotesis_y_solicita_discriminante_de_inyectores_main(monkeypatch) -> None:
    from src.config import settings
    from src.core.conversacion.models import ConversationState, QuestionIntent

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None
    repositorio = InMemoryConversationRepository()
    flujo = OrquestadorConversacion(repositorio=repositorio)
    estado = ConversationState(session_id="replay_versa_no_inyectores_local")
    estado.active_system = "combustible_admision"
    estado.falla_principal = "Inyectores con caudal insuficiente"
    estado.top3_actual = [{"falla": estado.falla_principal, "probabilidad": 0.6}]
    estado.historial_mensajes_usuario = [
        "Nissan Versa: el escáner muestra mezcla pobre",
        "Encontré que los inyectores no inyectan lo suficiente",
    ]
    estado.registrar_pregunta(
        intent=QuestionIntent.CONFIRMACION_ALTERNATIVA,
        texto="¿Fue correcta la hipótesis? Sí/No",
        hipotesis=[estado.falla_principal],
        incrementar_repregunta=False,
    )
    await repositorio.save_session(estado.session_id, estado)

    salida = await flujo.procesar_mensaje(
        session_id=estado.session_id,
        texto_usuario="No",
        gestor_diagnostico=gestor,
        proveedor="web",
    )

    texto = salida["respuesta_texto"].lower()
    assert salida["estado"].hipotesis_descartadas == [estado.falla_principal]
    assert "descarto esa hipótesis" in texto
    assert "caudal/patrón de pulverización" in texto
    assert "qué componente o prueba revisaste" not in texto
    assert salida["estado"].ultima_pregunta()["intent"] == QuestionIntent.COMPONENTE_REVISADO.value


@pytest.mark.anyio
async def test_cancelar_y_nuevo_caso_no_hereda_sistema_activo_t08(monkeypatch) -> None:
    """El reinicio explícito debe limpiar el ruteo del caso anterior."""
    from src.config import settings
    from src.core.conversacion.models import ConversationState

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "groq_chat_enabled", False)

    repositorio = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repositorio)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None

    estado = ConversationState(session_id="local_cancelar_nuevo_caso")
    estado.case_id = "case-anterior"
    estado.active_system = "refrigeracion"
    estado.active_symptoms = ["recalentamiento"]
    estado.historial_mensajes_usuario = ["Mazda: se recalienta en carretera"]
    await repositorio.save_session(estado.session_id, estado)
    case_anterior = estado.case_id

    cancelacion = await orquestador.procesar_mensaje(
        session_id=estado.session_id,
        texto_usuario="Cancelar",
        gestor_diagnostico=gestor,
        proveedor="web",
    )
    assert cancelacion["decision"] == "REINICIO"
    estado_tras_cancelar = await repositorio.get_session(estado.session_id)
    assert estado_tras_cancelar is not None
    assert estado_tras_cancelar.active_system is None

    respuesta = await orquestador.procesar_mensaje(
        session_id=estado.session_id,
        texto_usuario="Nuevo caso",
        gestor_diagnostico=gestor,
        proveedor="web",
    )

    estado_nuevo = await repositorio.get_session(estado.session_id)
    assert respuesta["decision"] == "REINICIO"
    assert estado_nuevo is not None
    assert estado_nuevo.case_id != case_anterior
    assert estado_nuevo.active_system is None
    assert estado_nuevo.active_symptoms == []
    assert estado_nuevo.historial_mensajes_usuario == []

    caso_b = await orquestador.procesar_mensaje(
        session_id=estado.session_id,
        texto_usuario="Nissan Versa: mezcla pobre en el escáner",
        gestor_diagnostico=gestor,
        proveedor="web",
    )
    assert caso_b["estado"].active_system == "combustible_admision"
    assert all("recalentamiento" not in sintoma.lower() for sintoma in caso_b["estado"].active_symptoms)


@pytest.mark.anyio
@pytest.mark.parametrize("comando", ["Cancelar", "Nuevo", "Nuevo caso"])
async def test_comando_nuevo_sin_caso_abierto_es_idempotente_t08(comando: str) -> None:
    """Los dos alias de nuevo reinician sin clasificar el comando como síntoma."""
    repositorio = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repositorio)
    gestor = GestorDiagnostico(gemini_api_key="")

    primera = await orquestador.procesar_mensaje(
        session_id=f"local_{comando.replace(' ', '_')}",
        texto_usuario=comando,
        gestor_diagnostico=gestor,
        proveedor="web",
    )
    segunda = await orquestador.procesar_mensaje(
        session_id=f"local_{comando.replace(' ', '_')}",
        texto_usuario=comando,
        gestor_diagnostico=gestor,
        proveedor="web",
    )

    assert primera["decision"] == "REINICIO"
    assert segunda["decision"] == "REINICIO"
    texto_respuesta = segunda["respuesta_texto"].lower()
    if comando == "Cancelar":
        assert "caso cancelado" in texto_respuesta
    else:
        assert "caso anterior cerrado" in texto_respuesta
    estado = await repositorio.get_session(f"local_{comando.replace(' ', '_')}")
    assert estado is not None
    assert estado.active_system is None
    assert estado.active_symptoms == []
    assert estado.historial_mensajes_usuario == []


@pytest.mark.anyio
@pytest.mark.parametrize("comando", ["Cancelar", "Nuevo"])
async def test_reinicio_deja_gate_listo_para_placa_del_siguiente_auto_t08(comando: str) -> None:
    from types import SimpleNamespace

    from src.core.conversacion.models import ConversationState
    from src.core.services.webhook.diagnostic_workflow import TechnicalDiagnosticWorkflow
    from src.core.session_manager import SessionManager

    estado = ConversationState(session_id="local_gate_placa_cancelar")
    estado.case_id = "case-mazda-anterior"
    estado.placa = "OLD123"
    estado.active_system = "refrigeracion"
    estado.active_symptoms = ["recalentamiento"]
    estado.historial_mensajes_usuario = ["Mazda: se recalienta en carretera"]

    conversacion = SimpleNamespace(
        id="local_gate_placa_cancelar",
        contexto={
            "placa": "OLD123",
            "placa_posttest": "OLD123",
            "posttest_placa_pendiente": False,
            "preplate_pending_input": "síntoma viejo",
            "validacion_diagnostico": {"etapa": "esperando_confirmacion"},
            "conversation_state": estado.exportar_dict(),
        },
    )
    gestor = SimpleNamespace(session_manager=SessionManager())

    resultado = await TechnicalDiagnosticWorkflow.preparar(
        gestor=gestor,
        conversacion=conversacion,
        usuario=SimpleNamespace(id="local-user", taller_id="local-taller"),
        remitente="local-only",
        proveedor="web",
        tipo_mensaje="text",
        texto_cliente=comando,
        audio_id="",
        placa="OLD123",
        marca_modelo="Mazda 3",
    )

    estado_limpio = conversacion.contexto["conversation_state"]
    assert resultado.dto.tipo_consulta == "reinicio"
    assert conversacion.contexto["posttest_placa_pendiente"] is True
    assert conversacion.contexto.get("placa") is None
    assert conversacion.contexto.get("placa_posttest") is None
    assert "preplate_pending_input" not in conversacion.contexto
    assert "validacion_diagnostico" not in conversacion.contexto
    assert estado_limpio["active_system"] is None
    assert estado_limpio["active_symptoms"] == []
    assert estado_limpio["historial_mensajes_usuario"] == []
    if comando == "Cancelar":
        assert "caso cancelado" in resultado.dto.respuesta_texto.lower()
    else:
        assert "caso anterior cerrado" in resultado.dto.respuesta_texto.lower()
    assert "envía" in resultado.dto.respuesta_texto.lower()
    assert "placa" in resultado.dto.respuesta_texto.lower()


@pytest.mark.anyio
@pytest.mark.parametrize("entrada", ["", "   ", "😀🙏", "4", "menu", "menú"])
async def test_entrada_vacia_emoji_o_menu_no_se_clasifica_como_falla_t08(entrada: str) -> None:
    repositorio = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repositorio)

    respuesta = await orquestador.procesar_mensaje(
        session_id=f"local_entrada_no_diagnostica_{repr(entrada)}",
        texto_usuario=entrada,
        gestor_diagnostico=object(),
        proveedor="web",
    )

    assert respuesta["decision"] == "PEDIR_TEXTO"
    assert respuesta["diagnostico_ml"] == "Entrada insuficiente"
    assert respuesta["estado"].historial_mensajes_usuario == []


@pytest.mark.anyio
async def test_saludo_inicial_no_se_clasifica_como_falla_t08() -> None:
    orquestador = OrquestadorConversacion(repositorio=InMemoryConversationRepository())

    respuesta = await orquestador.procesar_mensaje(
        session_id="local_saludo_sin_diagnostico",
        texto_usuario="Hola",
        gestor_diagnostico=object(),
        proveedor="web",
    )

    assert respuesta["decision"] == "SALUDO"
    assert respuesta["diagnostico_ml"] == "Saludo / Bienvenida"


@pytest.mark.anyio
async def test_replay_mazda_completo_conserva_refrigeracion_y_filtra_top3_fuera_de_tema_t08(
    monkeypatch,
) -> None:
    from src.config import settings
    from src.core.diagnostico.enrutador_sistema import respuesta_menciona_causa_fuera_de_sistema

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None
    flujo = OrquestadorConversacion(repositorio=InMemoryConversationRepository())
    mensajes = [
        "El carro empezó a recalentar",
        "En todo momento cuando calienta",
        "Calienta",
        "Si en el escaner la temperatura llega a 80 c y ya empieza a calentar",
        "Es un problema de refrigeración no de mezcla",
    ]
    respuestas = []

    for mensaje in mensajes:
        salida = await flujo.procesar_mensaje(
            session_id="replay_mazda_ruteo_local",
            texto_usuario=mensaje,
            gestor_diagnostico=gestor,
            proveedor="web",
        )
        respuestas.append(salida["respuesta_texto"].lower())
        assert salida["estado"].active_system == "refrigeracion"
        assert not respuesta_menciona_causa_fuera_de_sistema(
            "refrigeracion", salida["respuesta_texto"]
        )

    assert "termostato" in respuestas[-1] or "refrigerante" in respuestas[-1]
    assert not any("sensor de ox" in texto or "llanta" in texto or "embrague" in texto for texto in respuestas)


@pytest.mark.anyio
async def test_replay_versa_no_repite_pregunta_ni_reintroduce_iac_tras_hallazgo_inyectores_t08(
    monkeypatch,
) -> None:
    from src.config import settings

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None
    flujo = OrquestadorConversacion(repositorio=InMemoryConversationRepository())
    mensajes = [
        "Tengo mezcla pobre y el motor pierde fuerza",
        "El IAC ya lo revisé y está bien",
        "Encontré que los inyectores no inyectan lo suficiente",
        "Sí",
    ]
    salidas = []

    for mensaje in mensajes:
        salida = await flujo.procesar_mensaje(
            session_id="replay_versa_ruteo_local",
            texto_usuario=mensaje,
            gestor_diagnostico=gestor,
            proveedor="web",
        )
        salidas.append(salida)
        assert salida["estado"].active_system == "combustible_admision"

    preguntas_dtc = [
        pregunta
        for pregunta in salidas[-1]["estado"].preguntas_realizadas
        if "stft/ltft" in pregunta.get("texto", "").lower()
    ]
    respuesta_final = salidas[-1]["respuesta_texto"].lower()
    assert len(preguntas_dtc) == 1
    respuesta_hallazgo = salidas[-2]["respuesta_texto"].lower()
    assert "inyector" in respuesta_hallazgo
    assert "iac" not in respuesta_hallazgo and "cuerpo de aceleración" not in respuesta_hallazgo
    assert "qué componente o prueba revisaste" not in respuesta_final
    assert "manómetro" in respuesta_final


@pytest.mark.anyio
async def test_replay_versa_del_zip_prioriza_hallazgo_inyectores_ante_medicion_pendiente_t08(monkeypatch) -> None:
    """Reproduce el tramo crítico redactado de Alex: mezcla -> hallazgo -> No."""
    from src.config import settings

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None
    flujo = OrquestadorConversacion(repositorio=InMemoryConversationRepository())
    session_id = "alex_zip_versa_hallazgo_inyectores"
    turnos_iniciales = [
        "Se me prende el check del motor y arroja mezcla pobre",
        "En ralenti",
        "Por ejemplo ahora que esta caliente sigue con el dtc presente",
        "Si se conecto el scaner y arroja mezcla pobre en el sistema",
        "Ya lo revise y eso esta bien",
        "Encontré que los injectores no inyectan lo suficiente",
    ]

    for turno in turnos_iniciales:
        resultado = await flujo.procesar_mensaje(
            session_id=session_id,
            texto_usuario=turno,
            marca_modelo="Nissan Versa",
            gestor_diagnostico=gestor,
            proveedor="web",
        )

    estado = resultado["estado"]
    respuesta = resultado["respuesta_texto"].lower()
    assert estado.active_system == "combustible_admision"
    assert estado.obtener_hecho("caudal_inyectores_reportado") is not None
    assert resultado["decision"] != "PENDIENTE_MEDICION"
    assert "pendiente de una medición objetiva" not in respuesta
    assert "envía el dtc exacto" not in respuesta
    assert "inyector" in respuesta

    resultado_no = await flujo.procesar_mensaje(
        session_id=session_id,
        texto_usuario="No",
        marca_modelo="Nissan Versa",
        gestor_diagnostico=gestor,
        proveedor="web",
    )
    texto_no = resultado_no["respuesta_texto"].lower()
    assert resultado_no["decision"] == "PREGUNTAR"
    assert resultado_no["estado"].active_system == "combustible_admision"
    assert "inyector" in texto_no
    assert "caudal" in texto_no or "pulverización" in texto_no
    assert "stft/ltft" not in texto_no
    assert "cascabeleo" not in texto_no and "humo" not in texto_no
    assert "iac" not in texto_no and "cuerpo de aceleración" not in texto_no


@pytest.mark.anyio
async def test_revision_generica_descarta_hipotesis_activa_sin_repetirla_t08() -> None:
    from src.core.conversacion.models import ConversationState, QuestionIntent

    repositorio = InMemoryConversationRepository()
    flujo = OrquestadorConversacion(repositorio=repositorio)
    estado = ConversationState(session_id="alex_revision_iac_activa")
    estado.active_system = "combustible_admision"
    estado.falla_principal = "Cuerpo de aceleración o válvula IAC sucia"
    estado.top3_actual = [
        {"falla": estado.falla_principal, "probabilidad": 0.83},
        {"falla": "Inyectores obstruidos", "probabilidad": 0.12},
    ]
    estado.historial_mensajes_usuario = ["Nissan Versa: mezcla pobre en el escáner"]
    estado.registrar_pregunta(
        QuestionIntent.CONFIRMACION_ALTERNATIVA,
        "¿Has podido verificar este punto? ¿Fue correcta la hipótesis principal? Sí / No",
        hipotesis=[estado.falla_principal],
    )
    await repositorio.save_session(estado.session_id, estado)

    respuesta = await flujo.procesar_turno(
        estado.session_id,
        "Ya lo revisé y eso está bien",
        object(),
        proveedor="web",
    )

    assert respuesta["decision"] == "PREGUNTAR"
    assert estado.falla_principal in estado.hipotesis_descartadas
    assert "cuerpo de aceleración" not in respuesta["respuesta_texto"].lower()
    assert "iac" not in respuesta["respuesta_texto"].lower()


@pytest.mark.anyio
async def test_replay_yaris_tiembla_minimo_500_rpm_permanece_en_encendido_t08(monkeypatch) -> None:
    from src.config import settings

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None
    flujo = OrquestadorConversacion(repositorio=InMemoryConversationRepository())
    turnos = [
        "El vehículo tiembla en todo momento y el mínimo está en 500 rpm",
        "Detenido en ralentí",
        "Sí",
    ]
    salidas = []

    for turno in turnos:
        salida = await flujo.procesar_mensaje(
            session_id="replay_yaris_500rpm_local",
            texto_usuario=turno,
            marca_modelo="Toyota Yaris 2023",
            gestor_diagnostico=gestor,
            proveedor="web",
        )
        salidas.append(salida)
        assert salida["estado"].active_system == "encendido"

    texto = " ".join(s["respuesta_texto"].lower() for s in salidas)
    assert "sin hipótesis ml" not in texto
    assert "bujía" in texto or "bujia" in texto or "bobina" in texto


@pytest.mark.anyio
async def test_replay_chevrolet_map_sin_lectura_deja_medicion_pendiente_t08(monkeypatch) -> None:
    from src.config import settings

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None
    flujo = OrquestadorConversacion(repositorio=InMemoryConversationRepository())
    turnos = [
        "Tengo problemas con la carga absoluta, está fuera de rango",
        "Detenido en ralentí y andando también se siente una pérdida de potencia",
        "No",
    ]
    salidas = []

    for turno in turnos:
        salida = await flujo.procesar_mensaje(
            session_id="replay_chevrolet_map_local",
            texto_usuario=turno,
            marca_modelo="Chevrolet Joy 2020",
            gestor_diagnostico=gestor,
            proveedor="web",
        )
        salidas.append(salida)

    final = salidas[-1]["respuesta_texto"].lower()
    assert "pendiente la medición del map" in final
    assert "no confirmaré una causa" in final
    assert "confirma" not in salidas[-1]["decision"].lower()


@pytest.mark.anyio
async def test_no_descarta_hipotesis_y_solicita_discriminante_de_inyectores_t08(monkeypatch) -> None:
    from src.config import settings
    from src.core.conversacion.models import ConversationState, QuestionIntent

    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None
    repositorio = InMemoryConversationRepository()
    flujo = OrquestadorConversacion(repositorio=repositorio)
    estado = ConversationState(session_id="replay_versa_no_inyectores_local")
    estado.active_system = "combustible_admision"
    estado.falla_principal = "Inyectores con caudal insuficiente"
    estado.top3_actual = [{"falla": estado.falla_principal, "probabilidad": 0.6}]
    estado.historial_mensajes_usuario = [
        "Nissan Versa: el escáner muestra mezcla pobre",
        "Encontré que los inyectores no inyectan lo suficiente",
    ]
    estado.registrar_pregunta(
        intent=QuestionIntent.CONFIRMACION_ALTERNATIVA,
        texto="¿Fue correcta la hipótesis? Sí/No",
        hipotesis=[estado.falla_principal],
        incrementar_repregunta=False,
    )
    await repositorio.save_session(estado.session_id, estado)

    salida = await flujo.procesar_mensaje(
        session_id=estado.session_id,
        texto_usuario="No",
        gestor_diagnostico=gestor,
        proveedor="web",
    )

    texto = salida["respuesta_texto"].lower()
    assert salida["estado"].hipotesis_descartadas == [estado.falla_principal]
    assert "descarto esa hipótesis" in texto
    assert "caudal/patrón de pulverización" in texto
    assert "qué componente o prueba revisaste" not in texto
    assert salida["estado"].ultima_pregunta()["intent"] == QuestionIntent.COMPONENTE_REVISADO.value
