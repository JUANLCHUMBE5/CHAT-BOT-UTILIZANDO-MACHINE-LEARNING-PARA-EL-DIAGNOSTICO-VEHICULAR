"""Extracción especializada: hechos_operativos."""

from __future__ import annotations

import re

from src.core.conversacion.detector_polaridad import DetectorPolaridad
from src.core.conversacion.diccionario_automotriz import (
    extraer_hechos_linguisticos,
)
from src.core.conversacion.extraccion_hechos.patrones_hechos import (
    PATRON_ANTECEDENTE_MARCHA,
    PATRON_CLIC_UNICO,
    PATRON_CLICS_REPETIDOS,
    PATRON_DEMORA_ARRANQUE,
    PATRON_GIRO_LLAVE,
    PATRON_LUCES_ATENUAN,
    PATRON_NO_ARRANCA,
    PATRON_RADIO_PRENDE,
    PATRON_TABLERO_PRENDE,
)
from src.core.conversacion.models import FactState, FactType


def extraer_hechos_operativos(estado, texto_usuario, texto_normalizado, hechos_extraidos, corrs):
    texto_l = texto_usuario.lower()
    es_queja_climatizacion = bool(
        re.search(
            "\\b(no\\s+enfr[ií]a|enfr[ií]a\\s+(?:poco|nada|casi\\s+nada)|deja\\s+de\\s+enfriar|solo\\s+enfr[ií]a|enfr[ií]a\\s+(?:solo|cuando)|sale\\s+aire\\s+(?:caliente|tibio|ambiente|a\\s+temperatura\\s+ambiente)|sin\\s+gas(?:\\s+r134a)?|falta\\s+(?:de\\s+)?gas\\s+(?:al\\s+aire|r134a)|compresor\\s+(?:no\\s+entra|no\\s+acopla|no\\s+pega|no\\s+arranca|no\\s+activa)|clima\\s+(?:no\\s+enfr[ií]a|calienta|no\\s+sopla\\s+fr[ií]o)|aire\\s+(?:caliente|tibio|no\\s+tira\\s+fr[ií]o)|fuga\\s+de\\s+gas\\s+(?:r134a|del\\s+aire))\\b",
            texto_l,
        )
    )
    tiene_mencion_ac = bool(re.search("\\b(a/c|aire\\s+acondicionado|clima|el\\s+ac)\\b", texto_l))
    if es_queja_climatizacion:
        estado.dominio_probable = "CLIMATIZACION"
        h = estado.registrar_hecho(
            "sintoma_climatizacion",
            "aire acondicionado no enfría / sale aire caliente",
            categoria="sintoma",
            texto_crudo=texto_usuario,
            tipo=FactType.SINTOMA,
        )
        hechos_extraidos.append(h.to_dict())
        if re.search("\\b(sem[aá]foro|detenido|al\\s+parar|al\\s+detener)\\b", texto_l) and re.search(
            "\\b(manejando|en\\s+movimiento|velocidad)\\b", texto_l
        ):
            h_op = estado.registrar_hecho(
                "condicion_operacion",
                "deja de enfriar detenido en semáforo",
                categoria="condicion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_op.to_dict())
    elif tiene_mencion_ac:
        h = estado.registrar_hecho(
            "modificador_ac",
            "A/C encendido",
            categoria="modificador",
            texto_crudo=texto_usuario,
            tipo=FactType.MODIFICADOR,
        )
        hechos_extraidos.append(h.to_dict())
    es_queja_refrigeracion = bool(
        re.search(
            "\\b(recalienta|recalentar|recalentando|recalent[oó]|se\\s+recalienta|el\\s+auto\\s+recalienta|el\\s+carro\\s+recalienta|motor\\s+recalienta|hierve|hirviendo|levanta\\s+temperatura|se\\s+calienta|calienta\\s+el\\s+motor|(?:se\\s+(?:le\\s+)?sube|sube|subi[oó])\\s+(?:la\\s+)?temperatura|temperatura\\s+(?:del\\s+motor\\s+)?(?:est[aá]\\s+)?subiendo|temperatura\\s+(?:sube|al\\s+tope|volando|elevada|alta)|aguja\\s+de\\s+temperatura|(?:bota|botando|sale|echando)\\s+vapor|vapor\\s+(?:bajo|del|por\\s+el)\\s+cap[oó]|termostato|electroventilador|motoventilador|manguera\\s+(?:inferior|superior)?(?:\\s+del)?\\s+radiador)\\b",
            texto_l,
        )
        and (not re.search("\\bno\\s+(?:se\\s+)?(?:recalienta|calienta|hierve)\\b", texto_l))
    )
    if es_queja_refrigeracion:
        estado.dominio_probable = "REFRIGERACION"
        h_ref = estado.registrar_hecho(
            "sintoma_sobrecalentamiento",
            "sobrecalentamiento del motor / sistema de refrigeración",
            categoria="sintoma",
            texto_crudo=texto_usuario,
            tipo=FactType.SINTOMA,
        )
        hechos_extraidos.append(h_ref.to_dict())
    if re.search(
        "\\b(luces?\\s+prendidas?|luces?\\s+altas?|prendo\\s+las\\s+luces?|con\\s+luces?|luces?\\s+(?:se\\s+ponen\\s+)?tenues?|bajan?\\s+las\\s+luces?|luces?\\s+bajas?)\\b",
        texto_l,
    ):
        luces_tenues = bool(re.search("\\b(tenues?|bajan?\\s+las\\s+luces?|luces?\\s+bajas?)\\b", texto_l))
        valor_luces = "luces tenues" if luces_tenues else "luces encendidas"
        h = estado.registrar_hecho(
            "modificador_luces",
            valor_luces,
            categoria="modificador",
            texto_crudo=texto_usuario,
            tipo=FactType.MODIFICADOR,
        )
        hechos_extraidos.append(h.to_dict())
    ling = extraer_hechos_linguisticos(texto_usuario)
    for k, v in ling.items():
        if corrs and any((c[0] == k for c in corrs)):
            continue
        cat = (
            "temperatura"
            if k == "temperatura"
            else "cambio_accion"
            if k == "evolucion_accion"
            else "condicion"
        )
        h = estado.registrar_hecho(k, v, categoria=cat, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
    if re.search("\\brodamientos?\\b.{0,35}\\b(?:no\\s+tiene|sin)\\b.{0,20}\\b(?:ruido|holgura)\\b", texto_l):
        estado.eliminar_hecho("sintoma_rodamiento")
        h_rod = estado.registrar_hecho(
            "rodamiento_descartado",
            "rodamiento sin ruido ni holgura reportada",
            categoria="componente_descartado",
            estado=FactState.DESCARTADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_rod.to_dict())
    menciona_caja_automatica = bool(
        re.search(
            "\\b(?:caja\\s+(?:de\\s+cambios\\s+)?autom[aá]tica|transmisi[oó]n\\s+autom[aá]tica|dsg|cvt)\\b",
            texto_l,
        )
    )
    if menciona_caja_automatica:
        tipo_caja = (
            "DSG"
            if re.search("\\bdsg\\b", texto_l)
            else "CVT"
            if re.search("\\bcvt\\b", texto_l)
            else "automática"
        )
        estado.transmision = tipo_caja
    golpe_cambios = bool(
        re.search("\\b(?:golpe(?:a|teo|tea)?|patea|tironea)\\b", texto_l)
        and re.search("\\b(?:pasar|cambiar|meter|seleccionar|entrar)\\b", texto_l)
        and re.search("\\b(?:cambios?|marchas?|velocidades?|d|r)\\b", texto_l)
        and (
            menciona_caja_automatica
            or estado.transmision
            or re.search("\\b(?:caja|transmisi[oó]n|embrague|clutch|cambios?)\\b", texto_l)
        )
    )
    if golpe_cambios:
        h = estado.registrar_hecho(
            "sintoma_golpeteo_al_cambiar",
            "golpeteo al pasar cambios",
            categoria="sintoma",
            texto_crudo=texto_usuario,
            tipo=FactType.SINTOMA,
        )
        hechos_extraidos.append(h.to_dict())
    es_reversa = bool(re.search("\\b(reversa|retroceso|marcha\\s+atr[aá]s)\\b", texto_l))
    demora_acople = bool(re.search("\\b(demora|tarda)\\b.{0,45}\\b(enganchar|entrar|acoplar)\\b", texto_l))
    golpe_acople = bool(re.search("\\b(entra|engancha|acopla)\\b.{0,35}\\b(golpe|golpea|patea)\\b", texto_l))
    if es_reversa and demora_acople:
        estado.transmision = (
            "Automatica" if "automático" in texto_l or "automatico" in texto_l else estado.transmision
        )
        h = estado.registrar_hecho(
            "sintoma_demora_acople_reversa",
            "reversa demora en enganchar",
            categoria="sintoma",
            texto_crudo=texto_usuario,
            tipo=FactType.SINTOMA,
        )
        hechos_extraidos.append(h.to_dict())
        h = estado.registrar_hecho(
            "condicion_operacion",
            "al seleccionar reversa",
            categoria="condicion",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())
    if es_reversa and golpe_acople:
        h = estado.registrar_hecho(
            "sintoma_golpe_acople_reversa",
            "reversa entra con golpe",
            categoria="sintoma",
            texto_crudo=texto_usuario,
            tipo=FactType.SINTOMA,
        )
        hechos_extraidos.append(h.to_dict())
    es_no_arranca_componente = bool(
        re.search(
            "\\b(?:electroventilador|motoventilador|ventilador|electro|compresor)\\s+(?:no\\s+)",
            texto_usuario.lower(),
        )
    )
    es_arranca_y_se_apaga = bool(
        re.search(
            "\\b(s[ií]\\s+arranca\\s*[, ]+(?:pero\\s+)?se\\s+apaga|arranca\\s+y\\s+se\\s+apaga|arranca\\s*[, ]+(?:pero\\s+)?(?:luego\\s+)?se\\s+apaga)\\b",
            texto_usuario.lower(),
        )
        or (
            re.search("\\bno\\s+es\\s+que\\s+no\\s+(?:arranque|prenda|encienda)\\b", texto_usuario.lower())
            and re.search("\\b(?:se\\s+)?apaga\\b", texto_usuario.lower())
        )
    )
    es_arranca_confirmado = bool(
        re.search(
            "\\b(no\\s+es\\s+que\\s+no\\s+(?:arranque|prenda|encienda)|(?:el\\s+)?motor\\s+arranca\\s+(?:bien|al\\s+toque|normal|r[aá]pido))\\b",
            texto_usuario.lower(),
        )
    )
    if es_arranca_y_se_apaga:
        estado.eliminar_hecho("sintoma_motor_no_arranca")
        h_arr = estado.registrar_hecho(
            "sintoma_arranca_y_se_apaga",
            "arranca y se apaga",
            categoria="sintoma",
            texto_crudo=texto_usuario,
            tipo=FactType.SINTOMA,
        )
        hechos_extraidos.append(h_arr.to_dict())
        h_mot = estado.registrar_hecho(
            "motor_arranca", "SI", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION
        )
        hechos_extraidos.append(h_mot.to_dict())
    elif es_arranca_confirmado:
        estado.eliminar_hecho("sintoma_motor_no_arranca")
        h_mot = estado.registrar_hecho(
            "motor_arranca", "SI", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION
        )
        hechos_extraidos.append(h_mot.to_dict())
    elif PATRON_NO_ARRANCA.search(texto_usuario) and (not es_no_arranca_componente):
        h = estado.registrar_hecho(
            "motor_arranca", "NO", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION
        )
        hechos_extraidos.append(h.to_dict())
    if PATRON_GIRO_LLAVE.search(texto_usuario):
        h = estado.registrar_hecho(
            "evento", "giro_llave", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION
        )
        hechos_extraidos.append(h.to_dict())
    if PATRON_CLIC_UNICO.search(texto_usuario):
        h = estado.registrar_hecho(
            "ruido_arranque",
            "clic_unico",
            categoria="sintoma",
            texto_crudo=texto_usuario,
            tipo=FactType.SINTOMA,
        )
        hechos_extraidos.append(h.to_dict())
    elif PATRON_CLICS_REPETIDOS.search(texto_usuario):
        h = estado.registrar_hecho(
            "ruido_arranque",
            "clics_repetidos",
            categoria="sintoma",
            texto_crudo=texto_usuario,
            tipo=FactType.SINTOMA,
        )
        hechos_extraidos.append(h.to_dict())
    if PATRON_TABLERO_PRENDE.search(texto_usuario):
        h = estado.registrar_hecho(
            "tablero_enciende",
            "SI",
            categoria="condicion",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())
    if PATRON_RADIO_PRENDE.search(texto_usuario):
        h = estado.registrar_hecho(
            "radio_enciende", "SI", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION
        )
        hechos_extraidos.append(h.to_dict())
    if PATRON_LUCES_ATENUAN.search(texto_usuario):
        h = estado.registrar_hecho(
            "luces_se_atenuan",
            "SI",
            categoria="condicion",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())
    if PATRON_ANTECEDENTE_MARCHA.search(texto_usuario):
        h = estado.registrar_hecho(
            "antecedente_motor_en_marcha",
            "SI",
            categoria="condicion",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())
    for campo_s, val_s, estado_s in DetectorPolaridad.extraer_sintomas(texto_usuario):
        if golpe_cambios and campo_s == "sintoma_ruido_anómalo":
            continue
        hecho_existente = estado.obtener_hecho(campo_s)
        if (
            hecho_existente
            and hecho_existente.estado == FactState.CONFIRMADO
            and (estado_s == FactState.AUSENTE_NEGADO)
        ):
            if re.search(
                "\\b(?:en\\s+el\\s+pedal|resto\\s+del\\s+veh[ií]culo)\\b", texto_usuario, re.IGNORECASE
            ):
                continue
        h = estado.registrar_hecho(
            campo_s,
            val_s,
            categoria="sintoma",
            estado=estado_s,
            texto_crudo=texto_usuario,
            tipo=FactType.SINTOMA,
        )
        hechos_extraidos.append(h.to_dict())
        if (
            estado_s == FactState.CONFIRMADO
            and hasattr(estado, "active_symptoms")
            and (val_s not in estado.active_symptoms)
        ):
            estado.active_symptoms.append(val_s)
    if (
        not es_arranca_y_se_apaga
        and PATRON_NO_ARRANCA.search(texto_normalizado.lower())
        and (not es_no_arranca_componente)
        and (not estado.obtener_hecho("sintoma_motor_no_arranca"))
    ):
        h = estado.registrar_hecho(
            "sintoma_motor_no_arranca",
            "motor no arranca",
            categoria="sintoma",
            texto_crudo=texto_usuario,
            tipo=FactType.SINTOMA,
        )
        hechos_extraidos.append(h.to_dict())
    if PATRON_DEMORA_ARRANQUE.search(texto_usuario):
        h = estado.registrar_hecho(
            "sintoma_demora_arranque",
            "demora en arrancar",
            categoria="sintoma",
            texto_crudo=texto_usuario,
            tipo=FactType.SINTOMA,
        )
        hechos_extraidos.append(h.to_dict())
        if not estado.obtener_hecho("condicion_operacion"):
            h_c = estado.registrar_hecho(
                "condicion_operacion",
                "al dar arranque en frío",
                categoria="condicion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_c.to_dict())
    return texto_l
