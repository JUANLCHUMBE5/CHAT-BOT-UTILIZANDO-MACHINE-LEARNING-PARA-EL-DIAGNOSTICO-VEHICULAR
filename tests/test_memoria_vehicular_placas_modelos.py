"""Pruebas de regresión automatizadas para Memoria Vehicular, Placas y Modelos (PR 3).

Cubre:
- ESC-01: Corrección de marca y modelo en caliente.
- ESC-24: Preservación de hechos y placa a través de turnos sucesivos.
- ESC-26: Aporte tardío de placa vehicular.
- ESC-30: Consolidación de mensajes fraccionados.
- Corrección de vehículo en un solo mensaje (Toyota -> Nissan Sentra).
- Modelos vehiculares peruanos (Tiida, Swift, RAV4, Cerato, Vitara, Accent).
- Placas peruanas vs códigos DTC (evitar falsos positivos).
- Negación 'no es que no arranque, sí arranca pero se apaga'.
- Componente probado 'ya revisé la batería y está bien'.
"""

import asyncio

import pytest

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState, FactState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.fixture
def test_setup():
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    gestor = GestorDiagnostico()
    return repo, orquestador, gestor


def test_esc01_correccion_marca_modelo_en_caliente(test_setup):
    """ESC-01: Corrección de Marca y Modelo en Caliente."""
    repo, orquestador, gestor = test_setup
    sesion = "test_esc01_sesion"

    async def _run():
        # Turno 1: Nissan Tiida 2012
        await orquestador.procesar_turno(
            sesion, "Tengo un Nissan Tiida 2012 que tironea al acelerar", gestor
        )
        est1 = await repo.get_session(sesion)
        assert est1.marca == "Nissan"
        assert est1.modelo == "Tiida"
        assert est1.anio == "2012"

        # Turno 2: Corrección a Toyota Corolla 2018 con placa B4K-123
        await orquestador.procesar_turno(
            sesion,
            "Disculpa me equivoqué de carro, es un Toyota Corolla 2018 con placa B4K-123",
            gestor,
        )
        est2 = await repo.get_session(sesion)
        assert est2.marca == "Toyota"
        assert est2.modelo == "Corolla"
        assert est2.anio == "2018"
        assert est2.placa == "B4K-123"
        assert est2.marca != "Nissan"

    asyncio.run(_run())


def test_esc24_preservacion_hechos_turnos_sucesivos(test_setup):
    """ESC-24: Preservación de Hechos a Través de Turnos Sucesivos."""
    repo, orquestador, gestor = test_setup
    sesion = "test_esc24_sesion"

    async def _run():
        await orquestador.procesar_turno(
            sesion, "Tengo un Toyota Yaris 2015 con placa ABC-999", gestor
        )
        await orquestador.procesar_turno(
            sesion, "Presenta humo negro en aceleración y consumo alto", gestor
        )
        await orquestador.procesar_turno(
            sesion, "También tiembla un poco en mínimo", gestor
        )

        est = await repo.get_session(sesion)
        assert est.placa == "ABC-999"
        assert est.marca == "Toyota"
        assert est.modelo == "Yaris"
        assert est.anio == "2015"
        assert len(est.hechos) >= 4

    asyncio.run(_run())


def test_esc26_aporte_tardio_placa_vehicular(test_setup):
    """ESC-26: Aporte Tardío de Placa Vehicular."""
    repo, orquestador, gestor = test_setup
    sesion = "test_esc26_sesion"

    async def _run():
        await orquestador.procesar_turno(
            sesion, "El carro bota humo blanco en frío en un Toyota Hilux", gestor
        )
        await orquestador.procesar_turno(
            sesion, "La placa del carro es F7B-890", gestor
        )

        est = await repo.get_session(sesion)
        assert est.placa == "F7B-890"
        assert est.marca == "Toyota"
        assert est.modelo == "Hilux"
        assert any("humo" in k.lower() for k in est.hechos.keys())

    asyncio.run(_run())


def test_esc30_consolidacion_mensajes_fraccionados(test_setup):
    """ESC-30: Consolidación de Mensajes Fraccionados."""
    repo, orquestador, gestor = test_setup
    sesion = "test_esc30_sesion"

    async def _run():
        await orquestador.procesar_turno(sesion, "Nissan Tiida 2011", gestor)
        await orquestador.procesar_turno(sesion, "Bota humo negro", gestor)
        await orquestador.procesar_turno(sesion, "Solo cuando acelero a fondo", gestor)

        est = await repo.get_session(sesion)
        assert est.marca == "Nissan"
        assert "Tiida" in (est.modelo or "")
        assert len(est.hechos) >= 3

    asyncio.run(_run())


def test_correccion_marca_en_un_solo_mensaje():
    """Verifica que 'Es Toyota, perdón, me equivoqué, es Nissan Sentra 2015' fije Nissan Sentra."""
    estado = ConversationState(session_id="test_corr_single")
    ExtractorHechos.extraer_y_actualizar(
        estado, "Es Toyota, perdón, me equivoqué, es Nissan Sentra 2015"
    )
    assert estado.marca == "Nissan"
    assert estado.modelo == "Sentra"
    assert estado.anio == "2015"


def test_modelos_multimarca_peruanos():
    """Verifica reconocimiento de modelos populares peruanos."""
    modelos_a_probar = [
        ("Suzuki Swift 2016", "Suzuki", "Swift"),
        ("Kia Cerato 2017", "Kia", "Cerato"),
        ("Toyota RAV4 2014", "Toyota", "RAV4"),
        ("Hyundai Accent 2015", "Hyundai", "Accent"),
        ("Kia Sorento 2018", "Kia", "Sorento"),
        ("Suzuki Vitara 2019", "Suzuki", "Vitara"),
    ]
    for texto, marca_esp, mod_esp in modelos_a_probar:
        est = ConversationState(session_id="test_modelos")
        ExtractorHechos.extraer_y_actualizar(est, texto)
        assert est.marca == marca_esp, f"Fallo en marca para {texto}"
        assert est.modelo == mod_esp, f"Fallo en modelo para {texto}"


def test_extraccion_placas_vs_dtc():
    """Verifica que las placas peruanas se extraigan y no colisionen con códigos DTC."""
    assert ExtractorHechos.extraer_placa("Mi placa es ABC-123") == "ABC-123"
    assert ExtractorHechos.extraer_placa("Placa B4K-123") == "B4K-123"
    assert ExtractorHechos.extraer_placa("el auto F7B-890 está fallando") == "F7B-890"
    # Código DTC no debe ser tomado como placa
    assert ExtractorHechos.extraer_placa("Arroja código P0301 y P0171") is None


def test_correccion_arranca_pero_se_apaga():
    """Verifica 'No es que no arranque, sí arranca, pero se apaga'."""
    estado = ConversationState(session_id="test_no_arranca_corr")
    # Simular estado previo erróneo
    estado.registrar_hecho("sintoma_motor_no_arranca", "motor no arranca")

    ExtractorHechos.extraer_y_actualizar(
        estado, "No es que no arranque, sí arranca, pero se apaga"
    )
    # Debe eliminar o negar sintoma_motor_no_arranca y registrar arranca y se apaga
    assert estado.obtener_hecho("sintoma_arranca_y_se_apaga") is not None
    hecho_no_arr = estado.obtener_hecho("sintoma_motor_no_arranca")
    assert hecho_no_arr is None or hecho_no_arr.estado == FactState.AUSENTE_NEGADO


def test_descarte_bateria_probada():
    """Verifica que 'Ya revisé la batería y está bien' marque batería como descartada."""
    estado = ConversationState(session_id="test_bat_ok")
    ExtractorHechos.extraer_y_actualizar(estado, "Ya revisé la batería y está bien")
    assert any("bater" in k for k in estado.hechos.keys())
    assert any(
        h.categoria in ("componente_descartado", "rechazo_hipotesis_usuario")
        for h in estado.hechos.values()
    )
