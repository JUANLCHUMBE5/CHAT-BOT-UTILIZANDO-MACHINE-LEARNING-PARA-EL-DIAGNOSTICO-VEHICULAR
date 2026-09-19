"""Regresiones cross-system derivadas del incidente real motor -> transmision."""

from __future__ import annotations

import pytest

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationPhase, ConversationState, EstadoOperativo
from src.core.conversacion.segmentador_casos import (
    DecisionTransicion,
    SegmentadorCasos,
    SubsistemaVehicular,
)
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta


def _estado_diagnosticado(
    *,
    session_id: str,
    campo: str,
    valor: str,
    falla: str,
    estado_operativo: EstadoOperativo = EstadoOperativo.MARCHA,
) -> ConversationState:
    estado = ConversationState(session_id=session_id, case_id=f"case-{session_id}")
    estado.estado_operativo = estado_operativo
    estado.fase = ConversationPhase.RESULTADO
    estado.registrar_hecho(campo, valor, categoria="sintoma")
    estado.top3_actual = [{"falla": falla, "probabilidad": 0.80}]
    return estado


@pytest.mark.parametrize(
    ("estado", "mensaje", "subsistema_destino"),
    [
        (
            _estado_diagnosticado(
                session_id="motor-transmision",
                campo="sintoma_perdida_potencia",
                valor="perdida de potencia y misfire",
                falla="Falla en bujias o bobinas de encendido (misfire)",
            ),
            (
                "Hola, tengo un problema con mi carro automatico. La palanca entra normal en D, "
                "pero la reversa demora en enganchar y luego entra con un golpe."
            ),
            "TRANSMISION",
        ),
        (
            _estado_diagnosticado(
                session_id="transmision-motor",
                campo="sintoma_transmision",
                valor="caja patea al cambiar",
                falla="Falta o degradacion de aceite de caja de cambios",
            ),
            "Tengo otro problema: el motor tironea y pierde fuerza cuando acelero en subida.",
            "MARCHA_MOTOR",
        ),
        (
            _estado_diagnosticado(
                session_id="frenos-suspension",
                campo="sintoma_freno",
                valor="vibracion al frenar",
                falla="Discos de freno alabeados o desgastados",
                estado_operativo=EstadoOperativo.FRENADO,
            ),
            "Tengo otro problema: golpe seco en la suspension al pasar baches.",
            "SUSPENSION",
        ),
        (
            _estado_diagnosticado(
                session_id="electrico-clima",
                campo="sintoma_electrico",
                valor="alternador sin carga",
                falla="Alternador defectuoso o placa de diodos quemada",
            ),
            "Tengo una falla diferente: el aire acondicionado no enfria y sale aire caliente.",
            "CLIMATIZACION",
        ),
    ],
)
def test_cambia_caso_entre_dominios_aunque_estado_operativo_sea_similar(
    estado: ConversationState,
    mensaje: str,
    subsistema_destino: str,
) -> None:
    case_id_anterior = estado.case_id
    assert SegmentadorCasos.detectar_subsistema_texto(mensaje) == SubsistemaVehicular(
        subsistema_destino
    )

    resultado = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario=mensaje,
        estado_detectado_mensaje=EstadoOperativo.MARCHA,
        seniales_mensaje={"senial_marcha": True},
        seniales_heredadas={"senial_marcha": True},
    )

    assert resultado.decision == DecisionTransicion.CAMBIO_DE_CASO
    assert resultado.nuevo_case_id != case_id_anterior


def test_incidente_no_confunde_y_cuando_interno_con_coexistencia() -> None:
    estado = _estado_diagnosticado(
        session_id="incidente-real",
        campo="sintoma_perdida_potencia",
        valor="perdida de potencia y misfire",
        falla="Falla en bujias o bobinas de encendido (misfire)",
    )
    mensaje = (
        "Hola, tengo un problema con mi carro automatico. Cuando pongo la palanca en D entra normal, "
        "pero cuando paso a R demora en enganchar y cuando entra da un golpe."
    )

    resultado = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario=mensaje,
        estado_detectado_mensaje=EstadoOperativo.MARCHA,
        seniales_mensaje={"senial_marcha": True},
        seniales_heredadas={"senial_marcha": True},
    )

    assert resultado.decision == DecisionTransicion.CAMBIO_DE_CASO
    assert resultado.motivo == "NUEVA_QUEJA_PRINCIPAL: MARCHA_MOTOR_A_TRANSMISION"


def test_incidente_genera_consulta_ml_limpia_y_especifica_de_transmision() -> None:
    estado = _estado_diagnosticado(
        session_id="consulta-limpia",
        campo="sintoma_perdida_potencia",
        valor="perdida de potencia y misfire",
        falla="Falla en bujias o bobinas de encendido (misfire)",
    )
    mensaje = (
        "Hola, tengo un problema con mi carro automático. Cuando pongo la palanca en D entra normal, "
        "pero cuando paso a R demora unos segundos en enganchar. A veces tengo que acelerar un poquito "
        "para que recién entre la reversa y cuando entra da un golpe."
    )
    resultado = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario=mensaje,
        estado_detectado_mensaje=EstadoOperativo.MARCHA,
        seniales_mensaje={"senial_marcha": True},
        seniales_heredadas={"senial_marcha": True},
    )
    SegmentadorCasos.archivar_y_limpiar_caso(estado, resultado.nuevo_case_id)
    ExtractorHechos.extraer_y_actualizar(estado, mensaje)

    consulta = SintetizadorConsulta.sintetizar(estado).lower()

    assert "reversa demora en enganchar" in consulta
    assert "reversa entra con golpe" in consulta
    assert "al seleccionar reversa" in consulta
    assert "misfire" not in consulta
    assert "pérdida de potencia" not in consulta


@pytest.mark.parametrize(
    "mensaje",
    [
        "Ademas de vibrar al acelerar, escucho clics en la junta homocinetica al girar.",
        "Tambien vibra al frenar y siento un golpe en la suspension delantera.",
    ],
)
def test_mantiene_caso_cuando_el_usuario_enlaza_sintomas_relacionados(mensaje: str) -> None:
    estado = _estado_diagnosticado(
        session_id=f"relacionado-{len(mensaje)}",
        campo="sintoma_potencia",
        valor="vibracion al acelerar",
        falla="Falla en bujias o bobinas de encendido (misfire)",
    )

    resultado = SegmentadorCasos.evaluar_transicion(
        estado=estado,
        texto_usuario=mensaje,
        estado_detectado_mensaje=EstadoOperativo.MARCHA,
        seniales_mensaje={"senial_marcha": True},
        seniales_heredadas={"senial_marcha": True},
    )

    assert resultado.decision == DecisionTransicion.MANTENER_CASO
    assert "SINTOMAS_COEXISTENTES" in resultado.motivo
