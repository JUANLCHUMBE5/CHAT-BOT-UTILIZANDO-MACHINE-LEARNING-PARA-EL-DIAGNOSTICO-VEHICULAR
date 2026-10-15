"""Extracción de comprobaciones físicas, pruebas mecánicas y componentes descartados (Clean Architecture)."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from src.core.conversacion.evidencia_acciones import accion_afirmada
from src.core.conversacion.models import (
    ConversationState,
    FactState,
    FactType,
)


def extraer_comprobaciones_sistemas(estado: ConversationState, texto_usuario: str, texto_normalizado: str) -> List[Dict[str, Any]]:
    hechos_extraidos: List[Dict[str, Any]] = []
    texto_l = texto_usuario.lower()

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
        r"\bintercambi[ée]\b.{0,45}\brel[eé]\b.{0,60}\b(?:sigui[oó]|contin[uú]a|no\s+activ|sin\s+activ)",
        texto_l,
    ):
        h = estado.registrar_hecho(
            "rele_intercambiado_sin_resolver",
            "SI",
            categoria="resultado_prueba_cruzada",
            estado=FactState.CONFIRMADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
            procedencia="user_reported",
        )
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

    rotula_mencionada = re.search(
        r"\br[oó]tulas?\b.{0,35}\b(?:juego|desgaste|holgura|da[ñn]ada|axial|movimiento)\b|"
        r"\b(?:juego|holgura)\b.{0,35}\br[oó]tulas?\b",
        texto_l,
    )
    rotula_negada = bool(re.search(
        r"\br[oó]tulas?\b.{0,30}\b(?:no\s+tiene|sin)\b.{0,20}\b(?:juego|holgura|movimiento)\b",
        texto_l,
    ))
    if rotula_mencionada and rotula_negada:
        estado.eliminar_hecho("rotula_danada")
        h = estado.registrar_hecho(
            "rotula_descartada",
            "rótula sin juego con prueba física reportada",
            categoria="componente_descartado",
            estado=FactState.DESCARTADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h.to_dict())
    elif rotula_mencionada:
        m_mm_rot = re.search(r"\b(\d+(?:[.,]\d+)?)\s*mm\b", texto_l)
        val_rot = f"{m_mm_rot.group(1)} mm de holgura" if m_mm_rot else "SI"
        h = estado.registrar_hecho("rotula_danada", val_rot, categoria="comprobacion_fisica", estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if re.search(r"\bbieletas?\b.{0,35}\b(?:juego|holgura)\b|\b(?:juego|holgura)\b.{0,35}\bbieletas?\b", texto_l):
        h_bieleta = estado.registrar_hecho(
            "bieleta_con_juego",
            "bieleta con juego reportado en inspección física",
            categoria="comprobacion_fisica",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_bieleta.to_dict())
    if re.search(r"\b(?:cambi[eé]|reemplac[eé]|sustitu[ií])\b.{0,35}\bbieletas?\b", texto_l):
        h_bieleta = estado.registrar_hecho(
            "bieleta_reemplazada",
            "bieleta reemplazada por el mecánico",
            categoria="componente_reemplazado",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
        )
        hechos_extraidos.append(h_bieleta.to_dict())

    if re.search(r"\b(?:electro|moto)?ventilador\b", texto_l):
        if re.search(r"\b(?:baja|primera\s+velocidad)\b.{0,35}\b(?:no\s+entr[oó]|no\s+activ|no\s+funcion)", texto_l):
            h_vent = estado.registrar_hecho(
                "ventilador_baja_no_activa",
                "ventilador de baja no activa",
                categoria="comprobacion_fisica",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_vent.to_dict())

    comprobaciones_reportadas = (
        (
            "sin_burbujas_alimentacion",
            r"\b(?:no\s+(?:observ[eé]|veo)|sin)\b.{0,25}\bburbujas?\b.{0,45}\b(?:l[ií]nea|alimentaci[oó]n|combustible)\b",
            "sin burbujas visibles en alimentación",
        ),
        (
            "nivel_refrigerante_correcto",
            r"\b(?:refrigerante|coolant)\b.{0,45}\b(?:nivel\s+correcto|nivel\s+bien|al\s+nivel)\b",
            "nivel de refrigerante correcto reportado",
        ),
        (
            "sin_fugas_refrigerante",
            r"\b(?:no\s+(?:veo|hay)|sin)\b.{0,30}\bfugas?\s+externas?\b",
            "sin fugas externas visibles reportadas",
        ),
        (
            "bomba_agua_sin_juego_fuga",
            r"\bbomba\s+de\s+agua\b.{0,50}\b(?:no\s+tiene|sin)\b.{0,35}\b(?:juego|fuga)\b",
            "bomba de agua sin juego ni fuga reportada",
        ),
        (
            "bujias_inspeccion_uniforme",
            r"\bbuj[ií]as?\b.{0,55}\b(?:inspeccionad|color\s+uniforme|uniformes?)\b",
            "bujías inspeccionadas con aspecto uniforme reportado",
        ),
        (
            "nivel_combustible_suficiente",
            r"\b(?:tanque|combustible)\b.{0,45}\b(?:m[aá]s\s+de\s+medio|medio\s+tanque|por\s+encima\s+de\s+la\s+mitad)\b",
            "nivel de combustible superior a medio tanque reportado",
        ),
    )
    for campo, patron, valor in comprobaciones_reportadas:
        if re.search(patron, texto_l):
            h_comp = estado.registrar_hecho(
                campo,
                valor,
                categoria="comprobacion_fisica",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
                procedencia="user_reported",
            )
            hechos_extraidos.append(h_comp.to_dict())

    if re.search(r"\b(?:dos|2)\s+(?:problemas|fallas|aver[ií]as)\b.{0,45}\b(?:simult[aá]ne|mismo\s+tiempo)", texto_l):
        h_multi = estado.registrar_hecho(
            "averias_simultaneas_reportadas",
            "dos averías simultáneas en el mismo vehículo",
            categoria="alcance_caso",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
            procedencia="user_reported",
        )
        hechos_extraidos.append(h_multi.to_dict())

    if re.search(r"\bcausa\b.{0,35}\b(?:a[uú]n|todav[ií]a)\b.{0,20}\bno\s+(?:est[aá]\s+)?reparada\b", texto_l):
        h_pendiente = estado.registrar_hecho(
            "causa_contaminacion_pendiente",
            "causa de contaminación aún no reparada",
            categoria="inspeccion_pendiente",
            estado=FactState.NO_REVISADO,
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
            procedencia="user_reported",
        )
        hechos_extraidos.append(h_pendiente.to_dict())
        if re.search(r"\b(?:alta|segunda\s+velocidad)\b.{0,35}\b(?:s[ií]\s+)?(?:funciona|activa|entra)", texto_l):
            h_vent = estado.registrar_hecho(
                "ventilador_alta_funciona",
                "ventilador de alta funciona",
                categoria="comprobacion_fisica",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_vent.to_dict())

    if re.search(r"\b(?:no\s+es\s+la\s+bomba|bomba\s+manda\s+\d+\s*psi|bomba\s+descartada|descart[eé]\s+(?:la\s+)?bomba)\b", texto_l):
        h = estado.registrar_hecho("bomba_descartada", "DESCARTADO", categoria="componente_descartado", estado=FactState.DESCARTADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())
        if "bomba de combustible" not in estado.hipotesis_descartadas:
            estado.hipotesis_descartadas.append("bomba de combustible")

    if re.search(r"\b(?:candad(?:o|ito)|inmovilizador|transponder|b10da)\b", texto_l):
        h = estado.registrar_hecho("inmovilizador_confirmado", "SI", categoria="sistema", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
        hechos_extraidos.append(h.to_dict())

    if re.search(r"\b(?:wastegate|actuador|varilla)\b.{0,45}\b(?:mueve|libre|suave|ok)\b", texto_l):
        h = estado.registrar_hecho(
            "movimiento_wastegate_reportado",
            "movimiento manual de wastegate observado; actuador turbo no confirmado",
            categoria="comprobacion_fisica",
            texto_crudo=texto_usuario,
            tipo=FactType.CONDICION,
            procedencia="user_reported",
        )
        hechos_extraidos.append(h.to_dict())

    if accion_afirmada(texto_usuario, r"\b(?:revise|inspeccione|probe)\b", r"\bintercooler\b"):
        if re.search(r"\b(?:fuga|humo|aceite|uni[oó]n|manguera|sello)\b", texto_l):
            h_intercooler = estado.registrar_hecho(
                "inspeccion_intercooler_reportada",
                "intercooler y su unión inspeccionados por fuga reportada",
                categoria="comprobacion_fisica",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
                procedencia="user_reported",
            )
            hechos_extraidos.append(h_intercooler.to_dict())

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
