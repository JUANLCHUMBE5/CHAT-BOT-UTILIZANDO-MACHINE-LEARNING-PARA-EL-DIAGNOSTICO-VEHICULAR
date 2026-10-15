"""Regresiones de causas raíz halladas en la muestra conversacional congelada."""

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.formato_salidas.generador_diagnostico import evitar_respuesta_repetida
from src.core.conversacion.models import ConversationState, DtcStatus, EstadoOperativo, FactState
from src.core.conversacion.segmentacion.evaluador_reglas import evaluar_transicion
from src.core.conversacion.segmentacion.tipos import DecisionTransicion
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta


def actualizar(estado: ConversationState, *mensajes: str) -> ConversationState:
    for turno, mensaje in enumerate(mensajes, start=1):
        estado.turno_actual = turno
        ExtractorHechos.extraer_y_actualizar(estado, mensaje)
    return estado


def test_motor_se_conserva_como_perfil_del_vehiculo():
    estado = actualizar(
        ConversationState("motor"),
        "Nissan Frontier 2018 diésel motor YD25 demora en arrancar.",
    )
    assert estado.motor == "YD25"
    assert "motor YD25" in SintetizadorConsulta.sintetizar(estado)


def test_motorizacion_entre_anio_y_combustible_se_conserva():
    estado = actualizar(
        ConversationState("motor-desplazamiento"),
        "Ford Ranger 2021 3.2 diésel tiene alerta DPF.",
    )
    assert estado.motor == "3.2"


def test_condicion_motor_apagado_no_sobrescribe_motorizacion():
    estado = actualizar(
        ConversationState("motor-no-sobrescribir"),
        "Volkswagen Tiguan 2020 motor 1.4 TSI gasolina.",
        "La wastegate se mueve libre a mano con motor apagado.",
    )
    assert estado.motor == "1.4 TSI"


def test_dtc_negado_no_se_convierte_en_observado():
    estado = actualizar(
        ConversationState("dtc-negado"),
        "No tiene P0087 ni códigos Common Rail; el código presente es P0299.",
    )
    assert estado.obtener_hecho("dtc_P0087").estado == FactState.AUSENTE_NEGADO
    assert estado.obtener_hecho("dtc_P0299").estado == FactState.CONFIRMADO
    assert estado.dtc_status == DtcStatus.DTC_OBSERVADO
    consulta = SintetizadorConsulta.sintetizar(estado)
    assert "código de escáner P0087" not in consulta
    assert "No tiene P0087" in consulta
    assert "P0299" in consulta


def test_mediciones_sucesivas_no_sobrescriben_la_historia():
    estado = actualizar(
        ConversationState("mediciones"),
        "La presión solicitada es 1.55 bar absolutos.",
        "La presión real llega solo a 1.05 bar absolutos.",
        "En ruta ahora llega a 1.48 bar absolutos.",
    )
    valores = {m["valor"] for m in estado.measurements.values() if isinstance(m, dict)}
    assert {1.55, 1.05, 1.48} <= valores
    consulta = SintetizadorConsulta.sintetizar(estado)
    assert all(valor in consulta for valor in ("1.55", "1.05", "1.48"))


def test_extrae_todas_las_mediciones_de_una_misma_clausula():
    estado = actualizar(
        ConversationState("multi-medicion"),
        "La presión diferencial es 38 kPa a 2500 rpm.",
    )
    pares = {(m["valor"], m["unidad"]) for m in estado.measurements.values() if isinstance(m, dict)}
    assert (38.0, "kPa") in pares
    assert (2500.0, "RPM") in pares


def test_grados_celsius_se_registran_sin_perder_lecturas_previas():
    estado = actualizar(
        ConversationState("temperaturas"),
        "En carretera se mantiene cerca de 92 grados Celsius.",
        "En ralentí llegó a 108 grados Celsius según el escáner.",
    )
    valores = {m["valor"] for m in estado.measurements.values() if isinstance(m, dict)}
    assert {92.0, 108.0} <= valores


def test_revision_con_motor_frio_no_cambia_condicion_de_falla():
    estado = actualizar(
        ConversationState("temperatura-contextual"),
        "La falla aparece en caliente después de veinte minutos.",
        "El refrigerante está al nivel correcto con el motor frío.",
    )
    assert estado.obtener_valor_confirmado("temperatura") == "caliente"


def test_negaciones_de_suspension_no_se_convierten_en_fallas():
    estado = actualizar(
        ConversationState("suspension-negada"),
        "La rótula inferior no tiene juego con palanca.",
        "El rodamiento no tiene ruido ni holgura.",
    )
    assert estado.obtener_hecho("rotula_danada") is None
    assert estado.obtener_hecho("rotula_descartada").estado == FactState.DESCARTADO
    assert estado.obtener_hecho("sintoma_rodamiento") is None
    assert estado.obtener_hecho("rodamiento_descartado").estado == FactState.DESCARTADO


def test_movimiento_manual_wastegate_no_confirma_actuador():
    estado = actualizar(
        ConversationState("wastegate"),
        "La wastegate se mueve libre a mano con motor apagado.",
        "No afirmo que el actuador esté bueno porque no medí su recorrido.",
    )
    assert estado.obtener_hecho("actuador_turbo_descartado") is None
    hecho = estado.obtener_hecho("movimiento_wastegate_reportado")
    assert hecho is not None
    assert "no confirmado" in hecho.valor


def test_dos_averias_declaradas_no_generan_aclaracion_repetida():
    estado = actualizar(
        ConversationState("dos-averias"),
        "Ford Ranger 2021 diésel tiene alerta DPF y golpe delantero en baches.",
        "Son dos problemas simultáneos; no mezcles el tren delantero con el motor.",
        "Para el DPF aparece P2463 y potencia limitada.",
    )
    estado.top3_actual = [{"falla": "DPF saturado", "probabilidad": 0.4}]
    resultado = evaluar_transicion(
        estado,
        "El laboratorio reparó el inyector 4 y entregó protocolo de banco.",
        EstadoOperativo.DESCONOCIDO,
        {},
        {},
    )
    assert resultado.decision == DecisionTransicion.MANTENER_CASO
    assert "AVERIAS_SIMULTANEAS_DECLARADAS" in resultado.motivo


def test_resumen_repetido_reconoce_evidencia_nueva_sin_repetirlo():
    estado = ConversationState("respuesta-progresiva")
    diagnostico = "Posible falla en ventilador. Revise fusible, relé y cableado antes de cambiar piezas."
    estado.trazabilidad.append({"respuesta_enviada": diagnostico})
    estado.historial_mensajes_usuario.append("Intercambié el relé y la baja siguió sin activar.")
    respuesta = evitar_respuesta_repetida(
        diagnostico,
        estado,
        evidencia_duplicada=False,
        hechos_nuevos=[{"campo": "rele_intercambiado", "valor": "la falla continúa"}],
    )
    assert "rele intercambiado" in respuesta
    assert "Posible falla en ventilador" not in respuesta
    assert "sin convertirlo" in respuesta
