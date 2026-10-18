"""Suite de Evaluación Generalizada Multiturno — Fase 14.

Evalúa la robustez conversacional, el manejo de memoria contextual,
la preservación de casos 'SIN-PLACA' y la ausencia de trampas estáticas de validación
en diversos vehículos y sistemas automotrices independientes:

- Escenario 1: Toyota Corolla 2015 — Flujo orgánico preplate (recuperación de síntoma previo, no bloqueo ante 'no comprobado').
- Escenario 2: Chevrolet Aveo 2017 — Sistema de Refrigeración con NUEVO CASO (temperatura en tráfico, pendiente electroventilador).
- Escenario 3: Hyundai Elantra 2018 — Falla de encendido / bujías (misfire, sin descarte falso ante 'no probado').
- Escenario 4: Ford Ranger 2016 Diesel — Transición de SIN-PLACA a placa definitiva preservando contexto.
"""

import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import src.core.services.webhook_service as modulo
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


def setup_mock_service(monkeypatch, conversacion_contexto=None):
    """Crea una instancia aislada del WebhookService mockeando la base de datos."""
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    gestor.conversation_repo = InMemoryConversationRepository()
    monkeypatch.setattr(modulo.settings, "groq_api_key", "")

    usuario = SimpleNamespace(
        id=uuid.uuid4(),
        taller_id=uuid.uuid4(),
        nombres="Mecánico Certificador",
        rol=SimpleNamespace(codigo="mecanico"),
    )
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto=conversacion_contexto if conversacion_contexto is not None else {},
    )

    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.begin_nested.return_value.__aenter__ = AsyncMock()
    session.begin_nested.return_value.__aexit__ = AsyncMock(return_value=False)
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=False)

    monkeypatch.setattr(modulo, "database_configurada", lambda: True)
    monkeypatch.setattr(modulo, "obtener_engine", lambda: None)
    monkeypatch.setattr(modulo, "AsyncSession", lambda *a, **k: context)

    mensaje_repo = MagicMock()
    mensaje_repo.existe_meta_message_id = AsyncMock(return_value=False)
    mensaje_repo.crear_mensaje = AsyncMock(return_value=SimpleNamespace(id=uuid.uuid4()))
    monkeypatch.setattr(modulo, "MensajeRepository", lambda *a: mensaje_repo)

    diag_repo_mock = MagicMock()
    diag_repo_mock.obtener_pendiente_mecanico_por_id = AsyncMock(return_value=None)
    diag_repo_mock.obtener_ultimo_pendiente_mecanico = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "src.core.services.webhook.validation_workflow.DiagnosticoRepository",
        lambda *a: diag_repo_mock,
    )
    monkeypatch.setattr(
        "src.core.services.webhook_service.DiagnosticoRepository",
        lambda *a: diag_repo_mock,
    )

    conv_repo = SimpleNamespace(obtener_o_crear_activa=AsyncMock(return_value=conversacion))
    monkeypatch.setattr(modulo, "ConversacionRepository", lambda *a: conv_repo)
    monkeypatch.setattr(
        modulo,
        "OperacionesRepository",
        lambda *a: SimpleNamespace(registrar_uso_api=AsyncMock()),
    )
    monkeypatch.setattr(
        modulo.IdentityResolver,
        "resolver_o_registrar",
        AsyncMock(return_value=SimpleNamespace(status="ok", usuario=usuario)),
    )

    async def persistir_mock(**kwargs):
        dto = kwargs["dto"]
        ctx = dict(conversacion.contexto or {})
        if modulo.DiagnosticPersister.debe_solicitar_feedback(dto):
            ctx["validacion_diagnostico"] = {
                "diagnostico_id": str(uuid.uuid4()),
                "etapa": "esperando_confirmacion",
            }
        conversacion.contexto = ctx
        return {"status": "completado", "respuesta": getattr(dto, "respuesta_texto", "")}, Decimal("0")

    monkeypatch.setattr(modulo.DiagnosticPersister, "persistir_y_responder", persistir_mock)
    service = modulo.WebhookService(gestor)
    return service, conversacion


@pytest.mark.anyio
async def test_escenario_frenos_toyota_corolla_organico(monkeypatch):
    """Prueba flujo orgánico: turno 1 saludo con falla, turno 2 sin placa, turno 3 no comprobado."""
    service, conv = setup_mock_service(monkeypatch)

    # Turno 1: Saludo inicial con síntoma
    r1 = await service.procesar_mensaje(
        remitente="51999111222",
        meta_message_id="msg-corolla-1",
        texto_cliente="Hola, tengo un Toyota Corolla 2015. Al frenar suavemente escucho un chirrido agudo en las ruedas delanteras.",
        proveedor="api",
    )
    resp1 = str(r1.get("respuesta", ""))
    assert "ingresa la placa" in resp1.lower()

    # Turno 2: El usuario indica que no tiene placa a la mano
    r2 = await service.procesar_mensaje(
        remitente="51999111222",
        meta_message_id="msg-corolla-2",
        texto_cliente="No tengo la placa disponible ahorita. ¿Me puedes decir qué podría fallar con el chirrido?",
        proveedor="api",
    )
    resp2 = str(r2.get("respuesta", ""))
    # Debe diagnosticar recuperando el síntoma sin pedir placa nuevamente
    assert "Indique una placa válida" not in resp2
    assert "ingresa la placa" not in resp2.lower()
    assert any(w in resp2.lower() for w in ("freno", "pastilla", "disco", "chirrido"))

    # Turno 3: El mecánico aclara que no ha desmontado los discos ni pastillas
    r3 = await service.procesar_mensaje(
        remitente="51999111222",
        meta_message_id="msg-corolla-3",
        texto_cliente="No he desmontado las ruedas ni he comprobado el espesor de las pastillas. El pedal no vibra. ¿Qué dato necesitas?",
        proveedor="api",
    )
    resp3 = str(r3.get("respuesta", ""))
    # No debe quedar atrapado en plantilla estática ni resetearse
    assert "La hipótesis queda pendiente: no registraré una confirmación ni un descarte sin evidencia física" not in resp3
    assert "Soy CarBot y estoy aquí" not in resp3
    assert len(resp3) > 10


@pytest.mark.anyio
async def test_escenario_refrigeracion_chevrolet_aveo(monkeypatch):
    """Prueba flujo de refrigeración con NUEVO CASO donde se aclara comprobación pendiente."""
    service, conv = setup_mock_service(monkeypatch)

    # Turno 1: NUEVO CASO con sobrecalentamiento
    r1 = await service.procesar_mensaje(
        remitente="51999222333",
        meta_message_id="msg-aveo-1",
        texto_cliente="NUEVO CASO. Chevrolet Aveo 2017. El motor recalienta cuando está parado en semáforos o tráfico lento, pero en autopista la temperatura baja a lo normal.",
        proveedor="api",
    )
    resp1 = str(r1.get("respuesta", ""))
    assert "Indique una placa válida" not in resp1
    assert any(w in resp1.lower() for w in ("termostato", "ventilador", "refrigerante", "temperatura", "refrigeracion"))

    # Turno 2: No ha medido electroventilador
    r2 = await service.procesar_mensaje(
        remitente="51999222333",
        meta_message_id="msg-aveo-2",
        texto_cliente="No he comprobado si el electroventilador activa en alta velocidad. El nivel de refrigerante está bien. ¿Qué otras causas existen?",
        proveedor="api",
    )
    resp2 = str(r2.get("respuesta", ""))
    # No debe descartar ventilador/termostato por falso positivo de "no comprobado"
    assert "La hipótesis queda pendiente" not in resp2
    assert "Soy CarBot" not in resp2


@pytest.mark.anyio
async def test_escenario_encendido_hyundai_elantra(monkeypatch):
    """Prueba sistema de encendido con fallas de bobina/bujía sin falso descarte."""
    service, conv = setup_mock_service(monkeypatch)

    # Turno 1: Falla de encendido / tironeo con placa
    r1 = await service.procesar_mensaje(
        remitente="51999333444",
        meta_message_id="msg-elantra-1",
        texto_cliente="NUEVO CASO. Hyundai Elantra 2018 placa ABC-123. El motor tiembla y pierde potencia al acelerar en subidas, se siente como falla de cilindro o rateo.",
        proveedor="api",
    )
    resp1 = str(r1.get("respuesta", ""))
    assert any(w in resp1.lower() for w in ("bobina", "bujia", "encendido", "misfire", "cilindro"))

    # Turno 2: Usuario aclara que no ha sacado las bujías
    r2 = await service.procesar_mensaje(
        remitente="51999333444",
        meta_message_id="msg-elantra-2",
        texto_cliente="No he comprobado el estado de las bujías ni he medido la resistencia de las bobinas. ¿Cómo puedo saber cuál cilindro es?",
        proveedor="api",
    )
    resp2 = str(r2.get("respuesta", ""))
    assert "La hipótesis queda pendiente" not in resp2
    assert "Soy CarBot" not in resp2


@pytest.mark.anyio
async def test_escenario_asociacion_placa_posterior_preserva_contexto(monkeypatch):
    """Prueba que un caso iniciado sin placa pueda recibir la placa en un turno posterior sin perder memoria."""
    service, conv = setup_mock_service(monkeypatch)

    # Turno 1: Inicio sin placa con NUEVO CASO
    r1 = await service.procesar_mensaje(
        remitente="51999444555",
        meta_message_id="msg-ranger-1",
        texto_cliente="NUEVO CASO. Tengo una camioneta Ford Ranger 2016 3.2 diesel. No tengo la placa a mano ahorita. Pierde potencia y echa humo negro al acelerar a fondo.",
        proveedor="api",
    )
    resp1 = str(r1.get("respuesta", ""))
    assert "Indique una placa válida" not in resp1

    # Turno 2: El usuario ahora sí aporta la placa
    r2 = await service.procesar_mensaje(
        remitente="51999444555",
        meta_message_id="msg-ranger-2",
        texto_cliente="Ya tengo la placa: es XYZ-789. ¿Qué me decías sobre la pérdida de potencia y el humo negro?",
        proveedor="api",
    )
    resp2 = str(r2.get("respuesta", ""))
    assert "Soy CarBot y estoy aquí para apoyarte con el diagnóstico" not in resp2
    placa_guardada = conv.contexto.get("placa") or conv.contexto.get("perfil_vehiculo", {}).get("placa")
    assert placa_guardada in ("XYZ-789", "XYZ789")
