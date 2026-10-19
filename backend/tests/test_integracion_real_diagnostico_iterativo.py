"""Pruebas de integración real del ciclo iterativo multivuelta de CarBot.

Sin mocks en inferencia de Machine Learning, FAISS/RAG ni reglas de fusión.
Utiliza GestorDiagnostico real con artefactos de producción oficiales:
- TF-IDF 32,708 dimensiones (vectorizador_c1.pkl).
- Clasificador Nivel 2 SVM con calibración de probabilidad (modelo_diagnostico_c1.pkl).
- Clasificador Nivel 1 Macro-Sistemas (modelo_sistema_c1.pkl).
- Índice vectorial FAISS de procedimientos de taller OEM (indice_faiss.index).
"""

from __future__ import annotations

import pytest

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.mark.asyncio
async def test_integracion_real_multivuelta_svm_rag_fallback_transparente():
    """Valida el ciclo conversacional completo multivuelta en entorno real:

    Turno 1: Inferencia real de dirección con SVM + recuperación real FAISS/RAG.
    Turno 2: Respuesta 'ninguna coincide'; verificación de no descarte ni alteración artificial.
    Turno 3: Aporte de nueva evidencia técnica con reevaluación real del SVM y actualización de hipótesis.
    Reporte transparente de llm_usado=False en ausencia de API keys.
    """
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repo)
    gestor = GestorDiagnostico()

    session_id = "ses-int-real-001"

    # --- Turno 1: Síntoma inicial de dirección asistida ---
    texto_t1 = "Toyota Yaris 2018 gasolina, chillido agudo al girar el timon"
    res_t1 = await orquestador.procesar_turno(session_id, texto_t1, gestor)

    assert res_t1.get("decision") == "DIAGNOSTICAR"
    top3_t1 = res_t1.get("top3_actual", [])
    assert len(top3_t1) >= 1
    # SVM Nivel 2 infiere falla de dirección con alta probabilidad real
    falla_t1 = top3_t1[0]["falla"]
    prob_t1 = top3_t1[0]["probabilidad"]
    assert "cremallera" in falla_t1.lower() or "direccion" in falla_t1.lower()
    assert prob_t1 > 0.50
    assert top3_t1[0]["origen_probabilidad"] == "SVM"

    # FAISS/RAG real recupera manual de taller OEM de cremallera
    dto_t1 = res_t1.get("dto")
    assert dto_t1 is not None
    assert "CREMALLERA" in dto_t1.titulo_manual.upper()
    assert dto_t1.similitud_rag > 0.0

    # Trazabilidad LLM: Documentar explícitamente ejecución en fallback sin API key
    assert dto_t1.llm_usado is False

    # --- Turno 2: Mecánico responde 'ninguna coincide' ---
    texto_t2 = "ninguna coincide"
    res_t2 = await orquestador.procesar_turno(session_id, texto_t2, gestor)

    assert res_t2.get("decision") == "PREGUNTAR"
    resp_t2 = res_t2.get("respuesta_texto", "").lower()
    assert "posibilidades abiertas" in resp_t2 or "comprobaci" in resp_t2 or "descartar" in resp_t2

    # Estado de la sesión preserva hipótesis previa sin descartes artificiales
    estado_t2 = await repo.get_session(session_id)
    assert estado_t2 is not None
    assert len(estado_t2.top3_actual) >= 1
    assert estado_t2.top3_actual[0]["falla"] == falla_t1
    assert estado_t2.top3_actual[0]["probabilidad"] == prob_t1

    # --- Turno 3: Mecánico aporta nueva evidencia técnica de suspensión ---
    texto_t3 = "Al pasar por baches tiene amortiguadores rotos con bujes de suspension gastados"
    res_t3 = await orquestador.procesar_turno(session_id, texto_t3, gestor)

    assert res_t3.get("decision") == "DIAGNOSTICAR"
    top3_t3 = res_t3.get("top3_actual", [])
    assert len(top3_t3) >= 1

    # Reevaluación real del SVM: el top 1 ya no es cremallera de dirección
    falla_t3 = top3_t3[0]["falla"]
    prob_t3 = top3_t3[0]["probabilidad"]
    assert falla_t3 != falla_t1
    assert top3_t3[0]["origen_probabilidad"] == "SVM"
    assert prob_t3 > 0.0

    # Cambio de ranking registrado fielmente
    assert res_t3.get("cambio_ranking") is True
    assert res_t3.get("top3_previo", [])[0]["falla"] == falla_t1


@pytest.mark.asyncio
async def test_distincion_verificable_llm_autorizado_vs_fallback_determinista():
    """Demuestra la trazabilidad técnica que distingue la generación de respuesta:

    - Caso Fallback: llm_usado=False cuando el proveedor LLM no está disponible.
    - Caso Autorizado: llm_usado=True cuando el adaptador LLM genera la respuesta con respaldo RAG.
    """
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repo)
    gestor = GestorDiagnostico()

    session_id_fallback = "ses-diag-fallback"
    res_fb = await orquestador.procesar_turno(
        session_id_fallback,
        "Toyota Yaris 2018 gasolina, chillido agudo al girar el timon",
        gestor,
    )
    dto_fb = res_fb.get("dto")
    assert dto_fb is not None
    assert dto_fb.llm_usado is False
    assert dto_fb.llm_modelo is None

    # Simular adaptador LLM autorizado para pruebas
    session_id_llm = "ses-diag-llm"
    orig_generar = gestor._generar_respuesta_con_metadatos

    def mock_generar_autorizado(*args, **kwargs):
        return (
            "Explicación técnica validada contra manual OEM para cremallera de dirección.",
            {"usado": True, "modelo": "gemini-1.5-flash", "tokens_entrada": 120, "tokens_salida": 65},
        )

    gestor._generar_respuesta_con_metadatos = mock_generar_autorizado
    try:
        res_llm = await orquestador.procesar_turno(
            session_id_llm,
            "Toyota Yaris 2018 gasolina, chillido agudo al girar el timon",
            gestor,
        )
        dto_llm = res_llm.get("dto")
        assert dto_llm is not None
        assert dto_llm.llm_usado is True
        assert dto_llm.llm_modelo == "gemini-1.5-flash"
        assert dto_llm.tokens_entrada == 120
        assert dto_llm.tokens_salida == 65
    finally:
        gestor._generar_respuesta_con_metadatos = orig_generar
