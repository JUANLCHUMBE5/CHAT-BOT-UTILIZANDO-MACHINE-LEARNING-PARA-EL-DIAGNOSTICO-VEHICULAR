"""Regresiones de los fallos reproducidos en la auditoría 7c0267c."""
import math
from copy import deepcopy

import pytest
from fastapi import Request

from src.application.services.validacion_taller import calcular_detalles_campos_ficha2, resumir_fases
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.formato_salidas.acciones_prioritarias import (
    extraer_accion_prioritaria,
    generar_pregunta_contextual,
)
from src.core.conversacion.models import ConversationState
from src.core.conversacion.respuestas_cortas.interprete_intenciones import interpretar_respuesta_corta
from src.core.diagnostico.coherencia_evidencia import documento_compatible
from src.core.diagnostico.models import PrediccionML
from src.core.diagnostico.procesador_texto.compatibilidad import filtrar_predicciones_compatibles
from src.core.parser.message_parser import SinglePassMessageParser


@pytest.mark.parametrize("mensaje", ["No pierde fuerza y no vibra", "No vibra al frenar"])
def test_parser_no_afirma_sintomas_negados(mensaje):
    parsed = SinglePassMessageParser.parse(mensaje)
    assert not parsed.sintomas_afirmados
    assert parsed.sintomas_negados


@pytest.mark.parametrize("mensaje", [
    "No generes nuevo diagnóstico; consulta memoria",
    "¿Por qué propones otro caso? No cambies nada",
])
def test_parser_no_inicia_caso_desde_pregunta_o_negacion(mensaje):
    parsed = SinglePassMessageParser.parse(mensaje)
    assert not parsed.es_cambio_caso
    assert parsed.intencion.value == "CONSULTA_TECNICA"


def test_parser_conserva_arranque_con_duracion_natural():
    parsed = SinglePassMessageParser.parse("Demora cinco segundos en arrancar, pero no pierde fuerza")
    assert any(h.campo == "sintoma_demora_arranque" for h in parsed.sintomas_afirmados)
    assert not any("potencia" in h.campo for h in parsed.sintomas_afirmados)


@pytest.mark.parametrize("pieza", ["bujías", "bobinas"])
def test_reemplazo_no_equivale_a_descarte(pieza):
    estado = ConversationState(session_id="reemplazo")
    ExtractorHechos.extraer_y_actualizar(estado, f"Las {pieza} son nuevas, pero sigue la falla")
    assert not estado.hipotesis_descartadas
    assert not any(h.categoria == "componente_descartado" for h in estado.hechos.values())


def test_compresion_no_responde_como_presion_de_riel():
    estado = ConversationState(session_id="presion")
    estado.preguntas_realizadas = [{"texto": "¿Cuántos PSI marca el riel?", "intent": "MEDICION_PRESION"}]
    respuesta = interpretar_respuesta_corta(estado, "Compresión de 180 PSI en todos los cilindros")
    assert respuesta is None or respuesta.get("campo") != "medicion_presion"
    ExtractorHechos.extraer_y_actualizar(estado, "Compresión de 180 PSI en todos los cilindros")
    assert not any("combustible" in clave for clave in estado.measurements)
    assert any("compres" in clave for clave in estado.measurements)


def test_embrague_no_recibe_medicion_de_frenos():
    falla = "Desgaste del disco de embrague (patinamiento)"
    accion = extraer_accion_prioritaria(falla)
    assert "reloj comparador" not in accion
    pregunta = generar_pregunta_contextual(falla, estado=ConversationState(session_id="embrague"))
    assert "frenar" not in pregunta[0].lower()


def test_rag_no_ofrece_collarin_manual_a_caja_automatica():
    assert not documento_compatible(
        "Caja automática tarda en entrar reversa",
        "Inspección del collarín de embrague",
        "Comprobar el collarín al accionar el pedal de embrague",
    )


def test_gasolina_filtra_diesel_sin_renormalizar_probabilidades():
    predicciones = [PrediccionML(falla="Fuga Common Rail Diesel", probabilidad=0.6),
                   PrediccionML(falla="Falla en bobinas", probabilidad=0.2)]
    original = deepcopy(predicciones)
    viables, exclusiones = filtrar_predicciones_compatibles("Toyota Corolla gasolina", predicciones)
    assert len(viables) == 1 and viables[0].probabilidad == 0.2
    assert exclusiones[0]["probabilidad_raw"] == 0.6
    assert predicciones == original


@pytest.mark.parametrize("tiempo", [None, 0, -1, math.inf, math.nan])
def test_prdc_no_completa_tiempo_invalido(tiempo):
    completo, cantidad, campos = calcular_detalles_campos_ficha2(
        codigo_registro="SYNTHETIC", fecha_atencion="2026-10-15",
        datos_generales_vehiculo={}, sintomas_reportados="frena mal", descripcion_sintoma="al frenar",
        sistema_afectado_probable="frenos", diagnostico_confirmado=None, tiempo_atencion_minutos=tiempo,
    )
    assert completo == 0
    assert cantidad < 8
    assert not campos["campo_8"]["completo"]


def test_tprd_no_reduce_denominador_por_datos_ausentes():
    resumen = resumir_fases([{"fase": "posttest", "total": 2, "tiempos_evaluados": 1, "minutos": 10,
                             "campos_evaluados": 1, "completos": 1}])
    assert resumen["tiempo_promedio_posttest_min"] is None
    assert resumen["registros_completos_posttest_porcentaje"] is None


@pytest.mark.anyio
async def test_rest_memoria_no_clasifica_ni_modifica_estado(monkeypatch):
    from src.config import settings
    from src.core.gestor_diagnostico import GestorDiagnostico
    from src.core.identidad_conversacional import clave_sesion_rest
    from src.interfaces.api.v1.endpoints.diagnostico import analizar_sintoma
    from src.interfaces.api.v1.schemas import ConsultaDiagnostico
    monkeypatch.setattr(settings.database, "enabled", False)
    gestor = GestorDiagnostico()
    owner = {"taller_id": "00000000-0000-0000-0000-000000000001",
             "usuario_id": "00000000-0000-0000-0000-000000000002"}
    clave = clave_sesion_rest(owner["taller_id"], owner["usuario_id"], "audit-memory", None)
    estado = gestor.session_manager.obtener_o_crear_sesion(clave).conversation_state
    ExtractorHechos.extraer_y_actualizar(estado, "Toyota Corolla 2015 1.8 gasolina. Demora cinco segundos en arrancar. No pierde potencia")
    original = deepcopy(estado.exportar_dict())
    def prohibido(*args, **kwargs):
        raise AssertionError("Consulta de memoria invocó clasificación")
    monkeypatch.setattr(gestor, "procesar_consulta_texto", prohibido)
    request = Request({"type": "http", "method": "POST", "path": "/api/v1/diagnostico/analizar",
                       "headers": [], "client": ("127.0.0.1", 1234)})
    resultado = await analizar_sintoma(request=request, token_payload=owner, gestor=gestor,
        consulta=ConsultaDiagnostico(sintoma="¿Qué síntomas tienes registrados? No generes nuevo diagnóstico", session_id="audit-memory"))
    assert "Memoria técnica registrada" in resultado.respuesta_explicativa
    assert resultado.diagnostico_id is None
    assert estado.exportar_dict() == original


def test_no_inspeccion_no_se_registra_como_comprobacion_fisica():
    estado = ConversationState(session_id="sin-inspeccion")
    ExtractorHechos.extraer_y_actualizar(estado, "No inspeccioné el intercooler; no pude comprobar la fuga")
    assert estado.obtener_hecho("no_comprobado_intercooler") is not None
    assert estado.obtener_hecho("inspeccion_intercooler_reportada") is None


def test_plan_b_embrague_no_hereda_procedimiento_de_frenos():
    from src.core.conversacion.gestor_plan_b import GestorPlanB
    estado = ConversationState(session_id="embrague-plan-b")
    estado.bloquear_herramienta("elevador")
    estado.falla_principal = "Disco de embrague desgastado o patinando"
    plan = GestorPlanB.obtener_plan_b_para_falla(estado.falla_principal, estado)
    assert plan is not None
    assert "embrague" in plan[1]
    assert not any(palabra in plan[1] for palabra in ("pastillas", "rines", "alabeo"))


def test_parser_conserva_polaridades_en_condiciones_distintas():
    dto = SinglePassMessageParser.parse("Vibra al acelerar pero al frenar no vibra nada")
    assert any(h.campo == "sintoma_vibracion" for h in dto.sintomas_afirmados)
    assert any(h.campo == "sintoma_vibracion_frenos" for h in dto.sintomas_negados)


@pytest.mark.parametrize("texto,placa", [
    ("Toyota Yaris ABC-1234 vibra al acelerar en subida", "ABC-1234"),
    ("Toyota Yaris ABC-123 vibra al acelerar", "ABC-123"),
    ("La compresión marca 180 PSI y el código P0301", None),
    ("El motor gira a 2000 rpm", None),
])
def test_placa_multidato_conserva_formato_admitido_sin_capturar_mediciones(texto, placa):
    assert ExtractorHechos.extraer_placa(texto) == placa
