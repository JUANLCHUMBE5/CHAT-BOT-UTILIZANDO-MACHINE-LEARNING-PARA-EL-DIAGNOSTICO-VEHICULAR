"""Regresiones de mediciones reportadas sin convertir capacidad nominal en lectura."""

from src.core.conversacion.respuestas_cortas.extractor_mediciones import extraer_todas_mediciones


def test_bateria_nominal_12v_65ah_no_se_confunde_con_lectura_12v():
    texto = "La batería es nueva de 12V 65Ah probada con tester da 100% de salud y 12.7V"

    mediciones = extraer_todas_mediciones(texto.lower(), "MEDICION_TECNICA", "", None)

    assert not any(valor == 12.0 and unidad == "V" for valor, unidad, _ in mediciones)
    assert any(valor == 12.7 and unidad == "V" for valor, unidad, _ in mediciones)


def test_anio_seguido_de_a_gasolina_no_se_interpreta_como_amperios():
    mediciones = extraer_todas_mediciones(
        "Toyota Corolla 2017 a gasolina, la batería mide 12.6 V".lower(),
        "MEDICION_TECNICA",
        "",
        None,
    )

    assert not any(valor == 2017.0 and unidad == "A" for valor, unidad, _ in mediciones)
    assert any(valor == 12.6 and unidad == "V" for valor, unidad, _ in mediciones)
