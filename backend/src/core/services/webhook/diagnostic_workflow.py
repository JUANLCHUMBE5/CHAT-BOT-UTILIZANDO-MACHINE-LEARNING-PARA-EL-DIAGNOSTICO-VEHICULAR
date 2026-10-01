"""Flujo de audio y diagnóstico técnico del webhook de WhatsApp."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Optional

from src.core.gemini_queue import gemini_rate_limiter
from src.core.gestor_diagnostico import ResultadoDiagnostico
from src.core.logger import logger
from src.core.services.whatsapp_provider import whatsapp_provider_service


@dataclass
class ResultadoFlujoDiagnostico:
    """Resultado normalizado para persistir tras procesar texto o una nota de voz."""

    dto: ResultadoDiagnostico
    texto_cliente: str
    duracion_ms: int


class TechnicalDiagnosticWorkflow:
    """Prepara el DTO ML/RAG/Gemini sin mezclarlo con identidad ni outbox."""

    @staticmethod
    async def preparar(
        gestor: Any,
        conversacion: Any,
        usuario: Any,
        remitente: str,
        proveedor: str,
        tipo_mensaje: str,
        texto_cliente: str,
        audio_id: str,
        placa: str,
        marca_modelo: str,
        diagnostico_forzado: Optional[str] = None,
    ) -> ResultadoFlujoDiagnostico:
        inicio = time.perf_counter()
        id_sesion = str(conversacion.id)
        contexto_actual = dict(conversacion.contexto or {})

        # Si el caso previo fue completado o finalizado, reiniciar memoria para el nuevo caso
        if contexto_actual.get("caso_finalizado"):
            gestor.session_manager.finalizar_caso(id_sesion)
            contexto_actual.pop("caso_finalizado", None)
            contexto_actual.pop("conversation_state", None)
            contexto_actual.pop("estado_conversacion", None)
            contexto_actual.pop("validacion_diagnostico", None)
            conversacion.contexto = contexto_actual
            gestor.session_manager.cargar_contexto(id_sesion, contexto_actual)
        else:
            gestor.session_manager.cargar_contexto(id_sesion, contexto_actual)

        from src.core.conversacion.extractor_hechos import ExtractorHechos
        if (
            tipo_mensaje == "text"
            and ExtractorHechos.es_reinicio_solicitado(texto_cliente)
            and not ExtractorHechos.contiene_informacion_diagnostica(texto_cliente)
        ):
            gestor.session_manager.reiniciar_sesion(id_sesion)
            conversacion.contexto = gestor.session_manager.exportar_contexto(id_sesion)
            dto = ResultadoDiagnostico(
                respuesta_texto=(
                    "🚗 *Caso finalizado.* He limpiado la memoria para registrar un nuevo vehículo.\n\n"
                    "¿Cuál es la marca, modelo y la falla o síntoma que presenta el nuevo auto?"
                ),
                diagnostico_ml="Reinicio de sesión",
                confianza_ml=1.0,
                contexto_manual="",
                titulo_manual="",
                requiere_revision_humana=False,
                estado_sesion="inicio",
                modo_diagnostico="inicio",
                tipo_consulta="reinicio",
            )
            return ResultadoFlujoDiagnostico(
                dto=dto,
                texto_cliente=texto_cliente,
                duracion_ms=int((time.perf_counter() - inicio) * 1000),
            )

        if tipo_mensaje == "audio":
            try:
                audio_bytes, mime_type = await whatsapp_provider_service.descargar_audio(
                    proveedor, audio_id
                )
                slot_audio, motivo_audio = await gemini_rate_limiter.intentar_adquirir_slot_db()
                if not slot_audio:
                    raise RuntimeError(f"Transcripción no disponible: {motivo_audio}")
                texto_cliente = await asyncio.to_thread(
                    gestor.procesador_audio.transcribir_nota_de_voz,
                    audio_id,
                    audio_bytes,
                    mime_type,
                    gestor.api_key,
                )
                await gemini_rate_limiter.persistir_estado_local_db()
            except Exception as exc:
                await gemini_rate_limiter.persistir_estado_local_db()
                logger.warning(f"[Audio WhatsApp] No se pudo transcribir: {exc}")
                dto = ResultadoDiagnostico(
                    respuesta_texto=(
                        "🎤 No pude transcribir la nota de voz de forma segura. "
                        "Por favor, escribe el síntoma del vehículo en texto."
                    ),
                    diagnostico_ml="Audio pendiente de transcripción",
                    confianza_ml=0.0,
                    contexto_manual="",
                    titulo_manual="",
                    requiere_revision_humana=True,
                    estado_sesion="esperando_clarificacion",
                    modo_diagnostico="esperando_clarificacion",
                    tipo_consulta="aclaracion",
                )
            else:
                dto = await TechnicalDiagnosticWorkflow._procesar_texto(
                    gestor, texto_cliente, placa, marca_modelo, id_sesion, remitente, proveedor, usuario, conversacion,
                    diagnostico_forzado=diagnostico_forzado,
                )
        else:
            dto = await TechnicalDiagnosticWorkflow._procesar_texto(
                gestor, texto_cliente, placa, marca_modelo, id_sesion, remitente, proveedor, usuario, conversacion,
                diagnostico_forzado=diagnostico_forzado,
            )

        # Fusión segura del contexto durable
        contexto_previo = dict(conversacion.contexto or {})
        contexto_exportado = dict(gestor.session_manager.exportar_contexto(id_sesion) or {})
        contexto_actualizado = {**contexto_previo, **contexto_exportado}

        # Preservar claves críticas de la conversación y del webhook
        if "placa_posttest" in contexto_previo and "placa_posttest" not in contexto_actualizado:
            contexto_actualizado["placa_posttest"] = contexto_previo["placa_posttest"]
        if "placa" in contexto_previo and "placa" not in contexto_actualizado:
            contexto_actualizado["placa"] = contexto_previo["placa"]

        conversacion.contexto = contexto_actualizado
        return ResultadoFlujoDiagnostico(
            dto=dto,
            texto_cliente=texto_cliente,
            duracion_ms=int((time.perf_counter() - inicio) * 1000),
        )

    @staticmethod
    async def _procesar_texto(
        gestor: Any,
        texto_cliente: str,
        placa: str,
        marca_modelo: str,
        id_sesion: str,
        remitente: str,
        proveedor: str,
        usuario: Any,
        conversacion: Any,
        diagnostico_forzado: Optional[str] = None,
    ) -> ResultadoDiagnostico:
        from src.core.conversacion.models import ConversationState
        from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
        from src.core.conversacion.repositorio import PostgresConversationRepository

        # Reutilizar / inyectar la infraestructura persistente existente
        repo = getattr(gestor, "conversation_repo", None)
        if repo is None:
            repo = PostgresConversationRepository()
            try:
                setattr(gestor, "conversation_repo", repo)
            except Exception:
                pass

        if conversacion and getattr(conversacion, "contexto", None):
            ctx = conversacion.contexto
            if isinstance(ctx, dict):
                st_dict = ctx.get("conversation_state") if "conversation_state" in ctx else ctx
                if isinstance(st_dict, dict) and ("hechos" in st_dict or "case_id" in st_dict):
                    try:
                        st_init = ConversationState.from_dict(st_dict)
                        st_init.session_id = id_sesion
                        if placa and not st_init.placa:
                            st_init.placa = placa
                        if hasattr(repo, "_fallback"):
                            await repo._fallback.save_session(id_sesion, st_init)
                        else:
                            await repo.save_session(id_sesion, st_init)
                    except Exception as e:
                        logger.warning(f"[DiagnosticWorkflow] Error al deserializar contexto previo: {e}")

        orquestador = OrquestadorConversacion(repositorio=repo)
        res_turno = await orquestador.procesar_turno(
            session_id=id_sesion,
            texto_usuario=texto_cliente,
            gestor_diagnostico=gestor,
            placa=placa,
            marca_modelo=marca_modelo,
            proveedor=proveedor,
            diagnostico_forzado=diagnostico_forzado,
            diferir_encolado_persistente=True,
            taller_id=str(usuario.taller_id),
            usuario_id=str(usuario.id),
            conversacion_id=str(conversacion.id),
            remitente=remitente,
        )

        estado_actual = res_turno.get("estado")
        decision = res_turno.get("decision")
        decision_transicion = res_turno.get("decision_transicion")
        es_cambio_caso = (decision == "REINICIO" or decision_transicion == "CAMBIO_DE_CASO")

        if estado_actual:
            contexto_previo = dict(conversacion.contexto or {}) if conversacion else {}
            contexto_export_estado = estado_actual.exportar_dict()

            # Fusión segura sin destruir claves persistidas
            contexto_fusion = {**contexto_previo, "conversation_state": contexto_export_estado}
            contexto_fusion["case_id"] = estado_actual.case_id

            if es_cambio_caso:
                contexto_fusion.pop("placa_posttest", None)
                contexto_fusion.pop("placa", None)
            else:
                placa_efectiva = (
                    estado_actual.placa
                    or placa
                    or contexto_previo.get("placa_posttest")
                    or contexto_previo.get("placa")
                )
                if placa_efectiva and placa_efectiva not in ("WAPP-01", "SIN-PLACA", ""):
                    contexto_fusion["placa"] = placa_efectiva
                    contexto_fusion["placa_posttest"] = placa_efectiva

            conversacion.contexto = contexto_fusion

            # Sincronizar SessionManager
            datos_sesion_manager = dict(contexto_fusion)
            datos_sesion_manager["conversation_state"] = contexto_export_estado
            datos_sesion_manager["case_id"] = estado_actual.case_id
            if not es_cambio_caso and estado_actual.placa:
                datos_sesion_manager["placa"] = estado_actual.placa
            gestor.session_manager.cargar_contexto(id_sesion, datos_sesion_manager)

        if res_turno.get("status") in ("reinicio", "saludo", "saludo_caso_activo") or decision in ("REINICIO", "SALUDO"):
            es_saludo = (decision == "SALUDO" or res_turno.get("status") in ("saludo", "saludo_caso_activo"))
            return ResultadoDiagnostico(
                respuesta_texto=res_turno["respuesta_texto"],
                diagnostico_ml="Saludo / Bienvenida" if es_saludo else "Reinicio de sesión",
                confianza_ml=1.0,
                contexto_manual="",
                titulo_manual="",
                requiere_revision_humana=False,
                estado_sesion=estado_actual.fase.value if (estado_actual and res_turno.get("status") == "saludo_caso_activo") else "inicio",
                modo_diagnostico=estado_actual.fase.value if (estado_actual and res_turno.get("status") == "saludo_caso_activo") else "inicio",
                tipo_consulta="saludo" if es_saludo else "reinicio",
            )
        elif decision in ("PREGUNTAR", "PLAN_B") or (
            res_turno.get("es_pregunta") and decision not in ("DIAGNOSTICAR", "DIFERENCIAL", "DETALLE", "CONCLUSION_TECNICA")
        ):
            return ResultadoDiagnostico(
                respuesta_texto=res_turno["respuesta_texto"],
                diagnostico_ml="Aclaración técnica / Auto-interrogador",
                confianza_ml=0.0,
                contexto_manual="",
                titulo_manual="",
                requiere_revision_humana=True,
                estado_sesion="esperando_clarificacion",
                modo_diagnostico="esperando_clarificacion",
                tipo_consulta="aclaracion",
            )
        elif decision == "DIFERENCIAL":
            dto_base = res_turno.get("dto")
            if dto_base:
                return dto_base.model_copy(update={"respuesta_texto": res_turno["respuesta_texto"]})
            return ResultadoDiagnostico(
                respuesta_texto=res_turno["respuesta_texto"],
                diagnostico_ml=res_turno.get("diagnostico_ml", "Diagnóstico diferencial"),
                confianza_ml=res_turno.get("confianza_ml", 0.0),
                contexto_manual="",
                titulo_manual="",
                requiere_revision_humana=True,
                estado_sesion="diferencial",
                modo_diagnostico="diferencial",
                tipo_consulta="diagnostico",
            )
        elif decision == "DETALLE" or res_turno.get("status") == "detalle":
            return ResultadoDiagnostico(
                respuesta_texto=res_turno["respuesta_texto"],
                diagnostico_ml=res_turno.get("diagnostico_ml", "Detalle técnico"),
                confianza_ml=res_turno.get("confianza_ml", 1.0),
                contexto_manual="",
                titulo_manual="",
                requiere_revision_humana=False,
                estado_sesion="detalle",
                modo_diagnostico="detalle",
                tipo_consulta="consulta_tecnica",
            )
        else:
            dto_base = res_turno.get("dto")
            if dto_base:
                return dto_base.model_copy(update={"respuesta_texto": res_turno["respuesta_texto"]})
            return ResultadoDiagnostico(
                respuesta_texto=res_turno.get("respuesta_texto", ""),
                diagnostico_ml=res_turno.get("diagnostico_ml", "Diagnóstico completado"),
                confianza_ml=res_turno.get("confianza_ml", 0.8),
                contexto_manual="",
                titulo_manual="",
                requiere_revision_humana=False,
                estado_sesion="completo",
                modo_diagnostico="completo",
                tipo_consulta="diagnostico",
            )
