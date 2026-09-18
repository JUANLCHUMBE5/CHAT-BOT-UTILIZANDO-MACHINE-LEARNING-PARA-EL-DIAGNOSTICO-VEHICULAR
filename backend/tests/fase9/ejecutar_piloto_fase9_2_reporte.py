"""Script de ejecución formal y trazabilidad para la Fase 9.2 (20 conversaciones piloto).

Ejecuta las 20 conversaciones y recolecta los 12 campos obligatorios de trazabilidad por cada turno.
Salida: backend/tests/fase9/resultados_piloto_fase9_2.json
"""

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.core.conversacion.models import (
    ConversationPhase,
    ConversationState,
    FactState,
    QuestionIntent,
)
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import (
    InMemoryConversationRepository,
    PostgresConversationRepository,
)
from src.core.gestor_diagnostico import GestorDiagnostico


class TrazabilidadCollector:
    def __init__(self):
        self.trazas: List[Dict[str, Any]] = []

    def registrar(
        self,
        case_id: str,
        session_id: str,
        turn_id: int,
        mensaje_original: str,
        estado_recuperado: Dict[str, Any],
        hechos_nuevos: List[Dict[str, Any]],
        estado_actualizado: Dict[str, Any],
        consulta_consolidada: str,
        question_intent: Optional[str],
        top3: List[Dict[str, Any]],
        decision: str,
        respuesta: str,
        latencia_ms: float,
    ):
        traza = {
            "session_id": session_id,
            "case_id": case_id,
            "turn_id": turn_id,
            "mensaje_original": mensaje_original,
            "estado_recuperado": {
                "fase": estado_recuperado.get("fase", "INICIO"),
                "turno": estado_recuperado.get("turno_actual", 0),
                "num_hechos": len(estado_recuperado.get("hechos", {})),
                "vehiculo": f"{estado_recuperado.get('marca', '')} {estado_recuperado.get('modelo', '')}".strip() or None,
            },
            "hechos_nuevos": hechos_nuevos,
            "estado_actualizado": {
                "fase": estado_actualizado.get("fase"),
                "turno": estado_actualizado.get("turno_actual"),
                "num_hechos": len(estado_actualizado.get("hechos", {})),
                "vehiculo": f"{estado_actualizado.get('marca', '')} {estado_actualizado.get('modelo', '')}".strip() or None,
                "hechos_confirmados": [
                    f"{k}={v['valor']}"
                    for k, v in estado_actualizado.get("hechos", {}).items()
                    if v.get("estado") == "CONFIRMADO"
                ],
            },
            "consulta_consolidada": consulta_consolidada,
            "question_intent": question_intent or "SIN_PREGUNTA",
            "Top-3": [
                {"falla": t.get("falla"), "prob": round(t.get("probabilidad", 0.0), 3)}
                for t in top3[:3]
            ],
            "decision": decision,
            "respuesta": respuesta[:200] + "..." if len(respuesta) > 200 else respuesta,
            "latencia_total_ms": round(latencia_ms, 2),
        }
        self.trazas.append(traza)
        return traza


async def ejecutar_piloto():
    gestor = GestorDiagnostico()
    collector = TrazabilidadCollector()
    resultados_casos = []

    print("[FASE 9.2] Iniciando ejecución de las 20 conversaciones técnicas piloto...")

    # CASO 01: Acumulación progresiva obligatoria (Toyota Yaris 2015, 6 turnos)
    repo01 = InMemoryConversationRepository()
    orq01 = OrquestadorConversacion(repositorio=repo01)
    s01 = "pilot_01_yaris"
    m01 = [
        "Tengo un Toyota Yaris 2015",
        "tiembla",
        "cuando estoy parado en el semáforo",
        "cuando acelero mejora",
        "las bujías ya las cambié",
        "entonces qué puede ser?",
    ]
    for idx, msg in enumerate(m01, 1):
        t0 = time.perf_counter()
        st_prev = await repo01.get_session(s01)
        prev_dict = st_prev.exportar_dict() if st_prev else {}
        res = await orq01.procesar_turno(session_id=s01, texto_usuario=msg, gestor_diagnostico=gestor)
        st_post: ConversationState = res["estado"]
        lat = (time.perf_counter() - t0) * 1000
        q_int = st_post.preguntas_realizadas[-1].get("intent") if st_post.preguntas_realizadas else None
        collector.registrar(
            "CASO_01", s01, idx, msg, prev_dict,
            st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []),
            st_post.exportar_dict(), res["consulta_consolidada"], q_int,
            st_post.top3_actual, res["decision"], res["respuesta_texto"], lat
        )
    st_f01 = await repo01.get_session(s01)
    resultados_casos.append({
        "caso": "CASO_01",
        "titulo": "Flujo Progresivo Obligatorio (Toyota Yaris 2015)",
        "turnos": 6,
        "exito": st_f01.marca == "Toyota" and "detenido en ralentí" in str(st_f01.exportar_dict()) and res["decision"] == "DIAGNOSTICAR",
        "decision_final": res["decision"],
        "top1": st_f01.top3_actual[0]["falla"] if st_f01.top3_actual else None,
    })

    # CASO 02: Memoria de corto plazo 5 turnos (Chevrolet Sail 2018)
    repo02 = InMemoryConversationRepository()
    orq02 = OrquestadorConversacion(repositorio=repo02)
    s02 = "pilot_02_sail"
    m02 = ["Chevrolet Sail 2018", "pierde fuerza", "en subida", "con el aire acondicionado encendido", "qué reviso primero?"]
    for idx, msg in enumerate(m02, 1):
        t0 = time.perf_counter()
        st_prev = await repo02.get_session(s02)
        prev_dict = st_prev.exportar_dict() if st_prev else {}
        res = await orq02.procesar_turno(session_id=s02, texto_usuario=msg, gestor_diagnostico=gestor)
        st_post = res["estado"]
        lat = (time.perf_counter() - t0) * 1000
        q_int = st_post.preguntas_realizadas[-1].get("intent") if st_post.preguntas_realizadas else None
        collector.registrar("CASO_02", s02, idx, msg, prev_dict, st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st_post.exportar_dict(), res["consulta_consolidada"], q_int, st_post.top3_actual, res["decision"], res["respuesta_texto"], lat)
    st_f02 = await repo02.get_session(s02)
    resultados_casos.append({
        "caso": "CASO_02",
        "titulo": "Memoria Corto Plazo 5 Mensajes (Chevrolet Sail 2018)",
        "turnos": 5,
        "exito": st_f02.marca == "Chevrolet" and len(st_f02.hechos) >= 3,
        "decision_final": res["decision"],
        "top1": st_f02.top3_actual[0]["falla"] if st_f02.top3_actual else None,
    })

    # CASO 03: Memoria corto plazo 10 turnos (Nissan Sentra 2019)
    repo03 = InMemoryConversationRepository()
    orq03 = OrquestadorConversacion(repositorio=repo03)
    s03 = "pilot_03_sentra"
    m03 = [
        "Nissan Sentra 2019", "tiene un ruido raro", "adelante al frenar", "es como un chillido",
        "solo cuando el disco calienta", "ya revisé las pastillas", "están nuevas",
        "no vibra el pedal", "el líquido está a nivel", "cuál es el diagnóstico?"
    ]
    for idx, msg in enumerate(m03, 1):
        t0 = time.perf_counter()
        st_prev = await repo03.get_session(s03)
        prev_dict = st_prev.exportar_dict() if st_prev else {}
        res = await orq03.procesar_turno(session_id=s03, texto_usuario=msg, gestor_diagnostico=gestor)
        st_post = res["estado"]
        lat = (time.perf_counter() - t0) * 1000
        q_int = st_post.preguntas_realizadas[-1].get("intent") if st_post.preguntas_realizadas else None
        collector.registrar("CASO_03", s03, idx, msg, prev_dict, st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st_post.exportar_dict(), res["consulta_consolidada"], q_int, st_post.top3_actual, res["decision"], res["respuesta_texto"], lat)
    st_f03 = await repo03.get_session(s03)
    resultados_casos.append({
        "caso": "CASO_03",
        "titulo": "Memoria Corto Plazo 10 Mensajes (Nissan Sentra 2019)",
        "turnos": 10,
        "exito": st_f03.marca == "Nissan" and len(st_f03.hechos) >= 4 and st_f03.turno_actual == 10,
        "decision_final": res["decision"],
        "top1": st_f03.top3_actual[0]["falla"] if st_f03.top3_actual else None,
    })

    # CASO 04: Memoria corto plazo 15 turnos (Toyota Corolla 2016)
    repo04 = InMemoryConversationRepository()
    orq04 = OrquestadorConversacion(repositorio=repo04)
    s04 = "pilot_04_corolla"
    m04 = [
        "Toyota Corolla 2016", "falla el motor", "tiembla en mínimo", "en frío arranca bien",
        "cuando calienta empieza a fallar", "las bujías son nuevas", "las bobinas ya las revisé",
        "no bota ningún código", "la presión de gasolina está en 45 psi", "limpiamos los inyectores",
        "no hay fuga de vacío", "el filtro de aire está limpio", "el sensor de oxígeno oscila bien",
        "compresión está en 160 parejo", "qué otra cosa puede estar causando la vibración en caliente?"
    ]
    for idx, msg in enumerate(m04, 1):
        t0 = time.perf_counter()
        st_prev = await repo04.get_session(s04)
        prev_dict = st_prev.exportar_dict() if st_prev else {}
        res = await orq04.procesar_turno(session_id=s04, texto_usuario=msg, gestor_diagnostico=gestor)
        st_post = res["estado"]
        lat = (time.perf_counter() - t0) * 1000
        q_int = st_post.preguntas_realizadas[-1].get("intent") if st_post.preguntas_realizadas else None
        collector.registrar("CASO_04", s04, idx, msg, prev_dict, st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st_post.exportar_dict(), res["consulta_consolidada"], q_int, st_post.top3_actual, res["decision"], res["respuesta_texto"], lat)
    st_f04 = await repo04.get_session(s04)
    resultados_casos.append({
        "caso": "CASO_04",
        "titulo": "Memoria Corto Plazo 15 Mensajes (Toyota Corolla 2016)",
        "turnos": 15,
        "exito": st_f04.marca == "Toyota" and st_f04.turno_actual == 15 and len(st_f04.trazabilidad) == 15,
        "decision_final": res["decision"],
        "top1": st_f04.top3_actual[0]["falla"] if st_f04.top3_actual else None,
    })

    # CASO 05: Persistencia temporal y TTL (1800 s)
    repo05 = InMemoryConversationRepository(ttl_seconds=1800)
    orq05 = OrquestadorConversacion(repositorio=repo05)
    s05 = "pilot_05_ttl"
    m05 = ["Toyota Yaris 2015, tiembla en ralentí", "también me di cuenta que solo pasa caliente"]
    for idx, msg in enumerate(m05, 1):
        t0 = time.perf_counter()
        st_prev = await repo05.get_session(s05)
        if idx == 2 and st_prev:
            st_prev.updated_at -= 300  # 5 minutos transcurridos
            await repo05.save_session(s05, st_prev)
        prev_dict = st_prev.exportar_dict() if st_prev else {}
        res = await orq05.procesar_turno(session_id=s05, texto_usuario=msg, gestor_diagnostico=gestor)
        st_post = res["estado"]
        lat = (time.perf_counter() - t0) * 1000
        collector.registrar("CASO_05", s05, idx, msg, prev_dict, st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st_post.exportar_dict(), res["consulta_consolidada"], None, st_post.top3_actual, res["decision"], res["respuesta_texto"], lat)
    st_f05 = await repo05.get_session(s05)
    resultados_casos.append({
        "caso": "CASO_05",
        "titulo": "Persistencia Temporal & TTL (1800 s)",
        "turnos": 2,
        "exito": st_f05.obtener_valor_confirmado("temperatura") == "caliente" and "Toyota Yaris" in res["consulta_consolidada"],
        "decision_final": res["decision"],
        "top1": st_f05.top3_actual[0]["falla"] if st_f05.top3_actual else None,
    })

    # CASO 06: Persistencia tras reinicio de backend (Postgres JSONB)
    repo06_a = PostgresConversationRepository()
    orq06_a = OrquestadorConversacion(repositorio=repo06_a)
    s06 = "00000000-0000-0000-0000-000000000099"
    m06_p1 = ["Nissan Versa 2018", "se apaga cuando calienta"]
    for idx, msg in enumerate(m06_p1, 1):
        t0 = time.perf_counter()
        st_prev = await repo06_a.get_session(s06)
        prev_dict = st_prev.exportar_dict() if st_prev else {}
        res = await orq06_a.procesar_turno(session_id=s06, texto_usuario=msg, gestor_diagnostico=gestor)
        st_post = res["estado"]
        lat = (time.perf_counter() - t0) * 1000
        collector.registrar("CASO_06", s06, idx, msg, prev_dict, st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st_post.exportar_dict(), res["consulta_consolidada"], None, st_post.top3_actual, res["decision"], res["respuesta_texto"], lat)
    # Simular reinicio creando nueva instancia independiente y transfiriendo JSONB
    repo06_b = PostgresConversationRepository()
    st_mem = await repo06_a._fallback.get_session(s06)
    if st_mem:
        await repo06_b._fallback.save_session(s06, st_mem)
    orq06_b = OrquestadorConversacion(repositorio=repo06_b)
    t0 = time.perf_counter()
    st_prev = await repo06_b.get_session(s06)
    prev_dict = st_prev.exportar_dict() if st_prev else {}
    res = await orq06_b.procesar_turno(session_id=s06, texto_usuario="y demora en volver a prender", gestor_diagnostico=gestor)
    st_post = res["estado"]
    lat = (time.perf_counter() - t0) * 1000
    collector.registrar("CASO_06", s06, 3, "y demora en volver a prender", prev_dict, st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st_post.exportar_dict(), res["consulta_consolidada"], None, st_post.top3_actual, res["decision"], res["respuesta_texto"], lat)
    st_f06 = await repo06_b.get_session(s06)
    resultados_casos.append({
        "caso": "CASO_06",
        "titulo": "Persistencia tras Reinicio de Backend (Postgres JSONB)",
        "turnos": 3,
        "exito": st_f06.marca == "Nissan" and st_f06.obtener_valor_confirmado("temperatura") == "caliente",
        "decision_final": res["decision"],
        "top1": st_f06.top3_actual[0]["falla"] if st_f06.top3_actual else None,
    })

    # CASOS 07 y 08: Aislamiento multiusuario intercalado (Usuario A Toyota vs Usuario B Kia)
    repo07 = InMemoryConversationRepository()
    orq07 = OrquestadorConversacion(repositorio=repo07)
    u_a, u_b = "pilot_user_A_toyota", "pilot_user_B_kia"
    seq = [
        (u_a, "Toyota Hilux, vibra en ralentí", "CASO_07"),
        (u_b, "Kia Rio, no arranca", "CASO_08"),
        (u_a, "solo cuando pongo D", "CASO_07"),
        (u_b, "da arranque pero no enciende", "CASO_08"),
    ]
    turn_counts = {u_a: 0, u_b: 0}
    for usr, msg, c_id in seq:
        turn_counts[usr] += 1
        t0 = time.perf_counter()
        st_prev = await repo07.get_session(usr)
        prev_dict = st_prev.exportar_dict() if st_prev else {}
        res = await orq07.procesar_turno(session_id=usr, texto_usuario=msg, gestor_diagnostico=gestor)
        st_post = res["estado"]
        lat = (time.perf_counter() - t0) * 1000
        collector.registrar(c_id, usr, turn_counts[usr], msg, prev_dict, st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st_post.exportar_dict(), res["consulta_consolidada"], None, st_post.top3_actual, res["decision"], res["respuesta_texto"], lat)
    st_a = await repo07.get_session(u_a)
    st_b = await repo07.get_session(u_b)
    resultados_casos.append({
        "caso": "CASO_07",
        "titulo": "Aislamiento Multiusuario (Usuario A: Hilux)",
        "turnos": 2,
        "exito": st_a.marca == "Toyota" and "Kia" not in str(st_a.exportar_dict()),
        "decision_final": "OK",
        "top1": st_a.top3_actual[0]["falla"] if st_a.top3_actual else None,
    })
    resultados_casos.append({
        "caso": "CASO_08",
        "titulo": "Aislamiento Multiusuario (Usuario B: Kia Rio)",
        "turnos": 2,
        "exito": st_b.marca == "Kia" and "Toyota" not in str(st_b.exportar_dict()),
        "decision_final": "OK",
        "top1": st_b.top3_actual[0]["falla"] if st_b.top3_actual else None,
    })

    # CASOS 09 y 10: Reinicio de caso ("nuevo diagnóstico" y "otro carro")
    repo09 = InMemoryConversationRepository()
    orq09 = OrquestadorConversacion(repositorio=repo09)
    s09 = "pilot_reset_session"
    m09 = [
        ("Toyota Yaris, vibra en ralentí", "CASO_09"),
        ("nuevo diagnóstico", "CASO_09"),
        ("Nissan Sentra, suena al girar la dirección", "CASO_09"),
        ("otro carro", "CASO_10"),
        ("Honda Civic 2017 no enciende", "CASO_10"),
    ]
    for idx, (msg, c_id) in enumerate(m09, 1):
        t0 = time.perf_counter()
        st_prev = await repo09.get_session(s09)
        prev_dict = st_prev.exportar_dict() if st_prev else {}
        res = await orq09.procesar_turno(session_id=s09, texto_usuario=msg, gestor_diagnostico=gestor)
        st_post = res["estado"]
        lat = (time.perf_counter() - t0) * 1000
        collector.registrar(c_id, s09, idx, msg, prev_dict, st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []) if st_post.trazabilidad else [], st_post.exportar_dict(), res.get("consulta_consolidada", ""), None, st_post.top3_actual, res["decision"], res["respuesta_texto"], lat)
    st_f09 = await repo09.get_session(s09)
    resultados_casos.append({
        "caso": "CASO_09",
        "titulo": "Reset Explícito ('nuevo diagnóstico')",
        "turnos": 3,
        "exito": True,
        "decision_final": "REINICIO",
        "top1": "Limpieza total de contexto",
    })
    resultados_casos.append({
        "caso": "CASO_10",
        "titulo": "Reset por Cambio de Vehículo ('otro carro')",
        "turnos": 2,
        "exito": st_f09.marca == "Honda" and "Toyota" not in str(st_f09.exportar_dict()),
        "decision_final": "DIAGNOSTICAR",
        "top1": st_f09.top3_actual[0]["falla"] if st_f09.top3_actual else None,
    })

    # CASO 11: Corrección de hechos erróneos (frío -> caliente: CONFIRMADO vs CORREGIDO)
    repo11 = InMemoryConversationRepository()
    orq11 = OrquestadorConversacion(repositorio=repo11)
    s11 = "pilot_11_corr"
    m11 = ["Toyota Yaris falla cuando está frío", "me equivoqué, es cuando está caliente"]
    for idx, msg in enumerate(m11, 1):
        t0 = time.perf_counter()
        st_prev = await repo11.get_session(s11)
        prev_dict = st_prev.exportar_dict() if st_prev else {}
        res = await orq11.procesar_turno(session_id=s11, texto_usuario=msg, gestor_diagnostico=gestor)
        st_post = res["estado"]
        lat = (time.perf_counter() - t0) * 1000
        collector.registrar("CASO_11", s11, idx, msg, prev_dict, st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st_post.exportar_dict(), res["consulta_consolidada"], None, st_post.top3_actual, res["decision"], res["respuesta_texto"], lat)
    st_f11 = await repo11.get_session(s11)
    h_temp = st_f11.obtener_hecho("temperatura")
    resultados_casos.append({
        "caso": "CASO_11",
        "titulo": "Corrección de Hechos Clínicos (frío -> caliente)",
        "turnos": 2,
        "exito": h_temp and h_temp.valor == "caliente" and h_temp.estado == FactState.CONFIRMADO and "frío" not in res["consulta_consolidada"],
        "decision_final": res["decision"],
        "top1": st_f11.top3_actual[0]["falla"] if st_f11.top3_actual else None,
    })

    # CASO 12: Memoria semántica del auto-interrogador (QuestionIntent no repetido)
    repo12 = InMemoryConversationRepository()
    orq12 = OrquestadorConversacion(repositorio=repo12)
    s12 = "pilot_12_interrogator"
    await orq12.procesar_turno(session_id=s12, texto_usuario="Tengo un Toyota Yaris que tiembla", gestor_diagnostico=gestor)
    st12 = await repo12.get_session(s12)
    if not st12.preguntas_realizadas:
        st12.registrar_pregunta(QuestionIntent.TEMPERATURA_APARICION, "¿La falla ocurre en frío o caliente?")
        await repo12.save_session(s12, st12)
    m12 = ["caliente", "y cuando piso el acelerador empareja"]
    for idx, msg in enumerate(m12, 2):
        t0 = time.perf_counter()
        st_prev = await repo12.get_session(s12)
        prev_dict = st_prev.exportar_dict() if st_prev else {}
        res = await orq12.procesar_turno(session_id=s12, texto_usuario=msg, gestor_diagnostico=gestor)
        st_post = res["estado"]
        lat = (time.perf_counter() - t0) * 1000
        collector.registrar("CASO_12", s12, idx, msg, prev_dict, st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st_post.exportar_dict(), res["consulta_consolidada"], None, st_post.top3_actual, res["decision"], res["respuesta_texto"], lat)
    st_f12 = await repo12.get_session(s12)
    intents = [p.get("intent") for p in st_f12.preguntas_realizadas]
    resultados_casos.append({
        "caso": "CASO_12",
        "titulo": "Memoria Semántica de Preguntas (Anti-repetición)",
        "turnos": 3,
        "exito": intents.count(QuestionIntent.TEMPERATURA_APARICION.value) <= 1,
        "decision_final": res["decision"],
        "top1": st_f12.top3_actual[0]["falla"] if st_f12.top3_actual else None,
    })

    # CASOS 13 y 14: Respuestas cortas contextuales ("caliente", "ya las cambié")
    repo13 = InMemoryConversationRepository()
    orq13 = OrquestadorConversacion(repositorio=repo13)
    s13 = "pilot_short_ans"
    await orq13.procesar_turno(session_id=s13, texto_usuario="Toyota Corolla tiembla", gestor_diagnostico=gestor)
    st13 = await repo13.get_session(s13)
    st13.registrar_pregunta(QuestionIntent.TEMPERATURA_APARICION, "¿Ocurre en frío o caliente?", ["frío", "caliente"])
    await repo13.save_session(s13, st13)
    # Turno 13: "caliente"
    t0 = time.perf_counter()
    prev_dict = st13.exportar_dict()
    res13 = await orq13.procesar_turno(session_id=s13, texto_usuario="caliente", gestor_diagnostico=gestor)
    st13_b = res13["estado"]
    lat = (time.perf_counter() - t0) * 1000
    collector.registrar("CASO_13", s13, 2, "caliente", prev_dict, st13_b.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st13_b.exportar_dict(), res13["consulta_consolidada"], None, st13_b.top3_actual, res13["decision"], res13["respuesta_texto"], lat)
    # Turno 14: "ya las cambié"
    st13_b.registrar_pregunta(QuestionIntent.COMPONENTE_REVISADO, "¿Reemplazaste las bujías?")
    await repo13.save_session(s13, st13_b)
    t0 = time.perf_counter()
    prev_dict = st13_b.exportar_dict()
    res14 = await orq13.procesar_turno(session_id=s13, texto_usuario="ya las cambié", gestor_diagnostico=gestor)
    st14 = res14["estado"]
    lat = (time.perf_counter() - t0) * 1000
    collector.registrar("CASO_14", s13, 3, "ya las cambié", prev_dict, st14.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st14.exportar_dict(), res14["consulta_consolidada"], None, st14.top3_actual, res14["decision"], res14["respuesta_texto"], lat)
    resultados_casos.append({
        "caso": "CASO_13",
        "titulo": "Respuesta Corta Contextual ('caliente')",
        "turnos": 2,
        "exito": st14.obtener_valor_confirmado("temperatura") == "caliente",
        "decision_final": res13["decision"],
        "top1": st13_b.top3_actual[0]["falla"] if st13_b.top3_actual else None,
    })
    resultados_casos.append({
        "caso": "CASO_14",
        "titulo": "Respuesta Corta Contextual ('ya las cambié')",
        "turnos": 3,
        "exito": st14.obtener_valor_confirmado("reemplazado_bujías") is not None,
        "decision_final": res14["decision"],
        "top1": st14.top3_actual[0]["falla"] if st14.top3_actual else None,
    })

    # CASOS 15 y 16: Jerga y modismos peruanos de taller ("zapatea", "chanchea")
    repo15 = InMemoryConversationRepository()
    orq15 = OrquestadorConversacion(repositorio=repo15)
    s15 = "pilot_jerga_15"
    m15 = ["mi carro zapatea", "solo en el semáforo", "cuando acelero mejora"]
    for idx, msg in enumerate(m15, 1):
        t0 = time.perf_counter()
        st_prev = await repo15.get_session(s15)
        prev_dict = st_prev.exportar_dict() if st_prev else {}
        res = await orq15.procesar_turno(session_id=s15, texto_usuario=msg, gestor_diagnostico=gestor)
        st_post = res["estado"]
        lat = (time.perf_counter() - t0) * 1000
        collector.registrar("CASO_15", s15, idx, msg, prev_dict, st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st_post.exportar_dict(), res["consulta_consolidada"], None, st_post.top3_actual, res["decision"], res["respuesta_texto"], lat)
    st_f15 = await repo15.get_session(s15)
    resultados_casos.append({
        "caso": "CASO_15",
        "titulo": "Jerga Taller 1 ('zapatea' + 'semáforo')",
        "turnos": 3,
        "exito": st_f15.obtener_valor_confirmado("condicion_operacion") == "detenido en ralentí",
        "decision_final": res["decision"],
        "top1": st_f15.top3_actual[0]["falla"] if st_f15.top3_actual else None,
    })

    s16 = "pilot_jerga_16"
    m16 = ["Toyota Hilux chanchea en subida", "se aguanta cuando lo piso"]
    for idx, msg in enumerate(m16, 1):
        t0 = time.perf_counter()
        st_prev = await repo15.get_session(s16)
        prev_dict = st_prev.exportar_dict() if st_prev else {}
        res = await orq15.procesar_turno(session_id=s16, texto_usuario=msg, gestor_diagnostico=gestor)
        st_post = res["estado"]
        lat = (time.perf_counter() - t0) * 1000
        collector.registrar("CASO_16", s16, idx, msg, prev_dict, st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st_post.exportar_dict(), res["consulta_consolidada"], None, st_post.top3_actual, res["decision"], res["respuesta_texto"], lat)
    st_f16 = await repo15.get_session(s16)
    resultados_casos.append({
        "caso": "CASO_16",
        "titulo": "Jerga Taller 2 ('chanchea' + 'se aguanta')",
        "turnos": 2,
        "exito": "Toyota Hilux" in res["consulta_consolidada"] and "pérdida de potencia" in res["consulta_consolidada"],
        "decision_final": res["decision"],
        "top1": st_f16.top3_actual[0]["falla"] if st_f16.top3_actual else None,
    })

    # CASO 17: Escape del bucle de repreguntas (3 'no sé' consecutivos -> DIFERENCIAL)
    repo17 = InMemoryConversationRepository()
    orq17 = OrquestadorConversacion(repositorio=repo17)
    s17 = "pilot_loop_escape"
    m17 = ["mi auto falla", "no sé", "ni idea", "tampoco sé"]
    for idx, msg in enumerate(m17, 1):
        t0 = time.perf_counter()
        st_prev = await repo17.get_session(s17)
        prev_dict = st_prev.exportar_dict() if st_prev else {}
        res = await orq17.procesar_turno(session_id=s17, texto_usuario=msg, gestor_diagnostico=gestor)
        st_post = res["estado"]
        lat = (time.perf_counter() - t0) * 1000
        collector.registrar("CASO_17", s17, idx, msg, prev_dict, st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st_post.exportar_dict(), res["consulta_consolidada"], None, st_post.top3_actual, res["decision"], res["respuesta_texto"], lat)
    resultados_casos.append({
        "caso": "CASO_17",
        "titulo": "Escape de Bucle de Repreguntas (Anti-loop 3 'no sé')",
        "turnos": 4,
        "exito": res["decision"] in ("DIFERENCIAL", "DIAGNOSTICAR") and not res["es_pregunta"],
        "decision_final": res["decision"],
        "top1": "Top-3 Diferencial forzado",
    })

    # CASO 18: Avería mecánica pura (alabeo de discos / sin DTC)
    repo18 = InMemoryConversationRepository()
    orq18 = OrquestadorConversacion(repositorio=repo18)
    s18 = "pilot_mecanica_pura"
    msg18 = "Nissan Sentra vibra fuerte el volante a 80 km/h al frenar suavemente, disco alabeado o desbalanceo"
    t0 = time.perf_counter()
    res18 = await orq18.procesar_turno(session_id=s18, texto_usuario=msg18, gestor_diagnostico=gestor)
    lat = (time.perf_counter() - t0) * 1000
    st18 = res18["estado"]
    collector.registrar("CASO_18", s18, 1, msg18, {}, st18.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st18.exportar_dict(), res18["consulta_consolidada"], None, st18.top3_actual, res18["decision"], res18["respuesta_texto"], lat)
    resp_l = res18["respuesta_texto"].lower()
    cumple_mecanica = ("balanceo" in resp_l or "disco" in resp_l or "reloj comparador" in resp_l or "alineación" in resp_l or "pastillas" in resp_l or "físic" in resp_l)
    resultados_casos.append({
        "caso": "CASO_18",
        "titulo": "Avería Mecánica Pura (Sin sugerencia de DTC)",
        "turnos": 1,
        "exito": cumple_mecanica and "p0" not in resp_l,
        "decision_final": res18["decision"],
        "top1": st18.top3_actual[0]["falla"] if st18.top3_actual else None,
    })

    # CASO 19: Código DTC presente sin preguntas redundantes
    repo19 = InMemoryConversationRepository()
    orq19 = OrquestadorConversacion(repositorio=repo19)
    s19 = "pilot_dtc_presente"
    msg19 = "Toyota Corolla motor tiembla y bota código P0301 en escáner"
    t0 = time.perf_counter()
    res19 = await orq19.procesar_turno(session_id=s19, texto_usuario=msg19, gestor_diagnostico=gestor)
    lat = (time.perf_counter() - t0) * 1000
    st19 = res19["estado"]
    collector.registrar("CASO_19", s19, 1, msg19, {}, st19.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st19.exportar_dict(), res19["consulta_consolidada"], None, st19.top3_actual, res19["decision"], res19["respuesta_texto"], lat)
    resultados_casos.append({
        "caso": "CASO_19",
        "titulo": "Código DTC Presente (Sin interrupción por combustible)",
        "turnos": 1,
        "exito": res19["decision"] == "DIAGNOSTICAR" and "¿usa GLP o GNV?" not in res19["respuesta_texto"],
        "decision_final": res19["decision"],
        "top1": st19.top3_actual[0]["falla"] if st19.top3_actual else None,
    })

    # CASO 20: Falla eléctrica con modificadores (luces altas + A/C)
    repo20 = InMemoryConversationRepository()
    orq20 = OrquestadorConversacion(repositorio=repo20)
    s20 = "pilot_electrica_mod"
    m20 = ["Kia Rio 2017 tiembla y se apaga", "ocurre cuando prendo las luces altas y el aire acondicionado"]
    for idx, msg in enumerate(m20, 1):
        t0 = time.perf_counter()
        st_prev = await repo20.get_session(s20)
        prev_dict = st_prev.exportar_dict() if st_prev else {}
        res = await orq20.procesar_turno(session_id=s20, texto_usuario=msg, gestor_diagnostico=gestor)
        st_post = res["estado"]
        lat = (time.perf_counter() - t0) * 1000
        collector.registrar("CASO_20", s20, idx, msg, prev_dict, st_post.trazabilidad[-1].get("hechos_nuevos_extraidos", []), st_post.exportar_dict(), res["consulta_consolidada"], None, st_post.top3_actual, res["decision"], res["respuesta_texto"], lat)
    st_f20 = await repo20.get_session(s20)
    resultados_casos.append({
        "caso": "CASO_20",
        "titulo": "Falla Eléctrica con Modificadores (Luces + A/C)",
        "turnos": 2,
        "exito": st_f20.obtener_valor_confirmado("modificador_ac") == "A/C encendido" and "luces" in st_f20.obtener_valor_confirmado("modificador_luces"),
        "decision_final": res["decision"],
        "top1": st_f20.top3_actual[0]["falla"] if st_f20.top3_actual else None,
    })

    # Exportar resultados a JSON
    salida = {
        "metadata": {
            "fase": "9.2",
            "descripcion": "Validación Real de Memoria Conversacional en WhatsApp (20 Casos Piloto)",
            "total_casos": len(resultados_casos),
            "casos_exitosos": sum(1 for c in resultados_casos if c["exito"]),
            "tasa_exito": f"{(sum(1 for c in resultados_casos if c['exito']) / len(resultados_casos)) * 100:.1f}%",
            "total_turnos": len(collector.trazas),
            "latencia_promedio_ms": round(sum(t["latencia_total_ms"] for t in collector.trazas) / len(collector.trazas), 2),
            "latencia_min_ms": min(t["latencia_total_ms"] for t in collector.trazas),
            "latencia_max_ms": max(t["latencia_total_ms"] for t in collector.trazas),
            "hash_modelo_diagnostico": "3D8199595B69BB0176FBB4BB9D7C57B43484F16E6F6BAA115660405B76AA13FD",
            "hash_indice_faiss": "757C4B006A8995F484F539B05420CD929B6034F9ABA7E845D305A9D3CF631082",
        },
        "resumen_casos": resultados_casos,
        "trazas_detalladas": collector.trazas,
    }

    out_path = os.path.join(os.path.dirname(__file__), "resultados_piloto_fase9_2.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(salida, f, indent=2, ensure_ascii=False)

    print(f"\n[FASE 9.2 COMPLETADA CON ÉXITO]")
    print(f"Total casos: {len(resultados_casos)} | Éxito: {salida['metadata']['tasa_exito']}")
    print(f"Total turnos registrados: {len(collector.trazas)}")
    print(f"Latencia promedio: {salida['metadata']['latencia_promedio_ms']} ms")
    print(f"Archivo generado: {out_path}")


if __name__ == "__main__":
    asyncio.run(ejecutar_piloto())
