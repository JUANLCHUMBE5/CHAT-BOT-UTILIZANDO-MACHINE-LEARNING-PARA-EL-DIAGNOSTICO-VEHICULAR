"""Regresiones del incidente frenos → suspensión, sin servicios ni mensajes reales."""

from types import SimpleNamespace

import pytest

from src.core.conversacion.aislamiento_subsistemas import separar_problema
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta
from src.core.diagnostico.models import ResultadoDiagnostico
from src.core.services.webhook.diagnostic_persister import DiagnosticPersister

FRENOS = "El pedal de freno se siente esponjoso y se hunde casi hasta el fondo."
SUSPENSION = (
    "Cuando paso por baches o rompemuelles escucho un golpe seco, como un clac clac, "
    "en la rueda delantera derecha y el carro rebota más de lo normal."
)


def estado_frenos():
    estado = ConversationState(session_id="aislamiento", case_id="frenos-anterior")
    estado.marca, estado.modelo, estado.anio = "Toyota", "Corolla", "2015"
    estado.placa = "TEST-01"
    estado.active_system = "frenos"
    estado.active_symptoms = [FRENOS]
    estado.falla_principal = "Fuga hidráulica o aire en frenos"
    estado.top3_actual = [{"falla": estado.falla_principal, "probabilidad": 0.59}]
    ExtractorHechos.extraer_y_actualizar(estado, FRENOS)
    return estado


@pytest.mark.parametrize("mensaje", [SUSPENSION, (
    "Estoy evaluando un Toyota Corolla 2015 con golpeteo seco en el tren delantero "
    "al circular sobre irregularidades de la vía y rompemuelles. "
    "Se percibe oscilación excesiva de la carrocería."
)])
def test_bifurcacion_limpia_preserva_vehiculo_y_archiva_evidencia(mensaje):
    estado = estado_frenos()
    assert separar_problema(estado, mensaje)
    assert estado.case_id != "frenos-anterior"
    assert (estado.marca, estado.modelo, estado.anio, estado.placa) == (
        "Toyota", "Corolla", "2015", "TEST-01",
    )
    assert not estado.top3_actual and not estado.measurements
    assert estado.hechos_historicos[-1]["historial_mensajes_usuario"] == [FRENOS]
    ExtractorHechos.extraer_y_actualizar(estado, mensaje)
    estado.historial_mensajes_usuario.append(mensaje)
    consulta = SintetizadorConsulta.sintetizar(estado).lower()
    assert "esponjoso" not in consulta and "fuga" not in consulta
    assert "golp" in consulta
    assert not separar_problema(estado, mensaje)


@pytest.mark.parametrize("mensaje", [
    "El pedal sigue esponjoso", "No puedo revisar las ruedas",
    "La rueda suena", "Tengo suspensión ruidosa y el pedal de freno se hunde",
])
def test_no_bifurca_continuaciones_ambiguas_o_mixtas(mensaje):
    estado = estado_frenos()
    assert not separar_problema(estado, mensaje)
    assert estado.case_id == "frenos-anterior"


def test_recupera_sesion_ya_contaminada_sin_perder_historial():
    estado = estado_frenos()
    estado.historial_mensajes_usuario.append(SUSPENSION)
    estado.active_symptoms.append(SUSPENSION)
    assert separar_problema(estado, SUSPENSION)
    assert estado.case_id != "frenos-anterior"
    assert not estado.hechos and not estado.top3_actual
    assert SUSPENSION in estado.hechos_historicos[-1]["historial_mensajes_usuario"]
    assert FRENOS in estado.hechos_historicos[-1]["historial_mensajes_usuario"]


@pytest.mark.anyio
@pytest.mark.parametrize("mensaje", [
    "¿Puedo circular así?", "Voy a salir a circular", "Quiero probar en pista",
])
async def test_intencion_vial_bloquea_sin_inventar_fuga(mensaje):
    repo = InMemoryConversationRepository()
    estado = estado_frenos()
    await repo.save_session(estado.session_id, estado)
    resultado = await OrquestadorConversacion(repo).procesar_turno(
        estado.session_id, mensaje, SimpleNamespace(session_manager=None, motor_rag=None),
    )
    assert resultado["decision"] == "SEGURIDAD_CRITICA"
    assert resultado["status"] == "completado"
    texto = resultado["respuesta_texto"].lower()
    assert "no circule" in texto or "no circules" in texto
    assert "fuga de líquido por la rueda" not in texto
    assert resultado["confianza_ml"] == 0


@pytest.mark.anyio
async def test_orquestador_suspension_no_cortocircuita_y_preserva_aviso(monkeypatch):
    repo = InMemoryConversationRepository()
    estado = estado_frenos()
    await repo.save_session(estado.session_id, estado)
    async def capturar(self, session_id, texto_usuario, gestor_diagnostico, *args, **kwargs):
        actual = await self.repositorio.get_session(session_id)
        ExtractorHechos.extraer_y_actualizar(actual, texto_usuario)
        return {
            "respuesta_texto": "Suspensión pendiente de inspección física segura.",
            "decision": "DIAGNOSTICAR", "estado": actual, "confianza_ml": 0.0,
            "consulta_consolidada": SintetizadorConsulta.sintetizar(actual),
        }

    from src.core.conversacion.proteccion_turnos import proteger_turno
    monkeypatch.setattr(OrquestadorConversacion, "procesar_turno", proteger_turno(capturar))
    resultado = await OrquestadorConversacion(repo).procesar_turno(
        estado.session_id, SUSPENSION + " Al circular sobre irregularidades.",
        SimpleNamespace(session_manager=None, motor_rag=None),
    )
    assert "esponjoso" not in resultado["consulta_consolidada"]
    assert resultado["decision"] != "SEGURIDAD_CRITICA"
    assert resultado["decision_transicion"] == "CAMBIO_DE_CASO"
    assert "Advertencia pendiente" in resultado["respuesta_texto"]
    assert "Suspensión pendiente" in resultado["respuesta_texto"]
    restaurado = ConversationState.from_dict(resultado["estado"].exportar_dict())
    assert restaurado.hechos_historicos[-1]["case_id"] == "frenos-anterior"


@pytest.mark.parametrize("tipo,modo,texto", [
    ("seguridad_critica", "completo", "Detén la maniobra."),
    ("diagnostico", "seguridad_critica", "Solicita asistencia."),
    ("diagnostico", "completo", "PROHIBIDO CIRCULAR: pendiente de inspección."),
    ("diagnostico", "completo", "No circules hasta verificar el frenado."),
])
def test_seguridad_no_solicita_confirmacion(tipo, modo, texto):
    dto = ResultadoDiagnostico(
        respuesta_texto=texto, diagnostico_ml="Advertencia", confianza_ml=0,
        contexto_manual="", titulo_manual="", tipo_consulta=tipo, modo_diagnostico=modo,
    )
    assert not DiagnosticPersister.debe_solicitar_feedback(dto)


@pytest.mark.anyio
async def test_pipeline_real_no_arrastra_top_frenos():
    from src.core.gestor_diagnostico import GestorDiagnostico

    repo = InMemoryConversationRepository()
    estado = estado_frenos()
    await repo.save_session(estado.session_id, estado)
    gestor = GestorDiagnostico()
    resultado = await OrquestadorConversacion(repo).procesar_turno(
        estado.session_id, SUSPENSION, gestor,
    )
    assert resultado["estado"].case_id != "frenos-anterior"
    assert resultado["decision"] != "SEGURIDAD_CRITICA"
    assert "esponjoso" not in resultado.get("consulta_consolidada", "").lower()
    top = resultado["estado"].top3_actual
    assert top, resultado
    assert any(p in top[0]["falla"].lower() for p in ("amortigu", "suspensi", "bieleta", "rótula")), top
    assert "orden de inspección" in resultado["respuesta_texto"]
    assert "no confirma la avería" in resultado["respuesta_texto"]
    raw = resultado["top3_ml_raw"]
    assert raw[0]["probabilidad"] >= top[0]["probabilidad"]
    for candidata in top:
        original = next(p for p in raw if p["falla"] == candidata["falla"])
        assert candidata["probabilidad"] == original["probabilidad"]
    dto = resultado["dto"]
    assert dto.predicciones_ml[0].falla == top[0]["falla"]
    assert dto.diagnostico_ml == top[0]["falla"]
    assert dto.predicciones_ml_raw[0].falla == raw[0]["falla"]
    assert not DiagnosticPersister.debe_solicitar_feedback(dto)


@pytest.mark.anyio
async def test_adapter_seguridad_limpia_confirmacion_pendiente():
    from src.core.services.webhook.diagnostic_workflow import TechnicalDiagnosticWorkflow
    from src.core.session_manager import SessionManager

    repo = InMemoryConversationRepository()
    estado = estado_frenos()
    gestor = SimpleNamespace(conversation_repo=repo, session_manager=SessionManager(), motor_rag=None)
    conversacion = SimpleNamespace(id="conversacion-test", contexto={
        "case_id": estado.case_id, "conversation_state": estado.exportar_dict(),
        "validacion_diagnostico": {"etapa": "esperando_confirmacion"},
        "mensaje_interactivo": {"msg_id": "anterior"},
    })
    dto = await TechnicalDiagnosticWorkflow._procesar_texto(
        gestor, "¿Puedo circular así?", estado.placa, "Toyota Corolla 2015",
        estado.session_id, "sin-envio", "meta",
        SimpleNamespace(id="usuario-test", taller_id="taller-test"), conversacion,
    )
    assert dto.tipo_consulta == "seguridad_critica"
    assert dto.confianza_ml == 0
    assert not DiagnosticPersister.debe_solicitar_feedback(dto)
    assert "validacion_diagnostico" not in conversacion.contexto
    assert "mensaje_interactivo" not in conversacion.contexto


@pytest.mark.anyio
async def test_persistencia_alerta_no_crea_diagnostico_ni_confirmacion(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock

    import src.core.services.webhook.diagnostic_persister as modulo

    mensajes = SimpleNamespace(crear_mensaje=AsyncMock())
    diagnosticos = MagicMock()
    for nombre, repo in (
        ("MensajeRepository", mensajes), ("DiagnosticoRepository", diagnosticos),
        ("VehiculoRepository", MagicMock()), ("OperacionesRepository", MagicMock()),
    ):
        monkeypatch.setattr(modulo, nombre, lambda _session, repo=repo: repo)
    monkeypatch.setattr(modulo, "cifrar_texto_reversible", lambda _texto: "destino-prueba")
    conversacion = SimpleNamespace(id="test", contexto={
        "case_id": "caso-test", "validacion_diagnostico": {"etapa": "esperando_confirmacion"},
    })
    dto = ResultadoDiagnostico(
        respuesta_texto="No circules. Frenos pendientes de comprobación.",
        diagnostico_ml="Advertencia", confianza_ml=0, contexto_manual="", titulo_manual="",
        tipo_consulta="seguridad_critica", modo_diagnostico="seguridad_critica",
    )
    await DiagnosticPersister.persistir_y_responder(
        AsyncMock(), dto, SimpleNamespace(id="usuario", taller_id="taller"), conversacion,
        "¿Puedo circular así?", "id-prueba", "sin-envio", "meta", "TEST-01", "Toyota Corolla",
        0, "test",
    )
    assert not diagnosticos.mock_calls
    mensajes.crear_mensaje.assert_awaited_once()
    salida = mensajes.crear_mensaje.call_args.kwargs
    assert salida["case_id"] == "caso-test"
    assert "SÍ / NO" not in salida["texto"]
    assert "validacion_diagnostico" not in conversacion.contexto
