import pytest

from src.core.conversacion.models import ConversationState, EstadoOperativo, FactType
from src.core.conversacion.segmentacion.ejecutor_transicion import resolver_transicion_turno
from src.core.conversacion.segmentacion.tipos import DecisionTransicion
from src.core.diagnostico.seguridad_informativa import proteger_respuesta_informativa, temas_consulta


@pytest.mark.parametrize("contexto", [
    "No busco información de frenos.",
    "No quiero instrucciones sobre frenos.",
    "No me des información de frenos.",
    "No generes procedimientos de frenos.",
    "No busques información sobre frenos.",
    'El proveedor dijo "purgar frenos".',
    "Antes hablamos de frenos.",
])
def test_af01_contexto_no_autoriza_tema(contexto):
    pregunta = "¿Cómo hago el reaprendizaje del cuerpo de aceleración? " + contexto
    respuesta = "Purgar los frenos siguiendo el manual OEM."
    texto, meta = proteger_respuesta_informativa(pregunta, respuesta, {"usado": True})
    assert texto != respuesta
    assert "frenos" not in texto
    assert not meta["usado"]


@pytest.mark.parametrize("pregunta", [
    "Explica el reaprendizaje del cuerpo de aceleración.",
    'Explica "reaprendizaje del cuerpo de aceleración".',
    "Antes hablamos de frenos; ahora explica el reaprendizaje del cuerpo de aceleración.",
])
def test_af01_conserva_tema_solicitado(pregunta):
    texto = "El reaprendizaje del cuerpo de aceleración depende del manual OEM."
    assert proteger_respuesta_informativa(pregunta, texto, {"usado": True})[0] == texto
    assert "admisión y cuerpo de aceleración" in temas_consulta(pregunta)["solicitados"]


@pytest.mark.parametrize("anterior,mensaje,destino", [
    ("MARCHA_MOTOR", "No es problema de motor, el ruido viene de la suspensión. Corrige el síntoma.", "SUSPENSION"),
    ("SUSPENSION", "Me equivoqué, no es suspensión; al frenar vibra el pedal de freno.", "FRENOS"),
])
def test_af02_rectifica_sistema_sin_perder_identidad(anterior, mensaje, destino):
    estado = ConversationState(session_id="taller-A", case_id="caso-A", placa="ABC-123")
    estado.dominio_probable = anterior
    estado.marca, estado.modelo, estado.combustible = "Toyota", "Corolla", "gasolina"
    estado.registrar_hecho("sintoma_anterior", "síntoma rectificado", tipo=FactType.SINTOMA)
    estado.top3_actual = [{"falla": "hipótesis anterior", "probabilidad": 0.42}]
    estado.estado_operativo = EstadoOperativo.MARCHA
    resultado, transicion = resolver_transicion_turno(
        estado, mensaje, None, estado.session_id, 0, {}, tipo_mensaje="correccion_sistema",
    )
    assert resultado is None
    assert transicion.decision == DecisionTransicion.MANTENER_CASO
    assert estado.case_id == "caso-A"
    assert estado.placa == "ABC-123" and estado.combustible == "gasolina"
    assert estado.dominio_probable == destino
    assert estado.top3_actual == []
    assert estado.obtener_hecho("sintoma_anterior") is None
    assert any(h.get("campo") == "sintoma_anterior" for h in estado.hechos_historicos)


@pytest.mark.parametrize("mensaje", ["nuevo caso", "otro vehículo"])
def test_af02_nuevo_caso_explicito_sigue_abriendo_identidad(mensaje):
    estado = ConversationState(session_id="taller-A", case_id="caso-A", placa="ABC-123")
    estado.registrar_hecho("sintoma_anterior", "vibración")
    _, transicion = resolver_transicion_turno(estado, mensaje, None, estado.session_id, 0, {})
    assert transicion.decision == DecisionTransicion.CAMBIO_DE_CASO
    assert estado.case_id != "caso-A"
    assert estado.placa is None


@pytest.mark.anyio
@pytest.mark.parametrize("inicio,correccion,dominio,familia", [
    ("Toyota Corolla 2015 gasolina pierde potencia al acelerar.",
     "No es problema de motor, el ruido viene de la suspensión. Corrige el síntoma.",
     "SUSPENSION", "suspension"),
    ("Toyota Corolla 2015 gasolina golpea la suspensión en baches.",
     "Me equivoqué, no es suspensión; al frenar vibra el pedal de freno.", "FRENOS", "frenos"),
])
async def test_af02_conversacion_real_rectifica_sin_rechazar_sistema_afirmado(inicio, correccion, dominio, familia):
    from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
    from src.core.conversacion.repositorio import InMemoryConversationRepository
    from src.core.gestor_diagnostico import GestorDiagnostico

    gestor = GestorDiagnostico()
    gestor.api_key = ""
    orq = OrquestadorConversacion(repositorio=InMemoryConversationRepository())
    primero = await orq.procesar_turno(session_id="af02-" + familia, texto_usuario=inicio, gestor_diagnostico=gestor)
    case_id = primero["estado"].case_id
    segundo = await orq.procesar_turno(session_id="af02-" + familia, texto_usuario=correccion, gestor_diagnostico=gestor)
    estado = segundo["estado"]
    assert estado.case_id == case_id
    assert estado.dominio_probable == dominio
    assert estado.obtener_hecho("sintoma_rectificado") is not None
    assert estado.obtener_hecho("rechazo_usuario_" + familia) is None
    assert inicio in estado.historial_mensajes_usuario
    assert correccion in estado.historial_mensajes_usuario
    assert estado.hechos_historicos


def test_af02_negacion_de_otro_caso_no_confirma_cambio():
    from src.core.conversacion.models import QuestionIntent

    estado = ConversationState(session_id="taller-A", case_id="caso-A")
    estado.registrar_hecho("sintoma", "vibración")
    estado.registrar_pregunta(QuestionIntent.ACLARACION_ALCANCE, "¿Mismo caso u otro carro?")
    _, transicion = resolver_transicion_turno(
        estado, "No es otro carro; es el mismo caso.", None, estado.session_id, 0, {},
    )
    assert transicion.decision != DecisionTransicion.CAMBIO_DE_CASO
    assert estado.case_id == "caso-A"
