"""Regresiones aisladas T07: rechazos, evidencia nueva y repetición de respuestas."""

from src.core.conversacion.avance_preguntas import asegurar_pregunta_util
from src.core.conversacion.clasificador_mensajes import clasificar_mensaje
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.formateador_compacto import FormateadorCompacto
from src.core.conversacion.models import (
    ConversationState,
    FactState,
    FactType,
    QuestionIntent,
)
from src.core.conversacion.segmentador_casos import (
    DecisionTransicion,
    SegmentadorCasos,
    SubsistemaVehicular,
)
from src.core.conversacion.validador_compatibilidad import (
    ValidadorCompatibilidad,
    hipotesis_rechazada_en_texto,
)


def _candidata(falla: str) -> list[dict[str, object]]:
    return [{"falla": falla, "probabilidad": 0.82, "origen_probabilidad": "SVM"}]


def test_componente_revisado_bloquea_alias_de_hipotesis_sin_confirmar_falla():
    estado = ConversationState(session_id="t07-bobina")
    estado.falla_principal = "Falla en bobina de encendido"
    ExtractorHechos.extraer_y_actualizar(estado, "No es la bobina, ya la revisé")

    assert "componente:bobina" in estado.hipotesis_descartadas
    assert estado.obtener_hecho("rechazo_usuario_bobina").estado == FactState.AMBIGUO
    assert estado.obtener_hecho("falla_confirmada_usuario") is None
    assert hipotesis_rechazada_en_texto(
        "Bobinas de encendido defectuosas", estado.hipotesis_descartadas,
    )

    presentadas, exclusiones = ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
        _candidata("Bobinas de encendido defectuosas"), estado,
    )
    assert presentadas == []
    assert exclusiones[0]["motivo"] == "RECHAZADA_PREVIAMENTE_SIN_NUEVA_EVIDENCIA"


def test_bujias_reportadas_normales_no_reaparecen_como_causa():
    estado = ConversationState(session_id="t07-bujias")
    ExtractorHechos.extraer_y_actualizar(estado, "Las bujías están bien")
    presentadas, _ = ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
        _candidata("Bujias desgastadas"), estado,
    )
    assert presentadas == []


def test_respuesta_generica_vincula_revision_a_pieza_de_pregunta_unica():
    estado = ConversationState(session_id="t07-revision-contextual")
    estado.registrar_pregunta(
        QuestionIntent.COMPONENTE_REVISADO,
        "¿Ya verificaste la bobina de encendido?",
        hipotesis=["Bobina de encendido defectuosa"],
    )
    ExtractorHechos.extraer_y_actualizar(estado, "Sí, eso ya lo revisé y está bien")

    assert "componente:bobina" in estado.hipotesis_descartadas
    hecho = estado.obtener_hecho("rechazo_usuario_bobina")
    assert hecho is not None and hecho.estado == FactState.AMBIGUO


def test_respuesta_generica_no_descarta_varias_piezas_de_una_pregunta():
    estado = ConversationState(session_id="t07-revision-ambigua")
    estado.registrar_pregunta(
        QuestionIntent.COMPONENTE_REVISADO,
        "¿Revisaste las bujías y las bobinas?",
        hipotesis=["Bujías o bobinas defectuosas"],
    )
    ExtractorHechos.extraer_y_actualizar(estado, "Eso ya lo revisé y está bien")

    assert "componente:bobina" not in estado.hipotesis_descartadas
    assert "componente:bujia" not in estado.hipotesis_descartadas


def test_dos_descartes_se_conservan_independientemente():
    estado = ConversationState(session_id="t07-dos-descartes")
    ExtractorHechos.extraer_y_actualizar(estado, "No es la bobina, ya la revisé")
    ExtractorHechos.extraer_y_actualizar(estado, "Las bujías están bien")
    assert {"componente:bobina", "componente:bujia"}.issubset(estado.hipotesis_descartadas)


def test_rechazo_verbal_no_se_convierte_en_confirmacion_fisica():
    estado = ConversationState(session_id="t07-rechazo-verbal", falla_principal="Bobina defectuosa")
    estado.registrar_pregunta(
        QuestionIntent.CONFIRMACION_ALTERNATIVA,
        "¿La falla principal coincide con lo que observaste?",
        hipotesis=["Bobina defectuosa"],
    )
    ExtractorHechos.extraer_y_actualizar(estado, "Te estoy diciendo que esa falla ya fue descartada")

    hecho = estado.obtener_hecho("rechazo_usuario_hipotesis_1")
    assert hecho is not None and hecho.estado == FactState.AMBIGUO
    assert "Bobina defectuosa" in estado.hipotesis_descartadas
    assert estado.obtener_hecho("falla_confirmada_usuario") is None


def test_rechazo_generico_solo_aplica_a_hipotesis_principal_evaluada():
    estado = ConversationState(session_id="t07-rechazo-principal", falla_principal="Bobina defectuosa")
    estado.registrar_pregunta(
        QuestionIntent.CONFIRMACION_ALTERNATIVA,
        "¿La falla principal coincide con lo observado?",
        hipotesis=["Bobina defectuosa", "Lectura MAF incorrecta"],
    )
    ExtractorHechos.extraer_y_actualizar(estado, "Te estoy diciendo que esa falla ya fue descartada")

    assert "Bobina defectuosa" in estado.hipotesis_descartadas
    assert "Lectura MAF incorrecta" not in estado.hipotesis_descartadas


def test_resultado_anomalo_nuevo_permite_reconsiderar_sin_inflar_confianza():
    estado = ConversationState(session_id="t07-reconsiderar")
    estado.hipotesis_descartadas.append("componente:bobina")
    presentadas, exclusiones = ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
        _candidata("Bobina de encendido defectuosa"),
        estado,
        nueva_evidencia="Ahora sí se detectó chispa débil en la bobina",
    )
    assert presentadas == _candidata("Bobina de encendido defectuosa")
    assert presentadas[0]["probabilidad"] == 0.82
    assert exclusiones[0]["motivo"] == "RECONSIDERADA_CON_EVIDENCIA_NUEVA"


def test_correccion_de_sistema_archiva_hipotesis_anterior_y_conserva_vehiculo():
    estado = ConversationState(session_id="t07-sistema", case_id="caso-motor")
    estado.placa = "FICT-001"
    estado.dominio_probable = SubsistemaVehicular.MARCHA_MOTOR.value
    estado.falla_principal = "Misfire de motor"
    estado.top3_actual = [{"falla": "Misfire de motor", "probabilidad": 0.82}]
    estado.registrar_hecho(
        "sintoma_funcionamiento_irregular___misfire", "misfire", categoria="sintoma",
        tipo=FactType.SINTOMA,
    )
    mensaje = "No es un problema de motor; el ruido viene de la suspensión."

    assert clasificar_mensaje(mensaje, estado) == "correccion_sistema"
    respuesta, cambio = SegmentadorCasos.resolver_transicion_turno(
        estado,
        mensaje,
        gestor_diagnostico=None,
        session_id=estado.session_id,
        t0=0.0,
        contexto_previo={},
        tipo_mensaje="correccion_sistema",
    )
    assert respuesta is None
    assert cambio.decision == DecisionTransicion.CAMBIO_DE_CASO
    assert cambio.dominio_detectado_mensaje == SubsistemaVehicular.SUSPENSION

    assert estado.case_id == cambio.nuevo_case_id
    assert estado.placa == "FICT-001"
    assert estado.top3_actual == []
    assert estado.falla_principal is None


def test_correccion_de_frio_a_caliente_reemplaza_hecho_y_preserva_historial():
    estado = ConversationState(session_id="t07-temperatura")
    ExtractorHechos.extraer_y_actualizar(estado, "El motor falla en frío")
    ExtractorHechos.extraer_y_actualizar(estado, "Me equivoqué, en realidad falla en caliente")
    assert estado.obtener_valor_confirmado("temperatura") == "caliente"
    assert any(h.get("campo") == "temperatura" for h in estado.hechos_historicos)


def test_pregunta_equivalente_no_se_repite_pero_mantiene_punto_siguiente():
    estado = ConversationState(session_id="t07-pregunta", active_system="combustible_admision")
    estado.registrar_pregunta(
        QuestionIntent.CODIGO_DTC,
        "¿Qué código DTC aparece por la mezcla pobre?",
    )
    respuesta, pregunta = asegurar_pregunta_util(
        estado,
        "¿Qué valores STFT/LTFT o código de falla muestra el escáner para la mezcla?",
        estado.preguntas_realizadas,
    )
    assert pregunta is not None
    assert "stft" not in pregunta.lower()
    assert "dtc" not in pregunta.lower()
    assert "¿Qué código DTC aparece por la mezcla pobre?" not in respuesta


def test_llm_no_reintroduce_componente_rechazado_y_usa_fallback():
    determinista = "La causa sigue sin confirmar. Comparte una medición nueva."
    respuesta = FormateadorCompacto.integrar_respuesta_llm(
        "La bobina de encendido puede estar defectuosa; cámbiala.",
        determinista,
        llm_usado=True,
        respuesta_limitada=False,
        hipotesis_rechazadas=["componente:bobina"],
    )
    assert respuesta == determinista


def test_mismo_resumen_con_evidencia_duplicada_no_repite_diagnostico():
    estado = ConversationState(session_id="t07-resumen")
    estado.trazabilidad.append({
        "respuesta_enviada": "Posible falla: batería descargada. Revisa voltaje y bornes antes de cambiar piezas."
    })
    respuesta = FormateadorCompacto.evitar_respuesta_repetida(
        "Posible falla: batería descargada. Revisa voltaje y bornes antes de cambiar piezas.",
        estado,
        evidencia_duplicada=True,
    )
    assert "batería descargada" not in respuesta.lower()
    assert "evidencia nueva" in respuesta.lower()


def test_diagnostico_repetido_tres_veces_no_reaparece_tras_fallback():
    estado = ConversationState(session_id="t07-repeticion-tres")
    diagnostico = (
        "Posible falla: batería descargada. Revisa voltaje y bornes antes de cambiar piezas."
    )
    estado.trazabilidad.append({"respuesta_enviada": diagnostico})
    fallback = FormateadorCompacto.evitar_respuesta_repetida(
        diagnostico, estado, evidencia_duplicada=True,
    )
    assert "batería descargada" not in fallback.lower()

    estado.trazabilidad.append({"respuesta_enviada": fallback})
    fallback_tras_repeticion = FormateadorCompacto.evitar_respuesta_repetida(
        diagnostico, estado, evidencia_duplicada=True,
    )
    assert "batería descargada" not in fallback_tras_repeticion.lower()
    assert "evidencia nueva" in fallback_tras_repeticion.lower()


def test_memoria_de_veinte_turnos_conserva_dos_descartes():
    estado = ConversationState(session_id="t07-20-turnos")
    ExtractorHechos.extraer_y_actualizar(estado, "No es la bobina, ya la revisé")
    ExtractorHechos.extraer_y_actualizar(estado, "Las bujías están bien")
    for indice in range(20):
        estado.registrar_respuesta(f"respuesta sintética {indice}")
    recuperado = ConversationState.from_dict(estado.exportar_dict())
    assert {"componente:bobina", "componente:bujia"}.issubset(recuperado.hipotesis_descartadas)
    assert len(recuperado.respuestas_obtenidas) == 20
    assert recuperado.obtener_hecho("rechazo_usuario_bobina").estado == FactState.AMBIGUO


def test_respuesta_determinista_disponible_cuando_llm_esta_apagado():
    determinista = "Sigo con la prueba pendiente, sin confirmar una causa."
    respuesta = FormateadorCompacto.integrar_respuesta_llm(
        "", determinista, llm_usado=False, respuesta_limitada=False,
        hipotesis_rechazadas=["componente:bobina"],
    )
    assert respuesta == determinista
