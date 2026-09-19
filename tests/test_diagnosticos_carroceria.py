"""Pruebas de regresión para diagnósticos de carrocería, puertas, cerraduras y elevalunas."""

import pytest

from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.fixture
def gestor():
    return GestorDiagnostico(gemini_api_key="mock_key")


def test_control_remoto_no_desbloquea_puerta(gestor):
    """Verifica que un problema de control remoto/seguro eléctrico sea procesado correctamente."""
    sintoma = "al cerrar la puerta de mi auto y al aplastar el control de la puerta este no lo abre y sigue bloqueada"
    resultado = gestor.procesar_consulta_texto(sintoma)

    assert resultado.estado_sesion != "esperando_clarificacion"
    assert resultado.modo_diagnostico != "esperando_clarificacion"
    assert "puerta" in resultado.contexto_manual.lower() or "cierre" in resultado.contexto_manual.lower() or "actuador" in resultado.contexto_manual.lower()
    assert resultado.confianza_ml > 0.0


def test_chapa_o_pestillo_mecanico_trabado(gestor):
    """Verifica diagnóstico de cerradura, trinquete o pestillo mecánico desalineado."""
    sintoma = "la chapa de la puerta esta inclinada y no encaja en el marco, el pestillo mecanico se quedo trabado"
    resultado = gestor.procesar_consulta_texto(sintoma)

    assert resultado.estado_sesion != "esperando_clarificacion"
    assert "chapa" in resultado.contexto_manual.lower() or "cerradura" in resultado.contexto_manual.lower() or "pestillo" in resultado.contexto_manual.lower()


def test_elevalunas_electrico_guaya_rota(gestor):
    """Verifica diagnóstico de elevalunas o alzacristales quemado / guaya suelta."""
    sintoma = "el vidrio de la puerta del piloto no sube ni baja, se cayo la luna dentro de la puerta y suena la guaya"
    resultado = gestor.procesar_consulta_texto(sintoma)

    assert resultado.estado_sesion != "esperando_clarificacion"
    assert "elevalunas" in resultado.contexto_manual.lower() or "alzacristales" in resultado.contexto_manual.lower() or "vidrio" in resultado.contexto_manual.lower()


def test_limpiaparabrisas_motor_plumas_quemado(gestor):
    """Verifica diagnóstico de limpiaparabrisas que no funciona."""
    sintoma = "las plumas del limpiaparabrisas se quedaron trabadas a mitad del parabrisas y el motor huele a quemado"
    resultado = gestor.procesar_consulta_texto(sintoma)

    assert resultado.estado_sesion != "esperando_clarificacion"
    assert "limpiaparabrisas" in resultado.contexto_manual.lower() or "pluma" in resultado.contexto_manual.lower()


def test_mensaje_largo_descriptivo_no_es_ambiguo(gestor):
    """Un mensaje largo y descriptivo no debe ser rechazado por filtro de palabras rígido."""
    sintoma = "siento que al presionar el pulsador de la puerta del conductor el mecanismo intenta accionar pero no logra liberar el pestillo"
    es_ambiguo, mensaje = gestor._es_consulta_ambigua(sintoma)
    assert not es_ambiguo
    assert mensaje == ""


def test_consulta_verdaderamente_ambigua_pide_aclaracion(gestor):
    """Una consulta corta y sin contexto ('mi carro falla') debe pedir aclaración técnica."""
    sintoma = "mi carro falla"
    es_ambiguo, mensaje = gestor._es_consulta_ambigua(sintoma)
    assert es_ambiguo
    assert "especifique" in mensaje.lower()


def test_frase_real_whatsapp_no_pide_aclaracion_de_frenado(gestor):
    """La frase exacta enviada por WhatsApp no debe solicitar aclaraciones sobre frenos ni aceleración."""
    sintoma_whatsapp = (
        "MIRA ACA OTRO PROBLEMA DONDE, TAMBIEN TENGO FALLA EN PUERTA DONDE "
        "EL CLIENTE ME INDICA QUE AL CERRAR LA PUERTA ESTE NO SE DESBLOQUEA "
        "CON EL CONTROL, CADA QUE APLASTA EL CONTROL ESTE NO PUEDE DESBLOQUEARLO"
    )
    resultado = gestor.procesar_consulta_texto(sintoma_whatsapp)

    assert resultado.estado_sesion != "esperando_clarificacion"
    assert "frenar" not in resultado.respuesta_texto.lower()
    assert "acelerar" not in resultado.respuesta_texto.lower()
    assert resultado.similitud_rag >= 0.25


def test_rag_no_inventa_confianza_ml():
    class ModeloDebil:
        def predecir_falla_con_confianza(self, sintoma):
            return "Hipotesis sin confirmar", 0.07

    class RagFuerte:
        def recuperar_contexto_con_similitud(self, query):
            return "Inspeccionar actuador y cableado.", "Cierre centralizado", 0.81

        def recuperar_contexto(self, query):
            return "Inspeccionar actuador y cableado.", "Cierre centralizado"

    gestor_local = GestorDiagnostico(
        gemini_api_key="mock_key", modelo_ml=ModeloDebil(), motor_rag=RagFuerte()
    )
    resultado = gestor_local.procesar_consulta_texto(
        "la puerta no abre con el control y el actuador suena"
    )

    assert resultado.confianza_ml == pytest.approx(0.07)
    assert resultado.similitud_rag == pytest.approx(0.81)
    assert resultado.requiere_revision_humana
