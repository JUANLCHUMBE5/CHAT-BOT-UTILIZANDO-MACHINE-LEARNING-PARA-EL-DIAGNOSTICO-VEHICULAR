"""Regresiones de detección de polaridad clínica y descarte de preguntas contradictorias de Fase 9.14."""

from __future__ import annotations

from src.core.conversacion.compatibilidad_preguntas import CompatibilidadPreguntas
from src.core.conversacion.detector_polaridad import DetectorPolaridad
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.models import (
    ConversationPhase,
    ConversationState,
    EstadoOperativo,
    FactState,
    QuestionIntent,
)
from src.core.conversacion.segmentador_casos import (
    DecisionTransicion,
    SegmentadorCasos,
    SubsistemaVehicular,
)

MENSAJE_INCIDENTE_914 = (
    "Hola, ahora quisiera revisar otro problema. Cuando paso por pistas irregulares o baches escucho un "
    "golpeteo en la parte delantera del carro. En pista lisa casi no se escucha. Al frenar no vibra el volante "
    "y el motor funciona normal. Todavía no he revisado la suspensión."
)


def test_incidente_real_polaridad_y_pregunta_acustica_suspension() -> None:
    """Valida que el incidente real de WhatsApp clasifique negaciones y genere discriminación acústica."""
    estado = ConversationState(session_id="incidente-914", case_id="case-suspension")
    estado.dominio_probable = SubsistemaVehicular.SUSPENSION.value

    ExtractorHechos.extraer_y_actualizar(estado, MENSAJE_INCIDENTE_914)

    # 1. Validación de polaridad de hechos
    assert estado.es_hecho_negado("sintoma_vibración"), "sintoma_vibración debe ser AUSENTE_NEGADO"
    assert estado.es_hecho_negado("funcionamiento_motor"), "funcionamiento_motor debe ser AUSENTE_NEGADO"
    assert estado.es_hecho_no_revisado("revision_suspension"), "revision_suspension debe ser NO_REVISADO"
    assert estado.es_hecho_confirmado("sintoma_ruido_anómalo"), "sintoma_ruido_anómalo debe ser CONFIRMADO"

    # 2. Desacoplamiento de condición subordinada a negación
    assert estado.estado_operativo == EstadoOperativo.MARCHA, "Estado operativo debe ser MARCHA, no FRENADO"
    condicion = estado.obtener_valor_confirmado("condicion_operacion") or ""
    assert "bache" in condicion or "irregular" in condicion

    # 3. Selección de pregunta
    seleccion = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
    assert seleccion is not None
    pregunta, _, intent, candidatas, descartadas = seleccion

    assert intent == QuestionIntent.PRESENCIA_RUIDO
    assert "golpe seco" in pregunta.lower() or "rebote" in pregunta.lower() or "suspensión" in pregunta.lower()

    # 4. Verificar que la pregunta contradictoria de frenos fue descartada si fue evaluada
    assert "al frenar" not in pregunta.lower()
    assert "volante" not in pregunta.lower()


def test_polaridad_distingue_ausente_negado_vs_no_revisado() -> None:
    """Verifica la distinción semántica entre AUSENTE_NEGADO, NO_REVISADO y CONFIRMADO."""
    sintomas = DetectorPolaridad.extraer_sintomas(
        "Escucho un traqueteo fuerte pero al frenar no vibra nada y no se apaga."
    )
    mapa = {campo: st for campo, _, st in sintomas}

    assert mapa.get("sintoma_ruido_anómalo") == FactState.CONFIRMADO
    assert mapa.get("sintoma_vibración") == FactState.AUSENTE_NEGADO
    assert mapa.get("sintoma_apagado_de_motor") == FactState.AUSENTE_NEGADO

    no_rev = DetectorPolaridad.extraer_componentes_no_revisados(
        "Todavía no he revisado la suspensión ni los amortiguadores ni las pastillas de freno."
    )
    campos_no_rev = {campo for campo, _ in no_rev}
    assert "revision_suspension" in campos_no_rev
    assert "revision_amortiguadores" in campos_no_rev


def test_descarte_pregunta_contradictoria_vibracion_frenos() -> None:
    """Verifica que una pregunta que asume vibración sea rechazada con CONTRADICE_HECHO_CONFIRMADO."""
    estado = ConversationState(session_id="test-contradiccion", case_id="case-1")
    estado.dominio_probable = "SUSPENSION"
    estado.registrar_hecho(
        "sintoma_vibración",
        "vibración",
        estado=FactState.AUSENTE_NEGADO,
        categoria="sintoma",
    )

    pregunta_incompatible = "Al frenar, ¿la vibración se siente principalmente en el volante, en el pedal o en todo el vehículo?"
    assert CompatibilidadPreguntas.contradice_hecho_negado(pregunta_incompatible, estado)

    compatible, motivo = CompatibilidadPreguntas.validar(
        QuestionIntent.PRESENCIA_RUIDO,
        pregunta_incompatible,
        estado,
    )
    assert not compatible
    assert motivo == "CONTRADICE_HECHO_CONFIRMADO"


def test_dominio_motor_con_negaciones_no_pregunta_apagado_si_se_nego() -> None:
    """Verifica que en MOTOR las preguntas no contradigan síntomas negados como apagado o check engine."""
    estado = ConversationState(session_id="test-motor-neg", case_id="case-motor")
    estado.dominio_probable = "MARCHA_MOTOR"
    mensaje = "El motor tironea al acelerar fuerte, pero no se apaga nunca y no aparece ninguna luz en el tablero."
    ExtractorHechos.extraer_y_actualizar(estado, mensaje)

    assert estado.es_hecho_negado("sintoma_apagado_de_motor")
    assert estado.es_hecho_negado("sintoma_testigo_check_engine")
    assert estado.es_hecho_confirmado("sintoma_funcionamiento_irregular___misfire")

    pregunta_apagado = "¿El motor se apaga repentinamente al detenerte en un semáforo?"
    assert CompatibilidadPreguntas.contradice_hecho_negado(pregunta_apagado, estado)


def test_dominio_transmision_con_negaciones_no_pregunta_patinado() -> None:
    """Verifica que en TRANSMISIÓN no se pregunte por patinado si el usuario indicó que no patina."""
    estado = ConversationState(session_id="test-trans-neg", case_id="case-trans")
    estado.dominio_probable = "TRANSMISION"
    mensaje = "La caja golpea al pasar a D, pero no patina ninguna marcha y hacia adelante los cambios se sienten normales."
    ExtractorHechos.extraer_y_actualizar(estado, mensaje)

    assert estado.es_hecho_negado("sintoma_patinado_de_transmisión___embrague")
    pregunta_patinado = "¿Sientes que el embrague o la caja patina al acelerar en subida?"
    assert CompatibilidadPreguntas.contradice_hecho_negado(pregunta_patinado, estado)


def test_dominio_frenos_con_negaciones_pedal() -> None:
    """Verifica que en FRENOS si el usuario niega vibración o desvío, se descarte la contradicción."""
    estado = ConversationState(session_id="test-frenos-neg", case_id="case-frenos")
    estado.dominio_probable = "FRENOS"
    mensaje = "Escucho un chillido agudo al frenar pero no vibra el volante ni el pedal."
    ExtractorHechos.extraer_y_actualizar(estado, mensaje)

    assert estado.es_hecho_confirmado("sintoma_ruido_anómalo")
    assert estado.es_hecho_negado("sintoma_vibración")

    pregunta_vib = "Al frenar, ¿la vibración se siente principalmente en el volante, en el pedal o en todo el vehículo?"
    assert CompatibilidadPreguntas.contradice_hecho_negado(pregunta_vib, estado)


def test_segmentador_transicion_con_negaciones_asigna_dominio_correcto() -> None:
    """Verifica que la transición de caso transmision -> suspension asigne el dominio limpio."""
    estado = ConversationState(session_id="incidente-914-transicion", case_id="case-transmision-anterior")
    estado.fase = ConversationPhase.RESULTADO
    estado.dominio_probable = SubsistemaVehicular.TRANSMISION.value
    estado.registrar_hecho("sintoma_demora_reversa", "demora en reversa")
    estado.registrar_pregunta(QuestionIntent.TEMPERATURA_APARICION, "¿Falla en frío o caliente?")

    resultado = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario=MENSAJE_INCIDENTE_914,
        estado_detectado_mensaje=EstadoOperativo.MARCHA,
        seniales_mensaje={"senial_marcha": True},
        seniales_heredadas={"senial_marcha": True},
    )

    assert resultado.decision == DecisionTransicion.CAMBIO_DE_CASO
    assert resultado.dominio_detectado_mensaje == SubsistemaVehicular.SUSPENSION

    # Limpiar caso
    SegmentadorCasos.archivar_y_limpiar_caso(estado, resultado.nuevo_case_id)
    assert estado.case_id == resultado.nuevo_case_id
    assert estado.dominio_probable in (None, "DESCONOCIDO")
    assert estado.preguntas_realizadas == []
    assert estado.hechos == {}
