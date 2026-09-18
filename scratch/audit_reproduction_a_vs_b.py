import asyncio
import json
import sys

sys.path.insert(0, "backend")
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.formateador_compacto import FormateadorCompacto
from src.core.conversacion.models import ConversationState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.intent_classifier import clasificar_intencion_consulta
from src.core.sanitizer import sanitizar_prompt_usuario
from src.core.traductor_jerga import normalizar_jerga_peruana
from src.infrastructure.container import ServiceContainer

msg = "Buenas, mi carro estaba normal hasta ayer. Hoy salí a la carretera y a los 20 minutos de manejar empecé a sentir que perdía fuerza, como que se ahogaba. Bajé la velocidad y se recuperó. Pero a los 5 minutos otra vez. Ya no puedo pasar de 80. ¿Qué será?"


def run_condition_a():
    print("================ CONDICIÓN A: SESIÓN COMPLETAMENTE NUEVA ================")
    st = ConversationState(session_id="sesion_nueva_clean")
    hechos = ExtractorHechos.extraer_y_actualizar(st, msg)
    consulta_sint = SintetizadorConsulta.sintetizar(st)
    texto_norm = normalizar_jerga_peruana(sanitizar_prompt_usuario(consulta_sint))

    ml = ServiceContainer.get_modelo_ml()
    rag = ServiceContainer.get_motor_rag()

    macro_sist = ml.predecir_sistema(consulta_sint)
    top_ml = ml.predecir_top_fallas(consulta_sint, limite=3)

    # RAG
    falla_top1 = top_ml[0]["falla"]
    consulta_rag = falla_top1
    contexto_rag, titulo_rag = rag.recuperar_contexto(consulta_rag)

    # Formateo de respuesta
    resp_final = FormateadorCompacto.formatear_respuesta_diagnostico(
        top_hipotesis=top_ml,
        sintoma_original=msg,
        contexto_rag=contexto_rag,
        estado=st,
    )

    res = {
        "condicion": "A_SESION_NUEVA",
        "mensaje_original": msg,
        "hechos_extraidos": hechos,
        "consulta_sintetizada": consulta_sint,
        "texto_normalizado": texto_norm,
        "macro_sistema": macro_sist,
        "top_ml": top_ml,
        "consulta_rag": consulta_rag,
        "titulo_rag": titulo_rag,
        "resultado_rag_len": len(contexto_rag),
        "respuesta_final": resp_final,
    }
    return res


def run_condition_b():
    print("\n================ CONDICIÓN B: SESIÓN EXISTENTE (CONTAMINADA) ================")
    # Reproducir el estado que existía en la base de datos tras el turno 7 (arrancador/batería)
    st = ConversationState(session_id="sesion_existente_contaminada")
    msg_prev = "Buenas, hoy en la mañana salí normal, todo bien. Pero en la tarde ya no quiso arrancar. Le doy a la llave y hace clac clac clac, como si algo golpeara, pero no prende. Las luces del tablero sí prenden pero se ponen medio tenues cuando le doy arranque. ¿Qué será?"

    # Extraer hechos previos
    ExtractorHechos.extraer_y_actualizar(st, msg_prev)
    st.turnos_repregunta = 3  # Había alcanzado el límite de repreguntas

    # En la sesión real, los hechos del mensaje nuevo NO eliminaron los hechos previos porque la intención
    # o la síntesis conservó la bolsa de hechos o se clasificó como consulta técnica.
    # En el caso real de la traza 8 observada en DB:
    # consulta_consolidada = 'presenta ruido anómalo, motor no arranca, chasquido de arranque clac.'
    consulta_sint_b = "presenta ruido anómalo, motor no arranca, chasquido de arranque clac."
    texto_norm_b = normalizar_jerga_peruana(sanitizar_prompt_usuario(consulta_sint_b))

    ml = ServiceContainer.get_modelo_ml()
    rag = ServiceContainer.get_motor_rag()

    macro_sist_b = ml.predecir_sistema(consulta_sint_b)
    top_ml_b = ml.predecir_top_fallas(consulta_sint_b, limite=3)

    falla_top1_b = top_ml_b[0]["falla"]
    consulta_rag_b = falla_top1_b
    contexto_rag_b, titulo_rag_b = rag.recuperar_contexto(consulta_rag_b)

    resp_final_b = FormateadorCompacto.formatear_respuesta_diagnostico(
        top_hipotesis=top_ml_b,
        sintoma_original=msg,
        contexto_rag=contexto_rag_b,
        estado=st,
    )

    res = {
        "condicion": "B_SESION_EXISTENTE_CONTAMINADA",
        "mensaje_original": msg,
        "hechos_en_estado": list(st.hechos.keys()),
        "consulta_sintetizada": consulta_sint_b,
        "texto_normalizado": texto_norm_b,
        "macro_sistema": macro_sist_b,
        "top_ml": top_ml_b,
        "consulta_rag": consulta_rag_b,
        "titulo_rag": titulo_rag_b,
        "resultado_rag_len": len(contexto_rag_b),
        "respuesta_final": resp_final_b,
    }
    return res


res_a = run_condition_a()
res_b = run_condition_b()

with open("scratch/resultado_a_vs_b.json", "w", encoding="utf-8") as f:
    json.dump({"condicion_a": res_a, "condicion_b": res_b}, f, ensure_ascii=False, indent=2)

print("\nResultados guardados en scratch/resultado_a_vs_b.json con éxito.")
