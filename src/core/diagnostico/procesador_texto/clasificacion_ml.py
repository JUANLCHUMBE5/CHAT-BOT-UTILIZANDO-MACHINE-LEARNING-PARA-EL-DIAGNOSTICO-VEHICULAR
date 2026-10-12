"""Inferencia de Machine Learning supervisado y especialización por áreas de avería."""

from __future__ import annotations

import re
import time
from typing import Any, List, Optional, Tuple

from src.config import settings
from src.core.diagnostico.coherencia_evidencia import priorizar_evidencia
from src.core.diagnostico.enrutador_sistema import (
    ETIQUETAS_AREA,
    falla_coincide_con_areas,
    filtrar_causas,
)
from src.core.diagnostico.models import PrediccionML


def ejecutar_clasificacion_ml(
    gestor: Any,
    texto_evaluar: str,
    diagnostico_forzado: Optional[str],
    clave_sesion: Optional[str],
    areas_consulta: List[str],
    sistema_activo: Optional[str],
    modo_falla_combustible: Optional[str],
    tiene_dtc: bool,
    tiene_componente_especifico: bool,
) -> Tuple[str, float, List[PrediccionML], List[PrediccionML], str, int]:
    """Ejecuta inferencia ML, filtra por áreas y aplica especializaciones mecánicas.

    Retorna: (diagnostico_predictivo, confianza, predicciones_ml, predicciones_originales, motivo_enrutamiento, tiempo_ml_ms)
    """
    inicio_ml = time.perf_counter()
    texto_ml = gestor._purificar_sintoma_para_vectorizador_ml(texto_evaluar)

    if diagnostico_forzado:
        diagnostico_predictivo = diagnostico_forzado
        confianza = 0.80
        predicciones_ml = [PrediccionML(
            falla=diagnostico_forzado,
            probabilidad=0.0,
            origen_probabilidad="REGLA",
        )]
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

        for alt_nombre in alts_fallas[:2]:
            predicciones_ml.append(
                PrediccionML(
                    falla=alt_nombre,
                    probabilidad=0.0,
                    origen_probabilidad="REGLA",
                )
            )
    elif hasattr(gestor.modelo_ml, "predecir_top_fallas"):
        limite_candidatos = 12 if areas_consulta else 8
        predicciones_raw = gestor.modelo_ml.predecir_top_fallas(
            texto_ml,
            limite=limite_candidatos,
        )
        predicciones_ml = [PrediccionML(**item) for item in predicciones_raw]
        diagnostico_predictivo = predicciones_ml[0].falla if predicciones_ml else "DESCONOCIDO"
        confianza = predicciones_ml[0].probabilidad if predicciones_ml else 0.0
    elif hasattr(gestor.modelo_ml, "predecir_top_k"):
        limite_candidatos = 12 if areas_consulta else 8
        predicciones_raw = gestor.modelo_ml.predecir_top_k(
            texto_ml,
            k=limite_candidatos,
        )
        predicciones_ml = [
            PrediccionML(
                falla=str(item.get("falla", item.get("clase", ""))),
                probabilidad=float(item.get("probabilidad", item.get("score", 0.0))),
            )
            for item in predicciones_raw
        ]
        diagnostico_predictivo = predicciones_ml[0].falla if predicciones_ml else "DESCONOCIDO"
        confianza = predicciones_ml[0].probabilidad if predicciones_ml else 0.0
    else:
        diagnostico_predictivo, confianza = gestor.modelo_ml.predecir_falla_con_confianza(texto_ml)
        predicciones_ml = [PrediccionML(falla=diagnostico_predictivo, probabilidad=confianza)]

    predicciones_originales = [p.model_copy() for p in predicciones_ml]
    motivo_enrutamiento_area = ""
    if areas_consulta and not diagnostico_forzado:
        compatibles_area = filtrar_causas(sistema_activo, predicciones_ml, texto_evaluar)
        compatibles_area = [
            prediccion
            for prediccion in compatibles_area
            if falla_coincide_con_areas(prediccion.falla, areas_consulta)
        ]
        if compatibles_area:
            compatibles_area, _ = priorizar_evidencia(texto_evaluar, compatibles_area)
            predicciones_ml = compatibles_area[:3]
            diagnostico_predictivo = compatibles_area[0].falla
            confianza = compatibles_area[0].probabilidad
            motivo_enrutamiento_area = (
                "Enrutamiento por señal explícita del mecánico: "
                + ", ".join(ETIQUETAS_AREA.get(area, area) for area in areas_consulta)
                + "; probabilidades SVM originales conservadas."
            )
    elif sistema_activo and not diagnostico_forzado:
        compatibles_sis = filtrar_causas(sistema_activo, predicciones_ml, texto_evaluar)
        if compatibles_sis:
            predicciones_ml = compatibles_sis[:3]
            diagnostico_predictivo = compatibles_sis[0].falla
            confianza = compatibles_sis[0].probabilidad
        else:
            predicciones_ml = predicciones_ml[:3]
    else:
        predicciones_ml = predicciones_ml[:3]

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
            predicciones_ml[0] = PrediccionML(
                falla=diagnostico_predictivo,
                probabilidad=0.0,
                origen_probabilidad="REGLA",
            )

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
            predicciones_ml.insert(0, PrediccionML(
                falla=diagnostico_predictivo,
                probabilidad=0.0,
                origen_probabilidad="REGLA",
            ))
            predicciones_ml = predicciones_ml[:3]

    if areas_consulta and not diagnostico_forzado:
        compatibles_filtradas = filtrar_causas(sistema_activo, predicciones_originales, texto_evaluar)
        compatibles_filtradas = [
            prediccion
            for prediccion in compatibles_filtradas
            if falla_coincide_con_areas(prediccion.falla, areas_consulta)
        ][:3]
        if compatibles_filtradas:
            predicciones_ml = compatibles_filtradas
            diagnostico_predictivo = predicciones_ml[0].falla
            confianza = predicciones_ml[0].probabilidad
        elif not predicciones_ml:
            etiquetas_area = ", ".join(
                ETIQUETAS_AREA.get(area, area) for area in areas_consulta
            )
            diagnostico_predictivo = f"Sin hipótesis ML pertinente para {etiquetas_area}"
            confianza = 0.0
        else:
            diagnostico_predictivo = predicciones_ml[0].falla
            confianza = predicciones_ml[0].probabilidad

    # Especialización técnica: parpadeo de Check Engine / luz del motor bajo carga (Misfire severo)
    mencion_bobina_falla = any(
        p in texto_evaluar.lower()
        for p in (
            "bobina falla", "cambiar la bobina", "cambie la bobina individual",
            "al cambiar la bobina", "bobina no manda", "bobina mala", "falla de chispa",
            "sin chispa", "no genera chispa", "bobina individual"
        )
    )
    descarte_ambos_ignicion = any(
        p in texto_evaluar.lower()
        for p in (
            "cambie bujias y bobinas", "bujias y bobinas cambiadas", "bujias y bobinas nuevas",
            "descarte bujias y bobinas", "probe bujias y bobinas", "cambie cables bujias y bobinas"
        )
    )
    descarte_ignicion_total = descarte_ambos_ignicion or (
        any(
            p in texto_evaluar.lower()
            for p in (
                "cambie bujias", "cambie bobinas", "bujias nuevas", "bobinas nuevas",
                "probe bobinas", "probe bujias", "intercambie bobinas", "intercambie bujias",
                "descarte bujias", "descarte bobinas", "probe chispa",
            )
        )
        and not mencion_bobina_falla
    )

    es_parpadeo_check = (
        ("parpadea" in texto_evaluar.lower() or "destella" in texto_evaluar.lower())
        and any(w in texto_evaluar.lower() for w in ("luz del motor", "check engine", "testigo del motor"))
    ) or ("misfire" in texto_evaluar.lower())

    compresion_normal = bool(re.search(
        r"\b(?:compresi[oó]n\s+(?:en\s+los\s+\d+\s+cilindros\s+)?(?:marc[oó]\s+)?(?:1[2-9]\d|2\d\d)\s*psi|"
        r"buena\s+compresi[oó]n|compresi[oó]n\s+(?:pareja|buena|normal|excelente|perfecta))\b",
        texto_evaluar.lower()
    ))
    compresion_baja = any(
        w in texto_evaluar.lower()
        for w in ("baja compresion", "sin compresion", "valvula pisada", "valvula soplada", "anillos gastados", "fuga de compresion")
    ) or bool(re.search(r"\b(?:[0-8]\d)\s*psi\b", texto_evaluar.lower()))

    if descarte_ignicion_total:
        if "inyector" in texto_evaluar.lower() or "pulso" in texto_evaluar.lower() or "p020" in texto_evaluar.lower():
            promovida = "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"
        elif compresion_baja and not compresion_normal:
            promovida = "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados"
        else:
            promovida = "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"
        diagnostico_predictivo = promovida
        confianza = max(confianza, 0.78)
        if predicciones_ml:
            predicciones_ml = [p for p in predicciones_ml if "bujia" not in p.falla.lower()]
            predicciones_ml.insert(0, PrediccionML(
                falla=promovida,
                probabilidad=0.0,
                origen_probabilidad="REGLA",
            ))
            predicciones_ml = predicciones_ml[:3]
    elif (es_parpadeo_check or mencion_bobina_falla) and diagnostico_predictivo != "Falla en bujias o bobinas de encendido (misfire)":
        diagnostico_predictivo = "Falla en bujias o bobinas de encendido (misfire)"
        confianza = max(confianza, 0.75)
        if predicciones_ml:
            predicciones_ml.insert(0, PrediccionML(
                falla=diagnostico_predictivo,
                probabilidad=0.0,
                origen_probabilidad="REGLA",
            ))
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

    return (
        diagnostico_predictivo,
        confianza,
        predicciones_ml,
        predicciones_originales,
        motivo_enrutamiento_area,
        tiempo_ml_ms,
    )
