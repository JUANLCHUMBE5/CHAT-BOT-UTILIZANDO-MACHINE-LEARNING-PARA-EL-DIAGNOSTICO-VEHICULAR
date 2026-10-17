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
from src.core.diagnostico.reglas_coherencia_ml import aplicar_reglas_coherencia
from src.core.traductor_jerga import normalizar_jerga_peruana


def _normalizar(texto: str) -> str:
    return normalizar_jerga_peruana(texto or "")


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
        confianza = 0.0
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
                origen_probabilidad="SVM",
            )
            for item in predicciones_raw
        ]
        diagnostico_predictivo = predicciones_ml[0].falla if predicciones_ml else "DESCONOCIDO"
        confianza = predicciones_ml[0].probabilidad if predicciones_ml else 0.0
    else:
        diagnostico_predictivo, confianza = gestor.modelo_ml.predecir_falla_con_confianza(texto_ml)
        predicciones_ml = [PrediccionML(falla=diagnostico_predictivo, probabilidad=confianza, origen_probabilidad="SVM")]

    predicciones_originales = [p.model_copy() for p in predicciones_ml]
    motivo_enrutamiento_area = ""

    # Descarte explícito de bujías/bobinas si el mecánico ya las probó
    mencion_bujias_probadas = any(
        p in texto_evaluar.lower()
        for p in (
            "cambie bujias", "cambie las bujias", "bujias nuevas", "bujias cambiadas",
            "probe bujias", "bujias probadas", "descarte bujias", "descarte de bujias",
            "cambio bujias", "cambio de bujias", "bujias estan bien", "bujias descartadas",
            "descarte bujias y bobinas", "bujias y bobinas cambiadas", "bujias y bobinas nuevas",
        )
    )
    if mencion_bujias_probadas:
        predicciones_ml = [p for p in predicciones_ml if "bujia" not in p.falla.lower()]
        if not predicciones_ml:
            predicciones_ml = list(predicciones_originales)
        else:
            diagnostico_predictivo = predicciones_ml[0].falla
            confianza = predicciones_ml[0].probabilidad

    # Priorización causal de bomba de gasolina
    es_bomba_gasolina = (
        ("bomba de gasolina" in texto_evaluar.lower() or "bomba de combustible" in texto_evaluar.lower())
        and any(w in texto_evaluar.lower() for w in ("presion", "baja presion", "no levanta", "cae la presion", "sin presion", "falla"))
    )
    if es_bomba_gasolina:
        diagnostico_predictivo = "Bomba de gasolina quemada o con baja presion"
        confianza = 0.0
        if predicciones_ml:
            predicciones_ml = [p for p in predicciones_ml if p.falla != diagnostico_predictivo]
            predicciones_ml.insert(0, PrediccionML(
                falla=diagnostico_predictivo,
                probabilidad=0.0,
                origen_probabilidad="REGLA",
            ))
            predicciones_ml = predicciones_ml[:3]

    # Priorización causal de IAC / cuerpo de aceleración
    es_iac_sucia = (
        any(w in texto_evaluar.lower() for w in ("valvula iac", "valvula de ralenti", "cuerpo de aceleracion", "cuerpo de aceleración", "mariposa sucia"))
        and any(w in texto_evaluar.lower() for w in ("sucia", "carbon", "carbonizada", "trabada", "pegada", "limpiar", "descalibrada"))
    )
    if es_iac_sucia:
        diagnostico_predictivo = "Cuerpo de aceleracion o valvula IAC sucia"
        confianza = 0.0
        if predicciones_ml:
            predicciones_ml = [p for p in predicciones_ml if p.falla != diagnostico_predictivo]
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
        ]
        if compatibles_filtradas and "injectores" not in texto_evaluar.lower():
            compatibles_filtradas, _ = priorizar_evidencia(texto_evaluar, compatibles_filtradas)
        compatibles_filtradas = compatibles_filtradas[:3]

        texto_ecu = texto_evaluar.lower()
        falla_ecu = None
        es_bateria_descarga = bool(
            re.search(r"\b(?:bater[ií]a\s+se\s+descarga|descarga\s+de\s+bater[ií]a|borne|sulfatad[oa]|alternador\s+no\s+carga)\b", texto_ecu)
            and not re.search(r"\b(?:ecu|pcm|ecm|computadora|modulo|inmovilizador|red\s+can|bus\s+can|u0100|u0001)\b", texto_ecu)
        )
        top_es_c28 = bool(
            compatibles_filtradas
            and compatibles_filtradas[0].falla == "Falla o corto en la Computadora del Motor (ECU / PCM quemada)"
            and compatibles_filtradas[0].probabilidad >= 0.50
        )
        if "ELECTRICO_ECU" in areas_consulta and not es_bateria_descarga:
            if re.search(
                r"\b(?:escaner|esc[aá]ner|scanner|interfaz|obd2?|puerto)\b.{0,45}\b(?:no\s+comunica|sin\s+comunicacion|error\s+de\s+(?:enlace|comunicacion)|no\s+conecta|no\s+entra|no\s+enlaza)\b|"
                r"\b(?:no\s+comunica|sin\s+comunicacion|error\s+de\s+enlace)\b.{0,45}\b(?:con\s+(?:la\s+)?)?(?:ecu|pcm|ecm|bcm|computadora|modulo)\b|"
                r"\b(?:red\s+can|bus\s+can|can\s+(?:high|low|h|l)|u0100|u0101|u0001)\b",
                texto_ecu,
            ):
                falla_ecu = "Falla en conector, alimentacion o red CAN de comunicacion con ECU"
            elif (
                re.search(r"\b(?:no\s+arranca|no\s+enciende|no\s+prende|bloquea\s+(?:el\s+)?encendido|bloqueo|inmovilizador|llave\s+(?:parpadea|destella)|candado)\b", texto_ecu)
                and re.search(
                    r"\b(?:cambiar|cambiaron|cambio|cambie|reemplaz\w*|pusieron|instalaron|montaron)\s+(?:la\s+|el\s+|una?\s+)?(?:computadora|ecu|pcm|ecm|modulo)\b",
                    texto_ecu,
                )
            ):
                falla_ecu = "ECU no codificada o bloqueo de inmovilizador tras cambio de computadora"
            elif re.search(
                r"\b(?:cambiar|cambiaron|cambio|cambie|reemplaz\w*|pusieron|instalaron|montaron)\s+(?:la\s+|el\s+|una?\s+)?(?:computadora|ecu|pcm|ecm|modulo)\b|"
                r"\b(?:ecu|computadora)\b.{0,30}\b(?:incompatible|usada|desguace|de\s+otro|sin\s+codificar|desprogramada)\b",
                texto_ecu,
            ):
                falla_ecu = "ECU incompatible o falta de codificacion de computadora"
            elif not top_es_c28 and re.search(
                r"\b(?:antecedente\s+(?:el[eé]ctrico[/\s]+)?(?:ecu|computadora|arnes)|"
                r"corto\s+el[eé]ctrico|cortocircuito|cable\s+quemado|arn[eé]s\s+(?:quemado|en\s+corto|da[ñn]ado)|"
                r"quema\s+(?:el\s+)?fusible|olor\s+a\s+quemado\s+en\s+arn[eé]s|"
                r"modo\s+(?:de\s+)?(?:protecci[oó]n|emergencia|seguro|degradado)|limp\s+mode)\b",
                texto_ecu,
            ):
                falla_ecu = "Corto electrico en arnes o modo de proteccion de ECU"

        if falla_ecu:
            diagnostico_predictivo = falla_ecu
            confianza = 0.0
            predicciones_ml = [
                PrediccionML(
                    falla=falla_ecu,
                    probabilidad=0.0,
                    origen_probabilidad="REGLA",
                ),
                *[p for p in compatibles_filtradas if p.falla != falla_ecu],
            ][:3]
            motivo_enrutamiento_area = "Enrutamiento eléctrico / ECU por evidencia de módulo o comunicación."
        elif compatibles_filtradas:
            predicciones_ml = compatibles_filtradas
            diagnostico_predictivo = predicciones_ml[0].falla
            confianza = predicciones_ml[0].probabilidad
            motivo_enrutamiento_area = (
                "Enrutamiento por señal explícita del mecánico: "
                + ", ".join(ETIQUETAS_AREA.get(area, area) for area in areas_consulta)
                + "; probabilidades SVM originales conservadas."
            )
        else:
            etiquetas_area = ", ".join(
                ETIQUETAS_AREA.get(area, area) for area in areas_consulta
            )
            diagnostico_predictivo = f"Sin hipótesis ML pertinente para {etiquetas_area}"
            confianza = 0.0
            predicciones_ml = []
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

    texto_norm = _normalizar(texto_evaluar)
    falla_ect = None
    es_condicion_frio = bool(
        re.search(r"\b(?:en\s+fr[ií]o|motor\s+fr[ií]o|en\s+las\s+ma[ñn]anas|al\s+primer\s+arranque|cuando\s+est[aá]\s+fr[ií]o)\b", texto_norm)
    )
    es_check_intermitente = bool(
        re.search(r"\b(?:check\s+intermitente|prende\s+y\s+apaga|parpadea\s+(?:el\s+)?check|luz\s+intermitente|prende\s+el\s+check\s+en\s+fr[ií]o)\b", texto_norm)
        or ("check" in texto_norm and "intermitente" in texto_norm)
    )
    mencion_sensor_ect = bool(
        re.search(r"\b(?:sensor\s+ect|sensor\s+de\s+temperatura\s+(?:del?\s+)?(?:refrigerante|agua)|p011[5-8])\b", texto_norm)
    )
    no_sobrecalienta = not bool(
        re.search(r"\b(?:recalienta|sobrecalienta|hierve|humo\s+blanco|vapor)\b", texto_norm)
    )
    if (es_condicion_frio and es_check_intermitente) or (mencion_sensor_ect and no_sobrecalienta):
        falla_ect = "Falla en sensor de temperatura de refrigerante (ECT) o conexion intermitente"
        diagnostico_predictivo = falla_ect
        confianza = 0.0
        predicciones_ml = [
            PrediccionML(falla=falla_ect, probabilidad=0.0, origen_probabilidad="REGLA"),
            *[p for p in predicciones_ml if p.falla != falla_ect],
        ][:3]
        motivo_enrutamiento_area = "Priorización por síntoma térmico en frío (sensor ECT / conexión)."
    else:
        falla_tps = None
        es_tirones_aceleracion = bool(
            re.search(
                r"\b(?:acelera\s+a\s+tirones|al\s+acelerar\s+(?:da\s+tirones|tironea|jalonea|cabecea)|"
                r"tironea\s+al\s+acelerar|tirones\s+al\s+acelerar|jalonea\s+al\s+acelerar|"
                r"tirones\s+con\s+check|acelera\s+con\s+tirones)\b",
                texto_norm,
            )
        )
        es_contexto_tps = bool(
            re.search(
                r"\b(?:check|luz\s+del\s+motor|testigo|epc|tps|cuerpo\s+de\s+aceleracion|mariposa|p012\d|p2135)\b",
                texto_norm,
            )
        )
        no_misfire_carga = not bool(
            re.search(
                r"\b(?:parpadea|destella|misfire|p030\d|chispa|bobina|bujia|subida|pendiente)\b",
                texto_norm,
            )
        )
        if es_tirones_aceleracion and es_contexto_tps and no_misfire_carga:
            falla_tps = "Cuerpo de aceleracion o sensor TPS descalibrado"
            diagnostico_predictivo = falla_tps
            confianza = 0.0
            predicciones_ml = [
                PrediccionML(falla=falla_tps, probabilidad=0.0, origen_probabilidad="REGLA"),
                *[p for p in predicciones_ml if p.falla != falla_tps],
            ][:3]
            motivo_enrutamiento_area = "Priorización por síntoma de aceleración a tirones (TPS / cuerpo de aceleración)."

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
        confianza = 0.0
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
        confianza = 0.0
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
        confianza = 0.0
        predicciones_ml = [
            PrediccionML(
                falla=diagnostico_predictivo,
                probabilidad=0.0,
                origen_probabilidad="REGLA",
            )
        ]

    diagnostico_predictivo, confianza, predicciones_ml, motivo_regla = aplicar_reglas_coherencia(
        texto_evaluar,
        diagnostico_predictivo,
        confianza,
        predicciones_ml,
        predicciones_originales,
    )
    if motivo_regla:
        motivo_enrutamiento_area = "; ".join(filter(None, (motivo_enrutamiento_area, motivo_regla)))

    tiempo_ml_ms = max(0, int((time.perf_counter() - inicio_ml) * 1000))

    return (
        diagnostico_predictivo,
        confianza,
        predicciones_ml,
        predicciones_originales,
        motivo_enrutamiento_area,
        tiempo_ml_ms,
    )
