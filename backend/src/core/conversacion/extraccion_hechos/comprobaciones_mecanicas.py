"""Extracción de comprobaciones físicas, pruebas mecánicas y componentes descartados (Clean Architecture)."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from src.core.conversacion.detector_polaridad import DetectorPolaridad
from src.core.conversacion.evidencia_acciones import registrar_acciones_taller
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

    if re.search(r"\b(?:mud[oó]|migr[oó])\b.{0,30}\b(?:cilindro\s+1|p0301)\b", texto_l):
        h_mig = estado.registrar_hecho("bobina_migro_cilindro_1", "falla migró a cilindro 1", categoria="prueba_cruzada", tipo=FactType.CONDICION)
        hechos_extraidos.append(h_mig.to_dict())

    # Una prueba cruzada informa el resultado observado; no implica que la
    # bobina sea la causa. Conservamos cilindros y DTC para evitar que una
    # comprobación posterior borre esta evidencia física.
    intercambio = re.search(
        r"\bintercambi[eé]\s+(?:la\s+)?(bobina|inyector|buj[ií]a)\s*(?:del\s+)?(?:cilindro\s*)?(\d+)"
        r"\s+(?:con|por)\s+(?:la\s+)?(?:del\s+)?(?:cilindro\s*)?(\d+)\b",
        texto_l,
    )
    if not intercambio:
        intercambio = re.search(
            r"\b(bobina|inyector|buj[ií]a)\s*(?:del\s+)?(?:cilindro\s*)?(\d+)\s+"
            r"(?:fue\s+)?intercambiada\s+(?:con|por)\s+(?:la\s+)?(?:del\s+)?(?:cilindro\s*)?(\d+)\b",
            texto_l,
        )
    if intercambio:
        componente, origen, destino = intercambio.groups()
        h_intercambio = estado.registrar_hecho(
            f"prueba_intercambio_{componente}",
            f"{componente} {origen} intercambiada con {destino}",
            categoria="prueba_cruzada",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
            procedencia="user_reported",
        )
        hechos_extraidos.append(h_intercambio.to_dict())
        dtc = re.search(r"\b([pucb]\d{4})\b", texto_l, re.IGNORECASE)
        if dtc and re.search(r"\b(?:no\s+se\s+movi[oó]|sigui[oó]|persiste|no\s+cambi[oó])\b", texto_l):
            codigo = dtc.group(1).upper()
            h_persistente = estado.registrar_hecho(
                f"dtc_persistente_tras_intercambio_{codigo}",
                f"{codigo} no se movió tras intercambio de {componente}",
                categoria="resultado_prueba_cruzada",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
                procedencia="user_reported",
            )
            hechos_extraidos.append(h_persistente.to_dict())

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

    hechos_extraidos.extend(registrar_acciones_taller(estado, texto_usuario))

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

    from .comprobaciones_sistemas import extraer_comprobaciones_sistemas
    hechos_extraidos.extend(extraer_comprobaciones_sistemas(estado, texto_usuario, texto_normalizado))
    return hechos_extraidos
