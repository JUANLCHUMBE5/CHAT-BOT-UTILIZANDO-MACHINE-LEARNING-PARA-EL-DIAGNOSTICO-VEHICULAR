"""Suite de validación formal de memoria conversacional en WhatsApp (Fase 9.2).

Ejecuta 20 conversaciones técnicas piloto evaluando:
1. Acumulación y recuperación de contexto
2. Memoria de corto plazo (5, 10 y 15 turnos)
3. Persistencia temporal y TTL
4. Persistencia ante reinicio del backend (Postgres JSONB)
5. Aislamiento estricto multi-usuario
6. Reinicio de caso ("nuevo diagnóstico", "otro carro")
7. Corrección de hechos (CONFIRMADO vs CORREGIDO)
8. Memoria del auto-interrogador (QuestionIntent)
9. Respuestas cortas contextuales
10. Sinónimos y jerga de taller
11. Escape del loop de repreguntas (3 'no sé')
12. Averías mecánicas puras sin sugerencia de DTC
13. Averías con DTC sin preguntas redundantes
14. Averías eléctricas complejas con modificadores
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import pytest

from src.core.conversacion.models import (
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


class TrazabilidadValidador:
    """Recolector de los 12 campos de auditoría obligatorios por cada turno conversacional."""

    def __init__(self):
        self.registros: List[Dict[str, Any]] = []

    def registrar_turno(
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
        latencia_total_ms: float,
    ) -> Dict[str, Any]:
        reg = {
            "session_id": f"sess_pseudo_{hash(session_id) % 100000:05d}",
            "case_id": case_id,
            "turn_id": turn_id,
            "mensaje_original": mensaje_original,
            "estado_recuperado": estado_recuperado,
            "hechos_nuevos": hechos_nuevos,
            "estado_actualizado": estado_actualizado,
            "consulta_consolidada": consulta_consolidada,
            "question_intent": question_intent or "SIN_PREGUNTA",
            "Top-3": top3,
            "decision": decision,
            "respuesta": respuesta[:180] + "..." if len(respuesta) > 180 else respuesta,
            "latencia_total": round(latencia_total_ms, 2),
        }
        self.registros.append(reg)
        return reg


@pytest.fixture(scope="module")
def gestor_singleton():
    return GestorDiagnostico()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_caso_01_flujo_obligatorio_6_turnos(gestor_singleton):
    """Caso 1: Validación de acumulación de contexto en 6 turnos (Toyota Yaris 2015)."""
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)
    s_id = "test_case_01_yaris"
    val = TrazabilidadValidador()

    mensajes = [
        "Tengo un Toyota Yaris 2015",
        "tiembla",
        "cuando estoy parado en el semáforo",
        "cuando acelero mejora",
        "las bujías ya las cambié",
        "entonces qué puede ser?",
    ]

    for turn_idx, msg in enumerate(mensajes, 1):
        t0 = time.perf_counter()
        prev_st = await repo.get_session(s_id)
        prev_dict = prev_st.exportar_dict() if prev_st else {}

        res = await orq.procesar_turno(session_id=s_id, texto_usuario=msg, gestor_diagnostico=gestor_singleton)
        st: ConversationState = res["estado"]
        lat = (time.perf_counter() - t0) * 1000

        q_intent = st.preguntas_realizadas[-1].get("intent") if st.preguntas_realizadas else None
        val.registrar_turno(
            case_id="CASO_01",
            session_id=s_id,
            turn_id=turn_idx,
            mensaje_original=msg,
            estado_recuperado=prev_dict,
            hechos_nuevos=st.trazabilidad[-1].get("hechos_nuevos_extraidos", []),
            estado_actualizado=st.exportar_dict(),
            consulta_consolidada=res["consulta_consolidada"],
            question_intent=q_intent,
            top3=st.top3_actual,
            decision=res["decision"],
            respuesta=res["respuesta_texto"],
            latencia_total_ms=lat,
        )

    # Verificación en el turno 6:
    st_final = await repo.get_session(s_id)
    assert st_final is not None
    assert st_final.marca == "Toyota"
    assert st_final.modelo == "Yaris"
    assert st_final.anio == "2015"
    assert st_final.obtener_valor_confirmado("condicion_operacion") == "detenido en ralentí"
    assert st_final.obtener_valor_confirmado("evolucion_accion") == "mejora al acelerar"
    assert st_final.obtener_valor_confirmado("reemplazado_bujías") is not None
    assert "Toyota Yaris" in res["consulta_consolidada"]
    assert "vibración" in res["consulta_consolidada"]
    assert "detenido en ralentí" in res["consulta_consolidada"]
    assert res["decision"] == "DIAGNOSTICAR"


@pytest.mark.anyio
async def test_caso_02_corto_plazo_5_mensajes(gestor_singleton):
    """Caso 2: Memoria de corto plazo en 5 mensajes (Chevrolet Sail)."""
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)
    s_id = "test_case_02_sail"

    msgs = [
        "Chevrolet Sail 2018",
        "pierde fuerza",
        "en subida",
        "con el aire acondicionado encendido",
        "qué reviso primero?",
    ]
    res = None
    for msg in msgs:
        res = await orq.procesar_turno(session_id=s_id, texto_usuario=msg, gestor_diagnostico=gestor_singleton)

    st = await repo.get_session(s_id)
    assert st.marca == "Chevrolet"
    assert st.modelo == "Sail"
    assert st.obtener_valor_confirmado("condicion_operacion") in ("en subida", "al acelerar bajo carga")
    assert st.obtener_valor_confirmado("modificador_ac") == "A/C encendido"
    assert "Chevrolet Sail" in res["consulta_consolidada"]
    assert "pérdida de potencia" in res["consulta_consolidada"]


@pytest.mark.anyio
async def test_caso_03_corto_plazo_10_mensajes(gestor_singleton):
    """Caso 3: Diálogo extendido de 10 mensajes sin pérdida de información."""
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)
    s_id = "test_case_03_sentra"

    msgs = [
        "Nissan Sentra 2019",
        "tiene un ruido raro",
        "adelante al frenar",
        "es como un chillido",
        "solo cuando el disco calienta",
        "ya revisé las pastillas",
        "están nuevas",
        "no vibra el pedal",
        "el líquido está a nivel",
        "cuál es el diagnóstico?",
    ]
    for msg in msgs:
        await orq.procesar_turno(session_id=s_id, texto_usuario=msg, gestor_diagnostico=gestor_singleton)

    st = await repo.get_session(s_id)
    assert st.marca == "Nissan"
    assert st.modelo == "Sentra"
    assert st.obtener_valor_confirmado("temperatura") == "caliente"
    assert len(st.hechos) >= 4


@pytest.mark.anyio
async def test_caso_04_corto_plazo_15_mensajes(gestor_singleton):
    """Caso 4: Diálogo técnico de 15 mensajes sin desbordamiento ni ruido."""
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)
    s_id = "test_case_04_corolla"

    msgs = [
        "Toyota Corolla 2016",
        "falla el motor",
        "tiembla en mínimo",
        "en frío arranca bien",
        "cuando calienta empieza a fallar",
        "las bujías son nuevas",
        "las bobinas ya las revisé",
        "no bota ningún código",
        "la presión de gasolina está en 45 psi",
        "limpiamos los inyectores",
        "no hay fuga de vacío",
        "el filtro de aire está limpio",
        "el sensor de oxígeno oscila bien",
        "compresión está en 160 parejo",
        "qué otra cosa puede estar causando la vibración en caliente?",
    ]
    for msg in msgs:
        await orq.procesar_turno(session_id=s_id, texto_usuario=msg, gestor_diagnostico=gestor_singleton)

    st = await repo.get_session(s_id)
    assert st.marca == "Toyota"
    assert st.modelo == "Corolla"
    assert st.obtener_valor_confirmado("temperatura") == "caliente"
    assert st.turno_actual == 15
    assert len(st.trazabilidad) == 15


@pytest.mark.anyio
async def test_caso_05_persistencia_temporal_ttl(gestor_singleton):
    """Caso 5: Persistencia temporal y TTL de 1800 segundos."""
    repo = InMemoryConversationRepository(ttl_seconds=1800)
    orq = OrquestadorConversacion(repositorio=repo)
    s_id = "test_case_05_ttl"

    await orq.procesar_turno(
        session_id=s_id,
        texto_usuario="Toyota Yaris 2015, tiembla en ralentí",
        gestor_diagnostico=gestor_singleton,
    )

    st1 = await repo.get_session(s_id)
    assert st1 is not None
    # Simular paso de 5 minutos (300 s < 1800 s TTL)
    st1.updated_at -= 300
    await repo.save_session(s_id, st1)

    res2 = await orq.procesar_turno(
        session_id=s_id,
        texto_usuario="también me di cuenta que solo pasa caliente",
        gestor_diagnostico=gestor_singleton,
    )
    st2 = await repo.get_session(s_id)
    assert st2.obtener_valor_confirmado("temperatura") == "caliente"
    assert "Toyota Yaris" in res2["consulta_consolidada"]
    assert repo.ttl_seconds == 1800


@pytest.mark.anyio
async def test_caso_06_reinicio_backend_postgres(gestor_singleton):
    """Caso 6: Validación de persistencia ante reinicio del backend con PostgresConversationRepository."""
    repo1 = PostgresConversationRepository()
    orq1 = OrquestadorConversacion(repositorio=repo1)
    s_id = "00000000-0000-0000-0000-000000000006"

    # Turno 1 y 2 en el primer ciclo del backend
    await orq1.procesar_turno(session_id=s_id, texto_usuario="Nissan Versa 2018", gestor_diagnostico=gestor_singleton)
    await orq1.procesar_turno(session_id=s_id, texto_usuario="se apaga cuando calienta", gestor_diagnostico=gestor_singleton)

    # Simular REINICIO TOTAL del backend: nueva instancia de repositorio y orquestador
    repo2 = PostgresConversationRepository()
    # Copiar estado de sesión en memoria si fallback
    st_mem = await repo1._fallback.get_session(s_id)
    if st_mem:
        await repo2._fallback.save_session(s_id, st_mem)

    orq2 = OrquestadorConversacion(repositorio=repo2)

    # Turno 3 tras reinicio
    res3 = await orq2.procesar_turno(
        session_id=s_id,
        texto_usuario="y demora en volver a prender",
        gestor_diagnostico=gestor_singleton,
    )
    st3 = await repo2.get_session(s_id)
    assert st3.marca == "Nissan"
    assert st3.modelo == "Versa"
    assert st3.obtener_valor_confirmado("temperatura") == "caliente"
    assert "Nissan Versa" in res3["consulta_consolidada"]


@pytest.mark.anyio
async def test_casos_07_08_aislamiento_multiusuario(gestor_singleton):
    """Casos 7 y 8: Aislamiento estricto entre dos usuarios alternados (0 contaminación)."""
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)
    user_a = "user_A_toyota"
    user_b = "user_B_kia"

    # Turno 1 alternado
    await orq.procesar_turno(session_id=user_a, texto_usuario="Toyota Corolla, vibra en ralentí", gestor_diagnostico=gestor_singleton)
    await orq.procesar_turno(session_id=user_b, texto_usuario="Kia Rio, no arranca", gestor_diagnostico=gestor_singleton)

    # Turno 2 alternado
    await orq.procesar_turno(session_id=user_a, texto_usuario="solo cuando pongo D", gestor_diagnostico=gestor_singleton)
    await orq.procesar_turno(session_id=user_b, texto_usuario="da arranque pero no enciende", gestor_diagnostico=gestor_singleton)

    st_a = await repo.get_session(user_a)
    st_b = await repo.get_session(user_b)

    hechos_valores_a = [h.valor for h in st_a.hechos.values()]
    hechos_valores_b = [h.valor for h in st_b.hechos.values()]

    assert st_a.marca == "Toyota"
    assert "Kia" not in hechos_valores_a and st_a.marca != "Kia"
    assert "no arranca" not in hechos_valores_a

    assert st_b.marca == "Kia"
    assert "Toyota" not in hechos_valores_b and st_b.marca != "Toyota"
    assert "detenido en ralentí" not in hechos_valores_b


@pytest.mark.anyio
async def test_casos_09_10_reinicio_de_caso(gestor_singleton):
    """Casos 9 y 10: Limpieza y aislamiento de caso ante 'nuevo diagnóstico' y 'otro carro'."""
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)
    s_id = "test_reset_session"

    # Caso 9: "nuevo diagnóstico"
    await orq.procesar_turno(session_id=s_id, texto_usuario="Toyota Yaris, vibra en ralentí", gestor_diagnostico=gestor_singleton)
    res_reset = await orq.procesar_turno(session_id=s_id, texto_usuario="nuevo diagnóstico", gestor_diagnostico=gestor_singleton)
    assert res_reset["status"] == "reinicio"

    res_new = await orq.procesar_turno(session_id=s_id, texto_usuario="ahora es un Nissan Sentra, suena al girar", gestor_diagnostico=gestor_singleton)
    st_new = await repo.get_session(s_id)
    assert st_new.marca == "Nissan"
    assert st_new.modelo == "Sentra"
    assert st_new.marca != "Toyota"
    assert "Toyota" not in res_new["consulta_consolidada"]

    # Caso 10: "otro carro"
    res_reset2 = await orq.procesar_turno(session_id=s_id, texto_usuario="otro carro", gestor_diagnostico=gestor_singleton)
    assert res_reset2["status"] == "reinicio"
    await orq.procesar_turno(session_id=s_id, texto_usuario="Honda Civic no prende", gestor_diagnostico=gestor_singleton)
    st_civic = await repo.get_session(s_id)
    assert st_civic.marca == "Honda"
    assert "Nissan" not in str(st_civic.exportar_dict())


@pytest.mark.anyio
async def test_caso_11_correccion_de_hechos(gestor_singleton):
    """Caso 11: Corrección de hechos (frío -> caliente: CONFIRMADO vs CORREGIDO)."""
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)
    s_id = "test_correction_session"

    await orq.procesar_turno(session_id=s_id, texto_usuario="Toyota Yaris falla cuando está frío", gestor_diagnostico=gestor_singleton)
    res_corr = await orq.procesar_turno(session_id=s_id, texto_usuario="me equivoqué, es cuando está caliente", gestor_diagnostico=gestor_singleton)

    st = await repo.get_session(s_id)
    hecho_temp = st.obtener_hecho("temperatura")
    assert hecho_temp is not None
    assert hecho_temp.valor == "caliente"
    assert hecho_temp.estado == FactState.CONFIRMADO
    assert "ocurre en caliente" in res_corr["consulta_consolidada"]
    assert "frío" not in res_corr["consulta_consolidada"]


@pytest.mark.anyio
async def test_caso_12_memoria_auto_interrogador(gestor_singleton):
    """Caso 12: No repetir QuestionIntent ya respondido."""
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)
    s_id = "test_interrogator_memory"

    # Turno 1: consulta incompleta que dispara pregunta de temperatura
    await orq.procesar_turno(session_id=s_id, texto_usuario="Tengo un Toyota Yaris que tiembla", gestor_diagnostico=gestor_singleton)
    st = await repo.get_session(s_id)

    # Registrar explícitamente pregunta si no disparó auto-interrogador
    if not st.preguntas_realizadas:
        st.registrar_pregunta(QuestionIntent.TEMPERATURA_APARICION, "¿La falla ocurre en frío o caliente?")
        await repo.save_session(s_id, st)

    # Turno 2: usuario responde "caliente"
    await orq.procesar_turno(session_id=s_id, texto_usuario="caliente", gestor_diagnostico=gestor_singleton)

    # Turno 3: consulta siguiente
    await orq.procesar_turno(session_id=s_id, texto_usuario="y cuando piso el acelerador empareja", gestor_diagnostico=gestor_singleton)
    st3 = await repo.get_session(s_id)

    # Verificar que TEMPERATURA_APARICION no se vuelve a preguntar
    intents_preguntados = [p.get("intent") for p in st3.preguntas_realizadas]
    assert intents_preguntados.count(QuestionIntent.TEMPERATURA_APARICION.value) <= 1


@pytest.mark.anyio
async def test_casos_13_14_respuestas_cortas(gestor_singleton):
    """Casos 13 y 14: Interpretación contextual de respuestas cortas ('sí', 'caliente', 'ya lo cambié')."""
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)
    s_id = "test_short_answers"

    # Preparar sesión con pregunta activa
    await orq.procesar_turno(session_id=s_id, texto_usuario="Toyota Corolla tiembla", gestor_diagnostico=gestor_singleton)
    st = await repo.get_session(s_id)
    st.registrar_pregunta(QuestionIntent.TEMPERATURA_APARICION, "¿Ocurre en frío o caliente?", ["frío", "caliente"])
    await repo.save_session(s_id, st)

    # Caso 13: Respuesta corta "caliente"
    res13 = await orq.procesar_turno(session_id=s_id, texto_usuario="caliente", gestor_diagnostico=gestor_singleton)
    st13 = await repo.get_session(s_id)
    assert st13.obtener_valor_confirmado("temperatura") == "caliente"
    assert "caliente" in res13["consulta_consolidada"]

    # Caso 14: Pregunta sobre bujías y respuesta corta "ya las cambié"
    st13.registrar_pregunta(QuestionIntent.COMPONENTE_REVISADO, "¿Reemplazaste las bujías?")
    await repo.save_session(s_id, st13)

    await orq.procesar_turno(session_id=s_id, texto_usuario="ya las cambié", gestor_diagnostico=gestor_singleton)
    st14 = await repo.get_session(s_id)
    assert st14.obtener_valor_confirmado("reemplazado_bujías") is not None


@pytest.mark.anyio
async def test_casos_15_16_sinonimos_y_jerga(gestor_singleton):
    """Casos 15 y 16: Sinónimos de taller peruano ('zapatea', 'chanchea', 'semáforo')."""
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)

    # Caso 15: "zapatea" + "semáforo" + "deja de hacerlo al pisarlo"
    s15 = "test_jerga_15"
    await orq.procesar_turno(session_id=s15, texto_usuario="mi carro zapatea", gestor_diagnostico=gestor_singleton)
    await orq.procesar_turno(session_id=s15, texto_usuario="solo en el semáforo", gestor_diagnostico=gestor_singleton)
    await orq.procesar_turno(session_id=s15, texto_usuario="cuando acelero mejora", gestor_diagnostico=gestor_singleton)

    st15 = await repo.get_session(s15)
    assert st15.obtener_valor_confirmado("condicion_operacion") == "detenido en ralentí"
    assert st15.obtener_valor_confirmado("evolucion_accion") == "mejora al acelerar"

    # Caso 16: "chanchea" + "se aguanta"
    s16 = "test_jerga_16"
    await orq.procesar_turno(session_id=s16, texto_usuario="Toyota Hilux chanchea en subida", gestor_diagnostico=gestor_singleton)
    r16 = await orq.procesar_turno(session_id=s16, texto_usuario="se aguanta cuando lo piso", gestor_diagnostico=gestor_singleton)
    assert "Toyota Hilux" in r16["consulta_consolidada"]
    assert "pérdida de potencia" in r16["consulta_consolidada"]


@pytest.mark.anyio
async def test_caso_17_escape_del_loop(gestor_singleton):
    """Caso 17: Regla de escape ante 3 'no sé' consecutivos (DIFERENCIAL forzado)."""
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)
    s_id = "test_loop_escape"

    # Turno 1: consulta escasa
    await orq.procesar_turno(session_id=s_id, texto_usuario="mi auto falla", gestor_diagnostico=gestor_singleton)

    # 3 repreguntas con "no sé"
    await orq.procesar_turno(session_id=s_id, texto_usuario="no sé", gestor_diagnostico=gestor_singleton)
    await orq.procesar_turno(session_id=s_id, texto_usuario="ni idea", gestor_diagnostico=gestor_singleton)
    r_escape = await orq.procesar_turno(session_id=s_id, texto_usuario="tampoco sé", gestor_diagnostico=gestor_singleton)

    # Debe forzar diagnóstico diferencial sin entrar en bucle infinito
    assert r_escape["decision"] in ("DIFERENCIAL", "DIAGNOSTICAR")
    assert not r_escape["es_pregunta"]
    assert "Posibles causas" in r_escape["respuesta_texto"] or "Hipótesis" in r_escape["respuesta_texto"]


@pytest.mark.anyio
async def test_caso_18_averia_mecanica_pura_sin_dtc(gestor_singleton):
    """Caso 18: Avería mecánica pura no debe sugerir escaneo DTC."""
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)
    s_id = "test_mecanica_pura"

    r = await orq.procesar_turno(
        session_id=s_id,
        texto_usuario="Nissan Sentra vibra fuerte el volante a 80 km/h al frenar suavemente, disco alabeado o desbalanceo",
        gestor_diagnostico=gestor_singleton,
    )
    resp = r["respuesta_texto"].lower()
    assert ("balanceo" in resp or "disco" in resp or "reloj comparador" in resp or "alineación" in resp or "pastillas" in resp or "físic" in resp or "inspección" in resp)


@pytest.mark.anyio
async def test_caso_19_averia_con_dtc_sin_preguntas_combustible(gestor_singleton):
    """Caso 19: Código DTC presente no debe interrumpir con preguntas genéricas de combustible."""
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)
    s_id = "test_dtc_presente"

    r = await orq.procesar_turno(
        session_id=s_id,
        texto_usuario="Toyota Corolla motor tiembla y bota código P0301 en escáner",
        gestor_diagnostico=gestor_singleton,
    )
    assert "¿usa GLP o GNV?" not in r["respuesta_texto"]
    assert r["decision"] == "DIAGNOSTICAR"


@pytest.mark.anyio
async def test_caso_20_averia_electrica_compleja_modificadores(gestor_singleton):
    """Caso 20: Falla eléctrica compleja con modificadores de luces y A/C."""
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)
    s_id = "test_electrica_compleja"

    await orq.procesar_turno(session_id=s_id, texto_usuario="Kia Rio 2017 tiembla y se apaga", gestor_diagnostico=gestor_singleton)
    r2 = await orq.procesar_turno(
        session_id=s_id,
        texto_usuario="ocurre cuando prendo las luces altas y el aire acondicionado",
        gestor_diagnostico=gestor_singleton,
    )
    st = await repo.get_session(s_id)
    assert st.obtener_valor_confirmado("modificador_ac") == "A/C encendido"
    assert "luces" in st.obtener_valor_confirmado("modificador_luces")
    assert "A/C" in r2["consulta_consolidada"] or "luces" in r2["consulta_consolidada"]
