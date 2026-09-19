"""Pruebas de la Fase 9.11: Auditoría y Corrección de Plan B sin Herramientas.

Verifica:
1. Reproducción exacta del incidente real Fase 9.10 (tirones -> sin herramientas para chispa ni presión).
2. Activación de Plan B cuando no se cuenta con herramientas.
3. No descarte de hipótesis ni invención de resultados ante 'no lo he revisado'.
4. Alternativa segura ante 'no sé usarlo'.
5. Re-habilitación de pruebas cuando posteriormente se consigue la herramienta.
6. Prevención de bucles infinitos ante múltiples herramientas indisponibles.
7. Disponibilidad de herramienta que entrega procedimiento estándar.
"""

from unittest.mock import MagicMock

import pytest

from src.core.conversacion.formateador_compacto import FormateadorCompacto
from src.core.conversacion.gestor_plan_b import GestorPlanB
from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas
from src.core.conversacion.models import (
    ConversationState,
    EstadoOperativo,
    QuestionIntent,
)
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import (
    InMemoryConversationRepository,
)
from src.core.gestor_diagnostico import ResultadoDiagnostico


@pytest.fixture
def repo():
    return InMemoryConversationRepository()


@pytest.fixture
def orquestador(repo):
    return OrquestadorConversacion(repositorio=repo)


@pytest.fixture
def gestor_mock():
    gestor = MagicMock()
    del gestor.session_manager
    dto = ResultadoDiagnostico(
        respuesta_texto="Diagnóstico de prueba",
        diagnostico_ml="Falla en bujias o bobinas de encendido (misfire)",
        confianza_ml=0.70,
        contexto_manual="Manual de bujías",
        titulo_manual="Manual OEM Bujías",
        requiere_revision_humana=False,
        predicciones_ml=[
            {"falla": "Falla en bujias o bobinas de encendido (misfire)", "probabilidad": 0.70},
            {"falla": "Bomba de gasolina quemada o con baja presion", "probabilidad": 0.20},
        ],
    )
    gestor.procesar_consulta_texto.return_value = dto
    return gestor


@pytest.mark.anyio
async def test_reproduccion_exacta_incidente_fase_9_11(orquestador, gestor_mock):
    """
    Reproduce el incidente de Fase 9.10:
    Usuario reporta tirones y responde pregunta de temperatura.
    Luego CarBot presenta bujías/bobinas 70% y bomba 20%.
    Usuario dice: 'No lo he revisado. No tengo herramientas para comprobar la chispa ni medir la presión de gasolina.'
    Resultado obligatorio:
    - No repite la prueba de comprobación de chispa con herramientas.
    - No repite '¿deseas que te detalle el procedimiento de prueba?'.
    - Registra indisponibilidad de chispa y manómetro.
    - Activa Plan B sin herramientas (inspección visual de bobinas/cables o auditiva de bomba).
    - No descarta las hipótesis.
    """
    session_id = "test_incidente_fase_9_11_real"
    estado = ConversationState(session_id=session_id, case_id="case_incidente_9_11")
    estado.estado_operativo = EstadoOperativo.MARCHA
    estado.top3_actual = [
        {"falla": "Falla en bujias o bobinas de encendido (misfire)", "probabilidad": 0.70},
        {"falla": "Bomba de gasolina quemada o con baja presion", "probabilidad": 0.20},
    ]
    estado.registrar_pregunta(
        texto="¿Has podido verificar este punto o deseas que te detalle el procedimiento de prueba?",
        intent=QuestionIntent.GENERAL,
        hipotesis=["Falla en bujias o bobinas de encendido (misfire)", "Bomba de gasolina quemada o con baja presion"],
    )
    await orquestador.repositorio.save_session(session_id, estado)

    msg_usuario = "No lo he revisado. No tengo herramientas para comprobar la chispa ni medir la presión de gasolina."

    resp = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=msg_usuario,
        gestor_diagnostico=gestor_mock,
    )

    # Verificaciones obligatorias
    assert resp["decision"] == "PLAN_B"
    texto_resp = resp["respuesta_texto"].lower()

    # NO debe repetir la pregunta anterior de procedimiento
    assert "deseas que te detalle el procedimiento" not in texto_resp
    assert "has podido verificar este punto" not in texto_resp

    # DEBE activar Plan B sin herramientas para chispa / bujías
    assert any(w in texto_resp for w in ("sin herramientas", "visual", "bobinas", "cables", "aceite"))

    # Estado acumulativo debe reflejar herramientas y pruebas bloqueadas
    estado_act = resp["estado"]
    assert "chispa" in estado_act.herramientas_no_disponibles or "manometro" in estado_act.herramientas_no_disponibles
    assert estado_act.es_prueba_bloqueada("comprobar_chispa_bobinas")
    assert estado_act.es_prueba_bloqueada("medir_presion_gasolina")

    # Hipótesis NO deben estar descartadas
    assert "Falla en bujias o bobinas de encendido (misfire)" not in estado_act.hipotesis_descartadas
    assert "Bomba de gasolina quemada o con baja presion" not in estado_act.hipotesis_descartadas


@pytest.mark.anyio
async def test_herramienta_no_disponible_activa_plan_b_multimetro(orquestador, gestor_mock):
    """Verifica que 'no tengo multímetro' active el Plan B de luces/inspección en arranque."""
    session_id = "test_sin_multimetro"
    estado = ConversationState(session_id=session_id, case_id="case_sin_multimetro")
    estado.top3_actual = [
        {"falla": "Bateria descargada o bornes sulfatados", "probabilidad": 0.85},
        {"falla": "Falla en motor de arranque o solenoide defectuoso", "probabilidad": 0.10},
    ]
    estado.registrar_pregunta(
        texto="¿Tienes multímetro para comprobar el voltaje?",
        intent=QuestionIntent.DISPONIBILIDAD_HERRAMIENTA,
        hipotesis=["Bateria descargada o bornes sulfatados"],
    )
    await orquestador.repositorio.save_session(session_id, estado)

    resp = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario="No tengo tester ni multímetro",
        gestor_diagnostico=gestor_mock,
    )

    assert resp["decision"] == "PLAN_B"
    assert "luces del tablero" in resp["respuesta_texto"].lower()
    assert "multimetro" in resp["estado"].herramientas_no_disponibles


@pytest.mark.anyio
async def test_herramienta_disponible_da_procedimiento_o_medicion(orquestador, gestor_mock):
    """Verifica que con herramienta confirmada ('sí tengo'), solicite la medición técnica."""
    session_id = "test_con_manometro"
    estado = ConversationState(session_id=session_id, case_id="case_con_manometro")
    estado.top3_actual = [
        {"falla": "Bomba de gasolina quemada o con baja presion", "probabilidad": 0.80},
    ]
    estado.registrar_pregunta(
        texto="¿Cuentas con manómetro para medir la presión de combustible?",
        intent=QuestionIntent.DISPONIBILIDAD_HERRAMIENTA,
        hipotesis=["Bomba de gasolina quemada o con baja presion"],
    )
    await orquestador.repositorio.save_session(session_id, estado)

    resp = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario="Sí tengo manómetro",
        gestor_diagnostico=gestor_mock,
    )

    assert resp["decision"] == "PREGUNTAR"
    assert any(w in resp["respuesta_texto"].lower() for w in ("psi", "presión", "manómetro"))
    assert resp["question_intent"] == QuestionIntent.MEDICION_PRESION.value


@pytest.mark.anyio
async def test_no_lo_revise_no_inventa_resultado_ni_descarta():
    """'No lo he revisado' nunca debe inventar mediciones ni descartar la falla analizada."""
    estado = ConversationState(session_id="test_no_revisado")
    hechos = GestorPlanB.registrar_bloqueos_en_estado(estado, "Todavía no lo he revisado, no he mirado nada.")

    assert "estado_inspeccion_previa" in hechos
    assert estado.obtener_hecho("estado_inspeccion_previa").valor == "no_revisado_aun"
    assert len(estado.hipotesis_descartadas) == 0


@pytest.mark.anyio
async def test_no_se_usarlo_alternativa_segura():
    """'No sé usar el multímetro' activa Plan B y registra dificultad de operación."""
    estado = ConversationState(session_id="test_no_se_usar")
    estado.top3_actual = [{"falla": "Bateria descargada o bornes sulfatados", "probabilidad": 0.80}]
    estado.registrar_pregunta(
        texto="¿Tienes multímetro para comprobar el voltaje?",
        intent=QuestionIntent.DISPONIBILIDAD_HERRAMIENTA,
    )

    interp = InterpreteRespuestasCortas.interpretar(estado, "Tengo uno pero no sé cómo usarlo")
    assert interp is not None
    assert interp["categoria_respuesta"] == "HERRAMIENTA_INDISPONIBLE"
    assert interp["no_sabe_usar"] is True
    assert "multimetro" in estado.herramientas_no_disponibles


@pytest.mark.anyio
async def test_posteriormente_consigue_herramienta_desbloquea_prueba():
    """Si el usuario consigue la herramienta después, se desbloquea en el estado."""
    estado = ConversationState(session_id="test_recuperacion")
    estado.bloquear_herramienta("multimetro")
    estado.bloquear_prueba("medicion_voltaje_multimetro", "multimetro")
    assert estado.es_prueba_bloqueada("medicion_voltaje_multimetro")

    GestorPlanB.registrar_bloqueos_en_estado(estado, "Ya conseguí un multímetro prestado de mi vecino")
    assert "multimetro" not in estado.herramientas_no_disponibles
    assert not estado.es_prueba_bloqueada("medicion_voltaje_multimetro")


@pytest.mark.anyio
async def test_dos_herramientas_indisponibles_no_alterna_infinitamente(orquestador, gestor_mock):
    """
    Si tanto la herramienta A (chispa) como la B (manómetro) están indisponibles,
    y las alternativas sensoriales se agotaron, no cicla entre ambas y deriva a taller.
    """
    session_id = "test_dos_indisponibles"
    estado = ConversationState(session_id=session_id, case_id="case_dos_indisponibles")
    estado.top3_actual = [
        {"falla": "Falla en bujias o bobinas de encendido (misfire)", "probabilidad": 0.60},
        {"falla": "Bomba de gasolina quemada o con baja presion", "probabilidad": 0.30},
    ]
    # Simular que ya se hicieron 2 preguntas previas (incluyendo la visual de bobinas)
    estado.registrar_pregunta(texto="Pregunta 1 previa", intent=QuestionIntent.GENERAL)
    estado.registrar_pregunta(
        texto="Al revisar visualmente las bobinas: ¿notas grietas?",
        intent=QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
    )
    estado.bloquear_herramienta("general")
    estado.bloquear_herramienta("chispa")
    estado.bloquear_herramienta("manometro")
    await orquestador.repositorio.save_session(session_id, estado)

    resp = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario="Tampoco tengo manómetro ni ninguna otra herramienta.",
        gestor_diagnostico=gestor_mock,
    )

    assert resp["decision"] == "PLAN_B"
    # No debe volver a preguntar por comprobación con chispa ni manómetro
    assert "chispa azul" not in resp["respuesta_texto"].lower()
    assert "manómetro conectado" not in resp["respuesta_texto"].lower()


@pytest.mark.anyio
async def test_formateador_compacto_usa_plan_b_cuando_herramienta_bloqueada():
    """El formateador de WhatsApp debe presentar en 'Primero revisa:' el Plan B sin herramientas."""
    estado = ConversationState(session_id="test_formateador_plan_b")
    estado.bloquear_herramienta("chispa")
    estado.bloquear_prueba("comprobar_chispa_bobinas", "chispa")

    hipotesis = [
        {"falla": "Falla en bujias o bobinas de encendido (misfire)", "probabilidad": 0.70},
        {"falla": "Bomba de gasolina quemada o con baja presion", "probabilidad": 0.20},
    ]

    salida = FormateadorCompacto.formatear_respuesta_diagnostico(
        top_hipotesis=hipotesis,
        sintoma_original="el motor tironea",
        estado=estado,
    )

    # Debe contener la acción de Plan B en vez de la primaria con herramientas
    assert "Primero revisa:" in salida
    assert "visual de bobinas" in salida.lower()
    assert "sin herramientas para chispa" in salida.lower()
