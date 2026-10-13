"""Orquestador de extracción de hechos y actualización acumulativa de ConversationState."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from src.core.conversacion.detector_polaridad import DetectorPolaridad
from src.core.conversacion.diccionario_automotriz import (
    extraer_hechos_linguisticos,
    normalizar_jerga_automotriz,
)
from src.core.conversacion.extraccion_hechos.clasificador_mensajes import (
    es_reinicio_solicitado,
    extraer_placa,
    inferir_estado_operativo,
)
from src.core.conversacion.extraccion_hechos.correcciones_y_descartes import (
    detectar_correcciones,
    registrar_rechazos_explicitos,
)
from src.core.conversacion.extraccion_hechos.extraccion_taller import (
    extraer_comprobaciones_taller,
)
from src.core.conversacion.extraccion_hechos.patrones_hechos import (
    PATRON_ANIO,
    PATRON_ANTECEDENTE_MARCHA,
    PATRON_CLIC_UNICO,
    PATRON_CLICS_REPETIDOS,
    PATRON_CORRECCION_VEHICULO,
    PATRON_DEMORA_ARRANQUE,
    PATRON_DTC,
    PATRON_GIRO_LLAVE,
    PATRON_LUCES_ATENUAN,
    PATRON_NO_ARRANCA,
    PATRON_RADIO_PRENDE,
    PATRON_TABLERO_PRENDE,
    PATRONES_COMBUSTIBLE,
    PATRONES_MARCA,
    PATRONES_MODELO,
    seleccionar_entidad_vehicular,
)
from src.core.conversacion.models import (
    ConversationState,
    DtcStatus,
    EstadoOperativo,
    FactState,
    FactType,
)


def extraer_y_actualizar(
    estado: ConversationState,
    texto_usuario: str,
) -> List[Dict[str, Any]]:
    """Procesa el mensaje del usuario y actualiza el ConversationState acumulativo."""
    hechos_extraidos: List[Dict[str, Any]] = []
    texto_normalizado = normalizar_jerga_automotriz(texto_usuario)
    estado.historial_mensajes_usuario.append(texto_usuario)
    estado.turno_actual += 1

    # 1. Comprobar si hay correcciones explícitas
    corrs = detectar_correcciones(texto_usuario)
    if corrs:
        estado.last_user_correction = texto_usuario
        estado.turno_ultima_correccion = estado.turno_actual
        for campo, nuevo_val, cat, tipo_f in corrs:
            if campo == "sintoma_demora_arranque":
                estado.eliminar_hecho("sintoma_climatizacion")
                estado.eliminar_hecho("falla_confirmada_usuario")
                estado.eliminar_hecho("condicion_operacion")
                estado.estado_operativo = EstadoOperativo.ARRANQUE
                estado.dominio_probable = "ARRANQUE"
            elif campo == "estado_operativo":
                try:
                    estado.estado_operativo = EstadoOperativo(nuevo_val)
                except (ValueError, TypeError):
                    pass
            est_f = FactState.AUSENTE_NEGADO if (cat == "polaridad" and nuevo_val == "ausente") else FactState.CONFIRMADO
            h = estado.registrar_hecho(
                campo=campo,
                valor=nuevo_val,
                categoria=cat,
                estado=est_f,
                texto_crudo=texto_usuario,
                tipo=tipo_f,
            )
            hechos_extraidos.append(h.to_dict())

    # 1.5 Extracción de placa vehicular
    placa_encontrada = extraer_placa(texto_usuario)
    if placa_encontrada:
        actualizar_placa = False
        if estado.placa and estado.placa != placa_encontrada:
            es_correccion = bool(
                re.search(
                    r"\b(me\s+equivoqu[eé]|corrijo|la\s+placa\s+correcta|no\s+era\s+esa\s+placa|placa\s+real)\b",
                    texto_usuario,
                    re.IGNORECASE,
                )
            )
            if es_correccion:
                placa_vieja = estado.placa
                if placa_vieja and hasattr(estado, "active_symptoms") and estado.active_symptoms:
                    estado.active_symptoms = [
                        re.sub(rf"\b{placa_vieja}\b", placa_encontrada, s, flags=re.IGNORECASE)
                        for s in estado.active_symptoms
                    ]
                actualizar_placa = True
            elif es_reinicio_solicitado(texto_usuario) or re.search(
                r"\b(?:otro\s+(?:carro|auto|veh[ií]culo)|nuevo\s+caso)\b", texto_usuario, re.IGNORECASE
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

    # 2. Extracción de marca / modelo / año / combustible
    marcas_encontradas: List[Tuple[int, int, str]] = []
    for patron, marca in PATRONES_MARCA:
        for m in patron.finditer(texto_usuario):
            marcas_encontradas.append((m.start(), m.end(), marca))

    nueva_marca, marca_actual_negada = seleccionar_entidad_vehicular(
        texto_usuario, marcas_encontradas, estado.marca
    )
    if nueva_marca:
        if estado.marca and estado.marca != nueva_marca:
            es_correccion = bool(marca_actual_negada or PATRON_CORRECCION_VEHICULO.search(texto_usuario))
            if es_correccion:
                estado.last_user_correction = "marca"
                estado.turno_ultima_correccion = estado.turno_actual
                marca_antigua = estado.marca
                if marca_antigua and hasattr(estado, "active_symptoms") and estado.active_symptoms:
                    estado.active_symptoms = [
                        re.sub(rf"\b(?:no\s+(?:es|era)\s+)?{marca_antigua}\b", nueva_marca, s, flags=re.IGNORECASE)
                        for s in estado.active_symptoms
                    ]
            else:
                p_prev = estado.placa or placa_encontrada
                estado.reiniciar()
                estado.historial_mensajes_usuario.append(texto_usuario)
                estado.turno_actual = 1
                if p_prev and not re.search(r"\b(?:otro|otra)\s+(?:carro|auto|vehiculo)\b", texto_usuario, re.IGNORECASE):
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
    elif marca_actual_negada and not nueva_marca:
        estado.marca = None
        if "marca" in estado.hechos:
            del estado.hechos["marca"]

    m_anio = PATRON_ANIO.search(texto_usuario)
    if m_anio:
        nuevo_anio = m_anio.group(1)
        tiene_contexto_anio = not estado.anio or bool(re.search(rf"\b(?:a[ñn]o|del|modelo|es\s+[a-záéíóú0-9\s]*{nuevo_anio}|corrijo)\b", texto_usuario, re.IGNORECASE))
        if tiene_contexto_anio and (not estado.anio or estado.anio != nuevo_anio):
            anio_viejo = estado.anio
            if anio_viejo and hasattr(estado, "active_symptoms") and estado.active_symptoms:
                estado.active_symptoms = [
                    re.sub(rf"\b{anio_viejo}\b", nuevo_anio, s)
                    for s in estado.active_symptoms
                ]
            estado.anio = nuevo_anio
            h = estado.registrar_hecho(
                "anio",
                nuevo_anio,
                categoria="vehiculo",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h.to_dict())

    modelos_encontrados: List[Tuple[int, int, str]] = []
    for patron, mod in PATRONES_MODELO:
        for m in patron.finditer(texto_usuario):
            modelos_encontrados.append((m.start(), m.end(), mod))

    nuevo_mod, mod_actual_negado = seleccionar_entidad_vehicular(
        texto_usuario, modelos_encontrados, estado.modelo
    )
    if not nuevo_mod and (not estado.modelo or mod_actual_negado) and (estado.marca or nueva_marca):
        m_marca = estado.marca or nueva_marca
        m_gen = re.search(
            rf"\b{re.escape(m_marca)}\s+([A-Za-z0-9-]+)\b(?!\s*(?:placa|diesel|gasolina|glp|gnv))",
            texto_usuario,
            re.IGNORECASE,
        )
        if m_gen and not re.match(r"^(?:19[89]\d|20[0-2]\d|[A-Za-z]{3}-\d{3})$", m_gen.group(1)):
            cand = m_gen.group(1).title()
            stop_mods = {"MOTOR", "AUTO", "CARRO", "CAMIONETA", "CON", "DEL", "EN", "ESPECIFICA", "INDICA", "DICE", "MANUAL"}
            if len(cand) >= 2 and cand.upper() not in stop_mods:
                nuevo_mod = cand
    if nuevo_mod:
        if estado.modelo and estado.modelo != nuevo_mod:
            estado.last_user_correction = "modelo"
            estado.turno_ultima_correccion = estado.turno_actual
            mod_antiguo = estado.modelo
            if mod_antiguo and hasattr(estado, "active_symptoms") and estado.active_symptoms:
                estado.active_symptoms = [
                    re.sub(rf"\b(?:no\s+(?:es|era)\s+)?{mod_antiguo}\b", nuevo_mod, s, flags=re.IGNORECASE)
                    for s in estado.active_symptoms
                ]
        estado.modelo = nuevo_mod
        h = estado.registrar_hecho(
            "modelo",
            nuevo_mod,
            categoria="vehiculo",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())
    elif mod_actual_negado and not nuevo_mod:
        estado.modelo = None
        if "modelo" in estado.hechos:
            del estado.hechos["modelo"]

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
    if re.search(r"\b(mec[aá]nic[oa]|manual)\b", texto_l_trans) and any(
        w in texto_l_trans for w in ("caja", "transmision", "transmisión", "velocidades", "cambios", "embrague")
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
    elif re.search(r"\b(autom[aá]tic[oa]|cvt)\b", texto_l_trans) and any(
        w in texto_l_trans for w in ("caja", "transmision", "transmisión")
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

    # 3. Extracción de DTC
    for dtc in PATRON_DTC.findall(texto_usuario):
        dtc_canonico = dtc.upper()
        campo = f"dtc_{dtc_canonico}"
        estado.dtc_status = DtcStatus.DTC_OBSERVADO
        h = estado.registrar_hecho(campo, dtc_canonico, categoria="dtc", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    # 4. Mediciones y comprobaciones de taller
    hechos_extraidos.extend(extraer_comprobaciones_taller(estado, texto_usuario, texto_normalizado))
    hechos_extraidos.extend(registrar_rechazos_explicitos(estado, texto_usuario))

    # 5. Modificadores y sistemas complementarios
    texto_l = texto_usuario.lower()
    es_queja_climatizacion = bool(
        re.search(
            r"\b(no\s+enfr[ií]a|enfr[ií]a\s+(?:poco|nada|casi\s+nada)|deja\s+de\s+enfriar|solo\s+enfr[ií]a|enfr[ií]a\s+(?:solo|cuando)|sale\s+aire\s+(?:caliente|tibio|ambiente|a\s+temperatura\s+ambiente)|sin\s+gas(?:\s+r134a)?|falta\s+(?:de\s+)?gas\s+(?:al\s+aire|r134a)|compresor\s+(?:no\s+entra|no\s+acopla|no\s+pega|no\s+arranca|no\s+activa)|clima\s+(?:no\s+enfr[ií]a|calienta|no\s+sopla\s+fr[ií]o)|aire\s+(?:caliente|tibio|no\s+tira\s+fr[ií]o)|fuga\s+de\s+gas\s+(?:r134a|del\s+aire))\b",
            texto_l,
        )
    )
    tiene_mencion_ac = bool(re.search(r"\b(a/c|aire\s+acondicionado|clima|el\s+ac)\b", texto_l))

    if es_queja_climatizacion:
        estado.dominio_probable = "CLIMATIZACION"
        h = estado.registrar_hecho("sintoma_climatizacion", "aire acondicionado no enfría / sale aire caliente", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
        hechos_extraidos.append(h.to_dict())
        if re.search(r"\b(sem[aá]foro|detenido|al\s+parar|al\s+detener)\b", texto_l) and re.search(r"\b(manejando|en\s+movimiento|velocidad)\b", texto_l):
            h_op = estado.registrar_hecho("condicion_operacion", "deja de enfriar detenido en semáforo", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_op.to_dict())
    elif tiene_mencion_ac:
        h = estado.registrar_hecho("modificador_ac", "A/C encendido", categoria="modificador", texto_crudo=texto_usuario, tipo=FactType.MODIFICADOR)
        hechos_extraidos.append(h.to_dict())

    es_queja_refrigeracion = bool(
        re.search(
            r"\b(recalienta|recalentar|recalentando|recalent[oó]|se\s+recalienta|el\s+auto\s+recalienta|el\s+carro\s+recalienta|motor\s+recalienta|hierve|hirviendo|levanta\s+temperatura|se\s+calienta|calienta\s+el\s+motor|(?:se\s+(?:le\s+)?sube|sube|subi[oó])\s+(?:la\s+)?temperatura|temperatura\s+(?:del\s+motor\s+)?(?:est[aá]\s+)?subiendo|temperatura\s+(?:sube|al\s+tope|volando|elevada|alta)|aguja\s+de\s+temperatura|(?:bota|botando|sale|echando)\s+vapor|vapor\s+(?:bajo|del|por\s+el)\s+cap[oó]|termostato|electroventilador|motoventilador|manguera\s+(?:inferior|superior)?(?:\s+del)?\s+radiador)\b",
            texto_l,
        )
        and not re.search(r"\bno\s+(?:se\s+)?(?:recalienta|calienta|hierve)\b", texto_l)
    )
    if es_queja_refrigeracion:
        estado.dominio_probable = "REFRIGERACION"
        h_ref = estado.registrar_hecho("sintoma_sobrecalentamiento", "sobrecalentamiento del motor / sistema de refrigeración", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
        hechos_extraidos.append(h_ref.to_dict())

    if re.search(r"\b(luces?\s+prendidas?|luces?\s+altas?|prendo\s+las\s+luces?|con\s+luces?|luces?\s+(?:se\s+ponen\s+)?tenues?|bajan?\s+las\s+luces?|luces?\s+bajas?)\b", texto_l):
        luces_tenues = bool(re.search(r"\b(tenues?|bajan?\s+las\s+luces?|luces?\s+bajas?)\b", texto_l))
        valor_luces = "luces tenues" if luces_tenues else "luces encendidas"
        h = estado.registrar_hecho("modificador_luces", valor_luces, categoria="modificador", texto_crudo=texto_usuario, tipo=FactType.MODIFICADOR)
        hechos_extraidos.append(h.to_dict())

    ling = extraer_hechos_linguisticos(texto_usuario)
    for k, v in ling.items():
        if corrs and any(c[0] == k for c in corrs):
            continue
        cat = "temperatura" if k == "temperatura" else ("cambio_accion" if k == "evolucion_accion" else "condicion")
        h = estado.registrar_hecho(k, v, categoria=cat, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    menciona_caja_automatica = bool(re.search(r"\b(?:caja\s+(?:de\s+cambios\s+)?autom[aá]tica|transmisi[oó]n\s+autom[aá]tica|dsg|cvt)\b", texto_l))
    if menciona_caja_automatica:
        tipo_caja = "DSG" if re.search(r"\bdsg\b", texto_l) else ("CVT" if re.search(r"\bcvt\b", texto_l) else "automática")
        estado.transmision = tipo_caja

    golpe_cambios = bool(
        re.search(r"\b(?:golpe(?:a|teo|tea)?|patea|tironea)\b", texto_l)
        and re.search(r"\b(?:pasar|cambiar|meter|seleccionar|entrar)\b", texto_l)
        and re.search(r"\b(?:cambios?|marchas?|velocidades?|d|r)\b", texto_l)
        and (menciona_caja_automatica or estado.transmision or re.search(r"\b(?:caja|transmisi[oó]n|embrague|clutch|cambios?)\b", texto_l))
    )
    if golpe_cambios:
        h = estado.registrar_hecho("sintoma_golpeteo_al_cambiar", "golpeteo al pasar cambios", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
        hechos_extraidos.append(h.to_dict())

    es_reversa = bool(re.search(r"\b(reversa|retroceso|marcha\s+atr[aá]s)\b", texto_l))
    demora_acople = bool(re.search(r"\b(demora|tarda)\b.{0,45}\b(enganchar|entrar|acoplar)\b", texto_l))
    golpe_acople = bool(re.search(r"\b(entra|engancha|acopla)\b.{0,35}\b(golpe|golpea|patea)\b", texto_l))
    if es_reversa and demora_acople:
        estado.transmision = "Automatica" if "automático" in texto_l or "automatico" in texto_l else estado.transmision
        h = estado.registrar_hecho("sintoma_demora_acople_reversa", "reversa demora en enganchar", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
        hechos_extraidos.append(h.to_dict())
        h = estado.registrar_hecho("condicion_operacion", "al seleccionar reversa", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
    if es_reversa and golpe_acople:
        h = estado.registrar_hecho("sintoma_golpe_acople_reversa", "reversa entra con golpe", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
        hechos_extraidos.append(h.to_dict())

    # 6. Arranque y eventos
    es_no_arranca_componente = bool(
        re.search(r"\b(?:electroventilador|motoventilador|ventilador|electro|compresor)\s+(?:no\s+)", texto_usuario.lower())
    )
    es_arranca_y_se_apaga = bool(
        re.search(r"\b(s[ií]\s+arranca\s*[, ]+(?:pero\s+)?se\s+apaga|arranca\s+y\s+se\s+apaga|arranca\s*[, ]+(?:pero\s+)?(?:luego\s+)?se\s+apaga)\b", texto_usuario.lower())
        or (re.search(r"\bno\s+es\s+que\s+no\s+(?:arranque|prenda|encienda)\b", texto_usuario.lower()) and re.search(r"\b(?:se\s+)?apaga\b", texto_usuario.lower()))
    )
    es_arranca_confirmado = bool(
        re.search(r"\b(no\s+es\s+que\s+no\s+(?:arranque|prenda|encienda)|(?:el\s+)?motor\s+arranca\s+(?:bien|al\s+toque|normal|r[aá]pido))\b", texto_usuario.lower())
    )
    if es_arranca_y_se_apaga:
        estado.eliminar_hecho("sintoma_motor_no_arranca")
        h_arr = estado.registrar_hecho("sintoma_arranca_y_se_apaga", "arranca y se apaga", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
        hechos_extraidos.append(h_arr.to_dict())
        h_mot = estado.registrar_hecho("motor_arranca", "SI", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_mot.to_dict())
    elif es_arranca_confirmado:
        estado.eliminar_hecho("sintoma_motor_no_arranca")
        h_mot = estado.registrar_hecho("motor_arranca", "SI", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_mot.to_dict())
    elif PATRON_NO_ARRANCA.search(texto_usuario) and not es_no_arranca_componente:
        h = estado.registrar_hecho("motor_arranca", "NO", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if PATRON_GIRO_LLAVE.search(texto_usuario):
        h = estado.registrar_hecho("evento", "giro_llave", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if PATRON_CLIC_UNICO.search(texto_usuario):
        h = estado.registrar_hecho("ruido_arranque", "clic_unico", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
        hechos_extraidos.append(h.to_dict())
    elif PATRON_CLICS_REPETIDOS.search(texto_usuario):
        h = estado.registrar_hecho("ruido_arranque", "clics_repetidos", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
        hechos_extraidos.append(h.to_dict())

    if PATRON_TABLERO_PRENDE.search(texto_usuario):
        h = estado.registrar_hecho("tablero_enciende", "SI", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if PATRON_RADIO_PRENDE.search(texto_usuario):
        h = estado.registrar_hecho("radio_enciende", "SI", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if PATRON_LUCES_ATENUAN.search(texto_usuario):
        h = estado.registrar_hecho("luces_se_atenuan", "SI", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if PATRON_ANTECEDENTE_MARCHA.search(texto_usuario):
        h = estado.registrar_hecho("antecedente_motor_en_marcha", "SI", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    # 7. Síntomas primarios
    for campo_s, val_s, estado_s in DetectorPolaridad.extraer_sintomas(texto_usuario):
        if golpe_cambios and campo_s == "sintoma_ruido_anómalo":
            continue
        h = estado.registrar_hecho(campo_s, val_s, categoria="sintoma", estado=estado_s, texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
        hechos_extraidos.append(h.to_dict())

    if (
        not es_arranca_y_se_apaga
        and PATRON_NO_ARRANCA.search(texto_normalizado.lower())
        and not es_no_arranca_componente
        and not estado.obtener_hecho("sintoma_motor_no_arranca")
    ):
        h = estado.registrar_hecho("sintoma_motor_no_arranca", "motor no arranca", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
        hechos_extraidos.append(h.to_dict())

    if PATRON_DEMORA_ARRANQUE.search(texto_usuario):
        h = estado.registrar_hecho("sintoma_demora_arranque", "demora en arrancar", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
        hechos_extraidos.append(h.to_dict())
        if not estado.obtener_hecho("condicion_operacion"):
            h_c = estado.registrar_hecho("condicion_operacion", "al dar arranque en frío", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_c.to_dict())

    # 8. Ubicación, velocidad y freno
    es_volante_motor = bool(
        re.search(r"\bvolante\s+(?:de\s+inercia|motor|bimasa)\b|\b(?:alabeo|rectific|disco|embrague|caja|remaches)\b.{0,35}\bvolante\b|\bvolante\b.{0,35}\b(?:alabeo|rectific|disco|embrague|caja|remaches|inercia)\b", texto_l)
    )
    if not es_volante_motor and re.search(r"\b(en\s+el\s+volante|en\s+el\s+tim[oó]n|en\s+la\s+direcci[oó]n|volante|tim[oó]n)\b", texto_l):
        h = estado.registrar_hecho("ubicacion_sintoma", "en el volante", categoria="ubicacion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
    if re.search(r"\b(en\s+el\s+pedal|pedal\s+de\s+freno)\b", texto_l):
        if re.search(r"\b(no\s+siento|casi\s+no|sin\s+vibraci[oó]n|no\s+vibra|apenas)\b", texto_l):
            h = estado.registrar_hecho("vibracion_pedal", "mínima o nula", categoria="polaridad", estado=FactState.AUSENTE_NEGADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())
    if re.search(r"\b(resto\s+del\s+veh[ií]culo|carrocer[ií]a|asiento|todo\s+el\s+carro|todo\s+el\s+veh[ií]culo)\b", texto_l):
        if re.search(r"\b(no\s+vibra|tampoco\s+vibra|sin\s+vibraci[oó]n|no\s+se\s+siente)\b", texto_l):
            h = estado.registrar_hecho("vibracion_carroceria", "ausente", categoria="polaridad", estado=FactState.AUSENTE_NEGADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

    if re.search(r"\b(a\s+(?:una\s+)?velocidad\s+media\s+o\s+alta|a\s+alta\s+velocidad|en\s+carretera\s+a\s+velocidad|a\s+cierta\s+velocidad|a\s+m[aá]s\s+de\s+\d+)\b", texto_l):
        h = estado.registrar_hecho("condicion_velocidad", "a velocidad media o alta", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if re.search(r"\b(sin\s+frenar\s+(?:no\s+siente|no\s+vibra|no\s+pasa)|al\s+no\s+frenar\s+no|si\s+no\s+freno\s+no)\b", texto_l):
        h = estado.registrar_hecho("falla_sin_frenar", "no vibra sin frenar", categoria="polaridad", estado=FactState.AUSENTE_NEGADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if re.search(r"\b(todav[ií]a\s+no\s+he\s+revisado\s+el\s+veh[ií]culo|a[uú]n\s+no\s+se\s+ha\s+revisado|no\s+he\s+revisado\s+nada)\b", texto_l):
        h = estado.registrar_hecho("inspeccion_vehiculo", "no revisado aún en taller", categoria="inspeccion_pendiente", estado=FactState.NO_REVISADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if re.search(r"\b(gira\s+(?:con\s+)?buena\s+velocidad|gira\s+r[aá]pido|gira\s+normal)\b", texto_l):
        h = estado.registrar_hecho("giro_motor", "gira rápido con buena velocidad", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if re.search(r"\b((?:cuando|al)\s+(?:piso|pisa|se\s+pisa)\s+el\s+(?:pedal\s+de\s+)?freno|pisar\s+el\s+(?:pedal\s+de\s+)?freno)\b", texto_l):
        h_pedal_freno = estado.registrar_hecho("condicion_operacion", "al pisar el pedal de freno", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_pedal_freno.to_dict())

    # 9. Estado operativo y contradicciones
    res_op = inferir_estado_operativo(estado, texto_usuario)
    nuevo_estado_op, es_conflicto = res_op[0], res_op[1]
    if nuevo_estado_op != EstadoOperativo.DESCONOCIDO or not any(c[0] == "estado_operativo" for c in corrs):
        estado.estado_operativo = nuevo_estado_op

    if nuevo_estado_op == EstadoOperativo.FRENADO and not estado.obtener_hecho("condicion_operacion"):
        h_freno = estado.registrar_hecho("condicion_operacion", "al frenar", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_freno.to_dict())

    if es_conflicto:
        h = estado.registrar_hecho("conflicto_operativo", "arranque_vs_marcha", categoria="conflicto", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    return hechos_extraidos
