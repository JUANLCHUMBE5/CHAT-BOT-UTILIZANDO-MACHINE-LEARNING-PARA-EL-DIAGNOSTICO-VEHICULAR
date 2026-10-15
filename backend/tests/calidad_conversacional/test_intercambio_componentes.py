from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState


def test_intercambio_de_componentes_con_dtc_persistente_conserva_resultado_sin_confirmar_causa():
    estado = ConversationState(session_id="intercambio")
    ExtractorHechos.extraer_y_actualizar(
        estado,
        "La bobina 1 fue intercambiada con la 2 y el P0301 no se movió.",
    )

    assert estado.obtener_valor_confirmado("prueba_intercambio_bobina") == "bobina 1 intercambiada con 2"
    assert estado.obtener_valor_confirmado("dtc_persistente_tras_intercambio_P0301") == (
        "P0301 no se movió tras intercambio de bobina"
    )
    assert estado.obtener_hecho("bobina_migro_cilindro_1") is None
