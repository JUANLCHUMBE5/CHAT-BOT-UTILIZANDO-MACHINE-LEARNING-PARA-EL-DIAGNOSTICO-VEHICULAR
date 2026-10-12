"""Pruebas de regresión para correcciones vehiculares con negaciones y orientación cuando SVM se abstiene."""

import pytest

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.formateador_compacto import FormateadorCompacto
from src.core.conversacion.models import ConversationState, FactType
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


def test_negaciones_y_correcciones_vehiculares_aisladas():
    """Valida la resolución correcta de marcas y modelos ante frases compuestas con negaciones y antecedentes."""
    casos = [
        (
            "Disculpa me equivoqué de carro, es un Nissan Sentra 2017, no es Toyota",
            "Nissan",
            "Sentra",
            "2017",
        ),
        ("Es Nissan, no Toyota", "Nissan", None, None),
        ("No es Toyota, es Nissan", "Nissan", None, None),
        ("Me equivoqué, era Suzuki", "Suzuki", None, None),
        ("No es Corolla, es Sentra", None, "Sentra", None),
        ("Es Nissan Sentra, pero antes revisé un Toyota", "Nissan", "Sentra", None),
    ]

    for frase, marca_esp, mod_esp, anio_esp in casos:
        estado = ConversationState(session_id="test_veh_neg")
        estado.marca = "Toyota"
        estado.modelo = "Corolla"
        estado.anio = "2015"
        estado.placa = "B4K-123"

        ExtractorHechos.extraer_y_actualizar(estado, frase)

        if marca_esp:
            assert estado.marca == marca_esp, f"Frase '{frase}': se esperaba marca {marca_esp}, se obtuvo {estado.marca}"
        if mod_esp:
            assert estado.modelo == mod_esp, f"Frase '{frase}': se esperaba modelo {mod_esp}, se obtuvo {estado.modelo}"
        if anio_esp:
            assert estado.anio == anio_esp, f"Frase '{frase}': se esperaba año {anio_esp}, se obtuvo {estado.anio}"
        assert estado.placa == "B4K-123", "La placa debe conservarse tras la corrección"


@pytest.mark.anyio
async def test_conservacion_de_hechos_durante_correccion_vehiculo():
    """Valida que una corrección de vehículo no borre síntomas ni mediciones previas."""
    repo = InMemoryConversationRepository()
    gestor = GestorDiagnostico()
    orquestador = OrquestadorConversacion(repositorio=repo)
    sesion = "test_conservacion_hechos"

    # Turno 1: Registro inicial de síntomas y mediciones
    await orquestador.procesar_turno(
        sesion, "Tengo un Toyota Corolla 2015 placa B4K-123 que tiembla en mínimo", gestor
    )
    await orquestador.procesar_turno(
        sesion, "La batería marca 12.4 V en reposo y baja a 9.6 V al dar arranque", gestor
    )
    st1 = await repo.get_session(sesion)
    assert st1.marca == "Toyota"
    assert st1.placa == "B4K-123"
    assert st1.obtener_hecho("sintoma_vibración") is not None or any("tiembla" in k.lower() or "vibración" in k.lower() for k in st1.hechos.keys())
    assert st1.obtener_hecho("medicion_voltaje_durante_arranque") is not None

    # Turno 2: Corrección en caliente de vehículo
    await orquestador.procesar_turno(
        sesion, "Disculpa me equivoqué de carro, es un Nissan Sentra 2017, no es Toyota", gestor
    )
    st2 = await repo.get_session(sesion)
    assert st2.marca == "Nissan", f"Se esperaba Nissan, se obtuvo {st2.marca}"
    assert st2.modelo == "Sentra"
    assert st2.anio == "2017"
    assert st2.placa == "B4K-123"
    # Los síntomas y mediciones previas deben conservarse intactos
    assert st2.obtener_hecho("medicion_voltaje_durante_arranque") is not None
    assert any("vibración" in k.lower() or "tiembla" in k.lower() or "sintoma" in k.lower() for k in st2.hechos.keys())


def test_formateador_orientacion_refrigeracion_electroventilador_12v():
    """Valida orientación técnica prudente y metrológica ante electroventilador inoperativo a 12V."""
    st = ConversationState(session_id="test_refr_e2e")
    st.placa = "ABC-789"
    st.marca = "Kia"
    st.modelo = "Sportage"
    st.anio = "2019"
    st.active_system = "refrigeracion"
    st.registrar_hecho("sintoma_sobrecalentamiento", "sobrecalentamiento", categoria="sintoma", tipo=FactType.SINTOMA)
    st.registrar_hecho("probado_fusible", "fusible y relé verificados", categoria="componente_descartado")
    st.historial_mensajes_usuario = [
        "Tengo una camioneta Kia Sportage 2019 con placa ABC-789 que recalienta",
        "El electroventilador no prende para nada cuando la aguja pasa de la mitad",
        "Ya revisé el fusible y el relé del ventilador y están buenos",
        "Le metí 12V directo al electroventilador y no gira para nada, está muerto",
    ]

    respuesta = FormateadorCompacto.formatear_respuesta_diagnostico(
        top_hipotesis=[],
        sintoma_original="Le metí 12V directo al electroventilador y no gira para nada, está muerto",
        estado=st,
    )

    assert "Orientación técnica de refrigeración (sin porcentaje SVM)" in respuesta
    assert "electroventilador con 12 V sin respuesta de giro" in respuesta
    assert "falla interna en el motor del electroventilador" in respuesta
    assert "termostato" in respuesta.lower()
    assert "Seguridad" in respuesta
    assert "No tengo una hipótesis ML compatible" not in respuesta


@pytest.mark.anyio
async def test_flujo_completo_kia_sportage_electroventilador():
    """Valida flujo conversacional completo en caso Kia Sportage con abstención prudente del SVM."""
    repo = InMemoryConversationRepository()
    gestor = GestorDiagnostico()
    orquestador = OrquestadorConversacion(repositorio=repo)
    sesion = "test_kia_sportage_flujo"

    r1 = await orquestador.procesar_turno(
        sesion, "Tengo una camioneta Kia Sportage 2019 con placa ABC-789 que recalienta", gestor
    )
    assert r1["estado"].marca == "Kia"
    assert r1["estado"].modelo == "Sportage"
    assert r1["estado"].placa == "ABC-789"

    r2 = await orquestador.procesar_turno(
        sesion, "El electroventilador no prende para nada cuando la aguja pasa de la mitad", gestor
    )
    assert "electroventilador no enciende" in r2["respuesta_texto"].lower() or "orientación técnica" in r2["respuesta_texto"].lower()

    r3 = await orquestador.procesar_turno(
        sesion, "Le metí 12V directo al electroventilador y no gira para nada, está muerto", gestor
    )
    assert "motor del electroventilador" in r3["respuesta_texto"].lower()
    assert "sin porcentaje svm" in r3["respuesta_texto"].lower()
    assert "No tengo una hipótesis ML compatible" not in r3["respuesta_texto"]
