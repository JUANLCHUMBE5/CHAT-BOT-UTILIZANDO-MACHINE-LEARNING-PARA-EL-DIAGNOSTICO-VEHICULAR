import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'backend')
from src.core.conversacion.models import ConversationState, EstadoOperativo
from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas
from src.core.conversacion.gestor_plan_b import GestorPlanB
from src.core.conversacion.formateador_compacto import FormateadorCompacto

state = ConversationState(session_id="test_session")
state.estado_operativo = EstadoOperativo.MARCHA
state.top3_actual = [
    {"falla": "Falla en bujias o bobinas de encendido (misfire)", "probabilidad": 0.70},
    {"falla": "Bomba de gasolina quemada o con baja presion", "probabilidad": 0.20},
]
state.registrar_pregunta(
    texto="¿Has podido verificar este punto o deseas que te detalle el procedimiento de prueba?",
    intent="general",
    hipotesis=["Falla en bujias o bobinas de encendido (misfire)", "Bomba de gasolina quemada o con baja presion"]
)

msg = "No lo he revisado. No tengo herramientas para comprobar la chispa ni medir la presión de gasolina."

es_corta = InterpreteRespuestasCortas.es_respuesta_corta(msg)
print("es_respuesta_corta:", es_corta)

interp = InterpreteRespuestasCortas.interpretar(state, msg)
print("InterpreteRespuestasCortas result:", interp)

print("Herramientas no disponibles en estado:", state.herramientas_no_disponibles)
print("Pruebas no disponibles en estado:", state.pruebas_no_disponibles)

plan_b = GestorPlanB.obtener_plan_b_para_falla(state.top3_actual[0]["falla"], state)
print("Plan B para falla principal:", plan_b)

preg_ctx, intent_ctx = FormateadorCompacto.obtener_pregunta_contextual(state.top3_actual, msg, state)
print("Pregunta contextual generada:", preg_ctx)
print("Intent:", intent_ctx)

resp_formateada = FormateadorCompacto.formatear_respuesta_diagnostico(
    top_hipotesis=state.top3_actual,
    sintoma_original=msg,
    estado=state,
)
print("\n--- RESPUESTA FORMATEADA ---")
print(resp_formateada)
