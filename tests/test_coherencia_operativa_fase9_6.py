"""Suite de pruebas de integración y regresión para Fase 9.6: Coherencia Operativa y Anti-Loop Semántico."""

import pytest

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.models import (
    ConversationState,
    EstadoOperativo,
    QuestionIntent,
)
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.mark.anyio
async def test_reproduccion_caso_real_whatsapp():
    """Reproduce el caso real: CarBot debe identificar ARRANQUE y NO preguntar ralentí/carretera/frenado."""
    gestor = GestorDiagnostico()
    orq = OrquestadorConversacion()
    sid = "test_caso_real_whatsapp_9_6"

    mensaje_real = (
        "Buenas, mi carro tiene un problema. Ayer lo dejé estacionado en la calle y cuando "
        "volví en la noche ya no quiso arrancar. Le doy a la llave y hace como un clic seco, "
        "una sola vez, y nada más. Las luces del tablero sí prenden bien, y el radio también."
    )

    res = await orq.procesar_turno(session_id=sid, texto_usuario=mensaje_real, gestor_diagnostico=gestor)
    estado = res["estado"]

    # 1. Verificación de hechos extraídos
    assert estado.obtener_hecho("motor_arranca") is not None
    assert estado.obtener_hecho("motor_arranca").valor == "NO"
    assert estado.obtener_hecho("evento") is not None
    assert estado.obtener_hecho("evento").valor == "giro_llave"
    assert estado.obtener_hecho("ruido_arranque") is not None
    assert estado.obtener_hecho("ruido_arranque").valor == "clic_unico"
    assert estado.obtener_hecho("tablero_enciende") is not None
    assert estado.obtener_hecho("tablero_enciende").valor == "SI"
    assert estado.obtener_hecho("radio_enciende") is not None
    assert estado.obtener_hecho("radio_enciende").valor == "SI"

    # 2. Regla estricta: NO inferir bateria_buena ni motor_arranque_averiado
    assert estado.obtener_hecho("bateria_buena") is None
    assert estado.obtener_hecho("motor_arranque_averiado") is None

    # 3. Estado operativo inferido
    assert estado.estado_operativo == EstadoOperativo.ARRANQUE
    assert res["estado_operativo"] == "ARRANQUE"

    # 4. Anti-loop y compatibilidad de preguntas: NO preguntar ralentí/carretera/frenado
    assert res["es_pregunta"] is True
    pregunta = res["respuesta_texto"].lower()
    assert "ralentí" not in pregunta
    assert "ralenti" not in pregunta
    assert "carretera" not in pregunta
    assert "freno" not in pregunta
    assert "acelerar con fuerza" not in pregunta

    # 5. La pregunta debe ser coherente con el intento de arranque
    assert res["question_intent"] == QuestionIntent.COMPORTAMIENTO_ARRANQUE.value
    assert "arranque" in pregunta or "llave" in pregunta or "luces" in pregunta


@pytest.mark.anyio
async def test_escenario_a_no_arranca_clic_unico_accesorios():
    """Escenario A: No arranca + clic único + accesorios -> No preguntar ralentí/carretera/frenado."""
    estado = ConversationState(session_id="escenario_a")
    msg = "no arranca, hace un solo clic seco al girar la llave pero la radio y tablero prenden"
    ExtractorHechos.extraer_y_actualizar(estado, msg)

    assert estado.estado_operativo == EstadoOperativo.ARRANQUE
    sel = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    assert sel is not None
    txt, opc, intent, candidatas, descartadas = sel

    assert intent == QuestionIntent.COMPORTAMIENTO_ARRANQUE
    texto_l = txt.lower()
    assert "ralentí" not in texto_l
    assert "carretera" not in texto_l
    assert "freno" not in texto_l


@pytest.mark.anyio
async def test_escenario_b_no_arranca_clac_clac_luces_se_atenuan():
    """Escenario B: No arranca + clac-clac + luces se atenúan -> Preguntas compatibles con arranque."""
    estado = ConversationState(session_id="escenario_b")
    msg = "al darle a la llave no arranca, hace tac-tac rápido y las luces del tablero se atenúan"
    ExtractorHechos.extraer_y_actualizar(estado, msg)

    assert estado.estado_operativo == EstadoOperativo.ARRANQUE
    assert estado.obtener_hecho("ruido_arranque").valor == "clics_repetidos"
    assert estado.obtener_hecho("luces_se_atenuan").valor == "SI"

    # Si se formula pregunta, debe ser exclusivamente compatible con arranque
    sel = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    if sel:
        txt, _, intent, _, _ = sel
        assert intent != QuestionIntent.CONDICION_OPERACION
        assert "freno" not in txt.lower()
        assert "ralentí" not in txt.lower()


@pytest.mark.anyio
async def test_escenario_c_tiembla_unicamente_en_ralenti():
    """Escenario C: Tiembla únicamente en ralentí -> No preguntar inicialmente por frenado."""
    estado = ConversationState(session_id="escenario_c")
    msg = "el motor tiembla únicamente cuando está detenido en ralentí en el semáforo"
    ExtractorHechos.extraer_y_actualizar(estado, msg)

    assert estado.estado_operativo == EstadoOperativo.RALENTI
    sel = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    assert sel is not None
    txt, _, intent, _, _ = sel

    # No debe preguntar por frenado
    assert "freno" not in txt.lower()
    assert "frenar" not in txt.lower()
    assert intent != QuestionIntent.CONDICION_OPERACION


@pytest.mark.anyio
async def test_escenario_d_pierde_potencia_20_minutos_circulando():
    """Escenario D: Pierde potencia después de 20 min circulando -> Estado MARCHA; no preguntar arranque."""
    estado = ConversationState(session_id="escenario_d")
    msg = "pierde potencia después de 20 minutos circulando en carretera a 90 km/h"
    ExtractorHechos.extraer_y_actualizar(estado, msg)

    assert estado.estado_operativo == EstadoOperativo.MARCHA
    sel = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    if sel:
        txt, _, intent, _, _ = sel
        # No debe formular una pregunta de no-arranque
        assert "no arranca" not in txt.lower()
        assert "dar arranque" not in txt.lower()
        assert intent != QuestionIntent.COMPORTAMIENTO_ARRANQUE


@pytest.mark.anyio
async def test_escenario_e_vibra_unicamente_al_frenar():
    """Escenario E: Vibra únicamente al frenar -> Estado FRENADO."""
    estado = ConversationState(session_id="escenario_e")
    msg = "el timón vibra únicamente cuando piso el pedal de freno"
    ExtractorHechos.extraer_y_actualizar(estado, msg)

    assert estado.estado_operativo == EstadoOperativo.FRENADO
    sel = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    if sel:
        txt, _, intent, _, _ = sel
        assert "no arranca" not in txt.lower()
        assert intent != QuestionIntent.COMPORTAMIENTO_ARRANQUE


@pytest.mark.anyio
async def test_escenario_f_usuario_dice_solamente_mi_carro_falla():
    """Escenario F: Usuario dice solamente 'mi carro falla' -> Estado DESCONOCIDO; pregunta de condición es válida."""
    estado = ConversationState(session_id="escenario_f")
    msg = "mi carro falla"
    ExtractorHechos.extraer_y_actualizar(estado, msg)

    assert estado.estado_operativo == EstadoOperativo.DESCONOCIDO
    sel = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    assert sel is not None
    txt, opc, intent, _, _ = sel

    # Aquí sí es válida una pregunta general de condición de operación
    assert intent == QuestionIntent.CONDICION_OPERACION
    assert "ralentí" in txt.lower()
    assert "carretera" in txt.lower()
    assert "freno" in txt.lower()


@pytest.mark.anyio
async def test_escenario_g_cambio_de_caso_limpia_estado_operativo():
    """Escenario G: Usuario cambia de síntoma/caso -> No heredar estado operativo del caso anterior."""
    estado = ConversationState(session_id="escenario_g")
    ExtractorHechos.extraer_y_actualizar(estado, "no arranca el auto, hace un solo clic")
    assert estado.estado_operativo == EstadoOperativo.ARRANQUE

    # Cierre / reinicio de caso
    estado.iniciar_nuevo_caso()
    assert estado.estado_operativo == EstadoOperativo.DESCONOCIDO
    assert len(estado.hechos) == 0

    # Nuevo síntoma en caso nuevo
    ExtractorHechos.extraer_y_actualizar(estado, "vibra mucho al frenar en bajada")
    assert estado.estado_operativo == EstadoOperativo.FRENADO


@pytest.mark.anyio
async def test_escenario_h_informacion_contradictoria_aclaracion():
    """Escenario H: Información contradictoria ('no arranca' y 'cuando voy a 80 vibra') -> Solicitar aclaración."""
    estado = ConversationState(session_id="escenario_h")
    msg = "el carro no arranca y cuando voy a 80 vibra"
    ExtractorHechos.extraer_y_actualizar(estado, msg)

    # Detecta contradicción y registra conflicto
    assert estado.obtener_hecho("conflicto_operativo") is not None
    sel = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    assert sel is not None
    txt, opc, intent, _, _ = sel

    # Pregunta de aclaración de inconsistencia
    assert intent == QuestionIntent.ACLARACION_CONTRADICCION
    assert "antecedente" in txt.lower() or "otro momento" in txt.lower() or "distintas" in txt.lower()


@pytest.mark.anyio
async def test_anti_loop_multiturno_metricas():
    """Prueba Anti-Loop multi-turno: preguntas_incompatibles=0, repetidas=0, hechos_ya_conocidos=0."""
    gestor = GestorDiagnostico()
    orq = OrquestadorConversacion()
    sid = "test_anti_loop_metrics"

    preguntas_incompatibles = 0
    preguntas_repetidas_semanticamente = 0
    hechos_confirmados_preguntados_nuevamente = 0

    # Turno 1: Reporte inicial de no arranque
    msg1 = "mi auto no arranca, ayer lo estacioné y ahora hace un solo clic seco al dar llave pero tablero prende"
    res1 = await orq.procesar_turno(session_id=sid, texto_usuario=msg1, gestor_diagnostico=gestor)

    if res1["es_pregunta"]:
        txt1 = res1["respuesta_texto"].lower()
        if any(w in txt1 for w in ("ralentí", "carretera", "freno")):
            preguntas_incompatibles += 1
        if "un solo clic" in txt1:  # ya conocido
            hechos_confirmados_preguntados_nuevamente += 1

    # Turno 2: Respuesta del usuario a la pregunta de luces
    msg2 = "las luces del tablero se bajan por completo"
    res2 = await orq.procesar_turno(session_id=sid, texto_usuario=msg2, gestor_diagnostico=gestor)

    if res2["es_pregunta"]:
        txt2 = res2["respuesta_texto"].lower()
        if res2["question_intent"] == res1["question_intent"]:
            preguntas_repetidas_semanticamente += 1
        if any(w in txt2 for w in ("ralentí", "carretera", "freno")):
            preguntas_incompatibles += 1
        if "luces" in txt2:  # ya respondido
            hechos_confirmados_preguntados_nuevamente += 1

    assert preguntas_incompatibles == 0, f"Preguntas incompatibles detectadas: {preguntas_incompatibles}"
    assert preguntas_repetidas_semanticamente == 0, f"Preguntas repetidas detectadas: {preguntas_repetidas_semanticamente}"
    assert hechos_confirmados_preguntados_nuevamente == 0, f"Hechos conocidos preguntados nuevamente: {hechos_confirmados_preguntados_nuevamente}"
