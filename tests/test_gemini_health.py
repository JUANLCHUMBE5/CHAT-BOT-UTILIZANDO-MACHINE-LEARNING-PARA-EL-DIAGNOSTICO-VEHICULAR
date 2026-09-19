"""Pruebas unitarias del estado observable de Gemini."""

from src.core.gemini_queue import GeminiRateLimiter


def test_gemini_no_se_declara_disponible_antes_de_verificarlo():
    limiter = GeminiRateLimiter(max_por_minuto=12, max_por_dia=18)
    estado = limiter.obtener_estado_gemini(api_key_valida=True)

    assert estado["estado"] == "no_verificado"
    assert estado["disponible"] is False
    assert estado["ultima_verificacion"] is None


def test_gemini_registra_exito_real():
    limiter = GeminiRateLimiter(max_por_minuto=12, max_por_dia=18)
    limiter.registrar_estado_gemini(exitoso=True, codigo_http=200)
    estado = limiter.obtener_estado_gemini(api_key_valida=True)

    assert estado["estado"] == "disponible"
    assert estado["disponible"] is True
    assert estado["ultimo_codigo_http"] == 200
    assert estado["ultimo_exito"] is not None


def test_gemini_registra_cuota_externa_agotada():
    limiter = GeminiRateLimiter(max_por_minuto=12, max_por_dia=18)
    limiter.registrar_estado_gemini(
        exitoso=False,
        codigo_http=429,
        error="Gemini HTTP 429",
    )
    estado = limiter.obtener_estado_gemini(api_key_valida=True)

    assert estado["estado"] == "degradado_sin_cuota"
    assert estado["disponible"] is False
    assert estado["ultimo_codigo_http"] == 429
    assert estado["ultimo_error"] == "Gemini HTTP 429"


def test_gemini_sin_clave_tiene_estado_explicito():
    limiter = GeminiRateLimiter(max_por_minuto=12, max_por_dia=18)
    estado = limiter.obtener_estado_gemini(api_key_valida=False)

    assert estado["estado"] == "sin_api_key"
    assert estado["disponible"] is False
