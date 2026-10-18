# -*- coding: utf-8 -*-
"""
Módulo de Control y Tipificación de Especificaciones Técnicas CarBot RAG-03E / RAG-03C.2 / RAG-03F.

Implementa la política documental unificada y gobernanza metrológica CarBot:
- C02: Política documental única; prohibición de publicar especificaciones OEM verificadas si corpus_validado=False.
- A02: Prohibición de clasificar como especificación verificada sin correspondencia técnica
       entre la magnitud solicitada, componente documentado, cifra real y trazabilidad formal.
- A03: Validación de compatibilidad estructurada en 5 dimensiones (marca, modelo, año, motor, mercado).
- B-INT-01 / B-INT-02: Interoperabilidad con agentes 2 y 3 mediante parseo de referencias de páginas complejas
       y protección conversacional de cotas metrológicas.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from src.infrastructure.rag.contrato_documental import (
    DictamenDocumental,
    EstadoDocumental,
    TrazabilidadDocumental,
    VehiculoConsulta,
    normalizar_texto,
    parsear_referencias_paginas,
    verificar_compatibilidad_estructurada,
    verificar_presencia_cifra_y_trazabilidad,
)


def normalizar(texto: str) -> str:
    """Normaliza texto eliminando diacríticos y caracteres especiales."""
    return normalizar_texto(texto)


PATRONES_SOLICITUD_EXACTA = [
    r"\b(?:cual|que|cuanto|cuanta)\s+(?:es\s+)?(?:el\s+|la\s+)?(?:par|torque|apriete|tolerancia|presion|alabeo|holgura|resistencia|voltaje|amperaje|luz|carrera|gap|especificacion|cota|medida|espesor|limite)\b",
    r"\b(?:par\s+de\s+apriete|torque|tolerancia\s+maxima|tolerancia\s+oem|alabeo\s+maximo|presion\s+nominal|min\s+th|espesor\s+minimo|dtv|caida\s+de\s+tension|salto\s+axial)\b",
    r"\b(?:cuantos|cuantas)\s+(?:nm|n\.m|lb-?ft|bar|psi|mm|micras?|volts?|v|ohmios?|°c)\b",
    r"\b(?:valor\s+nominal|cota\s+oem|especificacion\s+del\s+fabricante)\b",
]

COMPONENTES_SISTEMAS = {
    "frenos_disco": [
        "disco de freno ventilado",
        "disco de freno",
        "disco",
        "rotor de freno",
        "rotor",
        "alabeo de disco",
        "dtv",
        "variacion de espesor de disco",
    ],
    "frenos_pastilla": [
        "pastilla de freno",
        "pastillas de freno",
        "balata",
        "balatas",
        "descarte de pastilla",
    ],
    "frenos_tambor": [
        "tambor de freno",
        "cojinete del tambor",
        "tuerca central de tambor",
        "zapatas",
        "tambor",
    ],
    "direccion_mdps": [
        "columna de direccion",
        "mdps",
        "c-mdps",
        "acoplador flexible",
        "cremallera",
        "timon",
        "soporte de columna",
    ],
    "turbo": ["turbocompresor", "eje de turbina", "juego axial de turbo", "turbo"],
    "cigueñal": [
        "bancada de cigueñal",
        "damper",
        "polea de cigueñal",
        "plato flexible",
        "volante de inercia",
        "cigueñal",
    ],
    "arbol_levas": [
        "arbol de levas",
        "valvula vvt-i",
        "actuador valvematic",
        "valvematic",
        "levas",
        "engranaje variador",
    ],
    "embrague": ["volante bimasa", "plato de embrague", "disco de embrague", "dmf", "embrague", "clutch"],
    "suspension": [
        "rotula inferior",
        "portamangueta",
        "amortiguador",
        "copela",
        "torreta",
        "trapecio",
        "caster",
        "camber",
    ],
    "refrigeracion_quimica": [
        "reactivo bromotimol",
        "bromotimol",
        "comprobador de culata",
        "bloque quimico",
        "camara del comprobador",
    ],
    "refrigeracion_termostato": [
        "termostato mecanico",
        "termostato",
        "carrera de apertura",
        "valvula termostatica",
        "temperatura de apertura",
    ],
    "refrigeracion_mecanica": ["bomba de agua", "tapa del radiador", "electroventilador", "termostato"],
    "combustible_gas": [
        "reductor tomasetto",
        "reductor de gas",
        "vaporizador",
        "variador de avance",
        "rampa de gas",
        "glp",
        "gnv",
    ],
    "combustible_bomba": [
        "bomba de combustible",
        "riel de inyeccion",
        "presion de combustible",
        "aforador",
        "linea de baja",
    ],
    "motor_culata": ["culata", "empaque de culata", "tapa de cilindros", "pernos de culata"],
    "encendido": [
        "luz de electrodos",
        "galgado de bujias",
        "bobina de encendido",
        "bujia",
        "bujias",
        "bobina",
    ],
}


def detectar_tipo_consulta(consulta: str) -> str:
    """Clasifica la intención de la consulta en ESPECIFICACION_EXACTA, PROCEDIMIENTO_TECNICO o CONSULTA_GENERAL."""
    q_norm = normalizar(consulta)
    for pat in PATRONES_SOLICITUD_EXACTA:
        if re.search(pat, q_norm):
            return "ESPECIFICACION_EXACTA"
    if any(
        k in q_norm
        for k in [
            "como se mide",
            "como diagnosticar",
            "procedimiento",
            "pasos para",
            "como probar",
            "comprobar",
            "como calibrar",
            "como revisar",
            "metodo de",
        ]
    ):
        return "PROCEDIMIENTO_TECNICO"
    return "CONSULTA_GENERAL"


def extraer_componente_principal(texto: str) -> Optional[str]:
    """Identifica el componente automotriz principal en una consulta o documento priorizando términos compuestos."""
    t_norm = normalizar(texto)
    candidatos_comp: List[Tuple[int, str]] = []
    for comp, sinonimos in COMPONENTES_SISTEMAS.items():
        for s in sinonimos:
            if s in t_norm:
                candidatos_comp.append((len(s), comp))
    if candidatos_comp:
        candidatos_comp.sort(key=lambda x: x[0], reverse=True)
        return candidatos_comp[0][1]
    return None


def extraer_componentes_documento(titulo: str, texto: str) -> List[str]:
    """Extrae los componentes mencionados en el título y en el cuerpo del documento."""
    tit_norm = normalizar(titulo)
    doc_norm = normalizar(texto)
    comps = []
    for comp, sinonimos in COMPONENTES_SISTEMAS.items():
        for s in sinonimos:
            if s in tit_norm or s in doc_norm:
                if comp not in comps:
                    comps.append(comp)
                break
    return comps


def es_consulta_alta_tension(texto: str) -> bool:
    """Detecta si la consulta se refiere a alta tensión híbrida/eléctrica (300V-600V, aislamiento, HV)."""
    t = normalizar(texto)
    return bool(
        re.search(
            r"\b(?:alta\s+tension|alto\s+voltaje|aislamiento|fuga\s+de\s+alta\s+tension|inversor|bateria\s+hv|300v|600v)\b",
            t,
        )
    )


def es_documento_bajo_voltaje(texto: str) -> bool:
    """Detecta si el documento trata exclusivamente sobre bajo voltaje / 12V / batería auxiliar."""
    t = normalizar(texto)
    return bool(
        re.search(r"\b(?:bajo\s+voltaje|bateria\s+auxiliar\s+12v|12v|dc-dc)\b", t)
        and not re.search(r"\b(?:alta\s+tension|alto\s+voltaje|300v|megohmetro|aislamiento)\b", t)
    )


def clasificar_y_filtrar_oem(
    consulta: str,
    candidato: Dict[str, Any],
    vehiculo_consulta: str = "",
    sistema_consulta: str = "",
    corpus_validado: bool = False,
) -> Tuple[str, float, str]:
    """Evalúa la coincidencia semántica, técnica y metrológica del candidato frente a la consulta.

    Aplica rigurosamente:
    - C02: Prohibición de cifras OEM y falsa confianza ML si corpus_validado=False.
    - A02: Exigencia de correspondencia entre magnitud solicitada y componente documentado.
           Prohibición de clasificar como ESPECIFICACION_DOCUMENTADA / verificada sin
           cifra real, unidad, página y fuente documental.
    - A03: Compatibilidad estructurada en 5 dimensiones (marca, modelo, año, motor, mercado).
    - A07/A09: Unificación de política y desestimación de sobreajustes.

    Retorna: (categoria_clasificacion, factor_penalizacion, dictamen_seguridad)
    """
    q_norm = normalizar(consulta)
    meta = candidato.get("metadatos", {}) or {}
    tit_norm = normalizar(candidato.get("titulo", ""))
    doc_norm = normalizar(f"{tit_norm} {candidato.get('documento', '')} {candidato.get('texto', '')}")
    tipo_q = detectar_tipo_consulta(consulta)

    # 1. Extracción estructurada del vehículo de la consulta (A03)
    vehiculo_struct = VehiculoConsulta.extraer(consulta, vehiculo_consulta)

    # 2. Exclusión de dominio vehicular (maquinaria pesada, aeronáutica, marítimo, motos fuera de dominio)
    patron_excluyente = (
        r"\b(?:yamaha|scania|tesla|cessna|boeing|wabco|harley|john\s+deere|caterpillar|"
        r"vestas|spacex|motocicletas?|motos?|dron(?:es)?|agricola|retroexcavadoras?|"
        r"marino|fuera\s+de\s+borda|forklift|montacargas?|carretilla\s+elevadora|apilador|transpaleta)\b"
    )
    if re.search(patron_excluyente, q_norm) or re.search(patron_excluyente, normalizar(vehiculo_consulta)):
        return (
            EstadoDocumental.AUSENCIA_DOCUMENTACION.value,
            0.0001,
            "Bloqueado: Vehículo/maquinaria fuera del dominio automotriz ligero cubierto.",
        )

    # 3. Alta Tensión Híbrida frente a Bajo Voltaje 12V
    if es_consulta_alta_tension(consulta) and es_documento_bajo_voltaje(doc_norm):
        return (
            EstadoDocumental.INFORMACION_PARCIAL.value,
            0.01,
            "Bloqueado por seguridad: Solicitud de alta tensión híbrida no puede ser respondida con manual de bajo voltaje 12V.",
        )

    # 4. Compatibilidad Vehicular Estructurada en 5 dimensiones (A03)
    es_comp, razon_comp = verificar_compatibilidad_estructurada(vehiculo_struct, candidato)
    if not es_comp:
        if tipo_q == "ESPECIFICACION_EXACTA":
            return (
                EstadoDocumental.INFORMACION_PARCIAL.value,
                0.005,
                f"Bloqueado: {razon_comp}. Se prohíbe entregar especificación de vehículo incompatible.",
            )
        return (
            EstadoDocumental.INFORMACION_PARCIAL.value,
            0.01,
            f"Parcial: {razon_comp}.",
        )

    # 5. Componentes y Magnitudes en Solicitud de Cifra Exacta (A02)
    comp_q = extraer_componente_principal(consulta)
    comps_doc = extraer_componentes_documento(tit_norm, doc_norm[:400])
    tit_comp = extraer_componente_principal(tit_norm)

    if tipo_q == "ESPECIFICACION_EXACTA":
        # Magnitud o propiedad específica inexistente en documentación técnica
        unidades_propiedades_especificas = [
            "microamperios",
            "kelvin",
            "fuego directo",
            "ruptura",
            "milihenrios",
            "minutos y segundos",
            "polarizacion",
            "pintura",
            "antitermica",
            "estallido",
            "hectopascales",
            "gotas",
            "por cada litro",
            "concentricidad",
        ]
        for prop in unidades_propiedades_especificas:
            if prop in q_norm and prop not in doc_norm:
                return (
                    EstadoDocumental.AUSENCIA_DOCUMENTACION.value,
                    0.0005,
                    f"Bloqueado: La magnitud o condición consultada ({prop}) no existe en la documentación técnica.",
                )

        # Discrepancia entre pastilla y disco de freno
        if comp_q == "frenos_pastilla":
            if tit_comp and tit_comp != "frenos_pastilla":
                return (
                    EstadoDocumental.INFORMACION_PARCIAL.value,
                    0.0005,
                    "Bloqueado: Consulta de pastillas de freno incompatible con documento de disco/buje.",
                )
            if not re.search(
                r"\b(?:espesor\s+minimo|min\s+th|descarte)\b.{0,40}\b(?:pastilla|balata)\b", doc_norm
            ):
                return (
                    EstadoDocumental.INFORMACION_PARCIAL.value,
                    0.0005,
                    "Bloqueado: El documento no contiene la cota de descarte de pastillas de freno.",
                )

        # Consulta de par de apriete / torque en documento sin datos de apriete
        tiene_torque_doc = bool(re.search(r"\b(?:par\s+de\s+apriete|torque|n\.?m|lb-?ft)\b", doc_norm))
        if any(t in q_norm for t in ["par de apriete", "torque", "n.m", "lb-ft"]) and not tiene_torque_doc:
            return (
                EstadoDocumental.AUSENCIA_DOCUMENTACION.value,
                0.001,
                "Bloqueado: La consulta solicita par de apriete pero el documento no contiene especificaciones de torque.",
            )

        # Discrepancia directa de componentes
        if comp_q and tit_comp and comp_q != tit_comp and comp_q not in comps_doc:
            return (
                EstadoDocumental.INFORMACION_PARCIAL.value,
                0.0005,
                f"Bloqueado: Componente consultado ({comp_q}) difiere del documento ({tit_comp}). Se prohíbe cifra errónea.",
            )
        if comp_q and comp_q not in comps_doc and comp_q not in doc_norm:
            return (
                EstadoDocumental.AUSENCIA_DOCUMENTACION.value,
                0.001,
                f"Bloqueado: El documento no contiene información sobre ({comp_q}).",
            )

    # 6. Verificación de presencia de cifra, página y correspondencia metrológica formal (A02, B-INT-02)
    tiene_cifra_real, trazabilidad, motivo_cifra = verificar_presencia_cifra_y_trazabilidad(
        consulta, candidato
    )

    # 7. Documentos multimarca/turismos generales (ej. Brembo) frente a modelos específicos
    marca_candidato = normalizar(candidato.get("marca") or meta.get("make") or meta.get("marca") or "")
    if "brembo" in marca_candidato and vehiculo_struct.marca and vehiculo_struct.marca != "brembo":
        if "brembo" not in q_norm:
            if tipo_q == "ESPECIFICACION_EXACTA":
                return (
                    EstadoDocumental.INFORMACION_PARCIAL.value,
                    0.25,
                    f"Parcial: Guía multimarca de componentes Brembo referencial; no sustituye la ficha OEM oficial de {vehiculo_struct.marca}.",
                )

    # 8. Decisión documental según validez intrínseca (A02) y gobernanza de publicación (C02)
    es_exp = bool(
        candidato.get("es_experimental")
        or meta.get("es_experimental")
        or "RAG_EXP_" in str(candidato.get("doc_id", ""))
    )

    if tipo_q == "ESPECIFICACION_EXACTA":
        # Si NO tiene cifra numérica, unidad o fuente formal -> Jamás puede ser exacta verificada
        if not tiene_cifra_real:
            # Guía o procedimiento general que aporta orientación sin cota OEM exacta
            factor_parcial = 0.70 if not es_exp else 0.40
            return (
                EstadoDocumental.INFORMACION_PARCIAL.value,
                factor_parcial,
                f"Parcial: Guía de taller referencial sin especificación numérica OEM verificable ({motivo_cifra}).",
            )

        # Si tiene cifra real y trazabilidad:
        if corpus_validado:
            return (
                EstadoDocumental.ESPECIFICACION_DOCUMENTADA.value,
                1.05,
                "Aprobado: Especificación OEM verificada documentalmente.",
            )
        else:
            # C02: Con corpus_validado=False, se RETIENE ABSOLUTAMENTE la clasificación exacta
            # y se prohíbe la autorización de publicación metrológica
            return (
                EstadoDocumental.INFORMACION_PARCIAL.value,
                0.65,
                "Retenido: corpus_validado=False. Documento en corpus experimental no validado para producción.",
            )

    if es_exp:
        return (
            EstadoDocumental.PROCEDIMIENTO_ESPECIFICO_OEM.value,
            1.0,
            "Aprobado: Procedimiento específico de servicio.",
        )
    return (
        EstadoDocumental.PROCEDIMIENTO_GENERAL.value,
        1.0,
        "Aprobado: Procedimiento general de diagnóstico.",
    )


__all__ = [
    "DictamenDocumental",
    "EstadoDocumental",
    "TrazabilidadDocumental",
    "VehiculoConsulta",
    "clasificar_y_filtrar_oem",
    "detectar_tipo_consulta",
    "es_consulta_alta_tension",
    "es_documento_bajo_voltaje",
    "extraer_componente_principal",
    "extraer_componentes_documento",
    "normalizar",
    "normalizar_texto",
    "parsear_referencias_paginas",
    "verificar_compatibilidad_estructurada",
    "verificar_presencia_cifra_y_trazabilidad",
]
