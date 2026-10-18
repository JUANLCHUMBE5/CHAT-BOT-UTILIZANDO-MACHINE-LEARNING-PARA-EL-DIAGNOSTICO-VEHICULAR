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
    PATRON_AFIRMACION_VEHICULAR,
    PATRON_ANIO,
    PATRON_ANTECEDENTE_MARCHA,
    PATRON_ANTECEDENTE_VEHICULAR,
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
            marca_actual_como_antecedente = any(
                nombre.casefold() == estado.marca.casefold()
                and PATRON_ANTECEDENTE_VEHICULAR.search(texto_usuario[:start].rstrip(" ,;:"))
                for start, end, nombre in marcas_encontradas
            )
            nueva_marca_afirmada = any(
                nombre.casefold() == nueva_marca.casefold()
                and PATRON_AFIRMACION_VEHICULAR.search(texto_usuario[:start].rstrip(" ,;:"))
                for start, end, nombre in marcas_encontradas
            )
            es_correccion = bool(
                marca_actual_negada
                or marca_actual_como_antecedente
                or nueva_marca_afirmada
                or PATRON_CORRECCION_VEHICULO.search(texto_usuario)
            )
            es_cambio_explicito = bool(
                (re.search(r"\b(?:cambiar|cambio|otro|otra|nuevo|neuvo)\s+(?:de\s+)?(?:carro|auto|vehiculo|caso)\b", texto_usuario, re.IGNORECASE) if not re.search(r"\b(?:su|un|el|mi)?\s*otro\s+(?:auto|carro|vehiculo).{0,80}\b(?:pero|aunque|sin embargo|estamos|revisando|este)\b", texto_usuario, re.IGNORECASE) else False)
                or re.search(r"\b(?:ahora|ahora\s+es|este\s+es)\s+(?:un|una)\b", texto_usuario, re.IGNORECASE)
            )
            if es_correccion:
                estado.last_user_correction = "marca"
                estado.turno_ultima_correccion = estado.turno_actual
                marca_antigua = estado.marca
                if marca_antigua and hasattr(estado, "active_symptoms") and estado.active_symptoms:
                    estado.active_symptoms = [
                        re.sub(rf"\b(?:no\s+(?:es|era)\s+)?{marca_antigua}\b", nueva_marca, s, flags=re.IGNORECASE)
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
            elif es_cambio_explicito:
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
                "marca",
                nueva_marca,
                categoria="vehiculo",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h.to_dict())
            for start, end, nombre in marcas_encontradas:
                if nombre.casefold() != nueva_marca.casefold():
                    prefijo = texto_usuario[:start].rstrip(" ,;:")
                    ventana_pre = prefijo[-45:] if len(prefijo) > 45 else prefijo
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
    elif marca_actual_negada and not nueva_marca:
        estado.marca = None
        if "marca" in estado.hechos:
            del estado.hechos["marca"]
    else:
        for start, end, nombre in marcas_encontradas:
            if not estado.marca or nombre.casefold() != estado.marca.casefold():
                prefijo = texto_usuario[:start].rstrip(" ,;:")
                ventana_pre = prefijo[-45:] if len(prefijo) > 45 else prefijo
                sufijo = texto_usuario[end:].lstrip(" ,;:")
                ventana_post = sufijo[:60]
                if PATRON_ANTECEDENTE_VEHICULAR.search(ventana_pre) or PATRON_COMPARATIVO_POST.search(ventana_post):
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
        tiene_contexto_anio = not estado.anio or bool(re.search(rf"\b(?:a[ñn]o|del|modelo|es\s+[a-záéíóú0-9\s]*{nuevo_anio}|corrijo)\b", texto_usuario, re.IGNORECASE))
        if tiene_contexto_anio and (not estado.anio or estado.anio != nuevo_anio):
            anio_viejo = estado.anio
            if anio_viejo and hasattr(estado, "active_symptoms") and estado.active_symptoms:
                estado.active_symptoms = [
                    re.sub(rf"\b(?:no\s+(?:es|era)\s+)?{anio_viejo}\b", nuevo_anio, s, flags=re.IGNORECASE)
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
    if nuevo_mod:
        if estado.modelo and estado.modelo != nuevo_mod:
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

    # El motor es parte del perfil del vehículo y no debe depender de que el
    # código sea conocido por una tabla de modelos. Se exige contexto explícito
    # ("motor X") o la secuencia año + motorización + combustible.
    motor_match = re.search(
        r"\bmotor\s+([a-z0-9][a-z0-9.-]*(?:\s+(?:tsi|tdi|hdi|crdi|d-4d|turbo))?)\b",
        texto_usuario,
        re.IGNORECASE,
    )
    if not motor_match:
        motor_match = re.search(
            r"\b(?:19[89]\d|20[0-2]\d)\s+([1-9]\d?(?:[.,]\d)?(?:\s+(?:tsi|tdi|hdi|crdi|d-4d|turbo))?)"
            r"\s+(?:di[eé]sel|gasolina|glp|gnv)\b",
            texto_usuario,
            re.IGNORECASE,
        )
    if motor_match:
        nuevo_motor = motor_match.group(1).strip().upper().replace(",", ".")
        if nuevo_motor not in {"NO", "SE", "ESTA", "ESTÁ", "APAGADO", "ENCENDIDO"} and estado.motor != nuevo_motor:
            estado.motor = nuevo_motor
            h_motor = estado.registrar_hecho(
                "motor",
                nuevo_motor,
                categoria="vehiculo",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_motor.to_dict())
    if not motor_match:
        motor_despues_combustible = re.search(
            r"\b(?:di[eé]sel|gasolina|glp|gnv)\s+([1-9]\d?(?:[.,]\d)?(?:\s+(?:tsi|tdi|hdi|crdi|d-4d|turbo))?)\b",
            texto_usuario,
            re.IGNORECASE,
        )
        if motor_despues_combustible and not estado.motor:
            nuevo_motor = motor_despues_combustible.group(1).strip().upper().replace(",", ".")
            estado.motor = nuevo_motor
            h_motor = estado.registrar_hecho(
                "motor",
                nuevo_motor,
                categoria="vehiculo",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
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
    dtc_positivo = False
    for coincidencia_dtc in PATRON_DTC.finditer(texto_usuario):
        dtc_canonico = coincidencia_dtc.group(0).upper()
        campo = f"dtc_{dtc_canonico}"
        prefijo = texto_usuario[max(0, coincidencia_dtc.start() - 55):coincidencia_dtc.start()]
        negado = bool(re.search(
            r"(?:\bno\s+(?:tiene|hay|aparece|presenta|marca|reporta|registra)|\bsin)\b[^.;,]{0,35}$",
            prefijo,
            re.IGNORECASE,
        ))
        estado_dtc = FactState.AUSENTE_NEGADO if negado else FactState.CONFIRMADO
        dtc_positivo = dtc_positivo or not negado
        h = estado.registrar_hecho(
            campo,
            dtc_canonico,
            categoria="dtc",
            estado=estado_dtc,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())
    if dtc_positivo:
        estado.dtc_status = DtcStatus.DTC_OBSERVADO

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

    if re.search(r"\brodamientos?\b.{0,35}\b(?:no\s+tiene|sin)\b.{0,20}\b(?:ruido|holgura)\b", texto_l):
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
        hecho_existente = estado.obtener_hecho(campo_s)
        if hecho_existente and hecho_existente.estado == FactState.CONFIRMADO and estado_s == FactState.AUSENTE_NEGADO:
            if re.search(r"\b(?:en\s+el\s+pedal|resto\s+del\s+veh[ií]culo)\b", texto_usuario, re.IGNORECASE):
                continue
        h = estado.registrar_hecho(campo_s, val_s, categoria="sintoma", estado=estado_s, texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
        hechos_extraidos.append(h.to_dict())
        if estado_s == FactState.CONFIRMADO and hasattr(estado, "active_symptoms") and val_s not in estado.active_symptoms:
            estado.active_symptoms.append(val_s)

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

    def _clausula_de_match(txt: str, pos: int) -> Tuple[str, str]:
        cortes_ant = list(
            re.finditer(
                r"[.;?!]+|\b(?:pero|aunque|sin\s+embargo|sino|mas\s+bien)\b|,\s*(?:pero|aunque|sino)\b",
                txt[:pos],
            )
        )
        ini = cortes_ant[-1].end() if cortes_ant else 0
        m_sig = re.search(
            r"[.;?!]+|\b(?:pero|aunque|sin\s+embargo|sino|mas\s+bien)\b|,\s*(?:pero|aunque|sino)\b",
            txt[pos:],
        )
        fin = pos + m_sig.start() if m_sig else len(txt)
        return txt[ini:pos], txt[ini:fin]

    def _prefijo_negado(prefijo_clausula: str) -> bool:
        return bool(
            re.search(
                r"\b(?:no\s+(?:(?:se|le|me)\s+)?(?:(?:hay|tiene|presenta|sient[eo]|escuch[ao]|"
                r"oyen?|veo|not[ao]|percib[eo]|hace|existe|muestra|da|vibra|tiembla|suena)\b)?|"
                r"tampoco\s+(?:(?:hay|tiene|presenta|sient[eo]|escuch[ao]|veo|hace|vibra|tiembla|suena)\b)?|"
                r"sin\s+(?!frenar\b)|"
                r"ni\s+(?:(?:hay|tiene|presenta|sient[eo]|escuch[ao]|vibra|tiembla|suena)\b)?|"
                r"nunca\b|jam[aá]s\b|cero\b|descartad[oa]\b)",
                prefijo_clausula,
            )
        )

    # 8. Ubicación, velocidad y freno
    es_volante_motor = bool(
        re.search(r"\bvolante\s+(?:de\s+inercia|motor|bimasa)\b|\b(?:alabeo|rectific|disco|embrague|caja|remaches)\b.{0,35}\bvolante\b|\bvolante\b.{0,35}\b(?:alabeo|rectific|disco|embrague|caja|remaches|inercia)\b", texto_l)
    )
    m_volante = re.search(r"\b(en\s+el\s+volante|en\s+el\s+tim[oó]n|en\s+la\s+direcci[oó]n|volante|tim[oó]n)\b", texto_l)
    if not es_volante_motor and m_volante:
        pref_vol, _ = _clausula_de_match(texto_l, m_volante.start())
        if not _prefijo_negado(pref_vol):
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

    if re.search(r"\b(todav[ií]a\s+no\s+he\s+revisado\s+el\s+veh[ií]culo|a[ú]n\s+no\s+se\s+ha\s+revisado|no\s+he\s+revisado\s+nada)\b", texto_l):
        h = estado.registrar_hecho("inspeccion_vehiculo", "no revisado aún en taller", categoria="inspeccion_pendiente", estado=FactState.NO_REVISADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if re.search(r"\b(gira\s+(?:con\s+)?buena\s+velocidad|gira\s+r[aá]pido|gira\s+normal)\b", texto_l):
        h = estado.registrar_hecho("giro_motor", "gira rápido con buena velocidad", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if re.search(r"\b((?:cuando|al)\s+(?:piso|pisa|se\s+pisa)\s+el\s+(?:pedal\s+de\s+)?freno|pisar\s+el\s+(?:pedal\s+de\s+)?freno)\b", texto_l):
        h_pedal_freno = estado.registrar_hecho("condicion_operacion", "al frenar", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_pedal_freno.to_dict())

    # 9. Estado operativo y contradicciones
    res_op = inferir_estado_operativo(estado, texto_usuario)
    nuevo_estado_op, es_conflicto = res_op[0], res_op[1]
    if nuevo_estado_op != EstadoOperativo.DESCONOCIDO or not any(c[0] == "estado_operativo" for c in corrs):
        estado.estado_operativo = nuevo_estado_op

    if nuevo_estado_op == EstadoOperativo.FRENADO and not estado.obtener_hecho("condicion_operacion"):
        h_freno = estado.registrar_hecho("condicion_operacion", "al frenar", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h_freno.to_dict())

    # 10. Duración reportada, limitaciones y síntomas específicos
    m_dur = re.search(
        r"\b(?:el\s+problema\s+)?(?:empez[oó]|inici[oó]\s+)?hace\s+([a-záéíóú0-9]+\s+(?:d[ií]as?|semanas?|meses?|horas?))\b",
        texto_usuario,
        re.IGNORECASE,
    )
    if m_dur:
        val_dur = f"hace {m_dur.group(1)}"
        h_dur = estado.registrar_hecho("duracion_problema", val_dur, categoria="duracion", tipo=FactType.CONDICION, texto_crudo=texto_usuario)
        hechos_extraidos.append(h_dur.to_dict())

    from src.core.conversacion.gestor_plan_b import GestorPlanB
    herramientas_indisp = GestorPlanB.detectar_indisponibilidad_en_texto(texto_usuario)
    for her in herramientas_indisp:
        estado.bloquear_herramienta(her)
        if her not in estado.tools_unavailable:
            estado.tools_unavailable.append(her)
        h_her = estado.registrar_hecho(f"herramienta_{her}", f"{her} no disponible", categoria="herramienta", estado=FactState.AUSENTE_NEGADO, tipo=FactType.CONDICION, texto_crudo=texto_usuario)
        hechos_extraidos.append(h_her.to_dict())

    if re.search(r"\b(?:no|ni|tampoco)\s+(?:puedo|podemos)\s+desmontar\s+(?:las?\s+)?ruedas?\b", texto_usuario, re.IGNORECASE):
        estado.bloquear_prueba("desmontar_ruedas", "taller", "imposibilidad_fisica")
        h_desm = estado.registrar_hecho("limitacion_desmontar_ruedas", "no puede desmontar ruedas", categoria="limitacion", estado=FactState.AUSENTE_NEGADO, tipo=FactType.CONDICION, texto_crudo=texto_usuario)
        hechos_extraidos.append(h_desm.to_dict())

    m_ch = re.search(r"\bchirridos?\b.{0,35}\bruedas?\b|\bchirridos?\s+(?:en\s+(?:las?\s+)?ruedas?|al\s+frenar)\b", texto_l)
    if m_ch:
        pref_ch, cl_ch = _clausula_de_match(texto_l, m_ch.start())
        estado_ch = FactState.AUSENTE_NEGADO if _prefijo_negado(pref_ch) else FactState.CONFIRMADO
        if re.search(r"\bdelanter[oa]s?\b", cl_ch):
            val_ch = "chirrido en ruedas delanteras"
        elif re.search(r"\btraser[oa]s?\b", cl_ch):
            val_ch = "chirrido en ruedas traseras"
        elif re.search(r"\bruedas?\b", cl_ch):
            val_ch = "chirrido en ruedas"
        else:
            val_ch = "chirrido al frenar"
        h_ch = estado.registrar_hecho("sintoma_chirrido_ruedas", val_ch, categoria="sintoma", estado=estado_ch, tipo=FactType.SINTOMA, texto_crudo=texto_usuario)
        hechos_extraidos.append(h_ch.to_dict())
    m_vp = re.search(r"\bpedal\s+vibra\b|\bvibraci(?:[oó]n|ones)\s+(?:en\s+el\s+pedal|del\s+pedal)\b", texto_l)
    if m_vp:
        pref_vp, cl_vp = _clausula_de_match(texto_l, m_vp.start())
        estado_vp = FactState.AUSENTE_NEGADO if _prefijo_negado(pref_vp) or re.search(r"\bno\s+vibra\b", cl_vp) else FactState.CONFIRMADO
        if re.search(r"\b(?:fren|frenar|frenada)\b", cl_vp):
            val_pedal = "vibración en el pedal de freno"
        elif re.search(r"\b(?:embrague|clutch|soltar|suelto|primera|zapate|trepida)\b", cl_vp):
            val_pedal = "vibración en pedal de embrague"
        else:
            val_pedal = "vibración en el pedal"
        h_vp = estado.registrar_hecho("sintoma_vibracion_pedal", val_pedal, categoria="sintoma", estado=estado_vp, tipo=FactType.SINTOMA, texto_crudo=texto_usuario)
        hechos_extraidos.append(h_vp.to_dict())
    m_vv = re.search(r"\bvibraci(?:[oó]n|ones)\s+(?:en\s+el\s+volante|del\s+volante)\b|\bvolante\s+vibra\b|\bvibra\s+(?:el\s+)?volante\b", texto_l)
    if m_vv:
        pref_vv, cl_vv = _clausula_de_match(texto_l, m_vv.start())
        estado_vv = FactState.AUSENTE_NEGADO if _prefijo_negado(pref_vv) or re.search(r"\b(?:no|tampoco)\s+vibra\b", cl_vv) else FactState.CONFIRMADO
        h_vv = estado.registrar_hecho("sintoma_vibracion_volante", "vibración en el volante", categoria="sintoma", estado=estado_vv, tipo=FactType.SINTOMA, texto_crudo=texto_usuario)
        hechos_extraidos.append(h_vv.to_dict())
    m_gs = re.search(r"\bgolpe(?:s)?\s+met[aá]lico(?:s)?\b|\bgolpes?\s+en\s+(?:la\s+)?suspensi[oó]n\b|\bsonido\s+en\s+baches\b", texto_l)
    if m_gs:
        pref_gs, cl_gs = _clausula_de_match(texto_l, m_gs.start())
        estado_gs = FactState.AUSENTE_NEGADO if _prefijo_negado(pref_gs) else FactState.CONFIRMADO
        tiene_metalico = bool(re.search(r"\bmet[aá]lic[oa]s?\b", cl_gs))
        tiene_susp = bool(re.search(r"\bsuspensi[oó]n\b", cl_gs))
        ubic_susp = (
            " delantera"
            if re.search(r"\bdelanter[oa]s?\b", cl_gs)
            else (" trasera" if re.search(r"\btraser[oa]s?\b", cl_gs) else "")
        )
        if tiene_metalico and tiene_susp:
            val_gs = f"golpes metálicos en la suspensión{ubic_susp}"
        elif tiene_metalico:
            val_gs = f"golpes metálicos{ubic_susp}"
        elif tiene_susp:
            val_gs = f"golpes en la suspensión{ubic_susp}"
        else:
            val_gs = "sonido en baches"
        h_gs = estado.registrar_hecho("sintoma_golpes_suspension", val_gs, categoria="sintoma", estado=estado_gs, tipo=FactType.SINTOMA, texto_crudo=texto_usuario)
        hechos_extraidos.append(h_gs.to_dict())

    if re.search(r"\b(?:el\s+)?pedal\s+no\s+est[aá]\s+(?:muy\s+)?esponjoso\b|\bno\s+est[aá]\s+esponjoso\b", texto_l):
        h_ne = estado.registrar_hecho("sintoma_pedal_esponjoso", "pedal esponjoso", categoria="sintoma", estado=FactState.AUSENTE_NEGADO, tipo=FactType.SINTOMA, texto_crudo=texto_usuario)
        hechos_extraidos.append(h_ne.to_dict())
    if re.search(r"\b(?:no|ni)\s+(?:se\s+)?(?:va\s+al\s+fondo|hunde)\b", texto_l):
        h_nf = estado.registrar_hecho("sintoma_pedal_se_va_al_fondo", "pedal se va al fondo", categoria="sintoma", estado=FactState.AUSENTE_NEGADO, tipo=FactType.SINTOMA, texto_crudo=texto_usuario)
        hechos_extraidos.append(h_nf.to_dict())
    if re.search(r"\bno\s+he\s+comprobado\b.{0,30}\bdiscos?\b|\bno\s+(?:s[eé]|revis[eé]|comprob[eé]|he\s+revisado|he\s+visto)\b.{0,30}\bdiscos?\b", texto_l):
        h_disc = estado.registrar_hecho("inspeccion_discos_freno", "discos no comprobados", categoria="inspeccion_pendiente", estado=FactState.NO_REVISADO, tipo=FactType.CONDICION, texto_crudo=texto_usuario)
        hechos_extraidos.append(h_disc.to_dict())
    if re.search(r"\bno\s+presenta\s+problemas\s+de\s+frenos\b|\bsin\s+problemas\s+de\s+frenos\b", texto_l):
        h_np = estado.registrar_hecho("sintoma_problemas_frenos", "problemas de frenos", categoria="sintoma", estado=FactState.AUSENTE_NEGADO, tipo=FactType.SINTOMA, texto_crudo=texto_usuario)
        hechos_extraidos.append(h_np.to_dict())

    if es_conflicto:
        h = estado.registrar_hecho("conflicto_operativo", "arranque_vs_marcha", categoria="conflicto", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    return hechos_extraidos
