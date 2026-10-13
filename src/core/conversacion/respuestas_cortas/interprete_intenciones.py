"""Interpretación clínica de respuestas breves guiadas por intención del turno."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, Optional

from src.core.conversacion.gestor_plan_b import GestorPlanB
from src.core.conversacion.models import (
    EstadoOperativo,
    FactState,
    FactType,
    QuestionIntent,
)
from src.core.conversacion.respuestas_cortas.extractor_mediciones import extraer_todas_mediciones
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
    if not ultima_preg:
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

    # 1. Selección por número de opción (1, 2, 3, etc.)
    m_opt = PATRON_OPCION_NUMERICA.search(texto_l)
    if m_opt and hipotesis:
        raw_val = m_opt.group(3).lower()
        idx = 0 if raw_val in ("1", "primera", "1️⃣") else (1 if raw_val in ("2", "segunda", "2️⃣") else 2)
        if idx < len(hipotesis):
            falla_elegida = hipotesis[idx]
            h = estado.registrar_hecho(
                campo="falla_confirmada_usuario",
                valor=falla_elegida,
                categoria="diagnostico",
                estado=FactState.CONFIRMADO,
                texto_crudo=texto_usuario,
            )
            return {
                "categoria_respuesta": "OPCION_NUMERICA",
                "campo": "falla_confirmada_usuario",
                "valor": falla_elegida,
                "diagnostico_forzado": falla_elegida,
                "hecho": h.to_dict(),
            }

    # 2. Respuestas técnicas numéricas (voltaje, presión, etc.)
    es_anio_sin_unidad = bool(
        re.search(r"\b(?:19[89]\d|20[0-2]\d)\b", texto_l)
        and not re.search(r"\b(?:psi|bar|kpa|mv|v|voltios?|volts?|ohmios?|rpm|km/h|%|mm|ms)\b", texto_l)
    )
    if not es_anio_sin_unidad and re.search(r"\d+(?:[.,]\d+)?", texto_l) and (
        intent_str in (
            QuestionIntent.MEDICION_TECNICA.value,
            QuestionIntent.MEDICION_VOLTAJE.value,
            QuestionIntent.MEDICION_PRESION.value,
            QuestionIntent.DISPONIBILIDAD_HERRAMIENTA.value,
        )
        or any(u in texto_l for u in ("v", "volt", "psi", "bar", "kpa", "rpm", "baja a", "marca", "da"))
        or any(k in texto_preg for k in ("voltaje", "multimetro", "presion", "manometro", "psi"))
        or (estado.pending_question and estado.pending_question.get("intent") in (QuestionIntent.MEDICION_PRESION.value, QuestionIntent.MEDICION_VOLTAJE.value))
    ):
        mediciones = extraer_todas_mediciones(texto_l, intent_str, texto_preg, estado.pending_question)
        if mediciones:
            respuesta_retorno = None
            mediciones_ordenadas = sorted(
                mediciones,
                key=lambda m: (0 if m[2] == "durante_arranque" else (1 if m[2] == "con_carga_electrica" else 2)),
            )
            for val, unidad, condicion in mediciones_ordenadas:
                if unidad in ("PSI", "bar", "kPa", "mbar"):
                    campo = "medicion_presion"
                    tipo_med = "presion_combustible"
                    contexto_med = "riel_inyeccion"
                elif unidad in ("V", "mV"):
                    es_caida = bool(
                        re.search(r"\b(?:ca[ií]da\s+de\s+tensi[oó]n|masa|chasis|tierra|borne\s+negativo)\b", texto_l)
                        or (val < 2.0 and not condicion)
                    )
                    if es_caida:
                        campo = "medicion_caida_tension_masa"
                        tipo_med = "caida_tension"
                        contexto_med = "masa_chasis"
                    elif condicion in ("reposo", "durante_arranque", "contacto_on"):
                        campo = f"medicion_voltaje_{condicion}"
                        tipo_med = "voltaje_bateria"
                        contexto_med = condicion
                    elif 13.0 <= val <= 15.5:
                        campo = "medicion_voltaje_alternador"
                        tipo_med = "voltaje_alternador"
                        contexto_med = "carga_alternador"
                    else:
                        campo = f"medicion_voltaje_{condicion}" if condicion else "medicion_voltaje"
                        tipo_med = "voltaje_bateria" if val < 13.0 else "voltaje_alternador"
                        contexto_med = condicion or "circuito"
                elif unidad in ("mA", "A"):
                    es_parasito = bool(re.search(r"\b(?:par[aá]sito|fuga|descarga|reposo|consumo)\b", texto_l))
                    tipo_med = "consumo_parasito" if es_parasito else "corriente_electrica"
                    campo = "medicion_consumo_parasito" if es_parasito else "medicion_corriente"
                    contexto_med = "reposo_bateria" if es_parasito else "circuito"
                elif unidad == "inHg":
                    tipo_med = "restriccion_vacio" if any(w in texto_l for w in ("restricci", "diesel", "diésel", "linea", "línea")) else "vacio_motor"
                    campo = "medicion_restriccion_vacio" if tipo_med == "restriccion_vacio" else "medicion_vacio_admision"
                    contexto_med = "linea_combustible" if tipo_med == "restriccion_vacio" else "multiple_admision"
                elif unidad == "mm":
                    if any(w in texto_l for w in ("disco", "freno", "alabeo", "comparador")):
                        tipo_med = "alabeo_disco"
                        campo = "medicion_alabeo_disco"
                        contexto_med = "disco_freno"
                    elif any(w in texto_l for w in ("rotula", "rótula", "juego", "axial", "holgura")):
                        tipo_med = "juego_rotula"
                        campo = "medicion_juego_rotula"
                        contexto_med = "rotula_suspension"
                    else:
                        tipo_med = "dimension_metrologica"
                        campo = "medicion_longitud_mm"
                        contexto_med = "componente"
                elif unidad == "ml":
                    tipo_med = "retorno_inyector" if any(w in texto_l for w in ("inyector", "retorno", "probeta")) else "volumen_fluido"
                    campo = "medicion_retorno_inyectores" if tipo_med == "retorno_inyector" else "medicion_volumen"
                    contexto_med = "inyectores_diesel" if tipo_med == "retorno_inyector" else "fluido"
                elif unidad in ("ohm", "kohm"):
                    tipo_med = "resistencia_electrica"
                    campo = "medicion_resistencia_iac" if "iac" in texto_l else "medicion_resistencia"
                    contexto_med = "valvula_iac" if "iac" in texto_l else ("bobina" if "bobina" in texto_l else "componente")
                elif unidad == "g/s":
                    tipo_med = "flujo_aire_maf"
                    campo = "medicion_flujo_maf"
                    contexto_med = "sensor_maf"
                elif unidad == "RPM":
                    campo = "medicion_rpm"
                    tipo_med = "rpm_motor"
                    contexto_med = "ralenti" if any(
                        w in texto_l or w in texto_preg for w in ("ralenti", "ralentí", "detenido", "idle")
                    ) else "motor"
                elif unidad in ("unidades", ""):
                    if intent_str == QuestionIntent.MEDICION_VOLTAJE.value or "voltaje" in texto_preg:
                        campo = f"medicion_voltaje_{condicion}" if condicion else "medicion_voltaje"
                        unidad = "V"
                        tipo_med = "voltaje_bateria"
                        contexto_med = condicion or "bateria"
                    elif intent_str == QuestionIntent.MEDICION_PRESION.value or "presion" in texto_preg:
                        campo = "medicion_presion"
                        unidad = "PSI"
                        tipo_med = "presion_combustible"
                        contexto_med = "riel_inyeccion"
                    else:
                        campo = "medicion_tecnica"
                        tipo_med = "medicion_tecnica"
                        contexto_med = "general"
                else:
                    campo = f"medicion_{unidad.lower()}"
                    tipo_med = f"medicion_{unidad.lower()}"
                    contexto_med = "general"

                valor_medicion = f"{val} {unidad}" + (f" ({condicion})" if condicion else "")
                if unidad == "RPM" and contexto_med == "ralenti":
                    valor_medicion = f"{val} {unidad} en ralentí"
                    estado.estado_operativo = EstadoOperativo.RALENTI

                h = estado.registrar_hecho(
                    campo=campo,
                    valor=valor_medicion,
                    categoria="medicion",
                    estado=FactState.CONFIRMADO,
                    texto_crudo=texto_usuario,
                    tipo=FactType.CONDICION,
                )
                estado.registrar_hecho("valor_medicion", str(val), categoria="medicion", tipo=FactType.CONDICION)
                estado.registrar_hecho("unidad_medicion", unidad, categoria="medicion", tipo=FactType.CONDICION)
                if condicion:
                    estado.registrar_hecho("condicion_medicion", condicion, categoria="medicion", tipo=FactType.CONDICION)

                estado.registrar_medicion(
                    tipo=tipo_med,
                    valor=val,
                    unidad=unidad,
                    contexto=contexto_med,
                    prueba=campo,
                    estado="observado",
                )
                estado.registrar_prueba_completada(campo, f"{val} {unidad}")

                if unidad == "V":
                    if condicion == "durante_arranque":
                        if val < 9.6:
                            estado.registrar_hecho("caida_tension_excesiva", "SI", categoria="medicion", tipo=FactType.CONDICION)
                        else:
                            estado.registrar_hecho("caida_tension_excesiva", "NO", categoria="medicion", tipo=FactType.CONDICION)
                            estado.registrar_hecho("voltaje_arranque_normal", "SI", categoria="medicion", tipo=FactType.CONDICION)
                    elif condicion == "reposo":
                        if val >= 12.4:
                            estado.registrar_hecho("voltaje_reposo_normal", "SI", categoria="medicion", tipo=FactType.CONDICION)
                    elif condicion == "con_carga_electrica" and val < 13.0:
                        estado.registrar_hecho("caida_voltaje_con_luces", "SI", categoria="medicion", tipo=FactType.CONDICION)

                if respuesta_retorno is None:
                    respuesta_retorno = {
                        "categoria_respuesta": "NUMERICO",
                        "campo": campo,
                        "valor": val,
                        "unidad": unidad,
                        "condicion_medicion": condicion,
                        "hecho": h.to_dict(),
                    }

            estado.limpiar_pregunta_pendiente()
            if respuesta_retorno:
                return respuesta_retorno

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

    # 7. Componente ya probado o reemplazado
    if any(c in texto_l for c in ("ya lo cambie", "ya lo cambié", "ya las cambié", "ya las cambie", "ya los cambié", "ya los cambie", "ya se cambiaron", "recién puesto", "recien puesto", "es nuevo", "son nuevas", "son nuevos")):
        pieza = "componente"
        for p_cand in ("bujías", "bujias", "bobinas", "bobina", "pastillas", "pastilla", "bomba", "filtro"):
            if p_cand in texto_preg:
                pieza = "bujías" if "buj" in p_cand else ("bobinas" if "bobin" in p_cand else ("pastillas" if "pastill" in p_cand else p_cand))
                break
        campo = f"reemplazado_{pieza}" if pieza != "componente" else "componente_reemplazado_reciente"
        h = estado.registrar_hecho(campo, f"{pieza} reemplazado(a)", categoria="antecedente", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        return {"categoria_respuesta": "COMPONENTE", "campo": campo, "valor": f"{pieza} reemplazado(a)", "hecho": h.to_dict()}

    if any(c in texto_l for c in ("ya lo revise", "ya lo revisé", "eso ya probe", "eso ya probé", "ya las revisé", "ya las revise")):
        pieza = "componente"
        for p_cand in ("bujías", "bujias", "bobinas", "bobina", "pastillas", "pastilla", "bomba", "filtro"):
            if p_cand in texto_preg:
                pieza = "bujías" if "buj" in p_cand else ("bobinas" if "bobin" in p_cand else ("pastillas" if "pastill" in p_cand else p_cand))
                break
        campo = f"probado_{pieza}" if pieza != "componente" else "componente_revisado_previo"
        h = estado.registrar_hecho(campo, f"{pieza} probado/descartado", categoria="componente_descartado", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        return {"categoria_respuesta": "COMPONENTE", "campo": campo, "valor": f"{pieza} probado/descartado", "hecho": h.to_dict()}

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
