"""Suite de regresión para los 5 defectos detectados por la auditoría independiente de Codex.

Cubre:
1. ARG-01: Seguridad ante fugas de combustible con negación parcial por cláusula.
2. ARG-02: Negación o mención ambigua de nuevo diagnóstico sin reinicio de case_id.
3. ARG-03: Polaridad de síntomas negados y prohibición de inventar ubicaciones ('delanteras' vs 'traseras').
4. ARG-04: Validación estricta de rango en selección numérica de hipótesis (rechazo de '3' cuando hay 1 opción).
5. ARG-05 / ARG-06: Evaluaciones de continuidad, aislamiento de sesiones y protecciones en Laboratorio CarBot.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.core.conversacion.detector_polaridad import DetectorPolaridad
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState, FactState, QuestionIntent
from src.core.conversacion.respuestas_cortas.interprete_intenciones import interpretar_respuesta_corta
from src.core.diagnostico.politica_seguridad import (
    BANNER_COMBUSTIBLE,
    PoliticaSeguridad,
    SeveridadSeguridad,
)
from src.core.parser.message_parser import IntentType, SinglePassMessageParser
from src.interfaces.api.v1.endpoints.laboratorio_local.app import create_laboratory_app

app = create_laboratory_app()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from src.config import settings
    from src.core.security import crear_jwt_token

    monkeypatch.setattr(settings, "enable_laboratory", True)
    monkeypatch.setattr(settings, "environment", "test")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setenv("CARBOT_BLOCK_DOTENV", "true")
    global app
    app = create_laboratory_app()
    token = crear_jwt_token(usuario_id="00000000-0000-0000-0000-000000000021")
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


# ==============================================================================
# 1. DEFECTO ARG-01: SEGURIDAD ANTE FUGAS DE COMBUSTIBLE CON NEGACIÓN PARCIAL
# ==============================================================================


@pytest.mark.parametrize(
    "mensaje_peligroso",
    [
        "No hay fuga en el tanque, pero la línea de gasolina rota chorrea gasolina.",
        "Sin fugas en el riel, aunque una manguera de gasolina rota pierde gasolina.",
        "No detecté fuga en la bomba; sin embargo, gotea gasolina cerca del escape y huele fuerte a gasolina.",
        "No presenta fuga de agua, pero bota gasolina por la línea inferior.",
    ],
)
def test_arg01_fuga_combustible_con_negacion_parcial_activa_critical_stop(
    mensaje_peligroso: str,
    client: TestClient,
) -> None:
    """Una negación parcial en otra cláusula jamás debe suprimir una alerta crítica de fuga de gasolina."""
    sev, banner = PoliticaSeguridad.evaluar_severidad(mensaje_peligroso, "")
    assert sev == SeveridadSeguridad.CRITICAL_STOP
    assert banner == BANNER_COMBUSTIBLE

    resp = client.post(
        "/api/v1/laboratorio/mensaje",
        json={"session_id": "test_arg01_fuel_safety", "mensaje": mensaje_peligroso},
    )
    assert resp.status_code == 200
    data = resp.json()
    texto_resp = data["respuesta_texto"].lower()
    assert "peligro crítico" in texto_resp or "no intente arrancar" in texto_resp
    assert "incendio" in texto_resp

    comprobaciones = {c["criterio"]: c["resultado"] for c in data["comprobaciones"]}
    assert comprobaciones.get("Advertencia de seguridad física (frenos/suspensión/térmico)") == "APROBADO"


def test_arg01_negacion_total_fuga_combustible_no_dispara_falso_positivo() -> None:
    """Cuando todas las menciones de fuga/olor están negadas, no debe activar CRITICAL_STOP."""
    sev, banner = PoliticaSeguridad.evaluar_severidad(
        "No hay fuga de gasolina ni olor fuerte a gasolina en el vehículo.", ""
    )
    assert sev == SeveridadSeguridad.NORMAL_DIAGNOSTIC
    assert banner is None


# ==============================================================================
# 2. DEFECTO ARG-02: NEGACIÓN DE NUEVO DIAGNÓSTICO NO REINICIA EL CASO
# ==============================================================================


@pytest.mark.parametrize(
    "frase_no_reinicio",
    [
        "No quiero iniciar un nuevo diagnóstico, seguimos con el Toyota Yaris ABC123.",
        "Consulta la memoria. No generes un nuevo diagnóstico.",
        "Todavía no abras un nuevo caso, sigue con el mismo vehículo.",
        "No sé si iniciar un nuevo diagnóstico o continuar con este caso.",
        "Tampoco quiero empezar otro diagnóstico ahora.",
        "Sin generar un nuevo diagnóstico, dime qué síntomas tienes registrados.",
    ],
)
def test_arg02_frases_negadas_o_ambiguas_no_solicitan_reinicio(frase_no_reinicio: str) -> None:
    """Distinguir intención afirmativa vs negativa o ambigua al mencionar nuevo diagnóstico."""
    assert ExtractorHechos.es_reinicio_solicitado(frase_no_reinicio) is False
    parsed = SinglePassMessageParser.parse(frase_no_reinicio)
    assert parsed.es_cambio_caso is False
    assert parsed.intencion != IntentType.CAMBIO_CASO


def test_arg02_laboratorio_conserva_case_id_ante_negacion_de_nuevo_diagnostico(
    client: TestClient,
) -> None:
    """Reproduce el caso exacto de Codex en el laboratorio verificando conservación de case_id y síntomas."""
    session_id = "test_arg02_continuity_no_reset"

    r1 = client.post(
        "/api/v1/laboratorio/mensaje",
        json={
            "session_id": session_id,
            "mensaje": (
                "Mi vehículo es un Toyota Yaris 2020, placa ABC123. "
                "Cuando freno escucho un chirrido en las ruedas delanteras y siento que el pedal vibra."
            ),
        },
    )
    assert r1.status_code == 200
    d1 = r1.json()
    case_id_original = d1["case_id"]
    assert case_id_original is not None
    assert len(d1["sintomas_confirmados"]) >= 2

    # Turno 2: Negación explícita de nuevo diagnóstico
    r2 = client.post(
        "/api/v1/laboratorio/mensaje",
        json={
            "session_id": session_id,
            "mensaje": "No quiero iniciar un nuevo diagnóstico, seguimos con el Toyota Yaris ABC123.",
        },
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["case_id"] == case_id_original
    assert d2["placa"] in ("ABC123", "ABC-123")
    assert len(d2["sintomas_confirmados"]) >= 2
    comp_t2 = {c["criterio"]: c["resultado"] for c in d2["comprobaciones"]}
    assert comp_t2.get("Aislamiento estricto de case_id") == "APROBADO"

    # Turno 3: Consulta de memoria prohibiendo generar nuevo diagnóstico
    r3 = client.post(
        "/api/v1/laboratorio/mensaje",
        json={
            "session_id": session_id,
            "mensaje": "Consulta la memoria. No generes un nuevo diagnóstico.",
        },
    )
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["case_id"] == case_id_original
    assert d3["confianza_ml"] == 0.0
    assert "no aplica" in (d3["diagnostico_ml"] or "").lower()
    assert len(d3["sintomas_confirmados"]) >= 2
    comp_t3 = {c["criterio"]: c["resultado"] for c in d3["comprobaciones"]}
    assert comp_t3.get("Aislamiento estricto de case_id") == "APROBADO"


# ==============================================================================
# 3. DEFECTO ARG-03: SÍNTOMAS NEGADOS Y PROHIBICIÓN DE INVENTAR UBICACIONES
# ==============================================================================


@pytest.mark.parametrize(
    "frase_negada,campo_esperado_negado,valor_esperado",
    [
        ("No hay chirrido en ruedas traseras.", "sintoma_chirrido_ruedas", "chirrido en ruedas traseras"),
        (
            "No escucho golpes metálicos en la suspensión trasera.",
            "sintoma_golpes_suspension",
            "golpes metálicos en la suspensión trasera",
        ),
        ("No siento vibraciones en el volante.", "sintoma_vibracion_volante", "vibración en el volante"),
    ],
)
def test_arg03_sintomas_negados_nunca_se_registran_como_confirmados(
    frase_negada: str,
    campo_esperado_negado: str,
    valor_esperado: str,
) -> None:
    """Reproduce exactamente las 3 oraciones negadas de la auditoría de Codex."""
    polaridades = DetectorPolaridad.extraer_sintomas(frase_negada)
    assert all(st == FactState.AUSENTE_NEGADO for _, _, st in polaridades)

    estado = ConversationState(session_id="arg03")
    ExtractorHechos.extraer_y_actualizar(estado, frase_negada)

    confirmados = [
        (k, h.valor)
        for k, h in estado.hechos.items()
        if h.estado == FactState.CONFIRMADO and h.categoria in ("sintoma", "ubicacion")
    ]
    assert confirmados == [], f"No debía confirmarse ningún síntoma ni ubicación en '{frase_negada}': {confirmados}"

    hecho_especifico = estado.obtener_hecho(campo_esperado_negado)
    assert hecho_especifico is not None
    assert hecho_especifico.estado == FactState.AUSENTE_NEGADO
    assert hecho_especifico.valor == valor_esperado
    assert "delanter" not in str(hecho_especifico.valor).lower()


def test_arg03_preserva_ubicacion_exacta_sin_inventar_delanteras() -> None:
    """Verifica que 'ruedas traseras' o 'ruedas' sin posición nunca inventen 'delanteras'."""
    estado_tras = ConversationState(session_id="arg03_tras")
    ExtractorHechos.extraer_y_actualizar(estado_tras, "Siento chirrido en ruedas traseras al frenar.")
    h_tras = estado_tras.obtener_hecho("sintoma_chirrido_ruedas")
    assert h_tras is not None
    assert h_tras.estado == FactState.CONFIRMADO
    assert h_tras.valor == "chirrido en ruedas traseras"

    estado_gen = ConversationState(session_id="arg03_gen")
    ExtractorHechos.extraer_y_actualizar(estado_gen, "Escucho un chirrido en las ruedas.")
    h_gen = estado_gen.obtener_hecho("sintoma_chirrido_ruedas")
    assert h_gen is not None
    assert h_gen.estado == FactState.CONFIRMADO
    assert h_gen.valor == "chirrido en ruedas"
    assert "delanter" not in str(h_gen.valor).lower()


# ==============================================================================
# 4. DEFECTO ARG-04: VALIDACIÓN ESTRICTA DE SELECCIÓN NUMÉRICA DE HIPÓTESIS
# ==============================================================================


@pytest.mark.parametrize(
    "entrada_invalida, indice_esperado",
    [
        ("3", 3),
        ("la 2", 2),
        ("2", 2),
        ("la 3", 3),
    ],
)
def test_arg04_interprete_rechaza_opcion_fuera_de_rango_cuando_solo_existe_una_hipotesis(
    entrada_invalida: str,
    indice_esperado: int,
) -> None:
    """Reproduce el caso de Codex (adversarial.py) y verifica que '3' y 'la 2' sean rechazadas sin clamping."""
    s = ConversationState(session_id="numeric")
    s.iniciar_nuevo_caso()
    s.top3_actual = [{"falla": "Discos de freno alabeados", "probabilidad": 0.3}]
    s.preguntas_realizadas = [{
        "intent": QuestionIntent.DISCRIMINACION_TOP3.value,
        "texto": "Selecciona 1",
        "case_id": s.case_id,
        "hipotesis": ["Discos de freno alabeados"],
    }]
    r = interpretar_respuesta_corta(s, entrada_invalida)
    assert r is not None
    assert r.get("categoria_respuesta") == "OPCION_NUMERICA_FUERA_DE_RANGO"
    assert r.get("indice_opcion") == indice_esperado
    assert r.get("total_opciones") == 1


@pytest.mark.parametrize("entrada_fuera_rango", ["3", "la 2"])
def test_arg04_laboratorio_rechaza_opcion_fuera_de_rango_sin_clamping(
    client: TestClient,
    entrada_fuera_rango: str,
) -> None:
    """Verifica en el endpoint que responder '3' o 'la 2' con 1 sola opción no seleccione la primera."""
    session_id = f"test_arg04_single_hypo_{hash(entrada_fuera_rango)}"
    # La aplicación independiente empieza vacía; no depender de otra prueba.
    inicial = client.post("/api/v1/laboratorio/mensaje", json={"session_id": session_id, "mensaje": "Hola"})
    assert inicial.status_code == 200
    gestor_lab = getattr(app.state, "gestor_laboratorio", None)
    assert gestor_lab is not None
    sesion = gestor_lab.session_manager.obtener_o_crear_sesion(f"lab::{session_id}")
    estado = sesion.conversation_state
    estado.iniciar_nuevo_caso()
    estado.top3_actual = [{"falla": "Discos de freno alabeados", "probabilidad": 0.3}]
    estado.preguntas_realizadas = [{
        "intent": QuestionIntent.DISCRIMINACION_TOP3.value,
        "texto": "¿Cuál de estas opciones describe mejor el fallo? 1) Discos de freno alabeados",
        "case_id": estado.case_id,
        "hipotesis": ["Discos de freno alabeados"],
    }]
    estado.falla_principal = None

    # Enviar entrada fuera de rango ('3' o 'la 2')
    r2 = client.post(
        "/api/v1/laboratorio/mensaje",
        json={"session_id": session_id, "mensaje": entrada_fuera_rango},
    )
    assert r2.status_code == 200
    d2 = r2.json()
    resp_l = d2["respuesta_texto"].lower()
    assert "no está disponible" in resp_l or "fuera de rango" in resp_l
    assert "seleccionaste provisionalmente" not in resp_l
    assert d2["confianza_ml"] == 0.0
    assert estado.falla_principal is None

    # Enviar '1' (válido, dentro de rango)
    r3 = client.post(
        "/api/v1/laboratorio/mensaje",
        json={"session_id": session_id, "mensaje": "1"},
    )
    assert r3.status_code == 200
    d3 = r3.json()
    assert "seleccionaste provisionalmente la opción 1" in d3["respuesta_texto"].lower()
    assert "discos de freno alabeados" in d3["respuesta_texto"].lower()



# ==============================================================================
# 5. DEFECTO ARG-05 / ARG-06: AISLAMIENTO Y COMPROBACIONES DEL LABORATORIO
# ==============================================================================


def test_arg05_toyota_replay_sin_falsos_fallidos_de_continuidad(client: TestClient) -> None:
    """En el caso Toyota de 3 turnos del mismo vehículo, ningún turno debe marcar FALLIDO en case_id."""
    resp = client.post("/api/v1/laboratorio/ejecutar-caso/toyota")
    assert resp.status_code == 200
    resultados = resp.json()["resultados"]
    assert len(resultados) == 3

    for paso in resultados:
        comprobaciones = paso["respuesta"]["comprobaciones"]
        fallidas = [c for c in comprobaciones if c["resultado"] == "FALLIDO"]
        assert fallidas == [], f"Turno {paso['turno']} presentó comprobaciones FALLIDAS: {fallidas}"


def test_arg06_aislamiento_entre_session_manager_productivo_y_laboratorio(client: TestClient) -> None:
    """Verifica que las sesiones del laboratorio no contaminen el SessionManager productivo."""
    sid_compartido = "sesion_aislamiento_prod_vs_lab"
    resp = client.post(
        "/api/v1/laboratorio/mensaje",
        json={
            "session_id": sid_compartido,
            "mensaje": "Toyota Yaris 2020 placa ABC123, chirrido en ruedas delanteras al frenar.",
        },
    )
    assert resp.status_code == 200

    gestor_prod = getattr(app.state, "gestor_diagnostico", None)
    gestor_lab = getattr(app.state, "gestor_laboratorio", None)
    assert gestor_lab is not None
    if gestor_prod is not None:
        assert gestor_prod.session_manager is not gestor_lab.session_manager
        assert sid_compartido not in gestor_prod.session_manager._sesiones
        assert f"lab::{sid_compartido}" not in gestor_prod.session_manager._sesiones

    # Validación de formato de session_id malicioso
    resp_invalido = client.post(
        "/api/v1/laboratorio/mensaje",
        json={"session_id": "../traversal/malicioso", "mensaje": "Hola"},
    )
    assert resp_invalido.status_code == 400

