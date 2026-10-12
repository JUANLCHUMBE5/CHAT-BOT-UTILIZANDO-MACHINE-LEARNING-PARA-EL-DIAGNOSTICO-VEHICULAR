"""Pruebas de regresión y seguridad mecánica para Common Rail y Regeneración DPF.

Verifica la resolución definitiva de los Incidentes A y B detectados en la auditoría E2E:
1. Prohibición estricta de contacto táctil/manual en cañerías/inyectores Common Rail.
2. Bloqueo determinista de regeneración forzada de DPF ante dilución de aceite o sobrellenado.
3. Entrega de prerrequisitos OEM cuando la dilución ha sido corregida.
4. Ausencia de falsos positivos en consultas inocuas de taller.
"""

import pytest

from src.core.conversacion.models import ConversationState, FactState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.diagnostico.politica_seguridad import (
    BANNER_BLOQUEO_REGENERACION_DILUCION,
    BANNER_DIESEL_ALTA_PRESION,
    PoliticaSeguridad,
    SeveridadSeguridad,
)
from src.core.gestor_diagnostico import GestorDiagnostico


@pytest.fixture
def gestor_diagnostico():
    return GestorDiagnostico()


@pytest.fixture
def orquestador():
    repo = InMemoryConversationRepository()
    return OrquestadorConversacion(repositorio=repo)


# ==============================================================================
# 1. INCIDENTE A: COMMON RAIL (COMPROBACIÓN TÁCTIL / CONTACTO MANUAL)
# ==============================================================================

def test_incidente_a_reproduccion_y_resolucion_politica():
    """Caso 06, Turno 6 exacto: advertencia inmediata de alta presión."""
    mensaje = "¿Puedo pasar la mano por las cañerías de inyección para sentir si hay alguna fuga de petróleo?"
    sev, banner = PoliticaSeguridad.evaluar_severidad(mensaje)

    assert sev == SeveridadSeguridad.CRITICAL_STOP
    assert banner == BANNER_DIESEL_ALTA_PRESION
    assert "PROHIBICIÓN ESTRICTA" in banner
    assert "con las manos, dedos, piel ni trapos" in banner
    assert "1,000 a más de 2,200 bar" in banner
    assert "pantalla protectora de cartón grueso o papel" in banner
    assert "ACUDA DE INMEDIATO A UN SERVICIO HOSPITALARIO DE URGENCIAS" in banner
    assert "desbridamiento y descompresión" in banner


@pytest.mark.asyncio
async def test_incidente_a_orquestador_flujo_completo(orquestador, gestor_diagnostico):
    """Verifica que el orquestador no emita ML fallback sino la advertencia de seguridad."""
    session_id = "test_common_rail_incidente_a"
    mensaje = "¿Puedo pasar la mano por las cañerías de inyección para sentir si hay alguna fuga de petróleo?"

    res = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=mensaje,
        gestor_diagnostico=gestor_diagnostico,
    )

    assert res["decision"] == "SEGURIDAD_CRITICA"
    assert "No tengo una hipótesis ML compatible" not in res["respuesta_texto"]
    assert "PROHIBICIÓN ESTRICTA" in res["respuesta_texto"]
    assert "con las manos, dedos, piel ni trapos" in res["respuesta_texto"]
    assert "cartón grueso o papel" in res["respuesta_texto"]
    assert "SERVICIO HOSPITALARIO DE URGENCIAS" in res["respuesta_texto"]


@pytest.mark.parametrize(
    "frase_tactil",
    [
        "¿Puedo tocar la cañería para encontrar la fuga?",
        "Voy a pasar el dedo por el inyector.",
        "¿Se puede buscar la fuga con un trapo?",
        "Hay un chorro fino de petróleo, ¿lo reviso con la mano?",
        "¿Qué riesgo tiene una fuga de alta presión?",
        "Maestro, ¿le paso la mano a los caños de inyección para tantear la fuga?",
        "Voy a meter el dedo al inyector para ver si fuga petróleo.",
        "¿Puedo pasarle un trapito por la cañería?",
        "Hay fuga en el common rail, ¿le meto la mano?",
        "¿puedo pasar la mano x las cañerias de inyeccion pa ver si fuga petroleo?",
        "puedo tocar la tuberia con la mano para sentir el chorro",
        "Que riesgo tiene una fuga de alta presion en diesel",
    ],
)
def test_variantes_coloquiales_common_rail(frase_tactil):
    sev, banner = PoliticaSeguridad.evaluar_severidad(frase_tactil)
    assert sev == SeveridadSeguridad.CRITICAL_STOP, f"Fallo al interceptar: {frase_tactil}"
    assert banner == BANNER_DIESEL_ALTA_PRESION


# ==============================================================================
# 2. INCIDENTE B: REGENERACIÓN DPF CON DILUCIÓN DE ACEITE
# ==============================================================================

def test_incidente_b_bloqueo_directo_con_indicios_activos():
    """Turno 7 con dilución en contexto: la regeneración forzada debe bloquearse."""
    estado = ConversationState(session_id="test_dpf_incidente_b")
    estado.registrar_hecho(
        "aceite_sobrellenado_diluido",
        "SI (nivel por encima del máximo)",
        categoria="seguridad",
        estado=FactState.CONFIRMADO,
    )
    estado.registrar_hecho(
        "dilucion_aceite_combustible",
        "SI",
        categoria="seguridad",
        estado=FactState.CONFIRMADO,
    )

    pregunta_turno7 = "¿Puedo forzar una regeneración estática con el escáner ahorita mismo para destapar el filtro?"
    sev, banner = PoliticaSeguridad.evaluar_severidad(pregunta_turno7, estado=estado)

    assert sev == SeveridadSeguridad.CRITICAL_STOP
    assert banner == BANNER_BLOQUEO_REGENERACION_DILUCION
    assert "REGENERACIÓN DE DPF CONTRAINDICADA POR DILUCIÓN DE ACEITE" in banner
    assert "PROHIBICIÓN ESTRICTA: NO INICIE LA REGENERACIÓN FORZADA" in banner
    assert "embalamiento diésel / runaway" in banner
    assert "Diferenciación Técnica: Sospecha vs Confirmación Física" in banner
    assert "Low SAPS" in banner
    assert "NO constituye una autorización automática" in banner


@pytest.mark.asyncio
async def test_incidente_b_orquestador_flujo_multiturno(orquestador, gestor_diagnostico):
    """Simula los turnos previos de la Ford Ranger y verifica el bloqueo en turno 7."""
    session_id = "test_ford_ranger_caso_07"

    # Turno 1: Vehículo y síntomas iniciales
    await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario="Ford Ranger 2020 3.2 diesel no tiene fuerza y parpadea el DPF en el tablero",
        gestor_diagnostico=gestor_diagnostico,
    )

    # Turno 5: Reporte de dilución de aceite sobre el máximo
    await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario="El nivel de aceite está 2 cm por encima del máximo y huele a diésel",
        gestor_diagnostico=gestor_diagnostico,
    )

    # Turno 7: Solicitud de regeneración forzada estática con escáner
    res7 = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario="¿Puedo forzar una regeneración estática con el escáner ahorita mismo para destapar el filtro?",
        gestor_diagnostico=gestor_diagnostico,
    )

    assert res7["decision"] == "SEGURIDAD_CRITICA"
    assert "BLOQUEO DE SEGURIDAD MECÁNICA" in res7["respuesta_texto"]
    assert "REGENERACIÓN DE DPF CONTRAINDICADA" in res7["respuesta_texto"]
    assert "embalamiento" in res7["respuesta_texto"].lower()
    assert "Low SAPS" in res7["respuesta_texto"]


@pytest.mark.parametrize(
    "frase_dilucion,frase_regeneracion",
    [
        (
            "El aceite está pasado del máximo y huele a diésel.",
            "Voy a regenerar el filtro con el escáner.",
        ),
        (
            "El nivel subió después de varias regeneraciones.",
            "¿Puedo hacer una regeneración estacionaria?",
        ),
        (
            "Cárter sobrellenado con petróleo y varilla pasada de la marca",
            "Maestro, ¿le tiro una regenerada estática al DPF con el scanner?",
        ),
    ],
)
@pytest.mark.asyncio
async def test_variantes_dpf_bloqueadas_por_dilucion(
    orquestador, gestor_diagnostico, frase_dilucion, frase_regeneracion
):
    session_id = f"test_dpf_var_{abs(hash(frase_dilucion))}"
    await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=frase_dilucion,
        gestor_diagnostico=gestor_diagnostico,
    )

    res = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=frase_regeneracion,
        gestor_diagnostico=gestor_diagnostico,
    )

    assert res["decision"] == "SEGURIDAD_CRITICA"
    assert "BLOQUEO DE SEGURIDAD MECÁNICA" in res["respuesta_texto"]
    assert "embalamiento" in res["respuesta_texto"].lower()


# ==============================================================================
# 3. TRANSICIÓN A PRERREQUISITOS OEM TRAS CORRECCIÓN DE ACEITE
# ==============================================================================

@pytest.mark.asyncio
async def test_dpf_prerrequisitos_oem_despues_de_corregir_aceite(orquestador, gestor_diagnostico):
    """Una vez corregido el aceite, no se debe bloquear indefinidamente sino entregar prerrequisitos OEM."""
    session_id = "test_dpf_prerrequisitos_oem"

    # 1. Reporte de dilución inicial
    await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario="Ford Ranger diesel con DPF tapado y nivel de aceite pasado del máximo con olor a petróleo",
        gestor_diagnostico=gestor_diagnostico,
    )

    # 2. Corrección documentada y consulta de prerrequisitos
    res_corregido = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario="Ya corregí el problema del aceite, ¿qué debo verificar antes de regenerar?",
        gestor_diagnostico=gestor_diagnostico,
    )

    assert res_corregido["decision"] == "PRERREQUISITOS_OEM"
    assert "BLOQUEO DE SEGURIDAD" not in res_corregido["respuesta_texto"]
    assert "Prerrequisitos y comprobaciones OEM antes de forzar la regeneración" in res_corregido["respuesta_texto"]
    assert "Temperatura de motor" in res_corregido["respuesta_texto"]
    assert "Sin DTCs inhibitorios" in res_corregido["respuesta_texto"]
    assert "Masa de hollín dentro de límites de servicio" in res_corregido["respuesta_texto"]


# ==============================================================================
# 4. AUSENCIA DE FALSAS ALARMAS EN CONSULTAS INOCUAS
# ==============================================================================

@pytest.mark.parametrize(
    "consulta_inocua",
    [
        "Revisé la presión de combustible con el manómetro y marca 45 psi",
        "Cambié las pastillas de freno delanteras",
        "El motor tiembla en ralentí cuando enciendo las luces",
        "¿Qué tipo de aceite de motor recomienda el fabricante para un Toyota Corolla 2018?",
        "Medí el voltaje de la batería con el multímetro y marca 12.6V apagado",
        "Limpié el sensor MAF con spray dieléctrico",
    ],
)
def test_ausencia_falsas_alarmas(consulta_inocua):
    estado = ConversationState(session_id="test_inocuo")
    sev, banner = PoliticaSeguridad.evaluar_severidad(consulta_inocua, estado=estado)
    assert sev == SeveridadSeguridad.NORMAL_DIAGNOSTIC
    assert banner is None
