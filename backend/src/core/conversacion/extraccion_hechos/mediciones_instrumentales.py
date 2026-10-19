"""Extracción de mediciones instrumentales y cuantitativas de taller (Fase 9 / Clean Architecture)."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from src.core.conversacion.extraccion_hechos.patrones_hechos import (
    PATRON_CAUSAL_INYECCION,
    PATRON_HALLAZGO_MAF,
    PATRON_MAP_FUERA_RANGO,
    PATRON_MEDICION,
    PATRON_MEZCLA_REPORTADA,
    PATRON_SENSOR_OXIGENO,
)
from src.core.conversacion.models import (
    ConversationState,
    FactType,
)


def extraer_mediciones_instrumentales(
    estado: ConversationState,
    texto_usuario: str,
    texto_normalizado: str,
) -> List[Dict[str, Any]]:
    """Extrae mediciones instrumentales cuantitativas y lecturas de sensores."""
    hechos_extraidos: List[Dict[str, Any]] = []
    texto_l = texto_usuario.lower()

    from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas

    mediciones_cuantitativas = InterpreteRespuestasCortas._extraer_todas_mediciones(
        texto_usuario.lower(),
        intent_str="MEDICION_TECNICA",
        texto_preg="",
        pending_q=estado.pending_question,
    )
    for val, unidad, condicion in mediciones_cuantitativas:
        if unidad in ("V", "mV"):
            es_caida_tension = bool(
                re.search(r"\b(?:ca[ií]da\s+de\s+tensi[oó]n|masa|chasis|tierra|borne\s+negativo)\b", texto_l)
            )
            if es_caida_tension:
                campo_v = "medicion_caida_tension_masa"
                tipo_v = "caida_tension"
                ctx_v = "masa_chasis"
            elif condicion in ("reposo", "durante_arranque", "contacto_on"):
                campo_v = f"medicion_voltaje_{condicion}"
                tipo_v = "voltaje_bateria"
                ctx_v = condicion
            else:
                campo_v = f'medicion_voltaje_{condicion}' if condicion else 'medicion_voltaje'
                tipo_v = 'voltaje_circuito'
                ctx_v = condicion or 'circuito_sin_identificar'

            valor_str = f"{val} {unidad}" + (f" ({condicion})" if condicion else "")
            h_m = estado.registrar_hecho(
                campo_v, valor_str, categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION
            )
            hechos_extraidos.append(h_m.to_dict())
            estado.registrar_medicion(
                tipo=tipo_v, valor=val, unidad=unidad, contexto=ctx_v, prueba=campo_v, estado="observado"
            )
            estado.registrar_prueba_completada(campo_v, f"{val} {unidad}")
            # No crear hechos de normalidad a partir de umbrales genéricos.
        elif unidad in ("mA", "A"):
            es_parasito = bool(re.search(r"\b(?:par[aá]sito|fuga|descarga|reposo|consumo)\b", texto_l))
            tipo_a = "consumo_parasito" if es_parasito else "corriente_electrica"
            campo_a = "medicion_consumo_parasito" if es_parasito else "medicion_corriente"
            ctx_a = "reposo_bateria" if es_parasito else "circuito"
            h_a = estado.registrar_hecho(
                campo_a,
                f"{val} {unidad}",
                categoria="medicion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_a.to_dict())
            estado.registrar_medicion(
                tipo=tipo_a, valor=val, unidad=unidad, contexto=ctx_a, prueba=campo_a, estado="observado"
            )
            estado.registrar_prueba_completada(campo_a, f"{val} {unidad}")
            if es_parasito:
                if "consumo_inicial" not in estado.hechos:
                    estado.registrar_hecho(
                        "consumo_inicial", f"{val} {unidad}", categoria="medicion", tipo=FactType.CONDICION
                    )
                if (
                    re.search(
                        r"\b(?:cay[oó]|baj[oó]|despu[eé]s|retirar|desconectar|qued[oó]|final)\b", texto_l
                    )
                    or "consumo_inicial" in estado.hechos
                ):
                    estado.registrar_hecho(
                        "consumo_final", f"{val} {unidad}", categoria="medicion", tipo=FactType.CONDICION
                    )
        elif unidad in ("PSI", "bar", "kPa", "mbar"):
            if "compresi" in texto_l or "cilindro" in texto_l:
                tipo_p = "compresion_motor"
                if condicion and ("cilindro" in condicion or "resto" in condicion):
                    campo_p = f"medicion_compresion_{condicion}"
                    ctx_p = condicion
                else:
                    campo_p = "medicion_compresion"
                    ctx_p = "cilindros"
            elif "dpf" in texto_l or "diferencial" in texto_l:
                tipo_p = "presion_diferencial_dpf"
                campo_p = "medicion_presion_diferencial"
                ctx_p = "dpf"
            elif "escape" in texto_l or "catalizador" in texto_l or "contrapresi" in texto_l:
                tipo_p = "contrapresion_escape"
                campo_p = "medicion_contrapresion_escape"
                ctx_p = "escape"
            else:
                tipo_p = "presion_combustible"
                if condicion:
                    campo_p = f"medicion_presion_{condicion}"
                    ctx_p = condicion
                else:
                    campo_p = "medicion_presion"
                    ctx_p = "riel_inyeccion"
            valor_p_str = f"{val} {unidad}" + (f" ({condicion})" if condicion else "")
            h_p = estado.registrar_hecho(
                campo_p, valor_p_str, categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION
            )
            hechos_extraidos.append(h_p.to_dict())
            estado.registrar_medicion(
                tipo=tipo_p, valor=val, unidad=unidad, contexto=ctx_p, prueba=campo_p, estado="observado"
            )
            estado.registrar_prueba_completada(campo_p, f"{val} {unidad}")
        elif unidad == "inHg":
            tipo_vac = (
                "restriccion_vacio"
                if any(w in texto_l for w in ("restricci", "diesel", "diésel", "linea", "línea"))
                else "vacio_motor"
            )
            campo_vac = (
                "medicion_restriccion_vacio" if tipo_vac == "restriccion_vacio" else "medicion_vacio_admision"
            )
            ctx_vac = "linea_combustible" if tipo_vac == "restriccion_vacio" else "multiple_admision"
            h_vac = estado.registrar_hecho(
                campo_vac,
                f"{val} {unidad}",
                categoria="medicion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_vac.to_dict())
            estado.registrar_medicion(
                tipo=tipo_vac,
                valor=val,
                unidad=unidad,
                contexto=ctx_vac,
                prueba=campo_vac,
                estado="observado",
            )
            estado.registrar_prueba_completada(campo_vac, f"{val} {unidad}")
        elif unidad == "mm":
            if any(w in texto_l for w in ("disco", "freno", "alabeo", "comparador")):
                tipo_mm = "alabeo_disco"
                campo_mm = "medicion_alabeo_disco"
                ctx_mm = "disco_freno"
            elif any(w in texto_l for w in ("rotula", "rótula", "juego", "axial", "holgura")):
                tipo_mm = "juego_rotula"
                campo_mm = "medicion_juego_rotula"
                ctx_mm = "rotula_suspension"
            else:
                tipo_mm = "dimension_metrologica"
                campo_mm = "medicion_longitud_mm"
                ctx_mm = "componente"
            h_mm = estado.registrar_hecho(
                campo_mm,
                f"{val} {unidad}",
                categoria="medicion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_mm.to_dict())
            estado.registrar_medicion(
                tipo=tipo_mm, valor=val, unidad=unidad, contexto=ctx_mm, prueba=campo_mm, estado="observado"
            )
            estado.registrar_prueba_completada(campo_mm, f"{val} {unidad}")
        elif unidad == "ml":
            tipo_vol = (
                "retorno_inyector"
                if any(w in texto_l for w in ("inyector", "retorno", "probeta"))
                else "volumen_fluido"
            )
            m_iny = re.search(r"\binyector\s*(\d+)\b", texto_l)
            if tipo_vol == "retorno_inyector" and m_iny:
                num_iny = m_iny.group(1)
                campo_vol = f"medicion_retorno_inyector_{num_iny}"
                ctx_vol = f"inyector_{num_iny}"
            else:
                campo_vol = (
                    "medicion_retorno_inyectores" if tipo_vol == "retorno_inyector" else "medicion_volumen"
                )
                ctx_vol = "inyectores_diesel" if tipo_vol == "retorno_inyector" else "fluido"
            h_vol = estado.registrar_hecho(
                campo_vol,
                f"{val} {unidad}",
                categoria="medicion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_vol.to_dict())
            estado.registrar_medicion(
                tipo=tipo_vol,
                valor=val,
                unidad=unidad,
                contexto=ctx_vol,
                prueba=campo_vol,
                estado="observado",
            )
            estado.registrar_prueba_completada(campo_vol, f"{val} {unidad}")
        elif unidad in ("ohm", "kohm"):
            tipo_ohm = "resistencia_electrica"
            campo_ohm = "medicion_resistencia_iac" if "iac" in texto_l else "medicion_resistencia"
            ctx_ohm = (
                "valvula_iac" if "iac" in texto_l else ("bobina" if "bobina" in texto_l else "componente")
            )
            h_ohm = estado.registrar_hecho(
                campo_ohm,
                f"{val} {unidad}",
                categoria="medicion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_ohm.to_dict())
            estado.registrar_medicion(
                tipo=tipo_ohm,
                valor=val,
                unidad=unidad,
                contexto=ctx_ohm,
                prueba=campo_ohm,
                estado="observado",
            )
            estado.registrar_prueba_completada(campo_ohm, f"{val} {unidad}")
        elif unidad == "g/s":
            tipo_gs = "flujo_aire_maf"
            campo_gs = "medicion_flujo_maf"
            ctx_gs = "sensor_maf"
            h_gs = estado.registrar_hecho(
                campo_gs,
                f"{val} {unidad}",
                categoria="medicion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_gs.to_dict())
            estado.registrar_medicion(
                tipo=tipo_gs, valor=val, unidad=unidad, contexto=ctx_gs, prueba=campo_gs, estado="observado"
            )
            estado.registrar_prueba_completada(campo_gs, f"{val} {unidad}")
        elif unidad in ("°C", "°F"):
            tipo_temp = "temperatura_medida"
            campo_temp = "medicion_temperatura"
            ctx_temp = "motor"
            h_temp = estado.registrar_hecho(
                campo_temp,
                f"{val} {unidad}",
                categoria="medicion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_temp.to_dict())
            estado.registrar_medicion(
                tipo=tipo_temp,
                valor=val,
                unidad=unidad,
                contexto=ctx_temp,
                prueba=campo_temp,
                estado="observado",
            )
            estado.registrar_prueba_completada(campo_temp, f"{val} {unidad}")
        elif unidad == "%":
            es_stft = bool(re.search(r"\bstft\b", texto_l))
            es_ltft = bool(re.search(r"\bltft\b", texto_l))
            campo_pct = (
                "medicion_stft" if es_stft else ("medicion_ltft" if es_ltft else "medicion_porcentaje")
            )
            tipo_pct = "trim_combustible" if (es_stft or es_ltft) else "porcentaje"
            ctx_pct = "inyeccion" if (es_stft or es_ltft) else "general"
            h_pct = estado.registrar_hecho(
                campo_pct,
                f"{val} {unidad}",
                categoria="medicion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_pct.to_dict())
            if es_stft:
                estado.registrar_hecho(
                    "stft_positivo",
                    f"+{int(val)}%" if val > 0 else f"{val}%",
                    categoria="medicion",
                    tipo=FactType.CONDICION,
                )
            estado.registrar_medicion(
                tipo=tipo_pct,
                valor=val,
                unidad=unidad,
                contexto=ctx_pct,
                prueba=campo_pct,
                estado="observado",
            )
            estado.registrar_prueba_completada(campo_pct, f"{val} {unidad}")
        elif unidad not in ("unidades",):
            tipo_gen = f"medicion_{unidad.lower()}"
            campo_gen = f"medicion_{unidad.lower()}"
            h_gen = estado.registrar_hecho(
                campo_gen,
                f"{val} {unidad}",
                categoria="medicion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_gen.to_dict())
            estado.registrar_medicion(
                tipo=tipo_gen,
                valor=val,
                unidad=unidad,
                contexto="general",
                prueba=campo_gen,
                estado="observado",
            )
            estado.registrar_prueba_completada(campo_gen, f"{val} {unidad}")

    if not mediciones_cuantitativas:
        for m_med in PATRON_MEDICION.finditer(texto_usuario):
            med_val = m_med.group(0).lower().replace(",", ".")
            h = estado.registrar_hecho(
                "medicion", med_val, categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION
            )
            hechos_extraidos.append(h.to_dict())

    if PATRON_MAP_FUERA_RANGO.search(texto_usuario):
        h_map = estado.registrar_hecho(
            "sensor_map_estado",
            "carga absoluta / sensor MAP reportado fuera de rango",
            categoria="medicion",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_map.to_dict())

    mezcla = PATRON_MEZCLA_REPORTADA.search(texto_usuario)
    if mezcla and not re.search(
        r"\b(?:no\s+(?:hay|presenta|arroja|marca)|descart(?:o|amos))\b.{0,35}"
        r"\bmezcla\s+" + mezcla.group(1) + r"\b",
        texto_usuario,
        re.IGNORECASE,
    ):
        h_mezcla = estado.registrar_hecho(
            f"mezcla_{mezcla.group(1).lower()}_reportada",
            f"mezcla {mezcla.group(1).lower()} reportada por el usuario",
            categoria="sintoma",
            texto_crudo=texto_usuario,
            tipo=FactType.SINTOMA,
        )
        hechos_extraidos.append(h_mezcla.to_dict())

    if PATRON_CAUSAL_INYECCION.search(texto_normalizado):
        h_inyeccion = estado.registrar_hecho(
            "caudal_inyectores_reportado",
            "usuario reporta caudal insuficiente en inyectores",
            categoria="sistema",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_inyeccion.to_dict())

    if PATRON_HALLAZGO_MAF.search(texto_normalizado):
        h_maf = estado.registrar_hecho(
            "sensor_maf_lectura_anomala_reportada",
            "usuario reporta lecturas anómalas del MAF",
            categoria="medicion",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_maf.to_dict())

    if PATRON_SENSOR_OXIGENO.search(texto_usuario) and re.search(
        r"\b(?:cambi[eé]|reemplaz[eé]|instal[eé])\b.{0,35}"
        r"\b(?:sensor|sonda|lambda|ox[ií]geno|o2)\b|"
        r"\b(?:sensor|sonda|lambda|ox[ií]geno|o2)\b.{0,35}"
        r"\b(?:cambi[eé]|reemplaz[eé]|instal[eé])\b",
        texto_usuario,
        re.IGNORECASE,
    ):
        h_sensor = estado.registrar_hecho(
            "sensor_oxigeno_reemplazado_reportado",
            "usuario reporta sensor de oxígeno reemplazado; síntoma persiste",
            categoria="antecedente",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_sensor.to_dict())

    return hechos_extraidos
