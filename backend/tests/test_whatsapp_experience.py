"""Regresiones de experiencia conversacional y salida breve para WhatsApp."""

from src.core.gemini_queue import GeminiRateLimiter, SolicitudGeminiEncolada
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.vehicle_profile import (
    extraer_datos_vehiculo,
    extraer_datos_vehiculo_contextual,
)


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

    primero = gestor.procesar_consulta_texto(
        "pierde fuerza en subida y se apaga", session_id="sesion-gnv"
    )
    assert primero.estado_sesion == "esperando_combustible"

    segundo = gestor.procesar_consulta_texto("pero el auto es a GNV", session_id="sesion-gnv")
    assert segundo.estado_sesion == "esperando_combustible"
    tercero = gestor.procesar_consulta_texto(
        "solo pasa en GNV; en gasolina va bien", session_id="sesion-gnv"
    )
    assert "pierde fuerza en subida" in capturados[-1]
    assert "gnv" in capturados[-1].lower()
    assert "solo usando GNV" in capturados[-1]
    assert tercero.sintoma_evaluado == capturados[-1]

    gestor.procesar_consulta_texto("la puerta no abre con el control", session_id="sesion-gnv")
    assert "pierde fuerza" not in capturados[-1]


def test_consulta_tecnica_no_exige_marca_modelo_ni_anio():
    gestor = GestorDiagnostico()
    gestor.api_key = ""

    resultado = gestor.procesar_consulta_texto(
        "qué porcentaje de refrigerante debo usar",
        session_id="perfil-refrigerante",
    )

    assert resultado.tipo_consulta == "consulta_tecnica"
    assert resultado.modo_diagnostico == "consulta_tecnica_degradada"
    assert "Necesito identificar el vehículo" not in resultado.respuesta_texto
    assert "refrigerante" in resultado.sintoma_evaluado
    assert "Si sabes el modelo" in resultado.respuesta_texto
    assert len(resultado.respuesta_texto) < 350


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


def test_contexto_antiguo_con_datos_requeridos_ya_no_bloquea_consulta():
    gestor_1 = GestorDiagnostico()
    gestor_1.api_key = ""
    sesion = gestor_1.session_manager.obtener_o_crear_sesion("persistente")
    sesion.establecer_consulta_tecnica(
        "qué potencia deben tener los focos LED H4",
        ["marca", "modelo", "anio", "motor"],
        False,
    )
    contexto = gestor_1.session_manager.exportar_contexto("persistente")

    gestor_2 = GestorDiagnostico()
    gestor_2.api_key = ""
    gestor_2.session_manager.cargar_contexto("persistente", contexto)
    resultado = gestor_2.procesar_consulta_texto(
        "no conozco esos datos",
        session_id="persistente",
    )

    assert resultado.tipo_consulta == "consulta_tecnica"
    assert resultado.modo_diagnostico == "consulta_tecnica_degradada"
    assert "qué potencia deben tener los focos LED H4" in resultado.sintoma_evaluado


def test_consulta_nueva_descarta_pregunta_tecnica_antigua():
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    sesion = gestor.session_manager.obtener_o_crear_sesion("contexto-antiguo")
    sesion.establecer_consulta_tecnica(
        "qué potencia deben tener los focos LED H4 para una Suzuki APV",
        ["modelo", "anio", "motor"],
        False,
    )

    resultado = gestor.procesar_consulta_texto(
        "cuántos kilómetros debe recorrer un auto para instalar GNV",
        session_id="contexto-antiguo",
    )

    assert resultado.tipo_consulta == "consulta_tecnica"
    assert "instalar gnv" in resultado.sintoma_evaluado.lower()
    assert "focos LED" not in resultado.sintoma_evaluado


def test_esta_bien_sin_diagnostico_pendiente_es_solo_cordial():
    gestor = GestorDiagnostico()

    resultado = gestor.procesar_consulta_texto(
        "ESTÁ BIEN",
        session_id="respuesta-cordial",
    )

    assert resultado.respuesta_texto == "👍 Entendido."
    assert resultado.tipo_consulta == "conversacional"
    assert resultado.modo_diagnostico == "conversacional"


def test_aclaracion_de_sintoma_es_breve_y_no_es_diagnostico():
    gestor = GestorDiagnostico()

    resultado = gestor.procesar_consulta_texto(
        "tengo una falla",
        session_id="consulta-ambigua",
    )

    assert len(resultado.respuesta_texto) < 80
    assert resultado.tipo_consulta == "aclaracion"


def test_vibraciones_al_manejar_pide_contexto_util_y_breve():
    gestor = GestorDiagnostico()

    resultado = gestor.procesar_consulta_texto(
        "Vibraciones al menjar",
        session_id="vibracion-generica",
    )

    assert resultado.tipo_consulta == "aclaracion"
    assert resultado.respuesta_texto == (
        "🔎 ¿Vibra al frenar, a cierta velocidad o en mínimo?"
    )


def test_perdida_potencia_no_ejecuta_ml_hasta_comparar_combustible(monkeypatch):
    gestor = GestorDiagnostico()
    llamadas_ml = []
    monkeypatch.setattr(
        gestor.modelo_ml,
        "predecir_top_fallas",
        lambda texto, limite=3: [
            {"falla": llamadas_ml.append(texto) or "válvula IAC", "probabilidad": 0.21}
        ],
    )
    monkeypatch.setattr(
        gestor,
        "_generar_respuesta_con_metadatos",
        lambda **kwargs: ("respuesta", {"usado": False, "modo": "diagnostico_degradado_ml_rag"}),
    )

    primero = gestor.procesar_consulta_texto(
        "cuando corre se chanchea", session_id="regresion-chanchea"
    )
    assert primero.estado_sesion == "esperando_combustible"
    assert "GNV" in primero.respuesta_texto
    assert llamadas_ml == []

    segundo = gestor.procesar_consulta_texto("es gnb", session_id="regresion-chanchea")
    assert segundo.estado_sesion == "esperando_combustible"
    assert "Falla solo en *GNV*" in segundo.respuesta_texto
    assert llamadas_ml == []

    resultado = gestor.procesar_consulta_texto(
        "solo falla en GNV, en gasolina funciona bien",
        session_id="regresion-chanchea",
    )
    assert resultado.estado_sesion == "completado"
    assert "gnv" in llamadas_ml[-1].lower()
    assert resultado.diagnostico_ml.startswith("Sistema GNV/GLP")


def test_perfil_vehiculo_acepta_formato_whatsapp_y_respuestas_breves():
    perfil = extraer_datos_vehiculo("_Toyota Corolla 2020, motor 1.8 gasolina_")
    assert perfil == {
        "anio": 2020,
        "marca": "Toyota",
        "modelo": "COROLLA",
        "motor": "1.8 L",
        "combustible": "gasolina",
    }

    modelo = extraer_datos_vehiculo_contextual(
        "Corolla", ["modelo", "anio", "motor"], {"marca": "Toyota"}
    )
    motor = extraer_datos_vehiculo_contextual("1.8", ["motor", "equipo_gas"], perfil)
    assert modelo["modelo"] == "COROLLA"
    assert motor["motor"] == "1.8 L"


def test_resumen_baja_confianza_no_afirma_una_pieza():
    solicitud = SolicitudGeminiEncolada(
        sintoma="se chanchea cuando corre",
        diagnostico_ml="Cuerpo de aceleración o válvula IAC sucia",
        confianza_ml=0.21,
        requiere_revision_humana=True,
    )
    resumen = GeminiRateLimiter._crear_resumen_whatsapp(solicitud, "Gravedad: Media")
    assert "no concluyente" in resumen.lower()
    assert "IAC" not in resumen


def test_resumen_solo_gnv_muestra_calibracion_como_prioridad():
    solicitud = SolicitudGeminiEncolada(
        sintoma=(
            "pierde potencia al acelerar. Combustible confirmado: GNV. "
            "La falla ocurre solo usando GNV; en gasolina funciona bien."
        ),
        diagnostico_ml="Sistema GNV/GLP: diferenciar calibración, presión, filtros e inyectores",
        confianza_ml=0.20,
        requiere_revision_humana=True,
    )
    resumen = GeminiRateLimiter._crear_resumen_whatsapp(solicitud, "Gravedad: Media")
    assert "posible descalibración" in resumen
    assert "Revisar primero la calibración" in resumen
    assert "por confirmar" in resumen
