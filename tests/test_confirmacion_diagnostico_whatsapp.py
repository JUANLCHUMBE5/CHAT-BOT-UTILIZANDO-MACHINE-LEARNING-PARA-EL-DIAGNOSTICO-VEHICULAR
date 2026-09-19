"""Regresiones del comando de validación técnica recibido por WhatsApp."""

import asyncio
import uuid
from types import SimpleNamespace

from src.application.services.confirmacion_diagnostico import (
    ConfirmacionDiagnosticoWhatsApp,
    instrucciones_confirmacion_whatsapp,
    interpretar_confirmacion_whatsapp,
    interpretar_respuesta_validacion_whatsapp,
)
from src.core.services.webhook_service import WebhookService


def test_confirmar_guarda_reparacion_u_observacion():
    resultado = interpretar_confirmacion_whatsapp(
        "CONFIRMAR: se calibró el sistema GNV y recuperó potencia"
    )

    assert resultado is not None
    assert resultado.estado == "confirmado"
    assert resultado.observacion == "se calibró el sistema GNV y recuperó potencia"
    assert not resultado.requiere_observacion


def test_descartar_exige_detallar_la_falla_diferente():
    resultado = interpretar_confirmacion_whatsapp("FALLA DIFERENTE")

    assert resultado is not None
    assert resultado.estado == "descartado"
    assert resultado.observacion is None
    assert resultado.requiere_observacion


def test_un_sintoma_con_palabra_confirmar_no_se_toma_como_comando():
    assert interpretar_confirmacion_whatsapp(
        "Quiero confirmar si la falla aparece cuando acelero"
    ) is None
    assert interpretar_confirmacion_whatsapp("confirmar presión de GNV") is None


def test_respuesta_si_no_acepta_variantes_breves():
    assert interpretar_respuesta_validacion_whatsapp("SÍ") == "si"
    assert interpretar_respuesta_validacion_whatsapp("está bien") == "si"
    assert interpretar_respuesta_validacion_whatsapp("NO") == "no"
    assert interpretar_respuesta_validacion_whatsapp("fue incorrecta") == "no"


def test_respuesta_si_no_no_interpreta_una_consulta_completa():
    assert interpretar_respuesta_validacion_whatsapp("No acelera cuando sube") is None
    assert interpretar_respuesta_validacion_whatsapp("Sí falla cuando está frío") is None


def test_instrucciones_piden_confirmacion_binaria():
    instrucciones = instrucciones_confirmacion_whatsapp()

    assert "¿Fue correcta?" in instrucciones
    assert "*SÍ / NO*" in instrucciones
    assert len(instrucciones.strip()) < 40


def test_respuesta_si_confirma_el_diagnostico_exacto_y_deja_auditoria():
    diagnostico_id = uuid.uuid4()
    usuario = SimpleNamespace(id=uuid.uuid4(), taller_id=uuid.uuid4())
    hipotesis = SimpleNamespace(orden=1, resultado=None)
    diagnostico = SimpleNamespace(
        id=diagnostico_id,
        estado="generado",
        conclusion_mecanico=None,
        hipotesis=[hipotesis],
        trazabilidad={},
    )

    class DiagnosticosFalsos:
        async def obtener_pendiente_mecanico_por_id(self, **filtros):
            assert filtros["diagnostico_id"] == diagnostico_id
            assert filtros["taller_id"] == usuario.taller_id
            assert filtros["mecanico_id"] == usuario.id
            return diagnostico

    class OperacionesFalsas:
        auditoria = None

        async def registrar_auditoria(self, **datos):
            self.auditoria = datos

    operaciones = OperacionesFalsas()
    mensaje, resultado_id = asyncio.run(
        WebhookService._procesar_confirmacion_tecnica(
            ConfirmacionDiagnosticoWhatsApp(estado="confirmado"),
            usuario,
            DiagnosticosFalsos(),
            operaciones,
            diagnostico_id=diagnostico_id,
        )
    )

    assert resultado_id == diagnostico_id
    assert "confirmado" in mensaje
    assert diagnostico.estado == "confirmado"
    assert hipotesis.resultado == "confirmada"
    assert diagnostico.trazabilidad["validacion_tecnica"]["canal"] == "whatsapp"
    assert operaciones.auditoria["entidad_id"] == diagnostico_id
