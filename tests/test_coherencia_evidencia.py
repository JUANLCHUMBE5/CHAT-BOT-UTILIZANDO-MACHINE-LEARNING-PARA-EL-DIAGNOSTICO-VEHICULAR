"""Regresiones y controles negativos de prioridad física y respuesta breve."""

import pytest

from src.core.diagnostico.coherencia_evidencia import (
    bateria_ya_comprobada,
    documento_compatible,
    limitar_respuesta,
    priorizar_evidencia,
)
from src.core.diagnostico.models import PrediccionML


def preds():
    return [
        PrediccionML(falla="Cuerpo de aceleracion o valvula IAC sucia", probabilidad=0.42),
        PrediccionML(falla="Falta o degradacion de aceite de caja de cambios", probabilidad=0.37),
    ]


@pytest.mark.parametrize("texto", [
    "Caja automática: tarda cinco segundos en acoplar y entra con golpe.",
    "En marcha atrás demora en enganchar la transmisión.",
    "Automático: en R demora varios segundos y entra con golpe.",
])
def test_acoplamiento_prioriza_candidato_existente_sin_inflar_confianza(texto):
    originales = preds()
    resultado, motivo = priorizar_evidencia(texto, originales)
    assert resultado[0] == originales[1]
    assert resultado[0].probabilidad == 0.37
    assert originales[0].probabilidad == 0.42
    assert motivo


@pytest.mark.parametrize("texto", [
    "La reversa entra normal. El motor tironea al acelerar.",
    "La caja no demora en enganchar y no entra con golpe.",
    "Automático: se apaga el motor al poner D y tiene ralentí inestable.",
    "Tengo una caja automática, el motor falla.",
])
def test_mencion_o_negacion_no_promueve_transmision(texto):
    resultado, motivo = priorizar_evidencia(texto, preds())
    assert resultado[0].probabilidad == 0.42
    assert not motivo


@pytest.mark.parametrize("texto,promover", [
    ("En elevador encontré juego en la rótula y el buje roto.", True),
    ("No encontré juego en la rótula y el buje no está roto.", False),
    ("Quizás revisar rótulas y bujes por el ruido.", False),
])
def test_hallazgo_suspension_y_negaciones(texto, promover):
    originales = [
        PrediccionML(falla="Llantas desbalanceadas o desalineadas", probabilidad=0.61),
        PrediccionML(falla="Amortiguadores reventados o bujes de suspension gastados", probabilidad=0.25),
    ]
    resultado, _ = priorizar_evidencia(texto, originales)
    assert resultado[0] == originales[1 if promover else 0]


def test_bateria_medida_no_pide_otra_vez_el_mismo_sintoma():
    assert bateria_ya_comprobada("Cae a 7 V al arrancar. Con batería de apoyo arranca.")
    assert not bateria_ya_comprobada("Cae a 7 V. Con batería de apoyo no arranca.")


def test_respuesta_sin_especificaciones_genericas():
    texto, filtrado = limitar_respuesta("Aprieta a 105 Nm.", preds())
    assert filtrado
    assert "105" not in texto
    assert "motorización" in texto
    assert len(texto) < 1200


def test_respuesta_breve_segura_se_conserva():
    texto = "Posible falla de transmisión. Comprueba el estado del fluido según el fabricante."
    assert limitar_respuesta(texto, preds()) == (texto, False)


def test_manual_de_caja_mecanica_no_aplica_a_automatica():
    assert not documento_compatible("Carro automático demora en R", "Servicio a caja de cambios mecánica", "")
    assert documento_compatible("Carro automático demora en R", "Diagnóstico de caja automática", "")
    assert not documento_compatible("Caja manual raspa", "Servicio de transmisión automática CVT", "")


def test_fallback_no_recomienda_motor_en_queja_de_acoplamiento():
    ordenadas, motivo = priorizar_evidencia("Caja automática entra con golpe", preds())
    texto, _ = limitar_respuesta("Apretar a 100 Nm", ordenadas, motivo)
    assert "IAC" not in texto


def test_sin_documento_no_remite_a_manual_inexistente():
    texto, limitado = limitar_respuesta("Siga el manual adjunto", preds(), sin_documento=True)
    assert limitado
    assert "manual adjunto" not in texto
    assert "No hay procedimiento compatible verificado" in texto
