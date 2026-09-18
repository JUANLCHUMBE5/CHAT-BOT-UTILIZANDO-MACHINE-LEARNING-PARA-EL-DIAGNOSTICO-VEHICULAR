"""Suite de pruebas de integración y regresión para Fase 9.5: Integridad Conversacional."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.intent_classifier import clasificar_intencion_consulta
from src.core.conversacion.models import ConversationState, FactType
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.guardia_contexto import GuardiaContextoDiagnostico
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository, PostgresConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.services.webhook_service import WebhookService, _obtener_lock_conversacion
from src.core.services.webhook.validation_workflow import ValidationWorkflow


@pytest.mark.anyio
async def test_regresion_incidente_caso_a_cerrado_caso_b_limpio():
    """Reproduce el incidente: Caso A cerrado no debe contaminar la consulta ML de Caso B."""
    gestor = GestorDiagnostico()
    orq = OrquestadorConversacion()
    sid = "test_regresion_incidente_9_5"

    # Caso A: no arranca + clac + luces tenues
    res_a = await orq.procesar_turno(
        session_id=sid,
        texto_usuario="no arranca clac luces tenues",
        gestor_diagnostico=gestor,
    )
    assert res_a["decision"] == "DIAGNOSTICAR"
    assert "no arranca" in res_a["consulta_consolidada"]
    case_id_a = res_a["estado"].case_id

    # Cierre formal del caso A
    await orq.finalizar_caso(sid, gestor)

    # Caso B: pierde fuerza después de 20 min en carretera + mejora al reducir velocidad + no pasa de 80
    res_b = await orq.procesar_turno(
        session_id=sid,
        texto_usuario="pierde fuerza después de 20 min en carretera + mejora al reducir velocidad + no pasa de 80",
        gestor_diagnostico=gestor,
    )

    consulta_b = res_b["consulta_consolidada"].lower()
    assert "no arranca" not in consulta_b, f"Contaminación detectada: {consulta_b}"
    assert "clac" not in consulta_b, f"Contaminación detectada: {consulta_b}"
    assert "luces tenues" not in consulta_b, f"Contaminación detectada: {consulta_b}"

    assert "pérdida de potencia" in consulta_b or "pierde fuerza" in consulta_b
    assert res_b["estado"].case_id != case_id_a, "El case_id debe ser nuevo"
    assert res_b["top3_actual"] is not None, "El modelo ML debe calcular un Top 3 nuevo"
    assert len(res_b["top3_actual"]) == 3, "Debe retornar 3 hipótesis"


@pytest.mark.anyio
async def test_intent_classifier_variantes_linguisticas():
    """Verifica que flexiones y tildes sean clasificadas como diagnostico y no consulta_tecnica."""
    frases_diagnostico = [
        "pierde fuerza al acelerar",
        "perdía fuerza en carretera",
        "perdia fuerza a 80",
        "el carro se ahoga",
        "se ahogaba cuando aceleraba",
        "no pasa de 80 km/h",
        "no puedo pasar de 80",
        "se me apaga en semáforo",
        "se apagaba en caliente",
        "cuesta arrancar en frío",
    ]
    for frase in frases_diagnostico:
        intencion = clasificar_intencion_consulta(frase)
        assert intencion == "diagnostico", f"Falla para '{frase}': se esperaba diagnostico y se obtuvo {intencion}"


@pytest.mark.anyio
async def test_flujo_no_pregunta_discriminante_sin_pop_ciego():
    """Verifica que 'NO' no haga pop ciego a Top 2, sino que pregunte discriminante y acepte nueva evidencia."""
    session = AsyncMock()
    conversacion = MagicMock()
    conversacion.id = "conv_123"
    conversacion.contexto = {
        "validacion_diagnostico": {
            "etapa": "esperando_confirmacion",
            "diagnostico_id": "00000000-0000-0000-0000-000000000001",
        }
    }
    usuario = MagicMock()
    usuario.id = "usr_123"
    usuario.taller_id = "taller_123"

    with patch("src.infrastructure.database.repositories.diagnostico_repository.DiagnosticoRepository.obtener_pendiente_mecanico_por_id") as mock_diag, \
         patch("src.infrastructure.database.repositories.mensaje_repository.MensajeRepository.crear_mensaje") as mock_msg:

        mock_d = MagicMock()
        mock_d.id = "00000000-0000-0000-0000-000000000001"
        mock_d.falla_predicha = "Bateria descargada"
        mock_d.sintoma_original = "no arranca clac"
        mock_d.trazabilidad = {"predicciones_ml": [{"falla": "Bateria descargada"}, {"falla": "Motor de arranque"}]}
        mock_diag.return_value = mock_d

        # Mecánico responde únicamente "NO"
        res = await ValidationWorkflow.manejar_flujo_validacion(
            session=session,
            conversacion=conversacion,
            usuario=usuario,
            texto_cliente="no",
            tipo_mensaje="text",
            meta_message_id="msg_no_1",
            proveedor="meta",
            remitente="51999888777",
            t_inicio=0.0,
        )

        assert res is not None
        assert res["status"] == "esperando_falla_real"
        # Verificar que no ofrece simplemente opción 2 o 3 ni hace pop a Top2
        assert "Pregunta técnica discriminante" in res["respuesta"]
        assert "Bateria descargada" in res["respuesta"]

        # Ahora el mecánico aporta nueva evidencia respondiendo a la pregunta
        res_evidencia = await ValidationWorkflow.manejar_flujo_validacion(
            session=session,
            conversacion=conversacion,
            usuario=usuario,
            texto_cliente="en caliente el motor jalonea a fondo",
            tipo_mensaje="text",
            meta_message_id="msg_no_2",
            proveedor="meta",
            remitente="51999888777",
            t_inicio=0.0,
        )

        assert res_evidencia is not None
        assert res_evidencia["status"] == "evaluar_alternativa"
        assert res_evidencia["diagnostico_forzado"] is None, "NO debe forzar Top 2"
        assert "Descarte previo: no es Bateria descargada" in res_evidencia["texto_evaluar"]
        assert "en caliente el motor jalonea a fondo" in res_evidencia["texto_evaluar"]


@pytest.mark.anyio
async def test_flujo_no_con_evidencia_inmediata():
    """Si el mecánico dice 'no, jalonea en alta', debe evaluar de inmediato sin bucle."""
    session = AsyncMock()
    conversacion = MagicMock()
    conversacion.id = "conv_123"
    conversacion.contexto = {
        "validacion_diagnostico": {
            "etapa": "esperando_confirmacion",
            "diagnostico_id": "00000000-0000-0000-0000-000000000001",
        }
    }
    usuario = MagicMock()
    usuario.id = "usr_123"
    usuario.taller_id = "taller_123"

    with patch("src.infrastructure.database.repositories.diagnostico_repository.DiagnosticoRepository.obtener_pendiente_mecanico_por_id") as mock_diag, \
         patch("src.infrastructure.database.repositories.mensaje_repository.MensajeRepository.crear_mensaje") as mock_msg:

        mock_d = MagicMock()
        mock_d.id = "00000000-0000-0000-0000-000000000001"
        mock_d.falla_predicha = "Alternador defectuoso"
        mock_d.sintoma_original = "bateria muerta"
        mock_d.trazabilidad = {"predicciones_ml": []}
        mock_diag.return_value = mock_d

        res = await ValidationWorkflow.manejar_flujo_validacion(
            session=session,
            conversacion=conversacion,
            usuario=usuario,
            texto_cliente="no, al acelerar en subida cascabelea fuerte",
            tipo_mensaje="text",
            meta_message_id="msg_no_inmed",
            proveedor="meta",
            remitente="51999888777",
            t_inicio=0.0,
        )

        assert res is not None
        assert res["status"] == "evaluar_alternativa"
        assert res["diagnostico_forzado"] is None
        assert "Alternador defectuoso" in res["texto_evaluar"]
        assert "cascabelea fuerte" in res["texto_evaluar"]


@pytest.mark.anyio
async def test_cambio_de_vehiculo_limpia_contexto():
    """Un cambio explícito de vehículo no debe contaminar el nuevo diagnóstico."""
    gestor = GestorDiagnostico()
    orq = OrquestadorConversacion()
    sid = "test_cambio_vehiculo"

    # Vehículo A: Toyota Corolla con frenos
    res_a = await orq.procesar_turno(
        session_id=sid,
        texto_usuario="tengo un Toyota Corolla que al frenar vibra el timón",
        gestor_diagnostico=gestor,
    )
    assert res_a["estado"].marca == "Toyota"
    assert res_a["estado"].modelo == "Corolla"

    # Vehículo B: Nissan Sentra
    res_b = await orq.procesar_turno(
        session_id=sid,
        texto_usuario="ahora tengo un Nissan Sentra que no arranca en frío",
        gestor_diagnostico=gestor,
    )
    assert res_b["estado"].marca == "Nissan"
    assert res_b["estado"].modelo == "Sentra"
    consulta_b = res_b["consulta_consolidada"].lower()
    assert "corolla" not in consulta_b
    assert "toyota" not in consulta_b
    assert "frenar" not in consulta_b
    assert "timón" not in consulta_b


@pytest.mark.anyio
async def test_guardia_contexto_obsolescencia_reconstruye():
    """GuardiaContextoDiagnostico intercepta cuando la consulta consolidada solo tiene hechos antiguos."""
    estado = ConversationState(session_id="test_guardia")
    # Simular hechos antiguos
    estado.registrar_hecho("sintoma_freno", "freno esponjoso", categoria="sintoma", tipo=FactType.SINTOMA)
    consulta_antigua = "presenta pedal de freno esponjoso."

    mensaje_nuevo = "pierde fuerza y se ahoga en carretera"

    es_valido, consulta_final, reg = GuardiaContextoDiagnostico.validar_y_proteger(
        estado=estado,
        mensaje_actual=mensaje_nuevo,
        consulta_consolidada=consulta_antigua,
    )

    assert not es_valido, "Debe detectar inconsistencia"
    assert reg.inconsistencia_detectada is True
    assert "pérdida de potencia" in consulta_final or "pierde fuerza" in consulta_final
    assert "freno" not in consulta_final, "Debe purgar los hechos antiguos"


@pytest.mark.anyio
async def test_dos_usuarios_aislamiento():
    """Dos sesiones simultáneas no deben compartir ni contaminar hechos."""
    gestor = GestorDiagnostico()
    orq = OrquestadorConversacion()

    sid_1 = "usuario_tel_111"
    sid_2 = "usuario_tel_222"

    res_1 = await orq.procesar_turno(
        session_id=sid_1,
        texto_usuario="no arranca clac luces tenues",
        gestor_diagnostico=gestor,
    )
    res_2 = await orq.procesar_turno(
        session_id=sid_2,
        texto_usuario="chillido agudo al frenar en bajada",
        gestor_diagnostico=gestor,
    )

    assert "no arranca" in res_1["consulta_consolidada"]
    assert "frenar" not in res_1["consulta_consolidada"]

    assert "frenar" in res_2["consulta_consolidada"]
    assert "no arranca" not in res_2["consulta_consolidada"]
    assert res_1["estado"].case_id != res_2["estado"].case_id


@pytest.mark.anyio
async def test_serializacion_lock_por_conversacion():
    """Verifica que mensajes consecutivos rápidos para el mismo remitente adquieren el mismo lock."""
    remitente = "+51999000111"
    lock1 = _obtener_lock_conversacion(remitente)
    lock2 = _obtener_lock_conversacion(remitente)
    assert lock1 is lock2, "El lock debe ser el mismo objeto para el mismo remitente"

    remitente_otro = "+51999000222"
    lock3 = _obtener_lock_conversacion(remitente_otro)
    assert lock1 is not lock3, "Remitentes distintos deben tener locks independientes"


@pytest.mark.anyio
async def test_persistencia_historica_sin_hechos_activos():
    """Al finalizar caso en repositorio, se limpian hechos activos pero se conserva case_id histórico."""
    repo = InMemoryConversationRepository()
    sid = "sesion_hist_test"

    estado = ConversationState(session_id=sid)
    ExtractorHechos.extraer_y_actualizar(estado, "falla en bujias")
    await repo.save_session(sid, estado)

    # Finalizar caso
    estado_limpio = await repo.finalizar_caso(sid)
    assert len(estado_limpio.hechos) == 0
    assert estado_limpio.case_id is not None

    # Leer de nuevo
    recuperado = await repo.get_session(sid)
    assert recuperado is not None
    assert len(recuperado.hechos) == 0
    assert recuperado.case_id == estado_limpio.case_id
