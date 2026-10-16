"""Suite de regresión para los defectos detectados por la auditoría independiente de Codex.

Cubre:
1. ARG-01: Seguridad ante fugas de combustible con negación parcial por cláusula.
2. ARG-02: Negación o mención ambigua de nuevo diagnóstico sin reinicio de case_id.
3. ARG-03: Polaridad de síntomas negados y prohibición de inventar ubicaciones ('delanteras' vs 'traseras').
4. ARG-04: Validación estricta de rango en selección numérica de hipótesis (rechazo de '3' cuando hay 1 opción).
"""

from __future__ import annotations

import pytest

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
) -> None:
    """Una negación parcial en otra cláusula jamás debe suprimir una alerta crítica de fuga de gasolina."""
    sev, banner = PoliticaSeguridad.evaluar_severidad(mensaje_peligroso, "")
    assert sev == SeveridadSeguridad.CRITICAL_STOP
    assert banner == BANNER_COMBUSTIBLE


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



