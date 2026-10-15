import pytest

from src.core.conversacion.evidencia_acciones import registrar_acciones_taller
from src.core.conversacion.models import ConversationState


@pytest.mark.parametrize("texto,componente", [
    ("La manguera del intercooler tenía aceite por fuera.", "intercooler"),
    ("La batería presenta corrosión en sus terminales.", "bateria"),
    ("Vi humedad en el alternador.", "alternador"),
])
def test_conserva_observacion_sin_confirmar_falla(texto, componente):
    estado = ConversationState(session_id="observacion")
    registrar_acciones_taller(estado, texto)
    hecho = estado.obtener_hecho(f"observacion_{componente}")
    assert hecho is not None
    assert hecho.texto_crudo == texto
    assert hecho.categoria == "observacion"
    assert estado.obtener_hecho("falla_confirmada_usuario") is None
    assert not any(h.categoria == "componente_descartado" for h in estado.hechos.values())


@pytest.mark.parametrize("texto", [
    "El intercooler no tiene aceite por fuera.",
    "Nunca vi humedad en el alternador.",
    "Creo que la batería tiene corrosión.",
])
def test_no_afirma_observaciones_negadas_o_sospechadas(texto):
    estado = ConversationState(session_id="observacion-no-afirmada")
    registrar_acciones_taller(estado, texto)
    assert not any(h.categoria == "observacion" for h in estado.hechos.values())
