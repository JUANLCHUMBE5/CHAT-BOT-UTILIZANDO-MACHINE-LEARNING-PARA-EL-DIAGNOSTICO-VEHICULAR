import pytest

from src.core.conversacion.models import ConversationState, FactState, QuestionIntent
from src.core.conversacion.respuestas_cortas.acciones_previas import interpretar_accion_previa
from src.core.conversacion.respuestas_cortas.interprete_intenciones import interpretar_respuesta_corta


@pytest.mark.parametrize("texto", ["ya lo cambié", "ya lo revisé"])
def test_accion_sin_pregunta_no_confirma_ni_descarta(texto):
    estado = ConversationState(session_id="accion-aislada")
    estado.historial_mensajes_usuario = ["El termostato se queda pegado", texto]
    resultado = interpretar_accion_previa(estado, texto, None)
    assert "termostato" in resultado["valor"]
    assert "resultado no confirmado" in resultado["valor"]
    assert resultado["hecho"]["categoria"] in ("antecedente", "prueba_realizada")


def test_antecedente_ambiguo_no_inventa_componente():
    estado = ConversationState(session_id="ambiguo")
    estado.historial_mensajes_usuario = ["Revisar bomba y filtro", "ya lo cambié"]
    resultado = interpretar_accion_previa(estado, "ya lo cambié", None)
    assert "componente no identificado" in resultado["valor"]


@pytest.mark.parametrize("texto", ["no lo cambié", "¿ya lo cambié?", 'Dije "ya lo cambié"'])
def test_no_asume_accion_de_negaciones_preguntas_o_citas(texto):
    estado = ConversationState(session_id="sin-accion")
    assert interpretar_accion_previa(estado, texto, None) is None


@pytest.mark.parametrize("texto", ["creo que sí", "puede ser"])
def test_respuesta_tentativa_no_sobrescribe_evidencia_confirmada(texto):
    estado = ConversationState(session_id="tentativa")
    estado.registrar_hecho("condicion_operacion", "al frenar", categoria="condicion")
    estado.registrar_pregunta(QuestionIntent.CONDICION_OPERACION, "¿Ocurre también acelerando?")
    resultado = interpretar_respuesta_corta(estado, texto)
    assert estado.obtener_valor_confirmado("condicion_operacion") == "al frenar"
    assert resultado["estado"] == FactState.AMBIGUO.value
