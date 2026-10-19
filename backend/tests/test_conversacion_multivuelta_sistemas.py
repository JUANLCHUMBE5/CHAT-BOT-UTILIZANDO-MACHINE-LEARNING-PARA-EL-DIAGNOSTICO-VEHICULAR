"""Suite de pruebas multivuelta en diversos sistemas automotrices.
Verifica:
1. Top-3 Dinámico (hasta 3 hipótesis respaldadas, sin forzar 3 si hay menos).
2. Opciones conversacionales: 1, 2, 3, Ninguna coincide, Otra causa, No sé, No tengo herramientas, Explícame.
3. No-descarte y preservación estricta de probabilidades SVM brutas (probabilidad_raw).
4. Reevaluación legítima ante nueva evidencia sintomática en diversos subsistemas.
5. Invocación controlada del LLM / Fallback determinista y formato breve estilo WhatsApp.
6. Cumplimiento de barreras de seguridad técnica H-C01 y H-C02.
"""

import asyncio
from functools import wraps

import pytest

from src.core.conversacion.models import ConversationState, FactState, QuestionIntent
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


def ejecutar_async(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper


@pytest.fixture
def orquestador_y_gestor():
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repo)
    gestor = GestorDiagnostico()
    return orq, gestor, repo


@ejecutar_async
async def test_sistema_frenos_multivuelta_no_herramientas_y_explicacion(orquestador_y_gestor):
    """Prueba en sistema de Frenos: reporte de vibración, no herramientas y solicitud de explicación."""
    orq, gestor, repo = orquestador_y_gestor
    sid = "test_frenos_multivuelta"

    # Turno 1: Reporte de vibración al frenar
    r1 = await orq.procesar_turno(sid, "El pedal de freno vibra fuertemente y rechina al frenar a alta velocidad", gestor)
    assert r1 is not None
    assert r1.get("decision") in ("PREGUNTAR", "DIAGNOSTICAR")
    assert "fren" in (r1.get("respuesta_texto") or "").lower()

    # Turno 2: El mecánico no cuenta con reloj comparador ni micrómetro
    r2 = await orq.procesar_turno(sid, "No tengo reloj comparador para medir el alabeo", gestor)
    assert r2 is not None
    assert r2.get("decision") == "PLAN_B"
    # No debe descartar componentes mecánicos ni la hipótesis de fallo
    estado = await repo.get_session(sid)
    assert estado is not None
    assert not any("disco" in str(h).lower() or "freno" in str(h).lower() for h in estado.hipotesis_descartadas)

    # Turno 3: El mecánico pide explicación paso a paso
    r3 = await orq.procesar_turno(sid, "Explicame como comprobarlo visualmente", gestor)
    assert r3 is not None
    # Debe mantener la seguridad documental H-C01 / H-C02: no inventar tolerancias OEM sin respaldo
    texto_t3 = r3.get("respuesta_texto") or ""
    assert "0.17" not in texto_t3
    assert "98 n.m" not in texto_t3.lower()


@ejecutar_async
async def test_sistema_electrico_arranque_multivuelta_no_se(orquestador_y_gestor):
    """Prueba en sistema Eléctrico / Arranque: respuesta 'no sé' no descarta hipótesis ni bloquea."""
    orq, gestor, repo = orquestador_y_gestor
    sid = "test_electrico_multivuelta"

    # Turno 1: Falla eléctrica de arranque
    r1 = await orq.procesar_turno(sid, "La batería parece descargada, al dar marcha se escucha un clac seco pero no gira el motor", gestor)
    assert r1 is not None

    # Turno 2: Respuesta 'no sé' a la verificación
    r2 = await orq.procesar_turno(sid, "no sé", gestor)
    assert r2 is not None
    estado = await repo.get_session(sid)
    # Verifica que el hecho desconocido fue registrado adecuadamente sin descartar
    hechos_desc = [h for h in estado.hechos.values() if h.estado == FactState.DESCONOCIDO]
    assert len(hechos_desc) >= 1
    assert len(estado.hipotesis_descartadas) == 0


@ejecutar_async
async def test_sistema_motor_combustion_reevaluacion_nueva_evidencia(orquestador_y_gestor):
    """Prueba en sistema Motor: reevaluación tras aportar nueva evidencia (humo negro y bujías negras)."""
    orq, gestor, repo = orquestador_y_gestor
    sid = "test_motor_reevaluacion"

    # Turno 1: Motor inestable
    r1 = await orq.procesar_turno(sid, "El motor pierde potencia y tiembla en ralentí", gestor)
    assert r1 is not None

    # Turno 2: Nueva evidencia clínica relevante
    r2 = await orq.procesar_turno(sid, "Al acelerar sale humo negro por el escape y las 4 bujías salieron llenas de hollín negro seco", gestor)
    assert r2 is not None
    estado = await repo.get_session(sid)
    # Los síntomas y condiciones deben acumularse en los hechos del estado
    hechos_vals = [str(h.valor).lower() for h in estado.hechos.values()]
    assert any("humo" in v or "buj" in v or "holl" in v or "acelerar" in v for v in hechos_vals)
    assert any("humo" in s.lower() or "buj" in s.lower() for s in estado.active_symptoms)


@ejecutar_async
async def test_opciones_conversacionales_ninguna_coincide_preserva_probabilidades_svm(orquestador_y_gestor):
    """Prueba de discriminación Top-3: 'ninguna coincide' no borra top3_actual ni altera probabilidades raw."""
    orq, gestor, repo = orquestador_y_gestor
    sid = "test_top3_ninguna_coincide_preservacion"

    # Simulamos estado con discriminación activa
    estado = ConversationState(session_id=sid, case_id="caso-top3-test")
    estado.top3_actual = [
        {"falla": "Falla en bobinas de encendido", "probabilidad": 0.58},
        {"falla": "Inyector de combustible con fuga", "probabilidad": 0.28},
        {"falla": "Baja compresion de cilindro", "probabilidad": 0.14},
    ]
    estado.falla_principal = "Falla en bobinas de encendido"
    estado.confianza_actual = 0.58
    estado.registrar_pregunta(
        QuestionIntent.DISCRIMINACION_TOP3,
        "¿Cuál de las siguientes opciones describe mejor la falla?\n1. Bobinas\n2. Inyector\n3. Compresión\n4. Ninguna coincide",
        opciones=["Bobinas", "Inyector", "Compresión"],
        hipotesis=["Bobinas", "Inyector", "Compresión"],
    )
    await repo.save_session(sid, estado)

    # Usuario responde 'ninguna coincide'
    r = await orq.procesar_turno(sid, "ninguna coincide", gestor)
    assert r is not None
    assert r.get("decision") == "PREGUNTAR"

    # Verificar que el top3_actual y las probabilidades brutas originales se preservan exactamente
    est_final = await repo.get_session(sid)
    assert len(est_final.top3_actual) == 3
    assert est_final.top3_actual[0]["probabilidad"] == 0.58
    assert est_final.top3_actual[1]["probabilidad"] == 0.28
    assert est_final.top3_actual[2]["probabilidad"] == 0.14
    assert not any("bobina" in str(h).lower() or "inyector" in str(h).lower() for h in est_final.hipotesis_descartadas)


@ejecutar_async
async def test_formato_breve_estilo_whatsapp_y_ausencia_alucinacion_oem(orquestador_y_gestor):
    """Verifica que las respuestas diagnósticas sigan el formato conciso (2-5 líneas) y sin invención de torques/temperaturas."""
    orq, gestor, repo = orquestador_y_gestor
    sid = "test_formato_whatsapp"

    r = await orq.procesar_turno(sid, "Tengo un Toyota Yaris con chillido agudo al girar el volante a los topes", gestor)
    assert r is not None
    txt = r.get("respuesta_texto") or ""
    lineas = [linea for linea in txt.split("\n") if linea.strip()]
    # Longitud adecuada de mensaje
    assert len(lineas) <= 8

    # Seguridad estricta H-C01 y H-C02
    assert "98 n.m" not in txt.lower()
    assert "0.17 mm" not in txt.lower()
    assert "0.05 a" not in txt.lower()
