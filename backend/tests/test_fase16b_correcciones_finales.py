"""Pruebas de regresión y validación para las cuatro correcciones finales de Fase 16B:
1. Semantic Purifier: eliminación de inyecciones sintéticas de etiquetas de fallas y pruebas de contraste.
2. Diagnóstico Diferencial: enrutamiento de mensajes mixtos y solicitudes de hipótesis alternativas sin abstención genérica.
3. Identificación del Vehículo: distinción entre vehículo actual y mención de antecedente sin reinicios espurios.
4. Mediciones Técnicas: distinción precisa entre reporte de medición y solicitud de tutorial/instrucciones.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import src.core.services.webhook_service as modulo
from src.core.conversacion.extraccion_hechos.actualizador_estado import extraer_y_actualizar
from src.core.conversacion.extraccion_hechos.clasificador_mensajes import es_solicitud_detalle
from src.core.conversacion.models import ConversationState, FactState
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.diagnostico.semantic_purifier import purificar_sintoma_para_vectorizador_ml
from src.core.gestor_diagnostico import GestorDiagnostico


class TestFase16BCorreccionesFinales:
    """Suite de validación de contraste y regresión de Fase 16B."""

    def test_semantic_purifier_sin_inyeccion_etiquetas_diagnosticas(self):
        """Verifica que el purificador no inyecte etiquetas de fallas ni cadenas diagnósticas sintéticas."""
        texto_entrada = (
            "Toyota Corolla 2015. Cambié bujías pero sigue perdiendo fuerza en subidas. "
            "Medí la presión en el riel y dio 20 PSI."
        )
        purificado = purificar_sintoma_para_vectorizador_ml(texto_entrada)

        # No debe contener hipótesis sintéticas inyectadas
        assert "bomba de gasolina quemada" not in purificado, (
            "El purificador inyectó la etiqueta sintética 'bomba de gasolina quemada'"
        )
        assert "falla motor de arranque" not in purificado
        assert "discos de freno alabeados" not in purificado
        assert "llantas desbalanceadas" not in purificado

        # Debe conservar la evidencia legítima reportada por el mecánico
        assert "20 psi" in purificado.lower() or "20" in purificado
        assert "perdiendo fuerza" in purificado.lower() or "fuerza" in purificado.lower()

    def test_semantic_purifier_contraste_hipotesis_previas(self):
        """Contraste: verifica que sugerencias previas o descartes legítimos no inyecten sesgos espurios."""
        texto_arranque = "La batería tiene fuerza pero no da marcha y suena clac seco."
        purificado_arranque = purificar_sintoma_para_vectorizador_ml(texto_arranque)

        assert "batería" not in purificado_arranque.lower() and "bateria" not in purificado_arranque.lower()
        assert "solenoide carbones terminal 50" not in purificado_arranque
        assert "no da marcha clac seco arrancador no gira" in purificado_arranque

    def test_distincion_medicion_vs_tutorial_reloj_comparador(self):
        """Diferencia reporte cuantitativo de medición de una solicitud de tutorial técnico."""
        # Reporte de medición: NO debe ser solicitud de detalle instructivo
        reporte_medicion = "Medí el alabeo del disco delantero derecho con reloj comparador y dio 0.12 mm"
        assert es_solicitud_detalle(reporte_medicion) is False, (
            "El reporte de medición fue erróneamente clasificado como solicitud de detalle"
        )

        # Consulta de procedimiento instructivo: SÍ debe ser solicitud de detalle instructivo
        consulta_tutorial = "¿Cómo se utiliza el reloj comparador paso a paso para medir alabeo?"
        assert es_solicitud_detalle(consulta_tutorial) is True, (
            "La consulta tutorial no fue clasificada como solicitud de detalle"
        )

    def test_vehiculo_activo_con_antecedente_sin_reinicio_de_caso(self):
        """Verifica que 'Es Nissan Sentra, pero antes revisé un Toyota' fije Nissan y preserve Toyota como antecedente."""
        estado = ConversationState(session_id="test-session-antecedente")
        texto = "Es un Nissan Sentra 2018, pero antes de este revisé un Toyota Corolla"

        hechos = extraer_y_actualizar(estado, texto)

        assert estado.marca == "Nissan", f"Marca activa incorrecta: {estado.marca}"
        assert estado.modelo == "Sentra", f"Modelo activo incorrecto: {estado.modelo}"
        assert estado.anio == "2018", f"Año incorrecto: {estado.anio}"

        # Toyota debe quedar como antecedente secundario y no como vehículo principal
        assert "vehiculo_mencionado_toyota" in estado.hechos
        assert estado.hechos["vehiculo_mencionado_toyota"].categoria == "antecedente"
        assert estado.session_id is not None

    def test_vehiculo_correccion_preserva_sintomas_acumulados(self):
        """Verifica que corregir la marca no borre los síntomas clínicos ya registrados."""
        estado = ConversationState(session_id="test-session-preservacion")
        # Turno 1: mecánico reporta vehículo inicial y síntoma
        extraer_y_actualizar(estado, "Tengo un Toyota con vibración al frenar")
        assert estado.marca == "Toyota"
        assert len(estado.active_symptoms) > 0

        # Turno 2: mecánico corrige la marca mencionando antecedente
        extraer_y_actualizar(estado, "Corrijo, es un Nissan Sentra, el Toyota era de ayer")
        assert estado.marca == "Nissan"
        assert estado.modelo == "Sentra"
        # Los síntomas acumulados NO deben haber sido borrados
        assert len(estado.active_symptoms) > 0

    @pytest.mark.anyio
    async def test_diagnostico_diferencial_mensaje_mixto_no_abstemio(self, monkeypatch):
        """Verifica que un mensaje mixto con síntomas y solicitud de causas alternativas no se desvíe a abstención."""
        gestor = GestorDiagnostico()
        gestor.api_key = ""
        gestor.conversation_repo = InMemoryConversationRepository()
        monkeypatch.setattr(modulo.settings, "groq_api_key", "")

        usuario = SimpleNamespace(
            id=uuid.uuid4(),
            taller_id=uuid.uuid4(),
            nombres="Mecánico Prueba Sentra",
            rol=SimpleNamespace(codigo="mecanico"),
        )
        conversacion = SimpleNamespace(
            id=uuid.uuid4(),
            contexto={},
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
            return {"status": "completado", "respuesta": getattr(dto, "respuesta_texto", "")}, Decimal("0")

        monkeypatch.setattr(modulo.DiagnosticPersister, "persistir_y_responder", persistir_mock)
        service = modulo.WebhookService(gestor)

        # Turno 1: apertura del caso
        t1_text = "NEUVO CASO. Tengo un Nissan Sentra 2018 que pierde potencia en pendientes. No tengo la placa."
        r1 = await service.procesar_mensaje(
            remitente="51999888777",
            meta_message_id="msg-diff-1",
            texto_cliente=t1_text,
            proveedor="api",
        )
        assert r1 is not None

        # Turno 2: mensaje mixto (síntoma + medición + causas alternativas)
        t2_text = (
            "Medí la presión de combustible y marcó 25 PSI. "
            "¿Qué otras causas posibles pueden explicar que tironee y qué dato necesitas para diferenciarlas?"
        )
        r2 = await service.procesar_mensaje(
            remitente="51999888777",
            meta_message_id="msg-diff-2",
            texto_cliente=t2_text,
            proveedor="api",
        )
        assert r2 is not None
        resp2 = str(r2.get("respuesta", ""))

        # No debe emitir abstención genérica
        assert "No encontré una fuente documental suficiente" not in resp2
        assert "La hipótesis queda pendiente: no registraré una confirmación" not in resp2
        # Debe referirse a las hipótesis diferenciales del sistema
        assert any(term in resp2.lower() for term in ("presión", "combustible", "bomba", "filtro", "psi", "inyector", "causas"))
