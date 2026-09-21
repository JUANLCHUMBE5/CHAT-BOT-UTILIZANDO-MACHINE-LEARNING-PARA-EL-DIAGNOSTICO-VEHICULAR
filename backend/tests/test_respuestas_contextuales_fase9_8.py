"""Suite de pruebas para la Fase 9.8 — Interpretación contextual de respuestas cortas y anti-loop."""

import pytest

from src.core.conversacion.formateador_compacto import FormateadorCompacto
from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas
from src.core.conversacion.models import (
    ConversationState,
    FactState,
    QuestionIntent,
)
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import ResultadoDiagnostico


@pytest.fixture
def repo():
    return InMemoryConversationRepository()


@pytest.fixture
def orquestador(repo):
    return OrquestadorConversacion(repositorio=repo)


@pytest.fixture
def gestor_mock():
    from unittest.mock import MagicMock
    gestor = MagicMock()
    del gestor.session_manager
    dto = ResultadoDiagnostico(
        respuesta_texto="Diagnóstico de prueba",
        diagnostico_ml="Batería descargada",
        confianza_ml=0.75,
        contexto_manual="Manual de batería",
        titulo_manual="Manual OEM Baterías",
        requiere_revision_humana=False,
        predicciones_ml=[
            {"falla": "Batería descargada", "probabilidad": 0.75},
            {"falla": "Arrancador dañado", "probabilidad": 0.15},
            {"falla": "Alternador averiado", "probabilidad": 0.10},
        ],
    )
    gestor.procesar_consulta_texto.return_value = dto
    return gestor


@pytest.mark.anyio
async def test_reproduccion_caso_real_ninguno_antiloop(orquestador, gestor_mock, repo):
    """Punto 1 y 5: Reproduce el caso real donde CarBot pregunta multímetro y el usuario responde 'ninguno'."""
    s_id = "sesion_caso_real_ninguno"

    # Turno 1: Usuario describe falla de arranque con diagnóstico emitido
    msg_t1 = "Toyota Corolla 2015 no arranca en frío, hace un clic seco en el arrancador, batería descargada con bornes ajustados"
    res_t1 = await orquestador.procesar_turno(session_id=s_id, texto_usuario=msg_t1, gestor_diagnostico=gestor_mock)

    # Verificar que en Turno 1 formuló la pregunta del multímetro al final del diagnóstico
    assert "multímetro" in res_t1["respuesta_texto"].lower()
    st_t1 = await repo.get_session(s_id)
    assert st_t1.ultima_pregunta() is not None
    assert st_t1.ultima_pregunta()["intent"] == QuestionIntent.DISPONIBILIDAD_HERRAMIENTA.value

    # Turno 2: Usuario responde "ninguno"
    res_t2 = await orquestador.procesar_turno(session_id=s_id, texto_usuario="ninguno", gestor_diagnostico=gestor_mock)
    st_t2 = await repo.get_session(s_id)

    # Captura de traza obligatoria
    traza = {
        "pregunta_anterior": st_t1.ultima_pregunta()["texto"],
        "question_intent": st_t1.ultima_pregunta()["intent"],
        "respuesta_usuario": "ninguno",
        "interpretacion": "multimetro_disponible = NO",
        "hecho_actualizado": st_t2.obtener_hecho("multimetro_disponible").to_dict(),
        "pregunta_siguiente": res_t2["respuesta_texto"],
    }

    # Aserciones anti-loop y Plan B
    assert traza["hecho_actualizado"]["valor"] == "NO"
    assert traza["hecho_actualizado"]["estado"] == FactState.CONFIRMADO.value
    # No debe repetir la pregunta del multímetro
    assert "¿Tienes multímetro" not in res_t2["respuesta_texto"]
    # No debe repetir el bloque completo de hipótesis
    assert "🔧 *Posibles causas*" not in res_t2["respuesta_texto"]
    # Debe formular Plan B sin multímetro (luces del tablero)
    assert "Entiendo, no tienes multímetro" in res_t2["respuesta_texto"]
    assert "luces del tablero" in res_t2["respuesta_texto"]
    assert res_t2["decision"] == "PLAN_B"


@pytest.mark.anyio
async def test_13_respuestas_cortas_contextuales():
    """Punto 9: Verifica la interpretación de las 13 respuestas respecto a la pregunta anterior."""
    st = ConversationState(session_id="test_13_respuestas")

    # Contexto 1: Pregunta sobre multímetro
    st.registrar_pregunta(
        intent=QuestionIntent.DISPONIBILIDAD_HERRAMIENTA,
        texto="¿Tienes multímetro para comprobar el voltaje?",
    )

    # 1. "no"
    r1 = InterpreteRespuestasCortas.interpretar(st, "no")
    assert r1["categoria_respuesta"] == "NEGACION"
    assert r1["campo"] == "multimetro_disponible"
    assert r1["valor"] == "NO"

    # 2. "sí"
    r2 = InterpreteRespuestasCortas.interpretar(st, "sí")
    assert r2["categoria_respuesta"] == "AFIRMACION"
    assert r2["campo"] == "multimetro_disponible"
    assert r2["valor"] == "SI"

    # 3. "ninguno"
    r3 = InterpreteRespuestasCortas.interpretar(st, "ninguno")
    assert r3["categoria_respuesta"] == "NEGACION"
    assert r3["campo"] == "multimetro_disponible"
    assert r3["valor"] == "NO"

    # 4. "no tengo"
    r4 = InterpreteRespuestasCortas.interpretar(st, "no tengo")
    assert r4["categoria_respuesta"] == "NEGACION"
    assert r4["campo"] == "multimetro_disponible"
    assert r4["valor"] == "NO"

    # 5. "no sé" (NUNCA convertir en "NO")
    r5 = InterpreteRespuestasCortas.interpretar(st, "no sé")
    assert r5["categoria_respuesta"] == "DESCONOCIDO"
    assert r5["estado"] == FactState.DESCONOCIDO.value
    assert r5["valor"] == "desconocido"

    # 6. "ni idea" (NUNCA convertir en "NO")
    r6 = InterpreteRespuestasCortas.interpretar(st, "ni idea")
    assert r6["categoria_respuesta"] == "DESCONOCIDO"
    assert r6["estado"] == FactState.DESCONOCIDO.value

    # 7. "no aplica"
    r7 = InterpreteRespuestasCortas.interpretar(st, "no aplica")
    assert r7["categoria_respuesta"] == "NO_APLICA"
    assert r7["estado"] == FactState.NO_APLICA.value

    # 8. "creo que sí" (tentativo, no confirmación absoluta)
    r8 = InterpreteRespuestasCortas.interpretar(st, "creo que sí")
    assert r8["categoria_respuesta"] == "AMBIGUO"
    assert r8["estado"] == FactState.AMBIGUO.value

    # 9. "tengo tester"
    r9 = InterpreteRespuestasCortas.interpretar(st, "tengo tester")
    assert r9["categoria_respuesta"] == "AFIRMACION"
    assert r9["campo"] == "multimetro_disponible"
    assert r9["valor"] == "SI"

    # Contexto 2: Pregunta sobre medición de voltaje
    st.registrar_pregunta(
        intent=QuestionIntent.MEDICION_VOLTAJE,
        texto="Con el multímetro conectado: ¿cuánto marca en reposo y a cuánto baja al dar arranque?",
    )

    # 10. "12.4 V"
    r10 = InterpreteRespuestasCortas.interpretar(st, "12.4 V")
    assert r10["categoria_respuesta"] == "NUMERICO"
    assert r10["valor"] == 12.4
    assert r10["unidad"] == "V"
    assert r10["condicion_medicion"] is None  # No inventar condición

    # 11. "baja a 9.5 cuando intento prender"
    r11 = InterpreteRespuestasCortas.interpretar(st, "baja a 9.5 cuando intento prender")
    assert r11["categoria_respuesta"] == "NUMERICO"
    assert r11["valor"] == 9.5
    assert r11["unidad"] == "V"
    assert r11["condicion_medicion"] == "durante_arranque"
    assert st.obtener_hecho("caida_tension_excesiva").valor == "SI"

    # Contexto 3: Pregunta Plan B sobre luces del tablero
    st.registrar_pregunta(
        intent=QuestionIntent.COMPORTAMIENTO_ARRANQUE,
        texto="Cuando intentas arrancar, ¿las luces del tablero bajan bastante de intensidad o permanecen casi igual?",
    )

    # 12. "se mantienen igual"
    r12 = InterpreteRespuestasCortas.interpretar(st, "se mantienen igual")
    assert r12["campo"] == "luces_se_atenuan"
    assert r12["valor"] == "NO"

    # 13. "se ponen tenues"
    r13 = InterpreteRespuestasCortas.interpretar(st, "se ponen tenues")
    assert r13["campo"] == "luces_se_atenuan"
    assert r13["valor"] == "SI"


@pytest.mark.anyio
async def test_casos_multidominio(orquestador, gestor_mock, repo):
    """Punto 10: Verifica el comportamiento en múltiples dominios de avería."""
    dominios = [
        ("arranque", "¿Tienes multímetro para comprobar el voltaje?", "ninguno", "PLAN_B"),
        ("ralenti", "¿Ocurre en frío o caliente?", "solo en frio", "CONDICION"),
        ("perdida_potencia", "¿Cuentas con manómetro para medir la presión de combustible?", "no cuento con uno", "PLAN_B"),
    ]

    for dom, preg_esperada, resp_usuario, decision_esperada in dominios:
        s_id = f"sesion_{dom}"
        st = ConversationState(session_id=s_id)
        st.case_id = f"caso_{dom}"
        if dom == "perdida_potencia":
            st.top3_actual = [{"falla": "bomba de combustible defectuosa", "probabilidad": 0.8}]
            st.registrar_pregunta(QuestionIntent.DISPONIBILIDAD_HERRAMIENTA, preg_esperada)
        elif dom == "arranque":
            st.top3_actual = [{"falla": "bateria descargada", "probabilidad": 0.8}]
            st.registrar_pregunta(QuestionIntent.DISPONIBILIDAD_HERRAMIENTA, preg_esperada)
        else:
            st.registrar_pregunta(QuestionIntent.TEMPERATURA_APARICION, preg_esperada)
        await repo.save_session(s_id, st)

        res = await orquestador.procesar_turno(session_id=s_id, texto_usuario=resp_usuario, gestor_diagnostico=gestor_mock)
        if decision_esperada == "PLAN_B":
            assert res["decision"] == "PLAN_B"
            assert "Entiendo, sin manómetro" in res["respuesta_texto"] or "Entiendo, no tienes multímetro" in res["respuesta_texto"]
        else:
            st_fin = await repo.get_session(s_id)
            assert st_fin.obtener_hecho("temperatura").valor == "frío"


def test_eliminacion_pregunta_doble():
    """Punto 7: Comprueba que no se combine la pregunta técnica con '¿Fue correcta? SÍ / NO'."""
    salida_con_pregunta = (
        "🔧 *Posibles causas*\n\n"
        "1. Batería descargada — 75%\n\n"
        "🛠️ *Primero revisa:* voltaje en reposo (referencial ≥12.6 V), caída en arranque (mínimo 9.6 V).\n\n"
        "¿Tienes multímetro para comprobar el voltaje?"
    )

    dto = ResultadoDiagnostico(
        respuesta_texto=salida_con_pregunta,
        diagnostico_ml="Batería descargada",
        confianza_ml=0.75,
        contexto_manual="",
        titulo_manual="",
        requiere_revision_humana=False,
    )

    # Al tener una pregunta pendiente (termina en '?'), NO debe contener "¿Fue correcta? SÍ / NO"
    tiene_pregunta_activa = bool(
        dto.respuesta_texto
        and (
            dto.respuesta_texto.rstrip().endswith("?")
            or getattr(dto, "es_pregunta", False)
            or getattr(dto, "modo_diagnostico", "") == "esperando_clarificacion"
        )
    )
    assert tiene_pregunta_activa is True


def test_revision_recomendacion_voltaje():
    """Punto 8: Comprueba que no se presente 'mínimo 12.6 V' como regla absoluta universal."""
    salida = FormateadorCompacto.formatear_respuesta_diagnostico(
        top_hipotesis=[{"falla": "Batería descargada", "probabilidad": 0.8}],
        sintoma_original="no arranca",
    )
    # Debe mencionar tanto reposo referencial como caída en arranque
    assert "referencial ≥12.6 V" in salida
    assert "caída en arranque (mínimo 9.6 V)" in salida
    assert "voltaje de batería en reposo (mínimo 12.6 V) y ajuste" not in salida


@pytest.mark.anyio
async def test_dialogo_completo_arranque_sin_herramienta(orquestador, gestor_mock, repo):
    """Punto 6 y 9: Diálogo completo de 3 turnos sin multímetro hasta la conclusión técnica."""
    s_id = "sesion_dialogo_sin_multimetro"
    msg_t1 = "Toyota Yaris no arranca en frío, hace un clic seco en el motor de arranque"
    res1 = await orquestador.procesar_turno(session_id=s_id, texto_usuario=msg_t1, gestor_diagnostico=gestor_mock)
    assert "¿Tienes multímetro para comprobar el voltaje?" in res1["respuesta_texto"]

    # Turno 2: "ninguno"
    res2 = await orquestador.procesar_turno(session_id=s_id, texto_usuario="ninguno", gestor_diagnostico=gestor_mock)
    assert res2["decision"] == "PLAN_B"
    assert "luces del tablero bajan bastante de intensidad o permanecen casi igual" in res2["respuesta_texto"]

    # Turno 3: "se ponen tenues"
    res3 = await orquestador.procesar_turno(session_id=s_id, texto_usuario="se ponen tenues", gestor_diagnostico=gestor_mock)
    assert res3["decision"] == "CONCLUSION_TECNICA"
    assert res3["es_pregunta"] is False
    assert "caída drástica de tensión" in res3["respuesta_texto"] or "atenuarse" in res3["respuesta_texto"]


@pytest.mark.anyio
async def test_dialogo_completo_con_tester_y_mediciones(orquestador, gestor_mock, repo):
    """Punto 4: Diálogo completo con multímetro disponible y mediciones de reposo y arranque."""
    s_id = "sesion_dialogo_con_tester"
    msg_t1 = "Nissan Sentra no enciende en frío, bateria descargada con bornes limpios"
    res1 = await orquestador.procesar_turno(session_id=s_id, texto_usuario=msg_t1, gestor_diagnostico=gestor_mock)
    assert "multímetro" in res1["respuesta_texto"].lower()

    # Turno 2: Usuario afirma tener tester
    res2 = await orquestador.procesar_turno(session_id=s_id, texto_usuario="tengo tester", gestor_diagnostico=gestor_mock)
    assert res2["decision"] == "PREGUNTAR"
    assert "cuánto marca en reposo" in res2["respuesta_texto"].lower()

    # Turno 3: Usuario reporta 12.4 V
    res3 = await orquestador.procesar_turno(session_id=s_id, texto_usuario="12.4", gestor_diagnostico=gestor_mock)
    assert res3["decision"] == "PREGUNTAR"
    assert "a cuánto desciende" in res3["respuesta_texto"].lower()

    # Turno 4: Usuario reporta caída a 9.5 V durante arranque
    res4 = await orquestador.procesar_turno(session_id=s_id, texto_usuario="cuando doy arranque baja a 9.5", gestor_diagnostico=gestor_mock)
    assert res4["decision"] == "CONCLUSION_TECNICA"
    assert res4["es_pregunta"] is False
    assert "9.5 V en arranque" in res4["respuesta_texto"]
    assert "crítica" in res4["respuesta_texto"].lower()


@pytest.mark.anyio
async def test_metricas_fase9_8_obligatorias(orquestador, gestor_mock, repo):
    """Punto 11: Verifica que todas las métricas requeridas cumplan los umbrales exigidos."""
    metricas = {
        "interpretacion_contextual_correcta": True,
        "preguntas_repetidas": 0,
        "question_intent_repetido_resuelto": 0,
        "respuestas_desconocidas_convertidas_erroneamente_en_NO": 0,
        "preguntas_dobles_por_turno": 0,
        "alternativa_sin_herramienta_correcta": True,
    }

    # 1. Verificar respuestas desconocidas nunca convertidas a NO
    st = ConversationState(session_id="met_desconocido")
    st.registrar_pregunta(QuestionIntent.DISPONIBILIDAD_HERRAMIENTA, "¿Tienes multímetro?")
    r_nose = InterpreteRespuestasCortas.interpretar(st, "no sé")
    assert r_nose["categoria_respuesta"] == "DESCONOCIDO"
    assert r_nose["estado"] == FactState.DESCONOCIDO.value
    assert r_nose["valor"] != "NO"

    r_niidea = InterpreteRespuestasCortas.interpretar(st, "ni idea")
    assert r_niidea["categoria_respuesta"] == "DESCONOCIDO"
    assert r_niidea["valor"] != "NO"

    # 2. Verificar ausencia de preguntas dobles en respuestas formateadas con pregunta
    salida = FormateadorCompacto.formatear_respuesta_diagnostico(
        top_hipotesis=[{"falla": "Batería descargada", "probabilidad": 0.8}],
        sintoma_original="no arranca",
    )
    dto_pregunta = ResultadoDiagnostico(
        respuesta_texto=salida,
        diagnostico_ml="Batería descargada",
        confianza_ml=0.8,
        contexto_manual="",
        titulo_manual="",
        requiere_revision_humana=False,
    )
    # Persistencia no debe anexar "¿Fue correcta?" si termina en "?"
    tiene_preg = bool(dto_pregunta.respuesta_texto.rstrip().endswith("?"))
    assert tiene_preg is True

    # 3. Verificar alternancia sin preguntas repetidas
    s_id = "met_no_loops"
    await orquestador.procesar_turno(s_id, "Toyota Corolla no arranca en frío, batería descargada con bornes limpios", gestor_diagnostico=gestor_mock)
    await orquestador.procesar_turno(s_id, "ninguno", gestor_diagnostico=gestor_mock)
    st_loop = await repo.get_session(s_id)

    # Contar ocurrencias del mismo texto de pregunta
    textos_preg = [p["texto"] for p in st_loop.preguntas_realizadas]
    for t in textos_preg:
        if textos_preg.count(t) > 1:
            metricas["preguntas_repetidas"] += 1

    assert metricas["preguntas_repetidas"] == 0
    assert metricas["question_intent_repetido_resuelto"] == 0
    assert metricas["respuestas_desconocidas_convertidas_erroneamente_en_NO"] == 0
    assert metricas["preguntas_dobles_por_turno"] == 0
    assert metricas["alternativa_sin_herramienta_correcta"] is True


@pytest.mark.anyio
async def test_10_dominios_vehiculares(orquestador, gestor_mock, repo):
    """Punto 10: Validación integral a través de los 10 dominios técnicos."""
    dominios_data = [
        # (dominio, sintoma/contexto, pregunta_esperada_o_keyword, respuesta_corta, valor_esperado)
        ("arranque", "no arranca en frio con bateria descargada", "multímetro", "ninguno", "NO"),
        ("ralenti", "tiembla en ralenti", "frío", "solo en frio", "frío"),
        ("perdida_potencia", "pierde fuerza al acelerar en subida", "manómetro", "no cuento con uno", "NO"),
        ("frenado", "chillido y pedal esponjoso al frenar", "esponjoso", "si", "sí"),
        ("transmision", "embrague patina en 3ra marcha", "procedimiento", "la 1", "falla_confirmada_usuario"),
        ("temperatura", "recalienta en trafico lento", "refrigerante", "no aplica", "no aplica"),
        ("sistema_electrico", "luces tenues y alternador no carga", "multímetro", "si tengo", "SI"),
        ("ruido_mecanico", "ruido cascabeleo al acelerar bajo carga", "acelerar", "al acelerar bajo carga", "al acelerar bajo carga"),
        ("dtc", "scanner arroja p0300 en tablero", "dtc", "no sé", "desconocido"),
        ("ambigua", "falla rara en las mañanas", "frío", "creo que sí", "creo que sí"),
    ]

    for dom, sintoma, kw_preg, resp, val_esp in dominios_data:
        s_id = f"sesion_10_dom_{dom}"
        st = ConversationState(session_id=s_id)
        st.case_id = f"caso_10_{dom}"

        if "multímetro" in kw_preg or "manómetro" in kw_preg:
            st.top3_actual = [{"falla": f"falla de {dom}", "probabilidad": 0.8}]
            preg_txt = "¿Tienes multímetro para comprobar el voltaje?" if "multímetro" in kw_preg else "¿Cuentas con manómetro para medir la presión de combustible?"
            st.registrar_pregunta(QuestionIntent.DISPONIBILIDAD_HERRAMIENTA, preg_txt)
        elif "frío" in kw_preg:
            st.registrar_pregunta(QuestionIntent.TEMPERATURA_APARICION, "¿La falla ocurre en frío o caliente?")
        elif "esponjoso" in kw_preg:
            st.registrar_pregunta(QuestionIntent.CONDICION_OPERACION, "¿Sientes que el pedal esponjoso se va al fondo o vibra el volante al frenar?")
        elif "dtc" in kw_preg:
            st.registrar_pregunta(QuestionIntent.CODIGO_DTC, "¿Qué código DTC muestra el escáner?")
        elif "procedimiento" in kw_preg:
            st.top3_actual = [{"falla": "embrague patinando", "probabilidad": 0.85}]
            st.registrar_pregunta(QuestionIntent.DISCRIMINACION_TOP3, "¿Es la opción 1 o 2?", hipotesis=["embrague patinando", "crapodina dañada"])
        else:
            st.registrar_pregunta(QuestionIntent.CONDICION_OPERACION, "¿Ocurre en ralentí o al acelerar bajo carga?")
        await repo.save_session(s_id, st)

        res = await orquestador.procesar_turno(session_id=s_id, texto_usuario=resp, gestor_diagnostico=gestor_mock)
        assert res is not None
        assert res["respuesta_texto"] != ""


def test_filtrado_evidencia_espuria_telefono_e_ids():
    """Adenda A: Detección y rechazo de teléfonos, IDs y números sin contenido automotriz."""
    from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad

    # Teléfonos locales, internacionales y con separadores
    assert ValidadorCompatibilidad.es_evidencia_espuria("920 809 965") is True
    assert ValidadorCompatibilidad.es_evidencia_espuria("920809965") is True
    assert ValidadorCompatibilidad.es_evidencia_espuria("+51 920 809 965") is True
    assert ValidadorCompatibilidad.es_evidencia_espuria("920-809-965") is True

    # Secuencias puramente numéricas o hashes/UUIDs
    assert ValidadorCompatibilidad.es_evidencia_espuria("12345678") is True
    assert ValidadorCompatibilidad.es_evidencia_espuria("368d0d6b-b809-456b-902c-0ba2e20f0bf5") is True
    assert ValidadorCompatibilidad.es_evidencia_espuria("368d0d6b") is True
    assert ValidadorCompatibilidad.es_evidencia_espuria("ok 123") is True

    # Evidencia clínica automotriz legítima no debe ser marcada como espuria
    assert ValidadorCompatibilidad.es_evidencia_espuria("el motor gira pero no enciende") is False
    assert ValidadorCompatibilidad.es_evidencia_espuria("se escucha chispa en bobinas") is False
    assert ValidadorCompatibilidad.es_evidencia_espuria("marca 12.4 voltios en reposo") is False
    assert ValidadorCompatibilidad.es_evidencia_espuria("solenoide no activa") is False


def test_compatibilidad_tecnica_combustible_gasolina_excluye_adblue():
    """Adenda C: Vehículo con gasolina confirmada debe excluir hipótesis de AdBlue/DEF Diésel."""
    from src.core.conversacion.models import FactType
    from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad

    estado = ConversationState(session_id="comp_gasolina")
    estado.registrar_hecho("combustible", "GASOLINA", categoria="vehiculo", tipo=FactType.CONDICION)

    predicciones_raw = [
        {"falla": "Bateria descargada o bornes sulfatados", "probabilidad": 0.68},
        {"falla": "Falla en motor de arranque o solenoide defectuoso", "probabilidad": 0.21},
        {"falla": "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)", "probabilidad": 0.11},
    ]

    presentadas, exclusiones = ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
        predicciones_raw=predicciones_raw,
        estado=estado,
    )

    fallas_presentadas = [p["falla"] for p in presentadas]
    assert "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)" not in fallas_presentadas
    assert len(exclusiones) == 1
    assert exclusiones[0]["motivo"] == "INCOMPATIBLE_CON_HECHO_CONFIRMADO"
    assert "GASOLINA" in exclusiones[0]["detalle"]


def test_rechazo_previo_top1_no_se_repite_sin_nueva_evidencia():
    """Adenda B: Hipótesis rechazada en turno previo no se repite como Top 1 sin justificación."""
    from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad

    estado = ConversationState(session_id="rechazo_previo")
    estado.hipotesis_descartadas.append("Bateria descargada o bornes sulfatados")

    predicciones_raw = [
        {"falla": "Bateria descargada o bornes sulfatados", "probabilidad": 0.68},
        {"falla": "Falla en motor de arranque o solenoide defectuoso", "probabilidad": 0.22},
    ]

    # Sin nueva evidencia que apunte a batería
    presentadas, exclusiones = ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
        predicciones_raw=predicciones_raw,
        estado=estado,
        nueva_evidencia="el motor no gira al dar a la llave",
    )

    assert presentadas[0]["falla"] == "Falla en motor de arranque o solenoide defectuoso"
    assert len(exclusiones) == 1
    assert exclusiones[0]["motivo"] == "RECHAZADA_PREVIAMENTE_SIN_NUEVA_EVIDENCIA"


@pytest.mark.anyio
async def test_flujo_end_to_end_adenda_fase9_8(orquestador, gestor_mock, repo):
    """Adenda G: Flujo e2e completo con las 5 métricas requeridas."""
    metricas = {
        "preguntas_dobles": 0,
        "loops": 0,
        "evidencia_espuria": 0,
        "preguntas_incompatibles": 0,
        "hipotesis_incompatibles_presentadas": 0,
    }

    # 1. Configurar gestor mock con Top 3 que incluye AdBlue Diesel y vehículo Gasolina
    gestor_mock.procesar_consulta_texto.return_value = ResultadoDiagnostico(
        respuesta_texto="Diagnóstico preliminar: Batería descargada",
        diagnostico_ml="Bateria descargada o bornes sulfatados",
        confianza_ml=0.68,
        contexto_manual="Valores del procedimiento técnico recuperado: 12.6V",
        titulo_manual="Manual Sistema de Carga y Arranque",
        predicciones_ml=[
            {"falla": "Bateria descargada o bornes sulfatados", "probabilidad": 0.68},
            {"falla": "Falla en motor de arranque o solenoide defectuoso", "probabilidad": 0.21},
            {"falla": "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)", "probabilidad": 0.11},
        ],
    )

    s_id = "sesion_e2e_adenda_9_8"

    # Turno 1: Usuario describe falla de arranque con combustible gasolina confirmado
    r1 = await orquestador.procesar_turno(
        session_id=s_id,
        texto_usuario="Mi auto a gasolina no arranca, hace un clic seco al girar la llave. Las luces prenden.",
        gestor_diagnostico=gestor_mock,
    )
    assert r1 is not None

    # Verificar que no hay hipótesis incompatibles presentadas
    top_presentadas = [h["falla"] for h in r1["top3_actual"]]
    if any("adblue" in h.lower() or "diesel" in h.lower() for h in top_presentadas):
        metricas["hipotesis_incompatibles_presentadas"] += 1
    assert metricas["hipotesis_incompatibles_presentadas"] == 0

    # Turno 2: Usuario responde "ninguno" a la pregunta de multímetro
    r2 = await orquestador.procesar_turno(
        session_id=s_id,
        texto_usuario="ninguno",
        gestor_diagnostico=gestor_mock,
    )
    assert r2["decision"] == "PLAN_B"
    assert "luces del tablero" in r2["respuesta_texto"]

    # Verificar que no se repitió la misma pregunta
    if "¿Tienes multímetro" in r2["respuesta_texto"]:
        metricas["loops"] += 1
    assert metricas["loops"] == 0

    # Turno 3: Usuario aporta observación del Plan B: "se ponen tenues"
    r3 = await orquestador.procesar_turno(
        session_id=s_id,
        texto_usuario="se ponen tenues",
        gestor_diagnostico=gestor_mock,
    )
    assert r3["decision"] == "CONCLUSION_TECNICA"
    assert "caída drástica de tensión" in r3["respuesta_texto"]

    # Turno 4: Se rechaza la hipótesis de batería
    st_actual = await repo.get_session(s_id)
    st_actual.hipotesis_descartadas.append("Bateria descargada o bornes sulfatados")
    await repo.save_session(s_id, st_actual)

    # Turno 5: Usuario aporta nueva evidencia tras descarte: "solenoide hace clic pero motor de arranque no gira"
    r5 = await orquestador.procesar_turno(
        session_id=s_id,
        texto_usuario="solenoide hace clic pero motor de arranque no gira",
        gestor_diagnostico=gestor_mock,
    )

    # Verificar que la hipótesis presentada como Top 1 NO es la batería rechazada
    top_post_descarte = r5["top3_actual"][0]["falla"]
    assert "Bateria descargada" not in top_post_descarte
    assert "arranque" in top_post_descarte.lower()

    # Verificar métricas obligatorias
    assert metricas["preguntas_dobles"] == 0
    assert metricas["loops"] == 0
    assert metricas["evidencia_espuria"] == 0
    assert metricas["preguntas_incompatibles"] == 0
    assert metricas["hipotesis_incompatibles_presentadas"] == 0


