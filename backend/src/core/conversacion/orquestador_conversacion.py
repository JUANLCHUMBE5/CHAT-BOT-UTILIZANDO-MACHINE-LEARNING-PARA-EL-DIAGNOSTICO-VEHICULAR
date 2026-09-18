"""Orquestador principal de la memoria conversacional acumulativa y auto-interrogador inteligente."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas
from src.core.conversacion.maquina_estados import MaquinaEstadosConversacion
from src.core.conversacion.models import (
    ConversationPhase,
    ConversationState,
    FactState,
    FactType,
    QuestionIntent,
    TurnTrace,
)
from src.core.conversacion.repositorio import (
    ConversationStateRepository,
    PostgresConversationRepository,
)
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta
from src.core.conversacion.suficiencia_informacion import EvaluadorSuficiencia
from src.core.logger import logger
from src.core.version import ORCHESTRATOR_VERSION


class OrquestadorConversacion:
    """Coordina el ciclo de vida de la conversación, extracción acumulativa y diagnóstico."""

    def __init__(self, repositorio: Optional[ConversationStateRepository] = None):
        self.repositorio = repositorio or PostgresConversationRepository()

    async def finalizar_caso(self, session_id: str, gestor_diagnostico: Optional[Any] = None) -> None:
        """Finaliza formalmente el case_id en el repositorio y en el SessionManager."""
        nuevo_id = None
        if gestor_diagnostico and hasattr(gestor_diagnostico, "session_manager"):
            nuevo_id = gestor_diagnostico.session_manager.finalizar_caso(session_id)
        await self.repositorio.finalizar_caso(session_id, nuevo_id)

    async def procesar_turno(
        self,
        session_id: str,
        texto_usuario: str,
        gestor_diagnostico: Any,
        placa: Optional[str] = None,
        marca_modelo: Optional[str] = None,
        proveedor: str = "meta",
        diagnostico_forzado: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Procesa un turno conversacional de WhatsApp con memoria y auto-interrogador inteligente."""
        t0 = time.perf_counter()
        texto_limpio = (texto_usuario or "").strip()

        # 1. Recuperar o inicializar estado de sesión
        estado = await self.repositorio.get_session(session_id)
        if estado is None:
            estado = ConversationState(session_id=session_id)
        if not estado.case_id:
            import uuid
            estado.case_id = str(uuid.uuid4())
            if not estado.active_problem_id:
                estado.active_problem_id = str(uuid.uuid4())

        # Sincronizar con SessionManager si existe y su caso fue reiniciado/finalizado
        if hasattr(gestor_diagnostico, "session_manager") and gestor_diagnostico.session_manager is not None:
            sesion_mgr = getattr(gestor_diagnostico.session_manager, "obtener_sesion", lambda _: None)(session_id)
            if sesion_mgr and isinstance(getattr(sesion_mgr, "case_id", None), str) and sesion_mgr.case_id != estado.case_id:
                estado.iniciar_nuevo_caso(sesion_mgr.case_id)

        contexto_previo = estado.exportar_dict(incluir_trazabilidad=False)

        # 2. Detección de reinicio de caso ("otro carro", "nuevo diagnóstico")
        if (
            ExtractorHechos.es_reinicio_solicitado(texto_limpio)
            and not ExtractorHechos.contiene_informacion_diagnostica(texto_limpio)
        ):
            await self.repositorio.reset_session(session_id)
            if hasattr(gestor_diagnostico, "session_manager") and gestor_diagnostico.session_manager:
                gestor_diagnostico.session_manager.reiniciar_sesion(session_id)
            resp_reinicio = (
                "🚗 *Caso finalizado.* He limpiado la memoria para registrar un nuevo vehículo.\n\n"
                "¿Cuál es la marca, modelo y la falla o síntoma que presenta el nuevo auto?"
            )
            return {
                "status": "reinicio", "respuesta_texto": resp_reinicio, "diagnostico_ml": "Reinicio de sesión",
                "confianza_ml": 1.0, "fase": ConversationPhase.INICIO.value, "es_pregunta": False, "decision": "REINICIO",
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2), "estado": ConversationState(session_id=session_id),
            }

        # 2.1 Detección de saludo inicial ("hola", "buenas", "buenos días")
        if ExtractorHechos.es_saludo(texto_limpio):
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

        # 2.2 Solicitud de profundización técnica ("más detalles", "cómo lo reviso")
        if ExtractorHechos.es_solicitud_detalle(texto_limpio) and (estado.top3_actual or getattr(estado, "falla_principal", None)):
            from src.core.conversacion.formateador_compacto import FormateadorCompacto

            top_actual = estado.top3_actual or []
            falla_target = top_actual[0]["falla"] if top_actual else "Falla mecánica bajo revisión"
            if any(w in texto_limpio for w in (" 2", "segunda", "opcion 2", "opción 2")):
                if len(top_actual) > 1:
                    falla_target = top_actual[1]["falla"]
            elif any(w in texto_limpio for w in (" 3", "tercera", "opcion 3", "opción 3")):
                if len(top_actual) > 2:
                    falla_target = top_actual[2]["falla"]

            contexto_rag_detalle = ""
            if hasattr(gestor_diagnostico.motor_rag, "recuperar_contexto"):
                res_rag = gestor_diagnostico.motor_rag.recuperar_contexto(falla_target)
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

        # 2.3 Segmentación automática de casos y aislamiento de contexto (Fase 9.10)
        from src.core.conversacion.segmentador_casos import SegmentadorCasos

        ret_trans, transicion = SegmentadorCasos.resolver_transicion_turno(
            estado=estado,
            texto_limpio=texto_limpio,
            gestor_diagnostico=gestor_diagnostico,
            session_id=session_id,
            t0=t0,
            contexto_previo=contexto_previo,
        )
        if ret_trans is not None:
            await self.repositorio.save_session(session_id, estado)
            return ret_trans
        if transicion.dominio_detectado_mensaje.value != "DESCONOCIDO":
            estado.dominio_probable = transicion.dominio_detectado_mensaje.value
        if transicion.decision.value == "CAMBIO_DE_CASO":
            contexto_previo = estado.exportar_dict(incluir_trazabilidad=False)

        # 3. Interpretación de respuestas cortas ("caliente", "la 2", "sí", etc.)
        falla_forzada_alternativa = diagnostico_forzado
        interpretacion_corta = None
        if InterpreteRespuestasCortas.es_respuesta_corta(texto_limpio):
            interpretacion_corta = InterpreteRespuestasCortas.interpretar(estado, texto_limpio)
            if interpretacion_corta and "diagnostico_forzado" in interpretacion_corta:
                falla_forzada_alternativa = interpretacion_corta["diagnostico_forzado"]

        # 4. Extracción acumulativa obligatoria de hechos clínicos
        estado_previo_hechos = dict(estado.hechos)
        hechos_extraidos = ExtractorHechos.extraer_y_actualizar(estado, texto_limpio)
        if interpretacion_corta and "hecho" in interpretacion_corta:
            hechos_extraidos.append(interpretacion_corta["hecho"])

        # Detección de evidencia duplicada (Fase 11.3 - Caso D / T04)
        es_evidencia_duplicada = False
        if hechos_extraidos and estado.top3_actual:
            campos_eval = [
                h.get("campo") for h in hechos_extraidos
                if isinstance(h, dict) and "campo" in h
            ]
            if campos_eval and all(
                c in estado_previo_hechos
                and estado_previo_hechos[c].valor == getattr(estado.hechos.get(c), "valor", None)
                for c in campos_eval
            ):
                es_evidencia_duplicada = True

        # 4b. Manejo de consulta técnica informativa pura (sin síntomas en el mensaje ni en el estado)
        from src.core.intent_classifier import clasificar_intencion_consulta
        tiene_sintomas = any(
            h.categoria == "sintoma" or h.tipo == FactType.SINTOMA
            for h in estado.hechos.values()
        )
        if not tiene_sintomas and clasificar_intencion_consulta(texto_limpio) == "consulta_tecnica":
            dto_tecnico = gestor_diagnostico._procesar_consulta_tecnica(
                pregunta=texto_limpio,
                inicio_total=t0,
                remitente=None,
                proveedor=proveedor,
                taller_id=None,
                usuario_id=None,
                conversacion_id=session_id,
                slot_gemini_preconcedido=None,
                diferir_encolado_persistente=False,
            )
            return {
                "status": "consulta_tecnica",
                "respuesta_texto": getattr(dto_tecnico, "respuesta_texto", "Información técnica."),
                "diagnostico_ml": getattr(dto_tecnico, "diagnostico_ml", "Consulta técnica"),
                "confianza_ml": getattr(dto_tecnico, "confianza_ml", 1.0),
                "fase": estado.fase.value,
                "es_pregunta": False,
                "decision": "DETALLE",
                "tiempo_ms": round((time.perf_counter() - t0) * 1000, 2),
                "estado": estado,
                "dto": dto_tecnico,
            }

        if estado.preguntas_realizadas:
            interp_str = (interpretacion_corta.get("valor") if interpretacion_corta else None) or "respuesta_usuario"
            estado.registrar_respuesta(texto_limpio, interp_str)

        if placa and placa not in ("REST-API", "WAPP-01", "DESCONOCIDO"):
            estado.placa = placa
        if marca_modelo and marca_modelo not in ("Vehiculo Generico", "Generico Generico", "Generico", ""):
            partes_mm = marca_modelo.split()
            if len(partes_mm) >= 1 and not estado.marca:
                estado.marca = partes_mm[0]
                estado.registrar_hecho("marca", partes_mm[0], categoria="vehiculo", texto_crudo=marca_modelo, tipo=FactType.CONDICION)
            if len(partes_mm) >= 2 and not estado.modelo:
                estado.modelo = " ".join(partes_mm[1:])
                estado.registrar_hecho("modelo", " ".join(partes_mm[1:]), categoria="vehiculo", texto_crudo=marca_modelo, tipo=FactType.CONDICION)

        # 5. Evaluación de suficiencia de información
        score, categorias_vistas, es_suficiente, motivo_suficiencia = EvaluadorSuficiencia.evaluar(estado)

        # 6. Reconstrucción de la consulta clínica consolidada y protección con guardia de contexto
        consulta_consolidada = SintetizadorConsulta.sintetizar(estado)

        from src.core.conversacion.guardia_contexto import GuardiaContextoDiagnostico
        es_valido, consulta_consolidada, reg_guardia = GuardiaContextoDiagnostico.validar_y_proteger(
            estado=estado,
            mensaje_actual=texto_limpio,
            consulta_consolidada=consulta_consolidada,
        )

        # 7. Decisión conversacional: PREGUNTAR vs DIAGNOSTICAR
        decision = "DIAGNOSTICAR"
        motivo_decision = motivo_suficiencia
        respuesta_texto = ""
        dto_resultado = None
        es_pregunta = False
        intent_elegido = None
        pregunta_elegida = None
        candidatas_traza = []
        descartadas_traza = []

        # Caso 0 (Fase 9.8, 9.11 y 9.15): Respuesta técnica, indisponibilidad de herramientas o Plan B
        if interpretacion_corta and estado.preguntas_realizadas:
            campo_ic = interpretacion_corta.get("campo")
            valor_ic = str(interpretacion_corta.get("valor", "")).upper()
            cat_ic = interpretacion_corta.get("categoria_respuesta", "")

            # 0.1 Activación de Plan B ante herramientas no disponibles o falta de procedimiento/conocimiento
            if (
                cat_ic in ("HERRAMIENTA_INDISPONIBLE", "NO_SABE_REALIZAR_PRUEBA", "NO_REVISADO")
                or (valor_ic == "NO" and campo_ic and "disponible" in campo_ic)
            ):
                from src.core.conversacion.compatibilidad_preguntas import CompatibilidadPreguntas
                from src.core.conversacion.gestor_plan_b import GestorPlanB

                dominio_actual = CompatibilidadPreguntas.dominio_actual(estado)
                ultima_preg_txt = estado.ultima_pregunta().get("texto", "") if estado.ultima_pregunta() else ""

                # Priorizar alternativa observable segura por inspección y dominio
                plan_b = GestorPlanB.obtener_plan_b_por_inspeccion(
                    dominio=dominio_actual,
                    ultima_preg=ultima_preg_txt,
                    estado=estado,
                )
                if not plan_b and estado.top3_actual:
                    top1_cand = estado.top3_actual[0].get("falla", "")
                    plan_b = GestorPlanB.obtener_plan_b_para_falla(top1_cand, estado)

                if plan_b:
                    pregunta_elegida = plan_b[1]
                    intent_elegido, decision = plan_b[2].value, "PLAN_B"
                    if cat_ic == "NO_SABE_REALIZAR_PRUEBA":
                        motivo_decision = f"Usuario no sabe realizar prueba ({campo_ic}): activando alternativa observable / Plan B seguro"
                    elif cat_ic == "NO_REVISADO":
                        motivo_decision = f"Comprobación no revisada ({campo_ic}): ofreciendo alternativa observable sencilla sin herramientas"
                    else:
                        motivo_decision = f"Herramienta indisponible ({campo_ic}): activando Plan B sensorial"
                elif cat_ic in ("HERRAMIENTA_INDISPONIBLE", "NO_SABE_REALIZAR_PRUEBA"):
                    pregunta_elegida = (
                        "Entiendo, sin comprobación previa ni método a la mano. "
                        "¿Prefieres que te oriente sobre precauciones de seguridad antes de llevarlo a inspección profesional en taller?"
                    )
                    intent_elegido, decision = QuestionIntent.PLAN_B_SIN_HERRAMIENTAS.value, "PLAN_B"
                    motivo_decision = "Sin método ni comprobación observable viable: orientando a derivación profesional"

            # 0.2 Herramienta disponible confirmada: solicitar medición técnica
            elif cat_ic == "HERRAMIENTA_RECUPERADA" or (valor_ic == "SI" and campo_ic and "disponible" in campo_ic):
                if campo_ic and "manometro" in campo_ic:
                    pregunta_elegida = "Con el manómetro conectado al riel de inyección: ¿cuántos PSI marca con la llave en ON y al dar marcha?"
                    intent_elegido, decision = QuestionIntent.MEDICION_PRESION.value, "PREGUNTAR"
                    motivo_decision = "Usuario cuenta con manómetro: solicitando lectura de presión de combustible"
                    estado.establecer_pregunta_pendiente(
                        intent=QuestionIntent.MEDICION_PRESION,
                        expected_quantity="presion_combustible",
                        expected_units=["PSI", "bar", "kPa"],
                        related_system="COMBUSTIBLE",
                    )
                elif campo_ic and "chispa" in campo_ic:
                    pregunta_elegida = "Con el probador de chispa conectado: ¿se observa salto constante de chispa azulada al dar arranque?"
                    intent_elegido, decision = QuestionIntent.COMPONENTE_REVISADO.value, "PREGUNTAR"
                    motivo_decision = "Usuario cuenta con probador de chispa: solicitando comprobación"
                else:
                    pregunta_elegida = "Con el multímetro conectado en escala de 20 V DC: ¿cuánto marca en reposo y a cuánto baja al dar arranque?"
                    intent_elegido, decision = QuestionIntent.MEDICION_VOLTAJE.value, "PREGUNTAR"
                    motivo_decision = "Usuario cuenta con multímetro: solicitando lectura de voltaje"
                    estado.establecer_pregunta_pendiente(
                        intent=QuestionIntent.MEDICION_VOLTAJE,
                        expected_quantity="voltaje_bateria",
                        expected_units=["V", "mV"],
                        related_system="ELECTRICO",
                    )

            if pregunta_elegida and intent_elegido and not respuesta_texto:
                estado.registrar_pregunta(intent=QuestionIntent(intent_elegido), texto=pregunta_elegida, incrementar_repregunta=False)
                respuesta_texto, es_pregunta = pregunta_elegida, True

            # 0.5 Medición técnica de PRESIÓN (Fase 11.3: NUNCA convertir PSI a V ni cambiar dominio)
            elif (campo_ic == "medicion_presion" or interpretacion_corta.get("unidad") in ("PSI", "bar", "kPa")) and interpretacion_corta.get("valor") is not None:
                val = interpretacion_corta.get("valor")
                unidad = interpretacion_corta.get("unidad", "PSI")
                estado.registrar_medicion("presion_combustible", float(val), unidad, contexto="riel_inyeccion", prueba="presion_combustible")
                estado.registrar_prueba_completada("presion_combustible", f"{val} {unidad}")
                estado.limpiar_pregunta_pendiente()

                respuesta_texto = (
                    f"Registrado: {val} {unidad} de presión de combustible en el riel. "
                    f"Compara este valor con la especificación de servicio del fabricante para el motor y sistema de inyección específico. "
                    f"Para continuar la comprobación, ¿se observa salto de chispa constante en las bujías o dispones de escáner para verificar códigos DTC?"
                )
                decision = "CONCLUSION_TECNICA"
                motivo_decision = f"Medición de presión {val} {unidad} registrada y contextualizada"
                es_pregunta = False

            # 0.5b Medición técnica de VOLTAJE
            elif campo_ic == "medicion_voltaje" and interpretacion_corta.get("valor") is not None:
                val = interpretacion_corta.get("valor")
                cond = interpretacion_corta.get("condicion_medicion")
                if cond == "durante_arranque":
                    if float(val) < 9.6:
                        respuesta_texto = (
                            f"⚠️ Caída de tensión crítica: {val} V en arranque (mínimo normal 9.6 V). "
                            f"Esto confirma descarga profunda, celda dañada o consumo excesivo del arrancador. "
                            f"Revisa ajuste de bornes y prueba con una batería de apoyo."
                        )
                    else:
                        respuesta_texto = (
                            f"✅ Caída de tensión normal: {val} V en arranque (adecuado ≥ 9.6 V). "
                            f"La batería retiene carga bajo demanda. El problema de arranque apunta al solenoide/arrancador o switch de encendido."
                        )
                    decision = "CONCLUSION_TECNICA"
                    motivo_decision = f"Medición de voltaje en arranque evaluada: {val} V"
                    es_pregunta = False
                else:
                    pregunta_arranque = (
                        f"Registrado: {val} V. Para comprobar si la batería mantiene la carga bajo consumo real, "
                        f"¿a cuánto desciende el multímetro mientras mantienes la llave en posición de arranque?"
                    )
                    intent_arranque = QuestionIntent.MEDICION_VOLTAJE
                    estado.registrar_pregunta(intent=intent_arranque, texto=pregunta_arranque, incrementar_repregunta=False)
                    decision = "PREGUNTAR"
                    motivo_decision = f"Voltaje inicial {val} V registrado: solicitando medición durante el arranque"
                    respuesta_texto = pregunta_arranque
                    es_pregunta = True
                    intent_elegido = intent_arranque.value
                    pregunta_elegida = pregunta_arranque

            # 0.6 Acople de compresor de A/C confirmado (Fase 11.3: consumo de prueba física)
            elif campo_ic == "compresor_acopla" or estado.obtener_valor_confirmado("compresor_acopla") == "SI":
                pregunta_ac = (
                    "Confirmado: el compresor sí acopla y el embrague responde. "
                    "Para verificar si hay fuga de gas o falta de intercambio de calor: ¿gira el electroventilador del condensador al encender el A/C y las tuberías del vano motor se sienten una bien fría y otra caliente?"
                )
                intent_ac = QuestionIntent.COMPONENTE_REVISADO
                estado.registrar_pregunta(intent=intent_ac, texto=pregunta_ac, incrementar_repregunta=False)
                decision = "PREGUNTAR"
                motivo_decision = "Compresor acopla confirmado: avanzando a electroventilador e intercambio térmico"
                respuesta_texto = pregunta_ac
                es_pregunta = True
                intent_elegido = intent_ac.value
                pregunta_elegida = pregunta_ac

            # 0.7 Luces de tablero observadas
            elif campo_ic == "luces_se_atenuan":
                if valor_ic == "SI":
                    respuesta_texto = (
                        "Al atenuarse fuertemente las luces del tablero al dar contacto, se produce una caída drástica de tensión. "
                        "Revisa ajuste y sulfatación en bornes de batería, o prueba con cables puente."
                    )
                else:
                    respuesta_texto = (
                        "Al mantenerse las luces encendidas con brillo normal, la batería no sufre caída de tensión. "
                        "El fallo de arranque se concentra en el circuito de control: relé de arranque, terminal 50 o solenoide."
                    )
                decision = "CONCLUSION_TECNICA"
                motivo_decision = f"Observación de luces de tablero procesada: {valor_ic}"
                es_pregunta = False

        # Caso A: Información insuficiente y aún con margen de repregunta (< 3)
        if not respuesta_texto and not es_suficiente and not falla_forzada_alternativa and estado.turnos_repregunta < estado.max_repreguntas:
            seleccion = GeneradorPreguntas.seleccionar_pregunta_con_filtro(estado)
            if seleccion:
                txt_preg, opciones_preg, intent_preg, candidatas_traza, descartadas_traza = seleccion
                estado.registrar_pregunta(
                    intent=intent_preg,
                    texto=txt_preg,
                    opciones=opciones_preg,
                )
                decision = "PREGUNTAR"
                motivo_decision = f"Información insuficiente ({score}/3 categorías). Aclarando {intent_preg.value}"
                respuesta_texto = txt_preg
                es_pregunta = True
                intent_elegido = intent_preg.value
                pregunta_elegida = txt_preg

        # Caso B y C: Diagnóstico ML (por límite de repreguntas alcanzado o información suficiente)
        if not respuesta_texto:
            es_caso_b = not es_suficiente and estado.turnos_repregunta >= estado.max_repreguntas and not falla_forzada_alternativa
            falla_diag = None if es_caso_b else falla_forzada_alternativa

            if hasattr(gestor_diagnostico, "session_manager"):
                gestor_diagnostico.session_manager.cargar_contexto(
                    session_id,
                    {"conversation_state": estado.exportar_dict(), "case_id": estado.case_id}
                )
            dto_resultado = gestor_diagnostico.procesar_consulta_texto(
                texto_usuario=consulta_consolidada,
                placa=estado.placa or "WAPP-01",
                marca_modelo=f"{estado.marca or 'Vehiculo'} {estado.modelo or 'Generico'}",
                session_id=session_id,
                proveedor=proveedor,
                diagnostico_forzado=falla_diag,
            )
            top3_ml_raw = None
            if getattr(dto_resultado, "predicciones_ml", None):
                top3_ml_raw = [
                    {
                        "falla": getattr(p, "falla", None) or (p.get("falla") if isinstance(p, dict) else str(p)),
                        "probabilidad": getattr(p, "probabilidad", 0.0) if hasattr(p, "probabilidad") else (p.get("probabilidad", 0.0) if isinstance(p, dict) else 0.0),
                    }
                    for p in dto_resultado.predicciones_ml[:3]
                ]
            elif dto_resultado.diagnostico_ml:
                top3_ml_raw = [{"falla": dto_resultado.diagnostico_ml, "probabilidad": dto_resultado.confianza_ml}]

            from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad
            hipotesis_final_presentada, exclusiones_compat = ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
                predicciones_raw=top3_ml_raw or [],
                estado=estado,
                nueva_evidencia=texto_limpio if hechos_extraidos else None,
            )

            if not (es_evidencia_duplicada and estado.top3_actual):
                estado.top3_actual = hipotesis_final_presentada or top3_ml_raw or []
                if hipotesis_final_presentada:
                    estado.falla_principal = hipotesis_final_presentada[0]["falla"]
                    estado.confianza_actual = hipotesis_final_presentada[0]["probabilidad"]
                else:
                    estado.confianza_actual = dto_resultado.confianza_ml

            from src.core.conversacion.formateador_compacto import FormateadorCompacto
            hipotesis_formatear = estado.top3_actual or [
                {"falla": dto_resultado.diagnostico_ml, "probabilidad": dto_resultado.confianza_ml}
            ]
            preg_ctx, intent_ctx = FormateadorCompacto.obtener_pregunta_contextual(
                top1_falla_o_hipotesis=hipotesis_formatear,
                sintoma_original=texto_limpio,
                estado=estado,
            )
            if preg_ctx and estado.ya_preguntado_texto(preg_ctx):
                preg_ctx = None
                intent_ctx = None
            scores_pres = FormateadorCompacto.calcular_scores_presentacion(hipotesis_formatear)
            respuesta_texto = FormateadorCompacto.formatear_respuesta_diagnostico(
                top_hipotesis=hipotesis_formatear,
                sintoma_original=texto_limpio,
                contexto_rag=getattr(dto_resultado, "contexto_manual", "") or "",
                pregunta_personalizada=preg_ctx,
                estado=estado,
            )
            if es_caso_b:
                decision = "DIFERENCIAL"
                motivo_decision = "Límite de 3 repreguntas alcanzado: forzando diagnóstico diferencial"
            else:
                decision = "DIAGNOSTICAR"
                motivo_decision = f"Diagnóstico completado con {score} categorías y certidumbre {int(dto_resultado.confianza_ml*100)}%"

            if preg_ctx and intent_ctx and not es_caso_b:
                estado.registrar_pregunta(
                    intent=intent_ctx,
                    texto=preg_ctx,
                    opciones=[],
                    hipotesis=[h.get("falla", "") for h in hipotesis_formatear],
                    incrementar_repregunta=False,
                )
                pregunta_elegida = preg_ctx
                intent_elegido = intent_ctx.value
                es_pregunta = True

        # 8. Transición formal en la máquina de estados
        MaquinaEstadosConversacion.transicionar(
            estado=estado,
            es_reinicio=False,
            nueva_evidencia=len(hechos_extraidos) > 0,
        )

        # 9. Registro de trazabilidad del turno
        traza = TurnTrace(
            turno=estado.turno_actual, mensaje_original=texto_limpio, contexto_previo=contexto_previo,
            hechos_nuevos_extraidos=hechos_extraidos,
            hechos_actualizados=[h.to_dict() for h in estado.hechos.values() if h.estado == FactState.CONFIRMADO],
            consulta_consolidada=consulta_consolidada, top3=estado.top3_actual, confianza=estado.confianza_actual,
            decision=decision, motivo_decision=motivo_decision, respuesta_enviada=respuesta_texto,
            estado_operativo=estado.estado_operativo.value, question_intent=intent_elegido,
            preguntas_candidatas=candidatas_traza, preguntas_descartadas=descartadas_traza,
            pregunta_final=pregunta_elegida, top3_ml_raw=locals().get("top3_ml_raw"),
            hipotesis_rechazadas_usuario=list(estado.hipotesis_descartadas),
            nueva_evidencia=texto_limpio if hechos_extraidos else None,
            hipotesis_final_presentada=locals().get("hipotesis_final_presentada"),
            exclusiones_compatibilidad=locals().get("exclusiones_compat", []),
            scores_presentacion=locals().get("scores_pres"),
            estado_previo=transicion.estado_previo.value if "transicion" in locals() else None,
            estado_detectado_mensaje_actual=transicion.estado_detectado_mensaje.value if "transicion" in locals() else None,
            decision_transicion=transicion.decision.value if "transicion" in locals() else None,
            motivo_transicion=transicion.motivo if "transicion" in locals() else None,
            dominio_previo=transicion.dominio_previo.value if "transicion" in locals() else None,
            dominio_detectado_actual=(
                transicion.dominio_detectado_mensaje.value if "transicion" in locals() else None
            ),
            dominio_actual=estado.dominio_probable,
            plan_b_activado=intent_elegido if decision == "PLAN_B" else None,
            herramientas_bloqueadas=list(estado.herramientas_no_disponibles),
            version_orquestador=ORCHESTRATOR_VERSION,
        )
        estado.trazabilidad.append(traza.to_dict())
        if len(estado.trazabilidad) > 15:
            estado.trazabilidad = estado.trazabilidad[-15:]

        # 10. Persistir estado conversacional acumulativo
        await self.repositorio.save_session(session_id, estado)

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        logger.info(
            f"[ConversacionTurno] Sesión {session_id} Turno {estado.turno_actual} -> Decisión: {decision} ({elapsed_ms}ms)"
        )

        return {
            "status": "completado",
            "respuesta_texto": respuesta_texto,
            "diagnostico_ml": getattr(dto_resultado, "diagnostico_ml", "Aclaración técnica"),
            "confianza_ml": getattr(dto_resultado, "confianza_ml", 0.0),
            "top3_actual": estado.top3_actual,
            "scores_presentacion": traza.scores_presentacion,
            "fase": estado.fase.value,
            "es_pregunta": es_pregunta,
            "decision": decision,
            "motivo_decision": motivo_decision,
            "consulta_consolidada": consulta_consolidada,
            "tiempo_ms": elapsed_ms,
            "dto": dto_resultado,
            "estado": estado,
            "estado_operativo": estado.estado_operativo.value,
            "question_intent": intent_elegido,
            "preguntas_candidatas": candidatas_traza,
            "preguntas_descartadas": descartadas_traza,
            "pregunta_final": pregunta_elegida,
            "version_orquestador": traza.version_orquestador,
            "top3_ml_raw": traza.top3_ml_raw,
            "hipotesis_rechazadas_usuario": traza.hipotesis_rechazadas_usuario,
            "nueva_evidencia": traza.nueva_evidencia,
            "hipotesis_final_presentada": traza.hipotesis_final_presentada,
            "exclusiones_compatibilidad": traza.exclusiones_compatibilidad,
            "estado_previo": traza.estado_previo,
            "estado_detectado_mensaje_actual": traza.estado_detectado_mensaje_actual,
            "decision_transicion": traza.decision_transicion,
            "motivo_transicion": traza.motivo_transicion,
            "dominio_previo": traza.dominio_previo,
            "dominio_detectado_actual": traza.dominio_detectado_actual,
            "dominio_actual": traza.dominio_actual,
        }

    procesar_mensaje = procesar_turno
