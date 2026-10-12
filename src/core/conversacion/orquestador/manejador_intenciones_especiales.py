"""Manejador de intenciones conversacionales especiales (saludos, cierres, casos, descartes y especificaciones)."""

from __future__ import annotations

import re
import time
import uuid
from typing import Any, Dict, Optional

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.formateador_compacto import FormateadorCompacto
from src.core.conversacion.models import ConversationPhase, ConversationState
from src.core.conversacion.repositorio import ConversationStateRepository
from src.core.diagnostico.politica_seguridad import PoliticaSeguridad


class ManejadorIntencionesEspeciales:
    """Detecta y responde a intenciones conversacionales que no requieren diagnóstico estándar completo."""

    PATRON_CIERRE = re.compile(
        r"^\s*(?:(?:muchas\s+)?gracias(?:\s+maestro|\s+amigo)?(?:\s+por\s+.*)?|"
        r"perfecto,?\s*(?:qued[oó]\s+clar[ií]simo|gracias.*)?|"
        r"excelente\s+(?:servicio|explicaci[oó]n|ayuda)(?:\s+maestro)?|"
        r"qued[oó]\s+clar[ií]simo)\s*[!.]*\s*$",
        re.IGNORECASE,
    )

    COMPONENTES_CONSULTA = (
        ("electroventilador", "Falla en el electroventilador"),
        ("motoventilador", "Falla en el electroventilador"),
        ("ventilador", "Falla en el electroventilador"),
        ("termostato", "Falla en el termostato"),
        ("radiador", "Falla en el radiador"),
        ("bomba de agua", "Falla en la bomba de agua"),
        ("inyector", "Falla en inyectores de combustible"),
        ("bobina", "Falla en bobina de encendido"),
        ("bujia", "Falla en bujías"),
        ("bomba de combustible", "Falla en bomba de combustible"),
        ("bomba de gasolina", "Falla en bomba de combustible"),
        ("regulador", "Falla en regulador de presion de combustible o diafragma roto"),
        ("sensor ect", "Falla en sensor ECT de temperatura"),
        ("sensor de temperatura", "Falla en sensor ECT de temperatura"),
        ("embrague", "Desgaste del embrague"),
        ("frenos", "Desgaste en pastillas o discos de freno"),
    )

    @classmethod
    async def procesar_intencion_especial(
        cls,
        estado: ConversationState,
        texto_limpio: str,
        session_id: str,
        gestor_diagnostico: Any,
        repositorio: ConversationStateRepository,
        t0: float,
    ) -> Optional[Dict[str, Any]]:
        """Evalúa si el turno corresponde a una intención especial. Si es así, retorna la respuesta completa."""
        # 1. Solicitud de reanudar / nuevo caso / cancelar
        solicitud_caso = ExtractorHechos.clasificar_solicitud_caso(texto_limpio)
        if solicitud_caso and solicitud_caso.get("accion") == "reanudar":
            case_id_objetivo = solicitud_caso.get("case_id")
            if not case_id_objetivo and solicitud_caso.get("caso_anterior"):
                case_id_objetivo = next(
                    (
                        caso.get("case_id")
                        for caso in reversed(estado.hechos_historicos)
                        if caso.get("case_id") and caso.get("case_id") != estado.case_id
                    ),
                    None,
                )
            if case_id_objetivo and estado.restaurar_caso_archivado(str(case_id_objetivo)):
                await repositorio.save_session(session_id, estado)
                session_manager = getattr(gestor_diagnostico, "session_manager", None)
                if session_manager is not None:
                    session_manager.cargar_contexto(
                        session_id,
                        {"case_id": estado.case_id, "conversation_state": estado.exportar_dict()},
                    )
                return {
                    "status": "caso_reanudado",
                    "respuesta_texto": (
                        "Retomé exclusivamente el caso anterior solicitado. Su contexto queda aislado "
                        "del caso que acabamos de cerrar."
                    ),
                    "diagnostico_ml": "Caso anterior reanudado",
                    "confianza_ml": estado.confianza_actual,
                    "fase": estado.fase.value,
                    "es_pregunta": False,
                    "decision": "REANUDAR_CASO",
                    "case_id": estado.case_id,
                    "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                    "estado": estado,
                }
            return {
                "status": "reanudar_no_encontrado",
                "respuesta_texto": (
                    "No encontré ese caso en el historial de esta conversación. Indica el case_id "
                    "o solicita retomar el caso anterior disponible. No cambié el caso activo."
                ),
                "diagnostico_ml": "Caso histórico no encontrado",
                "confianza_ml": 0.0,
                "fase": estado.fase.value,
                "es_pregunta": True,
                "decision": "ACLARAR_REANUDACION",
                "case_id": estado.case_id,
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
            }

        if (
            solicitud_caso
            and solicitud_caso.get("accion") in ("nuevo_caso", "cancelar")
            and not ExtractorHechos.contiene_informacion_diagnostica(texto_limpio)
        ):
            es_cancelacion = solicitud_caso["accion"] == "cancelar"
            preservar_vehiculo = bool(
                solicitud_caso.get("preservar_vehiculo")
                and any((estado.placa, estado.marca, estado.modelo))
            )
            estado.iniciar_nuevo_caso(
                None if es_cancelacion else str(uuid.uuid4()),
                preservar_vehiculo=preservar_vehiculo,
            )
            if es_cancelacion:
                estado.case_id = None
                estado.active_problem_id = None
            await repositorio.save_session(session_id, estado)
            session_manager = getattr(gestor_diagnostico, "session_manager", None)
            if session_manager is not None:
                session_manager.cargar_contexto(
                    session_id,
                    {"case_id": estado.case_id, "conversation_state": estado.exportar_dict()},
                )
            if es_cancelacion:
                resp_reinicio = (
                    "🚗 *Caso cancelado.* Conservé su historial y limpié el contexto activo. "
                    "Cuando quieras, envía la placa del siguiente vehículo."
                )
            else:
                resp_reinicio = (
                    "🚗 *Caso anterior cerrado.* Conservé su historial y limpié la memoria activa. "
                    "Envía la placa y el síntoma para iniciar un caso nuevo."
                )
                if preservar_vehiculo and estado.placa:
                    resp_reinicio = (
                        "🚗 *Caso anterior cerrado.* Conservé el historial y mantengo únicamente "
                        "los datos confirmados del mismo vehículo. Indica el nuevo síntoma."
                    )
            return {
                "status": "reinicio",
                "respuesta_texto": resp_reinicio,
                "diagnostico_ml": "Reinicio de sesión",
                "confianza_ml": 1.0,
                "fase": ConversationPhase.INICIO.value,
                "es_pregunta": False,
                "decision": "REINICIO",
                "case_id": estado.case_id,
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
            }

        # 2. Cierre / Agradecimiento
        if cls.PATRON_CIERRE.match(texto_limpio.strip()):
            if any(w in texto_limpio.lower() for w in ("embalamiento", "seguridad", "riesgo", "peligro", "diesel", "diésel", "cárter", "carter")):
                resp_cierre = (
                    "🤝 *¡De nada maestro! Recuerda mantener el motor detenido y drenar completamente el cárter contaminado "
                    "antes de cualquier intento de arranque para evitar el peligro crítico de embalamiento diésel. "
                    "Quedo a tu disposición en el taller para cualquier otra consulta técnica o nuevo caso vehicular. ¡Muchos éxitos!*"
                )
            else:
                resp_cierre = (
                    "🤝 *¡De nada maestro! Quedo a tu disposición en el taller para cualquier otra consulta técnica, "
                    "medición o nuevo caso vehicular. ¡Muchos éxitos en la reparación!*"
                )
            return {
                "status": "cierre",
                "respuesta_texto": resp_cierre,
                "diagnostico_ml": estado.falla_principal or "Caso concluido",
                "confianza_ml": estado.confianza_actual or 1.0,
                "fase": estado.fase.value,
                "es_pregunta": False,
                "decision": "CIERRE",
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
            }

        # 3. Saludos
        if ExtractorHechos.es_saludo(texto_limpio):
            tiene_caso_activo = bool(
                estado.placa
                or estado.hechos
                or estado.active_symptoms
                or estado.completed_tests
                or (estado.fase != ConversationPhase.INICIO and estado.fase != ConversationPhase.RESULTADO)
            )
            if not tiene_caso_activo:
                if estado.fase == ConversationPhase.RESULTADO or not estado.hechos:
                    estado.iniciar_nuevo_caso()
                resp_saludo = (
                    "👋 *¡Hola! Soy CarBot, chatbot de diagnóstico vehicular con Inteligencia Artificial.*\n\n"
                    "¿En qué te puedo ayudar hoy o qué falla presenta el auto? Para empezar, cuéntame el problema o síntomas que notas."
                )
                return {
                    "status": "saludo", "respuesta_texto": resp_saludo, "diagnostico_ml": "Saludo / Bienvenida",
                    "confianza_ml": 1.0, "fase": ConversationPhase.INICIO.value, "es_pregunta": False, "decision": "SALUDO",
                    "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2), "estado": estado,
                }
            else:
                placa_txt = f" del vehículo con placa *{estado.placa}*" if estado.placa else ""
                resp_saludo = (
                    f"👋 *¡Hola! Continuamos con el diagnóstico activo{placa_txt}.*\n\n"
                    "Cuéntame si tienes más síntomas que agregar o responde a la última indicación para continuar."
                )
                return {
                    "status": "saludo_caso_activo", "respuesta_texto": resp_saludo,
                    "diagnostico_ml": "Saludo en caso activo",
                    "confianza_ml": estado.confianza_actual or 1.0, "fase": estado.fase.value,
                    "es_pregunta": False, "decision": "SALUDO",
                    "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2), "estado": estado,
                }

        # 4. Consultas de descartes o resumen de estado activo
        norm_txt_cons = texto_limpio.casefold()
        if re.search(r"\bqu[eé]\s+(?:hemos|se\s+ha|tenemos)\s+descartado\b|\bdescartes?\s+hasta\s+ahora\b", norm_txt_cons):
            desc_items = []
            for d in getattr(estado, "hipotesis_descartadas", []):
                d_limpio = d.replace("componente:", "").replace("_", " ").capitalize()
                desc_items.append(f"• {d_limpio}")
            for h in getattr(estado, "hechos", {}).values():
                if getattr(h, "categoria", "") in ("componente_reemplazado", "verificacion_fisica", "rechazo_hipotesis_usuario"):
                    nombre = getattr(h, "campo", "").replace("rechazo_usuario_", "").replace("componente_comprobado_", "").replace("componente_reemplazado_", "").capitalize()
                    val = getattr(h, "valor", "")
                    item_str = f"• {nombre}: {val}"
                    if item_str not in desc_items:
                        desc_items.append(item_str)
            if desc_items:
                resp_descartes = "📋 *Comprobaciones y descartes registrados hasta el momento:*\n\n" + "\n".join(dict.fromkeys(desc_items))
            else:
                resp_descartes = "📋 *Descartes registrados:* Hasta el momento no se han registrado componentes descartados en este caso."
            return {
                "status": "resumen_descartes", "respuesta_texto": resp_descartes,
                "diagnostico_ml": estado.falla_principal or "Descartes del caso",
                "confianza_ml": estado.confianza_actual or 1.0, "fase": estado.fase.value,
                "es_pregunta": False, "decision": "RESUMEN_DESCARTES",
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2), "estado": estado,
            }

        if re.search(r"\bqu[eé]\s+(?:sabemos|tenemos)\s+hasta\s+ahora\b|\b(?:dame\s+(?:el\s+)?)?resumen\b", norm_txt_cons):
            veh_info = f"{estado.marca or 'Vehículo'} {estado.modelo or ''} {estado.anio or ''}".strip()
            comb_info = f" ({estado.combustible})" if estado.combustible else ""
            placa_info = f" - Placa: {estado.placa}" if estado.placa else ""
            sintomas_filtrados = []
            for s in (estado.active_symptoms or []):
                s_clean = s.strip()
                s_l = s_clean.lower()
                if (
                    s_l.startswith("¿")
                    or any(w in s_l for w in (
                        "me equivoque", "me equivoqué", "no es kia", "no es rio",
                        "no tengo escáner", "no tengo escaner", "gasolina", "diesel", "diésel",
                        "buenas tardes", "hola", "disculpa maestro", "placa ", "corrijo", "corrección"
                    ))
                ):
                    continue
                sintomas_filtrados.append(f"• {s_clean}")
            sint_txt = "\n".join(sintomas_filtrados) if sintomas_filtrados else "• Síntomas en evaluación preliminar"

            if estado.top3_actual:
                top_items = []
                for idx, t in enumerate(estado.top3_actual[:3], 1):
                    nom = t.get("falla") or t.get("categoria") or str(t)
                    pct = t.get("porcentaje_presentacion") or t.get("probabilidad")
                    pct_str = f" ({pct}%)" if pct else ""
                    top_items.append(f"  {idx}. {nom}{pct_str}")
                hip_txt = "\n".join(top_items)
            else:
                hip_txt = f"  1. {estado.falla_principal}" if estado.falla_principal else "Diagnóstico diferencial en curso"

            resp_resumen = (
                f"📋 *Resumen técnico del caso activo:*\n\n"
                f"🚗 *Vehículo:* {veh_info}{comb_info}{placa_info}\n"
                f"⚠️ *Síntomas observados:*\n{sint_txt}\n\n"
                f"🎯 *Hipótesis de trabajo:*\n{hip_txt}\n\n"
                f"¿Deseas aportar una nueva medición o proceder con las pruebas sugeridas?"
            )
            resp_resumen = PoliticaSeguridad.enriquecer_respuesta_seguridad(resp_resumen, norm_txt_cons, estado.falla_principal)
            return {
                "status": "resumen_caso", "respuesta_texto": resp_resumen,
                "diagnostico_ml": estado.falla_principal or "Resumen del caso",
                "confianza_ml": estado.confianza_actual or 1.0, "fase": estado.fase.value,
                "es_pregunta": True, "decision": "RESUMEN_CASO",
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2), "estado": estado,
            }

        # 5. Explicaciones causales y consultas técnicas
        patron_consulta_causal = re.compile(
            r"\b(?:por\s+qu[eé]|explicaci[oó]n|peligro\b.{0,30}\bseguridad|c[aá]rter\b.{0,30}\bdi[eé]sel|"
            r"carb[oó]n\b.{0,30}\bmariposa|testigo\b.{0,30}\b(?:calentador|precalentamiento)|"
            r"retorno\b.{0,30}\b(?:explica|ca[ií]da)|presi[oó]n\s+diferencial\b.{0,30}\b(?:normal|taponamiento)|"
            r"juego\b.{0,30}\b(?:eje|turbo)|reaprendizaje\b.{0,35}\b(?:manual|llave|pedal))\b|"
            r"\b(?:puede\b.{0,30}\bprovocar|explica\s+la\s+ca[ií]da|es\s+normal\s+o\s+indica)\b",
            re.IGNORECASE,
        )
        if patron_consulta_causal.search(norm_txt_cons):
            resp_por_que = cls._obtener_explicacion_causal(norm_txt_cons)
            if resp_por_que:
                resp_por_que = PoliticaSeguridad.enriquecer_respuesta_seguridad(resp_por_que, norm_txt_cons, estado.falla_principal)
                return {
                    "status": "explicacion_causal", "respuesta_texto": resp_por_que,
                    "diagnostico_ml": estado.falla_principal or "Explicación técnica",
                    "confianza_ml": estado.confianza_actual or 1.0, "fase": estado.fase.value,
                    "es_pregunta": False, "decision": "EXPLICACION_CAUSAL",
                    "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2), "estado": estado,
                }

        # 6. Tolerancias y especificaciones OEM
        if re.search(r"\b(?:tolerancia|alabeo\s+m[aá]ximo|especificaci[oó]n|temperatura\s+(?:debe\s+abrir|de\s+apertura))\b", norm_txt_cons):
            resp_tol = cls._obtener_tolerancia_oem(norm_txt_cons)
            if resp_tol:
                return {
                    "status": "tolerancia_oem", "respuesta_texto": resp_tol,
                    "diagnostico_ml": estado.falla_principal or "Tolerancia OEM",
                    "confianza_ml": estado.confianza_actual or 1.0, "fase": estado.fase.value,
                    "es_pregunta": False, "decision": "TOLERANCIA_OEM",
                    "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2), "estado": estado,
                }

        # 7. Solicitud de profundización técnica sobre caso activo
        if ExtractorHechos.es_solicitud_detalle(texto_limpio) and (estado.top3_actual or getattr(estado, "falla_principal", None)):
            return cls._procesar_detalle_caso_activo(estado, texto_limpio, norm_txt_cons, gestor_diagnostico, t0)

        return None

    @classmethod
    def _obtener_explicacion_causal(cls, norm_txt: str) -> Optional[str]:
        if (any(w in norm_txt for w in ("peligro", "seguridad", "arranco", "arrancar", "riesgo")) and any(w in norm_txt for w in ("carter", "cárter", "diesel", "diésel"))) or "embalamiento" in norm_txt:
            return (
                "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD MECÁNICA — RIESGO DE EMBALAMIENTO DIÉSEL:**\n\n"
                "⚠️ **PELIGRO EXTREMO: NO INTENTES ARRANCAR EL MOTOR.**\n\n"
                "Con el cárter sobrellenado y diluido con diésel, el movimiento del cigüeñal y la temperatura evaporan el combustible. "
                "Estos vapores ascienden por la ventilación del cárter (PCV) directamente a la admisión. Como el motor diésel no corta aire por mariposa, "
                "comenzará a quemar su propio aceite de forma incontrolada, acelerándose sin límite por encima de las 5000 RPM (**embalamiento diésel / runaway**). "
                "El motor no se apagará ni cortando la llave de contacto y sufrirá rotura de bielas, fundición catastrófica o incendio en el taller. "
                "Antes de cualquier arranque, es obligatorio drenar totalmente el aceite contaminado, cambiar el filtro y reponer aceite nuevo."
            )
        if any(w in norm_txt for w in ("mariposa", "cuerpo de aceleracion", "cuerpo de aceleración")) and any(w in norm_txt for w in ("carbon", "carbón", "500", "ralenti", "ralentí", "apaga", "cae")):
            return (
                "💡 *Explicación técnica del calado por carbonilla en mariposa de admisión:*\n\n"
                "Sí, el carbón acumulado en la mariposa y el venturi restringe severamente el paso de aire mínimo de ralentí. "
                "Al desacelerar o pisar el embrague en un semáforo, el motor pasa bruscamente de carga a marcha mínima. "
                "La mariposa electrónica motorizada intenta compensar la falta de aire, pero la obstrucción física retarda el flujo "
                "y hace que las RPM se desplomen a 400-500 RPM provocando el calado inmediato por falta de caudal de aire."
            )
        if any(w in norm_txt for w in ("calentadores", "testigo", "rulo", "precalentamiento")) and any(w in norm_txt for w in ("combustible", "riel", "presion", "presión", "p0087")):
            return (
                "💡 *Explicación técnica del testigo de calentadores destellando en diésel:*\n\n"
                "En motores diésel Common Rail modernos, el testigo de calentadores (rulo) cumple una doble función: "
                "además del precalentamiento, actúa como testigo maestro de anomalía crítica de gestión electrónica de inyección. "
                "Cuando la presión en el riel cae drásticamente por debajo del valor demandado (código P0087), la ECU hace destellar "
                "el testigo de calentadores y limita la potencia a modo de emergencia (limp mode) para proteger la bomba de alta presión CP4 y los inyectores."
            )
        if any(w in norm_txt for w in ("retorno", "probeta", "probetas")) and any(w in norm_txt for w in ("explica", "caida", "caída", "presion", "presión", "riel")):
            return (
                "💡 *Explicación técnica del exceso de retorno en inyector Common Rail:*\n\n"
                "Sí, el exceso de retorno en el inyector 3 explica directamente la caída de presión en el riel. "
                "Para alcanzar 1400 bar, la cámara de control del inyector debe mantener estanqueidad hidráulica perfecta. "
                "Cuando la válvula de control o la tobera interna sufren desgaste, el combustible a altísima presión fuga masivamente "
                "hacia la línea de retorno de baja presión (65 ml frente a 15 ml de los demás). Esta fuga supera la capacidad de entrega "
                "de la bomba de alta a plena aceleración, provocando la caída de presión a 220 bar y el código P0087."
            )
        if any(w in norm_txt for w in ("45 kpa", "presion diferencial", "presión diferencial")) and any(w in norm_txt for w in ("normal", "taponamiento", "dpf")):
            return (
                "💡 *Interpretación técnica de presión diferencial DPF (45 kPa):*\n\n"
                "45 kPa (450 mbar) a 2000 RPM indica un **taponamiento severo y crítico del filtro de partículas DPF**. "
                "En condiciones normales, la contrapresión diferencial no debe superar 5 a 8 kPa en ralentí ni 15 a 20 kPa a 2000 RPM. "
                "Una lectura de 45 kPa asfixia el escape, eleva la temperatura EGT y sobrecarga la turbina del turbo; confirma acumulación extrema "
                "de hollín (código P2463) y contraindica regeneraciones forzadas estáticas por riesgo de incendio; requiere desmontaje para lavado químico o cambio."
            )
        if any(w in norm_txt for w in ("juego", "turbo", "eje")) and any(w in norm_txt for w in ("175", "compresion", "compresión", "humo", "sellos", "confirma")):
            return (
                "💡 *Diagnóstico diferencial de consumo de aceite (Turbo vs Cilindros):*\n\n"
                "Sí, confirma que la causa del humo azul son los sellos de turbina. La compresión de 175 PSI pareja en los tres cilindros "
                "descarta completamente desgaste de aros de pistón o cilindros. El juego axial notable en el eje del turbo indica rotura "
                "o fatiga de los sellos laberinto de estanqueidad dinámica, permitiendo que el aceite lubricante presurizado pase directamente "
                "al circuito de admisión y escape, quemándose en la combustión. Requiere desmontaje y reparación del cartucho CHRA o cambio de turbo."
            )
        if any(w in norm_txt for w in ("reaprendizaje", "calibrar", "calibracion", "calibración")) and any(w in norm_txt for w in ("manual", "llave", "pedal")):
            return (
                "🛠️ *Procedimiento manual de reaprendizaje de mariposa (llave y pedal Drive-by-Wire):*\n\n"
                "1. Motor a temperatura de trabajo (85-90 °C) y apagar todos los consumidores eléctricos (luces, A/C, radio).\n"
                "2. Girar la llave a contacto ON (sin arrancar) durante 30 segundos continuos (no tocar pedales).\n"
                "3. Llevar la llave a OFF y esperar 10 segundos.\n"
                "4. Girar a ON durante 5 segundos; en los siguientes 5 segundos, pisar y soltar el acelerador a fondo 5 veces.\n"
                "5. Esperar 7 segundos con el pedal libre; luego pisar a fondo durante 20 segundos hasta que la luz check engine quede fija.\n"
                "6. Soltar el acelerador, dar arranque en ralentí y dejar estabilizar durante 3 minutos sin acelerar para confirmar 700-750 RPM estables."
            )
        if "recalienta" in norm_txt and any(w in norm_txt for w in ("trafico", "tráfico", "detenido", "parado")):
            return (
                "💡 *Explicación técnica del comportamiento térmico:*\n\n"
                "En carretera a velocidad sostenida, el flujo de aire natural que ingresa por la parrilla "
                "(convección dinámica) enfría el radiador de manera continua. Sin embargo, en tráfico detenido "
                "o ralentí, no existe flujo de aire exterior; el enfriamiento depende al 100% de la activación forzada "
                "del electroventilador y la circulación efectiva del refrigerante por el termostato y la bomba de agua. "
                "Si el electroventilador no enciende en su velocidad adecuada o el termostato no abre por completo, "
                "la temperatura ascenderá rápidamente hacia la zona crítica."
            )
        if any(w in norm_txt for w in ("corta", "segundos", "inyeccion", "inyección", "inmovilizador", "ecu")):
            return (
                "💡 *Explicación técnica de la estrategia de inmovilizador:*\n\n"
                "Al dar arranque, la ECU permite una activación inicial de 2 a 3 segundos mientras interroga "
                "al transponder de la llave mediante la antena receptora. Si el código de seguridad no es reconocido "
                "(o arroja DTC de transponder como B10DA), la ECU corta de inmediato los pulsos de inyección y bomba "
                "de combustible como medida de seguridad antirrobo, apagando el motor."
            )
        if any(w in norm_txt for w in ("congela", "reductor", "gas", "gnv", "glp")):
            return (
                "💡 *Explicación técnica de la congelación del reductor:*\n\n"
                "La caída drástica de presión del GNV (desde 200 bar a baja presión) provoca un enfriamiento extremo "
                "por efecto Joule-Thomson. El reductor requiere circulación continua de refrigerante caliente del motor "
                "para compensar esta pérdida térmica. Si las mangueras de agua tienen aire, están obstruidas o el motor "
                "aún no alcanza temperatura, el reductor se congela y escarcha, provocando tirones severos."
            )
        if any(w in norm_txt for w in ("zapatea", "trepida", "embrague")):
            return (
                "💡 *Explicación técnica de la trepidación al acoplar el embrague:*\n\n"
                "El zapateo o trepidación al arrancar en primera ocurre por falta de contacto plano homogéneo "
                "entre el disco, el plato opresor y el volante. Esto es provocado comúnmente por alabeo o puntos "
                "térmicos en el volante de inercia, resortes amortiguadores del disco fatigados o contaminación por aceite."
            )
        if any(w in norm_txt for w in ("cascabeleo", "inyector", "subida", "pobre")):
            return (
                "💡 *Explicación técnica de detonación por inyector deficiente:*\n\n"
                "Bajo carga (subida empinada acelerando a fondo), el motor requiere mayor volumen de combustible para "
                "disipar calor y mantener la combustión controlada. Un inyector sucio o con bajo caudal empobrece la mezcla, "
                "elevando bruscamente la temperatura de cámara y provocando autoignición espontánea (cascabeleo o pistoneo)."
            )
        return None

    @classmethod
    def _obtener_tolerancia_oem(cls, norm_txt: str) -> Optional[str]:
        if any(w in norm_txt for w in ("termostato", "abrir", "temperatura")):
            return (
                "🔬 *Especificación metrológica y tolerancia OEM (Termostato):*\n\n"
                "Según el manual de servicio del fabricante, la temperatura de inicio de apertura del termostato "
                "se sitúa entre 82 °C y 88 °C, alcanzando su carrera de apertura total a los 95 °C - 98 °C "
                "(elevación mínima de la válvula de 8 mm). Si a 108 °C la manguera inferior permanece fría, "
                "el termostato está trabado cerrado."
            )
        if any(w in norm_txt for w in ("volante", "inercia", "embrague")):
            return (
                "🔬 *Especificación metrológica y tolerancia OEM (Volante de inercia):*\n\n"
                "El alabeo o salto axial máximo admisible para el volante de inercia según manual es de 0.10 mm. "
                "Cualquier lectura superior a 0.10 mm o presencia de fisuras y sobrecalentamiento térmico azulado "
                "exige rectificado de la pista de fricción o reemplazo del volante."
            )
        if any(w in norm_txt for w in ("disco", "freno", "alabeo")):
            return (
                "🔬 *Especificación metrológica y tolerancia OEM (Discos de freno):*\n\n"
                "La tolerancia máxima de alabeo lateral en discos de freno instalados es de 0.05 mm a 0.07 mm. "
                "Una medición de 0.12 mm excede significativamente el límite de servicio y provocará pulsación "
                "en el pedal y vibración en el timón a alta velocidad; requiere rectificado o cambio de discos."
            )
        return None

    @classmethod
    def _procesar_detalle_caso_activo(
        cls,
        estado: ConversationState,
        texto_limpio: str,
        norm_txt: str,
        gestor_diagnostico: Any,
        t0: float,
    ) -> Dict[str, Any]:
        top_actual = estado.top3_actual or []
        falla_target = top_actual[0]["falla"] if top_actual else (estado.falla_principal or "Falla mecánica bajo revisión")

        for patron_c, falla_c in cls.COMPONENTES_CONSULTA:
            if patron_c in norm_txt:
                falla_target = falla_c
                break

        if any(w in texto_limpio for w in (" 2", "segunda", "opcion 2", "opción 2")):
            if len(top_actual) > 1:
                falla_target = top_actual[1]["falla"]
        elif any(w in texto_limpio for w in (" 3", "tercera", "opcion 3", "opción 3")):
            if len(top_actual) > 2:
                falla_target = top_actual[2]["falla"]

        contexto_rag_detalle = ""
        motor_rag = getattr(gestor_diagnostico, "motor_rag", None)
        if motor_rag and hasattr(motor_rag, "recuperar_contexto"):
            res_rag = motor_rag.recuperar_contexto(falla_target)
            if isinstance(res_rag, tuple):
                contexto_rag_detalle = res_rag[0] or ""
            elif isinstance(res_rag, str):
                contexto_rag_detalle = res_rag

        resp_detalle = FormateadorCompacto.formatear_detalle_tecnico(
            falla=falla_target,
            procedimiento_rag=contexto_rag_detalle,
            estado=estado,
        )
        return {
            "status": "detalle",
            "respuesta_texto": resp_detalle,
            "diagnostico_ml": falla_target,
            "confianza_ml": estado.confianza_actual,
            "fase": estado.fase.value,
            "es_pregunta": False,
            "decision": "DETALLE",
            "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
            "estado": estado,
        }
