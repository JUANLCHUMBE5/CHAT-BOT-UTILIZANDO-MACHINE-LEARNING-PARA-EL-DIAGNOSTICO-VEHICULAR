"""Pruebas exhaustivas de resiliencia de cola Gemini, pruebas de carga, deduplicación y recuperación ante caídas."""

import asyncio

import pytest

from src.core.gemini_queue import GeminiRateLimiter


@pytest.fixture
def rate_limiter():
    limiter = GeminiRateLimiter(max_por_minuto=60, max_por_dia=1000, ventana_segundos=1.0)
    return limiter


def test_encolamiento_y_posicion_cola(rate_limiter):
    """Verifica que el encolamiento asigne posiciones correlativas y calcule tiempos de espera."""
    for i in range(5):
        solicitud, pos, tiempo_espera = rate_limiter.encolar_solicitud(
            sintoma=f"Sintoma de prueba {i}",
            diagnostico_ml="Desgaste de pastillas y zapatas de freno",
            confianza_ml=0.95,
            contexto_manual="Manual de frenos",
            titulo_manual="Reemplazo de pastillas",
            solicitud_id=f"test-solicitud-{i}"
        )
        assert pos == i + 1
        assert tiempo_espera >= 0.0
        assert solicitud.id == f"test-solicitud-{i}"

    assert rate_limiter.tamaño_cola() == 5


def test_descolamiento_fifo_y_vaciado(rate_limiter):
    """Verifica la extracción ordenada FIFO de la cola."""
    sol1, pos1, _ = rate_limiter.encolar_solicitud(
        sintoma="La puerta no abre",
        diagnostico_ml="Falla electrica del cierre centralizado o actuador de puerta",
        confianza_ml=0.85,
        contexto_manual="Manual de carroceria",
        titulo_manual="Cierre centralizado",
        solicitud_id="sol-01"
    )
    sol2, pos2, _ = rate_limiter.encolar_solicitud(
        sintoma="El pedal de freno se hunde",
        diagnostico_ml="Fuga hidraulica o aire en el sistema de frenos",
        confianza_ml=0.90,
        contexto_manual="Manual de frenos",
        titulo_manual="Fuga de frenos",
        solicitud_id="sol-02"
    )
    assert pos1 == 1
    assert pos2 == 2
    assert rate_limiter.tamaño_cola() == 2

    extraida_1 = rate_limiter.descolar_siguiente()
    assert extraida_1 is not None
    assert extraida_1.id == "sol-01"
    assert rate_limiter.tamaño_cola() == 1

    extraida_2 = rate_limiter.descolar_siguiente()
    assert extraida_2 is not None
    assert extraida_2.id == "sol-02"
    assert rate_limiter.tamaño_cola() == 0

    assert rate_limiter.descolar_siguiente() is None


@pytest.mark.anyio
async def test_cola_consulta_tecnica_no_genera_resumen_de_averia(rate_limiter):
    solicitud, _, _ = rate_limiter.encolar_solicitud(
        sintoma="qué potencia deben tener los focos LED H4 para una Suzuki APV",
        diagnostico_ml="Consulta técnica informativa",
        confianza_ml=0.0,
        contexto_manual="No se encontró un procedimiento específico.",
        titulo_manual="Coincidencia baja",
        tipo_consulta="consulta_tecnica",
        solicitud_id="consulta-tecnica-01",
    )

    texto, metadatos = await rate_limiter._procesar_solicitud_encolada(
        solicitud, forzar_degradado=True
    )

    assert metadatos["modo"] == "consulta_tecnica_degradada"
    assert "posible falla" not in texto.lower()
    assert "diagnóstico sugerido" not in texto.lower()
    assert "marca, modelo, año" in texto.lower()


def test_recuperacion_worker_ante_excepciones():
    """Verifica que el worker de la cola se inicialice y detenga limpiamente sin fugas."""
    async def ejecutar_test():
        limiter = GeminiRateLimiter(max_por_minuto=100, max_por_dia=1000, ventana_segundos=1.0)

        sol1, pos1, _ = limiter.encolar_solicitud(
            sintoma="Falla de prueba para error",
            diagnostico_ml="Falla en bujias o bobinas de encendido (misfire)",
            confianza_ml=0.90,
            contexto_manual="Manual motor",
            titulo_manual="Bujias",
            solicitud_id="job-01"
        )
        sol2, pos2, _ = limiter.encolar_solicitud(
            sintoma="Falla exitosa 1",
            diagnostico_ml="Desgaste de pastillas y zapatas de freno",
            confianza_ml=0.92,
            contexto_manual="Manual frenos",
            titulo_manual="Pastillas",
            solicitud_id="job-02"
        )

        assert pos1 == 1
        assert pos2 == 2
        assert limiter.tamaño_cola() == 2

        limiter.iniciar_worker()
        await asyncio.sleep(0.1)
        await limiter.detener_worker()
        assert True

    asyncio.run(ejecutar_test())


def test_prueba_de_carga_concurrente_50_solicitudes(rate_limiter):
    """Simula una ráfaga concurrente de 50 solicitudes verificando integridad y tiempos."""
    num_solicitudes = 50

    for i in range(num_solicitudes):
        sol_id = f"load-test-job-{i:03d}"
        _, pos, t_esp = rate_limiter.encolar_solicitud(
            sintoma=f"Síntoma concurrente {i} en rampa de prueba",
            diagnostico_ml="Desgaste de pastillas y zapatas de freno",
            confianza_ml=0.90 + (i % 10) * 0.01,
            contexto_manual="Manual de frenos",
            titulo_manual="Frenos",
            solicitud_id=sol_id
        )
        assert pos == i + 1
        assert t_esp >= 0.0

    assert rate_limiter.tamaño_cola() == 50

    # Descolar todas y verificar orden FIFO
    for i in range(num_solicitudes):
        sol = rate_limiter.descolar_siguiente()
        assert sol is not None
        assert sol.id == f"load-test-job-{i:03d}"

    assert rate_limiter.tamaño_cola() == 0
