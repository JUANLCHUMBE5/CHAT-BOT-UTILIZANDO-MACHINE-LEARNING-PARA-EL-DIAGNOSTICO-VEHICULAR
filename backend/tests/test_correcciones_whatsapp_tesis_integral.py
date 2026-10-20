"""Pruebas integrales de validación y diálogo WhatsApp para las correcciones de tesis."""

from unittest.mock import MagicMock

from src.application.services.confirmacion_diagnostico import (
    instrucciones_confirmacion_whatsapp,
)
from src.core.conversacion.models import ConversationState
from src.core.conversacion.orientacion_provisional import (
    es_sintoma_mecanico_valido,
    generar_orientacion_provisional,
    obtener_orientacion_visual_segura,
)
from src.core.services.webhook.validation_workflow import (
    _respuesta_detalle_hipotesis,
    _solicita_continuar_sin_confirmacion,
)


def test_error_a_no_expone_mensaje_rag_interno():
    """Error A: Nunca emitir 'Sin procedimiento RAG registrado' ni placeholders internos."""
    hipotesis_mock = MagicMock()
    hipotesis_mock.falla_probable = "Fuga interna en cilindro maestro"
    hipotesis_mock.prueba_recomendada = "Sin procedimiento RAG registrado"

    detalle = _respuesta_detalle_hipotesis(hipotesis_mock, 1)

    assert "Sin procedimiento RAG registrado" not in detalle
    assert "no registrado" not in detalle.lower()
    # Debe invocar el fallback determinista seguro
    assert "depósito translúcido" in detalle.lower() or "inspección visual" in detalle.lower()
    assert "sin abrir la tapa" in detalle.lower()


def test_error_b_respuesta_no_sin_observacion_mantiene_hipotesis_abierta():
    """Error B: Responder 'NO' a secas no debe inducir ni ejecutar un descarte ciego."""
    hipotesis_mock = MagicMock()
    hipotesis_mock.falla_probable = "Bomba de combustible dañada"
    hipotesis_mock.prueba_recomendada = "Medir presión de riel con manómetro"

    detalle = _respuesta_detalle_hipotesis(hipotesis_mock, 1)
    # Debe indicar responder SÍ o describir qué observó, sin presionar 'o NO para descartar'
    assert "o NO para descartar y continuar el análisis" not in detalle
    assert "describe qué observaste al revisar" in detalle or "si la comprobaste" in detalle


def test_error_c_orientacion_visual_segura_frenos_pedal_esponjoso():
    """Error C: Inspección visual segura para pedal esponjoso/frenos."""
    estado = ConversationState(session_id="test-c")
    estado.active_symptoms = ["pedal esponjoso"]
    estado.active_system = "frenos"

    guias = obtener_orientacion_visual_segura(estado, falla="Fuga de líquido de frenos")
    texto_guia = " ".join(guias)

    # Debe contener verificación de depósito translúcido sin abrir la tapa
    assert "depósito translúcido" in texto_guia.lower() or "deposito translucido" in texto_guia.lower()
    assert "sin abrir la tapa" in texto_guia.lower()
    # Debe contener chequeo de fugas en piso / ruedas
    assert "ruedas" in texto_guia.lower() or "piso" in texto_guia.lower() or "fugas" in texto_guia.lower()
    # No debe alentar purgas ni desmontajes sin herramientas
    assert "purga" in texto_guia.lower() or "equipo adecuado" in texto_guia.lower()


def test_error_d_filtrado_palabras_de_control_en_active_symptoms():
    """Error D: Evitar que 'SI', 'NO', '1', '2' se agreguen a active_symptoms."""
    # Las palabras de control deben ser rechazadas
    assert not es_sintoma_mecanico_valido("SI")
    assert not es_sintoma_mecanico_valido("si")
    assert not es_sintoma_mecanico_valido("NO")
    assert not es_sintoma_mecanico_valido("no")
    assert not es_sintoma_mecanico_valido("1")
    assert not es_sintoma_mecanico_valido("2")
    assert not es_sintoma_mecanico_valido("la 1")
    assert not es_sintoma_mecanico_valido("la primera")
    assert not es_sintoma_mecanico_valido("correcto")
    assert not es_sintoma_mecanico_valido("negativo")

    # Los síntomas mecánicos genuinos deben ser aceptados
    assert es_sintoma_mecanico_valido("pedal esponjoso")
    assert es_sintoma_mecanico_valido("fuga de líquido")
    assert es_sintoma_mecanico_valido("motor no arranca")
    assert es_sintoma_mecanico_valido("humo azul por el escape")

    # En orientación provisional no deben salir mezclas espurias
    estado = ConversationState(session_id="test-d")
    estado.active_symptoms = ["SI", "pedal esponjoso", "2"]
    resp = generar_orientacion_provisional(estado, hipotesis_disponibles=[{"falla": "Fuga de frenos"}])
    assert "(SI; pedal esponjoso)" not in resp
    assert "(SI)" not in resp
    assert "pedal esponjoso" in resp.lower()


def test_error_e_instrucciones_confirmacion_whatsapp_sin_ambiguedades():
    """Error E: Instrucciones claras sin ¿Fue correcta? SÍ / NO (1/2/3)."""
    # Para 2 hipótesis
    inst_2 = instrucciones_confirmacion_whatsapp(2)
    assert "¿Fue correcta? *SÍ / NO*" not in inst_2
    assert "Selecciona una hipótesis a verificar" in inst_2
    assert "(1/2)" in inst_2

    # Para 3 hipótesis
    inst_3 = instrucciones_confirmacion_whatsapp(3)
    assert "¿Fue correcta? *SÍ / NO*" not in inst_3
    assert "Selecciona una hipótesis a verificar" in inst_3
    assert "(1/2/3)" in inst_3

    # Para 1 sola hipótesis
    inst_1 = instrucciones_confirmacion_whatsapp(1)
    assert "*SÍ / NO*" in inst_1


def test_solicita_continuar_sin_confirmacion_detecciones():
    """Verifica detección de intención de continuar o solicitar guía visual."""
    assert _solicita_continuar_sin_confirmacion("no puedo revisar")
    assert _solicita_continuar_sin_confirmacion("no tengo herramientas")
    assert _solicita_continuar_sin_confirmacion("quiero continuar")
    assert _solicita_continuar_sin_confirmacion("sigamos")
    assert _solicita_continuar_sin_confirmacion("todavia no lo he revisado")
    assert _solicita_continuar_sin_confirmacion("que puedo revisar visualmente")
