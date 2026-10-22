"""Frontera de seguridad y separación de casos, también para retornos anticipados."""

from __future__ import annotations

import re
import time
from functools import wraps

from src.core.conversacion.aislamiento_subsistemas import (
    advertencia_freno_archivado,
    hay_pedal_critico,
    normalizar,
    separar_problema,
)
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState
from src.core.conversacion.prioridad_inspeccion import sincronizar_prioridad
from src.core.diagnostico.banners_seguridad import BANNER_TEMPERATURA
from src.core.conversacion.riesgo_activo_rag03i import banner_riesgo_actual
from src.core.diagnostico.politica_seguridad import PoliticaSeguridad, SeveridadSeguridad


def _intencion_vial(texto: str) -> bool:
    return bool(re.search(
        r"\b(?:circular\s+asi|(?:puedo|quiero|voy a|salir a)\s+circular|"
        r"probar\s+(?:en\s+|a\s+la\s+)?(?:pista|calle)|"
        r"sacar(?:lo)?\s+a\s+(?:probar\s+a\s+)?(?:la\s+)?pista|manejar\s+asi)\b",
        normalizar(texto),
    ))


async def _sincronizar(self, gestor, session_id, estado):
    await self.repositorio.save_session(session_id, estado)
    manager = getattr(gestor, "session_manager", None)
    if manager is not None:
        manager.cargar_contexto(session_id, {
            "case_id": estado.case_id, "conversation_state": estado.exportar_dict(),
        })


def proteger_turno(procesar):
    """Aplica una frontera común sin duplicar el cuerpo del orquestador histórico."""
    @wraps(procesar)
    async def protegido(self, session_id, texto_usuario, gestor_diagnostico, *args, **kwargs):
        inicio = time.perf_counter()
        texto = (texto_usuario or "").strip()
        estado = await self.repositorio.get_session(session_id)
        if estado is None:
            estado = ConversationState(session_id=session_id)
        riesgo_actual = banner_riesgo_actual(estado, texto)
        cambio = separar_problema(estado, texto)
        severidad, banner = PoliticaSeguridad.evaluar_severidad(texto, "", estado=estado)
        if riesgo_actual and severidad != SeveridadSeguridad.CRITICAL_STOP:
            severidad, banner = SeveridadSeguridad.CRITICAL_STOP, riesgo_actual
        historia = " ".join([*estado.active_symptoms, *estado.historial_mensajes_usuario])
        if _intencion_vial(texto) and hay_pedal_critico(historia):
            banner = (
                "SEGURIDAD VIAL: NO CIRCULES NI HAGAS PRUEBAS DE RUTA. "
                "Los síntomas de frenos reportados requieren comprobación presencial antes de conducir. "
                "No se ha confirmado una fuga ni su ubicación. Mantén el vehículo inmovilizado y "
                "solicita traslado seguro a un taller; no realices purgas ni reemplazos basados "
                "solo en esta orientación."
            )
            severidad = SeveridadSeguridad.CRITICAL_STOP
        diagnostico_termico_inicial = (
            banner == BANNER_TEMPERATURA
            and estado.turno_actual == 0
            and not ExtractorHechos.es_consulta_memoria(texto)
            and re.search(r"\b(?:nissan|toyota|ford|chevrolet|honda|hyundai|kia)\b", texto, re.I)
            and not re.search(r"\b(?:abrir|abro|destapar|destapo|retirar|quito|quitar|manejar)\b", texto, re.I)
        )
        if severidad == SeveridadSeguridad.CRITICAL_STOP and banner and not diagnostico_termico_inicial:
            if not estado.case_id:
                estado.iniciar_nuevo_caso(preservar_vehiculo=True)
            ExtractorHechos.extraer_y_actualizar(estado, texto)
            if banner == BANNER_TEMPERATURA:
                estado.active_system = "refrigeracion"
            vehiculo = " ".join(str(v) for v in (estado.marca, estado.modelo, estado.anio) if v)
            if vehiculo and vehiculo.casefold() not in banner.casefold():
                banner = f"Vehículo del caso: {vehiculo}.\n\n{banner}"
            estado.trazabilidad.append({
                "turno": estado.turno_actual,
                "mensaje_original": texto,
                "decision": "SEGURIDAD_CRITICA",
                "respuesta_enviada": banner.strip(),
                "tipo_mensaje": "seguridad_critica",
            })
            estado.trazabilidad = estado.trazabilidad[-15:]
            await _sincronizar(self, gestor_diagnostico, session_id, estado)
            resultado = {
                "status": "completado", "decision": "SEGURIDAD_CRITICA",
                "respuesta_texto": banner.strip(), "confianza_ml": 0.0,
                "diagnostico_ml": "Advertencia de seguridad: comprobación pendiente",
                "es_pregunta": False, "estado": estado, "case_id": estado.case_id,
                "fase": estado.fase.value,
                "tiempo_ms": round((time.perf_counter() - inicio) * 1000, 2),
            }
        else:
            if cambio:
                await _sincronizar(self, gestor_diagnostico, session_id, estado)
            resultado = await procesar(
                self, session_id, texto_usuario, gestor_diagnostico, *args, **kwargs,
            )
        if cambio:
            resultado["decision_transicion"] = "CAMBIO_DE_CASO"
        aviso = advertencia_freno_archivado(resultado.get("estado"))
        if aviso:
            resultado["respuesta_texto"] = aviso + resultado.get("respuesta_texto", "")
        sincronizar_prioridad(resultado)
        from src.core.diagnostico.confianza_resultado import describir_confianza

        resultado["confianza"] = describir_confianza(resultado)
        return resultado

    return protegido
