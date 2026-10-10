"""Prioriza candidatos existentes sin inventar probabilidades ni piezas confirmadas."""

import re
import unicodedata

from src.core.diagnostico.taxonomia_sistemas import obtener_macro_sistema


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def priorizar_evidencia(texto, predicciones):
    """Conserva las puntuaciones originales y evita usar hallazgos negados."""
    txt = normalizar(texto)
    positivas = " ".join(
        frase for frase in re.split(r"[.;\n]|\bpero\b", txt)
        if not re.search(r"\b(no|sin|descartado|descartada)\b", frase)
    )
    motivo = ""
    compatibles = []
    # Una negación de caudal es evidencia positiva de una anomalía, no un descarte.
    if re.search(r"\b(?:inyectores|injectores)\b.{0,70}(?:no inyectan|caudal (?:bajo|insuficiente))", txt):
        compatibles = [p for p in predicciones if "inyector" in normalizar(p.falla)]
        motivo = "Caudal insuficiente reportado por el mecánico; método de comprobación pendiente."
    if re.search(r"\b(?:humo|vapor) blanco\b", positivas) and "refrigerante" in positivas:
        compatibles = [p for p in predicciones if re.search(r"culata|junta", normalizar(p.falla))]
        if compatibles:
            motivo = "Humo blanco y consumo de refrigerante: comprobar estanqueidad, sin confirmar culata."
    # Síntoma de acoplamiento + contexto de caja, no solo la letra R o D.
    caja = re.search(r"\b(automatic[oa]|transmision|caja|reversa|marcha atras)\b", positivas)
    acoplamiento = re.search(
        r"(?:demora|tarda|retardo).{0,60}(?:enganchar|acoplar|segundos)|"
        r"(?:entra|engancha|acopla).{0,20}(?:golpe|brusco)|no engrana", positivas,
    )
    if caja and acoplamiento and not re.search(r"se apaga|ralenti inestable|motor tironea", positivas):
        compatibles = [p for p in predicciones if obtener_macro_sistema(p.falla) == "TRANSMISION"]
        motivo = "Queja de acoplamiento de transmisión; componente exacto pendiente de comprobación."
    if re.search(
        r"\b(?:inyectores?|injectores?)\b.{0,65}\b(?:no\s+inyectan\s+(?:lo\s+)?suficiente|"
        r"inyectan\s+(?:poco|insuficiente)|caudal\s+(?:bajo|insuficiente))\b",
        txt,
    ):
        compatibles = [p for p in predicciones if re.search(r"inyector", normalizar(p.falla))]
        if compatibles:
            motivo = "Hallazgo reportado de caudal de inyectores priorizado para comprobación, no confirmado."
    # Hallazgo mecánico explícito, sin convertir una mera mención en confirmación.
    if re.search(r"\b(rotula|buje|bieleta)s?\b", positivas) and re.search(
        r"(?:encontre|detecte|observe|comprobe|med[ií]|en elevador).{0,100}(?:juego|holgura|rot[oa])|"
        r"(?:rotula|buje|bieleta).{0,25}(?:con juego|con holgura|rot[oa])", positivas,
    ):
        compatibles = [p for p in predicciones if re.search(r"buje|rotula|suspension", normalizar(p.falla))]
        motivo = "Hallazgo físico declarado en rótula/buje; priorizado sobre balanceo."
    if not compatibles:
        return predicciones, ""
    restantes = [p for p in predicciones if p not in compatibles]
    return compatibles + restantes, motivo


def bateria_ya_comprobada(texto):
    txt = normalizar(texto)
    return bool(
        re.search(r"cae a [678](?:[.,]\d+)?\s*v\b", txt)
        and re.search(r"con bateria (?:de apoyo|auxiliar).{0,20}arranca", txt)
        and not re.search(r"no arranca|sin bateria|no cae", txt)
    )


def documento_compatible(texto, titulo, contexto):
    """Descarta documentos incompatibles con transmisión o combustible declarados."""
    consulta = normalizar(texto)
    documento = normalizar(f"{titulo} {contexto}")
    automatico = bool(re.search(r"\b(automatic[oa]|cvt|dsg)\b", consulta))
    manual = bool(re.search(r"\b(?:caja|transmision) manual\b", consulta))
    doc_manual = bool(re.search(r"\b(?:caja de cambios|caja|transmision) (?:manual|mecanica)\b", documento))
    doc_auto = bool(re.search(r"\b(automatic[oa]|cvt|dsg)\b", documento))
    transmision_compatible = not (
        (automatico and doc_manual and not doc_auto)
        or (manual and doc_auto and not doc_manual)
    )

    documento_gas_dedicado = bool(
        re.search(
            r"\b(?:gnv|glp|quinta generacion|5ta generacion|reductor de gas|rampa de gas)\b",
            normalizar(titulo),
        )
    )
    combustible_declarado = bool(
        re.search(r"\b(?:gnv|glp|gasolina|diesel|di[eé]sel|gasohol)\b", consulta)
    )
    combustible_coincide = not documento_gas_dedicado or bool(
        combustible_declarado and re.search(r"\b(?:gnv|glp)\b", consulta)
    )
    return transmision_compatible and combustible_coincide


def preparar_contexto_rag_para_llm(contexto, titulo, metadatos, corpus_validado):
    """Solo entrega al LLM procedimientos OEM con validación documental y de taller."""
    meta = metadatos or {}
    auditoria = meta.get("auditoria") or {}
    estado = normalizar(str(meta.get("estado_validacion", ""))).replace(" ", "_")
    fuente = normalizar(str(meta.get("manual_oem", "")))
    fuente_generica = any(
        palabra in fuente
        for palabra in ("multimarca", "referencial", "universal", "estandar", "generico")
    )
    verificado = bool(
        corpus_validado
        and estado in {"validado_oem", "validado_oem_taller", "verificado_oem"}
        and auditoria.get("verificado_documental") is True
        and auditoria.get("auditoria_mecanica_formal_firmada") is True
        and fuente
        and not fuente_generica
    )
    if not contexto:
        return "", "Sin procedimiento RAG recuperado aplicable"
    if not verificado:
        return "", "Fuente RAG omitida: pendiente de validación OEM y de taller"
    return contexto, titulo


def limitar_respuesta(
    respuesta,
    predicciones,
    motivo="",
    sin_documento=False,
    contexto_verificado="",
    pregunta="",
):
    """La orientación inicial no publica especificaciones OEM sin verificación por vehículo.

    Se aplica también al fallback. El detalle técnico queda para una consulta
    identificada por vehículo; un texto RAG multimarca no acredita aplicabilidad.
    """
    unidades = r"(?<!\w)\d+(?:[.,]\d+)?\s*(?:nm|n·m|psi|bar|kpa|mm|rpm|°c|v|voltios|minutos)\b"
    cifras_respuesta = re.findall(unidades, respuesta or "", re.I)
    fuente_norm = normalizar(contexto_verificado or "")
    cifra_sin_respaldo = any(normalizar(cifra).replace(" ", "") not in fuente_norm.replace(" ", "") for cifra in cifras_respuesta)
    respuesta_norm = normalizar(respuesta or "")
    operacion_riesgosa = bool(
        re.search(
            r"desconect(?:a|e|ar|ando|e\w*)\s+(?:las?\s+)?(?:bobinas?|inyectores?).{0,80}"
            r"(?:ralenti|motor\s+en\s+marcha)|(?:ralenti|motor\s+en\s+marcha).{0,80}"
            r"desconect(?:a|e|ar|ando|e\w*)\s+(?:las?\s+)?(?:bobinas?|inyectores?)|"
            r"(?:rocia|roc[ií]a|aplica|usa).{0,70}(?:limpiador\s+de\s+(?:carburador|frenos)|"
            r"limpiador\s+de\s+contactos).{0,70}(?:motor\s+en\s+marcha|admision|cuerpo\s+de\s+aceleracion)|"
            r"(?:prueba|reaccion|enriquece).{0,100}limpiador\s+de\s+(?:carburador|frenos)",
            respuesta_norm,
        )
    )
    if (
        not sin_documento
        and not cifra_sin_respaldo
        and not operacion_riesgosa
        and len(respuesta) <= 1200
    ):
        return respuesta, False
    if not predicciones:
        return (
            "No tengo una hipótesis ML pertinente ni un procedimiento verificado suficiente para "
            "indicar valores o una prueba específica. Comparte el dato técnico que corresponda "
            "para orientar el siguiente paso sin adivinar ni desconectar componentes. "
            f"{_pregunta_aclaratoria_por_area(pregunta)}",
            True,
        )
    primera = predicciones[0].falla
    macro = obtener_macro_sistema(primera)
    prueba = {
        "TRANSMISION": "Comprueba el acoplamiento y el estado del fluido según el procedimiento del fabricante; no fuerces la marcha.",
        "SUSPENSION_CHASIS": "Confirma la holgura o daño mediante inspección física segura antes de cambiar componentes.",
        "FRENOS": "Comprueba físicamente el sistema de frenos; si el frenado es inseguro, no circules.",
        "ELECTRICO": "Comprueba alimentación, conexiones y caída de tensión antes de sustituir componentes.",
        "CLIMATIZACION": "Verifica la fuga y el funcionamiento del sistema con equipo adecuado antes de sustituir componentes.",
    }.get(macro, "Confirma la hipótesis mediante una prueba de taller antes de sustituir componentes.")
    presentables = predicciones
    if motivo.startswith("Queja de acoplamiento"):
        presentables = [p for p in predicciones if obtener_macro_sistema(p.falla) == "TRANSMISION"]
    opciones = "\n".join(f"{i}. {p.falla}" for i, p in enumerate(presentables[:3], 1))
    aviso = (
        "No hay procedimiento compatible verificado. "
        if sin_documento or cifra_sin_respaldo or operacion_riesgosa
        else ""
    )
    return (
        f"🔧 Hipótesis por comprobar:\n{opciones}\n\n{prueba}\n"
        f"{motivo}\n{aviso}Para especificaciones exactas necesito marca, modelo, año y motorización."
    ).strip(), True


def _pregunta_aclaratoria_por_area(pregunta):
    """Pide una sola evidencia útil, sin saltar a sistemas ajenos al síntoma."""
    from src.core.diagnostico.enrutador_sistema import detectar_areas_tecnicas

    areas = detectar_areas_tecnicas(pregunta or "")
    if "INYECCION_MEZCLA" in areas:
        return "¿Qué DTC aparece y qué valores STFT/LTFT o presión de combustible registraste?"
    if "ADMISION_MAP" in areas:
        return "¿Qué DTC aparece y qué valor de MAP/carga absoluta muestra el escáner, indicando unidad y condición de medición?"
    if "RALENTI" in areas:
        return "¿A cuántas RPM queda el motor y ocurre en frío, caliente o en ambas condiciones?"
    if "ENCENDIDO" in areas:
        return "¿Qué DTC aparece y en qué cilindro se presenta la falla, si el escáner lo identifica?"
    return "¿Qué código DTC aparece y qué lectura exacta del componente mostró el escáner?"
