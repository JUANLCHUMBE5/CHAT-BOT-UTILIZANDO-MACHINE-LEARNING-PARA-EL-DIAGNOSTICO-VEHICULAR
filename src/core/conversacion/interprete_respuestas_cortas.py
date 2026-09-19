"""Módulo de interpretación contextual de respuestas cortas, ambiguas y 'no sé' en WhatsApp."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

from src.core.conversacion.gestor_plan_b import GestorPlanB
from src.core.conversacion.models import (
    ConversationState,
    FactState,
    FactType,
    QuestionIntent,
)

PATRON_OPCION_NUMERICA = re.compile(
    r"^(la\s+)?(opci[oó]n\s+)?([1-3]|primera|segunda|tercera|1️⃣|2️⃣|3️⃣)\b", re.IGNORECASE
)

PATRON_NO_SE = re.compile(
    r"\b(no\s+s[eé]|ni\s+idea|no\s+me\s+fij[eé]|no\s+sabr[ií]a|no\s+estoy\s+seguro|desconozco)\b",
    re.IGNORECASE,
)

PATRON_NO_APLICA = re.compile(
    r"\b(no\s+aplica|eso\s+no\s+aplica|no\s+corresponde|no\s+tiene\s+ese\s+sistema|no\s+cuenta\s+con\s+eso)\b",
    re.IGNORECASE,
)

PATRON_AMBIGUO = re.compile(
    r"\b(a\s+veces|creo|creo\s+que\s+s[ií]|m[aá]s\s+o\s+menos|puede\s+ser|de\s+vez\s+en\s+cuando|a\s+ratos|tal\s+vez)\b",
    re.IGNORECASE,
)

PATRON_NUMERICO_MEDICION = re.compile(
    r"(?:baja\s+a\s+|marca\s+|mide\s+|llega\s+a\s+|da\s+|tengo\s+|est[aá]\s+en\s+)?(\d+(?:[.,]\d+)?)\s*(psi|bar|kpa|mv|v(?:oltios?|olts?)?|ma|a(?:mperios?)?|ohm(?:ios)?|Ω|°c|°f|rpm|km/h|%|mm|ms)?\b",
    re.IGNORECASE,
)

CUES_RESPUESTA_CORTA = (
    "la 1", "la 2", "la 3", "opcion 1", "opcion 2", "opcion 3",
    "ya lo cambie", "ya lo cambié", "eso ya lo revise", "eso ya lo revisé",
    "solo caliente", "solo en frio", "solo en semaforo", "solo parado",
    "no se", "no sé", "ni idea", "creo que si", "creo que sí", "a veces",
    "no aplica", "eso no aplica", "ninguno", "ninguna", "no tengo",
    "no cuento", "no tengo tester", "tengo tester", "se mantienen igual",
    "permanecen igual", "se ponen tenues", "bajan bastante",
    "no lo he revisado", "no he revisado", "no revisé", "no revise",
    "no tengo herramientas", "sin herramientas", "no sé usarlo", "no se usarlo",
    "no sé cómo", "no se como", "no sé bien cómo", "no se bien como",
    "cómo comprobar", "como comprobar", "cómo revisar", "como revisar",
    "ya conseguí", "ya consegui", "me prestaron", "no dispongo",
    "sí tengo", "si tengo", "sí cuento", "si cuento", "lo tengo",
    "ya lo conecté", "ya lo conecte", "sí maestro", "si maestro",
)


class InterpreteRespuestasCortas:
    """Interpreta respuestas breves del usuario respecto a la última pregunta formulada."""

    @staticmethod
    def es_respuesta_corta(texto: str) -> bool:
        """Determina si un mensaje es una respuesta breve dependiente de contexto."""
        if not texto:
            return False
        limpio = texto.strip().lower()
        palabras = limpio.split()
        if len(palabras) <= 4:
            return True
        if any(c in limpio for c in CUES_RESPUESTA_CORTA):
            return True
        # Afirmaciones (simples o compuestas con preguntas de seguimiento o herramientas)
        if re.search(r"^(?:s[ií](?:[,\s]+maestro|[,\s]+amigo|[,\s]+bot|[,\s]+carbot)?|[aá]firmativo|correcto|lo\s+tengo|ya\s+lo\s+conect[eé]|s[ií]\s+(?:tengo|cuento|dispongo))\b", limpio):
            return True
        # Menciones numéricas o con unidades técnicas
        if re.search(r"\b\d+(?:[.,]\d+)?\s*(?:psi|bar|kpa|mv|v(?:oltios?)?|ma|a(?:mperios?)?|ohm|Ω|°c|°f|rpm|km/h|%|mm|ms)?\b", limpio):
            return True
        from src.core.conversacion.gestor_plan_b import GestorPlanB
        if (
            GestorPlanB.detectar_indisponibilidad_en_texto(limpio)
            or GestorPlanB.detectar_no_revisado(limpio)
            or GestorPlanB.detectar_no_sabe_usar(limpio)
            or GestorPlanB.detectar_no_sabe_realizar(limpio)
            or GestorPlanB.detectar_recuperacion_herramienta(limpio)
        ):
            return True
        return False

    @staticmethod
    def _extraer_medicion(
        texto_l: str,
        intent_str: str,
        texto_preg: str,
        pending_q: Optional[Dict[str, Any]] = None,
    ) -> Optional[Tuple[float, str, Optional[str]]]:
        """Extrae valor, unidad y condición operacional de una respuesta técnica numérica sin mezclar magnitudes."""
        m = PATRON_NUMERICO_MEDICION.search(texto_l)
        if not m:
            return None
        val_str = m.group(1).replace(",", ".")
        try:
            val = float(val_str)
        except ValueError:
            return None

        unidad_raw = (m.group(2) or "").lower()
        if "psi" in unidad_raw:
            unidad = "PSI"
        elif "bar" in unidad_raw:
            unidad = "bar"
        elif "kpa" in unidad_raw:
            unidad = "kPa"
        elif "mv" in unidad_raw:
            unidad = "mV"
        elif "v" in unidad_raw or "volt" in unidad_raw:
            unidad = "V"
        elif "ma" in unidad_raw:
            unidad = "mA"
        elif "a" in unidad_raw or "amp" in unidad_raw:
            unidad = "A"
        elif "ohm" in unidad_raw or "Ω" in unidad_raw:
            unidad = "ohm"
        elif "°c" in unidad_raw or "c" == unidad_raw:
            unidad = "°C"
        elif "°f" in unidad_raw or "f" == unidad_raw:
            unidad = "°F"
        elif "rpm" in unidad_raw:
            unidad = "RPM"
        elif "km/h" in unidad_raw:
            unidad = "km/h"
        elif "%" in unidad_raw:
            unidad = "%"
        elif "mm" in unidad_raw:
            unidad = "mm"
        elif "ms" in unidad_raw:
            unidad = "ms"
        elif pending_q and pending_q.get("expected_units"):
            unidad = pending_q["expected_units"][0]
        elif "presion" in texto_preg or "manometro" in texto_preg or "combustible" in texto_preg:
            unidad = "PSI"
        elif "volt" in texto_preg or "multimetro" in texto_preg or "bateria" in texto_preg:
            unidad = "V"
        else:
            unidad = "unidades"

        # Determinación de condición de medición sin inventar si no se especifica
        condicion = None
        if any(w in texto_l for w in ("arranque", "doy arranque", "al prender", "al dar contacto", "intentar prender", "baja a", "al dar marcha", "doy marcha")):
            condicion = "durante_arranque"
        elif any(w in texto_l for w in ("contacto", "llave en on", "contacto puesto")):
            condicion = "contacto_on"
        elif any(w in texto_l for w in ("reposo", "apagado", "motor apagado", "en frio", "en frío")):
            condicion = "reposo"
        elif any(w in texto_l for w in ("ralenti", "ralentí", "prendido", "encendido", "andando", "cargando")):
            condicion = "ralenti_carga"

        return val, unidad, condicion

    @classmethod
    def interpretar(
        cls,
        estado: ConversationState,
        texto_usuario: str,
    ) -> Optional[Dict[str, Any]]:
        """Mapea una respuesta corta a hechos clínicos concretos según la última pregunta."""
        ultima_preg = estado.ultima_pregunta()
        if not ultima_preg:
            return None

        intent_str = str(ultima_preg.get("intent", QuestionIntent.GENERAL.value))
        texto_preg = str(ultima_preg.get("texto", "")).lower()
        texto_l = texto_usuario.strip().lower()
        hipotesis = ultima_preg.get("hipotesis") or []

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

        # 0.05 Manejo de 'No sé realizar la prueba / cómo comprobar' (Orientación y Plan B seguro)
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

        # 0.1 Manejo de 'No sé' / 'Ni idea' (NUNCA convertir en 'NO')
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
        if re.search(r"\d+(?:[.,]\d+)?", texto_l) and (
            intent_str in (
                QuestionIntent.MEDICION_TECNICA.value,
                QuestionIntent.MEDICION_VOLTAJE.value,
                QuestionIntent.MEDICION_PRESION.value,
                QuestionIntent.DISPONIBILIDAD_HERRAMIENTA.value,
            )
            or any(u in texto_l for u in ("v", "volt", "psi", "bar", "kpa", "baja a", "marca", "da"))
            or any(k in texto_preg for k in ("voltaje", "multimetro", "presion", "manometro", "psi"))
            or (estado.pending_question and estado.pending_question.get("intent") in (QuestionIntent.MEDICION_PRESION.value, QuestionIntent.MEDICION_VOLTAJE.value))
        ):
            medicion = cls._extraer_medicion(texto_l, intent_str, texto_preg, estado.pending_question)
            if medicion:
                val, unidad, condicion = medicion
                if unidad in ("PSI", "bar", "kPa"):
                    campo = "medicion_presion"
                    tipo_med = "presion_combustible"
                    contexto_med = "riel_inyeccion"
                elif unidad in ("V", "mV"):
                    campo = "medicion_voltaje"
                    tipo_med = "voltaje_bateria"
                    contexto_med = "bateria"
                elif intent_str == QuestionIntent.MEDICION_VOLTAJE.value or "voltaje" in texto_preg or "multimetro" in texto_preg:
                    campo = "medicion_voltaje"
                    unidad = "V"
                    tipo_med = "voltaje_bateria"
                    contexto_med = "bateria"
                elif intent_str == QuestionIntent.MEDICION_PRESION.value or "presion" in texto_preg or "manometro" in texto_preg:
                    campo = "medicion_presion"
                    unidad = "PSI"
                    tipo_med = "presion_combustible"
                    contexto_med = "riel_inyeccion"
                else:
                    campo = f"medicion_{unidad.lower()}"
                    tipo_med = "medicion_tecnica"
                    contexto_med = "general"

                h = estado.registrar_hecho(
                    campo=campo,
                    valor=f"{val} {unidad}" + (f" ({condicion})" if condicion else ""),
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
                estado.limpiar_pregunta_pendiente()

                if unidad == "V" and condicion == "durante_arranque":
                    if val < 9.6:
                        estado.registrar_hecho("caida_tension_excesiva", "SI", categoria="medicion", tipo=FactType.CONDICION)
                    else:
                        estado.registrar_hecho("caida_tension_excesiva", "NO", categoria="medicion", tipo=FactType.CONDICION)

                return {
                    "categoria_respuesta": "NUMERICO",
                    "campo": campo,
                    "valor": val,
                    "unidad": unidad,
                    "condicion_medicion": condicion,
                    "hecho": h.to_dict(),
                }

        # 3. Disponibilidad de herramientas y estado de comprobación (GestorPlanB - Fase 9.11)
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

        # 4. Respuestas a COMPORTAMIENTO_ARRANQUE y Luces del Tablero (Plan B sin herramienta)
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

        # 6. Respuestas a preguntas de condición de operación (ralentí, velocidad, frenado)
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

        # 7b. Resultado negativo de inspección (prueba física realizada sin detectar anomalía)
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

        # 9. Respuestas genéricas SÍ / NO (solo si no correspondía a un intent específico anterior)
        if texto_l in ("si", "sí", "afirmativo", "correcto"):
            h = estado.registrar_hecho(f"confirmado_pregunta_{estado.turno_actual}", "sí", categoria="confirmacion", texto_crudo=texto_usuario)
            return {"categoria_respuesta": "AFIRMACION", "campo": "confirmacion", "valor": "sí", "hecho": h.to_dict()}
        if texto_l in ("no", "negativo"):
            h = estado.registrar_hecho(f"descartado_pregunta_{estado.turno_actual}", "no", categoria="descarte", texto_crudo=texto_usuario)
            return {"categoria_respuesta": "NEGACION", "campo": "confirmacion", "valor": "no", "hecho": h.to_dict()}

        return None
