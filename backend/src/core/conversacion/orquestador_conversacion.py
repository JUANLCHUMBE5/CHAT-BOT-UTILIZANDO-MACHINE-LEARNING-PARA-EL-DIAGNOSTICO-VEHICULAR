"""Orquestador principal de la memoria conversacional acumulativa y auto-interrogador inteligente."""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.core.conversacion.repositorio import ConversationStateRepository, PostgresConversationRepository
from src.core.conversacion.turnos.ciclo_casos import ciclo_casos
from src.core.conversacion.turnos.consultas_basicas import consultas_basicas
from src.core.conversacion.turnos.consultas_tecnicas import consultas_tecnicas
from src.core.conversacion.turnos.contexto import ContextoTurno
from src.core.conversacion.turnos.entrada_segura import entrada_segura
from src.core.conversacion.turnos.evidencia import evidencia
from src.core.conversacion.turnos.interpretacion import interpretacion
from src.core.conversacion.turnos.persistir_salida import persistir_salida
from src.core.conversacion.turnos.preparar_diagnostico import preparar_diagnostico
from src.core.conversacion.turnos.resolver_diagnostico import resolver_diagnostico
from src.core.conversacion.turnos.respuestas_cortas import respuestas_cortas
from src.core.conversacion.turnos.transicion_y_plan_b import transicion_y_plan_b
from src.infrastructure.rag.contrato_documental import proteger_salida_conversacional
from src.infrastructure.rag.documental_evidencia import mediciones_con_procedencia
from src.infrastructure.rag.documental_salida import es_solicitud_especificacion


class OrquestadorConversacion:
    """Coordina el ciclo de vida de la conversación, extracción acumulativa y diagnóstico."""

    def __init__(self, repositorio: Optional[ConversationStateRepository] = None):
        self.repositorio = repositorio or PostgresConversationRepository()

    async def finalizar_caso(self, session_id: str, gestor_diagnostico: Optional[Any] = None) -> None:
        """Finaliza formalmente el case_id en el repositorio y en el SessionManager."""
        nuevo_id = None
        session_manager = getattr(gestor_diagnostico, "session_manager", None)
        if session_manager is not None:
            nuevo_id = session_manager.finalizar_caso(session_id)
        await self.repositorio.finalizar_caso(session_id, nuevo_id)

    def _proteger_salida(
        self, salida_dict: Dict[str, Any], consulta_usuario: str, vehiculo_str: str, corpus_validado: bool
    ) -> Dict[str, Any]:
        """Aplica la política de gobernanza documental (C02) a todas las salidas del orquestador."""
        resp_txt = salida_dict.get("respuesta_texto", "")
        if resp_txt:
            resp_seg, conf_seg, fue_interceptada = proteger_salida_conversacional(
                respuesta_propuesta=resp_txt,
                vehiculo_str=vehiculo_str,
                consulta_usuario=consulta_usuario,
                corpus_validado=corpus_validado,
                especificacion_autorizada=False,
                mediciones_reportadas=mediciones_con_procedencia(salida_dict.get("estado")),
            )
            salida_dict["respuesta_texto"] = resp_seg
            if fue_interceptada:
                salida_dict["confianza_ml"] = 0.0
                if salida_dict.get("decision") in (
                    "SEGURIDAD_CRITICA",
                    "CRITICAL_STOP",
                    "PRERREQUISITOS_OEM",
                ):
                    salida_dict["respuesta_texto"] = (
                        "PELIGRO: No realices la maniobra. Detén el trabajo y asegura el vehículo. No abras circuitos calientes ni presurizados y no te sitúes bajo un apoyo inseguro.\n"
                        + resp_seg
                    )
                    return salida_dict
                salida_dict["cifras_retenidas"] = True
                if es_solicitud_especificacion(consulta_usuario):
                    salida_dict["decision"] = "ABSTENCION_OEM_TOLERANCIA"
                    salida_dict["status"] = "tolerancia_no_validada"
        return salida_dict

    async def procesar_turno(
        self,
        session_id: str,
        texto_usuario: str,
        gestor_diagnostico: Any,
        placa: Optional[str] = None,
        marca_modelo: Optional[str] = None,
        proveedor: str = "meta",
        diagnostico_forzado: Optional[str] = None,
        diferir_encolado_persistente: bool = False,
        taller_id: Optional[str] = None,
        usuario_id: Optional[str] = None,
        conversacion_id: Optional[str] = None,
        remitente: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Procesa un turno conversacional de WhatsApp aplicando la política documental en todas las rutas."""
        res = await self._procesar_turno_interno(
            session_id=session_id,
            texto_usuario=texto_usuario,
            gestor_diagnostico=gestor_diagnostico,
            placa=placa,
            marca_modelo=marca_modelo,
            proveedor=proveedor,
            diagnostico_forzado=diagnostico_forzado,
            diferir_encolado_persistente=diferir_encolado_persistente,
            taller_id=taller_id,
            usuario_id=usuario_id,
            conversacion_id=conversacion_id,
            remitente=remitente,
        )
        estado = res.get("estado")
        # Defensa final frente a retornos anticipados: la respuesta de peligro
        # es autoritativa; jamás se agrega a una instrucción contradictoria.
        from src.core.diagnostico.politica_seguridad import PoliticaSeguridad, SeveridadSeguridad

        severidad, banner = PoliticaSeguridad.evaluar_severidad(texto_usuario, "", estado=estado)
        if severidad == SeveridadSeguridad.CRITICAL_STOP and banner:
            res.update(
                respuesta_texto=banner.strip(),
                decision="SEGURIDAD_CRITICA",
                confianza_ml=0.0,
                es_pregunta=False,
            )
        if estado is not None:
            res.setdefault("case_id", estado.case_id)
        veh_str = f"{getattr(estado, 'marca', '') or ''} {getattr(estado, 'modelo', '') or ''} {getattr(estado, 'anio', '') or ''}".strip()
        if res.get("decision") == "SEGURIDAD_CRITICA" and veh_str:
            res["respuesta_texto"] = f"Vehículo: {veh_str}.\n" + res["respuesta_texto"]
        elif (
            veh_str and estado is not None
            and not getattr(estado, "banner_vehiculo_mostrado", False)
            and res.get("decision") != "CONSULTA_MEMORIA"
        ):
            res["respuesta_texto"] = f"Vehículo: {veh_str}.\n" + res["respuesta_texto"]
            estado.banner_vehiculo_mostrado = True
        corpus_val = bool(getattr(getattr(gestor_diagnostico, "motor_rag", None), "corpus_validado", False))
        resultado = self._proteger_salida(res, texto_usuario, veh_str, corpus_val)
        if estado is not None and resultado.get("decision") != "CONSULTA_MEMORIA":
            if estado.trazabilidad:
                estado.trazabilidad[-1]["respuesta_enviada"] = resultado.get("respuesta_texto", "")
            if diferir_encolado_persistente and hasattr(self.repositorio, "_fallback"):
                await self.repositorio._fallback.save_session(session_id, estado)
            else:
                await self.repositorio.save_session(session_id, estado)
        return resultado

    async def _procesar_turno_interno(
        self,
        session_id: str,
        texto_usuario: str,
        gestor_diagnostico: Any,
        placa: Optional[str] = None,
        marca_modelo: Optional[str] = None,
        proveedor: str = "meta",
        diagnostico_forzado: Optional[str] = None,
        diferir_encolado_persistente: bool = False,
        taller_id: Optional[str] = None,
        usuario_id: Optional[str] = None,
        conversacion_id: Optional[str] = None,
        remitente: Optional[str] = None,
    ) -> Dict[str, Any]:
        turno = ContextoTurno(
            session_id=session_id,
            texto_usuario=texto_usuario,
            gestor_diagnostico=gestor_diagnostico,
            placa=placa,
            marca_modelo=marca_modelo,
            proveedor=proveedor,
            diagnostico_forzado=diagnostico_forzado,
            diferir_encolado_persistente=diferir_encolado_persistente,
            taller_id=taller_id,
            usuario_id=usuario_id,
            conversacion_id=conversacion_id,
            remitente=remitente,
        )
        for etapa in (
            entrada_segura,
            ciclo_casos,
            consultas_basicas,
            consultas_tecnicas,
            transicion_y_plan_b,
            interpretacion,
            evidencia,
            preparar_diagnostico,
            respuestas_cortas,
            resolver_diagnostico,
            persistir_salida,
        ):
            resultado = await etapa(self, turno)
            if resultado is not None:
                return resultado
        raise RuntimeError("El flujo conversacional terminó sin respuesta")

    procesar_mensaje = procesar_turno
