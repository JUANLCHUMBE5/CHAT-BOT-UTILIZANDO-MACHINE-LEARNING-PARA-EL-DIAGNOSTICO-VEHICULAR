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
    # Síntoma de acoplamiento + contexto de caja, no solo la letra R o D.
    caja = re.search(r"\b(automatic[oa]|transmision|caja|reversa|marcha atras)\b", positivas)
    acoplamiento = re.search(
        r"(?:demora|tarda|retardo).{0,60}(?:enganchar|acoplar|segundos)|"
        r"(?:entra|engancha|acopla).{0,20}(?:golpe|brusco)|no engrana", positivas,
    )
    if caja and acoplamiento and not re.search(r"se apaga|ralenti inestable|motor tironea", positivas):
        compatibles = [p for p in predicciones if obtener_macro_sistema(p.falla) == "TRANSMISION"]
        motivo = "Queja de acoplamiento de transmisión; componente exacto pendiente de comprobación."
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
    """Distingue transmisión manual/automática aunque compartan clase ML."""
    consulta = normalizar(texto)
    documento = normalizar(f"{titulo} {contexto}")
    automatico = bool(re.search(r"\b(automatic[oa]|cvt|dsg)\b", consulta))
    manual = bool(re.search(r"\b(?:caja|transmision) manual\b", consulta))
    doc_manual = bool(re.search(r"\b(?:caja de cambios|caja|transmision) (?:manual|mecanica)\b", documento))
    doc_auto = bool(re.search(r"\b(automatic[oa]|cvt|dsg)\b", documento))
    return not ((automatico and doc_manual and not doc_auto) or (manual and doc_auto and not doc_manual))


def limitar_respuesta(respuesta, predicciones, motivo="", sin_documento=False):
    """La orientación inicial no publica especificaciones OEM sin verificación por vehículo.

    Se aplica también al fallback. El detalle técnico queda para una consulta
    identificada por vehículo; un texto RAG multimarca no acredita aplicabilidad.
    """
    unidades = r"\b\d+(?:[.,]\d+)?\s*(?:nm|n·m|psi|bar|kpa|mm|rpm|°c|v|voltios|minutos)\b"
    if not sin_documento and len(respuesta) <= 1200 and not re.search(unidades, respuesta, re.I):
        return respuesta, False
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
    aviso = "No hay procedimiento compatible verificado. " if sin_documento else ""
    return (
        f"🔧 Hipótesis por comprobar:\n{opciones}\n\n{prueba}\n"
        f"{motivo}\n{aviso}Para especificaciones exactas necesito marca, modelo, año y motorización."
    ).strip(), True
