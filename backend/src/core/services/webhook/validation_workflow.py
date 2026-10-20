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
    SeleccionHipotesisTop3,
    _normalizar,
    interpretar_confirmacion_whatsapp,
    interpretar_respuesta_validacion_whatsapp,
    interpretar_seleccion_top3,
)
from src.config import settings
from src.core.logger import logger
from src.core.security import cifrar_texto_reversible
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.mensaje_repository import MensajeRepository
from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository

COSTO_META_MENSAJE_SERVICIO_USD = Decimal(str(settings.meta_message_price_usd))

_PATRON_DTC_O_MEDICION = re.compile(
    r"\b(?:[PBCU]\d{4}|\d+(?:[.,]\d+)?\s*(?:psi|bar|kpa|rpm|mm|ml|°\s*c|grados?\s+celsius|v(?:oltios?)?|ohm(?:ios?)?))\b",
    re.IGNORECASE,
)
_PATRON_OBSERVACION_TECNICA = re.compile(
    r"\b(?:med[ií]|prob[ée]|revis[ée]|inspeccion[ée]|intercambi[ée]|"
    r"abr(?:e|ió)|llega|alcanza|retorn(?:a|ó)|fuga|presi[oó]n|voltaje|compresi[oó]n)\b",
    re.IGNORECASE,
)


def _es_evidencia_diagnostica_nueva(texto_cliente: str) -> bool:
    """Evita que una confirmación pendiente consuma datos técnicos nuevos o consultas."""
    texto_normalizado = _normalizar(texto_cliente).strip(" .,!¡¿?")
    if texto_normalizado in {"si", "no", "correcto", "negativo", "incorrecto", "incorrecta"}:
        return False
    from src.core.conversacion.orientacion_provisional import es_feedback_conversacional

    if es_feedback_conversacional(texto_cliente):
        return False

    # Solicitudes de inspección visual o declaración de falta de herramientas no son evidencia nueva
    if re.search(r"\bqu[eé]\s+(?:puedo|podemos|se\s+puede)\s+(?:revisar|hacer|ver)(?:\s+visualmente)?\b", texto_normalizado):
        return False
    if any(k in texto_normalizado for k in ("sin herramienta", "no tengo herramienta", "no puedo revisar", "aun no", "todavia no", "visualmente")):
        return False

    from src.core.conversacion.extractor_hechos import ExtractorHechos

    tiene_pregunta = bool(
        "?" in texto_cliente
        or "¿" in texto_cliente
        or re.search(
            r"\b(?:qu[eé]|c[oó]mo|cu[aá]l(?:es)?|por\s*qu[eé]|diferenci\w*|explic\w*|sospech\w*|otra\s+causa|otras\s+posibles\s+causas)\b",
            texto_normalizado,
        )
    )
    tiene_evidencia_hechos = ExtractorHechos.contiene_informacion_diagnostica(texto_cliente)
    tiene_dtc_o_medicion = bool(_PATRON_DTC_O_MEDICION.search(texto_cliente))
    tiene_observacion_tecnica = bool(
        len(texto_normalizado.split()) >= 3
        and _PATRON_OBSERVACION_TECNICA.search(texto_cliente)
    )
    tiene_condicion_operativa = bool(
        re.search(
            r"\b(?:pendiente|subida|plano|terreno|carga|aceler\w*|combustible|tanque|nivel|fuerza|potencia|tiron\w*|freno\w*|pedal|embrague|recalienta|humo)\b",
            texto_normalizado,
        )
    )
    return bool(
        tiene_pregunta
        or tiene_evidencia_hechos
        or tiene_dtc_o_medicion
        or tiene_observacion_tecnica
        or tiene_condicion_operativa
    )


def _registrar_turno_consumido_por_validacion(
    contexto_conversacion: dict[str, Any],
    texto_cliente: str,
    conversacion_id: str,
) -> None:
    """Registra el turno cuando validación responde sin pasar al orquestador."""
    from src.core.conversacion.extractor_hechos import ExtractorHechos
    from src.core.conversacion.models import ConversationState
    from src.core.conversacion.orientacion_provisional import es_sintoma_mecanico_valido

    serializado = (
        contexto_conversacion.get("conversation_state")
        or contexto_conversacion.get("estado_conversacion")
    )
    estado = (
        ConversationState.from_dict(serializado)
        if isinstance(serializado, dict)
        else ConversationState(session_id=conversacion_id)
    )
    ExtractorHechos.extraer_y_actualizar(estado, texto_cliente)
    estado.active_symptoms = [s for s in estado.active_symptoms if es_sintoma_mecanico_valido(s)]
    exportado = estado.exportar_dict()
    contexto_conversacion["conversation_state"] = exportado
    contexto_conversacion["estado_conversacion"] = exportado


def _nombre_hipotesis(hipotesis: Any) -> str:
    """Obtiene el texto persistible de una hipótesis sin serializar relaciones ORM."""
    if not hipotesis:
        return ""
    val = (
        getattr(hipotesis, "falla_probable", None)
        or getattr(hipotesis, "falla", None)
        or getattr(hipotesis, "nombre", None)
    )
    if isinstance(val, str) and not val.startswith("<MagicMock"):
        return val
    if isinstance(hipotesis, dict):
        f = hipotesis.get("falla_probable") or hipotesis.get("falla") or hipotesis.get("nombre")
        if isinstance(f, str) and not f.startswith("<MagicMock"):
            return f
    return ""


def _procedimiento_seguro_fallback(falla: str) -> str:
    """Fallback determinista y seguro si no existe procedimiento RAG registrado."""
    falla_lower = falla.lower()
    if any(k in falla_lower for k in ("freno", "cilindro maestro", "pedal", "caliper", "cáliper", "pastilla", "disco")):
        return (
            "Con el vehículo detenido y motor apagado, realiza una inspección visual externa del depósito translúcido "
            "de líquido de frenos verificando que el nivel esté entre MIN y MAX (sin abrir la tapa para evitar contaminación), "
            "y revisa si hay goteos visibles en el piso o cara interna de ruedas. No realices purgas ni desarmes sin equipo adecuado."
        )
    if any(k in falla_lower for k in ("refrigera", "temperatura", "recalienta", "radiador", "termostato")):
        return (
            "Con el motor totalmente frío y apagado, realiza una inspección visual del depósito de refrigerante verificando "
            "que el nivel esté entre MIN y MAX, y comprueba si hay marcas de goteo en mangueras externas o radiador."
        )
    if any(k in falla_lower for k in ("bateria", "batería", "alternador", "arranque", "encendido")):
        return (
            "Con el motor apagado y sin llave en contacto, inspecciona visualmente el estado de los bornes y cables de batería "
            "en busca de sulfatación o terminales flojos, así como el estado externo de la correa de accesorios."
        )
    return (
        "Con el vehículo apagado y estacionado con freno de mano, efectúa una inspección visual directa del componente y conectores "
        "accesibles a simple vista en busca de fisuras, desconexiones o manchas visibles de fluidos."
    )


def _respuesta_detalle_hipotesis(hipotesis: Any, orden: int) -> str:
    """Devuelve una guía verificable para una selección Top-3, sin confirmarla aún."""

    falla = _nombre_hipotesis(hipotesis) or "Hipótesis técnica bajo revisión"
    prueba = str(getattr(hipotesis, "prueba_recomendada", None) or "").strip()
    if not prueba or any(k in prueba.lower() for k in ("sin procedimiento", "no registrado", "n/a", "none")):
        prueba = _procedimiento_seguro_fallback(falla)

    respuesta = (
        f"🔎 Seleccionaste la hipótesis *{orden}*: *{falla}*.\n\n"
        "Aún no la registraré como confirmada hasta contar con una verificación física.\n\n"
        f"🔧 *Primero verifica:* {prueba}\n\n"
        "Cuando realices la comprobación, responde *SÍ* si coincide con la hipótesis, o describe qué observaste al revisar (o si aún no has podido revisar)."
    )
    return respuesta


def _solicita_continuar_sin_confirmacion(texto: str) -> bool:
    """Detecta que el mecánico aún no aporta evidencia física y quiere seguir sin datos adicionales."""
    if _es_evidencia_diagnostica_nueva(texto):
        return False
    normalizado = _normalizar(texto)
    patrones = (
        r"\bquiero\s+(?:seguir|continuar)\b",
        r"\b(?:sigamos|continuemos|sigue|continua)\b",
        r"\bno\s+(?:he\s+)?(?:verificado|confirmado|comprobado|revisado|inspeccionado|hecho|realizado)\b",
        r"\b(?:aun|todavia)\s+no\s+(?:lo\s+|la\s+)?(?:he\s+)?(?:revisado|hecho|comprobado|verificado|inspeccionado)\b",
        r"\bno\s+(?:puedo|podemos)\b",
        r"\bno\s+(?:tengo|cuento\s+con|dispongo\s+de)\s+(?:herramientas?|reloj|elevador|manometro|scanner|escaner)\b",
        r"\bsin\s+(?:herramientas?|elevador|reloj|manometro|desmontar)\b",
        r"^no\s+se(?:\s+(?:todavia|aun))?$",
        r"\bnecesito\s+otra\s+(?:prueba|comprobacion)\b",
        r"\botra\s+forma\s+de\s+(?:revisar|comprobar|verificar)\b",
        r"\bqu[eé]\s+(?:puedo|podemos|se\s+puede)\s+(?:revisar|hacer|ver)(?:\s+visualmente)?\b",
        r"\b(?:revisar|verificar|inspeccionar)\s+visualmente\b",
    )
    return any(re.search(patron, normalizado) for patron in patrones)


def _respuesta_para_continuar_diagnostico(
    texto: str,
    estado: Any = None,
    falla_principal: str | None = None,
) -> str:
    """Mantiene la hipótesis pendiente y propone una guía de inspección visual segura y contextual."""
    from src.core.conversacion.orientacion_provisional import obtener_orientacion_visual_segura

    guias_visuales = obtener_orientacion_visual_segura(estado, falla=falla_principal)
    encabezado = (
        "Entendido. La hipótesis queda pendiente de forma provisional: no registraré una "
        "confirmación ni un descarte sin evidencia física directa.\n\n"
        "👁️ *Alternativa de inspección visual segura (sin herramientas ni elevador, sin desmontar la rueda):*\n"
    )
    cuerpo = "\n\n".join(guias_visuales)
    pie = "\n\nPodemos continuar el diagnóstico. Indica qué observas a simple vista o describe otro síntoma."
    return encabezado + cuerpo + pie


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

            falla_seleccionada = _nombre_hipotesis(hipotesis) or None

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
        interactivo: Optional[dict] = None,
    ) -> None:
        """Persiste una respuesta del flujo de validación en el outbox durable."""
        out_msg_id = f"out_{meta_message_id or uuid.uuid4()}"
        if interactivo and getattr(settings, "whatsapp_interactive_buttons_enabled", False) and conversacion and hasattr(conversacion, "contexto"):
            ctx = dict(conversacion.contexto or {})
            ctx["mensaje_interactivo"] = {
                "msg_id": out_msg_id,
                "interactivo": interactivo,
            }
            conversacion.contexto = ctx
        elif conversacion and hasattr(conversacion, "contexto"):
            ctx = dict(conversacion.contexto or {})
            ctx.pop("mensaje_interactivo", None)
            conversacion.contexto = ctx

        await msg_repo.crear_mensaje(
            conversacion_id=conversacion.id,
            taller_id=usuario.taller_id,
            usuario_id=usuario.id,
            meta_message_id=out_msg_id,
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
        payload_interactivo: Optional[str] = None,
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

        btn_accion_interactiva = None
        if payload_interactivo:
            p_lower = payload_interactivo.lower()
            if p_lower.startswith("conf_si") or p_lower in ("btn_si", "si"):
                btn_accion_interactiva = "si"
            elif p_lower.startswith("conf_no") or p_lower in ("btn_no", "no"):
                btn_accion_interactiva = "no"
            elif "hip_" in p_lower:
                m_ord = re.search(r"hip[_\-]?([1-9])", p_lower)
                if m_ord:
                    btn_accion_interactiva = SeleccionHipotesisTop3(
                        accion="CONFIRMAR",
                        orden=int(m_ord.group(1)),
                        metodo="boton_interactivo",
                        texto_referencia=texto_cliente,
                    )

        # Una consulta de memoria es de solo lectura. Debe prevalecer sobre la
        # validación pendiente y sobre cualquier fallback por imposibilidad.
        if tipo_mensaje == "text" and ExtractorHechos.es_consulta_memoria(texto_cliente):
            from src.core.conversacion.models import ConversationState
            from src.core.conversacion.resumen_memoria import generar_resumen_memoria

            raw_estado = contexto_conversacion.get("conversation_state") or {}
            estado_memoria = (
                ConversationState.from_dict(raw_estado)
                if isinstance(raw_estado, dict)
                else ConversationState(session_id=str(conversacion.id))
            )
            respuesta_texto = generar_resumen_memoria(estado_memoria)
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
                "status": "consulta_memoria",
                "conversacion_id": str(conversacion.id),
                "respuesta": respuesta_texto,
                "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
            }

        # Un Sí/No a una medición del hallazgo mostrado no valida el Top-1
        # original guardado en BD, aunque hubiera un contexto viejo de validación.
        estado_hilo = contexto_conversacion.get("conversation_state") or {}
        preguntas_hilo = estado_hilo.get("preguntas_realizadas") or []
        hallazgo_mostrado = (estado_hilo.get("hechos") or {}).get("hipotesis_en_evaluacion")
        if (
            tipo_mensaje == "text"
            and texto_cliente.strip().casefold() in {"si", "sí", "no", "correcto", "negativo"}
            and hallazgo_mostrado
            and preguntas_hilo
            and preguntas_hilo[-1].get("intent") != "CONFIRMACION_ALTERNATIVA"
        ):
            contexto_conversacion.pop("validacion_diagnostico", None)
            conversacion.contexto = contexto_conversacion
            return None

        # Si el mecánico indica que es otro carro o nuevo diagnóstico, liberar validación anterior
        if tipo_mensaje == "text" and ExtractorHechos.es_reinicio_solicitado(texto_cliente):
            contexto_conversacion.pop("validacion_diagnostico", None)
            conversacion.contexto = contexto_conversacion
            await session.commit()
            return None

        # Una medición, DTC, pregunta técnica o resultado de prueba posterior debe volver al
        # orquestador.
        if (
            tipo_mensaje == "text"
            and etapa_validacion in {"esperando_confirmacion", "esperando_aclaracion_confirmacion"}
            and _es_evidencia_diagnostica_nueva(texto_cliente)
        ):
            contexto_conversacion.pop("validacion_diagnostico", None)
            conversacion.contexto = contexto_conversacion
            logger.info("[Validación] Nueva evidencia técnica o consulta; se reanuda el flujo diagnóstico con el orquestador.")
            return None

        if tipo_mensaje in ("text", "interactive", "button") and etapa_validacion:
            _registrar_turno_consumido_por_validacion(
                contexto_conversacion, texto_cliente, str(conversacion.id)
            )
            conversacion.contexto = contexto_conversacion

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

        from src.core.conversacion.orientacion_provisional import (
            es_feedback_conversacional,
            es_imposibilidad_comprobacion_fisica,
            es_sin_mas_sintomas,
            generar_orientacion_provisional,
        )

        es_imposible_declarado = bool(
            es_imposibilidad_comprobacion_fisica(texto_cliente)
            or es_sin_mas_sintomas(texto_cliente)
        )

        if (
            tipo_mensaje == "text"
            and etapa_validacion in {"esperando_confirmacion", "esperando_aclaracion_confirmacion"}
            and (es_imposible_declarado or _solicita_continuar_sin_confirmacion(texto_cliente))
        ):
            contexto_conversacion.pop("validacion_diagnostico", None)
            conversacion.contexto = contexto_conversacion

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
                for h in sorted(
                    list(getattr(diagnostico_selector, "hipotesis", None) or []),
                    key=lambda x: getattr(x, "orden", 999),
                )[:3]:
                    nombre_h = _nombre_hipotesis(h)
                    if nombre_h:
                        hipotesis_selector.append({"falla": nombre_h})

            from src.core.conversacion.models import ConversationState

            raw_estado = (
                contexto_conversacion.get("conversation_state")
                or contexto_conversacion.get("estado_conversacion")
            )
            estado_obj = (
                ConversationState.from_dict(raw_estado)
                if raw_estado and isinstance(raw_estado, dict)
                else ConversationState(session_id=str(conversacion.id))
            )
            from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad

            hipotesis_selector, exclusiones = (
                ValidadorCompatibilidad.filtrar_hipotesis_almacenadas(
                    hipotesis_selector, estado_obj
                )
            )
            if exclusiones:
                contexto_conversacion["exclusiones_compatibilidad_orientacion"] = exclusiones
                conversacion.contexto = contexto_conversacion

            es_inspeccion_o_sin_herramientas = bool(
                not es_sin_mas_sintomas(texto_cliente)
                and "no puedo realizar comprobaciones" not in _normalizar(texto_cliente)
                and (
                    ("desmont" in _normalizar(texto_cliente) and "rueda" in _normalizar(texto_cliente))
                    or any(k in _normalizar(texto_cliente) for k in ("herramienta", "elevador", "aun no", "todavia no", "sin desmon", "sin reloj", "sin manometro", "visual"))
                    or _solicita_continuar_sin_confirmacion(texto_cliente)
                )
            )

            falla_princ = hipotesis_selector[0]["falla"] if hipotesis_selector else (
                diagnostico_selector.falla_predicha if diagnostico_selector else None
            )

            if es_inspeccion_o_sin_herramientas:
                respuesta_texto = _respuesta_para_continuar_diagnostico(
                    texto_cliente,
                    estado=estado_obj,
                    falla_principal=falla_princ,
                )
                status_salida = "continuar_diagnostico"
            else:
                respuesta_texto = generar_orientacion_provisional(
                    estado=estado_obj,
                    hipotesis_disponibles=hipotesis_selector,
                    falla_principal=falla_princ,
                )
                status_salida = "orientacion_provisional"

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
                "status": status_salida,
                "diagnostico_id": str(diagnostico_contexto_id) if diagnostico_contexto_id else None,
                "conversacion_id": str(conversacion.id),
                "respuesta": respuesta_texto,
                "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
            }

        if tipo_mensaje in ("text", "interactive", "button") and etapa_validacion in {
            "esperando_confirmacion",
            "esperando_aclaracion_confirmacion",
        }:

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
                for h in sorted(
                    list(getattr(diagnostico_selector, "hipotesis", None) or []),
                    key=lambda x: getattr(x, "orden", 999),
                )[:3]:
                    nombre_h = _nombre_hipotesis(h)
                    if nombre_h:
                        hipotesis_selector.append({"falla": nombre_h})

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

            if isinstance(btn_accion_interactiva, SeleccionHipotesisTop3):
                seleccion_top3 = btn_accion_interactiva
            else:
                seleccion_top3 = (
                    interpretar_seleccion_top3(
                        texto_cliente,
                        hipotesis_selector,
                    )
                    if hipotesis_selector
                    else None
                )

            if seleccion_top3 and seleccion_top3.accion in ("AMBIGUO", "NO_SE", "NINGUNA"):
                if seleccion_top3.accion == "NO_SE":
                    respuesta_texto = (
                        "Entendido, no te preocupes. Conservo las hipótesis bajo revisión técnica "
                        "sin confirmar ni descartar.\n\n"
                        "Para continuar orientándote: ¿qué síntoma o comportamiento adicional observas en el vehículo?"
                    )
                elif seleccion_top3.accion == "NINGUNA":
                    respuesta_texto = (
                        "Entendido. Ninguna de las opciones corresponde a lo observado.\n\n"
                        "Conservo el diagnóstico en revisión abierta. Por favor, indícame qué componente sospechas "
                        "o qué síntoma específico presenta para reorientar el análisis."
                    )
                else:
                    respuesta_texto = (
                        "🤔 No registraré una confirmación ni un descarte con esa respuesta.\n"
                        "Si quieres continuar, describe una observación o una comprobación "
                        "que sí puedas realizar de forma segura."
                    )
                flujo_validacion["etapa"] = "esperando_aclaracion_confirmacion"
                contexto_conversacion["validacion_diagnostico"] = flujo_validacion
                conversacion.contexto = contexto_conversacion
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
                    "status": "esperando_aclaracion_confirmacion",
                    "diagnostico_id": str(diagnostico_selector.id) if diagnostico_selector else None,
                    "conversacion_id": str(conversacion.id),
                    "respuesta": respuesta_texto,
                    "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                }

            if seleccion_top3 and seleccion_top3.accion == "CONFIRMAR":
                orden_previo = flujo_validacion.get("orden_seleccionado")
                hipotesis_elegida = next(
                    (
                        h for h in (getattr(diagnostico_selector, "hipotesis", None) or [])
                        if getattr(h, "orden", None) == seleccion_top3.orden
                    ),
                    None,
                )

                if orden_previo and orden_previo == seleccion_top3.orden:
                    falla_nombre = _nombre_hipotesis(hipotesis_elegida) or f"Opción {seleccion_top3.orden}"
                    prueba = str(getattr(hipotesis_elegida, "prueba_recomendada", None) or "").strip()
                    if not prueba or any(k in prueba.lower() for k in ("sin procedimiento", "no registrado", "n/a", "none")):
                        prueba = _procedimiento_seguro_fallback(falla_nombre)
                    respuesta_texto = (
                        f"Ya tienes seleccionada la hipótesis *{seleccion_top3.orden}*: *{falla_nombre}*.\n\n"
                        f"🔧 *Comprobación técnica pendiente:* {prueba}\n\n"
                        "¿Pudiste realizarla? Responde *SÍ* si confirmaste la avería o describe qué observaste al revisar."
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
                        "status": "recordatorio_comprobacion_pendiente",
                        "diagnostico_id": str(diagnostico_selector.id),
                        "conversacion_id": str(conversacion.id),
                        "respuesta": respuesta_texto,
                        "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                    }

                respuesta_texto = _respuesta_detalle_hipotesis(
                    hipotesis_elegida,
                    seleccion_top3.orden or 1,
                )
                flujo_validacion["orden_seleccionado"] = seleccion_top3.orden
                flujo_validacion["hipotesis_seleccionada"] = _nombre_hipotesis(hipotesis_elegida)
                flujo_validacion["etapa"] = "esperando_confirmacion"
                flujo_validacion["diagnostico_id"] = str(diagnostico_selector.id)
                contexto_conversacion["validacion_diagnostico"] = flujo_validacion
                conversacion.contexto = contexto_conversacion

                interactivo_conf = None
                if getattr(settings, "whatsapp_interactive_buttons_enabled", False):
                    from src.application.services.confirmacion_diagnostico import (
                        construir_botones_confirmacion,
                    )
                    interactivo_conf = construir_botones_confirmacion(diagnostico_selector.id)

                await cls.guardar_respuesta_validacion_outbox(
                    msg_repo,
                    conversacion,
                    usuario,
                    meta_message_id,
                    respuesta_texto,
                    proveedor,
                    remitente,
                    interactivo=interactivo_conf,
                )
                await session.commit()
                return {
                    "status": "esperando_confirmacion",
                    "diagnostico_id": str(diagnostico_selector.id),
                    "conversacion_id": str(conversacion.id),
                    "respuesta": respuesta_texto,
                    "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                }

            elif seleccion_top3 and seleccion_top3.accion == "DESCARTAR":
                orden_hipotesis_seleccionada = seleccion_top3.orden
                metodo_seleccion = seleccion_top3.metodo
                respuesta_binaria = "no"

            elif (
                seleccion_top3
                and seleccion_top3.accion == "DESCARTAR_Y_CONFIRMAR"
            ):
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
                if btn_accion_interactiva in ("si", "no"):
                    respuesta_binaria = btn_accion_interactiva
                else:
                    respuesta_binaria = interpretar_respuesta_validacion_whatsapp(
                        texto_cliente
                    )

            if (
                confirmacion is None
                and respuesta_binaria is None
                and etapa_validacion == "esperando_aclaracion_confirmacion"
            ):
                confirmacion = interpretar_confirmacion_whatsapp(texto_cliente)
                if confirmacion is None:
                    respuesta_texto = (
                        "🤔 No registraré una confirmación ni un descarte con ese texto.\n"
                        "Si quieres continuar, describe una observación o una comprobación "
                        "que sí puedas realizar de forma segura."
                    )
                    contexto_conversacion["validacion_diagnostico"] = flujo_validacion
                    conversacion.contexto = contexto_conversacion
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
                        "status": "esperando_aclaracion_confirmacion",
                        "diagnostico_id": (
                            str(diagnostico_selector.id) if diagnostico_selector else None
                        ),
                        "conversacion_id": str(conversacion.id),
                        "respuesta": respuesta_texto,
                        "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                    }

            traz_sel = getattr(diagnostico_selector, "trazabilidad", None) or {}
            conclusion_sel = str(getattr(diagnostico_selector, "conclusion_mecanico", "") or "").lower()
            falla_sel = str(getattr(diagnostico_selector, "falla_predicha", "") or "").lower()
            es_orientacion_previa = bool(
                traz_sel.get("orientacion_provisional")
                or "orientación provisional" in conclusion_sel
                or "orientacion provisional" in conclusion_sel
                or "sin confirmar" in conclusion_sel
                or "revisión presencial" in conclusion_sel
                or "revision presencial" in conclusion_sel
                or "orientación provisional" in falla_sel
            )

            if confirmacion is None and (es_orientacion_previa or es_feedback_conversacional(texto_cliente)):
                respuesta_texto = (
                    "Entendido. Tomo tu respuesta como retroalimentación sobre la orientación recibida.\n\n"
                    "El diagnóstico se mantiene en revisión y sin confirmación física hasta contar con "
                    "una inspección presencial en taller especializado."
                )
                contexto_conversacion.pop("validacion_diagnostico", None)
                conversacion.contexto = contexto_conversacion
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
                    "status": "feedback_registrado",
                    "diagnostico_id": str(diagnostico_selector.id) if diagnostico_selector else None,
                    "conversacion_id": str(conversacion.id),
                    "respuesta": respuesta_texto,
                    "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                }

            if confirmacion is None and respuesta_binaria == "si":
                confirmacion = ConfirmacionDiagnosticoWhatsApp(
                    estado="confirmado"
                )
                orden_hipotesis_seleccionada = flujo_validacion.get("orden_seleccionado") or 1
                metodo_seleccion = "binario"

            elif confirmacion is None and respuesta_binaria == "no":
                from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad

                texto_adicional = re.sub(
                    r"^(?:no|negativo|descartado|falso|no es|no fue|descartar)\b[,\s.:;-]*",
                    "",
                    texto_cliente,
                    flags=re.IGNORECASE,
                ).strip()
                tiene_observacion_tecnica = bool(
                    _PATRON_OBSERVACION_TECNICA.search(texto_cliente)
                    or _PATRON_DTC_O_MEDICION.search(texto_cliente)
                    or (len(texto_adicional.split()) >= 3 and not ValidadorCompatibilidad.es_evidencia_espuria(texto_adicional))
                )

                if not tiene_observacion_tecnica and btn_accion_interactiva != "no":
                    falla_nombre = flujo_validacion.get("hipotesis_seleccionada")
                    if not falla_nombre and orden_hipotesis_seleccionada and diagnostico_selector and getattr(diagnostico_selector, "hipotesis", None):
                        for h in getattr(diagnostico_selector, "hipotesis", []):
                            if getattr(h, "orden", None) == orden_hipotesis_seleccionada:
                                nom = _nombre_hipotesis(h)
                                if nom and not nom.startswith("<MagicMock"):
                                    falla_nombre = nom
                                break
                    prefijo_hip = f"la hipótesis *{falla_nombre}*" if (falla_nombre and not falla_nombre.startswith("<MagicMock")) else "la hipótesis"
                    respuesta_texto = (
                        f"Entendido. Mantengo {prefijo_hip} abierta de forma provisional: "
                        "no registrará una confirmación ni un descarte sin evidencia física directa, "
                        "ya que un 'NO' sin comprobación física directa no descarta la falla por sí solo.\n\n"
                        "¿Qué observaste al revisar? (O si todavía no pudiste realizar la prueba o no cuentas con herramientas, "
                        "indícalo para orientarte de forma segura)."
                    )
                    flujo_validacion["etapa"] = "esperando_aclaracion_confirmacion"
                    contexto_conversacion["validacion_diagnostico"] = flujo_validacion
                    conversacion.contexto = contexto_conversacion
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
                        "status": "esperando_aclaracion_confirmacion",
                        "diagnostico_id": str(diagnostico_selector.id) if diagnostico_selector else None,
                        "conversacion_id": str(conversacion.id),
                        "respuesta": respuesta_texto,
                        "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                    }

                orden_hipotesis_seleccionada = flujo_validacion.get("orden_seleccionado") or orden_hipotesis_seleccionada or 1
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
                            falla_descartada = _nombre_hipotesis(h) or falla_descartada
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

                if len(texto_adicional.split()) >= 3 and not ValidadorCompatibilidad.es_evidencia_espuria(texto_adicional):
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

                from src.core.conversacion.generador_preguntas import GeneradorPreguntas

                pregunta_disc, intent_disc = GeneradorPreguntas.formular_pregunta_discriminante_post_descarte(
                    estado=estado_obj,
                    falla_descartada=falla_descartada,
                )

                estado_obj.registrar_respuesta(texto_cliente, interpretacion=f"Descarte de hipótesis: {falla_descartada}")
                estado_obj.registrar_pregunta(
                    intent=intent_disc,
                    texto=pregunta_disc,
                    incrementar_repregunta=False,
                )

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

                from src.core.conversacion.orientacion_provisional import es_sintoma_mecanico_valido
                if diagnostico and diagnostico.sintoma_original and es_sintoma_mecanico_valido(diagnostico.sintoma_original) and diagnostico.sintoma_original not in estado_obj.active_symptoms:
                    estado_obj.active_symptoms.append(diagnostico.sintoma_original)
                estado_obj.active_symptoms = [s for s in estado_obj.active_symptoms if es_sintoma_mecanico_valido(s)]

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
                interactivo_siguiente = None
                hipotesis_restantes = [
                    h for h in (getattr(diagnostico, "hipotesis", None) or [])
                    if getattr(h, "resultado", None) not in ("descartada", "confirmada")
                ]
                if hipotesis_restantes and diagnostico and getattr(settings, "whatsapp_interactive_buttons_enabled", False):
                    from src.application.services.confirmacion_diagnostico import construir_botones_hipotesis
                    preds_restantes = [
                        {"falla": _nombre_hipotesis(h), "probabilidad": float(getattr(h, "confianza", 0.0) or 0.0)}
                        for h in hipotesis_restantes
                    ]
                    interactivo_siguiente = construir_botones_hipotesis(preds_restantes, case_id=str(diagnostico.id))

                await cls.guardar_respuesta_validacion_outbox(
                    msg_repo, conversacion, usuario, meta_message_id, respuesta_texto, proveedor, remitente, interactivo=interactivo_siguiente
                )
                await session.commit()
                return {
                    "status": "esperando_falla_real",
                    "diagnostico_id": str(diagnostico.id) if diagnostico else None,
                    "conversacion_id": str(conversacion.id),
                    "respuesta": respuesta_texto,
                    "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                }
        elif etapa_validacion == "esperando_falla_real":
            diag_sel = (
                await diag_repo.obtener_pendiente_mecanico_por_id(
                    diagnostico_id=diagnostico_contexto_id,
                    taller_id=usuario.taller_id,
                    mecanico_id=usuario.id,
                )
                if diagnostico_contexto_id
                else None
            )
            sel_texto = interpretar_seleccion_top3(texto_cliente, getattr(diag_sel, "hipotesis", None))
            seleccion_opcion = (
                btn_accion_interactiva
                if isinstance(btn_accion_interactiva, SeleccionHipotesisTop3)
                else sel_texto
            )
            if seleccion_opcion and seleccion_opcion.accion == "CONFIRMAR":
                if diag_sel:
                    hip_elegida = next(
                        (h for h in (getattr(diag_sel, "hipotesis", None) or []) if getattr(h, "orden", None) == seleccion_opcion.orden),
                        None
                    )
                    if hip_elegida:
                        resp_t = _respuesta_detalle_hipotesis(hip_elegida, seleccion_opcion.orden or 1)
                        flujo_validacion["orden_seleccionado"] = seleccion_opcion.orden
                        flujo_validacion["hipotesis_seleccionada"] = _nombre_hipotesis(hip_elegida)
                        flujo_validacion["etapa"] = "esperando_confirmacion"
                        flujo_validacion["diagnostico_id"] = str(diag_sel.id)
                        contexto_conversacion["validacion_diagnostico"] = flujo_validacion
                        conversacion.contexto = contexto_conversacion

                        inter_c = None
                        if getattr(settings, "whatsapp_interactive_buttons_enabled", False):
                            from src.application.services.confirmacion_diagnostico import (
                                construir_botones_confirmacion,
                            )
                            inter_c = construir_botones_confirmacion(diag_sel.id)
                        await cls.guardar_respuesta_validacion_outbox(
                            msg_repo, conversacion, usuario, meta_message_id, resp_t, proveedor, remitente, interactivo=inter_c
                        )
                        await session.commit()
                        return {
                            "status": "esperando_confirmacion",
                            "diagnostico_id": str(diag_sel.id),
                            "conversacion_id": str(conversacion.id),
                            "respuesta": resp_t,
                            "tiempo_total_ms": round((time.perf_counter() - t_inicio) * 1000, 2),
                        }

            falla_real = texto_cliente.strip()[:4000]
            texto_norm = _normalizar(falla_real)

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

            if not es_confirmacion_fisica_concreta and len(falla_real.split()) >= 2:
                from src.core.conversacion.extractor_hechos import ExtractorHechos
                from src.core.conversacion.models import ConversationState

                raw_st = contexto_conversacion.get("conversation_state") or contexto_conversacion.get("estado_conversacion")
                if raw_st and isinstance(raw_st, dict):
                    estado_obj = ConversationState.from_dict(raw_st)
                    ExtractorHechos.extraer_y_actualizar(estado_obj, falla_real)
                    from src.core.conversacion.orientacion_provisional import es_sintoma_mecanico_valido
                    estado_obj.active_symptoms = [s for s in estado_obj.active_symptoms if es_sintoma_mecanico_valido(s)]
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
