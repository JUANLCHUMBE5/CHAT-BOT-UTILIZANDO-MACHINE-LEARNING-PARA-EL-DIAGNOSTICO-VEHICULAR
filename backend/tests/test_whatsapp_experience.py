"""Regresiones de experiencia conversacional y salida breve para WhatsApp."""

from src.core.gemini_queue import GeminiRateLimiter, SolicitudGeminiEncolada
from src.core.gestor_diagnostico import GestorDiagnostico


def test_resumen_whatsapp_gnv_es_breve_y_prioriza_prueba_comparativa():
    solicitud = SolicitudGeminiEncolada(
        sintoma="pierde fuerza en subida pero el auto es a GNV",
        diagnostico_ml="Disco de embrague desgastado o patinando",
        confianza_ml=0.42,
        requiere_revision_humana=True,
    )
    resumen = GeminiRateLimiter._crear_resumen_whatsapp(solicitud, "Gravedad: Media")
    assert "gasolina y GNV/GLP" in resumen
    assert "embrague" not in resumen.lower()
    assert "Gravedad: *Media*" in resumen
    assert "Análisis completo disponible en el panel" in resumen
    assert len(resumen) < 700


def test_contexto_multiturno_une_dato_gnv_sin_arrastrar_consulta_nueva(monkeypatch):
    gestor = GestorDiagnostico()
    capturados = []

    monkeypatch.setattr(
        gestor.modelo_ml,
        "predecir_top_fallas",
        lambda texto, limite=3: [
            {"falla": capturados.append(texto) or "falla de alimentación", "probabilidad": 0.75}
        ],
    )
    monkeypatch.setattr(
        gestor,
        "_generar_respuesta_con_metadatos",
        lambda **kwargs: ("respuesta", {"usado": False, "modo": "diagnostico_degradado_ml_rag"}),
    )

    gestor.procesar_consulta_texto("pierde fuerza en subida y se apaga", session_id="sesion-gnv")
    segundo = gestor.procesar_consulta_texto("pero el auto es a GNV", session_id="sesion-gnv")
    assert "pierde fuerza en subida" in capturados[-1]
    assert "gnv" in capturados[-1].lower()
    assert segundo.sintoma_evaluado == capturados[-1]

    gestor.procesar_consulta_texto("la puerta no abre con el control", session_id="sesion-gnv")
    assert "pierde fuerza" not in capturados[-1]


def test_consulta_tecnica_pide_solo_datos_faltantes_y_luego_continua():
    gestor = GestorDiagnostico()
    gestor.api_key = ""

    primero = gestor.procesar_consulta_texto(
        "Toyota Corolla 2020: qué porcentaje de refrigerante debo usar",
        session_id="perfil-refrigerante",
    )

    assert primero.modo_diagnostico == "esperando_datos_vehiculo"
    assert "1. motor o cilindrada" in primero.respuesta_texto
    assert "1. marca" not in primero.respuesta_texto

    segundo = gestor.procesar_consulta_texto(
        "motor 1.8 gasolina",
        session_id="perfil-refrigerante",
    )

    assert segundo.tipo_consulta == "consulta_tecnica"
    assert segundo.modo_diagnostico == "consulta_tecnica_degradada"
    assert "Toyota" in segundo.sintoma_evaluado
    assert "COROLLA" in segundo.sintoma_evaluado
    assert "1.8 L" in segundo.sintoma_evaluado


def test_consulta_con_perfil_completo_no_repite_preguntas():
    gestor = GestorDiagnostico()
    gestor.api_key = ""

    resultado = gestor.procesar_consulta_texto(
        "Suzuki APV 2020 motor 1.6 gasolina: qué potencia deben tener los focos LED H4",
        session_id="perfil-completo",
    )

    assert resultado.tipo_consulta == "consulta_tecnica"
    assert resultado.modo_diagnostico == "consulta_tecnica_degradada"
    assert "Necesito identificar" not in resultado.respuesta_texto


def test_kilometraje_ambiguo_se_confirma_antes_de_responder():
    gestor = GestorDiagnostico()
    gestor.api_key = ""

    primero = gestor.procesar_consulta_texto(
        "Toyota Corolla 2020 motor 1.8: qué refrigerante uso si tiene más de 100 km",
        session_id="kilometraje-ambiguo",
    )
    assert primero.modo_diagnostico == "esperando_datos_vehiculo"
    assert "100 km" in primero.respuesta_texto
    assert "100 000 km" in primero.respuesta_texto

    segundo = gestor.procesar_consulta_texto(
        "quise decir 100 mil km",
        session_id="kilometraje-ambiguo",
    )
    assert segundo.tipo_consulta == "consulta_tecnica"
    assert "100000" in segundo.sintoma_evaluado


def test_contexto_vehiculo_se_puede_restaurar_tras_reinicio():
    gestor_1 = GestorDiagnostico()
    gestor_1.api_key = ""
    gestor_1.procesar_consulta_texto(
        "qué potencia deben tener los focos LED H4",
        session_id="persistente",
    )
    contexto = gestor_1.session_manager.exportar_contexto("persistente")

    gestor_2 = GestorDiagnostico()
    gestor_2.api_key = ""
    gestor_2.session_manager.cargar_contexto("persistente", contexto)
    resultado = gestor_2.procesar_consulta_texto(
        "Suzuki APV 2020 motor 1.6 gasolina",
        session_id="persistente",
    )

    assert resultado.tipo_consulta == "consulta_tecnica"
    assert "Suzuki" in resultado.sintoma_evaluado
    assert "APV" in resultado.sintoma_evaluado
