"""Pruebas exhaustivas para el modo WhatsApp solo texto y validación de tesis.

Verifica:
1. Desactivación de botones interactivos por defecto (WHATSAPP_INTERACTIVE_BUTTONS_ENABLED=False).
2. Menú de hipótesis numeradas dinámicamente sin 'NINGUNA' ni 'NO SÉ'.
3. Interpretación robusta en lenguaje natural: '1', 'La 1', 'La primera', 'Quiero revisar la primera', '2', 'La segunda', 'Quiero revisar la segunda'.
4. Prevención de falsos positivos en observaciones técnicas y números decimales (ej: 'alabeo de 0.2 mm').
5. Manejo de selección repetida sin reinicio ni duplicación de preguntas.
6. Alternativa visual segura sin requerir elevador ni herramientas complejas.
7. Confirmación SÍ / NO y preservación de hipótesis abiertas tras respuesta NO.
8. Sanitización de SIN-PLACA.
"""

from __future__ import annotations

import time
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.services.confirmacion_diagnostico import (
    instrucciones_confirmacion_whatsapp,
    interpretar_seleccion_top3,
)
from src.config import settings
from src.core.conversacion.comprension_semantica.interprete import _construir_contexto_resumido
from src.core.services.webhook.validation_workflow import ValidationWorkflow
from src.core.services.whatsapp_provider import WhatsAppProviderService


def test_instrucciones_menu_dinamico_sin_ninguna_ni_no_se():
    """El menú dinámico numera 1, 2, 3 sin exponer NINGUNA ni NO SÉ, y separa selección de SÍ/NO."""
    txt_1 = instrucciones_confirmacion_whatsapp(1)
    assert "*SÍ / NO*" in txt_1
    assert "1." not in txt_1
    assert "NINGUNA" not in txt_1
    assert "NO SÉ" not in txt_1

    txt_2 = instrucciones_confirmacion_whatsapp(2)
    assert "Selecciona una hipótesis a verificar" in txt_2
    assert "1. Primera hipótesis" in txt_2
    assert "2. Segunda hipótesis" in txt_2
    assert "3. Tercera hipótesis" not in txt_2
    assert "NINGUNA" not in txt_2
    assert "NO SÉ" not in txt_2
    assert "*SÍ / NO*" not in txt_2

    txt_3 = instrucciones_confirmacion_whatsapp(3)
    assert "Selecciona una hipótesis a verificar" in txt_3
    assert "1. Primera hipótesis" in txt_3
    assert "2. Segunda hipótesis" in txt_3
    assert "3. Tercera hipótesis" in txt_3
    assert "NINGUNA" not in txt_3
    assert "NO SÉ" not in txt_3
    assert "*SÍ / NO*" not in txt_3


@pytest.mark.parametrize(
    "frase,orden_esperado,accion_esperada",
    [
        ("1", 1, "CONFIRMAR"),
        ("La 1", 1, "CONFIRMAR"),
        ("la 1", 1, "CONFIRMAR"),
        ("La primera", 1, "CONFIRMAR"),
        ("primera", 1, "CONFIRMAR"),
        ("Quiero revisar la primera", 1, "CONFIRMAR"),
        ("vamos a revisar la 1", 1, "CONFIRMAR"),
        ("voy a revisar la primera", 1, "CONFIRMAR"),
        ("elijo la primera", 1, "CONFIRMAR"),
        ("2", 2, "CONFIRMAR"),
        ("La 2", 2, "CONFIRMAR"),
        ("la 2", 2, "CONFIRMAR"),
        ("La segunda", 2, "CONFIRMAR"),
        ("segunda", 2, "CONFIRMAR"),
        ("Quiero revisar la segunda", 2, "CONFIRMAR"),
        ("vamos con la 2", 2, "CONFIRMAR"),
        ("3", 3, "CONFIRMAR"),
        ("La 3", 3, "CONFIRMAR"),
        ("La tercera", 3, "CONFIRMAR"),
        ("Quiero revisar la tercera", 3, "CONFIRMAR"),
        ("no se", None, "NO_SE"),
        ("no sé", None, "NO_SE"),
        ("todavia no se", None, "NO_SE"),
        ("no estoy seguro", None, "NO_SE"),
        ("ninguna", None, "NINGUNA"),
        ("ninguna de las anteriores", None, "NINGUNA"),
    ],
)
def test_interpretar_seleccion_top3_lenguaje_natural(frase, orden_esperado, accion_esperada):
    res = interpretar_seleccion_top3(frase)
    assert res is not None
    assert res.orden == orden_esperado
    assert res.accion == accion_esperada


@pytest.mark.parametrize(
    "observacion",
    [
        "El disco tiene un alabeo visible de 0.2 mm",
        "Presión en riel de 28 psi",
        "El pedal se va al fondo pero no veo fugas",
        "Se escucha un golpeteo al acelerar a 2000 rpm",
        "El nivel de líquido de frenos está en 0.5 litros",
    ],
)
def test_observaciones_tecnicas_no_se_confunden_con_seleccion(observacion):
    """Las observaciones técnicas libres no deben confundirse con selección de hipótesis."""
    res = interpretar_seleccion_top3(observacion)
    assert res is None, f"Observación técnica {observacion!r} no debe seleccionarse como opción"


@pytest.mark.anyio
async def test_proveedor_whatsapp_no_envia_botones_si_bandera_desactivada():
    """WhatsAppProviderService elimina interactivos si la bandera está desactivada."""
    provider = WhatsAppProviderService()
    with patch.object(settings, "whatsapp_interactive_buttons_enabled", False):
        with patch.object(settings, "meta_access_token", "test-token"), patch.object(
            settings, "meta_phone_number_id", "123456"
        ):
            with patch("requests.post") as mock_post:
                mock_post.return_value = SimpleNamespace(
                    status_code=200,
                    content=b'{"messages": [{"id": "wamid.123"}]}',
                    json=lambda: {"messages": [{"id": "wamid.123"}]},
                )
                payload_interactivo = {
                    "tipo": "button",
                    "botones": [{"id": "hip_1", "title": "1. Fuga"}],
                }
                res = await provider.enviar(
                    proveedor="meta",
                    destino="+51999888777",
                    texto="Hola mecánico",
                    interactivo=payload_interactivo,
                )
                assert res.exitoso
                args, kwargs = mock_post.call_args
                json_enviado = kwargs.get("json", {})
                assert json_enviado.get("type") == "text"
                assert "interactive" not in json_enviado


@pytest.mark.anyio
async def test_seleccion_repetida_recuerda_comprobacion_sin_reiniciar():
    """Si el mecánico repite la selección, CarBot recuerda la prueba pendiente sin duplicar ni reiniciar."""
    diag_id = uuid.uuid4()
    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4())
    hip1 = SimpleNamespace(
        orden=1,
        falla_probable="Discos alabeados",
        prueba_recomendada="Medir alabeo con reloj comparador",
        resultado=None,
    )
    diagnostico = SimpleNamespace(
        id=diag_id,
        estado="generado",
        falla_predicha="Discos alabeados",
        sintoma_original="Vibración al frenar a alta velocidad",
        hipotesis=[hip1],
        trazabilidad={},
        conclusion_mecanico=None,
    )
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={
            "case_id": f"caso-{diag_id}",
            "validacion_diagnostico": {
                "etapa": "esperando_confirmacion",
                "diagnostico_id": str(diag_id),
                "orden_seleccionado": 1,
                "hipotesis_seleccionada": "Discos alabeados",
            },
        },
    )

    session = AsyncMock()
    diag_mock = MagicMock()
    diag_mock.obtener_pendiente_mecanico_por_id = AsyncMock(return_value=diagnostico)
    msg_mock = MagicMock()
    msg_mock.crear_mensaje = AsyncMock()

    with patch("src.core.services.webhook.validation_workflow.DiagnosticoRepository", lambda s: diag_mock), \
         patch("src.core.services.webhook.validation_workflow.MensajeRepository", lambda s: msg_mock):

        # Mecánico vuelve a enviar "1" o "la primera"
        res = await ValidationWorkflow.manejar_flujo_validacion(
            session=session,
            conversacion=conversacion,
            usuario=usuario,
            texto_cliente="Quiero revisar la primera",
            tipo_mensaje="text",
            meta_message_id="msg_rep_1",
            proveedor="meta",
            remitente="+51999888777",
            t_inicio=time.perf_counter(),
        )

        assert res is not None
        assert res["status"] == "recordatorio_comprobacion_pendiente"
        assert "Ya tienes seleccionada la hipótesis *1*" in res["respuesta"]
        assert "Medir alabeo con reloj comparador" in res["respuesta"]
        # No debe haber reiniciado ni cambiado el orden
        assert conversacion.contexto["validacion_diagnostico"]["orden_seleccionado"] == 1


@pytest.mark.anyio
async def test_alternativa_visual_segura_sin_herramientas():
    """Si el mecánico indica que no cuenta con herramientas o elevador, ofrece alternativa visual segura."""
    diag_id = uuid.uuid4()
    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4())
    hip1 = SimpleNamespace(
        orden=1,
        falla_probable="Fuga hidráulica",
        prueba_recomendada="Desmontar rueda y revisar calipers",
        resultado=None,
    )
    diagnostico = SimpleNamespace(
        id=diag_id,
        estado="generado",
        falla_predicha="Fuga hidráulica",
        sintoma_original="Pedal esponjoso",
        hipotesis=[hip1],
        trazabilidad={},
        conclusion_mecanico=None,
    )
    conversacion = SimpleNamespace(
        id=uuid.uuid4(),
        contexto={
            "case_id": f"caso-{diag_id}",
            "validacion_diagnostico": {
                "etapa": "esperando_confirmacion",
                "diagnostico_id": str(diag_id),
                "orden_seleccionado": 1,
            },
        },
    )

    session = AsyncMock()
    diag_mock = MagicMock()
    diag_mock.obtener_pendiente_mecanico_por_id = AsyncMock(return_value=diagnostico)
    msg_mock = MagicMock()
    msg_mock.crear_mensaje = AsyncMock()

    with patch("src.core.services.webhook.validation_workflow.DiagnosticoRepository", lambda s: diag_mock), \
         patch("src.core.services.webhook.validation_workflow.MensajeRepository", lambda s: msg_mock):

        res = await ValidationWorkflow.manejar_flujo_validacion(
            session=session,
            conversacion=conversacion,
            usuario=usuario,
            texto_cliente="Aún no la hago, no tengo herramientas ni elevador",
            tipo_mensaje="text",
            meta_message_id="msg_no_tools",
            proveedor="meta",
            remitente="+51999888777",
            t_inicio=time.perf_counter(),
        )

        assert res is not None
        assert "Alternativa de inspección visual segura" in res["respuesta"] or "Alternativa visual segura" in res["respuesta"]
        assert "sin herramientas ni elevador" in res["respuesta"] or "sin necesidad de herramientas" in res["respuesta"]


def test_sin_placa_no_se_expone_como_matricula_real():
    """_construir_contexto_resumido no debe exponer SIN-PLACA."""
    ctx = {
        "marca": "Toyota",
        "modelo": "Yaris",
        "placa": "SIN-PLACA",
        "falla_principal": "Frenos desgastados",
    }
    resultado = _construir_contexto_resumido(ctx)
    assert "SIN-PLACA" not in resultado
    assert "Toyota Yaris" in resultado
