"""Interpretación clínica de respuestas breves guiadas por intención del turno."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, Optional

from src.core.conversacion.gestor_plan_b import GestorPlanB
from src.core.conversacion.models import (
    FactState,
    FactType,
    QuestionIntent,
)
from src.core.conversacion.respuestas_cortas.acciones_previas import interpretar_accion_previa
from src.core.conversacion.respuestas_cortas.patrones_deteccion import (
    PATRON_AMBIGUO,
    PATRON_NO_APLICA,
    PATRON_NO_SE,
    PATRON_OPCION_NUMERICA,
)

if TYPE_CHECKING:
    from src.core.conversacion.models import ConversationState


def interpretar_respuesta_corta(
    estado: ConversationState,
    texto_usuario: str,
) -> Optional[Dict[str, Any]]:
    """Mapea una respuesta corta a hechos clínicos concretos según la última pregunta."""
    texto_l = texto_usuario.strip().lower()
    ultima_preg = estado.ultima_pregunta()
    accion = interpretar_accion_previa(estado, texto_usuario, ultima_preg)
    if accion is not None:
        return accion
    def _parsear_indice_opcion(raw_val: str) -> int:
        mapa = {
            "1": 0, "primera": 0, "1️⃣": 0,
            "2": 1, "segunda": 1, "2️⃣": 1,
            "3": 2, "tercera": 2, "3️⃣": 2,
            "4": 3, "cuarta": 3,
            "5": 4, "quinta": 4,
            "0": -1,
        }
        if raw_val in mapa:
            return mapa[raw_val]
        return int(raw_val) - 1 if raw_val.isdigit() else 2

    if not ultima_preg:
        m_opt_pre = PATRON_OPCION_NUMERICA.fullmatch(texto_l)
        if m_opt_pre and getattr(estado, "top3_actual", None):
            raw_val = m_opt_pre.group(3).lower()
            idx = _parsear_indice_opcion(raw_val)
            if 0 <= idx < len(estado.top3_actual):
                item = estado.top3_actual[idx]
                hip_val = item.get("falla", "") if isinstance(item, dict) else str(item)
                return {
                    "categoria_respuesta": "OPCION_NUMERICA_PROVISIONAL",
                    "campo": "hipotesis_seleccionada_provisional",
                    "valor": hip_val,
                    "indice_opcion": idx + 1,
                }
            return {
                "categoria_respuesta": "OPCION_NUMERICA_FUERA_DE_RANGO",
                "campo": "opcion_fuera_de_rango",
                "valor": raw_val,
                "indice_opcion": idx + 1,
                "total_opciones": len(estado.top3_actual),
            }
        if PATRON_NO_SE.fullmatch(texto_l):
            hecho = estado.registrar_hecho(
                "desconocido", "no determinado / no se fijó", categoria="desconocido",
                estado=FactState.DESCONOCIDO, texto_crudo=texto_usuario,
            )
            return {"categoria_respuesta": "DESCONOCIDO", "campo": "desconocido",
                    "valor": "desconocido", "hecho": hecho.to_dict()}
        if texto_l in ("si", "sí", "afirmativo", "correcto"):
            h = estado.registrar_hecho(
                f"confirmado_pregunta_{estado.turno_actual}",
                "sí",
                categoria="confirmacion",
                texto_crudo=texto_usuario,
            )
            return {
                "categoria_respuesta": "AFIRMACION",
                "campo": "confirmacion",
                "valor": "sí",
                "hecho": h.to_dict(),
            }
        if texto_l in ("no", "negativo"):
            h = estado.registrar_hecho(
                f"descartado_pregunta_{estado.turno_actual}",
                "no",
                categoria="descarte",
                texto_crudo=texto_usuario,
            )
            return {
                "categoria_respuesta": "NEGACION",
                "campo": "confirmacion",
                "valor": "no",
                "hecho": h.to_dict(),
            }
        return None

    intent_str = str(ultima_preg.get("intent", QuestionIntent.GENERAL.value))
    texto_preg = str(ultima_preg.get("texto", "")).lower()
    hipotesis = ultima_preg.get("hipotesis") or []

    if intent_str == QuestionIntent.MEDICION_TECNICA.value and texto_l in (
        "no", "no se", "no sé", "no lo tengo", "no tengo ese dato"
    ):
        hecho = estado.registrar_hecho(
            campo="medicion_tecnica_pendiente",
            valor="no disponible",
            categoria="inspeccion_pendiente",
            estado=FactState.NO_REVISADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        return {
            "categoria_respuesta": "NO_REVISADO",
            "campo": "medicion_tecnica_pendiente",
            "valor": "no disponible",
            "hecho": hecho.to_dict(),
        }

    if intent_str == QuestionIntent.MEDICION_TECNICA.value and texto_l in (
        "si", "sí", "afirmativo", "correcto"
    ):
        return {
            "categoria_respuesta": "MEDICION_INCOMPLETA",
            "campo": "medicion_tecnica_pendiente",
            "valor": "disponible_sin_valor",
        }

    if intent_str == QuestionIntent.COMPONENTE_REVISADO.value and texto_l in (
        "no", "no aun", "todavia no", "aun no"
    ):
        hecho = estado.registrar_hecho(
            campo="estado_inspeccion_previa",
            valor="no revisado",
            categoria="inspeccion_pendiente",
            estado=FactState.NO_REVISADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        return {
            "categoria_respuesta": "NO_REVISADO",
            "campo": "estado_inspeccion_previa",
            "valor": "no revisado",
            "hecho": hecho.to_dict(),
        }

    if intent_str == QuestionIntent.COMPONENTE_REVISADO.value and texto_l in (
        "si", "sí", "ya", "correcto", "lo revise", "lo revisé"
    ):
        hecho = estado.registrar_hecho(
            campo="revision_componente_pendiente",
            valor=texto_usuario,
            categoria="inspeccion",
            estado=FactState.AMBIGUO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        return {
            "categoria_respuesta": "REVISION_AMBIGUA",
            "campo": "revision_componente_pendiente",
            "valor": texto_usuario,
            "hecho": hecho.to_dict(),
        }

    # Revisión general reportada
    if re.search(
        r"\b(?:ya\s+)?(?:lo|la|eso)\s+revis[eé]\b.*\b(?:est[aá]\s+bien|correcto|normal)\b",
        texto_l,
    ) or re.search(
        r"\b(?:eso|ya)\s+(?:lo\s+)?(?:revis[eé]|prob[eé])\s+y\s+(?:eso\s+)?(?:est[aá]\s+bien|est[aá]\s+normal)\b",
        texto_l,
    ):
        if intent_str == QuestionIntent.CONFIRMACION_ALTERNATIVA.value or "verificar este punto" in texto_preg:
            diagnostico_actual = next(
                (
                    str(h.get("falla", "")) if isinstance(h, dict) else str(h)
                    for h in hipotesis
                    if (h.get("falla") if isinstance(h, dict) else h)
                ),
                estado.falla_principal or "",
            )
            if diagnostico_actual:
                hecho = estado.registrar_hecho(
                    "confirmacion_diagnostico_usuario",
                    "NO",
                    categoria="confirmacion_diagnostico",
                    texto_crudo=texto_usuario,
                    tipo=FactType.CONDICION,
                )
                return {
                    "categoria_respuesta": "DIAGNOSTICO_DESCARTADO",
                    "campo": "confirmacion_diagnostico_usuario",
                    "valor": "NO",
                    "diagnostico": diagnostico_actual,
                    "hecho": hecho.to_dict(),
                }
        return {
            "categoria_respuesta": "REVISION_AMBIGUA",
            "campo": "revision_componente_pendiente",
            "valor": texto_usuario,
            "hecho": estado.registrar_hecho(
                "revision_componente_pendiente",
                texto_usuario,
                categoria="inspeccion",
                estado=FactState.AMBIGUO,
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            ).to_dict(),
        }

    if intent_str == QuestionIntent.CONFIRMACION_ALTERNATIVA.value:
        es_si = texto_l in ("si", "sí", "correcto", "afirmativo", "así es", "asi es")
        es_no = texto_l in ("no", "negativo", "incorrecto")
        if es_si or es_no:
            diagnostico = next(
                (
                    str(h.get("falla", "")) if isinstance(h, dict) else str(h)
                    for h in hipotesis
                    if (h.get("falla") if isinstance(h, dict) else h)
                ),
                estado.falla_principal or "",
            )
            valor = "SI" if es_si else "NO"
            hecho = estado.registrar_hecho(
                "confirmacion_diagnostico_usuario",
                valor,
                categoria="confirmacion_diagnostico",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            return {
                "categoria_respuesta": "DIAGNOSTICO_CONFIRMADO" if es_si else "DIAGNOSTICO_DESCARTADO",
                "campo": "confirmacion_diagnostico_usuario",
                "valor": valor,
                "diagnostico": diagnostico,
                "hecho": hecho.to_dict(),
            }

    # 0. Manejo de 'No aplica'
    if PATRON_NO_APLICA.search(texto_l):
        campo = "herramienta_disponible" if "multimetro" in texto_preg or "manometro" in texto_preg else "condicion_operacion"
        h = estado.registrar_hecho(
            campo=campo,
            valor="no aplica",
            categoria="no_aplica",
            estado=FactState.NO_APLICA,
            texto_crudo=texto_usuario,
        )
        return {
            "categoria_respuesta": "NO_APLICA",
            "campo": campo,
            "valor": "no aplica",
            "estado": FactState.NO_APLICA.value,
            "hecho": h.to_dict(),
        }

    # 0.05 Manejo de 'No sé realizar la prueba / cómo comprobar'
    if GestorPlanB.detectar_no_sabe_realizar(texto_l) and not GestorPlanB.detectar_no_sabe_usar(texto_l):
        hechos_bloqueo = GestorPlanB.registrar_bloqueos_en_estado(estado, texto_usuario, texto_preg)
        campo_plan_b = "dificultad_procedimiento_inspeccion"
        no_rev = GestorPlanB.detectar_no_revisado(texto_l)
        h = estado.registrar_hecho(
            campo=campo_plan_b,
            valor="no_sabe_realizar",
            categoria="plan_b",
            estado=FactState.NO_SABE_REALIZAR,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        primer_hecho = list(hechos_bloqueo.values())[0] if hechos_bloqueo else h.to_dict()
        return {
            "categoria_respuesta": "NO_SABE_REALIZAR_PRUEBA",
            "campo": campo_plan_b,
            "valor": "no_sabe_realizar",
            "estado": FactState.NO_SABE_REALIZAR.value,
            "no_revisado": no_rev,
            "no_sabe_realizar": True,
            "hechos": hechos_bloqueo,
            "hecho": primer_hecho,
        }

    # 0.1 Manejo de 'No sé' / 'Ni idea'
    if PATRON_NO_SE.search(texto_l) and not GestorPlanB.detectar_no_sabe_usar(texto_l) and not GestorPlanB.detectar_no_sabe_realizar(texto_l):
        campo_desconocido = "desconocido"
        if intent_str in (QuestionIntent.DISPONIBILIDAD_HERRAMIENTA.value, QuestionIntent.MEDICION_VOLTAJE.value) or any(t in texto_preg for t in ("multimetro", "tester", "manometro")):
            campo_desconocido = "herramienta_disponible"
        elif intent_str == QuestionIntent.TEMPERATURA_APARICION.value:
            campo_desconocido = "temperatura"
        elif intent_str == QuestionIntent.CONDICION_OPERACION.value:
            campo_desconocido = "condicion_operacion"
        elif intent_str == QuestionIntent.CODIGO_DTC.value:
            campo_desconocido = "codigo_dtc"

        h = estado.registrar_hecho(
            campo=campo_desconocido,
            valor="no determinado / no se fijó",
            categoria="desconocido",
            estado=FactState.DESCONOCIDO,
            texto_crudo=texto_usuario,
        )
        return {
            "categoria_respuesta": "DESCONOCIDO",
            "campo": campo_desconocido,
            "valor": "desconocido",
            "estado": FactState.DESCONOCIDO.value,
            "hecho": h.to_dict(),
        }

    # 0.2 Manejo de respuestas ambiguas / tentativas
    if PATRON_AMBIGUO.search(texto_l) and not any(w in texto_l for w in ("12.", "11.", "13.", "10.", "9.", "8.")):
        campo_ambiguo = "comportamiento_ambiguo"
        m_amb = PATRON_AMBIGUO.search(texto_l)
        valor_ambiguo = m_amb.group(0) if m_amb else "ambiguo"
        if intent_str == QuestionIntent.DISPONIBILIDAD_HERRAMIENTA.value or "multimetro" in texto_preg:
            campo_ambiguo = "multimetro_disponible"
        elif intent_str == QuestionIntent.TEMPERATURA_APARICION.value:
            campo_ambiguo = "temperatura"
        elif intent_str == QuestionIntent.CONDICION_OPERACION.value:
            campo_ambiguo = "condicion_operacion"

        previo = estado.obtener_hecho(campo_ambiguo)
        if previo and previo.estado in (FactState.CONFIRMADO, FactState.CORREGIDO):
            campo_ambiguo = f"respuesta_tentativa_{campo_ambiguo}"
        h = estado.registrar_hecho(
            campo=campo_ambiguo,
            valor=f"{valor_ambiguo} (tentativo)",
            categoria="ambiguo",
            estado=FactState.AMBIGUO,
            confianza=0.5,
            texto_crudo=texto_usuario,
        )
        return {
            "categoria_respuesta": "AMBIGUO",
            "campo": campo_ambiguo,
            "valor": valor_ambiguo,
            "estado": FactState.AMBIGUO.value,
            "hecho": h.to_dict(),
        }

    # 1. Selección provisional de una opción de la pregunta activa.
    m_opt = PATRON_OPCION_NUMERICA.fullmatch(texto_l)
    pregunta_vigente = (
        len(estado.respuestas_obtenidas) < len(estado.preguntas_realizadas)
        and (not estado.pending_question or (
            estado.pending_question.get("intent") == intent_str
            and estado.pending_question.get("texto", "") == ultima_preg.get("texto", "")
            and (not estado.pending_question.get("case_id") or estado.pending_question["case_id"] == estado.case_id)
        ))
        and (not ultima_preg.get("case_id") or ultima_preg["case_id"] == estado.case_id)
    )
    hipotesis_candidatas = (
        list(hipotesis)
        if intent_str in (
            QuestionIntent.DISCRIMINACION_TOP3.value,
            QuestionIntent.CONFIRMACION_ALTERNATIVA.value,
        )
        else []
    )
    if not hipotesis_candidatas and getattr(estado, "top3_actual", None):
        hipotesis_candidatas = [
            h.get("falla") if isinstance(h, dict) else str(h)
            for h in estado.top3_actual
            if (h.get("falla") if isinstance(h, dict) else str(h))
        ]
    es_intent_medicion = intent_str in (
        QuestionIntent.MEDICION_VOLTAJE.value,
        QuestionIntent.MEDICION_PRESION.value,
        QuestionIntent.MEDICION_TECNICA.value,
    )
    tiene_prefijo_opcion = bool(m_opt and (m_opt.group(1) or m_opt.group(2)))
    if (
        m_opt
        and (not es_intent_medicion or tiene_prefijo_opcion or m_opt.group(3).lower() in ("1", "2", "3", "primera", "segunda", "tercera", "1️⃣", "2️⃣", "3️⃣"))
        and hipotesis_candidatas
        and (
            pregunta_vigente
            or (
                bool(getattr(estado, "top3_actual", None))
                and not estado.pending_question
            )
        )
    ):
        raw_val = m_opt.group(3).lower()
        idx = _parsear_indice_opcion(raw_val)
        if 0 <= idx < len(hipotesis_candidatas):
            return {
                "categoria_respuesta": "OPCION_NUMERICA_PROVISIONAL",
                "campo": "hipotesis_seleccionada_provisional",
                "valor": hipotesis_candidatas[idx],
                "indice_opcion": idx + 1,
            }
        return {
            "categoria_respuesta": "OPCION_NUMERICA_FUERA_DE_RANGO",
            "campo": "opcion_fuera_de_rango",
            "valor": raw_val,
            "indice_opcion": idx + 1,
            "total_opciones": len(hipotesis_candidatas),
        }

    opciones_preg = ultima_preg.get("opciones") or []
    if (
        m_opt
        and not hipotesis_candidatas
        and opciones_preg
        and intent_str not in (
            QuestionIntent.COMPORTAMIENTO_ARRANQUE.value,
            QuestionIntent.ACLARACION_CONTRADICCION.value,
        )
    ):
        raw_val = m_opt.group(3).lower()
        idx = _parsear_indice_opcion(raw_val)
        if idx < 0 or idx >= len(opciones_preg):
            return {
                "categoria_respuesta": "OPCION_NUMERICA_FUERA_DE_RANGO",
                "campo": "opcion_fuera_de_rango",
                "valor": raw_val,
                "indice_opcion": idx + 1,
                "total_opciones": len(opciones_preg),
            }
        opc_txt = str(opciones_preg[idx]).lower()
        if intent_str == QuestionIntent.TEMPERATURA_APARICION.value:
            val_temp = "frío" if idx == 0 else ("caliente" if idx == 1 else "frío y caliente")
            h = estado.registrar_hecho("temperatura", val_temp, categoria="temperatura", texto_crudo=texto_usuario)
            return {"categoria_respuesta": "CONDICION", "campo": "temperatura", "valor": val_temp, "hecho": h.to_dict()}
        if intent_str == QuestionIntent.CONDICION_OPERACION.value:
            h = estado.registrar_hecho("condicion_operacion", opc_txt, categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            return {"categoria_respuesta": "CONDICION", "campo": "condicion_operacion", "valor": opc_txt, "hecho": h.to_dict()}
        h = estado.registrar_hecho(f"respuesta_{intent_str}", opc_txt, categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        return {"categoria_respuesta": "CONDICION", "campo": f"respuesta_{intent_str}", "valor": opc_txt, "hecho": h.to_dict()}

    # Una unidad de presión no identifica el circuito. Las medidas explícitas
    # de otro sistema las conserva el extractor técnico, no la respuesta de riel.
    from .contexto_presion import presion_de_otro_circuito

    if presion_de_otro_circuito(texto_usuario):
        return None

    from .mediciones_turno import interpretar_mediciones
    respuesta_numerica = interpretar_mediciones(estado, texto_usuario, texto_l, texto_preg, intent_str)
    if respuesta_numerica:
        return respuesta_numerica

    # 3. Disponibilidad de herramientas y estado de comprobación
    indisponibles = GestorPlanB.detectar_indisponibilidad_en_texto(texto_l, texto_preg)
    recuperadas = GestorPlanB.detectar_recuperacion_herramienta(texto_l, texto_preg)
    no_revisado = GestorPlanB.detectar_no_revisado(texto_l)
    no_sabe_usar = GestorPlanB.detectar_no_sabe_usar(texto_l)

    if indisponibles or recuperadas or no_revisado or no_sabe_usar:
        hechos_bloqueo = GestorPlanB.registrar_bloqueos_en_estado(estado, texto_usuario, texto_preg)
        her_principal = indisponibles[0] if indisponibles else (recuperadas[0] if recuperadas else "general")
        val_resp = "NO" if (indisponibles or no_sabe_usar) else ("SI" if recuperadas else "no_revisado")
        if no_sabe_usar:
            cat_resp = "HERRAMIENTA_INDISPONIBLE"
        elif indisponibles:
            cat_resp = "NEGACION"
        elif recuperadas:
            cat_resp = "AFIRMACION"
        else:
            cat_resp = "NO_REVISADO"
        primer_hecho = list(hechos_bloqueo.values())[0] if hechos_bloqueo else None
        return {
            "categoria_respuesta": cat_resp,
            "campo": "estado_inspeccion_previa" if cat_resp == "NO_REVISADO" else f"{her_principal}_disponible",
            "valor": val_resp,
            "herramientas": indisponibles or recuperadas,
            "no_revisado": no_revisado,
            "no_sabe_usar": no_sabe_usar,
            "hechos": hechos_bloqueo,
            "hecho": primer_hecho or {},
        }

    # 4. Respuestas a COMPORTAMIENTO_ARRANQUE y Luces del Tablero
    if intent_str == QuestionIntent.COMPORTAMIENTO_ARRANQUE.value or any(w in texto_preg for w in ("luces del tablero", "tablero", "atenuan", "atenúan", "bajan bastante")):
        if any(w in texto_l for w in ("se apagan", "se bajan", "se atenúan", "se atenuan", "bajan bastante", "bajan mucho", "se ponen tenues", "tenues", "se van", "parpadean")):
            h = estado.registrar_hecho("luces_se_atenuan", "SI", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            return {"categoria_respuesta": "AFIRMACION", "campo": "luces_se_atenuan", "valor": "SI", "hecho": h.to_dict()}
        if any(w in texto_l for w in ("se mantienen igual", "permanecen igual", "se mantienen", "iguales", "normal", "brillo normal", "no se apagan", "no bajan")):
            h = estado.registrar_hecho("luces_se_atenuan", "NO", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            return {"categoria_respuesta": "NEGACION", "campo": "luces_se_atenuan", "valor": "NO", "hecho": h.to_dict()}
        if any(w in texto_l for w in ("no gira", "inmóvil", "inmovil", "nada", "solo el clic", "solo clic", "1", "la 1")):
            h = estado.registrar_hecho("giro_motor", "no_gira", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            return {"categoria_respuesta": "CONDICION", "campo": "giro_motor", "valor": "no_gira", "hecho": h.to_dict()}
        if any(w in texto_l for w in ("gira pesado", "gira lento", "pesado", "lento", "le cuesta", "2", "la 2")):
            h = estado.registrar_hecho("giro_motor", "gira_lento", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            return {"categoria_respuesta": "CONDICION", "campo": "giro_motor", "valor": "gira_lento", "hecho": h.to_dict()}

    # 5. Respuestas a preguntas de temperatura (frío vs caliente)
    if intent_str == QuestionIntent.TEMPERATURA_APARICION.value or texto_l in ("caliente", "en caliente", "frio", "frío", "en frio", "en frío"):
        if any(w in texto_l for w in ("caliente", "cuando calienta", "despues de andar", "después")):
            h = estado.registrar_hecho("temperatura", "caliente", categoria="temperatura", texto_crudo=texto_usuario)
            return {"categoria_respuesta": "CONDICION", "campo": "temperatura", "valor": "caliente", "hecho": h.to_dict()}
        if any(w in texto_l for w in ("frio", "frío", "primer arranque", "en la mañana")):
            h = estado.registrar_hecho("temperatura", "frío", categoria="temperatura", texto_crudo=texto_usuario)
            return {"categoria_respuesta": "CONDICION", "campo": "temperatura", "valor": "frío", "hecho": h.to_dict()}

    # 6. Respuestas a preguntas de condición de operación
    if intent_str == QuestionIntent.CONDICION_OPERACION.value or any(w in texto_l for w in ("parado", "semaforo", "semáforo", "detenido", "ralenti", "ralentí", "al frenar")):
        if any(w in texto_l for w in ("parado", "semaforo", "semáforo", "detenido", "ralenti", "ralentí")):
            h = estado.registrar_hecho("condicion_operacion", "detenido en ralentí", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            return {"categoria_respuesta": "CONDICION", "campo": "condicion_operacion", "valor": "detenido en ralentí", "hecho": h.to_dict()}
        if any(w in texto_l for w in ("acelerando", "cuando acelero", "al acelerar", "en subida")) and not any(w in texto_l for w in ("empareja", "mejora", "se le pasa")):
            h = estado.registrar_hecho("condicion_operacion", "al acelerar bajo carga", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            return {"categoria_respuesta": "CONDICION", "campo": "condicion_operacion", "valor": "al acelerar bajo carga", "hecho": h.to_dict()}
        if any(w in texto_l for w in ("frenando", "cuando freno", "al frenar")):
            h = estado.registrar_hecho("condicion_operacion", "al frenar", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            return {"categoria_respuesta": "CONDICION", "campo": "condicion_operacion", "valor": "al frenar", "hecho": h.to_dict()}

    # 7b. Resultado negativo de inspección
    if any(c in texto_l for c in ("no tienen holgura", "no tienen juego", "están firmes", "estan firmes", "se ven bien", "están bien", "estan bien", "no hay holgura", "sin holgura", "sin juego", "no se observa holgura")):
        campo_neg = "holgura_componentes" if any(w in texto_preg for w in ("holgura", "buje", "rotula", "rótula")) else "inspeccion_componente"
        h = estado.registrar_hecho(
            campo=campo_neg,
            valor="ausente / sin holgura confirmada",
            categoria="inspeccion_negativa",
            estado=FactState.AUSENTE_NEGADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        return {
            "categoria_respuesta": "RESULTADO_NEGATIVO",
            "campo": campo_neg,
            "valor": "sin_holgura",
            "estado": FactState.AUSENTE_NEGADO.value,
            "hecho": h.to_dict(),
        }

    # 8. Respuestas a ACLARACION_CONTRADICCION
    if intent_str == QuestionIntent.ACLARACION_CONTRADICCION.value:
        if any(w in texto_l for w in ("antes", "antecedente", "pasó antes", "1", "la 1", "opcion 1", "opción 1")):
            estado.eliminar_hecho("conflicto_operativo")
            h = estado.registrar_hecho("antecedente_marcha", "ocurrio_antes", categoria="antecedente", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            return {"categoria_respuesta": "ACLARACION", "campo": "antecedente_marcha", "valor": "ocurrio_antes", "hecho": h.to_dict()}
        if any(w in texto_l for w in ("otro", "otro carro", "otro problema", "otra consulta", "2", "la 2", "opcion 2", "opción 2")):
            estado.eliminar_hecho("conflicto_operativo")
            h = estado.registrar_hecho("antecedente_marcha", "otro_vehiculo", categoria="antecedente", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            return {"categoria_respuesta": "ACLARACION", "campo": "antecedente_marcha", "valor": "otro_vehiculo", "hecho": h.to_dict()}

    # 9. Respuestas genéricas SÍ / NO
    if texto_l in ("si", "sí", "afirmativo", "correcto"):
        h = estado.registrar_hecho(f"confirmado_pregunta_{estado.turno_actual}", "sí", categoria="confirmacion", texto_crudo=texto_usuario)
        return {"categoria_respuesta": "AFIRMACION", "campo": "confirmacion", "valor": "sí", "hecho": h.to_dict()}
    if texto_l in ("no", "negativo"):
        h = estado.registrar_hecho(f"descartado_pregunta_{estado.turno_actual}", "no", categoria="descarte", texto_crudo=texto_usuario)
        return {"categoria_respuesta": "NEGACION", "campo": "confirmacion", "valor": "no", "hecho": h.to_dict()}

    return None
