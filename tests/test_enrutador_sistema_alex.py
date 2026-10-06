from src.core.diagnostico.coherencia_evidencia import (
    limitar_respuesta,
    preparar_contexto_rag_para_llm,
    priorizar_evidencia,
)
from src.core.diagnostico.enrutador_sistema import (
    areas_para_sistema,
    detectar_areas_tecnicas,
    detectar_sistema_ruteo,
    falla_coincide_con_areas,
    filtrar_candidatos_por_area,
    filtrar_causas,
    resolver_sistema_activo,
    respuesta_menciona_causa_fuera_de_sistema,
)
from src.core.diagnostico.models import PrediccionML
from src.infrastructure.rag.query_builder import construir_consulta_hibrida


def test_inyeccion_y_mezcla_no_se_desvian_a_iac_o_refrigeracion():
    areas = detectar_areas_tecnicas(
        "mezcla pobre, sensor de oxígeno a 0.1 V e inyectores con poco caudal"
    )

    assert areas == ["INYECCION_MEZCLA"]
    assert falla_coincide_con_areas("Inyectores sucios o filtro de combustible obstruido", areas)
    assert not falla_coincide_con_areas("Cuerpo de aceleración o válvula IAC sucia", areas)
    assert not falla_coincide_con_areas("Falla en termostato o motoventilador", areas)


def test_map_es_mas_especifico_que_el_sintoma_secundario_de_ralenti():
    areas = detectar_areas_tecnicas(
        "En ralentí vibra y el escáner muestra la carga absoluta del MAP fuera de rango"
    )

    assert areas == ["ADMISION_MAP"]
    assert not falla_coincide_con_areas("Cuerpo de aceleración o válvula IAC sucia", areas)
    assert areas_para_sistema("combustible_admision", "sensor MAP carga absoluta") == ["ADMISION_MAP"]


def test_refrigeracion_y_encendido_se_detectan_sin_inferir_otras_areas():
    assert detectar_areas_tecnicas("El motor se recalienta; el termostato no abre") == [
        "REFRIGERACION"
    ]
    assert detectar_areas_tecnicas("La bobina no genera chispa y falla bajo carga") == [
        "ENCENDIDO"
    ]


def test_recalentando_en_texto_colloquial_activa_refrigeracion():
    areas = detectar_areas_tecnicas(
        "Mazda 3: el vehículo está recalentando; la temperatura sube en tráfico"
    )

    assert areas == ["REFRIGERACION"]


def test_ruteo_solicitado_para_las_seis_frases_de_regresion():
    casos = {
        "está recalentando": "refrigeracion",
        "es refrigeración no de mezcla": "refrigeracion",
        "tiembla y 500 rpm": "encendido",
        "500 rpm": "ambiguo",
        "patina embrague": "transmision",
        "ruido al frenar": "frenos",
    }

    assert {frase: detectar_sistema_ruteo(frase) for frase in casos} == casos
    assert detectar_sistema_ruteo("Buenas tardes") is None


def test_errores_tipograficos_frecuentes_no_desvian_el_ruteo():
    assert detectar_sistema_ruteo("está recalntar", usar_modelo=False) == "refrigeracion"
    assert detectar_sistema_ruteo("mescla pobre", usar_modelo=False) == "combustible_admision"


def test_yaris_temblores_y_minimo_bajo_enruta_a_encendido_antes_del_svm():
    frases = (
        "El vehículo tiembla en todo momento y el mínimo esta en 500 rpm",
        "tiembla y queda en 500 rpm",
        "Toyota Yaris 2023 tiembla mínimo 500 rpm",
    )
    assert all(detectar_sistema_ruteo(frase, usar_modelo=False) == "encendido" for frase in frases)
    assert detectar_sistema_ruteo("500 rpm", usar_modelo=False) == "ambiguo"
    assert detectar_sistema_ruteo("mínimo bajo", usar_modelo=False) == "ambiguo"


def test_fit_minimo_bajo_con_temblores_negados_no_se_fuerza_a_encendido():
    assert detectar_sistema_ruteo(
        "Honda Fit: no tiembla, solo mínimo bajo", usar_modelo=False
    ) == "ambiguo"


def test_logan_que_se_calienta_en_trafico_se_clasifica_como_sintoma():
    from src.core.intent_classifier import clasificar_intencion_consulta

    assert clasificar_intencion_consulta("Renault Logan se calienta en tráfico") == "diagnostico"


def test_cambio_de_computadora_se_rutea_a_electrico_ecu():
    assert detectar_sistema_ruteo(
        "VW Gol no arranca después de cambiar la computadora", usar_modelo=False
    ) == "electrico_ecu"


def test_refrigeracion_bloquea_hipotesis_de_bateria_inversor_e_hibrido_ev():
    propuestas = [
        "Termostato atascado",
        "Bomba de agua con caudal insuficiente",
        "Batería de alto voltaje defectuosa",
        "Inversor del vehículo eléctrico sobrecalentado",
        "Sistema híbrido de tracción con falla",
        "Falla de motor eléctrico de tracción",
        "O2 degradado",
        "Llantas desalineadas",
        "Embrague patinando",
    ]
    filtradas = filtrar_causas("refrigeracion", propuestas)
    assert filtradas == ["Termostato atascado", "Bomba de agua con caudal insuficiente"]
    assert respuesta_menciona_causa_fuera_de_sistema("refrigeracion", "Inversor EV defectuoso")
    assert respuesta_menciona_causa_fuera_de_sistema("refrigeracion", "Batería híbrida de alto voltaje")


def test_si_no_de_pregunta_de_verificacion_se_trata_como_confirmacion_de_causa():
    from src.core.conversacion.formateador_compacto import _generar_pregunta_contextual
    from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas
    from src.core.conversacion.models import ConversationState, QuestionIntent

    pregunta, intent = _generar_pregunta_contextual("Sensor de mezcla bajo revisión")
    assert "verificar este punto" in pregunta
    assert intent == QuestionIntent.CONFIRMACION_ALTERNATIVA

    estado = ConversationState(session_id="versa-si-no")
    estado.falla_principal = "Inyectores con caudal insuficiente"
    estado.registrar_pregunta(
        intent=intent,
        texto=pregunta,
        hipotesis=[estado.falla_principal],
        incrementar_repregunta=False,
    )
    afirmacion = InterpreteRespuestasCortas.interpretar(estado, "Sí")
    assert afirmacion["categoria_respuesta"] == "DIAGNOSTICO_CONFIRMADO"

    estado.registrar_pregunta(
        intent=intent,
        texto=pregunta,
        hipotesis=[estado.falla_principal],
        incrementar_repregunta=False,
    )
    negacion = InterpreteRespuestasCortas.interpretar(estado, "No")
    assert negacion["categoria_respuesta"] == "DIAGNOSTICO_DESCARTADO"
    assert negacion["diagnostico"] == "Inyectores con caudal insuficiente"


def test_descartar_inyectores_pregunta_por_prueba_de_inyeccion_y_no_repite_pregunta_vaga():
    from src.core.conversacion.filtro_preguntas_discriminantes import FiltroPreguntasDiscriminantes
    from src.core.conversacion.models import ConversationState

    estado = ConversationState(session_id="versa-descarte-inyectores")
    estado.historial_mensajes_usuario = [
        "Nissan Versa: mezcla pobre en el escáner",
        "Encontré que los inyectores no inyectan lo suficiente",
    ]
    pregunta, _ = FiltroPreguntasDiscriminantes.formular(
        estado,
        "Inyectores con caudal insuficiente",
    )
    assert "caudal/patrón de pulverización" in pregunta
    assert "qué falla o resultado encontraste" not in pregunta.lower()
    assert "IAC" not in pregunta


def test_memoria_de_sistema_activo_se_mantiene_y_permite_correccion():
    activo = resolver_sistema_activo("mezcla pobre", None)
    assert activo == "combustible_admision"
    assert resolver_sistema_activo("ya revisé eso", activo) == activo
    assert resolver_sistema_activo("500 rpm", activo) == activo
    assert resolver_sistema_activo("es refrigeración no de mezcla", activo) == "refrigeracion"
    assert resolver_sistema_activo("no es refrigeración", "refrigeracion") == "ambiguo"
    assert resolver_sistema_activo("500 rpm", None) == "ambiguo"
    assert resolver_sistema_activo("500 rpm y tiembla", "ambiguo") == "encendido"
    assert detectar_areas_tecnicas("es refrigeración no de mezcla") == ["REFRIGERACION"]


def test_dos_correcciones_consecutivas_convergen_al_ultimo_sistema_explicito():
    activo = resolver_sistema_activo("mezcla pobre", None)
    activo = resolver_sistema_activo("no es mezcla", activo)
    activo = resolver_sistema_activo("es refrigeración", activo)

    assert activo == "refrigeracion"


def test_replay_completo_del_hilo_mazda_no_repite_top3_fuera_de_refrigeracion():
    # Secuencia anonimizada reproducida del CSV local del 5 de octubre.
    turnos = [
        "El carro empezó a recalentar",
        "En todo momento cuando calienta",
        "Calienta",
        "Si en el escaner la temperatura llega a 80 c y ya empieza a calentar",
        "Es un problema de refrigeración no de mezcla",
    ]
    top3_incorrecto = [
        "Falla en sensor de oxígeno o mezcla rica",
        "Llantas desbalanceadas o desalineadas",
        "Disco de embrague desgastado o patinando",
    ]
    activo = None

    for turno in turnos:
        activo = resolver_sistema_activo(turno, activo)
        assert activo == "refrigeracion", turno
        causas = filtrar_causas(activo, top3_incorrecto, evidencia=" ".join(turnos))
        assert causas == [], turno
        assert respuesta_menciona_causa_fuera_de_sistema(activo, " ".join(top3_incorrecto))


def test_replay_versa_descarta_iac_y_prioriza_evidencia_de_inyectores():
    turnos = [
        "Tiene mezcla pobre y el motor pierde fuerza",
        "El IAC ya lo revise y está bien",
        "Encontré que los inyectores no inyectan lo suficiente",
    ]
    causas = [
        "Cuerpo de aceleración o válvula IAC sucia",
        "Inyectores con caudal insuficiente",
        "Termostato atascado",
        "Sensor MAP fuera de rango",
    ]
    activo = None

    for turno in turnos:
        activo = resolver_sistema_activo(turno, activo)
        assert activo == "combustible_admision", turno

    filtradas = filtrar_causas(activo, causas, evidencia=" ".join(turnos))
    assert "Inyectores con caudal insuficiente" in filtradas
    assert all("iac" not in causa.lower() for causa in filtradas)
    assert all("termostato" not in causa.lower() for causa in filtradas)


def test_suite_dirigida_de_confusiones_chasis_transmision_frenos_al_menos_9_de_10():
    casos = [
        ("La transmisión automática demora en acoplar y golpea", "transmision"),
        ("Patina el embrague al acelerar", "transmision"),
        ("No entran los cambios de la caja", "transmision"),
        ("El pedal vibra solo cuando freno", "frenos"),
        ("Hay ruido al frenar", "frenos"),
        ("Las pastillas de freno rechinan", "frenos"),
        ("El timón vibra a 80 km/h pero al frenar no tiembla", "suspension_direccion"),
        ("Rebota en los baches y golpea la suspensión", "suspension_direccion"),
        ("El volante vibra a velocidad de carretera", "suspension_direccion"),
        ("Se inclina demasiado en las curvas", "suspension_direccion"),
    ]

    aciertos = sum(detectar_sistema_ruteo(texto) == esperado for texto, esperado in casos)

    assert aciertos >= 9, [(texto, esperado, detectar_sistema_ruteo(texto)) for texto, esperado in casos]
    assert aciertos == 10


def test_sistema_activo_se_serializa_en_estado_conversacional():
    from src.core.conversacion.models import ConversationState

    estado = ConversationState(session_id="route-memory-test")
    estado.active_system = "refrigeracion"

    restaurado = ConversationState.from_dict(estado.exportar_dict())

    assert restaurado.active_system == "refrigeracion"
    assert areas_para_sistema(restaurado.active_system) == ["REFRIGERACION"]


def test_ruta_ambigua_de_500_rpm_pide_contexto_sin_llamar_modelos(monkeypatch):
    from src.core.gestor_diagnostico import GestorDiagnostico

    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None

    resultado = gestor.procesar_consulta_texto(
        "500 rpm",
        session_id="route_ambiguous_500rpm",
        proveedor="web",
    )

    assert resultado.modo_diagnostico == "esperando_clarificacion"
    assert resultado.diagnostico_ml == "Consulta Ambigua / Datos Faltantes"
    assert resultado.predicciones_ml == []
    assert resultado.llm_usado is False
    assert "¿ocurre al arrancar, acelerar o frenar?" in resultado.respuesta_texto


def test_filtro_causas_no_cruza_sistemas_ni_inventa_fallback():
    propuestas = [
        "termostato atascado",
        "sensor de oxígeno degradado",
        "embrague patina",
        "falla desconocida sin sistema identificable",
    ]

    assert filtrar_causas("refrigeracion", propuestas) == ["termostato atascado"]
    assert filtrar_causas("refrigeracion", ["sensor de oxígeno degradado"]) == []
    assert filtrar_causas("ambiguo", propuestas) == []
    assert respuesta_menciona_causa_fuera_de_sistema(
        "refrigeracion",
        "Revisa el sensor de oxígeno y las llantas.",
    )
    assert not respuesta_menciona_causa_fuera_de_sistema(
        "refrigeracion",
        "Comprueba si hay fugas de refrigerante y cuándo sube la temperatura.",
    )
    assert filtrar_causas(
        "transmision",
        ["disco de embrague desgastado", "desbalanceo de llantas"],
    ) == ["disco de embrague desgastado"]
    assert filtrar_causas(
        "frenos",
        ["discos de freno deformados", "termostato atascado"],
    ) == ["discos de freno deformados"]


def test_filtros_bloquean_causas_fuera_de_sistema_en_combustion_y_encendido():
    propuestas_combustible = [
        "Termostato atascado",
        "Radiador obstruido",
        "Pastillas de freno gastadas",
        "Inyectores con caudal insuficiente",
    ]
    propuestas_encendido = [
        "Radiador obstruido",
        "Embrague patinando",
        "Bobina de encendido defectuosa",
    ]

    assert filtrar_causas("combustible_admision", propuestas_combustible) == [
        "Inyectores con caudal insuficiente"
    ]
    assert filtrar_causas("encendido", propuestas_encendido) == [
        "Bobina de encendido defectuosa"
    ]


def test_hallazgo_de_inyectores_evitas_repetir_iac_como_causa():
    propuestas = [
        "inyectores sucios o con fuga",
        "cuerpo de aceleración o IAC sucia",
        "radiador obstruido",
    ]

    assert filtrar_causas(
        "combustible_admision",
        propuestas,
        evidencia="los inyectores no inyectan combustible",
    ) == ["inyectores sucios o con fuga"]
    assert respuesta_menciona_causa_fuera_de_sistema(
        "combustible_admision",
        "Vuelve a limpiar la válvula IAC.",
        evidencia="los inyectores no inyectan combustible",
    )


def test_hallazgo_inyectores_prioriza_inyeccion_sobre_o2_sin_cambiar_confianzas():
    predicciones = [
        PrediccionML(falla="Sensor de oxígeno degradado", probabilidad=0.52),
        PrediccionML(falla="Regulador de combustible", probabilidad=0.28),
        PrediccionML(falla="Inyectores obstruidos", probabilidad=0.20),
    ]

    ordenadas, motivo = priorizar_evidencia(
        "Encontré que los injectores no inyectan lo suficiente", predicciones
    )

    assert ordenadas[0].falla == "Inyectores obstruidos"
    assert ordenadas[0].probabilidad == 0.20
    assert "no confirmado" in motivo


def test_motor_tiembla_a_bajas_rpm_ruta_a_encendido_sin_inferir_por_rpm_sola():
    assert detectar_areas_tecnicas("El motor tiembla a 500 rpm en ralentí") == ["ENCENDIDO"]
    assert detectar_areas_tecnicas("El escáner marca 500 rpm") == []


def test_consulta_hibrida_no_agrega_clases_ml_fuera_del_area():
    consulta = construir_consulta_hibrida(
        consulta_usuario="sensor MAP con carga absoluta fuera de rango",
        macro_sistema="MOTOR",
        top_fallas=[
            {"falla": "Cuerpo de aceleración o válvula IAC sucia", "probabilidad": 0.86},
            {"falla": "Inyectores sucios o filtro de combustible", "probabilidad": 0.09},
        ],
        areas_consulta=["ADMISION_MAP"],
    ).lower()

    assert "sensor map" in consulta
    assert "carga absoluta" in consulta
    assert "valvula iac" not in consulta
    assert "inyectores sucios" not in consulta


def test_filtro_rag_descarta_documento_iac_para_consulta_map():
    candidatos = [
        {"titulo": "Procedimiento sensor MAP P0106", "documento": "Verificar presión absoluta del múltiple"},
        {"titulo": "Limpieza de válvula IAC", "documento": "Regular el ralentí del motor"},
    ]

    filtrados = filtrar_candidatos_por_area(candidatos, ["ADMISION_MAP"])

    assert [item["titulo"] for item in filtrados] == ["Procedimiento sensor MAP P0106"]


def test_filtro_rag_falla_cerrado_si_no_hay_procedimiento_del_area():
    candidatos = [
        {"titulo": "Limpieza de válvula IAC", "documento": "Regular el ralentí del motor"},
    ]

    assert filtrar_candidatos_por_area(candidatos, ["ADMISION_MAP"]) == []


def test_respuesta_llm_no_conserva_valores_electricos_ausentes_de_las_fuentes():
    respuesta, limitada = limitar_respuesta(
        "Mida 5.0V en el pin de señal KOEO.",
        [PrediccionML(falla="Inyectores sucios o filtro de combustible obstruido", probabilidad=0.6)],
        contexto_verificado="El síntoma reportado es carga absoluta MAP fuera de rango.",
    )

    assert limitada is True
    assert "5.0V" not in respuesta
    assert "No hay procedimiento compatible verificado" in respuesta


def test_respuesta_llm_bloquea_desconectar_bobinas_en_ralenti():
    respuesta, limitada = limitar_respuesta(
        "Desconecta las bobinas con el motor en marcha al ralentí.",
        [PrediccionML(falla="Cuerpo de aceleración o válvula IAC sucia", probabilidad=0.6)],
        contexto_verificado="Procedimiento de inspección del cuerpo de aceleración.",
    )

    assert limitada is True
    assert "desconecta las bobinas" not in respuesta.lower()


def test_sin_clase_ml_pertinente_pide_una_sola_aclaracion():
    respuesta, limitada = limitar_respuesta(
        "El modelo no pudo determinar la causa.",
        [],
        sin_documento=True,
    )

    assert limitada is True
    assert respuesta.count("¿") == 1 and respuesta.count("?") == 1
    assert "¿Qué código DTC aparece" in respuesta


def test_rag_preliminar_no_se_entrega_al_llm():
    contexto, titulo = preparar_contexto_rag_para_llm(
        "procedimiento candidato",
        "Diagnóstico MAP",
        {
            "manual_oem": "Manual Multimarca referencial",
            "estado_validacion": "corpus_preliminar_taller",
            "auditoria": {
                "verificado_documental": True,
                "auditoria_mecanica_formal_firmada": False,
            },
        },
        corpus_validado=False,
    )

    assert contexto == ""
    assert "pendiente de validación" in titulo


def test_rag_oem_solo_se_entrega_con_validacion_documental_y_de_taller():
    meta = {
        "manual_oem": "Toyota OEM Service Manual 2023",
        "estado_validacion": "validado_oem_taller",
        "auditoria": {
            "verificado_documental": True,
            "auditoria_mecanica_formal_firmada": True,
        },
    }

    assert preparar_contexto_rag_para_llm("paso técnico", "MAP", meta, True) == (
        "paso técnico",
        "MAP",
    )
    meta["manual_oem"] = "Manual Multimarca genérico"
    assert preparar_contexto_rag_para_llm("paso técnico", "MAP", meta, True)[0] == ""


def test_limitar_respuesta_bloquea_prueba_con_limpiador_inflamable():
    respuesta, limitada = limitar_respuesta(
        "Haz la prueba de reacción con limpiador de carburador.",
        [PrediccionML(falla="Falla en sensor de oxígeno o mezcla rica", probabilidad=0.7)],
        contexto_verificado="Sensor de oxígeno y mezcla pobre.",
    )

    assert limitada is True
    assert "No hay procedimiento compatible verificado" in respuesta


def test_caso_map_real_del_modelo_local_se_abstiene_sin_llamar_proveedores(monkeypatch):
    from src.config import settings
    from src.core.gestor_diagnostico import GestorDiagnostico

    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = ""
    gestor._registrar_en_tracker = lambda **kwargs: None

    resultado = gestor.procesar_consulta_texto(
        "Chevrolet Joy 2020: la carga absoluta del sensor MAP está fuera de rango; "
        "en ralentí vibra y pierde fuerza al acelerar en carretera.",
        marca_modelo="Chevrolet Joy 2020",
        session_id="test_map_abstention_offline",
        proveedor="web",
    )

    assert resultado.diagnostico_ml.startswith("Sin hipótesis ML pertinente para admisión")
    assert resultado.confianza_ml == 0.0
    assert resultado.predicciones_ml == []
    assert resultado.predicciones_ml_raw
    assert resultado.llm_usado is False


def test_gemini_recibe_cero_contexto_rag_no_validado_y_su_salida_se_filtra(monkeypatch):
    from src.config import settings
    from src.core.gemini_queue import gemini_rate_limiter
    from src.core.gestor_diagnostico import GestorDiagnostico

    monkeypatch.setattr(settings, "groq_chat_enabled", False)
    monkeypatch.setattr(gemini_rate_limiter, "intentar_adquirir_slot", lambda: True)
    monkeypatch.setattr(gemini_rate_limiter, "registrar_estado_gemini", lambda **kwargs: None)
    gestor = GestorDiagnostico(gemini_api_key="")
    gestor.api_key = "isolated-test-key"
    gestor._registrar_en_tracker = lambda **kwargs: None
    payloads = []

    class MockResponse:
        status_code = 200

        def json(self):
            return {
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": "Mide 5.0 V y rocía limpiador de carburador con el motor en marcha."
                        }]
                    }
                }],
                "usageMetadata": {"promptTokenCount": 20, "candidatesTokenCount": 20},
            }

    def mock_post(url, *, json, headers, timeout):
        payloads.append(json)
        return MockResponse()

    monkeypatch.setattr(gestor._http_session, "post", mock_post)
    resultado = gestor.procesar_consulta_texto(
        "Chevrolet Joy 2020: la carga absoluta del sensor MAP está fuera de rango; "
        "en ralentí vibra y pierde fuerza al acelerar en carretera.",
        marca_modelo="Chevrolet Joy 2020",
        session_id="test_map_mock_llm",
        proveedor="web",
    )

    prompt = payloads[0]["contents"][0]["parts"][0]["text"]
    assert "Fuente RAG omitida" in prompt
    assert "PROCEDIMIENTO: DIAGNÓSTICO DEL SENSOR MAP" not in prompt
    assert resultado.llm_usado is True
    assert resultado.respuesta_limitada is True
    assert "5.0 V" not in resultado.respuesta_texto
    assert "limpiador de carburador" not in resultado.respuesta_texto
