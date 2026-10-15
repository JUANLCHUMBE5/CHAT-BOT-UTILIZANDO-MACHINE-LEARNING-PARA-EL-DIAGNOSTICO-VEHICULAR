"""Pruebas de regresión automatizadas para los fallos reales de interacción detectados en 114 turnos."""

import asyncio

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


def test_regresion_seguridad_sobrecalentamiento():
    """Verifica que un síntoma de recalentamiento en tráfico inyecte la advertencia de seguridad crítica."""
    async def _run():
        repo = InMemoryConversationRepository()
        gestor = GestorDiagnostico()
        orq = OrquestadorConversacion(repositorio=repo)

        res = await orq.procesar_turno(
            "test_seguridad_recalentamiento",
            "Tengo un Hyundai Elantra 2015 con 95,000 km. El motor recalienta cuando estoy en tráfico pesado o detenido, la aguja de temperatura sube casi a la zona roja.",
            gestor,
        )
        resp = res.get("respuesta_texto", "")
        assert "ADVERTENCIA CRÍTICA DE SEGURIDAD" in resp or "SOBRECALENTAMIENTO" in resp
        assert "NUNCA intente abrir el tapón del radiador" in resp or "quemaduras" in resp

    asyncio.run(_run())


def test_regresion_compatibilidad_diesel_sin_gasolina():
    """Verifica que un vehículo confirmado diésel no reciba causas ni comprobaciones de gasolina."""
    async def _run():
        repo = InMemoryConversationRepository()
        gestor = GestorDiagnostico()
        orq = OrquestadorConversacion(repositorio=repo)

        await orq.procesar_turno(
            "test_compat_diesel",
            "Hola amigo, tengo una Nissan Frontier 2019 diésel placa D9R-321 que pierde fuerza en subida",
            gestor,
        )
        res2 = await orq.procesar_turno(
            "test_compat_diesel",
            "Le conecté el escáner y me bota código P0299 baja presión de sobrealimentación",
            gestor,
        )
        resp = res2.get("respuesta_texto", "")
        assert "bomba de gasolina" not in resp.lower()
        assert "bujía" not in resp.lower()
        assert "bujias" not in resp.lower()

    asyncio.run(_run())


def test_regresion_respeto_descartes_bujias_nuevas():
    """Verifica que si el usuario reporta bujías nuevas originales, no se insista en bujías defectuosas."""
    async def _run():
        repo = InMemoryConversationRepository()
        gestor = GestorDiagnostico()
        orq = OrquestadorConversacion(repositorio=repo)

        await orq.procesar_turno(
            "test_descarte_bujias",
            "Buenas tardes maestro, tengo un Suzuki Swift 2018 que tironea al acelerar",
            gestor,
        )
        res = await orq.procesar_turno(
            "test_descarte_bujias",
            "Las bujías son nuevas originales de concesionario, recién cambiadas, no son las bujías",
            gestor,
        )
        estado = res.get("estado")
        assert "componente:bujia" in estado.hipotesis_descartadas
        assert "Falla en bujías" not in (res.get("diagnostico_ml") or "")

    asyncio.run(_run())


def test_regresion_inmovilizador_sin_plantilla_refrigeracion():
    """Verifica que una pregunta de inmovilizador no responda con termostato ni refrigeración."""
    async def _run():
        repo = InMemoryConversationRepository()
        gestor = GestorDiagnostico()
        orq = OrquestadorConversacion(repositorio=repo)

        await orq.procesar_turno(
            "test_inmovilizador_no_termostato",
            "Tengo un Mazda 3 2016 placa K2L-876 que arranca y se apaga a los 3 segundos",
            gestor,
        )
        res = await orq.procesar_turno(
            "test_inmovilizador_no_termostato",
            "¿Cuál es la explicación técnica de por qué la ECU corta la inyección a los 3 segundos?",
            gestor,
        )
        resp = res.get("respuesta_texto", "")
        assert "termostato" not in resp.lower()
        assert "manguera superior" not in resp.lower()
        assert "transponder" in resp.lower() or "inmovilizador" in resp.lower() or "antena" in resp.lower()

    asyncio.run(_run())


def test_regresion_sin_bucles_segmentador_embrague():
    """Verifica que comprobaciones físicas coloquiales de embrague no provoquen bucle de caso nuevo."""
    async def _run():
        repo = InMemoryConversationRepository()
        gestor = GestorDiagnostico()
        orq = OrquestadorConversacion(repositorio=repo)

        await orq.procesar_turno(
            "test_no_bucle_embrague",
            "Hola amigo, tengo un Volkswagen Gol 2015 placa P1O-998 que zapatea feo al salir en primera",
            gestor,
        )
        res = await orq.procesar_turno(
            "test_no_bucle_embrague",
            "El cable de embrague tiene su juego libre de 15 mm y el pedal acciona suave",
            gestor,
        )
        resp = res.get("respuesta_texto", "")
        assert "¿Este problema corresponde al mismo vehículo" not in resp

    asyncio.run(_run())
