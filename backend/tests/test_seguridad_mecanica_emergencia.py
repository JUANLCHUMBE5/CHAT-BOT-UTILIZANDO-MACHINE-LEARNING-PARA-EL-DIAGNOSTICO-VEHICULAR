"""Pruebas de regresión automatizadas para seguridad mecánica crítica (Fase 1 / ESC-28)."""
import asyncio

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.diagnostico.politica_seguridad import (
    BANNER_TEMPERATURA,
    PoliticaSeguridad,
    SeveridadSeguridad,
)
from src.core.gestor_diagnostico import GestorDiagnostico


def test_evaluar_severidad_temperatura_critica_expresiones_reales():
    casos = [
        "El radiador está botando agua hirviendo con vapor y burbujea el depósito en un Nissan Sentra",
        "Sale vapor del motor y hierve el refrigerante",
        "Radiador hirviendo botando agua en subida",
        "Burbujea el depósito y sale con vapor blanco",
        "Sobrecalentamiento peligroso con vapor saliendo debajo del capó",
    ]
    for caso in casos:
        sev, banner = PoliticaSeguridad.evaluar_severidad(caso)
        assert sev == SeveridadSeguridad.CRITICAL_STOP, f"Fallo en detección crítica para: {caso}"
        assert banner == BANNER_TEMPERATURA, f"Banner incorrecto para: {caso}"


def test_orquestador_prioriza_seguridad_sin_preguntas_frivolas():
    async def _run():
        repo = InMemoryConversationRepository()
        orq = OrquestadorConversacion(repositorio=repo)
        gestor = GestorDiagnostico()
        
        mensaje = "El radiador está botando agua hirviendo con vapor y burbujea el depósito en un Nissan Sentra"
        res = await orq.procesar_turno(
            session_id="test_seguridad_termica_1",
            texto_usuario=mensaje,
            gestor_diagnostico=gestor,
        )
        
        assert res["decision"] == "DIAGNOSTICAR"
        assert "ADVERTENCIA CRÍTICA DE SEGURIDAD" in res["respuesta_texto"]
        assert "no abras el tapón del radiador" in res["respuesta_texto"].lower() or "no abrir la tapa del radiador" in res["respuesta_texto"].lower() or "nunca intente abrir" in res["respuesta_texto"].lower()
        assert "¿la falla se presenta cuando el vehículo está detenido en ralentí" not in res["respuesta_texto"]
        
        top1 = res["estado"].top3_actual[0]["falla"].lower()
        assert any(w in top1 for w in ("culata", "refrigerante", "radiador", "termostato"))

    asyncio.run(_run())
