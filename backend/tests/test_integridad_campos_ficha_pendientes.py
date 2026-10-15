from src.interfaces.api.v1.dtos.validacion import CasoValidacionDTO, CrearCasoValidacionDTO


def test_borrador_no_hereda_metodo_de_confirmacion_por_defecto():
    caso = CrearCasoValidacionDTO(
        placa="ABC123",
        marca_modelo="Toyota Corolla",
        sintoma="Arranque lento en frío",
        falla_real="Falla no confirmada",
        chatbot_prediccion="Hipótesis inicial",
        campos_completos=0,
        tiempo_diagnostico_minutos=15,
        prediccion_correcta=0,
    )
    assert caso.metodo_confirmacion is None


def test_respuesta_de_borrador_admite_metadatos_humanos_pendientes():
    caso = CasoValidacionDTO(
        item=1,
        fase="Post-test",
        fecha="2026-10-14",
        placa_enmascarada="***-1234",
        placa_hash="a" * 64,
        marca_modelo="Toyota Corolla",
        sintoma="Arranque lento en frío",
        falla_real=None,
        chatbot_prediccion="Hipótesis inicial",
        campos_completos=0,
        tiempo_diagnostico_minutos=None,
        prediccion_correcta=None,
        metodo_confirmacion=None,
    )
    assert caso.falla_real is None
    assert caso.tiempo_diagnostico_minutos is None
    assert caso.prediccion_correcta is None
    assert caso.metodo_confirmacion is None
