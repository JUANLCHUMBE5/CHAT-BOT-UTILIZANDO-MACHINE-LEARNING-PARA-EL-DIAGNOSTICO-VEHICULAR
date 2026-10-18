import copy

import pytest

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState, FactType
from src.core.diagnostic_cache import DiagnosticoLRUCache
from src.core.diagnostico.cache_contextual import generar_clave_contextual


@pytest.mark.parametrize("cambio", ["valor", "unidad", "vehiculo", "descarte", "taller", "caso", "sesion"])
def test_no_reutiliza_cache_de_contexto_distinto(cambio):
    state = ConversationState(session_id="s", case_id="c")
    state.registrar_hecho("lectura", "12 bar", categoria="medicion", tipo=FactType.CONDICION)

    def clave(st=state, taller="t", sesion="s", caso="c"):
        return generar_clave_contextual("ratea", "Toyota", "ABC-123", caso, taller, sesion, st)

    key = clave()
    cache = DiagnosticoLRUCache()
    cache.guardar(key, {"sentinela": "caso anterior"})
    other = copy.deepcopy(state)
    if cambio == "valor":
        other.hechos["lectura"].valor = "1.2 bar"
    elif cambio == "unidad":
        other.hechos["lectura"].valor = "12 psi"
    elif cambio == "vehiculo":
        other.marca = "Ford"
    elif cambio == "descarte":
        other.hipotesis_descartadas.append("Bujías")
    kwargs = {"st": other}
    if cambio == "taller":
        kwargs["taller"] = "otro"
    if cambio == "caso":
        kwargs["caso"] = "otro"
    if cambio == "sesion":
        kwargs["sesion"] = "otra"
    assert cache.obtener(clave(**kwargs)) is None
    assert cache.obtener(key) == {"sentinela": "caso anterior"}


def test_condicion_motor_no_sobrescribe_codigo():
    state = ConversationState(session_id="motor")
    state.motor = "1NZ-FE"
    for text in ("motor en marcha", "motor caliente", "motor hirviendo", "motor funcionando"):
        ExtractorHechos.extraer_y_actualizar(state, text)
        assert state.motor == "1NZ-FE"
