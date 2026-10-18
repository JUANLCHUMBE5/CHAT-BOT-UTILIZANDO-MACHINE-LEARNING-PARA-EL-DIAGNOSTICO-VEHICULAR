"""Contrato Documental Unificado para CarBot RAG-03 (RAG-03F).

Define los contratos tipados, la política de gobernanza documental y la validación
estructurada para los agentes 1, 2 y 3:
- C02: Prohibición absoluta de emitir cifras OEM verificadas o confianza ML positiva
  cuando corpus_validado=False.
- A02: Exigencia de correspondencia técnica estricta entre la magnitud solicitada
  y el componente documentado (no basta cualquier número con unidad).
- A03: Validación vehicular estructurada en 5 dimensiones (marca, modelo, año, motor, mercado).
- B-INT-02: Parser y validación de referencias de páginas complejas (enteros, rangos y listas).
- Interfaz estable para que el agente 3 conecte proteger_salida_conversacional e
  interceptar_o_autorizar_tolerancia.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

from src.infrastructure.rag.documental_compatibilidad import verificar_compatibilidad_estructurada
from src.infrastructure.rag.documental_tipos import (
    DictamenDocumental,
    EstadoDocumental,
    TrazabilidadDocumental,
    VehiculoConsulta,
    normalizar_texto,
    parsear_rango_anios,
    parsear_referencias_paginas,
)

UNIDADES_POR_MAGNITUD = {
    "TORQUE": ["n.m", "nm", "lb-ft", "lbft", "kgf.m", "kgfm", "n m"],
    "PRESION": ["bar", "psi", "kpa", "mpa"],
    "TOLERANCIA_LINEAL": ["mm", "micras", "micra", "µm", "um", "mils"],
    "TEMPERATURA": ["°c", "celsius", "grados c"],
    "ELECTRICA": ["v", "volts", "voltios", "mv", "ohmios", "ohms", "kohm", "mohm", "a", "amperios", "ma"],
}
PALABRAS_CLAVE_MAGNITUD = {
    "TORQUE": ["torque", "par", "apriete", "ajuste", "perno", "tuerca"],
    "PRESION": ["presion", "riel", "compresion", "bomba"],
    "TOLERANCIA_LINEAL": [
        "alabeo",
        "espesor",
        "descarte",
        "holgura",
        "salto",
        "juego",
        "luz",
        "carrera",
        "desgaste",
        "dtv",
        "variacion",
    ],
    "TEMPERATURA": ["temperatura", "apertura", "termostato", "calor", "sobrecalentamiento"],
    "ELECTRICA": [
        "resistencia",
        "voltaje",
        "tension",
        "corriente",
        "amperaje",
        "aislamiento",
        "fuga",
        "caida",
    ],
}


def detectar_magnitud_solicitada(consulta: str) -> Optional[str]:
    """Detecta qué magnitud física exacta solicita la consulta del usuario."""
    q_norm = normalizar_texto(consulta)
    if any((re.search(f"\\b{p}\\b", q_norm) for p in ["par de apriete", "torque", "apriete", "libras pie"])):
        return "TORQUE"
    if any((re.search(f"\\b{p}\\b", q_norm) for p in ["presion", "presion nominal", "psi", "bar"])):
        return "PRESION"
    if any(
        (
            re.search(f"\\b{p}\\b", q_norm)
            for p in [
                "alabeo",
                "alabeo maximo",
                "tolerancia",
                "espesor minimo",
                "min th",
                "descarte",
                "holgura",
                "juego axial",
                "salto axial",
                "dtv",
            ]
        )
    ):
        return "TOLERANCIA_LINEAL"
    if any((re.search(f"\\b{p}\\b", q_norm) for p in ["temperatura", "apertura del termostato", "grados"])):
        return "TEMPERATURA"
    if any(
        (
            re.search(f"\\b{p}\\b", q_norm)
            for p in ["resistencia", "voltaje", "amperaje", "caida de tension", "ohmios", "aislamiento"]
        )
    ):
        return "ELECTRICA"
    for mag, unidades in UNIDADES_POR_MAGNITUD.items():
        for u in unidades:
            if re.search(f"\\b{re.escape(u)}\\b", q_norm):
                return mag
    return None


def extraer_componente_consulta(consulta: str) -> Optional[str]:
    """Extrae el componente o subsistema objetivo de la consulta técnica."""
    q_norm = normalizar_texto(consulta)
    componentes = [
        (
            "frenos_disco",
            ["disco de freno", "discos de freno", "alabeo de disco", "rotor", "buje de rueda", "trepidacion"],
        ),
        (
            "frenos_pastilla",
            ["pastilla de freno", "pastillas de freno", "balata", "balatas", "descarte de pastilla"],
        ),
        (
            "direccion_mdps",
            ["columna de direccion", "mdps", "c-mdps", "acoplador flexible", "cremallera", "timon"],
        ),
        ("termostato", ["termostato", "apertura del termostato", "temperatura de apertura"]),
        ("volante_inercia", ["volante de inercia", "volante motor", "dmf", "bimasa", "salto axial"]),
        (
            "combustible_bomba",
            ["bomba de combustible", "riel de inyeccion", "presion de combustible", "aforador"],
        ),
        ("motor_culata", ["culata", "empaque de culata", "tapa de cilindros", "pernos de culata"]),
        ("electrico_alternador", ["alternador", "caida de tension", "carga del alternador", "bateria"]),
    ]
    for comp_id, terminos in componentes:
        if any((re.search(f"\\b{re.escape(t)}\\b", q_norm) for t in terminos)):
            return comp_id
    return None


def verificar_presencia_cifra_y_trazabilidad(
    consulta: str, candidato: Dict[str, Any]
) -> Tuple[bool, Optional[TrazabilidadDocumental], str]:
    """Verifica si el documento contiene la magnitud solicitada para el componente objetivo (A02).

    Exige correspondencia estricta:
    1. Fuente documental formal ('manual_oem', 'pdf_origen', 'archivo_fuente').
    2. Referencia de página válida (entero, lista o rango verificado mediante parsear_referencias_paginas).
    3. Correspondencia física entre la magnitud solicitada (ej. torque) y el valor numérico en el documento.
       No basta cualquier número con unidad si no corresponde a la magnitud o al componente consultado.

    Retorna: (tiene_especificacion_valida, trazabilidad, motivo)
    """
    meta = candidato.get("metadatos", {}) or {}
    fuente = str(
        candidato.get("manual_oem")
        or meta.get("manual_oem")
        or candidato.get("pdf_origen")
        or meta.get("pdf_origen")
        or candidato.get("archivo_fuente")
        or ""
    ).strip()
    fuente_norm = normalizar_texto(fuente)
    if (
        not fuente
        or any((g in fuente_norm for g in ("inventado", "desconocido", "sin_fuente")))
        or fuente_norm in ("none", "")
    ):
        return (False, None, "Documento sin fuente manual_oem identificada")
    from src.infrastructure.rag.trazas_cifras import seleccionar_cifra

    cifra, motivo = seleccionar_cifra(consulta, candidato, normalizar_texto, parsear_referencias_paginas)
    if cifra is None:
        return (False, None, motivo)
    _, paginas, pagina = parsear_referencias_paginas(cifra["pagina"])
    trazabilidad = TrazabilidadDocumental(
        fuente=fuente,
        pagina=pagina,
        paginas=paginas,
        componente=cifra["parametro"],
        parametro=cifra["parametro"],
        condicion=cifra["condicion"],
        cifra_encontrada=cifra["cifra"],
        unidad=cifra["unidad"],
        marca_aplicable=candidato.get("marca"),
        modelos_aplicables=candidato.get("modelos_aplicables") or [],
        rango_anios=parsear_rango_anios(candidato.get("anio")),
        mercado_aplicable=candidato.get("mercados_aplicables"),
    )
    return (True, trazabilidad, motivo)


def dictaminar_candidato_documental(
    consulta: str, candidato: Dict[str, Any], corpus_validado: bool = False, vehiculo_consulta: str = ""
) -> DictamenDocumental:
    """Dictamina el estado formal de un candidato antes de su uso o publicación (C02 / A02 / A03)."""
    v_struct = VehiculoConsulta.extraer(consulta, vehiculo_consulta)
    es_comp, motivo_comp = verificar_compatibilidad_estructurada(v_struct, candidato)
    if not es_comp:
        return DictamenDocumental(
            estado=EstadoDocumental.INFORMACION_PARCIAL,
            autorizado_publicar_cifra=False,
            confianza_ml_maxima=0.0,
            factor_relevancia=0.01,
            trazabilidad=None,
            motivo=f"Rechazado por incompatibilidad vehicular: {motivo_comp}",
        )
    if detectar_magnitud_solicitada(consulta):
        from src.infrastructure.rag.documental_compatibilidad import acreditar_aplicabilidad_exacta

        acreditado, motivo = acreditar_aplicabilidad_exacta(v_struct, candidato)
        if not acreditado:
            return DictamenDocumental(EstadoDocumental.INFORMACION_PARCIAL, False, 0.0, 0.01, None, motivo)
    tiene_cifra, traz, motivo_cifra = verificar_presencia_cifra_y_trazabilidad(consulta, candidato)
    if not tiene_cifra:
        es_exp = bool(candidato.get("es_experimental") or "RAG_EXP_" in str(candidato.get("doc_id", "")))
        return DictamenDocumental(
            estado=EstadoDocumental.PROCEDIMIENTO_ESPECIFICO_OEM
            if es_exp
            else EstadoDocumental.PROCEDIMIENTO_GENERAL,
            autorizado_publicar_cifra=False,
            confianza_ml_maxima=0.75 if es_exp else 0.5,
            factor_relevancia=1.0,
            trazabilidad=traz,
            motivo=f"Procedimiento cualitativo ({motivo_cifra})",
        )
    if not corpus_validado:
        return DictamenDocumental(
            estado=EstadoDocumental.INFORMACION_PARCIAL,
            autorizado_publicar_cifra=False,
            confianza_ml_maxima=0.0,
            factor_relevancia=0.85,
            trazabilidad=traz,
            motivo="Cifra identificada documentalmente pero retenida por política C02 (corpus_validado=False)",
        )
    return DictamenDocumental(
        estado=EstadoDocumental.ESPECIFICACION_DOCUMENTADA,
        autorizado_publicar_cifra=True,
        confianza_ml_maxima=0.99,
        factor_relevancia=1.05,
        trazabilidad=traz,
        motivo=f"Especificación autorizada: {motivo_cifra}",
    )


from src.infrastructure.rag.documental_salida import proteger_salida_conversacional


def interceptar_o_autorizar_tolerancia(
    consulta: str,
    vehiculo_str: str,
    respuesta_candidata: str,
    corpus_validado: bool = False,
    especificacion_autorizada: bool = False,
) -> Tuple[str, float, str]:
    """Punto de conexión unificado y estable para el agente 3 (C1 / C02).

    Retorna: (texto_final, confianza_ml, decision_control)
    decision_control in ('AUTORIZADO', 'ABSTENCION_METROLOGICA', 'RESPUESTA_GENERAL')
    """
    texto_seguro, conf, interceptada = proteger_salida_conversacional(
        respuesta_propuesta=respuesta_candidata,
        vehiculo_str=vehiculo_str,
        consulta_usuario=consulta,
        corpus_validado=corpus_validado,
        especificacion_autorizada=especificacion_autorizada,
    )
    if interceptada:
        return (texto_seguro, 0.0, "ABSTENCION_METROLOGICA")
    if corpus_validado and especificacion_autorizada:
        return (texto_seguro, conf, "AUTORIZADO")
    return (texto_seguro, conf, "RESPUESTA_GENERAL")


__all__ = [
    "DictamenDocumental",
    "EstadoDocumental",
    "TrazabilidadDocumental",
    "VehiculoConsulta",
    "detectar_magnitud_solicitada",
    "dictaminar_candidato_documental",
    "extraer_componente_consulta",
    "interceptar_o_autorizar_tolerancia",
    "normalizar_texto",
    "parsear_rango_anios",
    "parsear_referencias_paginas",
    "proteger_salida_conversacional",
    "verificar_compatibilidad_estructurada",
    "verificar_presencia_cifra_y_trazabilidad",
]
