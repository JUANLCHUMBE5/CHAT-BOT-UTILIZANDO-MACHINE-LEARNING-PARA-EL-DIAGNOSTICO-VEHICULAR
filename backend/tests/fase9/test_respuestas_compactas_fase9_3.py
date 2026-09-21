"""Pruebas automatizadas de la Fase 9.3: Respuestas conversacionales compactas para WhatsApp.

Verifica:
1. Estructura compacta visual canónica (Top-1, Top-2, Top-3 con confianza real).
2. Presencia de acción prioritaria concreta ('🛠️ Primero revisa').
3. Presencia de pregunta contextual de seguimiento.
4. Ausencia total de textos o símbolos internos (FactState, EvidenceLevel, question_intent, Límite alcanzado).
5. Flujo de profundización técnica bajo demanda ('más detalles' / 'cómo lo reviso').
6. Incorporación y refinamiento ante mediciones o descartes ('tiene 12.6 V', 'batería nueva').
7. Disponibilidad y preservación interna de la respuesta técnica completa en BD/DTO.
"""

from __future__ import annotations

import pytest

from src.core.conversacion.formateador_compacto import (
    FormateadorCompacto,
    _extraer_accion_prioritaria,
)
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.fixture
def gestor_real():
    return GestorDiagnostico()


@pytest.fixture
def orquestador():
    repo = InMemoryConversationRepository()
    return OrquestadorConversacion(repositorio=repo)


def test_formateador_compacto_estructura_basica():
    """Verifica que el formateador produzca la plantilla canónica sin filtrar nombres crudos."""
    top_hipotesis = [
        {"falla": "Bateria descargada o bornes sulfatados", "probabilidad": 0.784},
        {"falla": "En motor de arranque o solenoide defectuoso", "probabilidad": 0.152},
        {"falla": "Conexion electrica principal", "probabilidad": 0.064},
    ]

    salida = FormateadorCompacto.formatear_respuesta_diagnostico(
        top_hipotesis=top_hipotesis,
        sintoma_original="hace clac no prende",
    )

    assert "🔧 *Posibles causas*" in salida
    assert "1. Bateria descargada o bornes sulfatados — 78%" in salida
    assert "2. En motor de arranque o solenoide defectuoso — 15%" in salida
    assert "3. Conexion electrica principal — 6%" in salida
    assert "🛠️ *Primero revisa:*" in salida
    assert "¿Tienes multímetro para comprobar el voltaje?" in salida

    # Verificar ausencia estricta de textos internos
    assert "FactState" not in salida
    assert "EvidenceLevel" not in salida
    assert "question_intent" not in salida
    assert "sintoma_motor_no_arranca" not in salida
    assert "Límite de evaluación alcanzado" not in salida
    assert "porcentaje de acierto" not in salida.lower()


def test_formateador_compacto_maximo_tres_hipotesis():
    """Verifica que nunca se muestren más de 3 hipótesis en la respuesta."""
    top_hipotesis = [
        {"falla": "Falla 1", "probabilidad": 0.50},
        {"falla": "Falla 2", "probabilidad": 0.30},
        {"falla": "Falla 3", "probabilidad": 0.15},
        {"falla": "Falla 4", "probabilidad": 0.04},
        {"falla": "Falla 5", "probabilidad": 0.01},
    ]

    salida = FormateadorCompacto.formatear_respuesta_diagnostico(top_hipotesis)
    assert "1. Falla 1 — 50%" in salida
    assert "2. Falla 2 — 30%" in salida
    assert "3. Falla 3 — 15%" in salida
    assert "Falla 4" not in salida
    assert "Falla 5" not in salida


def test_accion_prioritaria_concisa():
    """Comprueba que la prueba prioritaria sea concisa y no un manual extenso."""
    accion_bat = _extraer_accion_prioritaria("Bateria descargada o bornes sulfatados")
    assert len(accion_bat) <= 140
    assert "voltaje" in accion_bat.lower() or "bornes" in accion_bat.lower()

    accion_freno = _extraer_accion_prioritaria("Desgaste de pastillas y zapatas de freno")
    assert len(accion_freno) <= 140
    assert "pastillas" in accion_freno.lower() or "espesor" in accion_freno.lower()


@pytest.mark.anyio
async def test_flujo_completo_respuesta_compacta_whatsapp(orquestador, gestor_real):
    """Verifica la respuesta diagnóstica normal y compacta para WhatsApp en el caso real."""
    session_id = "test_fase9_3_compacta"
    texto = "En la mañana arrancó normal. Ahora hace clac, no prende y las luces se ponen tenues cuando intento arrancar."

    res = await orquestador.procesar_turno(session_id, texto, gestor_real)

    assert res["status"] in ("completado", "diagnostico")
    assert res["decision"] == "DIAGNOSTICAR"

    # La respuesta para WhatsApp debe ser compacta
    resp_wapp = res["respuesta_texto"]
    assert "🔧 *Posibles causas*" in resp_wapp
    assert "1." in resp_wapp
    assert "🛠️ *Primero revisa:*" in resp_wapp
    assert "Límite de evaluación alcanzado" not in resp_wapp
    assert "EvidenceLevel" not in resp_wapp
    assert "FactState" not in resp_wapp

    # La respuesta técnica completa debe seguir disponible en el DTO interno
    dto = res["dto"]
    assert dto is not None
    assert dto.diagnostico_ml != ""
    assert dto.confianza_ml > 0.0
    assert len(dto.predicciones_ml) >= 1


@pytest.mark.anyio
async def test_solicitud_mas_detalles_recupera_rag(orquestador, gestor_real):
    """Verifica que al pedir 'más detalles' o 'cómo lo reviso' se devuelva el procedimiento paso a paso."""
    session_id = "test_fase9_3_detalles"
    texto_1 = "En la mañana arrancó normal. Ahora hace clac, no prende y las luces se ponen tenues cuando intento arrancar."
    await orquestador.procesar_turno(session_id, texto_1, gestor_real)

    # El usuario pide detalles (sin haber provisto DTC)
    texto_2 = "¿Cómo lo reviso paso a paso?"
    res_2 = await orquestador.procesar_turno(session_id, texto_2, gestor_real)

    assert res_2["status"] == "detalle"
    assert res_2["decision"] == "DETALLE"
    resp_det = res_2["respuesta_texto"]
    assert "📋 *Procedimiento de comprobación:" in resp_det
    assert "1." in resp_det
    assert "Si realizas un escaneo, algunos códigos relacionados que podrían aparecer son:" in resp_det
    assert "Código reportado por el escáner" not in resp_det
    assert "Deseas registrar el resultado" in resp_det


@pytest.mark.anyio
async def test_solicitud_mas_detalles_con_dtc_observado(orquestador, gestor_real):
    """Verifica que si existe DTC observado explícito, se muestre como código reportado por el escáner."""
    session_id = "test_fase9_3_dtc_obs"
    texto_1 = "Tengo código P0301 en escáner y el motor tiembla en ralentí"
    await orquestador.procesar_turno(session_id, texto_1, gestor_real)

    res_2 = await orquestador.procesar_turno(session_id, "más detalles", gestor_real)
    assert res_2["status"] == "detalle"
    resp_det = res_2["respuesta_texto"]
    assert "📡 *Código reportado por el escáner:* P0301" in resp_det
    assert "Si realizas un escaneo, algunos códigos relacionados" not in resp_det


@pytest.mark.anyio
async def test_refinamiento_tras_medicion_descarte(orquestador, gestor_real):
    """Verifica que una medición o descarte posterior se incorpore al estado sin perder el caso."""
    session_id = "test_fase9_3_refinamiento"
    texto_1 = "En la mañana arrancó normal. Ahora hace clac, no prende y las luces se ponen tenues cuando intento arrancar."
    res_1 = await orquestador.procesar_turno(session_id, texto_1, gestor_real)
    assert res_1["decision"] == "DIAGNOSTICAR"

    # Usuario reporta medición concreta
    texto_2 = "La batería tiene 12.6 V y está nueva, bornes limpios."
    res_2 = await orquestador.procesar_turno(session_id, texto_2, gestor_real)

    # 12.6 V en reposo no descarta una caída durante el arranque: el flujo
    # debe pedir la medición bajo carga antes de cerrar el diagnóstico.
    assert res_2["decision"] == "PREGUNTAR"
    resp_2 = res_2["respuesta_texto"]
    assert "arranque" in resp_2.lower()
    assert "multímetro" in resp_2.lower()

    # Verificar que el hecho de medición quedó registrado en el estado
    estado = await orquestador.repositorio.get_session(session_id)
    assert estado is not None
    assert any("12.6" in str(h.valor) for h in estado.hechos.values())
