"""Formateo de respuestas diagnósticas canónicas para WhatsApp (Fase 9.3 y 9.10)."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

from src.core.conversacion.formato_salidas.acciones_prioritarias import (
    extraer_accion_prioritaria,
    generar_pregunta_contextual,
    simplificar_nombre_falla,
)
from src.core.conversacion.formato_salidas.orientacion_abstencion import (
    formatear_orientacion_abstencion,
)
from src.core.conversacion.models import QuestionIntent


def integrar_respuesta_llm(
    respuesta_llm: str,
    respuesta_determinista: str,
    llm_usado: bool,
    respuesta_limitada: bool,
    hipotesis_rechazadas: Optional[List[str]] = None,
) -> str:
    """Usa la síntesis LLM segura y conserva una sola pregunta del flujo determinista."""
    if not llm_usado or respuesta_limitada or not respuesta_llm:
        return respuesta_determinista

    preguntas = re.findall(r"¿[^?]*\?", respuesta_determinista or "", flags=re.DOTALL)
    resumen = re.sub(r"¿[^?]*\?", "", respuesta_llm, flags=re.DOTALL)
    resumen = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", resumen).strip()
    if not resumen:
        return respuesta_determinista
    from src.core.conversacion.validador_compatibilidad import hipotesis_rechazada_en_texto

    if hipotesis_rechazada_en_texto(resumen, hipotesis_rechazadas):
        return respuesta_determinista

    pregunta_siguiente = preguntas[-1].strip() if preguntas else ""
    return f"{resumen}\n\n{pregunta_siguiente}".strip()


def evitar_respuesta_repetida(
    respuesta: str,
    estado: Optional[Any],
    evidencia_duplicada: bool,
    hechos_nuevos: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Evita volver a enviar el mismo resumen cuando no cambió la evidencia del caso."""
    if not estado or not getattr(estado, "trazabilidad", None):
        return respuesta
    respuestas_previas = [
        str(traza.get("respuesta_enviada", "")).strip()
        for traza in estado.trazabilidad[-5:]
        if str(traza.get("respuesta_enviada", "")).strip()
    ]
    if not respuestas_previas or not respuesta:
        return respuesta

    def tokens(texto: str) -> set[str]:
        normalizado = unicodedata.normalize("NFD", texto.casefold())
        limpio = "".join(c for c in normalizado if not unicodedata.combining(c))
        return {
            palabra
            for palabra in re.findall(r"[a-z0-9]+", limpio)
            if len(palabra) > 2
            and palabra not in {"con", "para", "por", "que", "del", "una", "los", "las", "esta", "este"}
        }

    actuales = tokens(respuesta)
    repetida = any(
        len(actuales & previos) >= 5 and len(actuales & previos) / max(1, len(actuales | previos)) >= 0.72
        for previos in (tokens(anterior) for anterior in respuestas_previas)
    )
    if not repetida:
        return respuesta
    if not evidencia_duplicada:
        es_abstencion = bool(re.search(r"(?:sin|no tengo una) hip[oó]tesis ml", respuesta, re.I))
        hechos_nuevos = hechos_nuevos or []
        if hechos_nuevos and all(
            "pendiente" in str(hecho.get("campo", "")).casefold()
            or str(hecho.get("estado", "")).upper()
            in {
                "DESCONOCIDO",
                "NO_REVISADO",
                "NO_SABE_REALIZAR",
            }
            for hecho in hechos_nuevos
        ):
            if not es_abstencion:
                return respuesta
            return (
                "Registré que la comprobación está pendiente o no disponible. "
                "No repetiré esa prueba ni confirmaré una falla sin su resultado. "
                "Conservo el caso a la espera de evidencia aplicable."
            )
        novedades = []
        for hecho in hechos_nuevos:
            campo = re.sub(r"_+", " ", str(hecho.get("campo", "dato"))).strip()
            valor = re.sub(r"\s+", " ", str(hecho.get("valor", ""))).strip()
            detalle = f"{campo}: {valor}" if valor else campo
            if detalle and detalle not in novedades:
                novedades.append(detalle)
        if novedades:
            resumen = "; ".join(novedades[:3])
            return (
                f"Registré en el turno {getattr(estado, 'turno_actual', '')}: {resumen}. "
                "Queda como evidencia reportada, sin convertirlo en confirmación física."
            )
        if not es_abstencion:
            return respuesta
    return (
        "No hay evidencia nueva que cambie la orientación anterior. La causa sigue sin confirmar; "
        "cuando tengas un resultado de prueba distinto, compártelo y actualizaré este mismo caso."
    )


def calcular_scores_presentacion(
    top_hipotesis: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Calcula scores de presentación para WhatsApp sin alterar las probabilidades RAW.
    Garantiza que tres hipótesis mutuamente excluyentes nunca sumen más de 100%.
    """
    if not top_hipotesis:
        return []

    items = list(top_hipotesis[:3])
    origenes = [str(item.get("origen_probabilidad", "SVM")).upper() for item in items]
    probs = [
        float(item.get("probabilidad", 0.0)) if origen == "SVM" else 0.0
        for item, origen in zip(items, origenes)
    ]
    pcts = [int(round(p * 100)) if p <= 1.0 else int(round(p)) for p in probs]
    suma_pcts = sum(pcts)

    es_conjunta = sum(probs) <= 1.05
    if es_conjunta and suma_pcts > 100:
        exceso = suma_pcts - 100
        for i in reversed(range(len(pcts))):
            ajuste = min(exceso, pcts[i])
            pcts[i] -= ajuste
            exceso -= ajuste
            if exceso <= 0:
                break

    resultado = []
    for item, pct in zip(items, pcts):
        resultado.append(
            {
                "falla": item.get("falla", ""),
                "probabilidad_raw": item.get("probabilidad", 0.0),
                "porcentaje_presentacion": pct,
                "es_distribucion_conjunta": es_conjunta,
                "origen_probabilidad": str(item.get("origen_probabilidad", "SVM")).upper(),
            }
        )
    return resultado


def obtener_pregunta_contextual(
    top1_falla_o_hipotesis: Any,
    sintoma_original: str = "",
    estado: Optional[Any] = None,
) -> Tuple[str, QuestionIntent]:
    """Retorna la pregunta contextual y su QuestionIntent correspondiente."""
    if isinstance(top1_falla_o_hipotesis, list) and top1_falla_o_hipotesis:
        primera = top1_falla_o_hipotesis[0]
        falla = primera.get("falla", "") if isinstance(primera, dict) else str(primera)
    elif isinstance(top1_falla_o_hipotesis, dict):
        falla = top1_falla_o_hipotesis.get("falla", "")
    else:
        falla = str(top1_falla_o_hipotesis or "")
    return generar_pregunta_contextual(falla, sintoma_original, estado)


def formatear_respuesta_diagnostico(
    top_hipotesis: List[Dict[str, Any]],
    sintoma_original: str = "",
    contexto_rag: str = "",
    prueba_personalizada: Optional[str] = None,
    pregunta_personalizada: Optional[str] = None,
    estado: Optional[Any] = None,
) -> str:
    """Produce el formato canónico compacto para WhatsApp."""
    if not top_hipotesis:
        return formatear_orientacion_abstencion(sintoma_original, estado)

    combustible_str = ""
    if estado:
        combustible_str = getattr(estado, "combustible", "") or ""
        if not combustible_str and getattr(estado, "hechos", None):
            h_comb = estado.hechos.get("combustible")
            if h_comb:
                combustible_str = getattr(h_comb, "valor", "") or ""
    combustible_str = str(combustible_str).lower()

    from src.core.conversacion.ruteador_sistema import tiene_descarte_de_componente

    scores_pres = calcular_scores_presentacion(top_hipotesis)
    es_conjunta = scores_pres[0].get("es_distribucion_conjunta", True) if scores_pres else True

    lineas_hipotesis = []
    candidatos_compatibles = []
    num_mostrado = 1
    for item in scores_pres:
        falla_nom = simplificar_nombre_falla(item.get("falla", ""))
        conf_pct = item.get("porcentaje_presentacion", 0)
        origen_probabilidad = item.get("origen_probabilidad", "SVM")
        falla_l = falla_nom.lower()

        if tiene_descarte_de_componente(estado, falla_nom):
            continue

        if origen_probabilidad != "SVM":
            etiqueta_confianza = "priorizada por evidencia; sin porcentaje SVM"
        else:
            etiqueta_confianza = f"{conf_pct}% (SVM)"

        es_precalentamiento = any(
            k in falla_l for k in ("precalentamiento", "incandesc", "glow", "calentador")
        )
        es_diesel_exclusivo = (
            any(k in falla_l for k in ("diesel", "dpf", "fap", "adblue", "def ", "common rail diesel"))
            or es_precalentamiento
        )
        if es_diesel_exclusivo:
            if combustible_str in ("gasolina", "glp", "gnv", "nafta"):
                continue
            elif not combustible_str:
                lineas_hipotesis.append(
                    f"{num_mostrado}. {falla_nom} — {etiqueta_confianza} *(solo si es Diésel)*"
                )
                candidatos_compatibles.append(item)
                num_mostrado += 1
                if num_mostrado > 3:
                    break
                continue

        es_gasolina_exclusivo = any(k in falla_l for k in ("gasolina", "bobina", "chispa", "carburador")) or (
            any(k in falla_l for k in ("bujia", "bujias")) and not es_precalentamiento
        )
        if es_gasolina_exclusivo and combustible_str in ("diesel", "diésel"):
            continue

        lineas_hipotesis.append(f"{num_mostrado}. {falla_nom} — {etiqueta_confianza}")
        candidatos_compatibles.append(item)
        num_mostrado += 1
        if num_mostrado > 3:
            break

    if not lineas_hipotesis:
        texto_ctx = f"{sintoma_original} {getattr(estado, 'active_symptoms', [])}".lower()
        if any(w in texto_ctx for w in ("glp", "gnv", "a gas", "conmuta a gas")):
            return (
                "🔧 *Orientación técnica para sistema GLP / GNV (conversión):*\n\n"
                "La falla se manifiesta específicamente al operar en gas, mientras que la inyección de gasolina funciona correctamente. "
                "Los equipos de conversión a gas (reductor, filtro de fase líquida, filtro de fase gaseosa, conmutadora y emulador) son sistemas complementarios "
                "fuera del catálogo estándar de inyección OEM.\n\n"
                "🛠️ *Primero revisa:* presión diferencial del reductor en datos en vivo con software de gas (Tomasetto/AEB/Lovato) y estado del filtro de fase líquida por saturación de limaduras.\n\n"
                "¿Dispones de software de diagnóstico de gas o manómetro para verificar la presión del reductor?"
            )
        if any(w in texto_ctx for w in ("rompemuelles", "baches", "rueda", "clac clac", "suspensi")):
            return (
                "🔧 *Orientación técnica para tren delantero y suspensión:*\n\n"
                "Al tratarse de una avería puramente mecánica en rodamiento o suspensión, no se registran códigos DTC en el escáner. "
                "Las causas estadísticas de arranque quedan descartadas.\n\n"
                "🛠️ *Primero revisa:* inspección en elevador con palanca para verificar holgura axial/vertical en rótulas de suspensión, terminales de dirección y bieletas estabilizadoras.\n\n"
                "¿Has verificado con palanca si la rótula de suspensión presenta juego vertical u oscilación en el elevador?"
            )
        if any(
            w in texto_ctx
            for w in ("gira motor con fuerza", "gira con fuerza", "candado", "inmovilizador", "transponder")
        ):
            return (
                "🔧 *Orientación técnica para sistema de inmovilizador / encendido:*\n\n"
                "El motor gira con fuerza al dar arranque, descartando batería y motor de arranque. "
                "La falta de encendido con giro potente apunta a bloqueo de seguridad inmovilizador (antena transponder o llave desprogramada) o falta de sincronismo.\n\n"
                "🛠️ *Primero revisa:* estado del testigo de inmovilizador/candado en el tablero al poner contacto y prueba de encendido con la segunda llave original.\n\n"
                "¿El testigo de candado/seguridad destella rápidamente o se apaga al girar la llave?"
            )
        return (
            "🔧 *Orientación técnica (sin porcentaje SVM):*\n\n"
            "Las causas estadísticas iniciales han sido descartadas mediante las comprobaciones reportadas. "
            "Se requiere inspección instrumental complementaria antes de emitir una nueva hipótesis.\n\n"
            "¿Deseas registrar alguna medición adicional o consultar el procedimiento de prueba de otro componente?"
        )

    bloque_causas = "\n".join(lineas_hipotesis)
    titulo_causas = "🔧 *Posibles causas*" if es_conjunta else "🔧 *Posibles causas (confianza individual)*"

    top1_falla = (
        candidatos_compatibles[0].get("falla", "")
        if candidatos_compatibles
        else top_hipotesis[0].get("falla", "")
    )
    es_solicitud_sensorial = bool(
        re.search(
            r"\b(?:sin\s+herramientas?|solo\s+mirando|sensorial|mirando\s+y\s+oliendo)\b",
            sintoma_original,
            re.I,
        )
    )
    if es_solicitud_sensorial:
        accion = "inspecci\u00f3n visual y comprobaci\u00f3n sensorial (olor a combustible crudo por el tubo de escape o vano motor, inspecci\u00f3n visual de cables cuarteados, arneses y mangueras de vac\u00edo sin herramientas)."
        pregunta = "\u00bfPercibes olor a gasolina cruda por el escape o notas cables/mangueras cuarteadas al revisar visualmente?"
    else:
        accion = prueba_personalizada or extraer_accion_prioritaria(top1_falla, contexto_rag, estado)
    if not accion.endswith("."):
        accion += "."

    if pregunta_personalizada is not None:
        pregunta = pregunta_personalizada
    elif not es_solicitud_sensorial:
        pregunta, _ = obtener_pregunta_contextual(top1_falla, sintoma_original, estado)

    if estado and pregunta:
        from src.core.conversacion.compatibilidad_preguntas import CompatibilidadPreguntas

        if CompatibilidadPreguntas.contradice_hecho_negado(pregunta, estado):
            pregunta = "La causa sigue pendiente de una comprobación física; conservo los síntomas negados."

    advertencia_seguridad = ""
    texto_eval_seg = f"{sintoma_original} {getattr(estado, 'active_symptoms', [])}".lower()
    if any(
        w in texto_eval_seg
        for w in ("recalienta", "sobrecalentamiento", "temperatura", "108 grados", "hirviendo")
    ):
        advertencia_seguridad = "\n\n⚠️ *Seguridad:* Evite circular con temperatura elevada para proteger el empaque de culata. No abrir la tapa del radiador ni del depósito de expansión mientras el motor permanezca caliente por riesgo de quemaduras por vapor presurizado."
    elif any(
        w in texto_eval_seg
        for w in ("suspensi", "bache", "amortiguador", "bujes", "rotula", "tren delantero")
    ):
        advertencia_seguridad = "\n\n⚠️ *Seguridad:* En comprobaciones de suspensión, utilice siempre elevador automotriz con trabas mecánicas o caballetes certificados. Nunca realice inspecciones bajo el vehículo sostenido únicamente con gata hidráulica."
    elif any(w in texto_eval_seg for w in ("freno", "frenar", "pastilla", "disco")):
        advertencia_seguridad = "\n\n⚠️ *Seguridad:* Al tratarse del sistema de frenos, la inspección física presencial en taller es indispensable antes de seguir circulando para evitar pérdida de frenado."

    return (
        f"{titulo_causas}\n\n"
        f"{bloque_causas}\n\n"
        f"🛠️ *Primero revisa:* {accion}\n\n"
        f"{pregunta}{advertencia_seguridad}"
    )
