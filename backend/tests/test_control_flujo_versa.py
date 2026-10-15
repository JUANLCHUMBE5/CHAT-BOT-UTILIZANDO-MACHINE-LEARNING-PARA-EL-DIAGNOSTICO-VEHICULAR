"""Regresiones aisladas de intención, aclaraciones y abstención ML."""

from src.core.conversacion.clasificador_mensajes import clasificar_mensaje
from src.core.conversacion.control_aclaraciones import aclaraciones_emitidas, dato_desconocido, debe_avanzar
from src.core.conversacion.formateador_compacto import FormateadorCompacto
from src.core.conversacion.models import ConversationState, QuestionIntent
from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad
from src.core.diagnostico.prompt_builder import construir_prompt_diagnostico


def test_descarte_y_hallazgo_actualizan_mismo_caso():
    estado = ConversationState(session_id="local")
    estado.active_symptoms.append("mezcla pobre")
    estado.top3_actual = [{"falla": "IAC", "probabilidad": 0.35}]
    assert clasificar_mensaje("ya revisé el cuerpo y está bien", estado) == "descarte"
    assert clasificar_mensaje("los injectores no inyectan", estado) == "hallazgo_mecanico"
    assert clasificar_mensaje("No", estado) == "descarte"
    assert clasificar_mensaje("Sí", estado) == "confirmacion"


def test_intencion_de_jerga_contradiccion_y_sintoma_nuevo():
    estado = ConversationState(session_id="local")
    estado.active_symptoms.append("mezcla pobre")
    estado.registrar_pregunta(QuestionIntent.MEDICION_TECNICA, "¿Tienes STFT/LTFT?")
    assert clasificar_mensaje("No tengo esa lectura", estado) == "respuesta_pendiente"
    assert clasificar_mensaje("No es mezcla, es refrigeración", estado) == "descarte"
    assert clasificar_mensaje("Los injectores no inyectan", estado) == "hallazgo_mecanico"
    assert clasificar_mensaje("Ahora hace ruido al frenar", estado) == "sintoma_nuevo"


def test_dato_desconocido_y_tope_configurable_avanzan():
    assert not dato_desconocido("En pista lisa casi no se escucha")
    assert dato_desconocido("No sé")
    estado = ConversationState(session_id="local", max_repreguntas=2)
    estado.active_symptoms.append("mezcla pobre")
    estado.registrar_pregunta(QuestionIntent.MEDICION_TECNICA, "¿Tienes el DTC exacto?")
    assert debe_avanzar(estado, "No tengo ese dato")
    assert not debe_avanzar(estado, "Al acelerar")
    estado.registrar_pregunta(
        QuestionIntent.MEDICION_TECNICA, "¿Tienes STFT/LTFT?", incrementar_repregunta=False,
    )
    assert aclaraciones_emitidas(estado) == 2
    assert debe_avanzar(estado, "Sigue igual")


def test_hipotesis_descartada_no_resucita_si_era_la_unica():
    estado = ConversationState(session_id="local")
    estado.hipotesis_descartadas = ["IAC"]
    presentadas, excluidas = ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
        [{"falla": "IAC", "probabilidad": 0.79}], estado,
        nueva_evidencia="Volví a mencionar IAC, pero está descartada",
    )
    assert presentadas == []
    assert excluidas[0]["motivo"].startswith("RECHAZADA_PREVIAMENTE")


def test_confianza_cero_no_se_presenta_como_hipotesis():
    mensaje = FormateadorCompacto.formatear_respuesta_diagnostico([])
    assert "50%" not in mensaje
    assert "No tengo una hipótesis ML compatible" in mensaje
    prompt = construir_prompt_diagnostico(
        pregunta_llm="mezcla pobre", diagnostico_ml="Sin hipótesis ML pertinente para admisión",
        confianza_pct=0, titulo_manual="", contexto_llm="", alerta_revision="",
        predicciones_ml=[],
    )
    assert "Hipótesis Principal: Sin hipótesis" not in prompt
    assert "Sin hipótesis ML pertinente; evidencia insuficiente" in prompt
