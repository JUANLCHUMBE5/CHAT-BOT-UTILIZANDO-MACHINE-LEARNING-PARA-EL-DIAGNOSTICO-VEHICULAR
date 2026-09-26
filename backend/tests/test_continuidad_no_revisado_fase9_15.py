"""Pruebas de regresión y continuidad para Fase 9.15.

Auditoría y validación de:
1. Turno 3 del incidente real de WhatsApp: el usuario indica no haber revisado y no saber cómo comprobar holgura.
2. Distinción conceptual estricta de los 4 estados:
   - NO_REVISADO
   - NO_SABE_REALIZAR_PRUEBA
   - HERRAMIENTA_NO_DISPONIBLE
   - RESULTADO_NEGATIVO
3. Activación de alternativas observables y procedimientos seguros (GestorPlanB) en 6 dominios:
   - Suspensión
   - Frenos
   - Motor
   - Eléctrico
   - Transmisión
   - Climatización
4. Controles de pertinencia OBD-II / DTC (admisible solo con evidencia electrónica compatible).
"""

from __future__ import annotations

from types import SimpleNamespace

from src.core.conversacion.compatibilidad_preguntas import CompatibilidadPreguntas
from src.core.conversacion.gestor_plan_b import GestorPlanB
from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas
from src.core.conversacion.models import (
    ConversationState,
    DtcStatus,
    FactState,
    FactType,
    QuestionIntent,
)
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion


class GestorDiagnosticoMock:
    """Mock ligero para pruebas del orquestador conversacional."""

    def __init__(self):
        self.session_manager = None
        self.motor_rag = None

    def clasificar_sintomas(self, consulta: str) -> list[dict]:
        c_l = consulta.lower()
        if "cascabeleo" in c_l or "suspension" in c_l or "bache" in c_l or "golpeteo" in c_l:
            return [
                {"falla": "Desgaste de bujes o rótulas de suspensión", "probabilidad": 0.72},
                {"falla": "Holgura en terminales de dirección", "probabilidad": 0.18},
                {"falla": "Desgaste en bieletas estabilizadoras", "probabilidad": 0.10},
            ]
        return [
            {"falla": "Falla mecánica general", "probabilidad": 0.60},
            {"falla": "Desgaste auxiliar", "probabilidad": 0.25},
            {"falla": "Revisión preventiva", "probabilidad": 0.15},
        ]

    def procesar_consulta_texto(self, *, texto_usuario, **kwargs):
        predicciones = self.clasificar_sintomas(texto_usuario)
        return SimpleNamespace(
            diagnostico_ml=predicciones[0]["falla"],
            confianza_ml=predicciones[0]["probabilidad"],
            predicciones_ml=predicciones,
        )


def test_diagnostico_sin_session_manager_no_falla():
    """Ejercita suficiencia real y diagnóstico con sesión opcional ausente."""
    import asyncio

    from src.core.conversacion.repositorio import InMemoryConversationRepository

    async def ejecutar():
        orquestador = OrquestadorConversacion(InMemoryConversationRepository())
        resultado = await orquestador.procesar_turno(
            "sin-session-manager",
            "Cuando paso por baches escucho un golpeteo en la parte delantera. "
            "En pista lisa casi no se escucha. Al frenar no vibra el volante "
            "y el motor funciona normal. Todavía no he revisado la suspensión.",
            GestorDiagnosticoMock(),
        )
        assert resultado["decision"] == "DIAGNOSTICAR"
        assert "suspensión" in resultado["respuesta_texto"].lower()
        assert "obd" not in resultado["respuesta_texto"].lower()
        await orquestador.finalizar_caso("sin-session-manager", GestorDiagnosticoMock())

    asyncio.run(ejecutar())


def test_incidente_real_whatsapp_fase9_15_completo(monkeypatch) -> None:
    """Valida Plan B con el incidente real en la ruta de interrogación.

    La suficiencia se controla: el mensaje inicial ya puede producir una
    hipótesis en el flujo actual. Esta prueba verifica la ruta de preguntas.
    """
    import asyncio

    from src.core.conversacion.suficiencia_informacion import EvaluadorSuficiencia

    monkeypatch.setattr(
        EvaluadorSuficiencia, "evaluar",
        lambda estado: (2, ["sintoma", "condicion"], False, "Interrogación controlada"),
    )

    async def _run() -> None:
        orquestador = OrquestadorConversacion()
        mock_diag = GestorDiagnosticoMock()
        session_id = "test-wapp-incidente-915"

        # Turno 1: Usuario describe ruido en baches, sin vibrar al frenar, motor normal
        msg1 = (
            "Hola, ahora quisiera revisar otro problema. Cuando paso por pistas irregulares o baches escucho "
            "un golpeteo en la parte delantera del carro. En pista lisa casi no se escucha. Al frenar no vibra el volante "
            "y el motor funciona normal. Todavía no he revisado la suspensión."
        )
        res1 = await orquestador.procesar_turno(session_id, msg1, mock_diag)
        assert res1["es_pregunta"], "Turno 1 debe emitir pregunta discriminante"
        assert "golpe seco" in res1["respuesta_texto"].lower() or "cascabeleo" in res1["respuesta_texto"].lower()

        # Turno 2: Usuario aclara cascabeleo metálico
        msg2 = "Es más como un cascabeleo metálico cuando paso por baches. En pista lisa casi no se escucha."
        res2 = await orquestador.procesar_turno(session_id, msg2, mock_diag)
        assert res2["es_pregunta"], "Turno 2 debe emitir pregunta de componentes"
        assert any(k in res2["respuesta_texto"].lower() for k in ("bujes", "rótulas", "rotulas", "holgura"))

        # Turno 3: Usuario indica que NO ha revisado y NO sabe cómo comprobar holgura
        msg3 = "No, todavía no los he revisado y no sé bien cómo comprobar si tienen holgura."
        res3 = await orquestador.procesar_turno(session_id, msg3, mock_diag)

        # 1. CarBot NO debe saltar a OBD-II
        assert "obd" not in res3["respuesta_texto"].lower(), "No debe saltar a OBD-II en suspensión puramente mecánica"
        assert "escáner" not in res3["respuesta_texto"].lower()
        assert "check engine" not in res3["respuesta_texto"].lower()

        # 2. CarBot debe ofrecer procedimiento seguro / Plan B observable
        assert res3["decision"] == "PLAN_B", "La decisión debe ser PLAN_B"
        assert any(
            k in res3["respuesta_texto"].lower()
            for k in ("sin levantar el vehículo", "vaivén", "clac-clac", "volante", "carrocería", "taller")
        ), "Debe presentar la comprobación segura sin levantar el vehículo o recomendación técnica"

    asyncio.run(_run())


def test_distincion_conceptual_cuatro_estados() -> None:
    """Verifica que NO_REVISADO, NO_SABE_REALIZAR_PRUEBA, HERRAMIENTA_NO_DISPONIBLE y RESULTADO_NEGATIVO se distingan."""
    estado = ConversationState(session_id="test-cuatro-estados", case_id="case-4e")
    estado.registrar_pregunta(
        intent=QuestionIntent.COMPONENTE_REVISADO,
        texto="¿Has podido revisar si los bujes de trapecios o las rótulas tienen holgura visible?",
    )

    # 1. NO_SABE_REALIZAR_PRUEBA
    interp_no_sabe = InterpreteRespuestasCortas.interpretar(
        estado, "No, todavía no los he revisado y no sé bien cómo comprobar si tienen holgura."
    )
    assert interp_no_sabe is not None
    assert interp_no_sabe["categoria_respuesta"] == "NO_SABE_REALIZAR_PRUEBA"
    assert interp_no_sabe["estado"] == FactState.NO_SABE_REALIZAR.value
    assert interp_no_sabe["no_revisado"] is True

    # 2. NO_REVISADO puro (sin declarar falta de técnica ni herramientas)
    estado_2 = ConversationState(session_id="test-no-rev", case_id="case-nr")
    estado_2.registrar_pregunta(
        intent=QuestionIntent.COMPONENTE_REVISADO,
        texto="¿Has podido revisar si los bujes de trapecios o las rótulas tienen holgura visible?",
    )
    interp_no_rev = InterpreteRespuestasCortas.interpretar(estado_2, "No, todavía no los he revisado.")
    assert interp_no_rev is not None
    assert interp_no_rev["categoria_respuesta"] == "NO_REVISADO"

    # 3. HERRAMIENTA_NO_DISPONIBLE
    estado_3 = ConversationState(session_id="test-sin-herr", case_id="case-sh")
    estado_3.registrar_pregunta(
        intent=QuestionIntent.DISPONIBILIDAD_HERRAMIENTA,
        texto="¿Dispones de multímetro automotriz para medir el voltaje?",
    )
    interp_herr = InterpreteRespuestasCortas.interpretar(estado_3, "No tengo multímetro ni herramientas.")
    assert interp_herr is not None
    assert interp_herr["categoria_respuesta"] in ("HERRAMIENTA_INDISPONIBLE", "NEGACION")
    assert estado_3.herramientas_no_disponibles

    # 4. RESULTADO_NEGATIVO (sí se realizó la prueba y no hay holgura)
    estado_4 = ConversationState(session_id="test-res-neg", case_id="case-rn")
    estado_4.registrar_pregunta(
        intent=QuestionIntent.COMPONENTE_REVISADO,
        texto="¿Has podido revisar si los bujes de trapecios o las rótulas tienen holgura visible?",
    )
    interp_neg = InterpreteRespuestasCortas.interpretar(estado_4, "Ya los revisé y no tienen holgura, están firmes.")
    assert interp_neg is not None
    assert interp_neg["categoria_respuesta"] == "RESULTADO_NEGATIVO"
    assert interp_neg["estado"] == FactState.AUSENTE_NEGADO.value


def test_plan_b_seis_dominios_sin_herramientas() -> None:
    """Verifica la generación de alternativas observables seguras en los 6 dominios principales."""
    # 1. Suspensión: no sabe cómo revisar holgura
    estado_susp = ConversationState(session_id="dom-susp", case_id="c-susp")
    estado_susp.dominio_probable = "SUSPENSION"
    pb_susp = GestorPlanB.obtener_plan_b_por_inspeccion("SUSPENSION", "revisar holgura de bujes", estado_susp)
    assert pb_susp is not None
    assert "vaivén" in pb_susp[1].lower() or "sin levantar el vehículo" in pb_susp[1].lower()

    # 2. Frenos: no sabe cómo medir espesor de discos
    estado_frenos = ConversationState(session_id="dom-frenos", case_id="c-frenos")
    estado_frenos.dominio_probable = "FRENOS"
    pb_frenos = GestorPlanB.obtener_plan_b_por_inspeccion("FRENOS", "medir espesor del disco", estado_frenos)
    assert pb_frenos is not None
    assert "linterna" in pb_frenos[1].lower() or "surcos" in pb_frenos[1].lower()

    # 3. Motor: no sabe cómo comprobar chispa
    estado_motor = ConversationState(session_id="dom-motor", case_id="c-motor")
    pb_motor = GestorPlanB.obtener_plan_b_por_inspeccion("MARCHA_MOTOR", "comprobar la chispa en bujías", estado_motor)
    assert pb_motor is not None
    assert "revoluciones" in pb_motor[1].lower() or "rpm" in pb_motor[1].lower() or "olor" in pb_motor[1].lower()

    # 4. Eléctrico: no tiene multímetro
    estado_elec = ConversationState(session_id="dom-elec", case_id="c-elec")
    estado_elec.bloquear_herramienta("multimetro")
    pb_elec = GestorPlanB.obtener_plan_b_para_falla("Batería defectuosa o descargada", estado_elec)
    assert pb_elec is not None
    assert "luces del tablero" in pb_elec[1].lower()

    # 5. Transmisión: no sabe revisar ATF
    estado_trans = ConversationState(session_id="dom-trans", case_id="c-trans")
    pb_trans = GestorPlanB.obtener_plan_b_por_inspeccion("TRANSMISION", "nivel y estado de aceite atf", estado_trans)
    assert pb_trans is not None
    assert "varilla" in pb_trans[1].lower() or "papel blanco" in pb_trans[1].lower()

    # 6. Climatización: no sabe comprobar compresor
    estado_clima = ConversationState(session_id="dom-clima", case_id="c-clima")
    pb_clima = GestorPlanB.obtener_plan_b_por_inspeccion("CLIMATIZACION", "compresor del aire", estado_clima)
    assert pb_clima is not None
    assert "clic" in pb_clima[1].lower() or "a/c" in pb_clima[1].lower()


def test_obd2_control_positivo_vs_negativo() -> None:
    """Verifica que OBD-II sea admisible con evidencia electrónica y descartado sin ella en avería mecánica."""
    # Control Negativo: suspensión mecánica pura sin testigos ni hipótesis electrónica
    estado_mecanico = ConversationState(session_id="obd-neg", case_id="c-obd-neg")
    estado_mecanico.dominio_probable = "SUSPENSION"
    estado_mecanico.top3_actual = [
        {"falla": "Bujes de trapecio deteriorados", "probabilidad": 0.70},
        {"falla": "Rótula con holgura", "probabilidad": 0.20},
    ]
    txt_dtc = "Para mayor precisión: ¿se ha conectado un escáner automotriz OBD-II o el tablero muestra el Check Engine?"
    compatible_neg, motivo_neg = CompatibilidadPreguntas.validar(QuestionIntent.CODIGO_DTC, txt_dtc, estado_mecanico)
    assert not compatible_neg, "OBD-II no debe ser compatible en suspensión mecánica sin justificación electrónica"
    assert motivo_neg == "SIN_JUSTIFICACION_ELECTRONICA"

    # Control Positivo 1: suspensión con testigo ABS encendido
    estado_abs = ConversationState(session_id="obd-pos-abs", case_id="c-obd-pos1")
    estado_abs.dominio_probable = "SUSPENSION"
    estado_abs.registrar_hecho("testigo_tablero", "luz de ABS encendida", categoria="dtc", tipo=FactType.CONDICION)
    compatible_abs, _ = CompatibilidadPreguntas.validar(QuestionIntent.CODIGO_DTC, txt_dtc, estado_abs)
    assert compatible_abs, "OBD-II debe ser admisible si hay testigo ABS"

    # Control Positivo 2: motor con Check Engine
    estado_motor = ConversationState(session_id="obd-pos-motor", case_id="c-obd-pos2")
    estado_motor.dominio_probable = "MARCHA_MOTOR"
    compatible_motor, _ = CompatibilidadPreguntas.validar(QuestionIntent.CODIGO_DTC, txt_dtc, estado_motor)
    assert compatible_motor, "OBD-II debe ser admisible en dominio de motor"

    # Control Positivo 3: DTC observado en el estado
    estado_dtc = ConversationState(session_id="obd-pos-dtc", case_id="c-obd-pos3")
    estado_dtc.dominio_probable = "SUSPENSION"
    estado_dtc.dtc_status = DtcStatus.DTC_OBSERVADO
    compatible_dtc, _ = CompatibilidadPreguntas.validar(QuestionIntent.CODIGO_DTC, txt_dtc, estado_dtc)
    assert compatible_dtc, "OBD-II debe ser admisible si existe DTC observado"
