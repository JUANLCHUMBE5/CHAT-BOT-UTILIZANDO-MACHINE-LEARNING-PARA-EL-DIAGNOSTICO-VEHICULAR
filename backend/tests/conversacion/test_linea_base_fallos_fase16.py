"""Pruebas de validación de soluciones implementadas en Fase 16B.

Casos evaluados y corregidos:
1. Retención vehicular correcta ante mención incidental o comparativa de otra marca.
2. Despacho directo de consultas técnicas en medio de un diagnóstico activo (copiloto flexible).
3. Conservación de síntomas y estado del diagnóstico sin forzar cuestionarios rígidos.
"""

import pytest

from src.core.conversacion.extraccion_hechos.actualizador_estado import extraer_y_actualizar
from src.core.conversacion.models import ConversationState, FactType
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


def test_retencion_vehicular_ante_mencion_comparativa():
    """Verifica que mencionar un vehículo de ejemplo no borra el vehículo del caso activo."""
    estado = ConversationState(session_id="test_lb_vehiculo")
    estado.marca = "Toyota"
    estado.modelo = "Yaris"
    estado.registrar_hecho("marca", "Toyota", categoria="vehiculo", tipo=FactType.CONDICION)
    estado.registrar_hecho("falla", "cascabeleo", categoria="sintoma", tipo=FactType.SINTOMA)
    estado.active_symptoms.append("cascabeleo")

    # El mecánico menciona otra marca como anécdota comparativa, no como corrección
    texto = "En un Nissan Tiida me pasó algo parecido, pero en este auto cascabelea en subida"
    extraer_y_actualizar(estado, texto)

    print(f"\n[F16B] Marca resultante tras mención comparativa: '{estado.marca}'")
    print(f"[F16B] Síntomas activos restantes: {estado.active_symptoms}")
    # Debe conservar Toyota y retener síntomas
    assert estado.marca == "Toyota", "La marca activa Toyota debe ser retenida"
    assert "cascabeleo" in estado.active_symptoms, "Los síntomas activos deben conservarse"
    assert "vehiculo_mencionado_nissan" in estado.hechos, "Nissan debe guardarse como antecedente"


@pytest.mark.anyio
async def test_consulta_tecnica_en_caso_activo_despacho_directo():
    """Verifica que una consulta técnica intermedia se atienda directamente sin bloquearse."""
    repo = InMemoryConversationRepository()
    estado = ConversationState(session_id="test_lb_consulta")
    estado.marca = "Toyota"
    estado.active_symptoms.append("tiembla en ralenti")
    estado.falla_principal = "Vibración irregular"
    await repo.save_session("test_lb_consulta", estado)

    gestor = GestorDiagnostico()
    gestor.conversation_repo = repo
    orquestador = OrquestadorConversacion(repositorio=repo)

    # El mecánico hace una pregunta técnica sobre cómo medir salto con reloj comparador
    mensaje = "¿Cómo se mide el alabeo de disco con reloj comparador?"

    res = await orquestador.procesar_turno(
        session_id="test_lb_consulta",
        texto_usuario=mensaje,
        gestor_diagnostico=gestor,
    )
    print(f"\n[F16B] Decisión de orquestador: {res.get('decision')}")
    print(f"[F16B] Status: {res.get('status')}")
    print(f"[F16B] Respuesta generada: {str(res.get('respuesta_texto'))[:120]}...")
    # Ahora debe despacharse directamente como DETALLE, no como pregunta rígida de cuestionario
    assert res.get("decision") == "DETALLE", "La consulta técnica debe responderse de inmediato"
    assert res.get("status") in ("detalle", "solicitud_detalle", "consulta_tecnica")
    assert "reloj comparador" in res.get("respuesta_texto").lower() or "alabeo" in res.get("respuesta_texto").lower() or "vibraci" in res.get("respuesta_texto").lower()
