"""Orquestador de extracción de hechos y actualización acumulativa de ConversationState."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from src.core.conversacion.diccionario_automotriz import (
    normalizar_jerga_automotriz,
)
from src.core.conversacion.extraccion_hechos.clasificador_mensajes import (
    inferir_estado_operativo,
)
from src.core.conversacion.extraccion_hechos.correcciones_y_descartes import (
    detectar_correcciones,
    registrar_rechazos_explicitos,
)
from src.core.conversacion.extraccion_hechos.extraccion_taller import extraer_comprobaciones_taller
from src.core.conversacion.extraccion_hechos.hechos_operativos import extraer_hechos_operativos
from src.core.conversacion.extraccion_hechos.patrones_hechos import (
    PATRON_DTC,
)
from src.core.conversacion.extraccion_hechos.perfil_vehicular import extraer_perfil_vehicular
from src.core.conversacion.models import ConversationState, DtcStatus, EstadoOperativo, FactState, FactType


def extraer_y_actualizar(estado: ConversationState, texto_usuario: str) -> List[Dict[str, Any]]:
    """Procesa el mensaje del usuario y actualiza el ConversationState acumulativo."""
    hechos_extraidos: List[Dict[str, Any]] = []
    texto_normalizado = normalizar_jerga_automotriz(texto_usuario)
    estado.historial_mensajes_usuario.append(texto_usuario)
    estado.turno_actual += 1
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
            est_f = (
                FactState.AUSENTE_NEGADO
                if cat == "polaridad" and nuevo_val == "ausente"
                else FactState.CONFIRMADO
            )
            h = estado.registrar_hecho(
                campo=campo,
                valor=nuevo_val,
                categoria=cat,
                estado=est_f,
                texto_crudo=texto_usuario,
                tipo=tipo_f,
            )
            hechos_extraidos.append(h.to_dict())
    extraer_perfil_vehicular(estado, texto_usuario, texto_normalizado, hechos_extraidos)
    dtc_positivo = False
    for coincidencia_dtc in PATRON_DTC.finditer(texto_usuario):
        dtc_canonico = coincidencia_dtc.group(0).upper()
        campo = f"dtc_{dtc_canonico}"
        prefijo = texto_usuario[max(0, coincidencia_dtc.start() - 55) : coincidencia_dtc.start()]
        negado = bool(
            re.search(
                "(?:\\bno\\s+(?:tiene|hay|aparece|presenta|marca|reporta|registra)|\\bsin)\\b[^.;,]{0,35}$",
                prefijo,
                re.IGNORECASE,
            )
        )
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
    hechos_extraidos.extend(extraer_comprobaciones_taller(estado, texto_usuario, texto_normalizado))
    hechos_extraidos.extend(registrar_rechazos_explicitos(estado, texto_usuario))
    m_cil = re.search("\\b(?:en\\s+el\\s+|del\\s+|de\\s+)?cilindro\\s*([1-8])\\b", texto_usuario.lower())
    if m_cil:
        num_cil = m_cil.group(1)
        h_cil = estado.registrar_hecho(
            "cilindro_afectado",
            f"cilindro {num_cil}",
            categoria="localizacion",
            estado=FactState.CONFIRMADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_cil.to_dict())
    texto_l = extraer_hechos_operativos(estado, texto_usuario, texto_normalizado, hechos_extraidos, corrs)

    def _clausula_de_match(txt: str, pos: int) -> Tuple[str, str]:
        cortes_ant = list(
            re.finditer(
                "[.;?!]+|\\b(?:pero|aunque|sin\\s+embargo|sino|mas\\s+bien)\\b|,\\s*(?:pero|aunque|sino)\\b",
                txt[:pos],
            )
        )
        ini = cortes_ant[-1].end() if cortes_ant else 0
        m_sig = re.search(
            "[.;?!]+|\\b(?:pero|aunque|sin\\s+embargo|sino|mas\\s+bien)\\b|,\\s*(?:pero|aunque|sino)\\b",
            txt[pos:],
        )
        fin = pos + m_sig.start() if m_sig else len(txt)
        return (txt[ini:pos], txt[ini:fin])

    def _prefijo_negado(prefijo_clausula: str) -> bool:
        return bool(
            re.search(
                "\\b(?:no\\s+(?:(?:se|le|me)\\s+)?(?:(?:hay|tiene|presenta|sient[eo]|escuch[ao]|oyen?|veo|not[ao]|percib[eo]|hace|existe|muestra|da|vibra|tiembla|suena)\\b)?|tampoco\\s+(?:(?:hay|tiene|presenta|sient[eo]|escuch[ao]|veo|hace|vibra|tiembla|suena)\\b)?|sin\\s+(?!frenar\\b)|ni\\s+(?:(?:hay|tiene|presenta|sient[eo]|escuch[ao]|vibra|tiembla|suena)\\b)?|nunca\\b|jam[aá]s\\b|cero\\b|descartad[oa]\\b)",
                prefijo_clausula,
            )
        )

    es_volante_motor = bool(
        re.search(
            "\\bvolante\\s+(?:de\\s+inercia|motor|bimasa)\\b|\\b(?:alabeo|rectific|disco|embrague|caja|remaches)\\b.{0,35}\\bvolante\\b|\\bvolante\\b.{0,35}\\b(?:alabeo|rectific|disco|embrague|caja|remaches|inercia)\\b",
            texto_l,
        )
    )
    m_volante = re.search(
        "\\b(en\\s+el\\s+volante|en\\s+el\\s+tim[oó]n|en\\s+la\\s+direcci[oó]n|volante|tim[oó]n)\\b", texto_l
    )
    if not es_volante_motor and m_volante:
        pref_vol, _ = _clausula_de_match(texto_l, m_volante.start())
        if not _prefijo_negado(pref_vol):
            h = estado.registrar_hecho(
                "ubicacion_sintoma",
                "en el volante",
                categoria="ubicacion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h.to_dict())
    if re.search("\\b(en\\s+el\\s+pedal|pedal\\s+de\\s+freno)\\b", texto_l):
        if re.search("\\b(no\\s+siento|casi\\s+no|sin\\s+vibraci[oó]n|no\\s+vibra|apenas)\\b", texto_l):
            h = estado.registrar_hecho(
                "vibracion_pedal",
                "mínima o nula",
                categoria="polaridad",
                estado=FactState.AUSENTE_NEGADO,
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h.to_dict())
    if re.search(
        "\\b(resto\\s+del\\s+veh[ií]culo|carrocer[ií]a|asiento|todo\\s+el\\s+carro|todo\\s+el\\s+veh[ií]culo)\\b",
        texto_l,
    ):
        if re.search("\\b(no\\s+vibra|tampoco\\s+vibra|sin\\s+vibraci[oó]n|no\\s+se\\s+siente)\\b", texto_l):
            h = estado.registrar_hecho(
                "vibracion_carroceria",
                "ausente",
                categoria="polaridad",
                estado=FactState.AUSENTE_NEGADO,
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h.to_dict())
    if re.search(
        "\\b(a\\s+(?:una\\s+)?velocidad\\s+media\\s+o\\s+alta|a\\s+alta\\s+velocidad|en\\s+carretera\\s+a\\s+velocidad|a\\s+cierta\\s+velocidad|a\\s+m[aá]s\\s+de\\s+\\d+)\\b",
        texto_l,
    ):
        h = estado.registrar_hecho(
            "condicion_velocidad",
            "a velocidad media o alta",
            categoria="condicion",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())
    if re.search(
        "\\b(sin\\s+frenar\\s+(?:no\\s+siente|no\\s+vibra|no\\s+pasa)|al\\s+no\\s+frenar\\s+no|si\\s+no\\s+freno\\s+no)\\b",
        texto_l,
    ):
        h = estado.registrar_hecho(
            "falla_sin_frenar",
            "no vibra sin frenar",
            categoria="polaridad",
            estado=FactState.AUSENTE_NEGADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())
    if re.search(
        "\\b(todav[ií]a\\s+no\\s+he\\s+revisado\\s+el\\s+veh[ií]culo|a[ú]n\\s+no\\s+se\\s+ha\\s+revisado|no\\s+he\\s+revisado\\s+nada)\\b",
        texto_l,
    ):
        h = estado.registrar_hecho(
            "inspeccion_vehiculo",
            "no revisado aún en taller",
            categoria="inspeccion_pendiente",
            estado=FactState.NO_REVISADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())
    if re.search("\\b(gira\\s+(?:con\\s+)?buena\\s+velocidad|gira\\s+r[aá]pido|gira\\s+normal)\\b", texto_l):
        h = estado.registrar_hecho(
            "giro_motor",
            "gira rápido con buena velocidad",
            categoria="condicion",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())
    if re.search(
        "\\b((?:cuando|al)\\s+(?:piso|pisa|se\\s+pisa)\\s+el\\s+(?:pedal\\s+de\\s+)?freno|pisar\\s+el\\s+(?:pedal\\s+de\\s+)?freno)\\b",
        texto_l,
    ):
        h_pedal_freno = estado.registrar_hecho(
            "condicion_operacion",
            "al frenar",
            categoria="condicion",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_pedal_freno.to_dict())
    res_op = inferir_estado_operativo(estado, texto_usuario)
    nuevo_estado_op, es_conflicto = (res_op[0], res_op[1])
    if nuevo_estado_op != EstadoOperativo.DESCONOCIDO or not any((c[0] == "estado_operativo" for c in corrs)):
        estado.estado_operativo = nuevo_estado_op
    if nuevo_estado_op == EstadoOperativo.FRENADO and (not estado.obtener_hecho("condicion_operacion")):
        h_freno = estado.registrar_hecho(
            "condicion_operacion",
            "al frenar",
            categoria="condicion",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_freno.to_dict())
    m_dur = re.search(
        "\\b(?:el\\s+problema\\s+)?(?:empez[oó]|inici[oó]\\s+)?hace\\s+([a-záéíóú0-9]+\\s+(?:d[ií]as?|semanas?|meses?|horas?))\\b",
        texto_usuario,
        re.IGNORECASE,
    )
    if m_dur:
        val_dur = f"hace {m_dur.group(1)}"
        h_dur = estado.registrar_hecho(
            "duracion_problema",
            val_dur,
            categoria="duracion",
            tipo=FactType.CONDICION,
            texto_crudo=texto_usuario,
        )
        hechos_extraidos.append(h_dur.to_dict())
    from src.core.conversacion.gestor_plan_b import GestorPlanB

    herramientas_indisp = GestorPlanB.detectar_indisponibilidad_en_texto(texto_usuario)
    for her in herramientas_indisp:
        estado.bloquear_herramienta(her)
        if her not in estado.tools_unavailable:
            estado.tools_unavailable.append(her)
        h_her = estado.registrar_hecho(
            f"herramienta_{her}",
            f"{her} no disponible",
            categoria="herramienta",
            estado=FactState.AUSENTE_NEGADO,
            tipo=FactType.CONDICION,
            texto_crudo=texto_usuario,
        )
        hechos_extraidos.append(h_her.to_dict())
    if re.search(
        "\\b(?:no|ni|tampoco)\\s+(?:puedo|podemos)\\s+desmontar\\s+(?:las?\\s+)?ruedas?\\b",
        texto_usuario,
        re.IGNORECASE,
    ):
        estado.bloquear_prueba("desmontar_ruedas", "taller", "imposibilidad_fisica")
        h_desm = estado.registrar_hecho(
            "limitacion_desmontar_ruedas",
            "no puede desmontar ruedas",
            categoria="limitacion",
            estado=FactState.AUSENTE_NEGADO,
            tipo=FactType.CONDICION,
            texto_crudo=texto_usuario,
        )
        hechos_extraidos.append(h_desm.to_dict())
    m_ch = re.search(
        "\\bchirridos?\\b.{0,35}\\bruedas?\\b|\\bchirridos?\\s+(?:en\\s+(?:las?\\s+)?ruedas?|al\\s+frenar)\\b",
        texto_l,
    )
    if m_ch:
        pref_ch, cl_ch = _clausula_de_match(texto_l, m_ch.start())
        estado_ch = FactState.AUSENTE_NEGADO if _prefijo_negado(pref_ch) else FactState.CONFIRMADO
        if re.search("\\bdelanter[oa]s?\\b", cl_ch):
            val_ch = "chirrido en ruedas delanteras"
        elif re.search("\\btraser[oa]s?\\b", cl_ch):
            val_ch = "chirrido en ruedas traseras"
        elif re.search("\\bruedas?\\b", cl_ch):
            val_ch = "chirrido en ruedas"
        else:
            val_ch = "chirrido al frenar"
        h_ch = estado.registrar_hecho(
            "sintoma_chirrido_ruedas",
            val_ch,
            categoria="sintoma",
            estado=estado_ch,
            tipo=FactType.SINTOMA,
            texto_crudo=texto_usuario,
        )
        hechos_extraidos.append(h_ch.to_dict())
    m_vp = re.search(
        "\\bpedal\\s+vibra\\b|\\bvibraci(?:[oó]n|ones)\\s+(?:en\\s+el\\s+pedal|del\\s+pedal)\\b", texto_l
    )
    if m_vp:
        pref_vp, cl_vp = _clausula_de_match(texto_l, m_vp.start())
        estado_vp = (
            FactState.AUSENTE_NEGADO
            if _prefijo_negado(pref_vp) or re.search("\\bno\\s+vibra\\b", cl_vp)
            else FactState.CONFIRMADO
        )
        if re.search("\\b(?:fren|frenar|frenada)\\b", cl_vp):
            val_pedal = "vibración en el pedal de freno"
        elif re.search("\\b(?:embrague|clutch|soltar|suelto|primera|zapate|trepida)\\b", cl_vp):
            val_pedal = "vibración en pedal de embrague"
        else:
            val_pedal = "vibración en el pedal"
        h_vp = estado.registrar_hecho(
            "sintoma_vibracion_pedal",
            val_pedal,
            categoria="sintoma",
            estado=estado_vp,
            tipo=FactType.SINTOMA,
            texto_crudo=texto_usuario,
        )
        hechos_extraidos.append(h_vp.to_dict())
    m_vv = re.search(
        "\\bvibraci(?:[oó]n|ones)\\s+(?:en\\s+el\\s+volante|del\\s+volante)\\b|\\bvolante\\s+vibra\\b|\\bvibra\\s+(?:el\\s+)?volante\\b",
        texto_l,
    )
    if m_vv:
        pref_vv, cl_vv = _clausula_de_match(texto_l, m_vv.start())
        estado_vv = (
            FactState.AUSENTE_NEGADO
            if _prefijo_negado(pref_vv) or re.search("\\b(?:no|tampoco)\\s+vibra\\b", cl_vv)
            else FactState.CONFIRMADO
        )
        h_vv = estado.registrar_hecho(
            "sintoma_vibracion_volante",
            "vibración en el volante",
            categoria="sintoma",
            estado=estado_vv,
            tipo=FactType.SINTOMA,
            texto_crudo=texto_usuario,
        )
        hechos_extraidos.append(h_vv.to_dict())
    m_gs = re.search(
        "\\bgolpe(?:s)?\\s+met[aá]lico(?:s)?\\b|\\bgolpes?\\s+en\\s+(?:la\\s+)?suspensi[oó]n\\b|\\bsonido\\s+en\\s+baches\\b",
        texto_l,
    )
    if m_gs:
        pref_gs, cl_gs = _clausula_de_match(texto_l, m_gs.start())
        estado_gs = FactState.AUSENTE_NEGADO if _prefijo_negado(pref_gs) else FactState.CONFIRMADO
        tiene_metalico = bool(re.search("\\bmet[aá]lic[oa]s?\\b", cl_gs))
        tiene_susp = bool(re.search("\\bsuspensi[oó]n\\b", cl_gs))
        ubic_susp = (
            " delantera"
            if re.search("\\bdelanter[oa]s?\\b", cl_gs)
            else " trasera"
            if re.search("\\btraser[oa]s?\\b", cl_gs)
            else ""
        )
        if tiene_metalico and tiene_susp:
            val_gs = f"golpes metálicos en la suspensión{ubic_susp}"
        elif tiene_metalico:
            val_gs = f"golpes metálicos{ubic_susp}"
        elif tiene_susp:
            val_gs = f"golpes en la suspensión{ubic_susp}"
        else:
            val_gs = "sonido en baches"
        h_gs = estado.registrar_hecho(
            "sintoma_golpes_suspension",
            val_gs,
            categoria="sintoma",
            estado=estado_gs,
            tipo=FactType.SINTOMA,
            texto_crudo=texto_usuario,
        )
        hechos_extraidos.append(h_gs.to_dict())
    if re.search(
        "\\b(?:el\\s+)?pedal\\s+no\\s+est[aá]\\s+(?:muy\\s+)?esponjoso\\b|\\bno\\s+est[aá]\\s+esponjoso\\b",
        texto_l,
    ):
        h_ne = estado.registrar_hecho(
            "sintoma_pedal_esponjoso",
            "pedal esponjoso",
            categoria="sintoma",
            estado=FactState.AUSENTE_NEGADO,
            tipo=FactType.SINTOMA,
            texto_crudo=texto_usuario,
        )
        hechos_extraidos.append(h_ne.to_dict())
    if re.search("\\b(?:no|ni)\\s+(?:se\\s+)?(?:va\\s+al\\s+fondo|hunde)\\b", texto_l):
        h_nf = estado.registrar_hecho(
            "sintoma_pedal_se_va_al_fondo",
            "pedal se va al fondo",
            categoria="sintoma",
            estado=FactState.AUSENTE_NEGADO,
            tipo=FactType.SINTOMA,
            texto_crudo=texto_usuario,
        )
        hechos_extraidos.append(h_nf.to_dict())
    if re.search(
        "\\bno\\s+he\\s+comprobado\\b.{0,30}\\bdiscos?\\b|\\bno\\s+(?:s[eé]|revis[eé]|comprob[eé]|he\\s+revisado|he\\s+visto)\\b.{0,30}\\bdiscos?\\b",
        texto_l,
    ):
        h_disc = estado.registrar_hecho(
            "inspeccion_discos_freno",
            "discos no comprobados",
            categoria="inspeccion_pendiente",
            estado=FactState.NO_REVISADO,
            tipo=FactType.CONDICION,
            texto_crudo=texto_usuario,
        )
        hechos_extraidos.append(h_disc.to_dict())
    if re.search(
        "\\bno\\s+presenta\\s+problemas\\s+de\\s+frenos\\b|\\bsin\\s+problemas\\s+de\\s+frenos\\b", texto_l
    ):
        h_np = estado.registrar_hecho(
            "sintoma_problemas_frenos",
            "problemas de frenos",
            categoria="sintoma",
            estado=FactState.AUSENTE_NEGADO,
            tipo=FactType.SINTOMA,
            texto_crudo=texto_usuario,
        )
        hechos_extraidos.append(h_np.to_dict())
    if es_conflicto:
        h = estado.registrar_hecho(
            "conflicto_operativo",
            "arranque_vs_marcha",
            categoria="conflicto",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())
    return hechos_extraidos
