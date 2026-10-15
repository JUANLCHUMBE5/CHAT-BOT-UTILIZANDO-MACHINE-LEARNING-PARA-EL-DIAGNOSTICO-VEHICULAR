import pytest

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas
from src.core.conversacion.models import (
    ConversationState,
    EstadoOperativo,
    FactState,
    QuestionIntent,
)
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta


def test_anio_de_vehiculo_no_se_convierte_en_lectura_de_peso_o_presion():
    estado = ConversationState(session_id="alex-anio")
    estado.registrar_pregunta(
        QuestionIntent.MEDICION_PRESION,
        "¿Cuántos PSI marca el manómetro?",
    )
    estado.establecer_pregunta_pendiente(
        intent=QuestionIntent.MEDICION_PRESION,
        expected_quantity="presion_combustible",
        expected_units=["PSI", "bar", "kPa"],
    )

    interpretacion = InterpreteRespuestasCortas.interpretar(estado, "Nissan Versa 2016")
    ExtractorHechos.extraer_y_actualizar(estado, "Nissan Versa 2016")

    assert interpretacion is None
    assert estado.anio == "2016"
    assert not estado.measurements
    consulta = SintetizadorConsulta.sintetizar(estado).lower()
    assert "año 2016" in consulta
    assert "2016.0" not in consulta
    assert "medición" not in consulta


def test_evidencia_map_fuera_de_rango_se_conserva_en_consulta_consolidada():
    estado = ConversationState(session_id="alex-map")
    ExtractorHechos.extraer_y_actualizar(
        estado,
        "Tengo problemas con la carga absoluta esta fueron de rango.",
    )

    hecho = estado.obtener_hecho("sensor_map_estado")
    assert hecho is not None
    assert hecho.estado == FactState.CONFIRMADO
    assert hecho.categoria == "medicion"
    assert hecho.texto_crudo == "Tengo problemas con la carga absoluta esta fueron de rango."

    consulta = SintetizadorConsulta.sintetizar(estado).lower()
    assert "carga absoluta" in consulta
    assert "sensor map" in consulta
    assert "fuera de rango" in consulta


def test_mezcla_inyectores_y_sensor_o2_reportados_se_conservan_sin_confirmar_falla():
    estado = ConversationState(session_id="alex-inyeccion-o2")
    texto = (
        "Nissan Versa: el escáner arroja mezcla pobre; encontré que los inyectores "
        "no inyectan lo suficiente. La sonda lambda se queda en 0.1 V, cambié "
        "la sonda y hace lo mismo."
    )

    ExtractorHechos.extraer_y_actualizar(estado, texto)

    mezcla = estado.obtener_hecho("mezcla_pobre_reportada")
    inyectores = estado.obtener_hecho("caudal_inyectores_reportado")
    sensor = estado.obtener_hecho("sensor_oxigeno_reemplazado_reportado")
    consulta = SintetizadorConsulta.sintetizar(estado).lower()

    assert mezcla is not None and mezcla.categoria == "sintoma"
    assert inyectores is not None and inyectores.categoria == "sistema"
    assert sensor is not None and sensor.categoria == "antecedente"
    assert all("confirm" not in hecho.valor.lower() for hecho in (mezcla, inyectores, sensor))
    assert "inyectores no inyectan lo suficiente" in consulta
    assert "sensor de oxígeno reemplazado" in consulta


def test_hallazgo_de_injectores_con_error_ortografico_desbloquea_ruta_de_inyeccion():
    estado = ConversationState(session_id="alex-injectores-typo")
    estado.historial_mensajes_usuario.extend(
        [
            "Se me prende el check del motor y arroja mezcla pobre",
            "Si se conecto el scaner y arroja mezcla pobre en el sistema",
            "Encontré que los injectores no inyectan lo suficiente",
        ]
    )

    ExtractorHechos.extraer_y_actualizar(
        estado,
        "Encontré que los injectores no inyectan lo suficiente",
    )

    hecho = estado.obtener_hecho("caudal_inyectores_reportado")
    assert hecho is not None
    assert hecho.categoria == "sistema"
    assert GeneradorPreguntas.falta_medicion_discriminante_por_area(estado) is False
    assert GeneradorPreguntas.pregunta_por_area(estado) is None


def test_correccion_de_mezcla_en_refrigeracion_no_pide_stft():
    estado = ConversationState(session_id="alex-fiesta-refrigeracion")
    estado.active_system = "refrigeracion"
    estado.historial_mensajes_usuario.extend(
        ["Ford Fiesta se calienta en tráfico", "No es mescla pobre"]
    )

    pregunta = GeneradorPreguntas.pregunta_por_area(estado)

    assert pregunta is not None
    assert "electroventilador" in pregunta[0].lower()
    assert "stft" not in pregunta[0].lower()
    assert "ltft" not in pregunta[0].lower()
    assert GeneradorPreguntas.falta_medicion_discriminante_por_area(estado) is False


def test_hallazgo_maf_se_conserva_y_no_se_confunde_con_map_ni_stft():
    estado = ConversationState(session_id="alex-sentra-maf")
    ExtractorHechos.extraer_y_actualizar(estado, "El MAF da lecturas raras")

    hecho = estado.obtener_hecho("sensor_maf_lectura_anomala_reportada")
    pregunta = GeneradorPreguntas.pregunta_por_area(estado)

    assert hecho is not None
    assert hecho.categoria == "medicion"
    assert pregunta is not None
    assert "maf" in pregunta[0].lower()
    assert "stft" not in pregunta[0].lower()
    assert GeneradorPreguntas.falta_medicion_discriminante_por_area(estado) is False


def test_reemplazo_de_ecu_y_error_de_codificacion_genera_pregunta_especifica():
    estado = ConversationState(session_id="alex-gol-ecu")
    estado.historial_mensajes_usuario.extend(
        ["Volkswagen Gol: cambié la computadora", "Aparece error de codificación"]
    )
    estado.active_system = "electrico_ecu"

    pregunta = GeneradorPreguntas.pregunta_por_area(estado)

    assert pregunta is not None
    assert "número de parte" in pregunta[0].lower()
    assert "inmovilizador" in pregunta[0].lower()


def test_fit_sin_temblor_obtiene_pregunta_de_contexto_no_de_encendido():
    estado = ConversationState(session_id="alex-fit-minimo")
    estado.active_system = "ambiguo"
    estado.historial_mensajes_usuario.extend(
        ["Honda Fit el mínimo está en 500 rpm", "No tiembla, solo el mínimo bajo"]
    )

    pregunta = GeneradorPreguntas.pregunta_por_area(estado)

    assert pregunta is not None
    assert "temblor" in pregunta[0].lower()
    assert "buj" not in pregunta[0].lower()


def test_fit_500_rpm_solo_pregunta_contexto_antes_de_diagnosticar():
    estado = ConversationState(session_id="alex-fit-500-rpm")
    estado.active_system = "ambiguo"
    estado.historial_mensajes_usuario.append("Honda Fit el mínimo está en 500 rpm")

    pregunta = GeneradorPreguntas.pregunta_por_area(estado)

    assert pregunta is not None
    assert "no identifica la causa" in pregunta[0].lower()
    assert "check engine" in pregunta[0].lower()


@pytest.mark.parametrize(
    ("mensaje", "fragmento"),
    [
        (
            "Nissan Versa arroja mezcla pobre en el escáner",
            "STFT/LTFT",
        ),
        (
            "Chevrolet Joy: carga absoluta del sensor MAP fuera de rango",
            "valor exacto de carga absoluta/MAP",
        ),
        (
            "Toyota Yaris: ralentí en 500 RPM",
            None,
        ),
    ],
)
def test_pregunta_area_evitar_consultas_fuera_de_contexto(mensaje, fragmento):
    estado = ConversationState(session_id="alex-pregunta-area")
    estado.historial_mensajes_usuario.append(mensaje)

    resultado = GeneradorPreguntas.pregunta_por_area(estado)

    if fragmento is None:
        assert resultado is None
    else:
        assert resultado is not None
        assert fragmento in resultado[0]


@pytest.mark.parametrize(
    ("mensaje", "requiere_lectura"),
    [
        ("Nissan Versa: escáner muestra mezcla pobre; inyectores con poco caudal", True),
        ("Nissan Versa: mezcla pobre; los injectores no inyectan lo suficiente", False),
        ("Nissan Versa: mezcla pobre, DTC P0171", False),
        ("Nissan Versa: mezcla pobre, STFT +18%", False),
        ("Chevrolet Joy: carga absoluta MAP fuera de rango", True),
        ("Chevrolet Joy: carga absoluta MAP 35 kPa", False),
    ],
)
def test_medicion_discriminante_requerida_segun_area(mensaje, requiere_lectura):
    estado = ConversationState(session_id="alex-area-medicion")
    estado.historial_mensajes_usuario.append(mensaje)

    assert GeneradorPreguntas.falta_medicion_discriminante_por_area(estado) is requiere_lectura


@pytest.mark.anyio
async def test_map_fuera_de_rango_pide_lectura_antes_de_invocar_diagnostico():
    from unittest.mock import MagicMock

    repo = InMemoryConversationRepository()
    gestor = MagicMock()
    del gestor.session_manager

    resultado = await OrquestadorConversacion(repo).procesar_turno(
        "alex-map-sin-lectura",
        "Chevrolet Joy: carga absoluta MAP fuera de rango; pierde potencia detenido y andando.",
        gestor,
    )

    assert resultado["decision"] == "PREGUNTAR"
    assert "valor exacto de carga absoluta/MAP" in resultado["respuesta_texto"]
    gestor.procesar_consulta_texto.assert_not_called()


def test_consulta_consolidada_conserva_aportes_recientes_pruebas_y_descartes():
    estado = ConversationState(session_id="alex-contexto-completo")
    ExtractorHechos.extraer_y_actualizar(
        estado,
        "El sensor de oxígeno marca mezcla pobre y los inyectores no entregan suficiente.",
    )
    estado.registrar_prueba_completada(
        "prueba_inyectores",
        "caudal correcto en banco",
        detalles={"origen": "mecánico"},
    )
    estado.registrar_medicion(
        "stft",
        18.0,
        "%",
        contexto="ralentí",
        prueba="escáner",
    )
    estado.hipotesis_descartadas.append("Inyectores obstruidos")

    consulta = SintetizadorConsulta.sintetizar(estado).lower()

    assert "no entregan suficiente" in consulta
    assert "prueba_inyectores: caudal correcto en banco" in consulta
    assert "stft: 18.0 % (ralentí)" in consulta
    assert "inyectores obstruidos" in consulta


def test_rpm_se_guarda_como_medicion_del_motor_en_ralenti():
    estado = ConversationState(session_id="alex-rpm")
    estado.registrar_pregunta(
        QuestionIntent.MEDICION_TECNICA,
        "¿A cuántas RPM queda el motor en ralentí?",
    )

    interpretacion = InterpreteRespuestasCortas.interpretar(estado, "Se queda en 500 RPM")

    assert interpretacion is not None
    assert interpretacion["campo"] == "medicion_rpm"
    assert estado.estado_operativo == EstadoOperativo.RALENTI
    assert estado.measurements["rpm_motor"]["valor"] == 500.0
    assert estado.measurements["rpm_motor"]["contexto"] == "ralenti"
    consulta = SintetizadorConsulta.sintetizar(estado).lower()
    assert "500.0 rpm en ralent" in consulta
    assert "unidades" not in consulta


def test_revision_generica_no_descarta_silenciosamente_top1():
    estado = ConversationState(session_id="alex-revision")
    estado.falla_principal = "Sensor de oxígeno defectuoso"
    estado.top3_actual = [
        {"falla": "Sensor de oxígeno defectuoso", "probabilidad": 0.55},
        {"falla": "Inyectores obstruidos", "probabilidad": 0.3},
    ]
    estado.registrar_pregunta(
        QuestionIntent.DISCRIMINACION_TOP3,
        "¿Qué comprobación realizaste?",
        hipotesis=["Sensor de oxígeno defectuoso", "Inyectores obstruidos"],
    )

    interpretacion = InterpreteRespuestasCortas.interpretar(
        estado,
        "Ya lo revisé y eso está bien.",
    )

    assert interpretacion is not None
    assert interpretacion["categoria_respuesta"] == "REVISION_AMBIGUA"
    assert not estado.hipotesis_descartadas
    assert estado.obtener_hecho("revision_componente_pendiente").estado == FactState.AMBIGUO


def test_revision_de_punto_de_confirmacion_descarta_la_hipotesis_actual():
    estado = ConversationState(session_id="alex-revision-punto-actual")
    estado.falla_principal = "Cuerpo de aceleración o válvula IAC sucia"
    estado.top3_actual = [
        {"falla": estado.falla_principal, "probabilidad": 0.83},
        {"falla": "Inyectores obstruidos", "probabilidad": 0.12},
    ]
    estado.registrar_pregunta(
        QuestionIntent.CONFIRMACION_ALTERNATIVA,
        "¿Has podido verificar este punto? ¿Fue correcta la hipótesis principal? Sí / No",
        hipotesis=[estado.falla_principal],
    )

    interpretacion = InterpreteRespuestasCortas.interpretar(
        estado,
        "Ya lo revisé y eso está bien",
    )

    assert interpretacion is not None
    assert interpretacion["categoria_respuesta"] == "DIAGNOSTICO_DESCARTADO"
    assert interpretacion["diagnostico"] == estado.falla_principal


def test_no_a_pregunta_de_verificacion_no_repite_el_top3():
    estado = ConversationState(session_id="alex-no-reviso")
    estado.top3_actual = [{"falla": "Inyectores sucios", "probabilidad": 0.6}]
    estado.registrar_pregunta(
        QuestionIntent.COMPONENTE_REVISADO,
        "¿Has podido verificar este punto?",
        hipotesis=["Inyectores sucios"],
    )

    interpretacion = InterpreteRespuestasCortas.interpretar(estado, "No")

    assert interpretacion["categoria_respuesta"] == "NO_REVISADO"
    assert estado.obtener_hecho("estado_inspeccion_previa").estado == FactState.NO_REVISADO


def test_rango_map_sin_lectura_numerica_no_cuenta_como_medicion_concluyente():
    from src.core.conversacion.suficiencia_informacion import EvaluadorSuficiencia

    estado = ConversationState(session_id="alex-map-suficiencia")
    ExtractorHechos.extraer_y_actualizar(
        estado,
        "Tengo problemas con la carga absoluta del MAP, está fuera de rango.",
    )

    es_fuerte, motivo = EvaluadorSuficiencia.tiene_evidencia_fuerte(estado)

    assert not es_fuerte
    assert "Medición técnica confirmada" not in motivo


def test_si_no_responde_a_confirmacion_del_diagnostico_sin_repetir_top3():
    estado = ConversationState(session_id="alex-confirmacion")
    estado.falla_principal = "Inyectores obstruidos"
    estado.registrar_pregunta(
        QuestionIntent.CONFIRMACION_ALTERNATIVA,
        "¿Fue correcta la hipótesis principal? SÍ / NO",
        hipotesis=["Inyectores obstruidos", "Sensor de oxígeno defectuoso"],
    )

    interpretacion = InterpreteRespuestasCortas.interpretar(estado, "Sí")

    assert interpretacion is not None
    assert interpretacion["categoria_respuesta"] == "DIAGNOSTICO_CONFIRMADO"
    assert interpretacion["diagnostico"] == "Inyectores obstruidos"
    assert estado.obtener_valor_confirmado("confirmacion_diagnostico_usuario") == "SI"


@pytest.mark.anyio
async def test_respuesta_ambigua_de_revision_pide_precision_sin_volver_a_diagnosticar():
    from unittest.mock import MagicMock

    repo = InMemoryConversationRepository()
    estado = ConversationState(session_id="alex-e2e-revision")
    estado.top3_actual = [
        {"falla": "Sensor de oxígeno defectuoso", "probabilidad": 0.55},
        {"falla": "Inyectores obstruidos", "probabilidad": 0.3},
    ]
    estado.registrar_pregunta(
        QuestionIntent.DISCRIMINACION_TOP3,
        "¿Qué comprobación realizaste?",
        hipotesis=["Sensor de oxígeno defectuoso", "Inyectores obstruidos"],
    )
    await repo.save_session(estado.session_id, estado)
    gestor = MagicMock()
    del gestor.session_manager

    resultado = await OrquestadorConversacion(repo).procesar_turno(
        estado.session_id,
        "Ya lo revisé y eso está bien",
        gestor,
    )

    assert resultado["decision"] == "PREGUNTAR"
    assert "qué componente o prueba" in resultado["respuesta_texto"].lower()
    assert "posibles causas" not in resultado["respuesta_texto"].lower()
    gestor.procesar_consulta_texto.assert_not_called()


@pytest.mark.anyio
async def test_confirmacion_si_no_repite_resultado_ni_invoca_modelo():
    from unittest.mock import MagicMock

    repo = InMemoryConversationRepository()
    estado = ConversationState(session_id="alex-e2e-confirmacion")
    estado.falla_principal = "Inyectores obstruidos"
    estado.top3_actual = [{"falla": "Inyectores obstruidos", "probabilidad": 0.8}]
    estado.registrar_pregunta(
        QuestionIntent.CONFIRMACION_ALTERNATIVA,
        "¿Fue correcta la hipótesis principal? SÍ / NO",
        hipotesis=["Inyectores obstruidos"],
    )
    await repo.save_session(estado.session_id, estado)
    gestor = MagicMock()
    del gestor.session_manager

    resultado = await OrquestadorConversacion(repo).procesar_turno(
        estado.session_id,
        "Sí",
        gestor,
    )
    estado_final = await repo.get_session(estado.session_id)

    assert resultado["decision"] == "CONFIRMACION"
    assert "registré" in resultado["respuesta_texto"].lower()
    assert "posibles causas" not in resultado["respuesta_texto"].lower()
    assert estado_final.obtener_valor_confirmado("confirmacion_diagnostico_usuario") == "SI"
    gestor.procesar_consulta_texto.assert_not_called()


@pytest.mark.anyio
async def test_dos_si_seguidos_no_reabren_diagnostico_ni_duplican_preguntas():
    from unittest.mock import MagicMock

    repo = InMemoryConversationRepository()
    estado = ConversationState(session_id="alex-confirmacion-si-doble")
    estado.active_system = "combustible_admision"
    estado.falla_principal = "Inyectores obstruidos"
    estado.top3_actual = [{"falla": "Inyectores obstruidos", "probabilidad": 0.8}]
    estado.registrar_pregunta(
        QuestionIntent.CONFIRMACION_ALTERNATIVA,
        "¿Fue correcta la hipótesis principal? SÍ / NO",
        hipotesis=["Inyectores obstruidos"],
    )
    await repo.save_session(estado.session_id, estado)
    gestor = MagicMock()
    del gestor.session_manager

    primera = await OrquestadorConversacion(repo).procesar_turno(estado.session_id, "Sí", gestor)
    preguntas_tras_primera = len(primera["estado"].preguntas_realizadas)
    segunda = await OrquestadorConversacion(repo).procesar_turno(estado.session_id, "Sí", gestor)

    assert primera["decision"] == "CONFIRMACION"
    assert segunda["decision"] == "CONFIRMACION"
    assert len(segunda["estado"].preguntas_realizadas) == preguntas_tras_primera
    assert segunda["estado"].active_system == "combustible_admision"
    assert segunda["estado"].falla_principal == "Inyectores obstruidos"
    gestor.procesar_consulta_texto.assert_not_called()


@pytest.mark.anyio
async def test_no_tengo_la_medicion_no_vuelve_a_clasificar_ni_repite_hipotesis():
    from unittest.mock import MagicMock

    repo = InMemoryConversationRepository()
    estado = ConversationState(session_id="alex-no-medicion")
    estado.historial_mensajes_usuario = ["Mezcla pobre en el escáner"]
    estado.top3_actual = [{"falla": "Inyectores sucios", "probabilidad": 0.04}]
    estado.registrar_pregunta(
        QuestionIntent.MEDICION_TECNICA,
        "¿Qué DTC exacto y qué valores STFT/LTFT muestra el escáner?",
        hipotesis=["Inyectores sucios"],
    )
    await repo.save_session(estado.session_id, estado)
    gestor = MagicMock()
    del gestor.session_manager

    resultado = await OrquestadorConversacion(repo).procesar_turno(
        estado.session_id,
        "No",
        gestor,
    )

    assert resultado["decision"] == "CONCLUSION_TECNICA"
    assert "repetir hipótesis" in resultado["respuesta_texto"].lower()
    assert "posibles causas" not in resultado["respuesta_texto"].lower()
    gestor.procesar_consulta_texto.assert_not_called()


@pytest.mark.anyio
async def test_orquestador_pasa_memoria_al_diagnostico_e_integra_sintesis_llm():
    from types import SimpleNamespace

    repo = InMemoryConversationRepository()
    estado = ConversationState(session_id="alex-e2e-llm-context")
    estado.historial_mensajes_usuario = [
        "Presenta mezcla pobre y pérdida de fuerza.",
        "Ya probé los inyectores en banco y el caudal está correcto.",
    ]
    estado.registrar_hecho("sintoma_base", "mezcla pobre y pérdida de fuerza", categoria="sintoma")
    estado.registrar_hecho("dtc_p0171", "P0171", categoria="dtc")
    estado.registrar_hecho("fuel_trim", "STFT +18%", categoria="medicion")
    estado.completed_tests["prueba_inyectores"] = "caudal correcto en banco"
    estado.top3_actual = [
        {"falla": "Sensor de oxígeno / mezcla pobre", "probabilidad": 0.72},
        {"falla": "Fuga de admisión", "probabilidad": 0.18},
    ]
    await repo.save_session(estado.session_id, estado)

    class GestorDiagnosticoFalso:
        session_manager = None

        def __init__(self):
            self.consulta_enviada = ""

        def procesar_consulta_texto(self, **kwargs):
            self.consulta_enviada = kwargs["texto_usuario"]
            return SimpleNamespace(
                respuesta_texto=(
                    "Los datos apuntan a una condición de mezcla pobre; los inyectores ya "
                    "tienen caudal correcto según lo reportado. ¿Ya mediste el sensor?"
                ),
                diagnostico_ml="Sensor de oxígeno / mezcla pobre",
                confianza_ml=0.72,
                predicciones_ml=[
                    SimpleNamespace(falla="Sensor de oxígeno / mezcla pobre", probabilidad=0.72),
                    SimpleNamespace(falla="Fuga de admisión", probabilidad=0.18),
                ],
                contexto_manual="procedimiento preliminar que no debe mostrarse",
                contexto_manual_verificado="",
                llm_usado=True,
                respuesta_limitada=False,
            )

    gestor = GestorDiagnosticoFalso()
    resultado = await OrquestadorConversacion(repo).procesar_turno(
        estado.session_id,
        "El banco confirma caudal correcto en los inyectores.",
        gestor,
    )

    assert "prueba_inyectores: caudal correcto en banco" in gestor.consulta_enviada
    assert "STFT +18%" in gestor.consulta_enviada
    assert "caudal correcto en los inyectores" in gestor.consulta_enviada
    assert "apuntan a una condición de mezcla pobre" in resultado["respuesta_texto"]
    assert "procedimiento preliminar" not in resultado["respuesta_texto"]
    assert resultado["respuesta_texto"].count("¿") == 1
    assert "¿Ya mediste el sensor?" not in resultado["respuesta_texto"]
    assert resultado["respuesta_texto"].rstrip().endswith("?")


def test_respuesta_llm_se_integra_y_conserva_una_sola_pregunta_controlada():
    from src.core.conversacion.formateador_compacto import FormateadorCompacto

    respuesta = FormateadorCompacto.integrar_respuesta_llm(
        respuesta_llm=(
            "La corrección positiva de combustible y el sensor O2 orientan a mezcla pobre. "
            "¿Ya mediste la presión?"
        ),
        respuesta_determinista=(
            "Posibles causas. Primero revisa el dato nuevo. "
            "¿Qué DTC y valores de STFT/LTFT muestra el escáner?"
        ),
        llm_usado=True,
        respuesta_limitada=False,
    )

    assert "corrección positiva" in respuesta
    assert "¿Qué DTC y valores" in respuesta
    assert respuesta.count("¿") == 1
    assert "¿Ya mediste la presión?" not in respuesta


def test_respuesta_llm_limitada_mantiene_fallback_determinista():
    from src.core.conversacion.formateador_compacto import FormateadorCompacto

    base = "Respuesta segura. ¿Qué lectura observaste?"
    assert FormateadorCompacto.integrar_respuesta_llm(
        respuesta_llm="Usa un valor no verificado.",
        respuesta_determinista=base,
        llm_usado=True,
        respuesta_limitada=True,
    ) == base
import pytest
