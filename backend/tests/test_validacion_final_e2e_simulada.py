"""Validación final de aceptación E2E con simulación de entrada WhatsApp."""

import pytest

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.fixture
def orquestador():
    repo = InMemoryConversationRepository()
    return OrquestadorConversacion(repositorio=repo)


@pytest.fixture
def gestor():
    return GestorDiagnostico()


@pytest.mark.anyio
async def test_e2e_conversacion_whatsapp_corolla_metrologia(orquestador, gestor):
    """E2E 1: Toyota Corolla 2015 con alabeo de 0.12 mm, evaluación OEM y solicitud de espesor."""
    sid = "wapp_sim_corolla_metrologia_01"

    # Turno 1: Reporte del síntoma inicial
    t1 = "Hola maestro, tengo un Toyota Corolla 2015 placa ABC-123. Al frenar a más de 60 km/h chilla y el pedal vibra bastante."
    res1 = await orquestador.procesar_turno(sid, t1, gestor_diagnostico=gestor)
    assert res1["status"] == "completado"
    # No debe repreguntar por vibración ya descrita
    assert "vibra el volante al frenar" not in res1["respuesta_texto"].lower()

    # Turno 2: Medición de 0.12 mm de alabeo
    t2 = "Medí el alabeo del disco delantero derecho con reloj comparador y dio 0.12 mm"
    res2 = await orquestador.procesar_turno(sid, t2, gestor_diagnostico=gestor)
    assert res2["status"] == "completado"
    resp2 = res2["respuesta_texto"]
    # Verificación de contenido técnico riguroso:
    assert "0.12" in resp2
    assert "0.05" in resp2 or "0.07" in resp2
    assert "OEM" in resp2 or "Toyota" in resp2
    assert "MIN THK" in resp2 or "espesor" in resp2.lower()
    # No debe tener bucle de confirmación prematura "¿Fue correcta? SÍ/NO"
    assert "¿fue correcta la orientación" not in resp2.lower()


@pytest.mark.anyio
async def test_e2e_conversacion_whatsapp_plan_b_sin_elevador(orquestador, gestor):
    """E2E 2: Homocinética / palier con carencia de elevador -> activación de Plan B seguro."""
    sid = "wapp_sim_plan_b_02"

    t1 = "Tengo un Toyota Yaris con placa DEF-456. Siento holgura y ruido en la suspensión al pasar por baches."
    res1 = await orquestador.procesar_turno(sid, t1, gestor_diagnostico=gestor)
    assert res1["status"] in ("completado", "preguntar")

    t2 = "No tengo elevador ni gata hidráulica para levantarlo en el taller."
    res2 = await orquestador.procesar_turno(sid, t2, gestor_diagnostico=gestor)
    assert res2["status"] == "completado"
    resp2 = res2["respuesta_texto"].lower()
    # Debe orientar a prueba en plano sin elevar
    assert any(w in resp2 for w in ("plano", "sin elevar", "vaivén", "piso", "dirección", "precauciones", "seguridad"))
    # No debe ordenar subir el auto
    assert "sube el carro al elevador" not in resp2


@pytest.mark.anyio
async def test_e2e_conversacion_whatsapp_cambio_vehiculo_aislamiento(orquestador, gestor):
    """E2E 3: Cambio de vehículo -> finalización de caso y reinicio de memoria de hechos."""
    sid = "wapp_sim_cambio_vehiculo_03"

    # Caso A: Freno de Corolla
    await orquestador.procesar_turno(sid, "Toyota Corolla 2015 con chillido de frenos", gestor_diagnostico=gestor)
    estado_a = await orquestador.repositorio.get_session(sid)
    assert estado_a.marca == "Toyota"

    # Finalizar caso explícitamente
    await orquestador.finalizar_caso(sid, gestor_diagnostico=gestor)

    # Caso B: Nuevo vehículo en el mismo chat (ej. mecánico atiende otro cliente)
    await orquestador.procesar_turno(
        sid,
        "Ahora ingresó un Hyundai Tucson 2020 placa GHI-789 que no arranca, suena clac seco al dar llave.",
        gestor_diagnostico=gestor,
    )
    estado_b = await orquestador.repositorio.get_session(sid)
    assert estado_b.marca == "Hyundai"
    assert estado_b.modelo == "Tucson"
    assert estado_b.placa == "GHI-789"
    # No deben arrastrarse síntomas de frenos del caso anterior
    assert not any("freno" in str(h.valor).lower() for h in estado_b.hechos.values() if h.categoria == "sintoma")


@pytest.mark.anyio
async def test_e2e_conversacion_whatsapp_descartes_sucesivos_sin_bucle(orquestador, gestor):
    """E2E 4: Descartes sucesivos -> no bucle de repregunta redundante."""
    sid = "wapp_sim_descartes_04"

    t1 = "Nissan Sentra 2016 pierde potencia y tironea al acelerar en subida."
    res1 = await orquestador.procesar_turno(sid, t1, gestor_diagnostico=gestor)
    assert res1["status"] == "completado"

    t2 = "Ya cambié las bujías y las bobinas están nuevas."
    res2 = await orquestador.procesar_turno(sid, t2, gestor_diagnostico=gestor)
    assert res2["status"] == "completado"

    # Verificar que bujías y bobinas no figuren como top-1
    top3 = res2.get("top3_actual") or []
    if top3:
        falla_top1 = top3[0].get("falla", "").lower()
        assert "bujia" not in falla_top1 and "bobina" not in falla_top1


@pytest.mark.anyio
async def test_e2e_conversacion_whatsapp_alerta_seguridad(orquestador, gestor):
    """E2E 5: Alerta de seguridad física (fuga de combustible con motor caliente)."""
    sid = "wapp_sim_seguridad_05"

    t1 = "Hay una fuga de gasolina en el riel de inyectores, gotea combustible sobre el múltiple caliente."
    res1 = await orquestador.procesar_turno(sid, t1, gestor_diagnostico=gestor)
    assert res1["status"] == "completado"
    resp1 = res1["respuesta_texto"].lower()
    # Debe contener advertencia de seguridad/peligro de incendio
    assert any(w in resp1 for w in ("seguridad", "peligro", "incendio", "apagar", "precaución", "riesgo", "fuga"))
