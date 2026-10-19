"""Regresiones públicas de remediación; no constituyen un holdout independiente."""

from copy import deepcopy

import pytest

from src.core.conversacion.gestor_plan_b import GestorPlanB
from src.core.conversacion.models import ConversationState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.session_manager import DiagnosticSession
from src.infrastructure.rag.documental_salida import proteger_salida_conversacional


@pytest.mark.parametrize("texto", [
    "La tolerancia es 0.17 mm; exige rectificado.",
    "PELIGRO: La tolerancia es 0.17 mm; exige rectificado.",
    "CRITICAL_STOP: La tolerancia es 0.17 mm; exige rectificado.",
    "Prerrequisitos: La tolerancia es 0.17 mm; exige rectificado.",
    "Con reloj comparador el salto de referencia no debe superar 0.17 mm.",
    "En el multímetro el valor aceptable no debe superar 0.17 V.",
    "Apriete el perno superior a 98 N.m.",
    "Apriete el perno superior a 98 N·m.",
    "El retorno no debe superar 20 ml por inyector.",
    "En el amperímetro no debe superar 0.05 A.",
])
def test_cifra_sin_procedencia_se_retiene(texto):
    respuesta, confianza, retenida = proteger_salida_conversacional(texto, "Toyota Raize 2024", "¿Cómo comprobar?", False)
    assert retenida and confianza == 0
    assert texto not in respuesta
    assert "documentación OEM validada" in respuesta


def test_medicion_del_mecanico_no_es_una_tolerancia():
    dato = "Medí 9.5 V durante el arranque y 12.6 V en reposo."
    respuesta, _, retenida = proteger_salida_conversacional(dato, "Toyota", dato, False)
    assert not retenida and respuesta == dato
    respuesta, _, retenida = proteger_salida_conversacional(
        "La lectura reportada fue 9.5 V; la tolerancia es 9.5 V y exige rectificado.",
        "Toyota", dato, False,
    )
    assert retenida and "la tolerancia es" not in respuesta
    assert dato in respuesta


def test_cifra_del_usuario_no_autoriza_apriete():
    salida, _, retenida = proteger_salida_conversacional(
        "Apriete el perno superior a 98 N.m.", "Hyundai", "Medí 98 N.m.", False
    )
    assert retenida and "Apriete" not in salida


@pytest.mark.parametrize("mensaje", [
    "No tengo la placa disponible. El freno chirría.",
    "No dispongo de placa. Tengo multímetro.",
])
def test_placa_ausente_no_es_herramienta_ausente(mensaje):
    assert GestorPlanB.detectar_indisponibilidad_en_texto(mensaje) == []


@pytest.mark.anyio
@pytest.mark.parametrize("prefijo", ["¿Qué vehículo recuerdas?", "Gracias por ayudar,", "2.", "Dame detalles:"])
async def test_emergencia_termica_antes_de_memoria_y_cierre(prefijo):
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repo)
    gestor = GestorDiagnostico()
    await orq.procesar_turno("termico", "Toyota Corolla 2018 gasolina, ratea en ralentí", gestor)
    case = (await repo.get_session("termico")).case_id
    mensaje = prefijo + " La temperatura está en zona roja y sale vapor."
    r = await orq.procesar_turno("termico", mensaje, gestor)
    assert r["decision"] == "SEGURIDAD_CRITICA"
    assert "motor" in r["respuesta_texto"].lower()
    assert any(x in r["respuesta_texto"].lower() for x in ("det", "apaga"))
    assert r["case_id"] == case
    assert mensaje in (await repo.get_session("termico")).historial_mensajes_usuario


@pytest.mark.anyio
async def test_common_rail_bloquea_sin_indicar_metodo_de_busqueda():
    orq = OrquestadorConversacion(InMemoryConversationRepository())
    r = await orq.procesar_turno(
        "common-rail", "Toyota Hilux diésel. Voy a aflojar racores con el motor en marcha.",
        GestorDiagnostico(),
    )
    texto = r["respuesta_texto"].casefold()
    assert r["decision"] == "SEGURIDAD_CRITICA"
    assert "no aflojes racores" in texto
    assert "personal capacitado" in texto
    prohibidos = [p for p in ("cartón", "papel", "pinzas", "guantes") if p in texto]
    assert not prohibidos, f"Método inseguro {prohibidos}: {texto}"
    import re

    assert re.search(r"\b\d+(?:[.,]\d+)?\s*bar\b", texto) is None


@pytest.mark.anyio
async def test_fallback_no_publica_tolerancias_genericas():
    o = OrquestadorConversacion(InMemoryConversationRepository())
    g = GestorDiagnostico()
    await o.procesar_turno("disco", "Toyota Raize 2024 gasolina", g)
    r = await o.procesar_turno("disco", "¿Cómo compruebo el disco con reloj comparador paso a paso?", g)
    assert "0.05" not in r["respuesta_texto"] and "0.02" not in r["respuesta_texto"]
    assert "manual" in r["respuesta_texto"].lower()


@pytest.mark.anyio
async def test_turbo_humo_no_mantener_motor_en_marcha():
    o = OrquestadorConversacion(InMemoryConversationRepository())
    r = await o.procesar_turno("turbo", "BMW 320d 2017 diésel, turbo al rojo vivo con humo de aceite", GestorDiagnostico())
    assert r["decision"] == "SEGURIDAD_CRITICA"
    assert "No lo mantengas en ralentí" in r["respuesta_texto"]
    assert "3 a 5" not in r["respuesta_texto"]


@pytest.mark.anyio
async def test_cierre_no_inventa_sintomas():
    repo = InMemoryConversationRepository()
    o = OrquestadorConversacion(repo)
    await o.procesar_turno("cierre", "Gracias maestro", GestorDiagnostico())
    assert not (await repo.get_session("cierre")).active_symptoms


@pytest.mark.anyio
async def test_consulta_oem_despues_del_cierre_no_se_convierte_en_sintoma():
    o = OrquestadorConversacion(InMemoryConversationRepository())
    g = GestorDiagnostico()
    await o.procesar_turno("cierre-oem", "Gracias por la ayuda amigo", g)
    r = await o.procesar_turno(
        "cierre-oem", "¿Qué viscosidad de aceite recomienda Toyota Yaris 2018?", g
    )
    assert "¿El problema aparece" not in r["respuesta_texto"]
    assert "documentación OEM validada" in r["respuesta_texto"]
    assert "corpus_validado=False" in r["respuesta_texto"]


@pytest.mark.anyio
async def test_correccion_vehicular_confirma_modelo_actualizado():
    repo = InMemoryConversationRepository()
    o = OrquestadorConversacion(repo)
    g = GestorDiagnostico()
    await o.procesar_turno("correccion-auto", "Toyota Yaris 2017 tiene vibración al frenar", g)
    r = await o.procesar_turno(
        "correccion-auto", "No es Toyota, me equivoqué de ficha: es un Nissan Sentra 2017", g
    )
    assert r["estado"].marca == "Nissan"
    assert "Sentra" in r["estado"].modelo
    assert "2017" in r["estado"].anio
    assert "Nissan Sentra 2017" in r["respuesta_texto"], (
        r["estado"].last_user_correction, r["estado"].turno_ultima_correccion,
        r["estado"].turno_actual, r["respuesta_texto"],
    )
    assert any("vibración al frenar" in s for s in r["estado"].active_symptoms)


def test_persistencia_preserva_sintoma_literal_y_condicion():
    original = DiagnosticSession("memoria")
    original.case_id = original.conversation_state.case_id = "caso-actual"
    original.agregar_sintoma("misfire en cilindro 2 al acelerar")
    recuperada = DiagnosticSession("memoria")
    recuperada.cargar_contexto(original.exportar_contexto())
    assert "misfire en cilindro 2 al acelerar" in recuperada.sintomas


@pytest.mark.anyio
async def test_dpf_no_inventa_comprobaciones():
    o = OrquestadorConversacion(InMemoryConversationRepository())
    r = await o.procesar_turno("dpf", "Peugeot 308 2019 diésel. ¿Qué condiciones necesito antes de regenerar el DPF?", GestorDiagnostico())
    assert "Habiendo verificado" not in r["respuesta_texto"]
    assert "70" not in r["respuesta_texto"] and "80" not in r["respuesta_texto"]


@pytest.mark.anyio
async def test_etiqueta_critica_no_autoriza_respuesta_insegura(monkeypatch):
    o = OrquestadorConversacion(InMemoryConversationRepository())
    estado = ConversationState(session_id="control")

    async def respuesta_insegura(**kwargs):
        return {
            "estado": estado, "decision": "SEGURIDAD_CRITICA",
            "respuesta_texto": "CRITICAL_STOP: Abre el tapón del radiador caliente usando un trapo.",
        }

    monkeypatch.setattr(o, "_procesar_turno_interno", respuesta_insegura)
    r = await o.procesar_turno("control", "Voy a abrir el tapón del radiador con el motor hirviendo", GestorDiagnostico())
    assert "usando un trapo" not in r["respuesta_texto"]
    assert "NUNCA abras" in r["respuesta_texto"]


@pytest.mark.anyio
@pytest.mark.parametrize("texto", [
    "Toyota Yaris, tiemvla el timon kuando frena a 80 por ora",
    "Honda City 2019, vibra el volante cuando freno",
    "El auto sacude el volante al frenar suavemente",
])
async def test_vibracion_de_frenado_no_se_cierra_como_desbalanceo(texto):
    o = OrquestadorConversacion(InMemoryConversationRepository())
    r = await o.procesar_turno("frenos", texto, GestorDiagnostico())
    assert r["decision"] == "PREGUNTAR"
    assert "discos" in r["respuesta_texto"] and "reloj comparador" in r["respuesta_texto"]
    assert "balanceo dinámico" not in r["respuesta_texto"]


@pytest.mark.anyio
async def test_sin_reloj_comparador_no_repite_medicion_inviable():
    from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas

    o = OrquestadorConversacion(InMemoryConversationRepository())
    g = GestorDiagnostico()
    inicial = await o.procesar_turno("sin-comparador", "Nissan Sentra 2016 tiembla al frenar", g)
    texto = "No tengo reloj comparador para medir el alabeo"
    interp = InterpreteRespuestasCortas.interpretar(deepcopy(inicial["estado"]), texto)
    assert interp and interp["categoria_respuesta"] == "HERRAMIENTA_INDISPONIBLE", interp
    r = await o.procesar_turno(
        "sin-comparador", texto, g
    )
    assert "reloj_comparador" in r["estado"].herramientas_no_disponibles
    assert "puedes registrar alabeo con reloj comparador" not in r["respuesta_texto"].lower(), (
        r["decision"], r["status"], r["estado"].herramientas_no_disponibles,
        r["estado"].preguntas_realizadas[-2:],
    )
    assert "inspección" in r["respuesta_texto"].lower() or "taller" in r["respuesta_texto"].lower()


def test_procedimiento_legacy_tambien_se_abstiene():
    from src.core.conversacion.orquestador.consultas_tecnicas import ManejadorConsultasTecnicas
    texto = ManejadorConsultasTecnicas._obtener_procedimiento_respaldo("torque de culata paso a paso")
    assert "Nm" not in texto and "90°" not in texto
    assert "No dispongo de documentación OEM validada" in texto


@pytest.mark.anyio
async def test_dos_voltajes_no_pierden_condicion_ni_declaran_normalidad():
    o = OrquestadorConversacion(InMemoryConversationRepository())
    g = GestorDiagnostico()
    await o.procesar_turno("voltajes", "Toyota Yaris 2018, no arranca en frío", g)
    r = await o.procesar_turno(
        "voltajes", "Batería tiene 12.6V con motor apagado, y cuando enciendo el motor baja a 12.1V", g
    )
    assert "12.6" in r["respuesta_texto"] and "12.1" in r["respuesta_texto"]
    medidas = r["estado"].measurements.values()
    assert any(m.get("contexto") == "motor_en_marcha" and m["valor"] == 12.1 for m in medidas)
    assert not r["estado"].obtener_valor_confirmado("voltaje_reposo_normal")


@pytest.mark.anyio
async def test_advertencia_electrica_no_desaparece_por_control_documental():
    o = OrquestadorConversacion(InMemoryConversationRepository())
    r = await o.procesar_turno(
        "tension", "¿Puedo meterle 24 voltios de dos baterías en serie a un alternador de 12V para probar si gira?",
        GestorDiagnostico(),
    )
    assert r["decision"] == "SEGURIDAD_CRITICA"
    assert "No conectes baterías" in r["respuesta_texto"]


@pytest.mark.anyio
async def test_plan_b_turbo_no_deriva_a_frenos():
    o = OrquestadorConversacion(InMemoryConversationRepository())
    g = GestorDiagnostico()
    await o.procesar_turno("vacio", "Toyota Hilux 2017 turbo no carga bien", g)
    r = await o.procesar_turno("vacio", "No tengo bomba de vacío manual", g)
    assert "turbo" in r["respuesta_texto"] and "mangueras" in r["respuesta_texto"]
    assert "disco" not in r["respuesta_texto"] and "freno" not in r["respuesta_texto"]


@pytest.mark.anyio
async def test_purga_gnv_sin_manual_no_indica_aflojar_mangueras_ni_arrancar():
    o = OrquestadorConversacion(InMemoryConversationRepository())
    r = await o.procesar_turno("purga-gnv", "Cómo purgo las mangueras del reductor GNV", GestorDiagnostico())
    texto = r["respuesta_texto"].lower()
    assert "no puedo indicar" in texto and "manual" in texto
    assert "no aflojes mangueras" in texto and "no arranques el motor" in texto
    assert "85-90" not in texto and "chorro continuo" not in texto


def test_no_escaneado_no_significa_sin_codigos():
    from src.core.conversacion.extractor_hechos import ExtractorHechos
    from src.core.conversacion.models import DtcStatus

    s = ConversationState(session_id="dtc")
    assert s.dtc_status == DtcStatus.DTC_DESCONOCIDO
    ExtractorHechos.extraer_y_actualizar(s, "Toyota Hilux diésel, pierde fuerza en subida")
    assert s.dtc_status == DtcStatus.DTC_DESCONOCIDO
    ExtractorHechos.extraer_y_actualizar(s, "Revisé con escáner, no hay códigos DTC")
    assert s.dtc_status == DtcStatus.SIN_DTC


def test_extractor_sin_escaner_no_falla_por_importacion_condicional():
    from src.core.conversacion.extraccion_hechos.comprobaciones_mecanicas import (
        extraer_comprobaciones_mecanicas,
    )
    from src.core.conversacion.models import DtcStatus

    s = ConversationState(session_id="sin-herramienta")
    extraer_comprobaciones_mecanicas(s, "No tengo escáner", "no tengo escaner")
    assert s.dtc_status == DtcStatus.DTC_DESCONOCIDO
    assert "escaner" in s.herramientas_no_disponibles


@pytest.mark.parametrize("valor", [9.0, 14.2, 18.3])
def test_componente_alternador_procede_del_mensaje_no_del_rango(valor):
    from src.core.conversacion.extractor_hechos import ExtractorHechos

    s = ConversationState(session_id="componente")
    ExtractorHechos.extraer_y_actualizar(s, f"El alternador marca {valor} V")
    h = s.obtener_hecho("medicion_voltaje_alternador")
    assert h is not None and str(valor) in h.valor
    assert s.obtener_valor_confirmado("voltaje_reposo_normal") is None


@pytest.mark.anyio
async def test_ood_recuerda_transmision_sin_contaminar_otro_vehiculo():
    o = OrquestadorConversacion(InMemoryConversationRepository())
    g = GestorDiagnostico()
    await o.procesar_turno("ood", "Volkswagen con caja automática DSG", g)
    r = await o.procesar_turno("ood", "golpea al pasar los cambios cuando calienta", g)
    assert r["decision"] == "ABSTENCION_OOD"
    r = await o.procesar_turno("ood", "Ahora otro vehículo: Toyota Corolla 2018 gasolina, ratea en ralentí", g)
    assert r["decision"] != "ABSTENCION_OOD"
    assert "DSG" not in r["respuesta_texto"]
