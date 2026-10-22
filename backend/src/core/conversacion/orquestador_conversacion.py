"""Orquestador principal de la memoria conversacional acumulativa y auto-interrogador inteligente."""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.core.conversacion.proteccion_turnos import proteger_turno
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
from src.infrastructure.rag.documental_salida import es_solicitud_especificacion, normalizar


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

    @proteger_turno
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
        if estado is not None and res.get("decision") != "SEGURIDAD_CRITICA":
            from src.core.conversacion.plan_b.catalogo import CATALOGO_HERRAMIENTAS

            respuesta_norm = normalizar(str(res.get("respuesta_texto", "")))
            herramientas_pedidas_de_nuevo = []
            for clave in getattr(estado, "herramientas_no_disponibles", []):
                # El bloqueo adicional solo cubre la regresión reproducida de frenos.
                # Las demás herramientas ya tienen Plan B específico y no deben perderlo.
                if clave != "reloj_comparador":
                    continue
                herramienta = CATALOGO_HERRAMIENTAS.get(clave)
                terminos = getattr(herramienta, "terminos", ()) if herramienta else (clave,)
                if res.get("es_pregunta") and any(
                    normalizar(termino) in respuesta_norm for termino in terminos
                ):
                    herramientas_pedidas_de_nuevo.append(
                        getattr(herramienta, "nombre_canonico", clave)
                    )
            if herramientas_pedidas_de_nuevo:
                lista = ", ".join(dict.fromkeys(herramientas_pedidas_de_nuevo))
                contexto_sintomas = normalizar(
                    " ".join(getattr(estado, "active_symptoms", []))
                    + " " + str(getattr(estado, "falla_principal", ""))
                    + " " + " ".join(str(x) for x in getattr(estado, "top3_actual", []))
                    + " " + str(getattr(estado, "active_system", ""))
                )
                if "reloj_comparador" in getattr(estado, "herramientas_no_disponibles", []) and any(
                    termino in contexto_sintomas for termino in ("freno", "disco", "pastilla", "alabeo")
                ):
                    res.update(
                        respuesta_texto=(
                            "Anotado: no dispones de reloj comparador. Sin desmontar ni meterte debajo del auto, "
                            "y solo con el vehículo completamente inmovilizado, puedes observar desde fuera con "
                            "una linterna si el disco presenta surcos marcados o zonas azuladas. No hagas pruebas "
                            "en vía pública ni toques piezas calientes. Esta observación no confirma alabeo; si "
                            "no es visible o persiste la vibración, solicita inspección en taller y mantén el caso pendiente."
                        ),
                        decision="PLAN_B",
                        status="plan_b_visual_frenos_sin_reloj",
                        es_pregunta=False,
                    )
                    herramientas_pedidas_de_nuevo = []
            if herramientas_pedidas_de_nuevo:
                res.update(
                    respuesta_texto=(
                        f"Anotado: no dispones de {lista}. No repetiré esa medición ni la daré por realizada. "
                        "Mantengo el caso pendiente; solicita la comprobación en un taller equipado antes de intervenir."
                    ),
                    decision="PLAN_B",
                    status="plan_b_herramienta_no_disponible",
                    es_pregunta=False,
                )
        # Defensa final frente a retornos anticipados: la respuesta de peligro
        # es autoritativa; jamás se agrega a una instrucción contradictoria.
        from src.core.diagnostico.politica_seguridad import PoliticaSeguridad, SeveridadSeguridad

        severidad, banner = PoliticaSeguridad.evaluar_severidad(texto_usuario, "", estado=estado)
        if severidad == SeveridadSeguridad.CRITICAL_STOP and banner:
            if res.get("decision") == "DIAGNOSTICAR" and (
                "ADVERTENCIA CRÍTICA DE SEGURIDAD" in res.get("respuesta_texto", "")
                or "BLOQUEO DE SEGURIDAD MECÁNICA" in res.get("respuesta_texto", "")
            ):
                pass
            else:
                res.update(
                    respuesta_texto=banner.strip(),
                    decision="SEGURIDAD_CRITICA",
                    confianza_ml=0.0,
                    es_pregunta=False,
                )
        if estado is not None:
            res.setdefault("case_id", estado.case_id)
        veh_str = f"{getattr(estado, 'marca', '') or ''} {getattr(estado, 'modelo', '') or ''} {getattr(estado, 'anio', '') or ''}".strip()
        correccion_vehicular_actual = (
            estado is not None
            and getattr(estado, "turno_ultima_correccion", None) == getattr(estado, "turno_actual", None)
            and getattr(estado, "last_user_correction", None) in ("marca", "modelo", "anio")
        )
        if correccion_vehicular_actual and veh_str and veh_str not in res.get("respuesta_texto", ""):
            if res.get("es_pregunta"):
                res.update(
                    respuesta_texto=(
                        f"Entendido, actualicé el vehículo a *{veh_str}*. Conservo los síntomas y mediciones reportados. "
                        "La comprobación de frenos sigue pendiente; no confirmo alabeo ni una pieza sin medición."
                    ),
                    es_pregunta=False,
                    status="correccion_vehiculo_pendiente",
                )
            else:
                res["respuesta_texto"] = (
                    f"Entendido, actualicé el vehículo a *{veh_str}*. Conservo los síntomas y mediciones reportados.\n\n"
                    + res.get("respuesta_texto", "")
                )
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
        if (
            resultado.get("decision") == "OPCION_NUMERICA_INVALIDA"
            and "fuera de rango" not in normalizar(str(resultado.get("respuesta_texto", "")))
        ):
            resultado["respuesta_texto"] = (
                "La opción indicada está fuera de rango. " + resultado.get("respuesta_texto", "")
            )
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
