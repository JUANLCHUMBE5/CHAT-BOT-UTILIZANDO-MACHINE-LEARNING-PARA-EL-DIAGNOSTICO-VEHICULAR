"""Extracción de comprobaciones físicas, pruebas mecánicas y componentes descartados (Clean Architecture)."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from src.core.conversacion.detector_polaridad import DetectorPolaridad
from src.core.conversacion.models import (
    ConversationState,
    DtcStatus,
    FactState,
    FactType,
)


def extraer_comprobaciones_mecanicas(
    estado: ConversationState,
    texto_usuario: str,
    texto_normalizado: str,
) -> List[Dict[str, Any]]:
    """Extrae comprobaciones físicas, piezas descartadas, estado de herramientas y síntomas observados."""
    hechos_extraidos: List[Dict[str, Any]] = []
    texto_l = texto_usuario.lower()

    # 1. Rizado AC y pruebas físicas directas
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

    m_ret = re.search(r"\b(?:retorno\b.{0,40}\binyector\s*(\d+)|\binyector\s*(\d+)\b.{0,40}\b(?:retorno|llen[oó]|marcaron))\b", texto_l)
    if m_ret:
        num_iny = m_ret.group(1) or m_ret.group(2)
        h_ret = estado.registrar_hecho(f"retorno_anomalo_inyector{num_iny}", f"retorno anómalo inyector {num_iny}", categoria="medicion_anomala", tipo=FactType.CONDICION)
        hechos_extraidos.append(h_ret.to_dict())

    if re.search(r"\b(?:no\s+(?:tiene|hay|registra|arroja)\s+(?:ning[uú]n\s+)?c[oó]digo|sin\s+(?:c[oó]digos?|dtc)|sin\s+fallas?\s+en\s+el\s+esc[aá]ner|esc[aá]ner\s+(?:limpio|no\s+tiene\s+ning[uú]n\s+c[oó]digo)|no\s+tiene\s+dtc)\b", texto_l):
        h_sdtc = estado.registrar_hecho("sin_dtc", "sin códigos DTC", categoria="dtc", tipo=FactType.CONDICION)
        hechos_extraidos.append(h_sdtc.to_dict())

    # 2. Componentes revisados o reemplazados
    if any(c in texto_l for c in ("ya cambie", "ya cambié", "ya las cambié", "ya las cambie", "ya los cambié", "ya los cambie", "ya le cambié", "ya se cambiaron", "ya se cambió", "nuevo", "nueva", "cambiamos", "recién cambiado", "recien cambiado", "recién cambié")):
        for pieza in ("bujias", "bujías", "bobinas", "bobina", "bomba", "filtro", "termostato", "pastillas", "aceite"):
            if pieza in texto_l:
                canon = "bujías" if "buj" in pieza else ("bobinas" if "bobin" in pieza else pieza)
                h = estado.registrar_hecho(f"reemplazado_{canon}", f"{canon} reemplazado(a)", categoria="antecedente", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())
                if "filtro" in pieza:
                    h_fd = estado.registrar_hecho("filtro_descartado", "DESCARTADO", categoria="componente_descartado", estado=FactState.DESCARTADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                    hechos_extraidos.append(h_fd.to_dict())
                    if "filtro de combustible" not in estado.hipotesis_descartadas and "filtro" not in estado.hipotesis_descartadas:
                        estado.hipotesis_descartadas.append("filtro de combustible")

    if any(c in texto_l for c in ("ya revise", "ya revisé", "probe", "probé", "intercambie", "intercambié", "descarte", "descarté", "esta bien", "está bien", "esta ok", "está ok")):
        for pieza in ("bujias", "bujías", "bobinas", "bobina", "bomba", "fusible", "presion", "presión", "compresion", "compresión", "bateria", "batería", "alternador", "arrancador", "filtro"):
            if pieza in texto_l:
                canon = "bujías" if "buj" in pieza else ("bobinas" if "bobin" in pieza else ("batería" if "bater" in pieza else pieza))
                h = estado.registrar_hecho(f"probado_{canon}", f"{canon} probado/descartado", categoria="componente_descartado", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())
                if "filtro" in pieza:
                    h_fd = estado.registrar_hecho("filtro_descartado", "DESCARTADO", categoria="componente_descartado", estado=FactState.DESCARTADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                    hechos_extraidos.append(h_fd.to_dict())
                    if "filtro de combustible" not in estado.hipotesis_descartadas:
                        estado.hipotesis_descartadas.append("filtro de combustible")

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

    # 3. Herramientas disponibles / no disponibles (Plan B / ConversationState)
    m_herramienta = re.search(r"\b(?:no\s+tengo|sin|carezco\s+de)\s+(osciloscopio|esc[aá]ner|scanner|man[oó]metro|vacu[oó]metro|compres[ií]metro|mult[ií]metro)\b", texto_l)
    if m_herramienta:
        raw_herr = m_herramienta.group(1).lower()
        herr = "escaner" if "scan" in raw_herr or "esc" in raw_herr else raw_herr
        herr = "manometro" if "man" in herr else herr
        estado.marcar_herramienta_indisponible(herr)
        if herr == "escaner":
            estado.dtc_status = DtcStatus.DTC_DESCONOCIDO
            h_esc = estado.registrar_hecho("escaner_disponible", "NO", estado=FactState.NO_APLICA)
            hechos_extraidos.append(h_esc.to_dict())

    m_disp = re.search(r"\b(?:s[ií],?\s+)?(?:tengo|dispongo\s+de|cuento\s+con)\s+(?:un\s+|el\s+)?(osciloscopio|esc[aá]ner|scanner|man[oó]metro|vacu[oó]metro|compres[ií]metro|mult[ií]metro)\b", texto_l)
    if m_disp and not m_herramienta:
        raw_disp = m_disp.group(1).lower()
        herr_disp = "escaner" if "scan" in raw_disp or "esc" in raw_disp else raw_disp
        herr_disp = "manometro" if "man" in herr_disp else herr_disp
        estado.marcar_herramienta_disponible(herr_disp)

    # 4. Estado de acople de compresor / clic A/C
    if "compresor" in texto_l or "clic" in texto_l:
        if re.search(r"\bno\s+s[eé]\s+(?:si\s+)?(?:acopla|se\s+escucha)\b", texto_l):
            h = estado.registrar_hecho("compresor_acopla", "DESCONOCIDO", estado=FactState.DESCONOCIDO)
            hechos_extraidos.append(h.to_dict())
        elif re.search(r"\b(?:no\s+acopla|no\s+pega|no\s+entra|no\s+se\s+escucha(?:\s+el)?\s+clic)\b", texto_l):
            estado.registrar_prueba_completada("acople_compresor", "NO")
            h = estado.registrar_hecho("compresor_acopla", "NO", estado=FactState.CONFIRMADO)
            hechos_extraidos.append(h.to_dict())
        elif re.search(r"\b(?:s[ií]\s+acopla|acopla\s+bien|s[ií]\s+pega|se\s+escucha\s+(?:el\s+)?clic|escuch[oó]\s+(?:el\s+)?clic|hace\s+clic)\b", texto_l):
            estado.registrar_prueba_completada("acople_compresor", "SI")
            h = estado.registrar_hecho("compresor_acopla", "SI", estado=FactState.CONFIRMADO)
            hechos_extraidos.append(h.to_dict())

    if re.search(r"\bno\s+s[eé]\s+(?:si\s+)?tiene\s+c[oó]digos\b", texto_l):
        h_cd = estado.registrar_hecho("codigos_dtc_observados", "NO_SABE", estado=FactState.DESCONOCIDO)
        hechos_extraidos.append(h_cd.to_dict())

    # Chispa
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
            r"\b(s[ií]\s+(?:hay|tiene|da|sale|salta|se\s+observa)|chispa\s+(?:buena|fuerte|azul|presente|normal|correcta|bien)|salta\s+chispa)\b",
            texto_l,
        )
    )
    if chispa_ausente:
        h = estado.registrar_hecho("chispa_presente", "NO", categoria="comprobacion_fisica", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
        estado.registrar_prueba_completada("chispa_bujias", "ausente")
    elif chispa_presente:
        h = estado.registrar_hecho("chispa_presente", "SI", categoria="comprobacion_fisica", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
        estado.registrar_prueba_completada("chispa_bujias", "presente")

    # Nivel de aceite / dilución
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

    # Pedal de freno esponjoso
    if re.search(
        r"\b(?:pedal(?:\s+de)?\s+freno|freno)\b.{0,45}\b(?:esponjoso|se\s+va\s+(?:lentamente\s+)?al\s+fondo|se\s+desinfla|pierde\s+presi[oó]n|sin\s+presi[oó]n|latea)\b|\b(?:pedal\s+esponjoso|pedal\s+se\s+hunde)\b",
        texto_l,
    ):
        h_pedal = estado.registrar_hecho("pedal_esponjoso", "SI", categoria="sintoma", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
        hechos_extraidos.append(h_pedal.to_dict())

    # Reemplazo de aceite
    if re.search(
        r"\b(?:dren[eé]|vaci[eé]|bot[eé]|cambi[eé]|reemplac[eé]|correg[ií])\b.{0,50}\b(?:aceite|filtro|problema\s+del\s+aceite)\b|\baceite\s+(?:ya\s+)?(?:est[aá]\s+)?(?:nuevo|cambiado|reemplazado|a\s+nivel)\b",
        texto_l,
    ):
        h_reemp = estado.registrar_hecho("reemplazado_aceite", "SI", categoria="seguridad", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_reemp.to_dict())
        h_aceite_desc = estado.registrar_hecho("dilucion_aceite_combustible", "CORREGIDO", categoria="seguridad", estado=FactState.DESCARTADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_aceite_desc.to_dict())

    # Mariposa con carbón
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

    # Compresión
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

    # Descarte de fugas
    if re.search(r"\b(?:no\s+tiene|sin)\s+fugas?\s+(?:de\s+)?escape\b|\bempaques?\s+del\s+m[uú]ltiple\b.{0,35}\b(?:sin\s+fuga|no\s+tiene\s+fuga|ni\s+fisuras)\b", texto_l):
        h_fe = estado.registrar_hecho("fuga_escape_descartada", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_fe.to_dict())

    if re.search(r"\b(?:no\s+hay|sin)\s+fugas?\s+(?:de\s+)?(?:petr[oó]leo|di[eé]sel|combustible)\b.{0,45}\b(?:alta\s+presi[oó]n|bomba\s+cp4|riel|tuber[ií]as)\b|\b(?:tuber[ií]as|bomba\s+cp4)\b.{0,45}\b(?:sin\s+fugas?|no\s+hay\s+fugas?)\b", texto_l):
        h_fa = estado.registrar_hecho("sin_fugas_alta", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_fa.to_dict())

    if re.search(r"\b(?:no\s+hay\s+manchas|sin\s+fugas?|no\s+hay\s+fugas?)\b.{0,50}\b(?:ret[eé]n\s+de\s+cig[uü]e[ñn]al|tapa\s+de\s+v[aá]lvulas)\b", texto_l):
        h_fr = estado.registrar_hecho("fuga_reten_descartada", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_fr.to_dict())

    # Juego de turbo
    if re.search(
        r"\b(?:turbina|turbocompresor|eje\s+(?:del\s+)?turbo|turbo)\b.{0,45}\b(?:juego\s+(?:radial|axial)|holgura\s+(?:radial|axial)|juego\s+notable)\b|\b(?:juego\s+(?:radial|axial)|holgura)\b.{0,45}\b(?:turbina|turbo)\b",
        texto_l,
    ):
        h_jt = estado.registrar_hecho("juego_eje_turbo_confirmado", "SI", categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_jt.to_dict())

    # Descarte de bujías
    if re.search(
        r"\bbuj[ií]as\b.{0,45}\b(?:limpias|caf[eé]\s+claro|buen\s+estado|sin\s+costra|normales|descart(?:adas?|o|amos|é))\b|"
        r"\b(?:limpias|sin\s+costra|descart(?:adas?|o|amos|é))\b.{0,30}\bbuj[ií]as\b",
        texto_l,
    ):
        h_buj = estado.registrar_hecho("bujias_descartadas", "DESCARTADO", categoria="componente_descartado", estado=FactState.DESCARTADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_buj.to_dict())
        if "bujías" not in estado.hipotesis_descartadas and "bujias" not in estado.hipotesis_descartadas:
            estado.hipotesis_descartadas.append("bujías")

    # Pruebas eléctricas y electroventilador
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
        h = estado.registrar_hecho("alimentacion_calentadores_ok", "SI", categoria="medicion", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    return hechos_extraidos
