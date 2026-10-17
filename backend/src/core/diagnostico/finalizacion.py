"""Validación final de evidencias, generación LLM y telemetría del diagnóstico."""

from __future__ import annotations

import time
from typing import Any

from src.config import settings
from src.core.diagnostic_cache import diagnostico_cache
from src.core.diagnostico.coherencia_evidencia import (
    documento_compatible,
    limitar_respuesta,
    preparar_contexto_rag_para_llm,
)
from src.core.diagnostico.enrutador_sistema import (
    ETIQUETAS_AREA,
    falla_coincide_con_areas,
    filtrar_causas,
    respuesta_menciona_causa_fuera_de_sistema,
)
from src.core.diagnostico.models import ResultadoDiagnostico
from src.infrastructure.container import ServiceContainer


def finalizar_diagnostico(
    *,
    gestor: Any,
    texto_usuario: Any,
    texto_evaluar: Any,
    diagnostico_predictivo: Any,
    confianza: Any,
    predicciones_ml: Any,
    predicciones_originales: Any,
    predicciones_svm_raw: Any,
    motivo_prioridad: Any,
    contexto_manual: Any,
    titulo_manual: Any,
    similitud_rag: Any,
    meta_rag_dict: Any,
    resultado_fusion: Any,
    rag_valido: Any,
    areas_consulta: Any,
    diagnostico_forzado: Any,
    sistema_activo: Any,
    tiene_dtc: Any,
    marca_evaluar: Any,
    placa_evaluar: Any,
    clave_sesion: Any,
    remitente: Any,
    proveedor: Any,
    taller_id: Any,
    usuario_id: Any,
    conversacion_id: Any,
    slot_gemini_preconcedido: Any,
    diferir_encolado_persistente: Any,
    tiempo_ml_ms: Any,
    tiempo_rag_ms: Any,
    inicio_total: Any,
    clave_cache: Any,
    case_id: Any,
) -> ResultadoDiagnostico:
    """Cierra el pipeline sin cambiar la selección ni las probabilidades del SVM."""
    from src.core.diagnostico.rag_hypothesis_compatibility import procedimiento_apoya_hipotesis

    falla_rag = (meta_rag_dict or {}).get("falla")
    falla_desconocida_o_abstencion = (
        not diagnostico_predictivo
        or diagnostico_predictivo in ("DESCONOCIDO", "Baja Confianza / Indeterminado")
        or str(diagnostico_predictivo).startswith("Sin hipótesis ML pertinente")
    )
    contradiccion_falla_rag = bool(
        falla_rag
        and not falla_desconocida_o_abstencion
        and not procedimiento_apoya_hipotesis(
            diagnostico_predictivo, titulo_manual, meta_rag_dict or {},
        )
    )

    if (
        contradiccion_falla_rag
        or not documento_compatible(texto_evaluar, titulo_manual, contexto_manual)
    ):
        contexto_manual, titulo_manual, similitud_rag = "", "Sin procedimiento compatible verificado", 0.0
        rag_valido = False

    es_hipotesis_regla = bool(
        predicciones_ml
        and getattr(predicciones_ml[0], "origen_probabilidad", "") == "REGLA"
    )

    probabilidad_original = (
        predicciones_ml[0].statistical_probability if predicciones_ml else None
    )
    confianza_abstencion = probabilidad_original if probabilidad_original is not None else confianza
    if confianza_abstencion < 0.10 and not areas_consulta and not es_hipotesis_regla:
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
                motivo_abstencion="CONFIANZA_INSUFICIENTE_SIN_RAG",
                predicciones_ml=predicciones_ml,
                predicciones_svm_raw=predicciones_svm_raw,
                tiempo_ml_ms=tiempo_ml_ms,
                tiempo_rag_ms=tiempo_rag_ms,
                tiempo_total_ms=max(0, int((time.perf_counter() - inicio_total) * 1000)),
            )
    elif confianza < 0.10:
        requiere_revision_humana = True
    else:
        requiere_revision_humana = confianza < settings.diagnostic.confidence_threshold

    if rag_valido and not getattr(gestor.motor_rag, "corpus_validado", False):
        requiere_revision_humana = True

    if areas_consulta and not diagnostico_forzado and not es_hipotesis_regla:
        predicciones_en_area = filtrar_causas(sistema_activo, predicciones_ml, texto_evaluar)
        predicciones_en_area = [
            prediccion
            for prediccion in predicciones_en_area
            if falla_coincide_con_areas(prediccion.falla, areas_consulta)
        ][:3]
        if not predicciones_en_area:
            etiquetas = ", ".join(ETIQUETAS_AREA.get(area, area) for area in areas_consulta)
            if not diagnostico_predictivo.startswith("Sistema GNV/GLP"):
                diagnostico_predictivo = f"Sin hipótesis ML pertinente para {etiquetas}"
            confianza = 0.0
            predicciones_ml = []
            requiere_revision_humana = True
        else:
            predicciones_ml = predicciones_en_area
            diagnostico_predictivo = predicciones_en_area[0].falla
            confianza = predicciones_en_area[0].probabilidad

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

    inicio_llm = time.perf_counter()
    predicciones_llm = predicciones_ml
    diagnostico_llm = diagnostico_predictivo
    confianza_llm = confianza
    contexto_llm, titulo_llm = preparar_contexto_rag_para_llm(
        contexto_manual,
        titulo_manual,
        meta_rag_dict,
        bool(getattr(gestor.motor_rag, "corpus_validado", False)),
    )
    respuesta_explicativa, uso_llm = gestor._generar_respuesta_con_metadatos(
        pregunta=texto_evaluar,
        diagnostico_ml=diagnostico_llm,
        confianza_ml=confianza_llm,
        contexto_manual=contexto_llm,
        titulo_manual=titulo_llm,
        requiere_revision_humana=requiere_revision_humana,
        remitente=remitente,
        proveedor=proveedor,
        taller_id=taller_id,
        usuario_id=usuario_id,
        conversacion_id=conversacion_id,
        slot_gemini_preconcedido=slot_gemini_preconcedido,
        diferir_encolado_persistente=diferir_encolado_persistente,
        case_id=case_id,
        predicciones_ml=predicciones_llm,
        dtc_info=info_dtc_texto,
        perfil_vehiculo=perfil_vehiculo_str,
        evidencia_confirmada=resultado_fusion.evidencia_confirmada,
        componentes_descartados=resultado_fusion.componentes_descartados,
        datos_faltantes=resultado_fusion.datos_faltantes,
    )
    if sistema_activo and sistema_activo != "ambiguo" and respuesta_menciona_causa_fuera_de_sistema(
        sistema_activo,
        respuesta_explicativa,
        evidencia=texto_evaluar,
    ):
        etiqueta = {
            "refrigeracion": "refrigeración",
            "combustible_admision": "combustible/admisión",
            "encendido": "encendido",
            "frenos": "frenos",
            "transmision": "transmisión",
            "suspension_direccion": "suspensión/dirección",
            "electrico_ecu": "eléctrico/ECU",
        }.get(sistema_activo, "sistema indicado")
        respuesta_explicativa = (
            f"Mantendré el análisis en {etiqueta} para no mezclar causas de otros sistemas. "
            "No hay una hipótesis compatible suficientemente sustentada todavía. "
            "¿Qué resultado observaste en la última comprobación realizada?"
        )
    respuesta_explicativa, respuesta_limitada = limitar_respuesta(
        respuesta_explicativa,
        predicciones_llm,
        motivo_prioridad,
        sin_documento=(
            not rag_valido
            or not getattr(gestor.motor_rag, "corpus_validado", False)
        ),
        contexto_verificado=f"{contexto_llm}\n{info_dtc_texto}",
        pregunta=texto_evaluar,
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
    prediccion_seleccionada = next(
        (p for p in predicciones_ml if p.falla == diagnostico_predictivo),
        None,
    )
    origen_confianza = (
        prediccion_seleccionada.origen_probabilidad
        if prediccion_seleccionada is not None
        else "ORQUESTADOR_SIN_PROBABILIDAD_SVM"
    )

    resultado_final = ResultadoDiagnostico(
        respuesta_texto=respuesta_con_seguridad,
        diagnostico_ml=diagnostico_predictivo,
        confianza_ml=confianza,
        origen_confianza=origen_confianza,
        contexto_manual=contexto_manual,
        titulo_manual=titulo_manual,
        contexto_manual_verificado=contexto_llm,
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
        predicciones_ml_raw=predicciones_originales,
        predicciones_svm_raw=predicciones_svm_raw,
        motivo_prioridad=motivo_prioridad,
        respuesta_limitada=respuesta_limitada,
        tiempo_ml_ms=tiempo_ml_ms,
        tiempo_rag_ms=tiempo_rag_ms,
        tiempo_llm_ms=tiempo_llm_ms,
        tiempo_total_ms=max(0, int((time.perf_counter() - inicio_total) * 1000)),
    )

    if clave_cache and resultado_final.modo_diagnostico not in (
        "en_cola_gemini",
        "consulta_tecnica_en_cola",
    ):
        diagnostico_cache.guardar(clave_cache, resultado_final)
    return resultado_final
