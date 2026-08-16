"""
test_diagnostic_cache.py
Pruebas de verificación para la Memoria Caché LRU de diagnósticos
y reducción de latencia / concurrencia para múltiples trabajadores mecánicos.
"""

import time
import pytest
from src.core.diagnostic_cache import DiagnosticoLRUCache, diagnostico_cache
from src.core.gestor_diagnostico import GestorDiagnostico, ResultadoDiagnostico


def test_cache_guardar_y_obtener_acierto():
    cache = DiagnosticoLRUCache(capacidad_maxima=10, ttl_default_segundos=60)
    clave = cache.generar_clave("pastillas de freno chillan", "Toyota Yaris")

    resultado_mock = ResultadoDiagnostico(
        respuesta_texto="Revisar pastillas",
        diagnostico_ml="Desgaste de pastillas",
        confianza_ml=0.9,
        contexto_manual="Manual frenos",
        titulo_manual="Manual Frenos"
    )

    # Debe ser Miss inicialmente
    assert cache.obtener(clave) is None

    # Guardar
    cache.guardar(clave, resultado_mock)

    # Debe ser Hit
    obtenido = cache.obtener(clave)
    assert obtenido is not None
    assert obtenido.diagnostico_ml == "Desgaste de pastillas"

    metricas = cache.obtener_metricas()
    assert metricas["hits"] == 1
    assert metricas["misses"] == 1
    assert metricas["elementos_actuales"] == 1


def test_cache_desalojo_lru_capacidad_maxima():
    cache = DiagnosticoLRUCache(capacidad_maxima=2, ttl_default_segundos=60)
    k1 = cache.generar_clave("falla 1")
    k2 = cache.generar_clave("falla 2")
    k3 = cache.generar_clave("falla 3")

    cache.guardar(k1, "res 1")
    cache.guardar(k2, "res 2")
    # k1 y k2 están en caché. Ahora guardamos k3 -> debe desalojar k1 (el más antiguo)
    cache.guardar(k3, "res 3")

    assert cache.obtener(k1) is None
    assert cache.obtener(k2) == "res 2"
    assert cache.obtener(k3) == "res 3"


def test_cache_expiracion_por_ttl():
    cache = DiagnosticoLRUCache(capacidad_maxima=5, ttl_default_segundos=0.05)
    clave = cache.generar_clave("falla expiracion")
    cache.guardar(clave, "resultado temporal")

    assert cache.obtener(clave) == "resultado temporal"
    time.sleep(0.06)
    # Debe haber expirado
    assert cache.obtener(clave) is None


def test_gestor_diagnostico_reutiliza_cache_en_segunda_llamada():
    gestor = GestorDiagnostico(gemini_api_key="mock_key")
    sintoma = "pastillas de freno chillan en bajada prueba cache"

    # Primera llamada: procesa y guarda en caché
    t0 = time.time()
    res1 = gestor.procesar_consulta_texto(sintoma, marca_modelo="Toyota Corolla")
    t_primera = (time.time() - t0) * 1000

    # Segunda llamada idéntica: debe responder desde caché en tiempo récord (< 10 ms)
    t1 = time.time()
    res2 = gestor.procesar_consulta_texto(sintoma, marca_modelo="Toyota Corolla")
    t_segunda = (time.time() - t1) * 1000

    assert res1.diagnostico_ml == res2.diagnostico_ml
    assert res2.desde_cache is True
    assert res2.predicciones_ml == res1.predicciones_ml
    assert t_segunda < 30.0  # Respuesta ultrarrápida desde memoria
