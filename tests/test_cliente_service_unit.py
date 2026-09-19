"""
Pruebas unitarias directas e independientes de base de datos para ClienteService.
Verifica la lógica conversacional, menú interactivo y solicitudes sin llamadas a IA.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.services.cliente_service import ClienteService
from src.infrastructure.database.models.access_requests import SolicitudAcceso
from src.infrastructure.database.models.catalogs import Taller, Usuario


@pytest.mark.anyio
async def test_cliente_service_menu_bienvenida():
    """Valida que el menú de bienvenida contenga los datos del taller sin invocar ML/RAG/Gemini."""
    mock_session = MagicMock()
    service = ClienteService(mock_session)

    taller = Taller(
        id=uuid.uuid4(),
        nombre="Taller Mecánico Automotriz Carabayllo",
        direccion="Av. Universitaria / Av. Túpac Amaru, Carabayllo",
        telefono="+51 987 654 321",
        horario_atencion="Lunes a Sábado de 8:00 AM a 6:00 PM",
        google_maps_url="https://maps.google.com/?q=carabayllo",
    )
    usuario = Usuario(
        id=uuid.uuid4(),
        taller_id=taller.id,
        rol_id=4,
        nombres="Cliente Juan",
        whatsapp_hash="a" * 64,
        whatsapp_ultimos4="1234",
    )

    respuesta = await service.procesar_mensaje_cliente(usuario, taller, "hola")
    assert "Hola, bienvenido a Taller Mecánico Automotriz Carabayllo" in respuesta
    assert "Lunes a Sábado de 8:00 AM a 6:00 PM" in respuesta
    assert "Av. Universitaria" in respuesta
    assert "1️⃣ *Consultar nuestros servicios*" in respuesta
    assert "4️⃣ *Solicitar acceso como mecánico*" in respuesta


@pytest.mark.anyio
async def test_cliente_service_opciones_servicios_citas_ubicacion():
    """Valida las respuestas para consulta de servicios, citas y ubicación."""
    mock_session = MagicMock()
    service = ClienteService(mock_session)

    taller = Taller(
        id=uuid.uuid4(),
        nombre="AutoTech Carabayllo",
        direccion="Av. Túpac Amaru 123",
        telefono="+51 999 888 777",
        horario_atencion="Lunes a Viernes 8am a 5pm",
        servicios="• Afinamiento electrónico\n• Frenos ABS",
        google_maps_url="https://maps.google.com/autotech",
    )
    usuario = Usuario(
        id=uuid.uuid4(),
        taller_id=taller.id,
        rol_id=4,
        nombres="Cliente Carlos",
        whatsapp_hash="b" * 64,
        whatsapp_ultimos4="0000",
    )

    # Opción 1: Servicios
    res_1 = await service.procesar_mensaje_cliente(usuario, taller, "1")
    assert "Servicios ofrecidos en AutoTech Carabayllo" in res_1
    assert "Afinamiento electrónico" in res_1

    # Opción 2: Citas
    res_2 = await service.procesar_mensaje_cliente(usuario, taller, "quisiera una cita para mañana")
    assert "Reserva de Atención - AutoTech Carabayllo" in res_2
    assert "+51 999 888 777" in res_2

    # Opción 3: Ubicación y Horarios
    res_3 = await service.procesar_mensaje_cliente(usuario, taller, "donde estan ubicados y cual es su horario")
    assert "Ubicación y Contacto - AutoTech Carabayllo" in res_3
    assert "Av. Túpac Amaru 123" in res_3
    assert "https://maps.google.com/autotech" in res_3


@pytest.mark.anyio
async def test_cliente_service_solicitud_acceso_mecanico():
    """Valida el registro de solicitudes de acceso para mecánicos y el manejo de duplicados."""
    mock_session = MagicMock()
    service = ClienteService(mock_session)
    service.solicitud_repo = MagicMock()

    taller = Taller(id=uuid.uuid4(), nombre="Taller Central", activo=True)
    usuario = Usuario(
        id=uuid.uuid4(),
        taller_id=taller.id,
        rol_id=4,
        nombres="Mecánico Solicitante",
        whatsapp_hash="c" * 64,
        whatsapp_ultimos4="5678",
    )

    # Caso 1: Primera solicitud
    service.solicitud_repo.obtener_pendiente_por_usuario = AsyncMock(return_value=None)
    service.solicitud_repo.crear_solicitud = AsyncMock()

    res_sol = await service.procesar_mensaje_cliente(usuario, taller, "soy mecanico")
    assert "Solicitud de Acceso como Mecánico Registrada" in res_sol
    service.solicitud_repo.crear_solicitud.assert_awaited_once()

    # Caso 2: Solicitud ya existente en estado pendiente
    service.solicitud_repo.obtener_pendiente_por_usuario = AsyncMock(
        return_value=SolicitudAcceso(
            id=uuid.uuid4(),
            usuario_id=usuario.id,
            taller_id=taller.id,
            estado="pendiente",
        )
    )
    res_dup = await service.procesar_mensaje_cliente(usuario, taller, "quiero acceso")
    assert "Solicitud de Mecánico en Trámite" in res_dup
    assert "Ya tienes una solicitud pendiente" in res_dup
