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
        h_riz = estado.registrar_hecho(
            "rizado_ac", "alto / diodo abierto", categoria="medicion", tipo=FactType.CONDICION
        )
        hechos_extraidos.append(h_riz.to_dict())

    if re.search(
        r"\b(?:co2|l[ií]quido\s+azul|probador\s+qu[ií]mico|fug(?:as?)?\s+de\s+combusti[oó]n|vir[oó]|amarillo)\b",
        texto_l,
    ):
        h_co2 = estado.registrar_hecho(
            "co2_quimico_positivo",
            "positivo / presencia de CO2",
            categoria="prueba_quimica",
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_co2.to_dict())

    if re.search(r"\b(?:mud[oó]|migr[oó])\b.{0,30}\b(?:cilindro\s+1|p0301)\b", texto_l):
        h_mig = estado.registrar_hecho(
            "bobina_migro_cilindro_1",
            "falla migró a cilindro 1",
            categoria="prueba_cruzada",
            tipo=FactType.CONDICION,
        )
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
        if dtc and re.search(
            r"\b(?:no\s+se\s+movi[oó]|sigui[oó]|persiste|no\s+cambi[oó]|falla\s+persiste)\b", texto_l
        ):
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
            # Si el DTC persiste tras intercambio de bobina, se descarta la bobina de encendido
            if componente == "bobina":
                estado.descartar_hipotesis("bobina_de_encendido")
                estado.descartar_hipotesis("bobina")
    else:
        # Detección de intercambio simple reportado en talleres: "bobina 2 intercambiada, falla persiste en cilindro 2"
        intercambio_simple = re.search(
            r"\b(?:(bobina|inyector|buj[ií]a)\s*(?:del\s+)?(?:cilindro\s*)?(\d+)?\s*(?:fue\s+)?intercambiada|"
            r"intercambi[eé]\s+(?:la\s+)?(bobina|inyector|buj[ií]a)\s*(?:del\s+)?(?:cilindro\s*)?(\d+)?)\b",
            texto_l,
        )
        if intercambio_simple:
            comp_sim = intercambio_simple.group(1) or intercambio_simple.group(3) or "bobina"
            cil_sim = intercambio_simple.group(2) or intercambio_simple.group(4) or ""
            h_sim = estado.registrar_hecho(
                f"prueba_intercambio_{comp_sim}",
                f"{comp_sim} {cil_sim} intercambiada".strip(),
                categoria="prueba_cruzada",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
                procedencia="user_reported",
            )
            hechos_extraidos.append(h_sim.to_dict())
            if re.search(
                r"\b(?:no\s+se\s+movi[oó]|sigui[oó]|persiste|no\s+cambi[oó]|falla\s+persiste)\b", texto_l
            ):
                if comp_sim == "bobina":
                    estado.descartar_hipotesis("bobina_de_encendido")
                    estado.descartar_hipotesis("bobina")
                elif comp_sim == "bujía" or comp_sim == "bujia":
                    estado.descartar_hipotesis("bujias_desgastadas")
                    estado.descartar_hipotesis("bujia")
                elif comp_sim == "inyector":
                    estado.descartar_hipotesis("inyector_averiado")
                    estado.descartar_hipotesis("inyector")
                h_desc = estado.registrar_hecho(
                    f"{comp_sim}_descartada_tras_intercambio",
                    f"{comp_sim} descartada, falla persiste en el mismo cilindro",
                    categoria="descarte_componente",
                    texto_crudo=texto_usuario,
                    tipo=FactType.CONDICION,
                    procedencia="user_reported",
                )
                hechos_extraidos.append(h_desc.to_dict())

    # Piezas ya reemplazadas sin éxito reportadas por mecánico o propietario
    m_reemp_sin_exito = re.search(
        r"\b(?:ya\s+)?(?:cambi[eé]|reemplac[eé]|puse\s+nuev[ao]s?)\s+(?:las?\s+)?(buj[ií]as?|bobinas?|bomba(?:\s+de\s+gasolina)?|filtro(?:\s+de\s+gasolina)?)\s+(?:y\s+)?(?:sigue|contin[uú]a)\s+(?:igual|la\s+falla|el\s+problema)\b",
        texto_l,
    )
    if m_reemp_sin_exito:
        comp_reemp = m_reemp_sin_exito.group(1).lower()
        if "buj" in comp_reemp:
            nom_comp = "bujias"
            estado.descartar_hipotesis("bujia")
            estado.descartar_hipotesis("bujias_desgastadas")
        elif "bobin" in comp_reemp:
            nom_comp = "bobinas"
            estado.descartar_hipotesis("bobina_de_encendido")
            estado.descartar_hipotesis("bobina")
        elif "bomba" in comp_reemp:
            nom_comp = "bomba_gasolina"
            estado.descartar_hipotesis("bomba_combustible")
        else:
            nom_comp = comp_reemp
            estado.descartar_hipotesis(comp_reemp)
        h_reemp_desc = estado.registrar_hecho(
            f"{nom_comp}_reemplazada_sin_exito",
            f"{nom_comp} reemplazada nueva sin cambio en la falla",
            categoria="descarte_componente",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
            procedencia="user_reported",
        )
        hechos_extraidos.append(h_reemp_desc.to_dict())

    if re.search(r"\b(?:empaque\s+de\s+culata|junta\s+de\s+culata)\b", texto_l) and re.search(
        r"\b(?:quemado|soplado|roto|solucionado|cambio|nuevo)\b", texto_l
    ):
        h_cul = estado.registrar_hecho(
            "empaque_culata",
            "empaque de culata confirmado",
            categoria="componente_averiado",
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_cul.to_dict())

    if re.search(r"\btermostato\b.{0,40}\b(?:olla|term[oó]metro|abre|perfecto|descartado|bien)\b", texto_l):
        h_term = estado.registrar_hecho(
            "termostato_descartado",
            "termostato comprobado normal",
            categoria="verificacion_fisica",
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_term.to_dict())

    if re.search(
        r"\bresistencia\b.{0,50}\b(?:abiert[ao]|quemad[ao]|ol|infinita|primera\s+velocidad)\b", texto_l
    ):
        h_res = estado.registrar_hecho(
            "resistencia_baja_quemada",
            "resistencia quemada",
            categoria="componente_averiado",
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_res.to_dict())

    if re.search(r"\b(?:en\s+tr[aá]fico|tr[aá]fico\s+pesado|parado\s+en\s+el\s+sem[aá]foro)\b", texto_l):
        h_traf = estado.registrar_hecho(
            "condicion", "en trafico / ralenti", categoria="condicion", tipo=FactType.CONDICION
        )
        hechos_extraidos.append(h_traf.to_dict())

    m_sol = re.search(
        r"\b(?:qued[oó]\s+resuelto|caso\s+solucionado|falla\s+qued[oó]\s+resuelta|solucionado\s+con|reparaci[oó]n:\s*)\s*(?:cambiando|con|reemplazando|instalando)?\s*([a-z\u00e1\u00e9\u00ed\u00f3\u00fa0-9\s/-]+?)(?:\.|$|,|\s+genera|\s+consolida)",
        texto_l,
    )
    if m_sol:
        h_sol = estado.registrar_hecho(
            "solucion", m_sol.group(1).strip(), categoria="reparacion_confirmada", tipo=FactType.CONDICION
        )
        hechos_extraidos.append(h_sol.to_dict())

    m_ret = re.search(
        r"\b(?:retorno\b.{0,40}\binyector\s*(\d+)|\binyector\s*(\d+)\b.{0,40}\b(?:retorno|llen[oó]|marcaron))\b",
        texto_l,
    )
    if m_ret:
        num_iny = m_ret.group(1) or m_ret.group(2)
        h_ret = estado.registrar_hecho(
            f"retorno_anomalo_inyector{num_iny}",
            f"retorno anómalo inyector {num_iny}",
            categoria="medicion_anomala",
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_ret.to_dict())

    if re.search(
        r"\b(?:no\s+(?:tiene|hay|registra|arroja)\s+(?:ning[u\u00fa]n\s+)?c[o\u00f3]digo|sin\s+(?:c[o\u00f3]digos?|dtc)|sin\s+fallas?\s+en\s+el\s+esc[a\u00e1]ner|esc[a\u00e1]ner\s+(?:limpio|no\s+tiene\s+ning[u\u00fa]n\s+c[o\u00f3]digo)|no\s+tiene\s+dtc)\b",
        texto_l,
    ):
        h_sdtc = estado.registrar_hecho(
            "sin_dtc", "sin códigos DTC", categoria="dtc", tipo=FactType.CONDICION
        )
        hechos_extraidos.append(h_sdtc.to_dict())

    hechos_extraidos.extend(registrar_acciones_taller(estado, texto_usuario))

    for campo_nr, val_nr in DetectorPolaridad.extraer_componentes_no_revisados(texto_usuario):
        h = estado.registrar_hecho(
            campo_nr,
            val_nr,
            categoria="inspeccion_pendiente",
            estado=FactState.NO_REVISADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())

    for campo_norm, val_norm in DetectorPolaridad.extraer_sistemas_normales(texto_usuario):
        h = estado.registrar_hecho(
            campo_norm,
            val_norm,
            categoria="sistema_normal",
            estado=FactState.AUSENTE_NEGADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())

    # 3. Herramientas disponibles / no disponibles (Plan B / ConversationState)
    m_herramienta = re.search(
        r"\b(?:no\s+tengo|sin|carezco\s+de)\s+(osciloscopio|esc[a\u00e1]ner|scanner|man[o\u00f3]metro|vacu[o\u00f3]metro|compres[i\u00ed]metro|mult[i\u00ed]metro|extractor|herramientas?)\b",
        texto_l,
    )
    if m_herramienta:
        raw_herr = m_herramienta.group(1).lower()
        herr = "escaner" if "scan" in raw_herr or "esc" in raw_herr else raw_herr
        herr = "manometro" if "man" in herr else herr
        herr = "general" if "herramienta" in herr else herr
        estado.marcar_herramienta_indisponible(herr)
        if herr == "escaner":
            estado.dtc_status = DtcStatus.DTC_DESCONOCIDO
            h_esc = estado.registrar_hecho("escaner_disponible", "NO", estado=FactState.NO_APLICA)
            hechos_extraidos.append(h_esc.to_dict())

    m_disp = re.search(
        r"\b(?:s[i\u00ed],?\s+)?(?:tengo|dispongo\s+de|cuento\s+con)\s+(?:un\s+|el\s+)?(osciloscopio|esc[a\u00e1]ner|scanner|man[o\u00f3]metro|vacu[o\u00f3]metro|compres[i\u00ed]metro|mult[i\u00ed]metro)\b",
        texto_l,
    )
    if m_disp and not m_herramienta:
        raw_disp = m_disp.group(1).lower()
        herr_disp = "escaner" if "scan" in raw_disp or "esc" in raw_disp else raw_disp
        herr_disp = "manometro" if "man" in herr_disp else herr_disp
        estado.marcar_herramienta_disponible(herr_disp)

    # 4. Estado de acople de compresor / clic A/C
    if "compresor" in texto_l or "clic" in texto_l:
        if re.search(r"\bno\s+s[e\u00e9]\s+(?:si\s+)?(?:acopla|se\s+escucha)\b", texto_l):
            h = estado.registrar_hecho("compresor_acopla", "DESCONOCIDO", estado=FactState.DESCONOCIDO)
            hechos_extraidos.append(h.to_dict())
        elif re.search(
            r"\b(?:no\s+acopla|no\s+pega|no\s+entra|no\s+se\s+escucha(?:\s+el)?\s+clic)\b", texto_l
        ):
            estado.registrar_prueba_completada("acople_compresor", "NO")
            h = estado.registrar_hecho("compresor_acopla", "NO", estado=FactState.CONFIRMADO)
            hechos_extraidos.append(h.to_dict())
        elif re.search(
            r"\b(?:s[i\u00ed]\s+acopla|acopla\s+bien|s[i\u00ed]\s+pega|se\s+escucha\s+(?:el\s+)?clic|escuch[o\u00f3]\s+(?:el\s+)?clic|hace\s+clic)\b",
            texto_l,
        ):
            estado.registrar_prueba_completada("acople_compresor", "SI")
            h = estado.registrar_hecho("compresor_acopla", "SI", estado=FactState.CONFIRMADO)
            hechos_extraidos.append(h.to_dict())

    if re.search(r"\bno\s+s[e\u00e9]\s+(?:si\s+)?tiene\s+c[o\u00f3]digos\b", texto_l):
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
            r"\b(s[i\u00ed]\s+(?:hay|tiene|da|sale|salta|se\s+observa)|chispa\s+(?:buena|fuerte|azul|presente|normal|correcta|bien)|salta\s+chispa)\b",
            texto_l,
        )
    )
    if chispa_ausente:
        h = estado.registrar_hecho(
            "chispa_presente",
            "NO",
            categoria="comprobacion_fisica",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())
        estado.registrar_prueba_completada("chispa_bujias", "ausente")
    elif chispa_presente:
        h = estado.registrar_hecho(
            "chispa_presente",
            "SI",
            categoria="comprobacion_fisica",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())
        estado.registrar_prueba_completada("chispa_bujias", "presente")

    # Nivel de aceite / dilución
    if (
        re.search(
            r"\b(?:varilla|nivel\s+de\s+aceite|aceite)\b.{0,50}(?:(\d+(?:[.,]\d+)?)\s*(?:cm|cent[ií]metros)\b.{0,30}\b(?:por\s+encima|encima|sobre|arriba|pasado)\b.{0,25}\b(?:full|m[aá]ximo|marca)|(?:por\s+encima|encima|sobre|arriba|pasado)\b.{0,30}\b(?:full|m[aá]ximo|marca)\b.{0,30}(\d+(?:[.,]\d+)?)\s*(?:cm|cent[ií]metros))\b",
            texto_l,
        )
        or re.search(
            r"\b(?:varilla|nivel\s+de\s+aceite)\b.{0,40}\b(?:por\s+encima|encima|sobre|alto|pasado)\b.{0,30}\b(?:full|m[aá]ximo)\b",
            texto_l,
        )
        or re.search(
            r"\baceite\b.{0,40}\b(?:huele|olor)\b.{0,20}\b(?:di[eé]sel|petr[oó]leo)\b|\baceite\b.{0,30}\bpasado\b.{0,20}\bm[aá]ximo\b|\b(?:nivel|aceite)\b.{0,30}\bsubi[oó]\b",
            texto_l,
        )
    ):
        h_aceite = estado.registrar_hecho(
            "aceite_sobrellenado_diluido",
            "SI (nivel por encima del máximo)",
            categoria="seguridad",
            estado=FactState.CONFIRMADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_aceite.to_dict())
        h_aceite2 = estado.registrar_hecho(
            "dilucion_aceite_combustible",
            "SI",
            categoria="seguridad",
            estado=FactState.CONFIRMADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_aceite2.to_dict())
        h_aceite3 = estado.registrar_hecho(
            "aceite_diluido",
            "SI",
            categoria="seguridad",
            estado=FactState.CONFIRMADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_aceite3.to_dict())

    # Pedal de freno esponjoso
    if re.search(
        r"\b(?:pedal(?:\s+de)?\s+freno|freno)\b.{0,45}\b(?:esponjoso|se\s+va\s+(?:lentamente\s+)?al\s+fondo|se\s+desinfla|pierde\s+presi[oó]n|sin\s+presi[oó]n|latea)\b|\b(?:pedal\s+esponjoso|pedal\s+se\s+hunde)\b",
        texto_l,
    ):
        h_pedal = estado.registrar_hecho(
            "pedal_esponjoso",
            "SI",
            categoria="sintoma",
            estado=FactState.CONFIRMADO,
            texto_crudo=texto_usuario,
            tipo=FactType.SINTOMA,
        )
        hechos_extraidos.append(h_pedal.to_dict())

    # Reemplazo de aceite
    if re.search(
        r"\b(?:dren[eé]|vaci[eé]|bot[eé]|cambi[eé]|reemplac[eé]|correg[ií])\b.{0,50}\b(?:aceite|filtro|problema\s+del\s+aceite)\b|\baceite\s+(?:ya\s+)?(?:est[aá]\s+)?(?:nuevo|cambiado|reemplazado|a\s+nivel)\b",
        texto_l,
    ):
        h_reemp = estado.registrar_hecho(
            "reemplazado_aceite",
            "SI",
            categoria="seguridad",
            estado=FactState.CONFIRMADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_reemp.to_dict())

    from .comprobaciones_sistemas import extraer_comprobaciones_sistemas

    hechos_extraidos.extend(extraer_comprobaciones_sistemas(estado, texto_usuario, texto_normalizado))
    return hechos_extraidos
