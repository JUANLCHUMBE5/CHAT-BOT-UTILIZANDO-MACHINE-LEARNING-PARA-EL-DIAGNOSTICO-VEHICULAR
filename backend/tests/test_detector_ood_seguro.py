"""Pruebas unitarias y de integración para la detección OOD y abstención segura."""

import pytest

from src.core.diagnostico.detector_ood import detectar_sintoma_fuera_de_catalogo

CASOS_OOD = [
    # Airbag / SRS / BCM
    "Quedó prendida la luz roja del Airbag en el tablero, no suena el claxon y no funcionan los botones del timón",
    "Testigo del airbag encendido tras desmontar el volante, posible cinta reloj rota",
    "Bolsas de aire no desplegadas y testigo srs parpadeando",
    # GLP / GNV
    "El conmutador de gas pita seguido y se regresa solo a gasolina aunque el tanque de GLP está lleno",
    "Falla en el reductor de gnv, no pasa gas a los inyectores de gas",
    "Se pasa solo a gasolina cuando acelero fuerte en gas glp",
    # EPS
    "El timón eléctrico EPS está durísimo y parpadea el testigo EPS en la pantalla",
    "Dirección electroasistida bloqueada con código en módulo eps",
    "Se siente golpeteo en la columna por la estrellita del timon o acoplador elastico del timon",
    # Red CAN / Inmovilizador
    "Parpadea la llave en el tablero, no hay comunicación CAN con ECM ni TCM por el conector OBD2",
    "Línea CAN en corto, resistencia de 120 ohms en lugar de 60 ohms en DLC",
    "Chip de la llave desprogramado, candadito parpadea y motor bloqueado",
    # HVAC Compuertas
    "Suena un clac-clac plástico repetitivo detrás del tablero al cambiar de frío a caliente por compuerta de mezcla",
    "Actuador de mezcla blend door trabado, sale aire caliente por el lado del copiloto",
    # Transmisión convertidor / mecatrónica
    "El convertidor de par patina en subida y vibra al bloquear",
    "La mecatrónica DSG tiene el acumulador de presión hidráulica reventado",
]

CASOS_IN_DOMAIN = [
    # In-domain no deben abstenerse por OOD
    "El motor tiembla en ralentí, ratea al acelerar y parpadea el check engine con código P0300",
    "El carro no arranca, la batería amanece muerta y el alternador solo bota 11.8V",
    "Prendo el aire acondicionado pero el compresor no acopla y sale aire tibio",
    "Al frenar de 80 a 40 km/h vibra fuerte el pedal y el timón por disco alabeado",
    "El pedal de embrague patina en subida y huele a quemado",
    "El carro rebota como lancha y los amortiguadores delanteros están chorreando aceite",
    "La dirección hidráulica está dura y la cremallera hidráulica bota líquido de dirección",
    "El motor se calienta en tráfico y hierve el refrigerante en el depósito",
]


@pytest.mark.parametrize("texto", CASOS_OOD)
def test_detector_ood_casos_positivos(texto):
    es_ood, regla = detectar_sintoma_fuera_de_catalogo(texto)
    assert es_ood is True, f"Fallo al detectar OOD: {texto}"
    assert regla is not None
    assert regla.categoria in [
        "AIRBAG_SRS_BCM", "GLP_GNV_CONVERSION", "DIRECCION_EPS_ELECTRONICA",
        "RED_CAN_INMOVILIZADOR_CENTRAL", "HVAC_COMPUERTA_MEZCLA_CALEFACCION",
        "TRANSMISION_NO_CUBIERTA_CONVERTIDOR"
    ]


@pytest.mark.parametrize("texto", CASOS_IN_DOMAIN)
def test_detector_ood_no_falsas_abstenciones(texto):
    es_ood, regla = detectar_sintoma_fuera_de_catalogo(texto)
    assert es_ood is False, f"Falsa abstención generada en caso conocido: {texto} (detectado como {regla.categoria if regla else None})"
