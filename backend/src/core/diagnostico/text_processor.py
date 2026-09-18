"""Procesamiento y orquestación secuencial de consultas de texto para diagnóstico y consultas técnicas."""

from __future__ import annotations

import re
import time
from typing import Any, Optional

from src.config import settings
from src.core.diagnostic_cache import diagnostico_cache
from src.core.diagnostico.models import PrediccionML, ResultadoDiagnostico
from src.core.intent_classifier import clasificar_intencion_consulta
from src.core.logger import logger
from src.core.sanitizer import sanitizar_prompt_usuario
from src.core.security import anonimizar_identificador
from src.core.traductor_jerga import normalizar_jerga_peruana
from src.core.vehicle_profile import (
    extraer_datos_vehiculo,
    extraer_datos_vehiculo_contextual,
    kilometraje_es_ambiguo,
)
from src.core.whatsapp_response import formatear_consulta_tecnica_whatsapp
from src.infrastructure.container import ServiceContainer


def procesar_consulta_tecnica(
    gestor: Any,
    pregunta: str,
    *,
    inicio_total: float,
    remitente: Optional[str],
    proveedor: str,
    taller_id: Optional[str],
    usuario_id: Optional[str],
    conversacion_id: Optional[str],
    slot_gemini_preconcedido: Optional[bool],
    diferir_encolado_persistente: bool,
) -> ResultadoDiagnostico:
    """Responde información automotriz sin forzar una clase de avería ML."""
    inicio_rag = time.perf_counter()
    if hasattr(gestor.motor_rag, "recuperar_contexto_con_similitud"):
        contexto, titulo, similitud = gestor.motor_rag.recuperar_contexto_con_similitud(pregunta)
    else:
        contexto, titulo = gestor.motor_rag.recuperar_contexto(pregunta)
        similitud = 0.0
    tiempo_rag_ms = max(0, int((time.perf_counter() - inicio_rag) * 1000))

    inicio_llm = time.perf_counter()
    respuesta, uso_llm = gestor._generar_respuesta_con_metadatos(
        pregunta=pregunta,
        diagnostico_ml="Consulta técnica informativa",
        confianza_ml=0.0,
        contexto_manual=contexto,
        titulo_manual=titulo,
        requiere_revision_humana=False,
        remitente=remitente,
        proveedor=proveedor,
        taller_id=taller_id,
        usuario_id=usuario_id,
        conversacion_id=conversacion_id,
        slot_gemini_preconcedido=slot_gemini_preconcedido,
        diferir_encolado_persistente=diferir_encolado_persistente,
        tipo_consulta="consulta_tecnica",
    )
    tiempo_llm_ms = max(0, int((time.perf_counter() - inicio_llm) * 1000))
    modo = uso_llm.get(
        "modo",
        "consulta_tecnica" if uso_llm.get("usado") else "consulta_tecnica_degradada",
    )
    if proveedor.lower() in {"meta", "twilio", "whatsapp"} and modo != "consulta_tecnica_en_cola":
        respuesta = formatear_consulta_tecnica_whatsapp(
            respuesta,
            modelo_informado=bool(extraer_datos_vehiculo(pregunta).get("modelo")),
        )
    return ResultadoDiagnostico(
        respuesta_texto=respuesta,
        diagnostico_ml="Consulta técnica informativa",
        confianza_ml=0.0,
        contexto_manual=contexto,
        titulo_manual=titulo,
        similitud_rag=similitud,
        requiere_revision_humana=False,
        modo_diagnostico=modo,
        solicitud_id=uso_llm.get("solicitud_id"),
        llm_usado=uso_llm.get("usado", False),
        llm_modelo=uso_llm.get("modelo"),
        tokens_entrada=uso_llm.get("tokens_entrada", 0),
        tokens_salida=uso_llm.get("tokens_salida", 0),
        posicion_cola=uso_llm.get("posicion_cola", 0),
        tiempo_espera_cola=uso_llm.get("tiempo_espera_cola", 0.0),
        sintoma_evaluado=pregunta,
        tiempo_rag_ms=tiempo_rag_ms,
        tiempo_llm_ms=tiempo_llm_ms,
        tiempo_total_ms=max(0, int((time.perf_counter() - inicio_total) * 1000)),
        tipo_consulta="consulta_tecnica",
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
) -> ResultadoDiagnostico:
    """
    Flujo tripartito secuencial THREAD-SAFE para consultas de texto:
    1. ML clasifica el síntoma y calcula confianza.
    2. RAG recupera el procedimiento del manual de taller.
    3. Gemini LLM sintetiza la respuesta técnica estructurada en 3 secciones.
    """
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

    if sesion_pendiente and sesion_pendiente.estado in ("esperando_autopregunta", "esperando_aclaracion_sintoma"):
        from src.core.diagnostico.auto_interrogador import (
            es_rechazo_de_opciones,
            generar_pregunta_descarte_secundario,
            resolver_respuesta_autopregunta,
        )

        idx_opt, txt_opt, diag_canonica = resolver_respuesta_autopregunta(
            texto_normalizado,
            sesion_pendiente.autopregunta_opciones,
            sesion_pendiente.autopregunta_hipotesis,
        )
        if idx_opt is not None:
            sintoma_base = sesion_pendiente.autopregunta_sintoma_base or sesion_pendiente.obtener_sintoma_completo()
            texto_evaluar = f"{sintoma_base}. Confirmación técnica: {txt_opt}".strip()
            texto_normalizado = texto_evaluar
            sesion_pendiente.sintomas = [texto_evaluar]
            sesion_pendiente.estado = "en_proceso"
            otras_hipotesis = [
                h for i, h in enumerate(sesion_pendiente.autopregunta_hipotesis) if i != idx_opt
            ]
            sesion_pendiente.ultimas_hipotesis_diferenciales = otras_hipotesis
            sesion_pendiente.autopregunta_sintoma_base = None
            sesion_pendiente.autopregunta_opciones = []
            sesion_pendiente.autopregunta_hipotesis = []
            diagnostico_forzado = diag_canonica
        elif es_rechazo_de_opciones(texto_normalizado):
            sintoma_base = sesion_pendiente.autopregunta_sintoma_base or sesion_pendiente.obtener_sintoma_completo()
            hipotesis_descartadas = list(sesion_pendiente.autopregunta_hipotesis)
            sesion_pendiente.ultimas_hipotesis_diferenciales = hipotesis_descartadas
            sesion_pendiente.autopregunta_opciones = []
            sesion_pendiente.autopregunta_hipotesis = []
            sesion_pendiente.estado = "esperando_aclaracion_sintoma"

            mensaje_descarte = generar_pregunta_descarte_secundario(sintoma_base, hipotesis_descartadas)
            return ResultadoDiagnostico(
                respuesta_texto=mensaje_descarte,
                diagnostico_ml="Descarte de opciones previas / Solicitud de aclaración técnica",
                confianza_ml=0.0,
                contexto_manual="",
                titulo_manual="",
                requiere_revision_humana=True,
                estado_sesion="esperando_aclaracion_sintoma",
                modo_diagnostico="esperando_clarificacion",
                sintoma_evaluado=sintoma_base,
                tipo_consulta="aclaracion",
                tiempo_ml_ms=0,
                tiempo_total_ms=max(0, int((time.perf_counter() - inicio_total) * 1000)),
            )
        else:
            es_cambio = any(
                f in texto_normalizado.lower()
                for f in (
                    "otro problema", "otra falla", "nuevo problema", "hola", "buenas", "reiniciar",
                    "el cliente dejó", "el cliente dejo", "el cliente trajo", "el cliente dice",
                    "el cliente indica", "otro vehículo", "otro vehiculo", "otro carro", "este es otro",
                    "nuevo caso", "tengo otro", "ahora presenta", "ahora el problema", "ahora revisemos",
                    "ya revisaré", "ya revisare", "olvida lo anterior", "eso ya lo revisé", "eso ya lo revise"
                )
            )
            sintoma_base = sesion_pendiente.autopregunta_sintoma_base or sesion_pendiente.obtener_sintoma_completo()
            if sintoma_base and not es_cambio:
                descarte_previo = ""
                if sesion_pendiente.ultimas_hipotesis_diferenciales:
                    descarte_previo = f" Descarte previo: no es {', '.join(sesion_pendiente.ultimas_hipotesis_diferenciales[:2])}."
                texto_evaluar = f"{sintoma_base}.{descarte_previo} Aclaración técnica del mecánico: {texto_normalizado}".strip()
                texto_normalizado = texto_evaluar
                sesion_pendiente.sintomas = [texto_evaluar]
                sesion_pendiente.estado = "en_proceso"
                sesion_pendiente.autopregunta_sintoma_base = None
                sesion_pendiente.autopregunta_opciones = []
                sesion_pendiente.autopregunta_hipotesis = []
            elif es_cambio:
                sesion_pendiente.reiniciar()

    if sesion_pendiente and sesion_pendiente.estado == "esperando_combustible":
        combustible_anterior = sesion_pendiente.perfil_vehiculo.get("combustible")
        combustible, modo_falla = gestor._extraer_contexto_combustible(
            texto_normalizado, combustible_anterior
        )
        es_respuesta_combustible = bool(
            combustible
            or modo_falla
            or any(t in texto_normalizado.lower() for t in ("gnv", "glp", "gasolina", "gas", "ambos", "dos"))
        )
        es_cambio_de_tema = any(
            term in texto_normalizado.lower()
            for term in (
                "freno", "pedal", "pastilla", "zapata", "disco", "liquido", "timon", "timón",
                "cremallera", "rotula", "rótula", "amortiguador", "palier", "homocinetica",
                "homocinética", "rodaje", "rodamiento", "embrague", "clutch", "bateria",
                "otro problema", "otra falla", "nuevo problema", "tengo un susto", "mire maestro",
            )
        )
        if not es_respuesta_combustible or es_cambio_de_tema:
            sesion_pendiente.reiniciar()
        else:
            if combustible in {"GNV", "GLP"} or (combustible and not combustible_anterior):
                sesion_pendiente.actualizar_perfil({"combustible": combustible})
            sesion_pendiente.establecer_modo_falla_combustible(modo_falla)
            combustible_confirmado = sesion_pendiente.perfil_vehiculo.get("combustible")
            if not combustible_confirmado or not sesion_pendiente.modo_falla_combustible:
                return gestor._resultado_solicitud_combustible(
                    sesion_pendiente, combustible_confirmado
                )

            pregunta_original = sesion_pendiente.consulta_combustible_pendiente or ""
            contexto_combustible = gestor._texto_modo_combustible(
                combustible_confirmado, sesion_pendiente.modo_falla_combustible
            )
            texto_normalizado = f"{pregunta_original} {contexto_combustible}".strip()
            sesion_pendiente.reiniciar()

    if sesion_pendiente and sesion_pendiente.estado == "esperando_datos_vehiculo":
        sesion_pendiente.campos_requeridos = []
        es_nueva_consulta = clasificar_intencion_consulta(texto_normalizado) == "consulta_tecnica"
        if es_nueva_consulta:
            sesion_pendiente.reiniciar()
        else:
            datos_recibidos = extraer_datos_vehiculo_contextual(
                texto_normalizado,
                sesion_pendiente.campos_faltantes(),
                sesion_pendiente.perfil_vehiculo,
            )
            if marca_modelo and marca_modelo not in ("Vehiculo Generico", "Generico", ""):
                datos_recibidos.update(extraer_datos_vehiculo(marca_modelo))
            sesion_pendiente.actualizar_perfil(datos_recibidos)
            if sesion_pendiente.kilometraje_por_aclarar:
                return gestor._resultado_solicitud_datos_vehiculo(sesion_pendiente)

            pregunta_original = sesion_pendiente.consulta_tecnica_pendiente or texto_normalizado
            perfil_texto = gestor._formatear_perfil_vehiculo(sesion_pendiente.perfil_vehiculo)
            pregunta_contextual = pregunta_original
            if perfil_texto:
                pregunta_contextual += f"\n\nDATOS CONFIRMADOS DEL VEHÍCULO:\n{perfil_texto}"
            sesion_pendiente.reiniciar()
            return gestor._procesar_consulta_tecnica(
                pregunta_contextual,
                inicio_total=inicio_total,
                remitente=remitente,
                proveedor=proveedor,
                taller_id=taller_id,
                usuario_id=usuario_id,
                conversacion_id=conversacion_id,
                slot_gemini_preconcedido=slot_gemini_preconcedido,
                diferir_encolado_persistente=diferir_encolado_persistente,
            )

    es_saludo, mensaje_saludo = gestor._es_saludo_o_contacto_inicial(texto_normalizado)
    if es_saludo:
        if session_id:
            gestor.session_manager.reiniciar_sesion(session_id)
        return ResultadoDiagnostico(
            respuesta_texto=mensaje_saludo,
            diagnostico_ml="Consulta General / Saludo",
            confianza_ml=1.0,
            contexto_manual="",
            titulo_manual="",
            modo_diagnostico="saludo",
            tipo_consulta="conversacional",
        )

    if gestor._es_respuesta_cordial(texto_normalizado):
        if clave_sesion:
            gestor.session_manager.reiniciar_sesion(clave_sesion)
        return ResultadoDiagnostico(
            respuesta_texto="👍 Entendido.",
            diagnostico_ml="Confirmación conversacional",
            confianza_ml=0.0,
            contexto_manual="",
            titulo_manual="",
            modo_diagnostico="conversacional",
            sintoma_evaluado=texto_normalizado,
            tipo_consulta="conversacional",
        )

    if clave_sesion:
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
                tiene_sintomas_reales
                and not gestor._es_continuacion_contextual(texto_normalizado)
                and len(texto_normalizado.split()) >= 12
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
        and gestor._es_perdida_potencia_bajo_carga(texto_evaluar)
        and not tiene_dtc
        and not tiene_componente_especifico
    ):
        sesion_combustible = gestor.session_manager.obtener_o_crear_sesion(clave_sesion)
        combustible_confirmado = (
            combustible_detectado or sesion_combustible.perfil_vehiculo.get("combustible")
        )
        if combustible_detectado:
            sesion_combustible.actualizar_perfil({"combustible": combustible_detectado})
        if not combustible_confirmado or not modo_falla_combustible:
            sesion_combustible.establecer_consulta_combustible(texto_evaluar)
            return gestor._resultado_solicitud_combustible(
                sesion_combustible, combustible_confirmado
            )

    tipo_consulta = clasificar_intencion_consulta(texto_evaluar)
    logger.debug("Intención detectada: %s", tipo_consulta)
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

    # Consultar Caché LRU en Memoria
    clave_cache = diagnostico_cache.generar_clave(
        sintoma=texto_evaluar,
        marca_modelo=marca_evaluar or "",
        placa=placa_evaluar or "",
    )
    resultado_en_cache = diagnostico_cache.obtener(clave_cache)
    if resultado_en_cache is not None:
        logger.info("⚡ Diagnóstico obtenido instantáneamente desde Memoria Caché LRU (< 5ms)")
        return resultado_en_cache.model_copy(
            update={
                "desde_cache": True,
                "tiempo_total_ms": max(1, int((time.perf_counter() - inicio_total) * 1000)),
            }
        )

    # PASO 1: Machine Learning Supervisado
    inicio_ml = time.perf_counter()
    texto_ml = gestor._purificar_sintoma_para_vectorizador_ml(texto_evaluar)
    if diagnostico_forzado:
        diagnostico_predictivo = diagnostico_forzado
        confianza = 0.80
        predicciones_ml = [PrediccionML(falla=diagnostico_forzado, probabilidad=0.80)]
        alts_fallas = []
        if clave_sesion:
            ses_act = gestor.session_manager.obtener_sesion(clave_sesion)
            if ses_act and getattr(ses_act, "ultimas_hipotesis_diferenciales", None):
                alts_fallas = [h for h in ses_act.ultimas_hipotesis_diferenciales if h != diagnostico_forzado]

        if len(alts_fallas) < 2 and hasattr(gestor.modelo_ml, "predecir_top_fallas"):
            raw_top = gestor.modelo_ml.predecir_top_fallas(texto_ml, limite=5)
            for item in raw_top:
                f_nom = item.get("falla")
                if f_nom and f_nom != diagnostico_forzado and f_nom not in alts_fallas:
                    alts_fallas.append(f_nom)

        probs_diff = [0.13, 0.07]
        for i, alt_nombre in enumerate(alts_fallas[:2]):
            predicciones_ml.append(
                PrediccionML(falla=alt_nombre, probabilidad=probs_diff[i] if i < len(probs_diff) else 0.05)
            )
    elif hasattr(gestor.modelo_ml, "predecir_top_fallas"):
        predicciones_raw = gestor.modelo_ml.predecir_top_fallas(texto_ml, limite=3)
        predicciones_ml = [PrediccionML(**item) for item in predicciones_raw]
        diagnostico_predictivo = predicciones_ml[0].falla
        confianza = predicciones_ml[0].probabilidad
    else:
        diagnostico_predictivo, confianza = gestor.modelo_ml.predecir_falla_con_confianza(texto_ml)
        predicciones_ml = [PrediccionML(falla=diagnostico_predictivo, probabilidad=confianza)]

    # Especialización técnica: motor de arranque / clac seco
    es_sintoma_arrancador = any(
        p in texto_evaluar.lower()
        for p in (
            "clac seco", "no da marcha", "se queda mudo", "toques al arrancador",
            "golpecitos al arrancador", "engancha y prende", "solo un clac",
            "clac clac en el arrancador", "clac clac", "chasquido en el arrancador",
        )
    )
    if es_sintoma_arrancador and diagnostico_predictivo in (
        "Bateria descargada o bornes sulfatados",
        "Falla en bateria, bornes o circuito del motor de arranque (solenoide/carbones)",
        "Falla en motor de arranque o solenoide (carbones gastados / contactos fogueados)",
        "ELECTRICO_002",
    ):
        diagnostico_predictivo = "Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)"
        if predicciones_ml:
            predicciones_ml[0] = PrediccionML(falla=diagnostico_predictivo, probabilidad=confianza)

    # Especialización técnica: bombín de embrague pegado al piso
    es_bombin = any(
        p in texto_evaluar.lower()
        for p in (
            "pedal se fue al piso", "pedal pegado al piso", "pedal de embrague se fue",
            "pedal quedo flojo", "pedal al piso como trapo", "pedal en el piso",
        )
    )
    if es_bombin and diagnostico_predictivo != "Falla en bombin o bomba hidraulica de embrague":
        diagnostico_predictivo = "Falla en bombin o bomba hidraulica de embrague"
        confianza = max(confianza, 0.75)
        if predicciones_ml:
            predicciones_ml.insert(0, PrediccionML(falla=diagnostico_predictivo, probabilidad=confianza))
            predicciones_ml = predicciones_ml[:3]

    # Especialización técnica: parpadeo de Check Engine / luz del motor bajo carga (Misfire severo)
    descarte_ignicion = any(
        p in texto_evaluar.lower()
        for p in (
            "cambie bujia", "cambie bobina", "bujias nuevas", "bobinas nuevas",
            "probe bobina", "probe bujia", "intercambie bobina", "intercambie bujia",
            "cambie bujias y bobinas", "bujias y bobinas cambiadas", "descarte bujia",
            "descarte bobina", "probe chispa",
        )
    )
    es_parpadeo_check = (
        ("parpadea" in texto_evaluar.lower() or "destella" in texto_evaluar.lower())
        and any(w in texto_evaluar.lower() for w in ("luz del motor", "check engine", "testigo del motor"))
    ) or ("misfire" in texto_evaluar.lower())

    if descarte_ignicion:
        if "inyector" in texto_evaluar.lower() or "pulso" in texto_evaluar.lower() or "p020" in texto_evaluar.lower():
            promovida = "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"
        elif any(w in texto_evaluar.lower() for w in ("compresion", "valvula", "piston", "anillos")):
            promovida = "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados"
        else:
            promovida = "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"
        diagnostico_predictivo = promovida
        confianza = max(confianza, 0.78)
        if predicciones_ml:
            predicciones_ml = [p for p in predicciones_ml if "bujia" not in p.falla.lower()]
            predicciones_ml.insert(0, PrediccionML(falla=promovida, probabilidad=confianza))
            predicciones_ml = predicciones_ml[:3]
    elif es_parpadeo_check and diagnostico_predictivo != "Falla en bujias o bobinas de encendido (misfire)":
        diagnostico_predictivo = "Falla en bujias o bobinas de encendido (misfire)"
        confianza = max(confianza, 0.70)
        if predicciones_ml:
            predicciones_ml.insert(0, PrediccionML(falla=diagnostico_predictivo, probabilidad=confianza))
            predicciones_ml = predicciones_ml[:3]

    if (
        gestor._es_perdida_potencia_bajo_carga(texto_evaluar)
        and modo_falla_combustible == "solo_gas"
        and confianza < settings.diagnostic.confidence_threshold
        and not tiene_dtc
        and not tiene_componente_especifico
    ):
        diagnostico_predictivo = "Sistema GNV/GLP: diferenciar calibración, presión, filtros e inyectores"

    tiempo_ml_ms = max(0, int((time.perf_counter() - inicio_ml) * 1000))

    # Si el usuario ya descartó hipótesis previamente, excluirlas para no sugerirlas de nuevo
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

    # Auto-Preguntas Técnicas de Descarte para 100% de Asertividad
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

    # PASO 2: Motor RAG Multiseñal Híbrido
    inicio_rag = time.perf_counter()
    from src.core.diagnostico.taxonomia_sistemas import obtener_macro_sistema
    macro_sis_ml = obtener_macro_sistema(diagnostico_predictivo) if diagnostico_predictivo else None
    dtcs_encontrados = [d.upper() for d in re.findall(r"\b[pbcu]\d{4}\b", texto_evaluar, re.IGNORECASE)]

    meta_rag_dict = {}
    if hasattr(gestor.motor_rag, "recuperar_procedimiento_hibrido"):
        contexto_manual, titulo_manual, similitud_rag, meta_rag_dict = gestor.motor_rag.recuperar_procedimiento_hibrido(
            consulta=texto_evaluar,
            macro_sistema=macro_sis_ml,
            top_fallas=[p.model_dump() for p in predicciones_ml] if predicciones_ml else None,
            codigos_dtc=dtcs_encontrados,
            marca=marca_evaluar,
            modelo=None,
        )
    elif hasattr(gestor.motor_rag, "recuperar_contexto_con_similitud"):
        contexto_manual, titulo_manual, similitud_rag = gestor.motor_rag.recuperar_contexto_con_similitud(texto_ml)
        if similitud_rag < settings.diagnostic.rag_min_similarity:
            c2, t2, s2 = gestor.motor_rag.recuperar_contexto_con_similitud(texto_evaluar)
            if s2 > similitud_rag:
                contexto_manual, titulo_manual, similitud_rag = c2, t2, s2
    else:
        contexto_manual, titulo_manual = gestor.motor_rag.recuperar_contexto(texto_ml)
        similitud_rag = 0.0
    tiempo_rag_ms = max(0, int((time.perf_counter() - inicio_rag) * 1000))

    rag_valido = (
        contexto_manual
        and "No se encontró" not in contexto_manual
        and "Manual técnico no indexado" not in contexto_manual
        and "Coincidencia baja" not in titulo_manual
        and "Desconocido" not in titulo_manual
        and "Error" not in titulo_manual
    )

    # PASO 2.5: Fusión Multiseñal y Prioridad de Evidencia (DTC + Metrología Física + Descarte + RAG)
    from src.core.diagnostico.politica_fusion import PoliticaFusionDiagnostica, ResultadoFusion
    if not diagnostico_predictivo.startswith("Sistema GNV/GLP"):
        resultado_fusion = PoliticaFusionDiagnostica.fusionar_evidencia(
            sintoma_texto=texto_evaluar,
            predicciones_ml=[p.model_dump() for p in predicciones_ml] if predicciones_ml else [],
            macro_sistema_ml=macro_sis_ml,
            rag_meta=meta_rag_dict or {},
            rag_similitud=similitud_rag,
            codigos_dtc=dtcs_encontrados,
        )
        diagnostico_predictivo = resultado_fusion.falla_principal
        confianza = resultado_fusion.confianza_final
        if resultado_fusion.diferenciales:
            nuevas_preds = [PrediccionML(falla=diagnostico_predictivo, probabilidad=confianza)]
            for dif in resultado_fusion.diferenciales:
                nuevas_preds.append(PrediccionML(falla=dif["falla"], probabilidad=dif["probabilidad"]))
            predicciones_ml = nuevas_preds
    else:
        resultado_fusion = ResultadoFusion(
            falla_principal=diagnostico_predictivo,
            confianza_final=confianza,
            diferenciales=[],
            evidencia_confirmada=["Falla exclusiva en modo GNV/GLP confirmada"],
            componentes_descartados=[],
            datos_faltantes=[],
            origen_decision="COMBUSTIBLE_DUAL",
        )

    if confianza < 0.10:
        if rag_valido:
            diagnostico_predictivo = f"Hipótesis ML de baja confianza: {diagnostico_predictivo}"
            requiere_revision_humana = True
        else:
            return ResultadoDiagnostico(
                respuesta_texto=(
                    "⚠️ **Síntoma no reconocido con suficiente certeza (< 10%)**\n\n"
                    "El modelo de Machine Learning requiere una descripción un poco más detallada del síntoma.\n"
                    "Por favor, indique el sistema o componente afectado (ej. **frenos**, **motor**, "
                    "**carrocería/puertas**, **encendido/batería**, **transmisión** o **acelerador/mínimo**)."
                ),
                diagnostico_ml="Baja Confianza / Indeterminado",
                confianza_ml=confianza,
                contexto_manual="",
                titulo_manual="",
                similitud_rag=similitud_rag,
                requiere_revision_humana=True,
                modo_diagnostico="baja_confianza",
                predicciones_ml=predicciones_ml,
                tiempo_ml_ms=tiempo_ml_ms,
                tiempo_rag_ms=tiempo_rag_ms,
                tiempo_total_ms=max(0, int((time.perf_counter() - inicio_total) * 1000)),
            )
    else:
        requiere_revision_humana = confianza < settings.diagnostic.confidence_threshold

    if rag_valido and not getattr(gestor.motor_rag, "corpus_validado", False):
        requiere_revision_humana = True

    # Enriquecimiento con Catálogo Oficial DTC (18,805 códigos en SQLite)
    info_dtc_texto = ""
    if tiene_dtc:
        dtc_service = ServiceContainer.get_dtc_service()
        codigos_detectados = dtc_service.extraer_codigos_en_texto(texto_evaluar)
        if codigos_detectados:
            defs_dtc = []
            for c in codigos_detectados[:2]:
                info_dtc = dtc_service.consultar_codigo(c, marca=marca_evaluar)
                if info_dtc:
                    defs_dtc.append(f"• Código {info_dtc['codigo']} ({info_dtc['marca']}): {info_dtc['descripcion']}")
            if defs_dtc:
                info_dtc_texto = "\n".join(defs_dtc)
                bloque_dtc = "DEFINICIÓN OFICIAL DEL CÓDIGO (OBD-II):\n" + info_dtc_texto + "\n\n"
                contexto_manual = bloque_dtc + (contexto_manual or "")

    perfil_vehiculo_str = f"Vehículo: {marca_evaluar or 'Genérico'} | Placa: {placa_evaluar or 'N/A'}"
    if clave_sesion:
        ses_act = gestor.session_manager.obtener_sesion(clave_sesion)
        if ses_act and getattr(ses_act, "perfil_vehiculo", None):
            pv_fmt = gestor._formatear_perfil_vehiculo(ses_act.perfil_vehiculo)
            if pv_fmt:
                perfil_vehiculo_str = pv_fmt

    # PASO 3: Gemini LLM
    inicio_llm = time.perf_counter()
    respuesta_explicativa, uso_llm = gestor._generar_respuesta_con_metadatos(
        pregunta=texto_evaluar,
        diagnostico_ml=diagnostico_predictivo,
        confianza_ml=confianza,
        contexto_manual=contexto_manual,
        titulo_manual=titulo_manual,
        requiere_revision_humana=requiere_revision_humana,
        remitente=remitente,
        proveedor=proveedor,
        taller_id=taller_id,
        usuario_id=usuario_id,
        conversacion_id=conversacion_id,
        slot_gemini_preconcedido=slot_gemini_preconcedido,
        diferir_encolado_persistente=diferir_encolado_persistente,
        predicciones_ml=predicciones_ml,
        dtc_info=info_dtc_texto,
        perfil_vehiculo=perfil_vehiculo_str,
        evidencia_confirmada=resultado_fusion.evidencia_confirmada,
        componentes_descartados=resultado_fusion.componentes_descartados,
        datos_faltantes=resultado_fusion.datos_faltantes,
    )
    tiempo_llm_ms = max(0, int((time.perf_counter() - inicio_llm) * 1000))

    gestor._registrar_en_tracker(
        placa=placa_evaluar or "DESCONOCIDO",
        marca_modelo=marca_evaluar or "Generico",
        sintoma=texto_evaluar,
        diagnostico_ml=diagnostico_predictivo,
        campos_completos=1,
    )

    if clave_sesion:
        gestor.session_manager.obtener_o_crear_sesion(clave_sesion).estado = "completo"

    from src.core.diagnostico.politica_seguridad import PoliticaSeguridad

    respuesta_con_seguridad = PoliticaSeguridad.enriquecer_respuesta_seguridad(
        respuesta_texto=respuesta_explicativa,
        texto_usuario=f"{texto_usuario} {texto_evaluar}",
        diagnostico_ml=diagnostico_predictivo,
    )

    modo = uso_llm.get("modo", "completo_ml_rag_llm" if uso_llm.get("usado") else "diagnostico_degradado_ml_rag")

    resultado_final = ResultadoDiagnostico(
        respuesta_texto=respuesta_con_seguridad,
        diagnostico_ml=diagnostico_predictivo,
        confianza_ml=confianza,
        contexto_manual=contexto_manual,
        titulo_manual=titulo_manual,
        similitud_rag=similitud_rag,
        requiere_revision_humana=requiere_revision_humana,
        modo_diagnostico=modo,
        solicitud_id=uso_llm.get("solicitud_id"),
        llm_usado=uso_llm.get("usado", False),
        llm_modelo=uso_llm.get("modelo"),
        tokens_entrada=uso_llm.get("tokens_entrada", 0),
        tokens_salida=uso_llm.get("tokens_salida", 0),
        posicion_cola=uso_llm.get("posicion_cola", 0),
        tiempo_espera_cola=uso_llm.get("tiempo_espera_cola", 0.0),
        sintoma_evaluado=texto_evaluar,
        predicciones_ml=predicciones_ml,
        tiempo_ml_ms=tiempo_ml_ms,
        tiempo_rag_ms=tiempo_rag_ms,
        tiempo_llm_ms=tiempo_llm_ms,
        tiempo_total_ms=max(0, int((time.perf_counter() - inicio_total) * 1000)),
    )

    diagnostico_cache.guardar(clave_cache, resultado_final)
    return resultado_final
