"""Presentación del historial REST, separada del flujo de procesamiento."""
from datetime import datetime
from typing import Optional

from src.config import settings
from src.interfaces.api.v1.dtos.diagnosticos import EtapaProcesamientoDTO, ItemDiagnosticoDTO, PrediccionMLDTO


def _es_procedimiento_rag_real(valor: Optional[str]) -> bool:
    if not valor or not valor.strip():
        return False
    normalizado = valor.strip().lower()
    indicadores_ausencia = (
        "sin procedimiento rag",
        "inspección directa de componentes",
        "no se encontró un procedimiento",
        "no se encontro un procedimiento",
        "manual técnico no indexado",
        "manual tecnico no indexado",
        "error al buscar",
    )
    return not any(indicador in normalizado for indicador in indicadores_ausencia)


def _fecha_confirmacion_tecnica(diagnostico, trazabilidad: dict) -> Optional[str]:
    if diagnostico.estado not in {"confirmado", "descartado"}:
        return None
    validacion = trazabilidad.get("validacion_tecnica") or {}
    fecha_iso = validacion.get("validado_en")
    if fecha_iso:
        try:
            return datetime.fromisoformat(str(fecha_iso)).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass
    return diagnostico.actualizado_en.strftime("%Y-%m-%d %H:%M") if diagnostico.actualizado_en else None


def presentar_historial(diag_db_list):
    res_items = []
    for d in diag_db_list:
        placa_str = f"***-{d.vehiculo.placa_ultimos4}" if d.vehiculo and d.vehiculo.placa_ultimos4 else "Sin Placa Registrada"
        marca_str = f"{d.vehiculo.marca} {d.vehiculo.modelo}" if d.vehiculo and d.vehiculo.marca else "Vehículo No Registrado"
        confianza_val = round(float(d.confianza) * 100, 1) if d.confianza is not None else 0.0
        similitud_val = round(float(d.similitud_rag) * 100, 1) if d.similitud_rag is not None else 0.0
        duracion_val = int(d.duracion_ms) if d.duracion_ms is not None else 0

        hip = d.hipotesis[0] if d.hipotesis else None
        proc_rag = "Sin procedimiento RAG registrado"
        fuente_ref = None

        if hip:
            if _es_procedimiento_rag_real(hip.prueba_recomendada):
                proc_rag = hip.prueba_recomendada
            elif hip.evidencia and "RAG:" in hip.evidencia:
                proc_rag = hip.evidencia

            if hip.evidencia and "Fuente:" in hip.evidencia:
                fuente_ref = hip.evidencia.split("Fuente:", 1)[1].split(". Corpus:", 1)[0].strip()

        if not fuente_ref and d.version_corpus_rag:
            fuente_ref = f"Corpus local: {d.version_corpus_rag} (fuente documental no registrada)"

        traza = d.trazabilidad or {}
        duracion_val = int(traza.get("tiempo_total_ms", duracion_val))
        predicciones_traza = traza.get("predicciones_ml") or []
        if predicciones_traza:
            predicciones = [
                PrediccionMLDTO(
                    orden=indice,
                    falla=str(item.get("falla", "Sin clasificación")),
                    probabilidad=round(float(item.get("probabilidad", 0)) * 100, 1),
                    origen_probabilidad=str(item.get("origen_probabilidad", "NO_REGISTRADO")),
                    **{key: item.get(key) for key in (
                        "statistical_probability", "operational_score", "raw_svm_score", "prediction_source",
                        "class_id", "model_version", "taxonomy_version",
                    )},
                )
                for indice, item in enumerate(predicciones_traza[:3], start=1)
            ]
        else:
            predicciones = [
                PrediccionMLDTO(
                    orden=hipotesis.orden,
                    falla=hipotesis.falla_probable,
                    probabilidad=round(float(hipotesis.confianza or 0) * 100, 1),
                    origen_probabilidad="NO_REGISTRADO",
                )
                for hipotesis in d.hipotesis[:3]
            ]
            if not predicciones:
                predicciones = [
                    PrediccionMLDTO(
                        orden=1,
                        falla=d.falla_predicha or "Sin falla predicha",
                        probabilidad=confianza_val,
                        origen_probabilidad="NO_REGISTRADO",
                    )
                ]

        etapas_raw = traza.get("etapas") or []
        etapas = []
        for etapa_raw in etapas_raw:
            etapa = dict(etapa_raw)
            if etapa.get("clave") == "ml":
                etapa["nombre"] = settings.model_algorithm
            etapas.append(EtapaProcesamientoDTO(**etapa))
        if not etapas:
            etapas = [
                EtapaProcesamientoDTO(
                    clave="ml",
                    nombre="Clasificación ML registrada",
                    estado="completado",
                    duracion_ms=duracion_val,
                    detalle="Diagnóstico histórico: solo se conserva el tiempo total.",
                ),
                EtapaProcesamientoDTO(
                    clave="rag",
                    nombre="Búsqueda RAG en manuales",
                    estado="completado" if similitud_val > 0 else "sin_resultado",
                    detalle=fuente_ref,
                ),
                EtapaProcesamientoDTO(
                    clave="llm",
                    nombre="Síntesis técnica Gemini",
                    estado="completado" if d.sintesis_llm else "sin_registro",
                ),
            ]
        gemini = traza.get("gemini") or {}

        cliente_nom = "Cliente WhatsApp"
        cliente_tel = None
        if d.conversacion and d.conversacion.usuario:
            cliente_nom = d.conversacion.usuario.nombres or "Cliente WhatsApp"
            cliente_tel = f"+51 *** *** {d.conversacion.usuario.whatsapp_ultimos4}"
        elif d.vehiculo and d.vehiculo.registrado_por:
            cliente_nom = d.vehiculo.registrado_por.nombres or "Cliente WhatsApp"
            cliente_tel = f"+51 *** *** {d.vehiculo.registrado_por.whatsapp_ultimos4}"

        res_items.append(
            ItemDiagnosticoDTO(
                id=str(d.id),
                sintoma_original=d.sintoma_original,
                sintoma_normalizado=d.sintoma_normalizado or d.sintoma_original,
                falla_predicha=d.falla_predicha or "Sin falla predicha",
                confianza=confianza_val,
                origen_confianza=traza.get("origen_confianza", "NO_REGISTRADO"),
                similitud_rag=similitud_val,
                modo_diagnostico=d.modo_diagnostico or "completo_ml_rag_llm",
                estado=d.estado or "generado",
                fuente=d.fuente,
                mecanico_id=str(d.mecanico_id),
                mecanico_nombre=d.mecanico.nombres if d.mecanico else "Mecánico No Asignado",
                cliente_nombre=cliente_nom,
                cliente_telefono=cliente_tel,
                placa_vehiculo=placa_str,
                marca_modelo=marca_str,
                fecha_hora=d.creado_en.strftime("%Y-%m-%d %H:%M") if d.creado_en else "Fecha no registrada",
                duracion_ms=duracion_val,
                procedimiento_rag=proc_rag,
                fuente_manual=fuente_ref,
                version_corpus_rag=d.version_corpus_rag,
                tiempo_gravedad=d.conclusion_mecanico or "Sin conclusión registrada",
                sintesis_llm=d.sintesis_llm,
                notas_mecanico=d.conclusion_mecanico,
                fecha_confirmacion=_fecha_confirmacion_tecnica(d, traza),
                predicciones_ml=predicciones,
                etapas_procesamiento=etapas,
                version_modelo_ml=d.version_modelo_ml,
                llm_usado=bool(gemini.get("usado", bool(d.sintesis_llm))),
                llm_modelo=gemini.get("modelo"),
                tokens_entrada=int(gemini.get("tokens_entrada", 0)),
                tokens_salida=int(gemini.get("tokens_salida", 0)),
                conversacion_id=str(d.conversacion_id) if d.conversacion_id else None,
                desde_cache=bool(traza.get("desde_cache", False)),
            )
        )
    return res_items
