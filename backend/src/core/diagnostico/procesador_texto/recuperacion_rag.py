"""Recuperación RAG multiseñal y fusión de evidencia diagnóstica."""

from __future__ import annotations

import re
import time
from typing import Any, List, Optional, Tuple

from src.config import settings
from src.core.diagnostico.coherencia_evidencia import (
    documento_compatible,
    preparar_contexto_rag_para_llm,
)
from src.core.diagnostico.models import PrediccionML
from src.core.diagnostico.politica_fusion import PoliticaFusionDiagnostica, ResultadoFusion
from src.core.diagnostico.taxonomia_sistemas import obtener_macro_sistema


def ejecutar_recuperacion_y_fusion_rag(
    gestor: Any,
    texto_evaluar: str,
    diagnostico_predictivo: str,
    confianza: float,
    predicciones_ml: List[PrediccionML],
    texto_ml: str,
    marca_evaluar: Optional[str],
) -> Tuple[str, str, float, dict, bool, ResultadoFusion, str, float, List[PrediccionML], int]:
    """Recupera el procedimiento técnico del manual RAG y ejecuta la fusión multiseñal.

    Retorna:
    (contexto_manual, titulo_manual, similitud_rag, meta_rag_dict, rag_valido,
     resultado_fusion, diagnostico_predictivo, confianza, predicciones_ml, tiempo_rag_ms)
    """
    inicio_rag = time.perf_counter()
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
    rag_corpus_validado = bool(getattr(gestor.motor_rag, "corpus_validado", False))
    contexto_rag_validado, _ = preparar_contexto_rag_para_llm(
        contexto_manual,
        titulo_manual,
        meta_rag_dict,
        rag_corpus_validado,
    )
    falla_rag = str((meta_rag_dict or {}).get("falla") or "").strip()
    macro_rag_declarado = str(
        (meta_rag_dict or {}).get("macro_sistema")
        or (meta_rag_dict or {}).get("sistema")
        or ""
    ).strip().upper()
    macro_rag = obtener_macro_sistema(falla_rag) if falla_rag else macro_rag_declarado
    sistema_rag_compatible = bool(
        macro_sis_ml
        and macro_rag == macro_sis_ml
        and (not macro_rag_declarado or macro_rag_declarado == macro_sis_ml)
    )
    umbral_evidencia_rag = max(0.80, float(settings.diagnostic.rag_min_similarity))
    rag_evidencia_validada = bool(
        rag_valido
        and contexto_rag_validado
        and documento_compatible(texto_evaluar, titulo_manual, contexto_manual)
        and sistema_rag_compatible
        and similitud_rag >= umbral_evidencia_rag
    )

    # Fusión multiseñal
    if not diagnostico_predictivo.startswith("Sistema GNV/GLP"):
        predicciones_pre_fusion = list(predicciones_ml)
        resultado_fusion = PoliticaFusionDiagnostica.fusionar_evidencia(
            sintoma_texto=texto_evaluar,
            predicciones_ml=[p.model_dump() for p in predicciones_ml] if predicciones_ml else [],
            macro_sistema_ml=macro_sis_ml,
            rag_meta=meta_rag_dict or {},
            rag_similitud=similitud_rag,
            codigos_dtc=dtcs_encontrados,
            rag_evidencia_validada=rag_evidencia_validada,
        )
        diagnostico_predictivo = resultado_fusion.falla_principal
        probabilidades_svm = {
            pred.falla: pred.probabilidad
            for pred in predicciones_pre_fusion
            if pred.origen_probabilidad in ("SVM", "SVM_ORIGINAL_REORDENADO_REGLA")
        }
        fuentes_candidatas = {
            pred.falla: pred.origen_probabilidad for pred in predicciones_pre_fusion
        }
        confianza_principal_svm = probabilidades_svm.get(diagnostico_predictivo)
        origen_principal = (
            fuentes_candidatas.get(diagnostico_predictivo, "SVM")
            if confianza_principal_svm is not None
            else fuentes_candidatas.get(
                diagnostico_predictivo,
                resultado_fusion.origen_confianza,
            )
        )
        nuevas_preds = [PrediccionML(
            falla=diagnostico_predictivo,
            probabilidad=(
                confianza_principal_svm
                if confianza_principal_svm is not None
                else 0.0
            ),
            origen_probabilidad=origen_principal,
        )]
        for dif in resultado_fusion.diferenciales:
            nuevas_preds.append(PrediccionML(
                falla=dif["falla"],
                probabilidad=float(dif.get("probabilidad", 0.0) or 0.0),
                origen_probabilidad=dif.get("origen_probabilidad", "SVM"),
            ))
        predicciones_ml = nuevas_preds
        confianza = (
            float(confianza_principal_svm)
            if origen_principal in ("SVM", "SVM_ORIGINAL_REORDENADO_REGLA") and confianza_principal_svm is not None
            else 0.0
        )
    else:
        resultado_fusion = ResultadoFusion(
            falla_principal=diagnostico_predictivo,
            confianza_final=confianza,
            diferenciales=[],
            evidencia_confirmada=["Falla exclusiva en modo GNV/GLP confirmada"],
            componentes_descartados=[],
            datos_faltantes=[],
            origen_decision="COMBUSTIBLE_DUAL",
            origen_confianza="REGLA",
        )

    return (
        contexto_manual,
        titulo_manual,
        similitud_rag,
        meta_rag_dict or {},
        bool(rag_valido),
        resultado_fusion,
        diagnostico_predictivo,
        confianza,
        predicciones_ml,
        tiempo_rag_ms,
    )
