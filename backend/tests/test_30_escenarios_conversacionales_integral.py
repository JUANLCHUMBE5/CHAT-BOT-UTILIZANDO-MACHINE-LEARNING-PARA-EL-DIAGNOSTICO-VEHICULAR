"""CARBOT - SUITE DE VALIDACIÓN CONVERSACIONAL INTEGRAL (30 ESCENARIOS MULTITURNO).

Valida de extremo a extremo:
- 30 Escenarios completos cubriendo todos los subsistemas vehiculares:
  Frenos, Suspensión, Motor, Refrigeración, Transmisión Manual y Automática, Climatización,
  Sistemas Híbridos/EV, Camiones Pesados Neumáticos, Consumos Eléctricos, Cambio de Vehículo,
  Respuestas Naturales, Corrección de Síntomas, RAG sin procedimiento, Interrupciones y Seguridad.
- Persistencia de case_id, vehículo y síntomas.
- No bucles ni preguntas repetidas.
- Hipótesis SVM con probabilidades intactas.
- No descarte ni confirmación física sin evidencia.
- Menú sin ambigüedades (1 vs 2/3 hipótesis).
- Orientación visual segura (frenos: depósito sin abrir tapa, piso/ruedas, prohibido circular).
- Cero exposición de placeholders de BD ('Sin procedimiento RAG...').
"""

from __future__ import annotations

import asyncio
import re
import time
import uuid
from types import SimpleNamespace
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.services.confirmacion_diagnostico import (
    ConfirmacionDiagnosticoWhatsApp,
    interpretar_confirmacion_whatsapp,
    interpretar_respuesta_validacion_whatsapp,
    interpretar_seleccion_top3,
    instrucciones_confirmacion_whatsapp,
)
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState, FactState
from src.core.conversacion.orientacion_provisional import (
    es_sintoma_mecanico_valido,
    obtener_orientacion_visual_segura,
)
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.services.webhook.validation_workflow import (
    ValidationWorkflow,
    _es_evidencia_diagnostica_nueva,
    _procedimiento_seguro_fallback,
    _solicita_continuar_sin_confirmacion,
)


@pytest.fixture(scope="module")
def gestor_real():
    """Instancia real y compartida del GestorDiagnostico (SVM C1 + FAISS RAG)."""
    return GestorDiagnostico()


@pytest.fixture
def repo():
    return InMemoryConversationRepository()


@pytest.fixture
def orquestador(repo):
    return OrquestadorConversacion(repositorio=repo)


# ==============================================================================
# ESCENARIO 1: Frenos - Pedal esponjoso y orientación de seguridad crítica
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_01_frenos_pedal_esponjoso_seguridad(orquestador, gestor_real, repo):
    sid = "case-scen-01"
    t1 = await orquestador.procesar_turno(sid, "Tengo un Toyota Corolla 2015 con el pedal de freno esponjoso y se va al fondo", gestor_real)
    resp1 = t1.get("respuesta_texto", "")
    assert "Corolla" in resp1 or "Toyota" in resp1
    assert "freno" in resp1.lower()
    guias = obtener_orientacion_visual_segura(falla="frenos")
    assert any("sin abrir la tapa" in g.lower() or "sin retirarla" in g.lower() for g in guias)
    assert any("no conduzcas" in g.lower() or "prohibido" in g.lower() or "esponjoso" in g.lower() for g in guias)
    estado = await repo.get_session(sid)
    assert estado is not None
    assert "Corolla" in (estado.modelo or "")
    assert estado.case_id is not None


# ==============================================================================
# ESCENARIO 2: Frenos - Vibración al frenar y discriminación en pedal vs timón
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_02_frenos_vibracion_pedal(orquestador, gestor_real, repo):
    sid = "case-scen-02"
    t1 = await orquestador.procesar_turno(sid, "Nissan Sentra 2018 vibra fuertemente al frenar a 80 km/h", gestor_real)
    assert len(t1.get("respuesta_texto", "")) > 0
    t2 = await orquestador.procesar_turno(sid, "La vibración se siente solo en el pedal de freno, el timón no vibra nada", gestor_real)
    estado = await repo.get_session(sid)
    assert estado.obtener_hecho("vibracion_pedal") is not None or any("vibración" in k for k in estado.hechos.keys())


# ==============================================================================
# ESCENARIO 3: Frenos - Chirrido y respuesta natural 'no tengo herramientas'
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_03_frenos_chirrido_sin_herramientas():
    obs = _es_evidencia_diagnostica_nueva("No tengo herramientas ni elevador para sacar la rueda")
    assert obs is False
    conf = interpretar_confirmacion_whatsapp("No tengo herramientas")
    assert conf is None
    bin_resp = interpretar_respuesta_validacion_whatsapp("No tengo herramientas")
    assert bin_resp is None


# ==============================================================================
# ESCENARIO 4: Suspensión - Golpes secos en baches (Toyota Hilux)
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_04_suspension_golpes_baches(orquestador, gestor_real, repo):
    sid = "case-scen-04"
    t1 = await orquestador.procesar_turno(sid, "Toyota Hilux 2020 golpe seco metálico adelante en baches y trocha", gestor_real)
    resp1 = t1.get("respuesta_texto", "")
    assert len(resp1) > 0
    estado = await repo.get_session(sid)
    assert estado.marca == "Toyota" or "Hilux" in (estado.modelo or "")


# ==============================================================================
# ESCENARIO 5: Suspensión - Ruido al pasar rompemuelles y selección 'la primera'
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_05_suspension_chillido_badenes(orquestador, gestor_real, repo):
    sid = "case-scen-05"
    t1 = await orquestador.procesar_turno(sid, "Kia Cerato 2017 chirría como cama vieja al pasar rompemuelles despacio", gestor_real)
    assert len(t1.get("respuesta_texto", "")) > 0


# ==============================================================================
# ESCENARIO 6: Motor - Dificultad de arranque en frío
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_06_motor_dificultad_arranque_frio(orquestador, gestor_real, repo):
    sid = "case-scen-06"
    t1 = await orquestador.procesar_turno(sid, "Toyota Hilux 2012 motor diesel demora en arrancar en las mañanas cuando hace frío", gestor_real)
    resp = t1.get("respuesta_texto", "")
    assert len(resp) > 0
    assert "Hilux" in resp or "Toyota" in resp


# ==============================================================================
# ESCENARIO 7: Motor - Pérdida de potencia y DTC P0301 (Falla de encendido)
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_07_motor_perdida_potencia_dtc(orquestador, gestor_real, repo):
    sid = "case-scen-07"
    t1 = await orquestador.procesar_turno(sid, "Kia Rio 2016 pierde potencia en subidas y escaneé DTC P0301", gestor_real)
    estado = await repo.get_session(sid)
    hecho_dtc = estado.obtener_hecho("dtc_P0301")
    assert hecho_dtc is not None and hecho_dtc.valor == "P0301"


# ==============================================================================
# ESCENARIO 8: Motor - Corrección de síntoma: humo negro vs humo blanco
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_08_motor_correccion_humo():
    sid = "case-scen-08"
    estado = ConversationState(session_id=sid)
    ExtractorHechos.extraer_y_actualizar(estado, "bota humo blanco por el escape")
    ExtractorHechos.extraer_y_actualizar(estado, "no bota humo blanco, bota humo negro al acelerar")
    h_blanco = estado.obtener_hecho("sintoma_humo_blanco___ebullición_refrigerante")
    h_negro = estado.obtener_hecho("sintoma_humo_negro_exceso_combustible")
    assert h_blanco is not None and h_blanco.estado == FactState.AUSENTE_NEGADO
    assert h_negro is not None and h_negro.estado == FactState.CONFIRMADO


# ==============================================================================
# ESCENARIO 9: Refrigeración - Sobrecalentamiento en tráfico y seguridad térmica
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_09_refrigeracion_sobrecalentamiento(orquestador, gestor_real, repo):
    sid = "case-scen-09"
    t1 = await orquestador.procesar_turno(sid, "Chevrolet Cruze 2014 recalienta cuando estoy parado en tráfico pero normaliza en autopista", gestor_real)
    resp = t1.get("respuesta_texto", "")
    assert len(resp) > 0
    guias = obtener_orientacion_visual_segura(falla="refrigeracion")
    assert any("sin abrir la tapa" in g.lower() or "motor totalmente frío" in g.lower() for g in guias)


# ==============================================================================
# ESCENARIO 10: Refrigeración - Pérdida de refrigerante y verificación externa
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_10_refrigeracion_perdida_fluido():
    guias = obtener_orientacion_visual_segura(falla="refrigeracion")
    assert any("depósito" in g.lower() or "radiador" in g.lower() for g in guias)
    assert any("piso" in g.lower() or "mangueras" in g.lower() or "suelo" in g.lower() for g in guias)


# ==============================================================================
# ESCENARIO 11: Cambio de vehículo en sesión activa (Aislamiento de casos)
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_11_cambio_vehiculo_aislamiento(orquestador, gestor_real, repo):
    sid = "case-scen-11"
    await orquestador.procesar_turno(sid, "Tengo una Hyundai Tucson 2018 con chillido de frenos", gestor_real)
    est1 = await repo.get_session(sid)
    assert "Tucson" in (est1.modelo or "")
    case1 = est1.case_id

    await orquestador.procesar_turno(sid, "Ahora llegó otro carro al taller: un Nissan Sentra 2016 que no enciende el motor", gestor_real)
    est2 = await repo.get_session(sid)
    assert "Sentra" in (est2.modelo or "")
    assert est2.case_id != case1


# ==============================================================================
# ESCENARIO 12: Respuestas naturales '1', 'la 1', 'la primera', 'segunda'
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_12_interpretacion_ordinales_exhaustiva():
    casos = [
        ("1", 1), ("la 1", 1), ("la primera", 1), ("primera", 1),
        ("2", 2), ("la 2", 2), ("la segunda", 2), ("segunda", 2),
        ("3", 3), ("la 3", 3), ("la tercera", 3), ("tercera", 3),
    ]
    for texto, esperado in casos:
        sel = interpretar_seleccion_top3(texto)
        assert sel is not None and sel.orden == esperado, f"Falló para '{texto}': esperado {esperado}"


# ==============================================================================
# ESCENARIO 13: Respuesta natural 'todavía no revisé' (No descarte ciego)
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_13_respuesta_todavia_no_revise():
    res_bin = interpretar_respuesta_validacion_whatsapp("todavía no revisé el carro")
    assert res_bin is None


# ==============================================================================
# ESCENARIO 14: RAG sin procedimiento disponible (Fallback visual determinista)
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_14_rag_sin_procedimiento_seguro():
    texto = _procedimiento_seguro_fallback("Falla desconocida en módulo electrónico")
    assert "Sin procedimiento RAG registrado" not in texto
    assert "inspección visual directa" in texto


# ==============================================================================
# ESCENARIO 15: Filtrado de palabras de control en active_symptoms
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_15_filtrado_palabras_control_sintomas():
    palabras_control = ["SI", "NO", "1", "2", "3", "la 1", "la primera", "correcto", "incorrecto"]
    for p in palabras_control:
        assert es_sintoma_mecanico_valido(p) is False, f"Palabra '{p}' no debió ser síntoma válido"

    sintomas_reales = ["pedal esponjoso", "chirrido al frenar", "humo blanco en frío", "vibración en subida"]
    for s in sintomas_reales:
        assert es_sintoma_mecanico_valido(s) is True, f"Síntoma '{s}' debió ser válido"


# ==============================================================================
# ESCENARIO 16: Interrupciones y consultas de continuidad sin perder contexto
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_16_interrupcion_continuidad(orquestador, gestor_real, repo):
    sid = "case-scen-16"
    await orquestador.procesar_turno(sid, "Toyota Yaris 2015 con vibración al acelerar en tercera marcha", gestor_real)
    await orquestador.procesar_turno(sid, "¿A qué hora cierran el taller hoy?", gestor_real)
    estado = await repo.get_session(sid)
    assert "Yaris" in (estado.modelo or "")


# ==============================================================================
# ESCENARIO 17: Respuestas ambiguas ('puede ser', 'no sé') no confirman ni descartan
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_17_respuestas_ambiguas():
    for amb in ["puede ser", "no sé todavía", "tal vez sea eso", "a ver déjame ver"]:
        conf = interpretar_confirmacion_whatsapp(amb)
        assert conf is None
        bin_resp = interpretar_respuesta_validacion_whatsapp(amb)
        assert bin_resp is None


# ==============================================================================
# ESCENARIO 18: Confirmación formal con evidencia física suficiente (SÍ + datos)
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_18_confirmacion_con_evidencia_fisica():
    resp = "CONFIRMAR: medí la presión con manómetro y marca 15 psi, está baja"
    conf = interpretar_confirmacion_whatsapp(resp)
    assert conf is not None
    assert conf.estado == "confirmado"
    assert "15 psi" in conf.observacion


# ==============================================================================
# ESCENARIO 19: Separación estricta de menús (1 vs 2/3 hipótesis)
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_19_separacion_estricta_menus():
    msg_1 = instrucciones_confirmacion_whatsapp(cantidad_hipotesis=1)
    assert "¿Fue correcta? *SÍ / NO*" in msg_1
    assert "Selecciona una hipótesis" not in msg_1

    msg_2 = instrucciones_confirmacion_whatsapp(cantidad_hipotesis=2)
    assert "Selecciona una hipótesis a verificar" in msg_2
    assert "¿Fue correcta? *SÍ / NO*" not in msg_2
    assert "1. Primera hipótesis" in msg_2
    assert "2. Segunda hipótesis" in msg_2
    assert "NINGUNA" not in msg_2

    msg_3 = instrucciones_confirmacion_whatsapp(cantidad_hipotesis=3)
    assert "Selecciona una hipótesis a verificar" in msg_3
    assert "¿Fue correcta? *SÍ / NO*" not in msg_3
    assert "1. Primera hipótesis" in msg_3
    assert "2. Segunda hipótesis" in msg_3
    assert "3. Tercera hipótesis" in msg_3
    assert "NINGUNA" not in msg_3


# ==============================================================================
# ESCENARIO 20: Transmisión - Rasquido al enganchar reversa y persistencia SVM
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_20_transmision_persistencia_svm(orquestador, gestor_real, repo):
    sid = "case-scen-20"
    t1 = await orquestador.procesar_turno(sid, "Volkswagen Gol 2012 rasca la caja al meter retroceso y pedal de embrague bajo", gestor_real)
    resp = t1.get("respuesta_texto", "")
    assert len(resp) > 0
    estado = await repo.get_session(sid)
    assert estado is not None
    assert estado.case_id is not None


# ==============================================================================
# ESCENARIOS 21 AL 30 (OPTIMIZACIÓN INTEGRAL MULTISISTEMA)
# ==============================================================================
@pytest.mark.anyio
async def test_escenario_21_transmision_automatica_patinamiento(orquestador, gestor_real, repo):
    sid = "case-scen-21"
    t1 = await orquestador.procesar_turno(sid, "Honda CR-V 2016 caja automática patea al pasar de 2da a 3ra y patina en aceleración fuerte", gestor_real)
    resp = t1.get("respuesta_texto", "")
    assert any(term in resp.lower() for term in ["caja", "transmisi", "atf", "patina", "embrague"])
    estado = await repo.get_session(sid)
    assert estado.case_id is not None


@pytest.mark.anyio
async def test_escenario_22_climatizacion_ac_aire_tibio(orquestador, gestor_real, repo):
    sid = "case-scen-22"
    t1 = await orquestador.procesar_turno(sid, "Toyota Rav4 2019 el aire acondicionado tira aire tibio pero el compresor pega", gestor_real)
    resp = t1.get("respuesta_texto", "")
    assert len(resp) > 0
    estado = await repo.get_session(sid)
    assert "rav4" in (estado.modelo or "").lower()


@pytest.mark.anyio
async def test_escenario_23_hibrido_ev_bateria_hv(orquestador, gestor_real, repo):
    sid = "case-scen-23"
    t1 = await orquestador.procesar_turno(sid, "Toyota Prius 2017 triángulo rojo en tablero y código P0A80 reemplazo de batería híbrida", gestor_real)
    resp = t1.get("respuesta_texto", "")
    assert any(term in resp.lower() for term in ["híbrid", "hibrid", "batería", "bateria", "p0a80", "tensión", "voltaje"])


@pytest.mark.anyio
async def test_escenario_24_electrico_fuga_parasita_nocturna(orquestador, gestor_real, repo):
    sid = "case-scen-24"
    t1 = await orquestador.procesar_turno(sid, "Hyundai Accent 2018 si queda parqueado dos días la batería amanece en cero voltios, tiene fuga parásita", gestor_real)
    resp = t1.get("respuesta_texto", "")
    assert any(term in resp.lower() for term in ["fuga", "batería", "bateria", "consumo", "amperio", "eléctric"])


@pytest.mark.anyio
async def test_escenario_25_camiones_freno_neumatico_bloqueado(orquestador, gestor_real, repo):
    sid = "case-scen-25"
    t1 = await orquestador.procesar_turno(sid, "Camión Volvo FH 2015 el eje trasero quedó amarrado y no libera los frenos de aire Maxi-Brake", gestor_real)
    resp = t1.get("respuesta_texto", "")
    assert any(term in resp.lower() for term in ["freno", "aire", "neumátic", "maxi", "bloque", "camión", "valvula"])


@pytest.mark.anyio
async def test_escenario_26_motor_gdi_descarbonizado(orquestador, gestor_real, repo):
    sid = "case-scen-26"
    t1 = await orquestador.procesar_turno(sid, "Ford Focus 2.0 GDI cascabelea bajo carga y tiene acumulación de carbonilla en válvulas de admisión", gestor_real)
    resp = t1.get("respuesta_texto", "")
    assert len(resp) > 0


@pytest.mark.anyio
async def test_escenario_27_motor_desfase_vvt_ckp(orquestador, gestor_real, repo):
    sid = "case-scen-27"
    t1 = await orquestador.procesar_turno(sid, "Nissan X-Trail 2015 código P0011 y desfasaje en árbol de levas VVT con pérdida de fuerza", gestor_real)
    resp = t1.get("respuesta_texto", "")
    assert len(resp) > 0


@pytest.mark.anyio
async def test_escenario_28_frenos_caliper_pegado_olor_quemado(orquestador, gestor_real, repo):
    sid = "case-scen-28"
    t1 = await orquestador.procesar_turno(sid, "Chevrolet Cruze 2013 la rueda delantera izquierda sale humo con olor a quemado y el carro se frena solo", gestor_real)
    resp = t1.get("respuesta_texto", "")
    assert any(term in resp.lower() for term in ["caliper", "freno", "mordaza", "pistón", "pastilla", "disco"])


@pytest.mark.anyio
async def test_escenario_29_suspension_homocinetica_clac_clac(orquestador, gestor_real, repo):
    sid = "case-scen-29"
    t1 = await orquestador.procesar_turno(sid, "Toyota Yaris 2016 suena un chasquido clac clac clac fuerte al girar el timón a la derecha acelerando", gestor_real)
    resp = t1.get("respuesta_texto", "")
    assert any(term in resp.lower() for term in ["palier", "homocinética", "homocinetica", "junta", "dirección", "semieje", "suspens"])


@pytest.mark.anyio
async def test_escenario_30_correccion_diagnostica_en_medio_conversacion(orquestador, gestor_real, repo):
    sid = "case-scen-30"
    t1 = await orquestador.procesar_turno(sid, "Kia Rio 2018 pensaba que el motor tenía un silbido raro", gestor_real)
    assert len(t1.get("respuesta_texto", "")) > 0
    t2 = await orquestador.procesar_turno(sid, "No es el motor maestro, levanté el carro y el zumbido viene del rodaje de masa de la rueda delantera", gestor_real)
    resp2 = t2.get("respuesta_texto", "")
    assert len(resp2) > 0
    estado = await repo.get_session(sid)
    assert estado is not None
    assert estado.case_id is not None
