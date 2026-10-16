"""Interpretación y registro de mediciones en respuestas breves."""
import re

from src.core.conversacion.models import EstadoOperativo, FactState, FactType, QuestionIntent

from .extractor_mediciones import extraer_todas_mediciones


def interpretar_mediciones(estado, texto_usuario, texto_l, texto_preg, intent_str):
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
        or any(u in texto_l for u in ("v", "volt", "psi", "bar", "kpa", "rpm", "mm", "ml", "inhg", "ohm", "kohm", "baja a", "marca", "da", "dio", "mide", "midio"))
        or any(k in texto_preg for k in ("voltaje", "multimetro", "presion", "manometro", "psi", "alabeo", "disco", "comparador", "espesor", "holgura", "mm"))
        or (estado.pending_question and estado.pending_question.get("intent") in (QuestionIntent.MEDICION_PRESION.value, QuestionIntent.MEDICION_VOLTAJE.value, QuestionIntent.MEDICION_TECNICA.value))
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

    return None
