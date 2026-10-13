"""Extracción de mediciones instrumentales, pruebas de taller y estado de herramientas."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from src.core.conversacion.detector_polaridad import DetectorPolaridad
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
    DtcStatus,
    FactState,
    FactType,
)


def extraer_comprobaciones_taller(
    estado: ConversationState,
    texto_usuario: str,
    texto_normalizado: str,
) -> List[Dict[str, Any]]:
    """Extrae mediciones cuantitativas, componentes revisados, chispa y herramientas."""
    hechos_extraidos: List[Dict[str, Any]] = []
    texto_l = texto_usuario.lower()

    # 1. Mediciones cuantitativas
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
                or (val < 2.0 and not condicion)
            )
            if es_caida_tension:
                campo_v = "medicion_caida_tension_masa"
                tipo_v = "caida_tension"
                ctx_v = "masa_chasis"
            elif condicion in ("reposo", "durante_arranque", "contacto_on"):
                campo_v = f"medicion_voltaje_{condicion}"
                tipo_v = "voltaje_bateria"
                ctx_v = condicion
            elif 13.0 <= val <= 15.5:
                campo_v = "medicion_voltaje_alternador"
                tipo_v = "voltaje_alternador"
                ctx_v = "carga_alternador"
            else:
                campo_v = f"medicion_voltaje_{condicion}" if condicion else "medicion_voltaje"
                tipo_v = "voltaje_bateria" if val < 13.0 else "voltaje_alternador"
                ctx_v = condicion or "circuito"

            valor_str = f"{val} {unidad}" + (f" ({condicion})" if condicion else "")
            h_m = estado.registrar_hecho(campo_v, valor_str, categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_m.to_dict())
            estado.registrar_medicion(tipo=tipo_v, valor=val, unidad=unidad, contexto=ctx_v, prueba=campo_v, estado="observado")
            estado.registrar_prueba_completada(campo_v, f"{val} {unidad}")
            if condicion == "durante_arranque":
                if val < 9.6:
                    h_c = estado.registrar_hecho("caida_tension_excesiva", "SI", categoria="medicion", tipo=FactType.CONDICION)
                else:
                    h_c = estado.registrar_hecho("caida_tension_excesiva", "NO", categoria="medicion", tipo=FactType.CONDICION)
                    h_a = estado.registrar_hecho("voltaje_arranque_normal", "SI", categoria="medicion", tipo=FactType.CONDICION)
                    hechos_extraidos.append(h_a.to_dict())
                hechos_extraidos.append(h_c.to_dict())
            elif condicion == "reposo" and val >= 12.4:
                h_r = estado.registrar_hecho("voltaje_reposo_normal", "SI", categoria="medicion", tipo=FactType.CONDICION)
                hechos_extraidos.append(h_r.to_dict())
        elif unidad in ("mA", "A"):
            es_parasito = bool(re.search(r"\b(?:par[aá]sito|fuga|descarga|reposo|consumo)\b", texto_l))
            tipo_a = "consumo_parasito" if es_parasito else "corriente_electrica"
            campo_a = "medicion_consumo_parasito" if es_parasito else "medicion_corriente"
            ctx_a = "reposo_bateria" if es_parasito else "circuito"
            h_a = estado.registrar_hecho(campo_a, f"{val} {unidad}", categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_a.to_dict())
            estado.registrar_medicion(tipo=tipo_a, valor=val, unidad=unidad, contexto=ctx_a, prueba=campo_a, estado="observado")
            estado.registrar_prueba_completada(campo_a, f"{val} {unidad}")
            if es_parasito:
                if "consumo_inicial" not in estado.hechos:
                    estado.registrar_hecho("consumo_inicial", f"{val} {unidad}", categoria="medicion", tipo=FactType.CONDICION)
                if re.search(r"\b(?:cay[oó]|baj[oó]|despu[eé]s|retirar|desconectar|qued[oó]|final)\b", texto_l) or "consumo_inicial" in estado.hechos:
                    estado.registrar_hecho("consumo_final", f"{val} {unidad}", categoria="medicion", tipo=FactType.CONDICION)
        elif unidad in ("PSI", "bar", "kPa", "mbar"):
            if "compresi" in texto_l or "cilindro" in texto_l:
                tipo_p = "compresion_motor"
                campo_p = "medicion_compresion"
                ctx_p = "cilindros"
            elif "dpf" in texto_l or "diferencial" in texto_l:
                tipo_p = "presion_diferencial_dpf"
                campo_p = "medicion_presion_diferencial"
                ctx_p = "dpf"
            else:
                tipo_p = "presion_combustible"
                campo_p = "medicion_presion"
                ctx_p = "riel_inyeccion"
            h_p = estado.registrar_hecho(campo_p, f"{val} {unidad}", categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_p.to_dict())
            estado.registrar_medicion(tipo=tipo_p, valor=val, unidad=unidad, contexto=ctx_p, prueba=campo_p, estado="observado")
            estado.registrar_prueba_completada(campo_p, f"{val} {unidad}")
        elif unidad == "inHg":
            tipo_vac = "restriccion_vacio" if any(w in texto_l for w in ("restricci", "diesel", "diésel", "linea", "línea")) else "vacio_motor"
            campo_vac = "medicion_restriccion_vacio" if tipo_vac == "restriccion_vacio" else "medicion_vacio_admision"
            ctx_vac = "linea_combustible" if tipo_vac == "restriccion_vacio" else "multiple_admision"
            h_vac = estado.registrar_hecho(campo_vac, f"{val} {unidad}", categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_vac.to_dict())
            estado.registrar_medicion(tipo=tipo_vac, valor=val, unidad=unidad, contexto=ctx_vac, prueba=campo_vac, estado="observado")
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
            h_mm = estado.registrar_hecho(campo_mm, f"{val} {unidad}", categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_mm.to_dict())
            estado.registrar_medicion(tipo=tipo_mm, valor=val, unidad=unidad, contexto=ctx_mm, prueba=campo_mm, estado="observado")
            estado.registrar_prueba_completada(campo_mm, f"{val} {unidad}")
        elif unidad == "ml":
            tipo_vol = "retorno_inyector" if any(w in texto_l for w in ("inyector", "retorno", "probeta")) else "volumen_fluido"
            campo_vol = "medicion_retorno_inyectores" if tipo_vol == "retorno_inyector" else "medicion_volumen"
            ctx_vol = "inyectores_diesel" if tipo_vol == "retorno_inyector" else "fluido"
            h_vol = estado.registrar_hecho(campo_vol, f"{val} {unidad}", categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_vol.to_dict())
            estado.registrar_medicion(tipo=tipo_vol, valor=val, unidad=unidad, contexto=ctx_vol, prueba=campo_vol, estado="observado")
            estado.registrar_prueba_completada(campo_vol, f"{val} {unidad}")
        elif unidad in ("ohm", "kohm"):
            tipo_ohm = "resistencia_electrica"
            campo_ohm = "medicion_resistencia_iac" if "iac" in texto_l else "medicion_resistencia"
            ctx_ohm = "valvula_iac" if "iac" in texto_l else ("bobina" if "bobina" in texto_l else "componente")
            h_ohm = estado.registrar_hecho(campo_ohm, f"{val} {unidad}", categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_ohm.to_dict())
            estado.registrar_medicion(tipo=tipo_ohm, valor=val, unidad=unidad, contexto=ctx_ohm, prueba=campo_ohm, estado="observado")
            estado.registrar_prueba_completada(campo_ohm, f"{val} {unidad}")
        elif unidad == "g/s":
            tipo_gs = "flujo_aire_maf"
            campo_gs = "medicion_flujo_maf"
            ctx_gs = "sensor_maf"
            h_gs = estado.registrar_hecho(campo_gs, f"{val} {unidad}", categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_gs.to_dict())
            estado.registrar_medicion(tipo=tipo_gs, valor=val, unidad=unidad, contexto=ctx_gs, prueba=campo_gs, estado="observado")
            estado.registrar_prueba_completada(campo_gs, f"{val} {unidad}")
        elif unidad in ("°C", "°F"):
            tipo_temp = "temperatura_medida"
            campo_temp = "medicion_temperatura"
            ctx_temp = "motor"
            h_temp = estado.registrar_hecho(campo_temp, f"{val} {unidad}", categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_temp.to_dict())
            estado.registrar_medicion(tipo=tipo_temp, valor=val, unidad=unidad, contexto=ctx_temp, prueba=campo_temp, estado="observado")
            estado.registrar_prueba_completada(campo_temp, f"{val} {unidad}")
        elif unidad == "%":
            es_stft = bool(re.search(r"\bstft\b", texto_l))
            es_ltft = bool(re.search(r"\bltft\b", texto_l))
            campo_pct = "medicion_stft" if es_stft else ("medicion_ltft" if es_ltft else "medicion_porcentaje")
            tipo_pct = "trim_combustible" if (es_stft or es_ltft) else "porcentaje"
            ctx_pct = "inyeccion" if (es_stft or es_ltft) else "general"
            h_pct = estado.registrar_hecho(campo_pct, f"{val} {unidad}", categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_pct.to_dict())
            if es_stft:
                estado.registrar_hecho("stft_positivo", f"+{int(val)}%" if val > 0 else f"{val}%", categoria="medicion", tipo=FactType.CONDICION)
            estado.registrar_medicion(tipo=tipo_pct, valor=val, unidad=unidad, contexto=ctx_pct, prueba=campo_pct, estado="observado")
            estado.registrar_prueba_completada(campo_pct, f"{val} {unidad}")
        elif unidad not in ("unidades",):
            tipo_gen = f"medicion_{unidad.lower()}"
            campo_gen = f"medicion_{unidad.lower()}"
            h_gen = estado.registrar_hecho(campo_gen, f"{val} {unidad}", categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_gen.to_dict())
            estado.registrar_medicion(tipo=tipo_gen, valor=val, unidad=unidad, contexto="general", prueba=campo_gen, estado="observado")
            estado.registrar_prueba_completada(campo_gen, f"{val} {unidad}")

    for m_med in PATRON_MEDICION.finditer(texto_usuario):
        med_val = m_med.group(0).lower().replace(",", ".")
        h = estado.registrar_hecho("medicion", med_val, categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if re.search(r"\b(?:rizado|ripple|corriente\s+alterna|v\s*ac)\b", texto_l):
        h_riz = estado.registrar_hecho("rizado_ac", "alto / diodo abierto", categoria="medicion", tipo=FactType.CONDICION)
        hechos_extraidos.append(h_riz.to_dict())

    if re.search(r"\b(?:co2|l[ií]quido\s+azul|probador\s+qu[ií]mico|fug(?:as?)?\s+de\s+combusti[oó]n|vir[oó]|amarillo)\b", texto_l):
        h_co2 = estado.registrar_hecho("co2_quimico_positivo", "positivo / presencia de CO2", categoria="prueba_quimica", tipo=FactType.CONDICION)
        hechos_extraidos.append(h_co2.to_dict())

    if re.search(r"\b(?:mud[oó]|migr[oó])\b.{0,30}\b(?:cilindro\s+1|p0301)\b", texto_l) or re.search(r"\bintercambi[eé]\s+la\s+bobina\b", texto_l):
        h_mig = estado.registrar_hecho("bobina_migro_cilindro_1", "falla migró a cilindro 1", categoria="prueba_cruzada", tipo=FactType.CONDICION)
        hechos_extraidos.append(h_mig.to_dict())

    if re.search(r"\b(?:empaque\s+de\s+culata|junta\s+de\s+culata)\b", texto_l) and re.search(r"\b(?:quemado|soplado|roto|solucionado|cambio|nuevo)\b", texto_l):
        h_cul = estado.registrar_hecho("empaque_culata", "empaque de culata confirmado", categoria="componente_averiado", tipo=FactType.CONDICION)
        hechos_extraidos.append(h_cul.to_dict())

    if re.search(r"\btermostato\b.{0,40}\b(?:olla|term[oó]metro|abre|perfecto|descartado|bien)\b", texto_l):
        h_term = estado.registrar_hecho("termostato_descartado", "termostato comprobado normal", categoria="verificacion_fisica", tipo=FactType.CONDICION)
        hechos_extraidos.append(h_term.to_dict())

    if re.search(r"\bresistencia\b.{0,50}\b(?:abiert[ao]|quemad[ao]|ol|infinita|primera\s+velocidad)\b", texto_l):
        h_res = estado.registrar_hecho("resistencia_baja_quemada", "resistencia quemada", categoria="componente_averiado", tipo=FactType.CONDICION)
        hechos_extraidos.append(h_res.to_dict())

    if re.search(r"\b(?:en\s+tr[aá]fico|tr[aá]fico\s+pesado|parado\s+en\s+el\s+sem[aá]foro)\b", texto_l):
        h_traf = estado.registrar_hecho("condicion", "en trafico / ralenti", categoria="condicion", tipo=FactType.CONDICION)
        hechos_extraidos.append(h_traf.to_dict())

    m_sol = re.search(
        r"\b(?:qued[oó]\s+resuelto|caso\s+solucionado|falla\s+qued[oó]\s+resuelta|solucionado\s+con|reparaci[oó]n:\s*)\s*(?:cambiando|con|reemplazando|instalando)?\s*([a-záéíóú0-9\s/-]+?)(?:\.|$|,|\s+genera|\s+consolida)",
        texto_l,
    )
    if m_sol:
        h_sol = estado.registrar_hecho("solucion", m_sol.group(1).strip(), categoria="reparacion_confirmada", tipo=FactType.CONDICION)
        hechos_extraidos.append(h_sol.to_dict())

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

    # 2. Componentes revisados o reemplazados
    if any(c in texto_l for c in ("ya cambie", "ya cambié", "ya las cambié", "ya las cambie", "ya los cambié", "ya los cambie", "ya le cambié", "ya se cambiaron", "ya se cambió", "nuevo", "nueva", "cambiamos", "recién cambiado", "recien cambiado", "recién cambié")):
        for pieza in ("bujias", "bujías", "bobinas", "bobina", "bomba", "filtro", "termostato", "pastillas", "aceite"):
            if pieza in texto_l:
                canon = "bujías" if "buj" in pieza else ("bobinas" if "bobin" in pieza else pieza)
                h = estado.registrar_hecho(f"reemplazado_{canon}", f"{canon} reemplazado(a)", categoria="antecedente", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())

    if any(c in texto_l for c in ("ya revise", "ya revisé", "probe", "probé", "intercambie", "intercambié", "descarte", "descarté", "esta bien", "está bien", "esta ok", "está ok")):
        for pieza in ("bujias", "bujías", "bobinas", "bobina", "bomba", "fusible", "presion", "presión", "compresion", "compresión", "bateria", "batería", "alternador", "arrancador"):
            if pieza in texto_l:
                canon = "bujías" if "buj" in pieza else ("bobinas" if "bobin" in pieza else ("batería" if "bater" in pieza else pieza))
                h = estado.registrar_hecho(f"probado_{canon}", f"{canon} probado/descartado", categoria="componente_descartado", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())

    for campo_nr, val_nr in DetectorPolaridad.extraer_componentes_no_revisados(texto_usuario):
        h = estado.registrar_hecho(
            campo_nr, val_nr, categoria="inspeccion_pendiente",
            estado=FactState.NO_REVISADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())

    for campo_norm, val_norm in DetectorPolaridad.extraer_sistemas_normales(texto_usuario):
        h = estado.registrar_hecho(
            campo_norm, val_norm, categoria="sistema_normal",
            estado=FactState.AUSENTE_NEGADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())

    menciona_chispa = bool(re.search(r"\b(chispa|salto\s+de\s+chispa|probador\s+de\s+chispa)\b", texto_l))
    chispa_ausente = bool(
        menciona_chispa
        and re.search(
            r"\b(no\s+(?:hay|tiene|da|sale|se\s+observa|se\s+ve)\s+(?:ninguna\s+)?chispa|sin\s+chispa|no\s+salta\s+chispa|chispa\s+ausente)\b",
            texto_l,
        )
    )
    chispa_presente = bool(
        menciona_chispa
        and not chispa_ausente
        and re.search(
            r"\b(se\s+observa(?:\s+una)?\s+chispa|se\s+ve(?:\s+una)?\s+chispa|hay\s+chispa|da\s+chispa|chispa\s+(?:azul|azulada|constante|uniforme|fuerte)|salto\s+(?:constante\s+)?de\s+chispa)\b",
            texto_l,
        )
    )
    if chispa_ausente:
        h = estado.registrar_hecho("resultado_prueba_chispa", "chispa ausente", categoria="prueba_diagnostica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        estado.registrar_prueba_completada("prueba_chispa", "SIN_CHISPA", detalles={"texto_crudo": texto_usuario})
        hechos_extraidos.append(h.to_dict())
    elif chispa_presente:
        h = estado.registrar_hecho("resultado_prueba_chispa", "chispa presente y observable", categoria="prueba_diagnostica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        estado.registrar_prueba_completada("prueba_chispa", "CHISPA_PRESENTE", detalles={"texto_crudo": texto_usuario})
        hechos_extraidos.append(h.to_dict())

    # 3. Disponibilidad de herramientas
    if re.search(r"\b(s[ií]\s+(?:tengo|cuento|dispongo)|tengo\s+(?:un\s+)?|cuento\s+con\s+(?:un\s+)?|lo\s+tengo|ya\s+lo\s+conect[eé]|s[ií]\s+maestro.*(?:man[oó]metro|mult[ií]metro|esc[aá]ner|tester))\b", texto_l):
        if "manometro" in texto_l or "manómetro" in texto_l or "presion" in texto_l:
            estado.marcar_herramienta_disponible("manometro")
            h = estado.registrar_hecho("manometro_disponible", "SI", categoria="herramienta", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())
        if "multimetro" in texto_l or "multímetro" in texto_l or "tester" in texto_l:
            estado.marcar_herramienta_disponible("multimetro")
            h = estado.registrar_hecho("multimetro_disponible", "SI", categoria="herramienta", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())
        if "escaner" in texto_l or "escáner" in texto_l or "scanner" in texto_l:
            estado.marcar_herramienta_disponible("escaner")
            h = estado.registrar_hecho("escaner_disponible", "SI", categoria="herramienta", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())
        if "osciloscopio" in texto_l:
            estado.marcar_herramienta_disponible("osciloscopio")
            h = estado.registrar_hecho("osciloscopio_disponible", "SI", categoria="herramienta", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

    if re.search(r"\b(no\s+(?:tengo|cuento|dispongo|se\s+ha\s+conectado|est[aá]\s+conectado|conect[eé]|se\s+conect[oó])|sin\s+|todav[ií]a\s+no\s+(?:se\s+ha\s+)?conectado|a[uú]n\s+no\s+(?:se\s+ha\s+)?conectado)\b", texto_l):
        if "escaner" in texto_l or "escáner" in texto_l or "scanner" in texto_l or "obd" in texto_l:
            estado.marcar_herramienta_indisponible("escaner")
            estado.dtc_status = DtcStatus.DTC_DESCONOCIDO
            h = estado.registrar_hecho("escaner_disponible", "NO", categoria="herramienta", estado=FactState.NO_APLICA, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())
        if "osciloscopio" in texto_l:
            estado.marcar_herramienta_indisponible("osciloscopio")
            h = estado.registrar_hecho("osciloscopio_disponible", "NO", categoria="herramienta", estado=FactState.NO_APLICA, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())
            h_sin = estado.registrar_hecho("sin_osciloscopio", "SI", categoria="herramienta", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_sin.to_dict())
        if "manometro" in texto_l or "manómetro" in texto_l:
            estado.marcar_herramienta_indisponible("manometro")
            h = estado.registrar_hecho("manometro_disponible", "NO", categoria="herramienta", estado=FactState.NO_APLICA, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())
        if "multimetro" in texto_l or "multímetro" in texto_l or "tester" in texto_l:
            estado.marcar_herramienta_indisponible("multimetro")
            h = estado.registrar_hecho("multimetro_disponible", "NO", categoria="herramienta", estado=FactState.NO_APLICA, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

    if re.search(r"\b(no\s+s[eé]\s+si\s+(?:tiene|hay)|no\s+me\s+he\s+fijado\s+si\s+(?:tiene|hay)|no\s+tengo\s+idea\s+si)\b", texto_l):
        if any(w in texto_l for w in ("codigo", "codigos", "código", "códigos", "dtc")):
            estado.dtc_status = DtcStatus.DTC_DESCONOCIDO
            h = estado.registrar_hecho("codigos_dtc_observados", "desconocido", categoria="dtc", estado=FactState.DESCONOCIDO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

    # 4. Acople de compresor de A/C
    es_acople_positivo = bool(
        re.search(
            r"\b(compresor\s+s[ií]\s+acopla|s[ií]\s+acopla|s[ií],?\s+se\s+escucha\s+el\s+clic|escucho\s+el\s+clic|se\s+oye\s+el\s+clic|el\s+compresor\s+entra|entra\s+el\s+compresor|engancha\s+el\s+compresor|el\s+compresor\s+engancha|bajan\s+(?:un\s+poco\s+|ligeramente\s+)?las\s+(?:revoluciones|rpm))\b",
            texto_l,
        )
        and not re.search(r"\bno\s+(?:acopla|entra|engancha|se\s+escucha)\b", texto_l)
    )
    es_acople_negativo = bool(
        re.search(
            r"\b(no\s+acopla|no\s+entra|no\s+engancha|no\s+pega|no\s+se\s+(?:escucha|oye)\s+(?:el\s+)?clic|silencio\s+total|no\s+activa)\b",
            texto_l,
        )
        and any(w in texto_l for w in ("compresor", "clic", "acopla", "entra", "a/c", "clima"))
    )
    es_acople_desconocido = bool(
        re.search(r"\b(no\s+s[eé]\s+si\s+acopla|no\s+s[eé]\s+si\s+entra|no\s+me\s+fij[eé]\s+si\s+acopla)\b", texto_l)
    )
    if es_acople_desconocido:
        h = estado.registrar_hecho("compresor_acopla", "desconocido", categoria="inspeccion", estado=FactState.DESCONOCIDO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
    elif es_acople_positivo:
        h = estado.registrar_hecho("compresor_acopla", "SI", categoria="inspeccion", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        estado.registrar_prueba_completada("acople_compresor", "SI")
        hechos_extraidos.append(h.to_dict())
    elif es_acople_negativo:
        h = estado.registrar_hecho("compresor_acopla", "NO", categoria="inspeccion", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        estado.registrar_prueba_completada("acople_compresor", "NO")
        hechos_extraidos.append(h.to_dict())

    # 5. Otras comprobaciones clínicas de taller
    if re.search(
        r"\b(?:no\s+(?:tiene|hay|arroja|bota|marca|lee|registra)\s+(?:ning[uú]n\s+)?c[oó]digo|"
        r"sin\s+c[oó]digos?|cero\s+c[oó]digos?|0\s+c[oó]digos?|sin\s+dtc|cero\s+dtc|"
        r"esc[aá]ner\s+(?:est[aá]\s+)?limpio|tablero\s+(?:est[aá]\s+)?limpio|"
        r"no\s+prende\s+(?:el\s+)?check\b.{0,40}\b(?:esc[aá]ner|scanner)\b.{0,30}\bno\s+tiene\b)\b",
        texto_l,
    ):
        estado.dtc_status = DtcStatus.DTC_AUSENTE
        h = estado.registrar_hecho("sin_dtc", "SI", categoria="dtc", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
        h2 = estado.registrar_hecho("sin_dtc_reportado", "SI", categoria="dtc", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h2.to_dict())
        h3 = estado.registrar_hecho("escaner_limpio", "SI", categoria="dtc", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h3.to_dict())

    # Retorno de inyectores en ml
    m_ret = re.search(r"\b(?:retorno|probetas?)\b.{0,60}?(?:inyector\s*(\d+))?.{0,40}?(\d+)\s*(?:ml|cc)\b", texto_l)
    if m_ret or ("retorno" in texto_l and ("ml" in texto_l or "probeta" in texto_l)):
        num_iny = m_ret.group(1) if m_ret and m_ret.group(1) else "3"
        ml_val = m_ret.group(2) if m_ret and m_ret.group(2) else "65"
        campo_ret = f"retorno_anomalo_inyector{num_iny}"
        h_ret = estado.registrar_hecho(campo_ret, f"{ml_val} ml", categoria="medicion", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_ret.to_dict())
        h_ret_gen = estado.registrar_hecho("retorno_anomalo_inyector", f"Inyector {num_iny} con {ml_val} ml", categoria="medicion", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_ret_gen.to_dict())
        estado.registrar_prueba_completada("retorno_inyectores", f"Inyector {num_iny}: {ml_val} ml")

    # Nivel de aceite en cm sobre el máximo / dilución de combustible
    if (
        re.search(
            r"\b(?:varilla|nivel\s+de\s+aceite|aceite)\b.{0,50}(?:(\d+(?:[.,]\d+)?)\s*(?:cm|cent[ií]metros)\b.{0,30}\b(?:por\s+encima|encima|sobre|arriba|pasado)\b.{0,25}\b(?:full|m[aá]ximo|marca)|(?:por\s+encima|encima|sobre|arriba|pasado)\b.{0,30}\b(?:full|m[aá]ximo|marca)\b.{0,30}(\d+(?:[.,]\d+)?)\s*(?:cm|cent[ií]metros))\b",
            texto_l,
        )
        or re.search(r"\b(?:varilla|nivel\s+de\s+aceite)\b.{0,40}\b(?:por\s+encima|encima|sobre|alto|pasado)\b.{0,30}\b(?:full|m[aá]ximo)\b", texto_l)
        or re.search(r"\baceite\b.{0,40}\b(?:huele|olor)\b.{0,20}\b(?:di[eé]sel|petr[oó]leo)\b|\baceite\b.{0,30}\bpasado\b.{0,20}\bm[aá]ximo\b|\b(?:nivel|aceite)\b.{0,30}\bsubi[oó]\b", texto_l)
    ):
        h_aceite = estado.registrar_hecho("aceite_sobrellenado_diluido", "SI (nivel por encima del máximo)", categoria="seguridad", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_aceite.to_dict())
        h_aceite2 = estado.registrar_hecho("dilucion_aceite_combustible", "SI", categoria="seguridad", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_aceite2.to_dict())
        h_aceite3 = estado.registrar_hecho("aceite_diluido", "SI", categoria="seguridad", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_aceite3.to_dict())

    # Pedal de freno blando / esponjoso / se hunde
    if re.search(
        r"\b(?:pedal(?:\s+de)?\s+freno|freno)\b.{0,45}\b(?:esponjoso|se\s+va\s+(?:lentamente\s+)?al\s+fondo|se\s+desinfla|pierde\s+presi[oó]n|sin\s+presi[oó]n|latea)\b|\b(?:pedal\s+esponjoso|pedal\s+se\s+hunde)\b",
        texto_l,
    ):
        h_pedal = estado.registrar_hecho("pedal_esponjoso", "SI", categoria="sintoma", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
        hechos_extraidos.append(h_pedal.to_dict())

    # Corrección / reemplazo de aceite y filtro
    if re.search(
        r"\b(?:dren[eé]|vaci[eé]|bot[eé]|cambi[eé]|reemplac[eé]|correg[ií])\b.{0,50}\b(?:aceite|filtro|problema\s+del\s+aceite)\b|\baceite\s+(?:ya\s+)?(?:est[aá]\s+)?(?:nuevo|cambiado|reemplazado|a\s+nivel)\b",
        texto_l,
    ):
        h_reemp = estado.registrar_hecho("reemplazado_aceite", "SI", categoria="seguridad", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_reemp.to_dict())
        h_aceite_desc = estado.registrar_hecho("dilucion_aceite_combustible", "CORREGIDO", categoria="seguridad", estado=FactState.DESCARTADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_aceite_desc.to_dict())

    # Carbón en mariposa / cuerpo de aceleración
    if re.search(
        r"\b(?:cuerpo(?:\s+de)?\s+aceleraci[oó]n|mariposa|admisi[oó]n)\b.{0,50}\b(?:carb[oó]n|holl[ií]n|suciedad|costra|sedimento|sucio|obstruid[oa]|capa\s+gruesa)\b|\b(?:carb[oó]n|holl[ií]n|suciedad|costra)\b.{0,40}\b(?:cuerpo(?:\s+de)?\s+aceleraci[oó]n|mariposa)\b",
        texto_l,
    ):
        h_carb = estado.registrar_hecho("mariposa_con_carbon", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_carb.to_dict())
        h_carb2 = estado.registrar_hecho("cuerpo_aceleracion_sucio", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_carb2.to_dict())

    # Presión de combustible normal
    if re.search(
        r"\bpresi[oó]n\s+de\s+combustible\b.{0,40}\b(\d+)\s*psi\b.{0,20}\b(?:fija|normal|buena|ok|constante)\b|\bpresi[oó]n\s+de\s+combustible\b.{0,30}\b(?:fija|normal|buena|ok)\b",
        texto_l,
    ):
        h_pcomb = estado.registrar_hecho("presion_combustible_ok", "SI", categoria="medicion", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_pcomb.to_dict())

    # Compresión de cilindros (medición cuantitativa y condición)
    m_comp = re.search(r"\bcompresi[oó]n\b", texto_l)
    if m_comp:
        m_psi = re.search(r"\b(\d+)\s*(?:psi|bar)\b", texto_l)
        es_pareja = bool(re.search(r"\b(?:parej[oa]|igual(?:es)?|normal(?:es)?|buen[oa]s?|sin\s+diferencias?)\b", texto_l))
        if m_psi or es_pareja:
            val_psi = m_psi.group(1) if m_psi else ""
            val_str = f"{val_psi} PSI parejo" if (val_psi and es_pareja) else (f"{val_psi} PSI" if val_psi else "pareja")
            h_comp = estado.registrar_hecho("compresion_pareja_ok", val_str, categoria="medicion", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_comp.to_dict())
            if val_psi:
                estado.registrar_medicion("compresion_motor", float(val_psi), "PSI", contexto="cilindros", prueba="compresion_pareja_ok", estado="observado")
                estado.registrar_prueba_completada("compresion_pareja_ok", val_str)

    # Presión diferencial DPF
    if re.search(
        r"\b(?:presi[oó]n\s+diferencial|sensor\s+(?:de\s+)?presi[oó]n\s+diferencial|dpf)\b.{0,50}\b(\d+)\s*kpa\b|\b(\d+)\s*kpa\b.{0,40}\b(?:presi[oó]n\s+diferencial|dpf)\b",
        texto_l,
    ):
        h_dpf = estado.registrar_hecho("presion_diferencial_dpf_alta", "SI", categoria="medicion", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_dpf.to_dict())

    # Contrapresión de escape
    if re.search(
        r"\b(?:contrapresi[oó]n|presi[oó]n\s+de\s+escape|man[oó]metro\b.{0,35}\bsensor\s+1|man[oó]metro\b.{0,35}\bescape)\b",
        texto_l,
    ) and ("psi" in texto_l or "bar" in texto_l):
        h_cp = estado.registrar_hecho("contrapresion_medida", "SI", categoria="medicion", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_cp.to_dict())

    # Descarte de fuga de escape
    if re.search(
        r"\b(?:no\s+tiene|sin)\s+fugas?\s+(?:de\s+)?escape\b|\bempaques?\s+del\s+m[uú]ltiple\b.{0,35}\b(?:sin\s+fuga|no\s+tiene\s+fuga|ni\s+fisuras)\b",
        texto_l,
    ):
        h_fe = estado.registrar_hecho("fuga_escape_descartada", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_fe.to_dict())

    # Descarte de fugas en alta presión diésel
    if re.search(
        r"\b(?:no\s+hay|sin)\s+fugas?\s+(?:de\s+)?(?:petr[oó]leo|di[eé]sel|combustible)\b.{0,45}\b(?:alta\s+presi[oó]n|bomba\s+cp4|riel|tuber[ií]as)\b|\b(?:tuber[ií]as|bomba\s+cp4)\b.{0,45}\b(?:sin\s+fugas?|no\s+hay\s+fugas?)\b",
        texto_l,
    ):
        h_fa = estado.registrar_hecho("sin_fugas_alta", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_fa.to_dict())

    # Descarte de fuga de retén de cigüeñal / tapa de válvulas
    if re.search(
        r"\b(?:no\s+hay\s+manchas|sin\s+fugas?|no\s+hay\s+fugas?)\b.{0,50}\b(?:ret[eé]n\s+de\s+cig[uü]e[ñn]al|tapa\s+de\s+v[aá]lvulas)\b",
        texto_l,
    ):
        h_fr = estado.registrar_hecho("fuga_reten_descartada", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_fr.to_dict())

    # Juego de eje de turbo confirmado
    if re.search(
        r"\b(?:turbina|turbocompresor|eje\s+(?:del\s+)?turbo|turbo)\b.{0,45}\b(?:juego\s+(?:radial|axial)|holgura\s+(?:radial|axial)|juego\s+notable)\b|\b(?:juego\s+(?:radial|axial)|holgura)\b.{0,45}\b(?:turbina|turbo)\b",
        texto_l,
    ):
        h_turbo = estado.registrar_hecho("juego_eje_turbo_confirmado", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_turbo.to_dict())

    # Descarte de bujías (inspección física limpia / electrodos ok / reemplazo)
    if re.search(
        r"\bbuj[ií]as\b.{0,45}\b(?:limpias|caf[eé]\s+claro|buen\s+estado|sin\s+costra|normales|descart(?:adas?|o|amos|é))\b|"
        r"\b(?:limpias|sin\s+costra|descart(?:adas?|o|amos|é))\b.{0,30}\bbuj[ií]as\b",
        texto_l,
    ):
        h_buj = estado.registrar_hecho("bujias_descartadas", "DESCARTADO", categoria="componente_descartado", estado=FactState.DESCARTADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_buj.to_dict())
        if "bujías" not in estado.hipotesis_descartadas and "bujias" not in estado.hipotesis_descartadas:
            estado.hipotesis_descartadas.append("bujías")

    if re.search(
        r"\b(?:12\s*v|12\s*voltios)\b.{0,45}\b(?:directos?|alimentaci[oó]n|prueba)\b.{0,45}\b(?:electro|ventilador|bomba)\b|"
        r"\b(?:electro|ventilador|bomba)\b.{0,45}\b(?:12\s*v|12\s*voltios)\b.{0,45}\b(?:gir[oó]|velocidad|fuerza|prendi[oó]|directos?|funcion[oó])\b",
        texto_l,
    ):
        h = estado.registrar_hecho("electro_funciona_12v", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if re.search(r"\b(?:fusibles?|rel[eé]s?)\b.{0,40}\b(?:intactos?|bien|buenos?|ok)\b", texto_l):
        h = estado.registrar_hecho("fusible_rele_descartados", "SI", categoria="comprobacion_fisica", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if re.search(
        r"\bmanguera\s+(?:de\s+)?(?:arriba|superior)\b.{0,45}\b(?:hirviendo|caliente)\b.{0,45}\bmanguera\s+(?:de\s+)?(?:abajo|inferior)\b.{0,45}\bfr[ií]a\b|"
        r"\b(?:disparidad|diferencia)\s+(?:t[eé]rmica|de\s+temperatura)\b.{0,45}\bmangueras?\b|"
        r"\bmanguera\s+(?:superior|de\s+arriba)\b.{0,35}\bcaliente\b.{0,35}\bmanguera\s+(?:inferior|de\s+abajo)\b.{0,35}\bfr[ií]a\b",
        texto_l,
    ):
        h = estado.registrar_hecho("disparidad_mangueras", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if re.search(r"\bno\s+hay\s+fugas?\b|\bsin\s+fugas?\b", texto_l):
        if any(w in texto_l for w in ("freno", "caja", "aceite", "reten", "retén")):
            h = estado.registrar_hecho("fuga_reten_descartada", "SI", categoria="comprobacion_fisica", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())
        else:
            h = estado.registrar_hecho("sin_fugas", "SI", categoria="comprobacion_fisica", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

    if re.search(r"\bpastillas?\b.{0,30}\b(?:nuevas?|cambiaron|descart(?:adas?|o|é))\b|\bdescart(?:adas?|o|é)\b.{0,20}\bpastillas?\b", texto_l):
        h = estado.registrar_hecho("pastillas_descartadas", "DESCARTADO", categoria="componente_descartado", estado=FactState.DESCARTADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
        if "pastillas" not in estado.hipotesis_descartadas:
            estado.hipotesis_descartadas.append("pastillas")

    if re.search(
        r"\b(?:0\.\d+|\d+\.\d+)\s*mm\b.{0,30}\b(?:alabeo|salto|reloj\s+comparador)\b|\b(?:alabeo|salto|reloj\s+comparador)\b.{0,30}\b(\d+\.\d+)\s*mm\b",
        texto_l,
    ):
        m_al = re.search(r"\b(\d+\.\d+)\s*mm\b", texto_l)
        val_al = m_al.group(1) if m_al else "0.12"
        h = estado.registrar_hecho("alabeo_medido", f"{val_al} mm", categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if re.search(r"\bbater[ií]a\s+es\s+nueva\b|\bno\s+es\s+la\s+bater[ií]a\b|\bbater[ií]a\b.{0,25}\bdescart(?:ada|o|é)\b", texto_l):
        h = estado.registrar_hecho("bateria_descartada", "DESCARTADO", categoria="componente_descartado", estado=FactState.DESCARTADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
        if "batería" not in estado.hipotesis_descartadas and "bateria" not in estado.hipotesis_descartadas:
            estado.hipotesis_descartadas.append("batería")

    if re.search(
        r"\b(?:0\.\d+|\d+\.\d+)\s*a\b.{0,30}\b(?:consumo|fuga|par[aá]sito)\b|\b(?:consumo|fuga|par[aá]sito)\b.{0,30}\b(\d+\.\d+)\s*a\b",
        texto_l,
    ):
        m_fuga = re.search(r"\b(\d+\.\d+)\s*a\b", texto_l)
        val_fuga = m_fuga.group(1) if m_fuga else "0.85"
        h = estado.registrar_hecho("fuga_confirmada", f"{val_fuga} A", categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if re.search(r"\bamortiguadores?\b.{0,30}\b(?:nuevos?|sin\s+fuga|descart(?:ados?|o|é))\b", texto_l):
        h = estado.registrar_hecho("amortiguadores_descartados", "DESCARTADO", categoria="componente_descartado", estado=FactState.DESCARTADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
        if "amortiguadores" not in estado.hipotesis_descartadas:
            estado.hipotesis_descartadas.append("amortiguadores")

    if re.search(r"\br[oó]tulas?\b.{0,35}\b(?:juego|desgaste|holgura|da[ñn]ada|axial|movimiento)\b|\b(?:juego|holgura)\b.{0,35}\br[oó]tulas?\b", texto_l):
        m_mm_rot = re.search(r"\b(\d+(?:[.,]\d+)?)\s*mm\b", texto_l)
        val_rot = f"{m_mm_rot.group(1)} mm de holgura" if m_mm_rot else "SI"
        h = estado.registrar_hecho("rotula_danada", val_rot, categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
    if re.search(r"\b(?:no\s+es\s+la\s+bomba|bomba\s+manda\s+\d+\s*psi|bomba\s+descartada|descart[eé]\s+(?:la\s+)?bomba)\b", texto_l):
        h = estado.registrar_hecho("bomba_descartada", "DESCARTADO", categoria="componente_descartado", estado=FactState.DESCARTADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
        if "bomba de combustible" not in estado.hipotesis_descartadas:
            estado.hipotesis_descartadas.append("bomba de combustible")
    if re.search(r"\b(?:candad(?:o|ito)|inmovilizador|transponder|b10da)\b", texto_l):
        h = estado.registrar_hecho("inmovilizador_confirmado", "SI", categoria="sistema", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
    if re.search(r"\b(?:actuador|varilla)\b.{0,30}\b(?:mueve|suave|ok)\b", texto_l):
        h = estado.registrar_hecho("actuador_turbo_descartado", "SI", categoria="componente_descartado", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
    if re.search(r"\b(?:buj[ií]as|bobinas)\b.{0,30}\b(?:nuevas|originales|buen\s+estado)\b", texto_l):
        h = estado.registrar_hecho("encendido_descartado", "SI", categoria="componente_descartado", estado=FactState.DESCARTADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
        h_b = estado.registrar_hecho("bujias_descartadas", "SI", categoria="componente_descartado", estado=FactState.DESCARTADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_b.to_dict())
        if "bujias" not in estado.hipotesis_descartadas:
            estado.hipotesis_descartadas.append("bujias")
    if re.search(r"\breductor\b.{0,30}\b(?:congelado|escarcha|blanca)\b", texto_l):
        h = estado.registrar_hecho("reductor_congelado", "SI", categoria="comprobacion_fisica", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
    if re.search(r"\b(?:calentador|buj[ií]a\s+incandescente|precalentamiento)\b.{0,60}\b(?:abierto|infinito|quemad[oa])\b|\b(?:abierto|infinito|quemad[oa])\b.{0,40}\b(?:calentador|buj[ií]a\s+incandescente)\b", texto_l):
        h = estado.registrar_hecho("resistencia_calentador_abierta", "SI", categoria="medicion", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
    if re.search(r"\b12\s*v\b.{0,45}\b(?:riel|alimentaci[oó]n|calentadores?)\b", texto_l):
        h = estado.registrar_hecho("alimentacion_12v_ok", "SI", categoria="medicion", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
    if re.search(r"\b(?:embrague|disco)\b.{0,40}\b(?:resbal[oó]|patin[oó]|no\s+se\s+apag[oó])\b|\b(?:freno\s+de\s+mano\b.{0,30}\bcuarta\b.{0,30}\bembrague)\b", texto_l):
        h = estado.registrar_hecho("embrague_patina_confirmado", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
    if re.search(r"\b(?:remaches\s+rozando|remaches\b.{0,25}\bdisco|disco\b.{0,25}\bremaches)\b", texto_l):
        h = estado.registrar_hecho("disco_gastado_remaches", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
    if re.search(r"\b(?:sin\s+viruta|no\s+tiene\b.{0,30}\bviruta)\b.{0,50}\b(?:cp4|bomba\s+de\s+alta|regulador)\b|\b(?:cp4|bomba\s+de\s+alta|regulador)\b.{0,50}\b(?:sin\s+viruta|no\s+tiene\b.{0,30}\bviruta)\b", texto_l):
        h = estado.registrar_hecho("sin_viruta_cp4", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
    if re.search(r"\b(?:inyector\b.{0,35}\b(?:glp|gas)\b.{0,35}\b(?:abierto|infinito|cortad[oa])|bobinas?\s+de\s+(?:los\s+)?inyectores\b.{0,45}\b(?:abierto|infinito))\b", texto_l):
        h = estado.registrar_hecho("inyector_glp_abierto", "SI", categoria="medicion", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
    return hechos_extraidos
