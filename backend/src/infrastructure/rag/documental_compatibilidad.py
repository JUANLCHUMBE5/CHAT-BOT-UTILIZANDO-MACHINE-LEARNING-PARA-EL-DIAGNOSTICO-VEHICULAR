"""Contrato único: documental compatibilidad de RAG-03G."""

from __future__ import annotations

import re
from typing import Any, Dict, Tuple

from .documental_tipos import VehiculoConsulta, normalizar_texto, parsear_rango_anios


def acreditar_aplicabilidad_exacta(vehiculo, candidato):
    """Desconocido no equivale a compatibilidad para una especificación exacta."""
    meta = candidato.get("metadatos") or {}
    dimensiones = (
        ("marca", "marca", "marcas_aplicables"),
        ("modelo", "modelo", "modelos_aplicables"),
        ("anio", "anio", "anios_aplicables"),
        ("motor", "motor", "motores_aplicables"),
        ("mercado", "mercado", "mercados_aplicables"),
    )
    for atributo, singular, plural in dimensiones:
        if not getattr(vehiculo, atributo, None):
            return False, f"Falta {atributo} del vehículo para acreditar cifra exacta"
        valor = candidato.get(plural) or candidato.get(singular) or meta.get(plural) or meta.get(singular)
        if not valor or any(
            w in normalizar_texto(str(valor)) for w in ("desconocido", "no identificado", "sin confirmar")
        ):
            return False, f"Falta aplicabilidad documental de {atributo}"
        if atributo == "anio" and not parsear_rango_anios(valor):
            return False, "Años documentales no verificables"
    compatible, motivo = verificar_compatibilidad_estructurada(vehiculo, candidato)
    if not compatible:
        return compatible, motivo
    # El helper de recuperación es permisivo con campos desconocidos. Una cifra
    # exige además coincidencia de modelo, código de motor y mercado explícitos.
    for atributo, campo in (
        ("modelo", "modelos_aplicables"),
        ("motor", "motores_aplicables"),
        ("mercado", "mercados_aplicables"),
    ):
        doc = normalizar_texto(
            str(candidato.get(campo) or candidato.get(atributo) or meta.get(campo) or meta.get(atributo))
        )
        q = normalizar_texto(str(getattr(vehiculo, atributo)))
        if any(w in doc for w in ("universal", "indiferente", "global")):
            continue
        if atributo == "mercado":
            grupos = {
                "usa_norteamerica": ("usa", "ee.uu", "norteamerica", "usdm", "hma"),
                "peru_latam": ("peru", "latam", "latinoamerica"),
                "japon": ("japon", "jdm"),
                "europa": ("europa", "ece"),
            }
            if any(w in doc for w in grupos.get(q, (q,))):
                continue
        elif re.search(rf"(?<!\w){re.escape(q)}(?!\w)", doc):
            continue
        return False, f"{atributo} no acreditado documentalmente"
    return True, "Cinco dimensiones explícitas y compatibles"


def verificar_compatibilidad_estructurada(
    vehiculo: VehiculoConsulta, candidato: Dict[str, Any]
) -> Tuple[bool, str]:
    """Evalúa la compatibilidad en 5 dimensiones técnicas (A03).

    Consume campos estructurados singulares y plurales provistos por Agente 2:
    - 'marca' / 'marcas_aplicables'
    - 'modelo' / 'modelos_aplicables'
    - 'anio' / 'anios_aplicables'
    - 'motores_aplicables'
    - 'mercados_aplicables'
    - 'alcance_aplicacion'

    Retorna: (es_compatible, motivo)
    """
    meta = candidato.get("metadatos", {}) or {}
    marca_doc = normalizar_texto(candidato.get("marca") or meta.get("make") or meta.get("marca") or "")
    marcas_plural = [
        normalizar_texto(m) for m in candidato.get("marcas_aplicables") or meta.get("marcas_aplicables") or []
    ]
    modelo_doc = normalizar_texto(candidato.get("modelo") or meta.get("model") or meta.get("modelo") or "")
    modelos_plural = [
        normalizar_texto(m)
        for m in candidato.get("modelos_aplicables") or meta.get("modelos_aplicables") or []
    ]
    motor_doc = normalizar_texto(
        candidato.get("motores_aplicables") or meta.get("motores_aplicables") or meta.get("motor") or ""
    )
    mercado_doc = normalizar_texto(
        candidato.get("mercados_aplicables") or meta.get("mercados_aplicables") or meta.get("mercado") or ""
    )
    alcance_doc = normalizar_texto(
        candidato.get("alcance_aplicacion") or meta.get("alcance_aplicacion") or ""
    )
    titulo_doc = normalizar_texto(candidato.get("titulo") or "")
    doc_completo = f"{titulo_doc} {' '.join(modelos_plural)} {alcance_doc} {modelo_doc} {normalizar_texto(candidato.get('documento') or candidato.get('texto') or '')}"
    es_universal_marca = (
        "universal" in marca_doc
        or "multimarca" in marca_doc
        or any(("universal" in m or "multimarca" in m for m in marcas_plural))
        or (candidato.get("vehicle_scope") == "UNIVERSAL")
        or (meta.get("vehicle_scope") == "UNIVERSAL")
    )
    if vehiculo.marca:
        v_marca = vehiculo.marca.lower()
        es_brembo_multimarca = "brembo" in marca_doc or any(("brembo" in m for m in marcas_plural))
        if not es_brembo_multimarca and (not es_universal_marca):
            coincide_marca = (
                v_marca in marca_doc
                or any((v_marca in m for m in marcas_plural))
                or (v_marca == "hyundai" and "hyundai" in marca_doc)
                or (v_marca == "kia" and "kia" in marca_doc)
            )
            if not coincide_marca:
                marcas_opuestas = [
                    "toyota",
                    "nissan",
                    "honda",
                    "suzuki",
                    "fiat",
                    "chevrolet",
                    "ford",
                    "volkswagen",
                ]
                for mo in marcas_opuestas:
                    if mo in marca_doc and v_marca != mo:
                        return (
                            False,
                            f"Marca incompatible: documento de {marca_doc} no aplica a vehículo {vehiculo.marca}",
                        )
                return (False, f"Marca consultada ({vehiculo.marca}) no amparada en documento ({marca_doc})")
    if vehiculo.modelo:
        v_modelo = vehiculo.modelo.lower()
        es_universal_modelo = es_universal_marca or any(
            (
                w in modelo_doc or any((w in m for m in modelos_plural))
                for w in (
                    "universal",
                    "turismos",
                    "general",
                    "todos los modelos",
                    "multimarca",
                    "estandar sae",
                )
            )
        )
        if not es_universal_modelo:
            coincide_modelo = v_modelo in modelo_doc or any((v_modelo in m for m in modelos_plural))
            if "no extrapolar" in alcance_doc:
                for frase_no in re.findall("no\\s+extrapolar\\s+a\\s+([^.]+)", alcance_doc):
                    if v_modelo in frase_no:
                        return (
                            False,
                            f"Modelo {vehiculo.modelo} excluido expresamente por alcance técnico del boletín",
                        )
            modelos_diferenciados = [
                ("tucson", ["elantra", "accent", "sonata", "i10", "i30"]),
                ("sportage", ["rio", "cerato", "forte", "optima", "picanto"]),
                ("hilux", ["yaris", "corolla", "raize"]),
            ]
            for mod_objetivo, mods_incompatibles in modelos_diferenciados:
                if v_modelo == mod_objetivo:
                    doc_tiene_incompatibles = any(
                        (
                            mi in modelo_doc or any((mi in m for m in modelos_plural))
                            for mi in mods_incompatibles
                        )
                    )
                    if doc_tiene_incompatibles and (not coincide_modelo):
                        return (
                            False,
                            f"Manual/boletín de turismos ligeros no aplica al modelo {vehiculo.modelo}",
                        )
            if not coincide_modelo and modelos_plural:
                return (
                    False,
                    f"Modelo {vehiculo.modelo} no figura en la lista autorizada ({', '.join(modelos_plural)})",
                )
    if vehiculo.anio:
        v_anio = vehiculo.anio
        rango_doc = parsear_rango_anios(
            candidato.get("anio")
            or meta.get("anio")
            or candidato.get("anios_aplicables")
            or meta.get("anios_aplicables")
        )
        if rango_doc:
            a_min, a_max = rango_doc
            if v_anio < a_min or v_anio > a_max:
                return (
                    False,
                    f"Año consultado ({v_anio}) fuera del rango oficial amparado ({a_min}-{a_max})",
                )
    if vehiculo.motor:
        v_motor = normalizar_texto(vehiculo.motor)
        es_universal_motor = any(
            (
                w in motor_doc
                for w in (
                    "universal",
                    "indiferente",
                    "todos",
                    "universal para los modelos",
                    "universal para modelos",
                )
            )
        )
        es_diesel_usuario = any((d in v_motor for d in ("diesel", "crdi", "d4fb", "tdi", "petrolero")))
        es_gasolina_usuario = any(
            (g in v_motor for g in ("gasolina", "nafta", "g4fc", "1nz", "2nz", "hr16de", "gdi"))
        )
        es_diesel_doc = any(
            (d in f"{motor_doc} {doc_completo}" for d in ("diesel", "crdi", "common rail", "d4fb"))
        )
        es_gasolina_doc = any(
            (g in f"{motor_doc} {doc_completo}" for g in ("gasolina", "spark ignition", "g4fc", "valvematic"))
        )
        if es_diesel_usuario:
            if (
                "norteamerica (hma)" in mercado_doc
                or "usdm" in mercado_doc
                or "hyundai motor america" in marca_doc
            ):
                return (
                    False,
                    f"Motor diésel ({vehiculo.motor}) incompatible con boletín de mercado Norteamérica (HMA)",
                )
            if es_gasolina_doc and (not es_diesel_doc):
                return (
                    False,
                    f"Motor diésel ({vehiculo.motor}) incompatible con documento exclusivo de motor a gasolina",
                )
        if es_gasolina_usuario and es_diesel_doc and (not es_gasolina_doc):
            return (
                False,
                f"Motor a gasolina ({vehiculo.motor}) incompatible con procedimiento exclusivo de sistema diésel",
            )
        if not es_universal_motor and motor_doc:
            tokens_motores_doc = set(re.findall("\\b[a-z0-9\\-]+\\b", motor_doc))
            if tokens_motores_doc and (
                not any((tm in v_motor or v_motor in tm for tm in tokens_motores_doc))
            ):
                return (
                    False,
                    f"Motor consultado ({vehiculo.motor}) no coincide con motorizaciones cubiertas ({motor_doc})",
                )
    if vehiculo.mercado:
        v_mercado = vehiculo.mercado.lower()
        es_universal_mercado = any(
            (w in mercado_doc for w in ("global", "aftermarket", "universal", "indiferente"))
        )
        if not es_universal_mercado:
            es_tsb_usdm = any(
                (
                    w in f"{marca_doc} {' '.join(marcas_plural)} {mercado_doc} {alcance_doc} {titulo_doc}"
                    for w in (
                        "hyundai motor america",
                        "kia motors america",
                        "norteamerica (hma)",
                        "usdm",
                        "nhtsa",
                    )
                )
            )
            if es_tsb_usdm:
                if v_mercado in ("peru_latam", "japon"):
                    return (
                        False,
                        f"Boletín técnico regional de mercado EE.UU. (HMA) no homologado formalmente para mercado {vehiculo.mercado}",
                    )
    return (True, "Compatibilidad vehicular estructurada satisfactoria")
