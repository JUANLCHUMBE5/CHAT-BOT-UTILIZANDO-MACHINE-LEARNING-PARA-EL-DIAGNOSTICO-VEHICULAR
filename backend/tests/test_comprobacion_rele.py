from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState


def test_intercambio_de_rele_con_falla_persistente_se_conserva_como_prueba_reportada():
    estado = ConversationState(session_id="rele-ventilador")

    ExtractorHechos.extraer_y_actualizar(
        estado,
        "Intercambié el relé por otro conocido y la baja siguió sin activar.",
    )

    hecho = estado.hechos["rele_intercambiado_sin_resolver"]
    assert hecho.valor == "SI"
    assert hecho.procedencia == "user_reported"
    assert hecho.texto_crudo == "Intercambié el relé por otro conocido y la baja siguió sin activar."
