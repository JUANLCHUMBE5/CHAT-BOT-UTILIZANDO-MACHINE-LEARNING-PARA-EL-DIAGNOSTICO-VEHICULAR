import asyncio
import json
import sys
sys.path.insert(0, 'backend')
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from src.core.conversacion.models import ConversationState, EstadoOperativo, QuestionIntent
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.suficiencia_informacion import EvaluadorSuficiencia
from src.core.gestor_diagnostico import GestorDiagnostico

msg = (
    "Buenas, mi carro tiene un problema. Ayer lo dejé estacionado en la calle y cuando "
    "volví en la noche ya no quiso arrancar. Le doy a la llave y hace como un clic seco, "
    "una sola vez, y nada más. Las luces del tablero sí prenden bien, y el radio también."
)

print("=== 1. SIMULACION CASO LIMPIO (TEST UNITARIO) ===")
st_clean = ConversationState(session_id="test_clean")
hechos_clean = ExtractorHechos.extraer_y_actualizar(st_clean, msg)
print("Estado operativo:", st_clean.estado_operativo.value)
print("Hechos extraídos:", hechos_clean)
score_c, cat_c, suf_c, mot_c = EvaluadorSuficiencia.evaluar(st_clean)
print("Suficiencia:", score_c, "Suficiente?", suf_c, "Motivo:", mot_c)
sel_c = GeneradorPreguntas.seleccionar_pregunta_con_filtro(st_clean)
if sel_c:
    txt, opc, intent, cand, desc = sel_c
    print("Pregunta seleccionada:", txt)
    print("Intent:", intent.value)
    print("Candidatas:", cand)
    print("Descartadas:", desc)
else:
    print("Ninguna pregunta seleccionada")

print("\n=== 2. SIMULACION CON CONTEXTO TURNO 1 (EL ESTADO QUE HABÍA EN WHATSAPP A LAS 01:00:06) ===")
# En WhatsApp a las 00:43:11, se había registrado CONDICION_OPERACION
st_wapp = ConversationState(session_id="test_wapp")
# Simular turno 1 previo
st_wapp.turnos_repregunta = 1
st_wapp.turno_actual = 1
st_wapp.registrar_pregunta(
    intent=QuestionIntent.CONDICION_OPERACION,
    texto="Para orientar el diagnóstico: ¿la falla se presenta cuando el vehículo está detenido en ralentí, al acelerar con fuerza en carretera o únicamente al pisar el pedal de freno?",
    opciones=["Detenido en ralentí", "Al acelerar bajo carga", "Al frenar"]
)
# Ahora llega el mensaje a las 01:00:06 (Turno 2)
st_wapp.turno_actual = 2
st_wapp.turnos_repregunta = 2 # o el orquestador registra respuesta
st_wapp.registrar_respuesta(msg, "respuesta_usuario")
hechos_wapp = ExtractorHechos.extraer_y_actualizar(st_wapp, msg)
print("Estado operativo WAPP:", st_wapp.estado_operativo.value)
print("Hechos en WAPP:", [f"{h.campo}={h.valor}" for h in st_wapp.hechos.values()])
print("Preguntas ya realizadas:", [p["intent"] for p in st_wapp.preguntas_realizadas])
print("Respuestas obtenidas:", len(st_wapp.respuestas_obtenidas))
score_w, cat_w, suf_w, mot_w = EvaluadorSuficiencia.evaluar(st_wapp)
print("Suficiencia:", score_w, "Suficiente?", suf_w)

sel_w = GeneradorPreguntas.seleccionar_pregunta_con_filtro(st_wapp)
if sel_w:
    txt_w, opc_w, intent_w, cand_w, desc_w = sel_w
    print("Pregunta seleccionada WAPP:", txt_w)
    print("Intent WAPP:", intent_w.value)
    print("Candidatas WAPP:", cand_w)
    print("Descartadas WAPP:", desc_w)
else:
    print("Ninguna pregunta seleccionada WAPP")
