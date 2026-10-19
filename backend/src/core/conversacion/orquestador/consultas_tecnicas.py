"""Manejo de consultas técnicas informativas y procedimientos de comprobación paso a paso."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState, FactType
from src.core.intent_classifier import clasificar_intencion_consulta


class ManejadorConsultasTecnicas:
    """Procesa consultas técnicas puras o solicitudes de procedimientos de comprobación de taller."""

    @classmethod
    def es_consulta_o_procedimiento(cls, texto_limpio: str, estado: ConversationState) -> bool:
        """Determina si el turno es una consulta técnica pura o procedimiento paso a paso."""
        es_solicitud_detalle = ExtractorHechos.es_solicitud_detalle(texto_limpio)
        tiene_sintomas = bool(
            estado.active_symptoms
            or estado.top3_actual
            or getattr(estado, "falla_principal", None)
            or any(
                h.categoria in ("sintoma", "condicion") or h.tipo == FactType.SINTOMA
                for h in estado.hechos.values()
            )
        )
        return es_solicitud_detalle or (
            not tiene_sintomas and clasificar_intencion_consulta(texto_limpio) == "consulta_tecnica"
        )

    @classmethod
    def procesar_consulta(
        cls,
        estado: ConversationState,
        texto_limpio: str,
        gestor_diagnostico: Any,
        session_id: str,
        t0: float,
        remitente: Optional[str] = None,
        proveedor: str = "meta",
        taller_id: Optional[str] = None,
        usuario_id: Optional[str] = None,
        conversacion_id: Optional[str] = None,
        diferir_encolado_persistente: bool = False,
    ) -> Dict[str, Any]:
        """Ejecuta la consulta técnica contra el gestor y retorna la respuesta con procedimiento OEM."""
        es_solicitud_detalle = ExtractorHechos.es_solicitud_detalle(texto_limpio)
        dto_tecnico = gestor_diagnostico._procesar_consulta_tecnica(
            pregunta=texto_limpio,
            inicio_total=t0,
            remitente=remitente,
            proveedor=proveedor,
            taller_id=taller_id,
            usuario_id=usuario_id,
            conversacion_id=conversacion_id or session_id,
            slot_gemini_preconcedido=None,
            diferir_encolado_persistente=diferir_encolado_persistente,
        )
        resp_texto = getattr(dto_tecnico, "respuesta_texto", "")
        if es_solicitud_detalle and (
            not resp_texto
            or "No encontré una fuente documental" in resp_texto
            or "no dispongo de información" in resp_texto.lower()
            or "aviso de control metrológico" in resp_texto.lower()
            or "sin respaldo documental" in resp_texto.lower()
        ):
            resp_texto = cls._obtener_procedimiento_respaldo(texto_limpio.casefold())

        if resp_texto and (estado.marca or estado.modelo):
            veh_str = f"{estado.marca or ''} {estado.modelo or ''}".strip()
            lineas = []
            for linea in resp_texto.split("\n"):
                if "Modelos Compatibles Frecuentes en Peru:" in linea:
                    lineas.append(f"Vehículo en Consulta: {veh_str}")
                else:
                    lineas.append(linea)
            resp_texto = "\n".join(lineas)

        return {
            "status": "consulta_tecnica" if not es_solicitud_detalle else "solicitud_detalle",
            "respuesta_texto": resp_texto or "Información técnica.",
            "diagnostico_ml": getattr(dto_tecnico, "diagnostico_ml", "Consulta técnica"),
            "confianza_ml": getattr(dto_tecnico, "confianza_ml", 1.0),
            "fase": estado.fase.value,
            "es_pregunta": False,
            "decision": "DETALLE",
            "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
            "estado": estado,
            "dto": dto_tecnico,
        }

    @classmethod
    def _obtener_procedimiento_respaldo(cls, norm_q: str) -> str:
        from src.core.conversacion.formato_salidas.orientacion_segura import orientar_sin_manual
        return orientar_sin_manual(norm_q)
