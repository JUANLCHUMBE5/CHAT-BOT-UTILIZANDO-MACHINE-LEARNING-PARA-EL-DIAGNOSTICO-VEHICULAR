"""Módulo para el flujo conversacional de validación técnica de diagnósticos por mecánicos."""

from __future__ import annotations

import re
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.confirmacion_diagnostico import (
    ConfirmacionDiagnosticoWhatsApp,
    _normalizar,
    interpretar_confirmacion_whatsapp,
    interpretar_respuesta_validacion_whatsapp,
    interpretar_seleccion_top3,
)
from src.config import settings
from src.core.security import cifrar_texto_reversible
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.mensaje_repository import MensajeRepository
from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository

COSTO_META_MENSAJE_SERVICIO_USD = Decimal(str(settings.meta_message_price_usd))


class ValidationWorkflow:
    """Gestiona la confirmación o descarte de diagnósticos por parte del mecánico."""

    @staticmethod
    async def procesar_confirmacion_tecnica(
        confirmacion: ConfirmacionDiagnosticoWhatsApp,
        usuario: Any,
        diag_repo: DiagnosticoRepository,
        operaciones_repo: OperacionesRepository,
        diagnostico_id: uuid.UUID | None = None,
        orden_hipotesis: int | None = None,
        metodo_seleccion: str | None = None,
    ) -> tuple[str, uuid.UUID | None]:
        """Actualiza el último diagnóstico del mecánico y deja trazabilidad del canal."""

        if confirmacion.requiere_observacion and not confirmacion.observacion:
            return (
                "⚠️ Para descartar el diagnóstico indica la falla encontrada.\n"
                "Ejemplo: *DESCARTAR: bobina de encendido defectuosa*",
                None,
            )

        diagnostico = (
            await diag_repo.obtener_pendiente_mecanico_por_id(
                diagnostico_id=diagnostico_id,
                taller_id=usuario.taller_id,
                mecanico_id=usuario.id,
            )
            if diagnostico_id
            else await diag_repo.obtener_ultimo_pendiente_mecanico(
                taller_id=usuario.taller_id,
                mecanico_id=usuario.id,
            )
        )
        if diagnostico is None:
            return (
                "ℹ️ No tienes un diagnóstico pendiente de validación. "
                "Realiza una nueva consulta y confirma el resultado después de la revisión física.",
                None,
            )

        diagnostico.estado = confirmacion.estado
        observacion = confirmacion.observacion
        if observacion:
            diagnostico.conclusion_mecanico = observacion
        elif confirmacion.estado == "confirmado":
            diagnostico.conclusion_mecanico = "Falla confirmada físicamente por el mecánico."
        else:
            diagnostico.conclusion_mecanico = "Diagnóstico dejado en revisión por el mecánico."

        orden_objetivo = orden_hipotesis or 1
        falla_seleccionada = None

        for hipotesis in diagnostico.hipotesis:
            if hipotesis.orden != orden_objetivo:
                continue

            falla_seleccionada = (
                getattr(hipotesis, "falla", None)
                or getattr(hipotesis, "nombre", None)
                or getattr(hipotesis, "diagnostico", None)
            )

            if confirmacion.estado == "confirmado":
                hipotesis.resultado = "confirmada"
            elif confirmacion.estado == "descartado":
                hipotesis.resultado = "descartada"

        validado_en = datetime.now(timezone.utc).isoformat()
        trazabilidad = dict(diagnostico.trazabilidad or {})
        trazabilidad["validacion_tecnica"] = {
            "canal": "whatsapp",
            "estado": confirmacion.estado,
            "mecanico_id": str(usuario.id),
            "validado_en": validado_en,
            "tiene_observacion": bool(observacion),
            "orden_hipotesis": orden_objetivo,
            "falla_seleccionada": falla_seleccionada,
            "metodo_seleccion": metodo_seleccion or "binario",
        }
        diagnostico.trazabilidad = trazabilidad

        await operaciones_repo.registrar_auditoria(
            accion="validar_diagnostico_whatsapp",
            entidad="diagnostico",
            entidad_id=diagnostico.id,
            taller_id=usuario.taller_id,
            usuario_id=usuario.id,
            detalles={
                "estado_nuevo": confirmacion.estado,
                "canal": "whatsapp",
                "tiene_observacion": bool(observacion),
            },
        )

        referencia = str(diagnostico.id)[:8]
        if confirmacion.estado == "confirmado":
            mensaje = f"✅ Diagnóstico *{referencia}* confirmado por el mecánico."
            if observacion:
                mensaje += f"\nReparación/observación: {observacion}"
        elif confirmacion.estado == "descartado":
            mensaje = (
                f"❌ Diagnóstico *{referencia}* descartado.\n"
                f"Falla encontrada: {observacion}"
            )
        else:
            mensaje = f"🟠 Diagnóstico *{referencia}* marcado como en revisión."
            if observacion:
                mensaje += f"\nObservación: {observacion}"
        return mensaje, diagnostico.id

    @staticmethod
    async def guardar_respuesta_validacion_outbox(
        msg_repo: MensajeRepository,
        conversacion: Any,
        usuario: Any,
        meta_message_id: str,
        respuesta_texto: str,
        proveedor: str,
        remitente: str,
    ) -> None:
        """Persiste una respuesta del flujo de validación en el outbox durable."""

        await msg_repo.crear_mensaje(
            conversacion_id=conversacion.id,
            taller_id=usuario.taller_id,
            usuario_id=usuario.id,
            meta_message_id=f"out_{meta_message_id or uuid.uuid4()}",
            direccion="salida",
            tipo="texto",
            texto=respuesta_texto,
            categoria_cobro="servicio",
            estado_entrega="pendiente",
            costo_estimado=(
                Decimal(str(settings.twilio_message_price_usd))
                if proveedor == "twilio"
                else COSTO_META_MENSAJE_SERVICIO_USD
            ),
            moneda="USD",
            proveedor=proveedor,
            destinatario_cifrado=cifrar_texto_reversible(remitente),
            disponible_entrega_en=datetime.now(timezone.utc),
        )

    @classmethod
    async def manejar_flujo_validacion(
        cls,
        session: AsyncSession,
        conversacion: Any,
        usuario: Any,
        texto_cliente: str,
        tipo_mensaje: str,
        meta_message_id: str,
        proveedor: str,
        remitente: str,
        t_inicio: float,
    ) -> Optional[dict[str, Any]]:
        """
        Interpreta si el mensaje entrante corresponde a la validación conversacional
        o a un comando explícito de confirmación/descarte. Si corresponde, ejecuta
        el flujo, guarda en outbox y commitea la transacción. Si no, retorna None.
        """
        msg_repo = MensajeRepository(session)
        diag_repo = DiagnosticoRepository(session)
        operaciones_repo = OperacionesRepository(session)

        from src.core.conversacion.extractor_hechos import ExtractorHechos

        contexto_conversacion = dict(conversacion.contexto or {})
        flujo_validacion = dict(contexto_conversacion.get("validacion_diagnostico") or {})
        etapa_validacion = flujo_validacion.get("etapa")

        # Si el mecánico indica que es otro carro o nuevo diagnóstico, liberar validación anterior
        if tipo_mensaje == "text" and ExtractorHechos.es_reinicio_solicitado(texto_cliente):
            contexto_conversacion.pop("validacion_diagnostico", None)
            conversacion.contexto = contexto_conversacion
            await session.commit()
            return None

        diagnostico_contexto_id = None
        try:
            if flujo_validacion.get("diagnostico_id"):
                diagnostico_contexto_id = uuid.UUID(str(flujo_validacion["diagnostico_id"]))
        except ValueError:
            contexto_conversacion.pop("validacion_diagnostico", None)
            conversacion.contexto = contexto_conversacion
            flujo_validacion = {}
            etapa_validacion = None

        confirmacion = None
        orden_hipotesis_seleccionada = None
        metodo_seleccion = None

        if tipo_mensaje == "text" and etapa_validacion == "esperando_confirmacion":

            diagnostico_selector = (
                await diag_repo.obtener_pendiente_mecanico_por_id(
                    diagnostico_id=diagnostico_contexto_id,
                    taller_id=usuario.taller_id,
                    mecanico_id=usuario.id,
                )
                if diagnostico_contexto_id
                else await diag_repo.obtener_ultimo_pendiente_mecanico(
                    taller_id=usuario.taller_id,
                    mecanico_id=usuario.id,
                )
            )

            hipotesis_selector = []

            if diagnostico_selector:
                # Fuente principal: hipótesis persistidas del diagnóstico.
                hipotesis_persistidas = list(
                    getattr(diagnostico_selector, "hipotesis", None) or []
                )

                if hipotesis_persistidas:
                    for h in sorted(
                        hipotesis_persistidas,
                        key=lambda x: getattr(x, "orden", 999)
                    )[:3]:
                        nombre_h = (
                            getattr(h, "falla", None)
                            or getattr(h, "nombre", None)
                            or getattr(h, "diagnostico", None)
                            or ""
                        )
                        if nombre_h:
                            hipotesis_selector.append({"falla": nombre_h})

                # Compatibilidad histórica:
                # algunos diagnósticos/tests conservan Top-3 únicamente
                # dentro de trazabilidad["predicciones_ml"].
                if not hipotesis_selector:
                    trazabilidad_selector = (
                        getattr(diagnostico_selector, "trazabilidad", None)
                        or {}
                    )

                    predicciones_ml = (
                        trazabilidad_selector.get("predicciones_ml")
                        or []
                    )

                    for pred in predicciones_ml[:3]:
                        if isinstance(pred, dict):
                            nombre_h = (
                                pred.get("falla")
                                or pred.get("nombre")
                                or pred.get("diagnostico")
                                or ""
                            )
                            if nombre_h:
                                hipotesis_selector.append(
                                    {"falla": nombre_h}
                                )

            seleccion_top3 = (
                interpretar_seleccion_top3(
                    texto_cliente,
                    hipotesis_selector,
                )
                if hipotesis_selector
                else None
            )

            if seleccion_top3 and seleccion_top3.accion == "AMBIGUO":
                respuesta_texto = (
                    "🤔 Entendido. No voy a confirmar una falla mientras exista duda.\n"
                    "Indica cuál verificaste físicamente: *1, 2 o 3*, "
                    "o escribe el nombre de la falla."
                )
                await cls.guardar_respuesta_validacion_outbox(
                    msg_repo,
                    conversacion,
                    usuario,
                    meta_message_id,
                    respuesta_texto,
                    proveedor,
                    remitente,
                )
                await session.commit()
                return {
                    "status": "esperando_confirmacion",
                    "diagnostico_id": str(diagnostico_selector.id) if diagnostico_selector else None,
                    "conversacion_id": str(conversacion.id),
                    "respuesta": respuesta_texto,
                    "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                }

            if seleccion_top3 and seleccion_top3.accion == "CONFIRMAR":
                orden_hipotesis_seleccionada = seleccion_top3.orden
                metodo_seleccion = seleccion_top3.metodo
                confirmacion = ConfirmacionDiagnosticoWhatsApp(
                    estado="confirmado"
                )

            elif seleccion_top3 and seleccion_top3.accion == "DESCARTAR":
                # Reutilizar el flujo seguro existente de NO,
                # pero contra la hipótesis seleccionada.
                orden_hipotesis_seleccionada = seleccion_top3.orden
                metodo_seleccion = seleccion_top3.metodo
                respuesta_binaria = "no"

            elif (
                seleccion_top3
                and seleccion_top3.accion == "DESCARTAR_Y_CONFIRMAR"
            ):
                # Persistir descarte específico antes de confirmar la alternativa.
                for h in (
                    getattr(diagnostico_selector, "hipotesis", None) or []
                ):
                    if getattr(h, "orden", None) == seleccion_top3.orden_descartado:
                        h.resultado = "descartada"

                orden_hipotesis_seleccionada = seleccion_top3.orden
                metodo_seleccion = seleccion_top3.metodo
                confirmacion = ConfirmacionDiagnosticoWhatsApp(
                    estado="confirmado"
                )
                respuesta_binaria = None

            else:
                respuesta_binaria = interpretar_respuesta_validacion_whatsapp(
                    texto_cliente
                )

            if confirmacion is None and respuesta_binaria == "si":
                confirmacion = ConfirmacionDiagnosticoWhatsApp(
                    estado="confirmado"
                )
                orden_hipotesis_seleccionada = 1
                metodo_seleccion = "binario"

            elif confirmacion is None and respuesta_binaria == "no":
                diagnostico = (
                    await diag_repo.obtener_pendiente_mecanico_por_id(
                        diagnostico_id=diagnostico_contexto_id,
                        taller_id=usuario.taller_id,
                        mecanico_id=usuario.id,
                    )
                    if diagnostico_contexto_id
                    else await diag_repo.obtener_ultimo_pendiente_mecanico(
                        taller_id=usuario.taller_id,
                        mecanico_id=usuario.id,
                    )
                )

                falla_descartada = (
                    diagnostico.falla_predicha
                    if diagnostico
                    else "la hipótesis principal"
                )

                if diagnostico and orden_hipotesis_seleccionada:
                    for h in (
                        getattr(diagnostico, "hipotesis", None) or []
                    ):
                        if getattr(h, "orden", None) == orden_hipotesis_seleccionada:
                            falla_descartada = (
                                getattr(h, "falla", None)
                                or getattr(h, "nombre", None)
                                or getattr(h, "diagnostico", None)
                                or falla_descartada
                            )
                            h.resultado = "descartada"
                            break

                sintoma_base = diagnostico.sintoma_original if diagnostico else ""

                from src.core.conversacion.models import ConversationState, FactType
                raw_estado = contexto_conversacion.get("conversation_state") or contexto_conversacion.get("estado_conversacion")
                estado_obj = (
                    ConversationState.from_dict(raw_estado)
                    if raw_estado and isinstance(raw_estado, dict)
                    else ConversationState(session_id=str(conversacion.id))
                )
                if falla_descartada not in estado_obj.hipotesis_descartadas:
                    estado_obj.hipotesis_descartadas.append(falla_descartada)
                campo_desc = f"descarte_{falla_descartada.lower()[:30].replace(' ', '_')}"
                estado_obj.registrar_hecho(
                    campo_desc,
                    f"{falla_descartada} descartada",
                    categoria="componente_descartado",
                    tipo=FactType.CONDICION,
                )
                contexto_conversacion["conversation_state"] = estado_obj.exportar_dict()
                contexto_conversacion["estado_conversacion"] = estado_obj.exportar_dict()

                # Verificar si en este mismo mensaje el mecánico ya aportó nueva evidencia
                from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad

                texto_adicional = re.sub(
                    r"^(?:no|negativo|descartado|falso|no es|no fue|descartar)\b[,\s.:;-]*",
                    "",
                    texto_cliente,
                    flags=re.IGNORECASE,
                ).strip()

                if len(texto_adicional.split()) >= 3 and not ValidadorCompatibilidad.es_evidencia_espuria(texto_adicional):
                    # Caso: contexto actual + hipótesis rechazada + nueva evidencia inmediata
                    contexto_conversacion.pop("validacion_diagnostico", None)
                    conversacion.contexto = contexto_conversacion
                    await session.commit()
                    texto_a_evaluar = (
                        f"{sintoma_base}. Descarte previo: no es {falla_descartada}. "
                        f"Nueva observación técnica: {texto_adicional}"
                    ).strip()
                    return {
                        "status": "evaluar_alternativa",
                        "texto_evaluar": texto_a_evaluar,
                        "diagnostico_forzado": None,
                    }

                # Si no hay nueva evidencia suficiente, realizar pregunta discriminante adaptativa (excluyendo hechos conocidos)
                from src.core.conversacion.generador_preguntas import GeneradorPreguntas

                pregunta_disc, intent_disc = GeneradorPreguntas.formular_pregunta_discriminante_post_descarte(
                    estado=estado_obj,
                    falla_descartada=falla_descartada,
                )

                # Registrar la respuesta del usuario ("NO") y la pregunta técnica discriminante formulada
                estado_obj.registrar_respuesta(texto_cliente, interpretacion=f"Descarte de hipótesis: {falla_descartada}")
                estado_obj.registrar_pregunta(
                    intent=intent_disc,
                    texto=pregunta_disc,
                    incrementar_repregunta=False,
                )

                # Preservar atributos de caso y memoria estructurada
                placa_activa = (
                    estado_obj.placa
                    or contexto_conversacion.get("placa_posttest")
                    or contexto_conversacion.get("placa")
                    or getattr(conversacion, "placa", None)
                )
                if placa_activa:
                    estado_obj.placa = placa_activa
                case_id_activo = (
                    estado_obj.case_id
                    or contexto_conversacion.get("case_id")
                    or (str(diagnostico.id) if diagnostico else None)
                )
                if case_id_activo:
                    estado_obj.case_id = str(case_id_activo)

                if diagnostico and diagnostico.sintoma_original and diagnostico.sintoma_original not in estado_obj.active_symptoms:
                    estado_obj.active_symptoms.append(diagnostico.sintoma_original)

                contexto_conversacion["conversation_state"] = estado_obj.exportar_dict()
                contexto_conversacion["estado_conversacion"] = estado_obj.exportar_dict()
                if placa_activa:
                    contexto_conversacion["placa"] = placa_activa
                    contexto_conversacion["placa_posttest"] = placa_activa
                if case_id_activo:
                    contexto_conversacion["case_id"] = str(case_id_activo)

                respuesta_texto = (
                    f"❌ Registrado: se descarta *{falla_descartada}*.\n\n"
                    f"🔧 *Pregunta técnica discriminante:*\n"
                    f"Para aislar la causa real y reevaluar el diagnóstico:\n"
                    f"{pregunta_disc}\n\n"
                    f"💬 Escribe la observación adicional o prueba realizada para reorientar el análisis."
                )

                flujo_validacion["etapa"] = "esperando_falla_real"
                flujo_validacion["diagnostico_id"] = str(diagnostico.id) if diagnostico else None
                flujo_validacion["falla_descartada"] = falla_descartada
                flujo_validacion["sintoma_base"] = sintoma_base
                contexto_conversacion["validacion_diagnostico"] = flujo_validacion
                conversacion.contexto = contexto_conversacion
                await cls.guardar_respuesta_validacion_outbox(
                    msg_repo, conversacion, usuario, meta_message_id, respuesta_texto, proveedor, remitente
                )
                await session.commit()
                return {
                    "status": "esperando_falla_real",
                    "diagnostico_id": str(diagnostico.id) if diagnostico else None,
                    "conversacion_id": str(conversacion.id),
                    "respuesta": respuesta_texto,
                    "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                }
        elif tipo_mensaje == "text" and etapa_validacion == "esperando_falla_real":
            falla_real = texto_cliente.strip()[:4000]
            texto_norm = _normalizar(falla_real)

            # Saludos cordiales
            saludos = ("hola", "holaa", "buenas", "buenos dias", "buenas tardes", "buenas noches", "que tal", "saludos", "ola")
            if any(texto_norm == s or texto_norm.startswith(f"{s} ") for s in saludos):
                respuesta_texto = (
                    "⚠️ Indica la falla encontrada físicamente o describe los síntomas detectados "
                    "(por ejemplo: *en carretera jalonea a 80 km/h*) para reorientar el diagnóstico."
                )
                await cls.guardar_respuesta_validacion_outbox(
                    msg_repo, conversacion, usuario, meta_message_id, respuesta_texto, proveedor, remitente
                )
                await session.commit()
                return {
                    "status": "esperando_falla_real",
                    "diagnostico_id": str(diagnostico_contexto_id) if diagnostico_contexto_id else None,
                    "conversacion_id": str(conversacion.id),
                    "respuesta": respuesta_texto,
                    "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                }

            sintoma_base = flujo_validacion.get("sintoma_base") or ""
            falla_previa_descartada = flujo_validacion.get("falla_descartada") or "la hipótesis previa"

            es_confirmacion_fisica_concreta = any(
                frase in texto_norm
                for frase in (
                    "era ", "fue ", "encontre ", "encontré ", "solucionado con ", "cambie ", "cambié ",
                    "se cambio ", "se cambió ", "descartar:", "descartar "
                )
            ) or bool(
                re.search(
                    r"\b(defectuos[ao]|dañad[ao]|rot[ao]|quemad[ao]|cruzad[ao]|suci[ao]|obstruid[ao]|tapado|tapada|rajad[ao]|gastad[ao]|desgastad[ao]|vencid[ao]|en\s+corto|cortocircuito)\b",
                    texto_norm,
                )
            )

            # Filtrar evidencia espuria (teléfonos, secuencias numéricas sin contenido automotriz)
            from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad
            if ValidadorCompatibilidad.es_evidencia_espuria(falla_real):
                respuesta_texto = (
                    "⚠️ El texto ingresado no describe una falla o síntoma mecánico del vehículo. "
                    "Por favor describe lo que observas (por ejemplo: 'el motor gira pero no enciende' o 'se escucha un clic seco')."
                )
                await cls.guardar_respuesta_validacion_outbox(
                    msg_repo, conversacion, usuario, meta_message_id, respuesta_texto, proveedor, remitente
                )
                await session.commit()
                return {
                    "status": "esperando_falla_real",
                    "diagnostico_id": str(diagnostico_contexto_id) if diagnostico_contexto_id else None,
                    "conversacion_id": str(conversacion.id),
                    "respuesta": respuesta_texto,
                    "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                }

            # Si el mecánico describe nueva evidencia o responde la pregunta discriminante
            if not es_confirmacion_fisica_concreta and len(falla_real.split()) >= 2:
                from src.core.conversacion.extractor_hechos import ExtractorHechos
                from src.core.conversacion.models import ConversationState

                raw_st = contexto_conversacion.get("conversation_state") or contexto_conversacion.get("estado_conversacion")
                if raw_st and isinstance(raw_st, dict):
                    estado_obj = ConversationState.from_dict(raw_st)
                    ExtractorHechos.extraer_y_actualizar(estado_obj, falla_real)
                    contexto_conversacion["conversation_state"] = estado_obj.exportar_dict()
                    contexto_conversacion["estado_conversacion"] = estado_obj.exportar_dict()

                contexto_conversacion.pop("validacion_diagnostico", None)
                conversacion.contexto = contexto_conversacion
                await session.commit()
                texto_a_evaluar = (
                    f"{sintoma_base}. Descarte previo: no es {falla_previa_descartada}. "
                    f"Nueva evidencia técnica: {falla_real}"
                ).strip()
                return {
                    "status": "evaluar_alternativa",
                    "texto_evaluar": texto_a_evaluar,
                    "diagnostico_forzado": None,
                }

            if len(falla_real) < 4:
                respuesta_texto = (
                    "⚠️ Describe la falla concreta encontrada o el comportamiento observado, "
                    "por ejemplo: *inyector de GNV obstruido* o *pierde fuerza al acelerar*."
                )
                await cls.guardar_respuesta_validacion_outbox(
                    msg_repo, conversacion, usuario, meta_message_id, respuesta_texto, proveedor, remitente
                )
                await session.commit()
                return {
                    "status": "esperando_falla_real",
                    "diagnostico_id": str(diagnostico_contexto_id) if diagnostico_contexto_id else None,
                    "conversacion_id": str(conversacion.id),
                    "respuesta": respuesta_texto,
                    "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                }

            confirmacion = ConfirmacionDiagnosticoWhatsApp(
                estado="descartado",
                observacion=falla_real,
            )

        # Se conservan los comandos explícitos como compatibilidad
        if confirmacion is None:
            confirmacion = (
                interpretar_confirmacion_whatsapp(texto_cliente)
                if tipo_mensaje == "text"
                else None
            )

        if confirmacion is not None:
            respuesta_texto, diagnostico_confirmado_id = await cls.procesar_confirmacion_tecnica(
                confirmacion,
                usuario,
                diag_repo,
                operaciones_repo,
                diagnostico_id=diagnostico_contexto_id,
                orden_hipotesis=orden_hipotesis_seleccionada,
                metodo_seleccion=metodo_seleccion,
            )
            if diagnostico_confirmado_id:
                contexto_conversacion.pop("validacion_diagnostico", None)
                contexto_conversacion.pop("conversation_state", None)
                contexto_conversacion.pop("estado_conversacion", None)
                contexto_conversacion["caso_finalizado"] = True
                conversacion.contexto = contexto_conversacion

            await cls.guardar_respuesta_validacion_outbox(
                msg_repo, conversacion, usuario, meta_message_id, respuesta_texto, proveedor, remitente
            )
            await session.commit()
            return {
                "status": "validacion_tecnica",
                "diagnostico_id": str(diagnostico_confirmado_id) if diagnostico_confirmado_id else None,
                "conversacion_id": str(conversacion.id),
                "respuesta": respuesta_texto,
                "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
            }

        return None
