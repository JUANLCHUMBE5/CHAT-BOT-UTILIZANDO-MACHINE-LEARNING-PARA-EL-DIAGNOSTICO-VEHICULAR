"""Orquestador principal del flujo tripartito de consultas diagnósticas de texto."""

from __future__ import annotations

import re
import time
from typing import Any, Optional

from src.core.diagnostic_cache import diagnostico_cache
from src.core.diagnostico.coherencia_evidencia import (
    bateria_ya_comprobada,
    priorizar_evidencia,
)
from src.core.diagnostico.finalizacion import finalizar_diagnostico
from src.core.diagnostico.models import ResultadoDiagnostico
from src.core.diagnostico.procesador_texto.clasificacion_ml import (
    ejecutar_clasificacion_ml,
)
from src.core.diagnostico.procesador_texto.interaccion_sesion import (
    manejar_interaccion_previa,
)
from src.core.diagnostico.procesador_texto.recuperacion_rag import (
    ejecutar_recuperacion_y_fusion_rag,
)
from src.core.intent_classifier import clasificar_intencion_consulta
from src.core.logger import logger
from src.core.sanitizer import sanitizar_prompt_usuario
from src.core.security import anonimizar_identificador
from src.core.traductor_jerga import normalizar_jerga_peruana
from src.core.vehicle_profile import (
    extraer_datos_vehiculo,
    kilometraje_es_ambiguo,
)


def procesar_consulta_texto(
    gestor: Any,
    texto_usuario: str,
    placa: Optional[str] = None,
    marca_modelo: Optional[str] = None,
    session_id: Optional[str] = None,
    remitente: Optional[str] = None,
    proveedor: str = "meta",
    taller_id: Optional[str] = None,
    usuario_id: Optional[str] = None,
    conversacion_id: Optional[str] = None,
    slot_gemini_preconcedido: Optional[bool] = None,
    diferir_encolado_persistente: bool = False,
    diagnostico_forzado: Optional[str] = None,
    orquestado: bool = False,
    case_id: Optional[str] = None,
) -> ResultadoDiagnostico:
    """Flujo tripartito secuencial THREAD-SAFE para consultas de texto."""
    inicio_total = time.perf_counter()
    texto_sanitizado = sanitizar_prompt_usuario(texto_usuario)
    texto_normalizado = normalizar_jerga_peruana(texto_sanitizado)

    placa_anonima = anonimizar_identificador(placa or "")
    session_id_anon = anonimizar_identificador(session_id or "")
    logger.info(
        f"Procesando consulta texto (Longitud: {len(texto_normalizado)} caracteres) | "
        f"Placa Anonimizada: {placa_anonima} | Session ID Anonimizado: {session_id_anon} | Proveedor: {proveedor}"
    )

    clave_sesion = session_id or (placa if placa not in (None, "REST-API", "WAPP-01") else None)
    sesion_pendiente = gestor.session_manager.obtener_sesion(clave_sesion) if clave_sesion else None
    case_id_actual = case_id or getattr(sesion_pendiente, "case_id", None)

    # 1. Estados interactivos previos de sesión
    resultado_interactivo, texto_normalizado, diag_f = manejar_interaccion_previa(
        gestor=gestor,
        texto_normalizado=texto_normalizado,
        clave_sesion=clave_sesion,
        sesion_pendiente=sesion_pendiente,
        marca_modelo=marca_modelo,
        inicio_total=inicio_total,
        remitente=remitente,
        proveedor=proveedor,
        taller_id=taller_id,
        usuario_id=usuario_id,
        conversacion_id=conversacion_id,
        slot_gemini_preconcedido=slot_gemini_preconcedido,
        diferir_encolado_persistente=diferir_encolado_persistente,
    )
    if resultado_interactivo:
        return resultado_interactivo
    if diag_f:
        diagnostico_forzado = diag_f

    # 2. Acumulación y segmentación contextual
    if orquestado:
        texto_evaluar = texto_normalizado
        marca_evaluar = marca_modelo
        placa_evaluar = placa
    elif clave_sesion:
        sesion_anterior = gestor.session_manager.obtener_sesion(clave_sesion)
        from src.core.conversacion.segmentador_casos import SegmentadorCasos

        es_cambio_explicito = any(
            f in texto_normalizado.lower()
            for f in (
                "otro problema", "otra falla", "nuevo problema", "tengo un susto", "tengo un problema",
                "mire maestro", "otra cosa", "cambio de tema", "el cliente dejó", "el cliente dejo",
                "el cliente trajo", "el cliente dice", "el cliente indica", "otro vehículo", "otro vehiculo",
                "otro carro", "este es otro", "nuevo caso", "tengo otro", "ahora presenta",
                "ahora el problema", "ahora revisemos", "ya revisaré", "ya revisare", "olvida lo anterior",
                "eso ya lo revisé", "eso ya lo revise"
            )
        ) or SegmentadorCasos.es_nueva_queja_principal(texto_normalizado)

        if diagnostico_forzado:
            sesion = sesion_anterior or gestor.session_manager.obtener_o_crear_sesion(clave_sesion)
            texto_evaluar = sesion.obtener_sintoma_completo() or texto_normalizado
            marca_evaluar = marca_modelo or sesion.marca_modelo
            placa_evaluar = placa or sesion.placa
        elif sesion_anterior and sesion_anterior.estado == "en_proceso" and not es_cambio_explicito:
            sesion = sesion_anterior
            texto_evaluar = sesion.obtener_sintoma_completo() or texto_normalizado
            marca_evaluar = marca_modelo or sesion.marca_modelo
            placa_evaluar = placa or sesion.placa
        else:
            tiene_sintomas_reales = False
            if sesion_anterior and sesion_anterior.conversation_state:
                tiene_sintomas_reales = any(
                    h.categoria == "sintoma" and h.estado.value == "CONFIRMADO"
                    for h in sesion_anterior.conversation_state.hechos.values()
                )

            es_nuevo = es_cambio_explicito or (
                (
                    tiene_sintomas_reales
                    or (sesion_anterior and getattr(sesion_anterior, "estado", "") in ("completo", "completado"))
                )
                and not gestor._es_continuacion_contextual(texto_normalizado)
            )
            if sesion_anterior and es_nuevo:
                if es_cambio_explicito:
                    gestor.session_manager.finalizar_caso(clave_sesion)
                elif tiene_sintomas_reales:
                    gestor.session_manager.reiniciar_sesion(clave_sesion)
            sesion = gestor.session_manager.acumular_input_usuario(
                session_id=clave_sesion,
                texto_usuario=texto_normalizado,
                placa=placa,
                marca_modelo=marca_modelo,
            )

            texto_evaluar = sesion.obtener_sintoma_completo()
            perfil_recibido = extraer_datos_vehiculo(texto_evaluar)
            if marca_modelo and marca_modelo not in ("Vehiculo Generico", "Generico", ""):
                perfil_recibido.update(extraer_datos_vehiculo(marca_modelo))
            if perfil_recibido:
                sesion.actualizar_perfil(perfil_recibido)
            marca_evaluar = marca_modelo or sesion.marca_modelo
            placa_evaluar = placa or sesion.placa
    else:
        texto_evaluar = texto_normalizado
        marca_evaluar = marca_modelo
        placa_evaluar = placa

    combustible_detectado, modo_falla_combustible = gestor._extraer_contexto_combustible(texto_evaluar)
    tiene_dtc = bool(re.search(r"\b[pbcu]\d{4}\b", texto_evaluar, re.IGNORECASE))
    tiene_componente_especifico = any(
        c in texto_evaluar.lower()
        for c in (
            "bobina", "bujia", "bujía", "inyector", "sensor", "valvula", "válvula",
            "compresion", "compresión", "bomba de gasolina", "bomba de combustible",
            "cables de bujia", "distribuidor", "catalizador", "egr", "maf", "map", "cilindro",
            "presion de combustible", "presión de combustible", "la bomba", "manometro", "manómetro",
            "cae fuerte", "aforador", "tanque casi vacio", "tanque casi vacío",
        )
    )
    if (
        clave_sesion
        and not orquestado
        and gestor._es_perdida_potencia_bajo_carga(texto_evaluar)
        and not tiene_dtc
        and not tiene_componente_especifico
    ):
        sesion_combustible = gestor.session_manager.obtener_o_crear_sesion(clave_sesion)
        combustible_confirmado = (
            combustible_detectado or sesion_combustible.perfil_vehiculo.get("combustible")
        )
        modo_confirmado = modo_falla_combustible or sesion_combustible.modo_falla_combustible
        if combustible_detectado:
            sesion_combustible.actualizar_perfil({"combustible": combustible_detectado})
        if modo_falla_combustible:
            sesion_combustible.establecer_modo_falla_combustible(modo_falla_combustible)
        if not combustible_confirmado or not modo_confirmado:
            consulta_orig = (
                sesion_combustible.sintomas[0] if sesion_combustible.sintomas else texto_evaluar
            )
            sesion_combustible.establecer_consulta_combustible(consulta_orig)
            return gestor._resultado_solicitud_combustible(
                sesion_combustible, combustible_confirmado
            )

    tipo_consulta = clasificar_intencion_consulta(texto_evaluar)
    if tipo_consulta == "consulta_tecnica":
        if clave_sesion:
            sesion_tecnica = gestor.session_manager.obtener_o_crear_sesion(clave_sesion)
            datos_iniciales = extraer_datos_vehiculo(texto_evaluar)
            if marca_evaluar and marca_evaluar not in ("Vehiculo Generico", "Generico", ""):
                datos_iniciales.update(extraer_datos_vehiculo(marca_evaluar))
            sesion_tecnica.actualizar_perfil(datos_iniciales)
            sesion_tecnica.establecer_consulta_tecnica(
                texto_evaluar,
                gestor._campos_requeridos_consulta_tecnica(texto_evaluar),
                kilometraje_es_ambiguo(texto_evaluar),
            )
            if sesion_tecnica.campos_faltantes() or sesion_tecnica.kilometraje_por_aclarar:
                return gestor._resultado_solicitud_datos_vehiculo(sesion_tecnica)

            perfil_texto = gestor._formatear_perfil_vehiculo(sesion_tecnica.perfil_vehiculo)
            if perfil_texto:
                texto_evaluar += f"\n\nDATOS CONFIRMADOS DEL VEHÍCULO:\n{perfil_texto}"
            sesion_tecnica.reiniciar()
        return gestor._procesar_consulta_tecnica(
            texto_evaluar,
            inicio_total=inicio_total,
            remitente=remitente,
            proveedor=proveedor,
            taller_id=taller_id,
            usuario_id=usuario_id,
            conversacion_id=conversacion_id,
            slot_gemini_preconcedido=slot_gemini_preconcedido,
            diferir_encolado_persistente=diferir_encolado_persistente,
        )

    if not orquestado and not diagnostico_forzado:
        es_ambigua, mensaje_aclaracion = gestor._es_consulta_ambigua(texto_evaluar)
        if es_ambigua:
            if clave_sesion:
                gestor.session_manager.obtener_o_crear_sesion(clave_sesion).estado = "esperando_clarificacion"
            return ResultadoDiagnostico(
                respuesta_texto=mensaje_aclaracion,
                diagnostico_ml="Consulta Ambigua / Datos Faltantes",
                confianza_ml=0.0,
                contexto_manual="",
                titulo_manual="",
                requiere_revision_humana=True,
                estado_sesion="esperando_clarificacion",
                modo_diagnostico="esperando_clarificacion",
                tipo_consulta="aclaracion",
            )

    if tipo_consulta == "fuera_de_alcance":
        if clave_sesion:
            gestor.session_manager.reiniciar_sesion(clave_sesion)
        return ResultadoDiagnostico(
            respuesta_texto="🚗 Describe el síntoma, por ejemplo: *vibra al manejar*.",
            diagnostico_ml="Consulta fuera del alcance automotriz",
            confianza_ml=0.0,
            contexto_manual="",
            titulo_manual="",
            requiere_revision_humana=True,
            modo_diagnostico="fuera_de_alcance",
            sintoma_evaluado=texto_evaluar,
            tiempo_total_ms=max(0, int((time.perf_counter() - inicio_total) * 1000)),
            tipo_consulta="fuera_de_alcance",
        )

    # 3. Consulta de Caché LRU
    clave_cache = None
    if case_id_actual:
        clave_cache = diagnostico_cache.generar_clave(
            sintoma=texto_evaluar,
            marca_modelo=marca_evaluar or "",
            placa=placa_evaluar or "",
            case_id=case_id_actual,
        )
    resultado_en_cache = diagnostico_cache.obtener(clave_cache) if clave_cache else None
    if resultado_en_cache is not None:
        logger.info("⚡ Diagnóstico obtenido instantáneamente desde Memoria Caché LRU (< 5ms)")
        return resultado_en_cache.model_copy(
            update={
                "desde_cache": True,
                "tiempo_total_ms": max(1, int((time.perf_counter() - inicio_total) * 1000)),
            }
        )

    # 4. Enrutamiento del sistema activo
    from src.core.diagnostico.enrutador_sistema import (
        areas_para_sistema,
        detectar_areas_tecnicas,
        resolver_sistema_activo,
    )

    sesion_ruteo = gestor.session_manager.obtener_sesion(clave_sesion) if clave_sesion else None
    estado_ruteo = getattr(sesion_ruteo, "conversation_state", None)
    texto_ruteo = texto_normalizado
    if estado_ruteo is not None and estado_ruteo.active_system == "ambiguo":
        texto_ruteo = " ".join(estado_ruteo.historial_mensajes_usuario[-2:]) or texto_normalizado
    sistema_activo = resolver_sistema_activo(
        texto_ruteo,
        getattr(estado_ruteo, "active_system", None),
    )
    if estado_ruteo is not None:
        estado_ruteo.active_system = sistema_activo
    areas_consulta = detectar_areas_tecnicas(texto_normalizado)
    if sistema_activo and sistema_activo != "ambiguo":
        areas_consulta = areas_para_sistema(sistema_activo, texto_normalizado) or areas_para_sistema(
            sistema_activo,
            texto_evaluar,
        )
    elif not areas_consulta and sistema_activo is None:
        areas_consulta = detectar_areas_tecnicas(texto_evaluar)
    if sistema_activo == "ambiguo":
        pregunta_aclaratoria = (
            "Entiendo el dato de 500 rpm, pero por sí solo no identifica la causa. "
            "¿El motor tiembla o ratea, se apaga, o solo observaste ese valor en el escáner?"
            if re.search(r"\b500\s*rpm\b", texto_normalizado.lower())
            else (
                "Aún no puedo ubicar el sistema sin asumir una causa. "
                "¿Qué síntoma concreto presenta el vehículo y en qué momento ocurre?"
            )
        )
        return ResultadoDiagnostico(
            respuesta_texto=pregunta_aclaratoria,
            diagnostico_ml="Se requiere contexto para clasificar el sistema",
            confianza_ml=0.0,
            contexto_manual="",
            titulo_manual="",
            requiere_revision_humana=True,
            modo_diagnostico="ruteo_ambiguo",
            sintoma_evaluado=texto_evaluar,
            tiempo_total_ms=max(0, int((time.perf_counter() - inicio_total) * 1000)),
            predicciones_ml=[],
            predicciones_ml_raw=[],
        )

    # 5. Inferencia ML y filtrado por área
    (
        diagnostico_predictivo,
        confianza,
        predicciones_ml,
        predicciones_originales,
        motivo_enrutamiento_area,
        tiempo_ml_ms,
    ) = ejecutar_clasificacion_ml(
        gestor=gestor,
        texto_evaluar=texto_evaluar,
        diagnostico_forzado=diagnostico_forzado,
        clave_sesion=clave_sesion,
        areas_consulta=areas_consulta,
        sistema_activo=sistema_activo,
        modo_falla_combustible=modo_falla_combustible,
        tiene_dtc=tiene_dtc,
        tiene_componente_especifico=tiene_componente_especifico,
    )

    ses_chk = gestor.session_manager.obtener_sesion(clave_sesion) if clave_sesion else None
    ya_aclarado = False
    if ses_chk:
        if ses_chk.ultimas_hipotesis_diferenciales:
            descartadas_set = set(ses_chk.ultimas_hipotesis_diferenciales)
            if diagnostico_predictivo in descartadas_set and predicciones_ml:
                for pred_alt in predicciones_ml:
                    if pred_alt.falla not in descartadas_set:
                        diagnostico_predictivo = pred_alt.falla
                        confianza = pred_alt.probabilidad
                        break
        if ses_chk.estado == "en_proceso" or bool(ses_chk.ultimas_hipotesis_diferenciales):
            ya_aclarado = True

    predicciones_ml, motivo_prioridad = priorizar_evidencia(texto_evaluar, predicciones_ml)
    motivo_prioridad_fisica = motivo_prioridad
    if motivo_enrutamiento_area:
        motivo_prioridad = "; ".join(
            motivo for motivo in (motivo_prioridad, motivo_enrutamiento_area) if motivo
        )
    if motivo_prioridad:
        diagnostico_predictivo = predicciones_ml[0].falla
        confianza = predicciones_ml[0].probabilidad

    # 6. Auto-pregunta de descarte
    from src.core.diagnostico.auto_interrogador import (
        evaluar_auto_pregunta_descarte,
        formatear_mensaje_auto_pregunta,
    )
    from src.core.diagnostico.politica_seguridad import PoliticaSeguridad, SeveridadSeguridad

    sev_seguridad, banner_seguridad = PoliticaSeguridad.evaluar_severidad(
        f"{texto_usuario} {texto_evaluar}", diagnostico_predictivo
    )
    es_critico_seguridad = (sev_seguridad == SeveridadSeguridad.CRITICAL_STOP)

    auto_preg = evaluar_auto_pregunta_descarte(
        texto=texto_evaluar,
        diagnostico_top1=diagnostico_predictivo,
        confianza_top1=confianza,
        predicciones_top=[p.model_dump() for p in predicciones_ml] if predicciones_ml else None,
    )
    if (
        clave_sesion
        and auto_preg
        and auto_preg.es_necesaria
        and not diagnostico_forzado
        and not ya_aclarado
        and not es_critico_seguridad
        and not motivo_prioridad
        and not (areas_consulta and not predicciones_ml)
        and not bateria_ya_comprobada(texto_evaluar)
    ):
        ses_auto = gestor.session_manager.obtener_o_crear_sesion(clave_sesion)
        if ses_auto.estado != "esperando_autopregunta":
            ses_auto.establecer_autopregunta(
                sintoma_base=texto_evaluar,
                opciones=auto_preg.opciones,
                hipotesis=auto_preg.hipotesis_diferenciales,
            )
            return ResultadoDiagnostico(
                respuesta_texto=formatear_mensaje_auto_pregunta(auto_preg),
                diagnostico_ml="Auto-pregunta técnica de descarte enviada",
                confianza_ml=confianza,
                contexto_manual="",
                titulo_manual="",
                requiere_revision_humana=True,
                estado_sesion="esperando_autopregunta",
                modo_diagnostico="esperando_clarificacion",
                sintoma_evaluado=texto_evaluar,
                tipo_consulta="aclaracion",
                predicciones_ml=predicciones_ml,
                tiempo_ml_ms=tiempo_ml_ms,
                tiempo_total_ms=max(0, int((time.perf_counter() - inicio_total) * 1000)),
            )

    # 7. Recuperación RAG y fusión
    texto_ml = gestor._purificar_sintoma_para_vectorizador_ml(texto_evaluar)
    (
        contexto_manual,
        titulo_manual,
        similitud_rag,
        meta_rag_dict,
        rag_valido,
        resultado_fusion,
        diagnostico_predictivo,
        confianza,
        predicciones_ml,
        tiempo_rag_ms,
    ) = ejecutar_recuperacion_y_fusion_rag(
        gestor=gestor,
        texto_evaluar=texto_evaluar,
        diagnostico_predictivo=diagnostico_predictivo,
        confianza=confianza,
        predicciones_ml=predicciones_ml,
        texto_ml=texto_ml,
        marca_evaluar=marca_evaluar,
    )

    if motivo_prioridad_fisica:
        predicciones_ml, _ = priorizar_evidencia(texto_evaluar, predicciones_originales)
        diagnostico_predictivo = predicciones_ml[0].falla
        confianza = predicciones_ml[0].probabilidad
        resultado_fusion.evidencia_confirmada.append(motivo_prioridad)

    # 8. Finalización y síntesis
    return finalizar_diagnostico(
        gestor=gestor,
        texto_usuario=texto_usuario,
        texto_evaluar=texto_evaluar,
        diagnostico_predictivo=diagnostico_predictivo,
        confianza=confianza,
        predicciones_ml=predicciones_ml,
        predicciones_originales=predicciones_originales,
        motivo_prioridad=motivo_prioridad,
        contexto_manual=contexto_manual,
        titulo_manual=titulo_manual,
        similitud_rag=similitud_rag,
        meta_rag_dict=meta_rag_dict,
        resultado_fusion=resultado_fusion,
        rag_valido=rag_valido,
        areas_consulta=areas_consulta,
        diagnostico_forzado=diagnostico_forzado,
        sistema_activo=sistema_activo,
        tiene_dtc=tiene_dtc,
        marca_evaluar=marca_evaluar,
        placa_evaluar=placa_evaluar,
        clave_sesion=clave_sesion,
        case_id=case_id_actual,
        remitente=remitente,
        proveedor=proveedor,
        taller_id=taller_id,
        usuario_id=usuario_id,
        conversacion_id=conversacion_id,
        slot_gemini_preconcedido=slot_gemini_preconcedido,
        diferir_encolado_persistente=diferir_encolado_persistente,
        tiempo_ml_ms=tiempo_ml_ms,
        tiempo_rag_ms=tiempo_rag_ms,
        inicio_total=inicio_total,
        clave_cache=clave_cache,
    )
