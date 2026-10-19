"""Extracción especializada: perfil_vehicular."""

from __future__ import annotations

import re
from typing import List, Tuple

from src.core.conversacion.extraccion_hechos.clasificador_mensajes import (
    es_reinicio_solicitado,
    extraer_placa,
)
from src.core.conversacion.extraccion_hechos.patrones_hechos import (
    PATRON_AFIRMACION_VEHICULAR,
    PATRON_ANIO,
    PATRON_ANTECEDENTE_VEHICULAR,
    PATRON_COMPARATIVO_POST,
    PATRON_CORRECCION_VEHICULO,
    PATRONES_COMBUSTIBLE,
    PATRONES_MARCA,
    PATRONES_MODELO,
    seleccionar_entidad_vehicular,
)
from src.core.conversacion.models import FactState, FactType


def extraer_perfil_vehicular(estado, texto_usuario, texto_normalizado, hechos_extraidos):
    placa_encontrada = extraer_placa(texto_usuario)
    if placa_encontrada:
        actualizar_placa = False
        if estado.placa and estado.placa != placa_encontrada:
            es_correccion = bool(
                re.search(
                    "\\b(me\\s+equivoqu[eé]|corrijo|la\\s+placa\\s+correcta|no\\s+era\\s+esa\\s+placa|placa\\s+real)\\b",
                    texto_usuario,
                    re.IGNORECASE,
                )
            )
            if es_correccion:
                placa_vieja = estado.placa
                if placa_vieja and hasattr(estado, "active_symptoms") and estado.active_symptoms:
                    estado.active_symptoms = [
                        re.sub(f"\\b{placa_vieja}\\b", placa_encontrada, s, flags=re.IGNORECASE)
                        for s in estado.active_symptoms
                    ]
                actualizar_placa = True
            elif es_reinicio_solicitado(texto_usuario) or re.search(
                "\\b(?:otro\\s+(?:carro|auto|veh[ií]culo)|nuevo\\s+caso)\\b", texto_usuario, re.IGNORECASE
            ):
                estado.reiniciar()
                estado.historial_mensajes_usuario.append(texto_usuario)
                estado.turno_actual = 1
                actualizar_placa = True
        else:
            actualizar_placa = True
        if actualizar_placa:
            estado.placa = placa_encontrada
            h_placa = estado.registrar_hecho(
                "placa",
                placa_encontrada,
                categoria="vehiculo",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_placa.to_dict())
    marcas_encontradas: List[Tuple[int, int, str]] = []
    for patron, marca in PATRONES_MARCA:
        for m in patron.finditer(texto_usuario):
            marcas_encontradas.append((m.start(), m.end(), marca))
    nueva_marca, marca_actual_negada = seleccionar_entidad_vehicular(
        texto_usuario, marcas_encontradas, estado.marca
    )
    if nueva_marca:
        if estado.marca and estado.marca != nueva_marca:
            marca_actual_como_antecedente = any(
                (
                    nombre.casefold() == estado.marca.casefold()
                    and PATRON_ANTECEDENTE_VEHICULAR.search(texto_usuario[:start].rstrip(" ,;:"))
                    for start, end, nombre in marcas_encontradas
                )
            )
            nueva_marca_afirmada = any(
                (
                    nombre.casefold() == nueva_marca.casefold()
                    and PATRON_AFIRMACION_VEHICULAR.search(texto_usuario[:start].rstrip(" ,;:"))
                    for start, end, nombre in marcas_encontradas
                )
            )
            es_correccion = bool(
                marca_actual_negada
                or marca_actual_como_antecedente
                or nueva_marca_afirmada
                or PATRON_CORRECCION_VEHICULO.search(texto_usuario)
            )
            es_cambio_explicito = bool(
                (
                    re.search(
                        "\\b(?:cambiar|cambio|cambiemos|dejemos|otro|otra|nuevo|neuvo)\\s+(?:de\\s+)?(?:carro|auto|vehiculo|caso)\\b",
                        texto_usuario,
                        re.IGNORECASE,
                    )
                    if not re.search(
                        "\\b(?:su|un|el|mi)?\\s*otro\\s+(?:auto|carro|vehiculo).{0,80}\\b(?:pero|aunque|sin embargo|estamos|revisando|este)\\b",
                        texto_usuario,
                        re.IGNORECASE,
                    )
                    else False
                )
                or re.search(
                    "\\b(?:ahora|ahora\\s+es|este\\s+es)\\s+(?:un|una)\\b", texto_usuario, re.IGNORECASE
                )
                or re.search("\\bahora\\s+tengo\\s+(?:un|una)\\b", texto_usuario, re.IGNORECASE)
                or re.search("\\bdejemos\\s+el\\s+[a-z]+", texto_usuario, re.IGNORECASE)
            )
            if es_cambio_explicito:
                p_prev = estado.placa or placa_encontrada
                estado.reiniciar()
                estado.historial_mensajes_usuario.append(texto_usuario)
                estado.turno_actual = 1
                if p_prev and (
                    not re.search(
                        "\\b(?:otro|otra)\\s+(?:carro|auto|vehiculo)\\b", texto_usuario, re.IGNORECASE
                    )
                ):
                    estado.placa = p_prev
                    estado.registrar_hecho(
                        "placa",
                        p_prev,
                        categoria="vehiculo",
                        texto_crudo=texto_usuario,
                        tipo=FactType.CONDICION,
                    )
                estado.marca = nueva_marca
                h = estado.registrar_hecho(
                    "marca",
                    nueva_marca,
                    categoria="vehiculo",
                    texto_crudo=texto_usuario,
                    tipo=FactType.CONDICION,
                )
                hechos_extraidos.append(h.to_dict())
            elif es_correccion:
                estado.last_user_correction = "marca"
                estado.turno_ultima_correccion = estado.turno_actual
                marca_antigua = estado.marca
                if marca_antigua and hasattr(estado, "active_symptoms") and estado.active_symptoms:
                    estado.active_symptoms = [
                        re.sub(
                            f"\\b(?:no\\s+(?:es|era)\\s+)?{marca_antigua}\\b",
                            nueva_marca,
                            s,
                            flags=re.IGNORECASE,
                        )
                        for s in estado.active_symptoms
                    ]
                estado.marca = nueva_marca
                h = estado.registrar_hecho(
                    "marca",
                    nueva_marca,
                    categoria="vehiculo",
                    texto_crudo=texto_usuario,
                    tipo=FactType.CONDICION,
                )
                hechos_extraidos.append(h.to_dict())
                if marca_actual_como_antecedente and marca_antigua:
                    campo_ant = f"vehiculo_mencionado_{marca_antigua.lower()}"
                    h_ant = estado.registrar_hecho(
                        campo_ant,
                        marca_antigua,
                        categoria="antecedente",
                        texto_crudo=texto_usuario,
                        tipo=FactType.CONDICION,
                    )
                    hechos_extraidos.append(h_ant.to_dict())
            else:
                campo_ant = f"vehiculo_mencionado_{nueva_marca.lower()}"
                h_ant = estado.registrar_hecho(
                    campo_ant,
                    nueva_marca,
                    categoria="antecedente",
                    texto_crudo=texto_usuario,
                    tipo=FactType.CONDICION,
                )
                hechos_extraidos.append(h_ant.to_dict())
        else:
            estado.marca = nueva_marca
            h = estado.registrar_hecho(
                "marca", nueva_marca, categoria="vehiculo", texto_crudo=texto_usuario, tipo=FactType.CONDICION
            )
            hechos_extraidos.append(h.to_dict())
            for start, end, nombre in marcas_encontradas:
                if nombre.casefold() != nueva_marca.casefold():
                    prefijo = texto_usuario[:start].rstrip(" ,;:")
                    ventana_pre = prefijo[-75:] if len(prefijo) > 75 else prefijo
                    if PATRON_ANTECEDENTE_VEHICULAR.search(ventana_pre):
                        campo_ant = f"vehiculo_mencionado_{nombre.lower()}"
                        h_ant = estado.registrar_hecho(
                            campo_ant,
                            nombre,
                            categoria="antecedente",
                            texto_crudo=texto_usuario,
                            tipo=FactType.CONDICION,
                        )
                        hechos_extraidos.append(h_ant.to_dict())
    elif marca_actual_negada and (not nueva_marca):
        estado.marca = None
        if "marca" in estado.hechos:
            del estado.hechos["marca"]
    else:
        for start, end, nombre in marcas_encontradas:
            if not estado.marca or nombre.casefold() != estado.marca.casefold():
                prefijo = texto_usuario[:start].rstrip(" ,;:")
                ventana_pre = prefijo[-75:] if len(prefijo) > 75 else prefijo
                sufijo = texto_usuario[end:].lstrip(" ,;:")
                ventana_post = sufijo[:75]
                if PATRON_ANTECEDENTE_VEHICULAR.search(ventana_pre) or PATRON_COMPARATIVO_POST.search(
                    ventana_post
                ):
                    campo_ant = f"vehiculo_mencionado_{nombre.lower()}"
                    h_ant = estado.registrar_hecho(
                        campo_ant,
                        nombre,
                        categoria="antecedente",
                        texto_crudo=texto_usuario,
                        tipo=FactType.CONDICION,
                    )
                    hechos_extraidos.append(h_ant.to_dict())
    m_anio = PATRON_ANIO.search(texto_usuario)
    if m_anio:
        nuevo_anio = m_anio.group(1)
        tiene_contexto_anio = not estado.anio or bool(
            re.search(
                f"\\b(?:a[ñn]o|del|modelo|es\\s+[a-záéíóú0-9\\s]*{nuevo_anio}|corrijo)\\b",
                texto_usuario,
                re.IGNORECASE,
            )
        )
        if tiene_contexto_anio and (not estado.anio or estado.anio != nuevo_anio):
            anio_viejo = estado.anio
            if anio_viejo and hasattr(estado, "active_symptoms") and estado.active_symptoms:
                estado.active_symptoms = [
                    re.sub(f"\\b(?:no\\s+(?:es|era)\\s+)?{anio_viejo}\\b", nuevo_anio, s, flags=re.IGNORECASE)
                    for s in estado.active_symptoms
                ]
            estado.anio = nuevo_anio
            h = estado.registrar_hecho(
                "anio", nuevo_anio, categoria="vehiculo", texto_crudo=texto_usuario, tipo=FactType.CONDICION
            )
            hechos_extraidos.append(h.to_dict())
    modelos_encontrados: List[Tuple[int, int, str]] = []
    for patron, mod in PATRONES_MODELO:
        for m in patron.finditer(texto_usuario):
            modelos_encontrados.append((m.start(), m.end(), mod))
    nuevo_mod, mod_actual_negado = seleccionar_entidad_vehicular(
        texto_usuario, modelos_encontrados, estado.modelo
    )
    if nuevo_mod:
        if estado.modelo and estado.modelo != nuevo_mod:
            mod_antiguo = estado.modelo
            if mod_antiguo and hasattr(estado, "active_symptoms") and estado.active_symptoms:
                estado.active_symptoms = [
                    re.sub(f"\\b(?:no\\s+(?:es|era)\\s+)?{mod_antiguo}\\b", nuevo_mod, s, flags=re.IGNORECASE)
                    for s in estado.active_symptoms
                ]
        estado.modelo = nuevo_mod
        h = estado.registrar_hecho(
            "modelo", nuevo_mod, categoria="vehiculo", texto_crudo=texto_usuario, tipo=FactType.CONDICION
        )
        hechos_extraidos.append(h.to_dict())
    elif mod_actual_negado and (not nuevo_mod):
        estado.modelo = None
        if "modelo" in estado.hechos:
            del estado.hechos["modelo"]
    else:
        for start, end, nombre in modelos_encontrados:
            if not estado.modelo or nombre.casefold() != estado.modelo.casefold():
                prefijo = texto_usuario[:start].rstrip(" ,;:")
                ventana_pre = prefijo[-75:] if len(prefijo) > 75 else prefijo
                sufijo = texto_usuario[end:].lstrip(" ,;:")
                ventana_post = sufijo[:75]
                if PATRON_ANTECEDENTE_VEHICULAR.search(ventana_pre) or PATRON_COMPARATIVO_POST.search(
                    ventana_post
                ):
                    campo_ant = f"modelo_mencionado_{nombre.lower()}"
                    h_ant = estado.registrar_hecho(
                        campo_ant,
                        nombre,
                        categoria="antecedente",
                        texto_crudo=texto_usuario,
                        tipo=FactType.CONDICION,
                    )
                    hechos_extraidos.append(h_ant.to_dict())
    motor_match = re.search(
        "\\bmotor\\s+([a-z0-9][a-z0-9.-]*(?:\\s+(?:tsi|tdi|hdi|crdi|d-4d|turbo))?)\\b",
        texto_usuario,
        re.IGNORECASE,
    )
    if not motor_match:
        motor_match = re.search(
            "\\b(?:19[89]\\d|20[0-2]\\d)\\s+([1-9]\\d?(?:[.,]\\d)?(?:\\s+(?:tsi|tdi|hdi|crdi|d-4d|turbo))?)\\s+(?:di[eé]sel|gasolina|glp|gnv)\\b",
            texto_usuario,
            re.IGNORECASE,
        )
    if motor_match:
        nuevo_motor = motor_match.group(1).strip().upper().replace(",", ".")
        if (
            nuevo_motor
            not in {
                "NO",
                "SE",
                "ESTA",
                "ESTÁ",
                "APAGADO",
                "ENCENDIDO",
                "EN",
                "ESTE",
                "HIRVIENDO",
                "CALIENTE",
                "FRIO",
                "FRÍO",
                "FUNCIONANDO",
            }
            and estado.motor != nuevo_motor
        ):
            estado.motor = nuevo_motor
            h_motor = estado.registrar_hecho(
                "motor", nuevo_motor, categoria="vehiculo", texto_crudo=texto_usuario, tipo=FactType.CONDICION
            )
            hechos_extraidos.append(h_motor.to_dict())
    if not motor_match:
        motor_despues_combustible = re.search(
            "\\b(?:di[eé]sel|gasolina|glp|gnv)\\s+([1-9]\\d?(?:[.,]\\d)?(?:\\s+(?:tsi|tdi|hdi|crdi|d-4d|turbo))?)\\b",
            texto_usuario,
            re.IGNORECASE,
        )
        if motor_despues_combustible and (not estado.motor):
            nuevo_motor = motor_despues_combustible.group(1).strip().upper().replace(",", ".")
            estado.motor = nuevo_motor
            h_motor = estado.registrar_hecho(
                "motor", nuevo_motor, categoria="vehiculo", texto_crudo=texto_usuario, tipo=FactType.CONDICION
            )
            hechos_extraidos.append(h_motor.to_dict())
    for patron, comb in PATRONES_COMBUSTIBLE:
        if patron.search(texto_usuario):
            nuevo_comb = comb
            if not estado.combustible or estado.combustible != nuevo_comb:
                estado.combustible = nuevo_comb
                h = estado.registrar_hecho(
                    "combustible",
                    nuevo_comb,
                    categoria="vehiculo",
                    texto_crudo=texto_usuario,
                    tipo=FactType.CONDICION,
                )
                hechos_extraidos.append(h.to_dict())
            break
    texto_l_trans = texto_usuario.lower()
    if re.search("\\b(mec[aá]nic[oa]|manual)\\b", texto_l_trans) and any(
        (
            w in texto_l_trans
            for w in ("caja", "transmision", "transmisión", "velocidades", "cambios", "embrague")
        )
    ):
        h_trans = estado.registrar_hecho(
            "transmision",
            "MANUAL",
            categoria="perfil",
            estado=FactState.CONFIRMADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_trans.to_dict())
    elif re.search("\\b(autom[aá]tic[oa]|cvt)\\b", texto_l_trans) and any(
        (w in texto_l_trans for w in ("caja", "transmision", "transmisión"))
    ):
        val_trans = "CVT" if "cvt" in texto_l_trans else "AUTOMATICA"
        h_trans = estado.registrar_hecho(
            "transmision",
            val_trans,
            categoria="perfil",
            estado=FactState.CONFIRMADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_trans.to_dict())
