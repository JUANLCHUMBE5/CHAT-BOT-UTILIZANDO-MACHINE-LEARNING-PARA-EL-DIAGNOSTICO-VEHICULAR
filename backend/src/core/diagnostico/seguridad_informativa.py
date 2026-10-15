"""Límite conservador para respuestas informativas, incluidos fallbacks y colas."""
from __future__ import annotations

import re
import unicodedata
from functools import wraps
from inspect import signature

# Dominios explícitos: no se deducen averías a partir de la marca del vehículo.
DOMINIOS = {
    "admisión y cuerpo de aceleración": r"cuerpo de aceleracion|mariposa|ralenti|marcha minima|reaprendizaje|sensor maf",
    "frenos": r"frenos?|pastillas?|caliper|purga|liquido de frenos|discos? de freno",
    "embrague": r"embrague|collarin|clutch|crapodina",
    "transmisión": r"caja de cambios|caja automatica|transmision|cvt|dsg",
    "refrigeración": r"radiador|termostato|caja termostatica|refrigeracion|refrigerante",
    "suspensión": r"suspension|rotulas?|bieletas?|amortiguadores?",
    "iluminación": r"focos?|luces|led|h4|faros?",
    "inyección diésel": r"common rail|diesel|inyectores?|scv|dpf",
    "encendido": r"bujias?|bobinas?|misfire|chispa",
    "alimentación gasolina": r"gasolina|gasohol|bomba de combustible",
}


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.casefold())
                   if unicodedata.category(c) != "Mn")


def dominios(texto):
    normalizado = normalizar(texto)
    return {nombre for nombre, patron in DOMINIOS.items()
            if re.search(r"\b(?:" + patron + r")\b", normalizado)}


def temas_consulta(texto):
    """Separa menciones de contexto de temas realmente solicitados."""
    resultado = {k: set() for k in ("solicitados", "negados", "citados", "historicos")}
    texto = normalizar(texto)

    def cita(match):
        prefijo = texto[max(0, match.start() - 80):match.start()]
        explicita = re.search(r"\b(?:explica|describe|como|procedimiento|informacion|sobre)\b", prefijo)
        contexto = re.search(r"\b(?:dijo|dice|respondio|antes|anterior|no|sin)\b", prefijo)
        if explicita and not contexto:
            return match.group(0)[1:-1]
        resultado["citados"].update(dominios(match.group(0)))
        return " "

    sin_citas = re.sub(r'"[^"\n]*"|«[^»]*»|“[^”]*”|\'[^\'\n]*\'', cita, texto)
    for clausula in re.split(r"[.;!?\n]|\b(?:pero|ahora|sino|en cambio|mejor)\b", sin_citas):
        for nombre, patron in DOMINIOS.items():
            for match in re.finditer(r"\b(?:" + patron + r")\b", clausula):
                antes = clausula[:match.start()]
                negado = re.search(
                    r"\b(?:no\s+(?:(?:me|nos|le|se)\s+)?(?:busco|busques|quiero|necesito|solicito|pido|trates|incluyas|muestres|"
                    r"hables|generes|des|expliques|es|son|sobre)|sin|excepto|excluye|excluir|evita)\b[^.;!?]*$", antes,
                )
                historico = re.search(r"\b(?:antes|anterior|previamente|hablamos|tratamos|historico)\b", antes)
                categoria = "negados" if negado else ("historicos" if historico else "solicitados")
                resultado[categoria].add(nombre)
    resultado["solicitados"] -= resultado["negados"]
    return resultado


def validar_respuesta_informativa(pregunta, respuesta):
    """No certifica pertinencia clínica: rechaza contradicciones explícitas y falla cerrada."""
    consulta = temas_consulta(pregunta)["solicitados"]
    salida = dominios(respuesta)
    texto = normalizar(respuesta)
    if not respuesta.strip() or not consulta or not salida or salida - consulta:
        raise ValueError("Contenido informativo sin pertinencia verificable")
    if re.search(r"diagnostico sugerido|certeza|falla confirmada|\d+\s*%", texto):
        raise ValueError("Una consulta informativa no autoriza un diagnóstico")
    if re.search(r"\d+(?:[.,]\d+)?\s*(?:psi|bar|kpa|nm|mm|rpm|v|°c)\b", texto):
        raise ValueError("Especificación sin fuente documental verificada")
    if re.search(r"(?:destap|abr|afloj|puent|desconect|regener)\w*.{0,65}"
                 r"(?:caliente|hirviendo|common rail|inyector|en marcha|aceite contaminado)", texto):
        raise ValueError("Instrucción informativa potencialmente peligrosa")
    return respuesta


def proteger_respuesta_informativa(pregunta, respuesta, metadatos):
    try:
        validar_respuesta_informativa(pregunta, respuesta)
        return respuesta, metadatos
    except ValueError as exc:
        tema = ", ".join(sorted(temas_consulta(pregunta)["solicitados"])) or "la consulta técnica"
        texto = (f"Sobre {tema}: no dispongo de información suficientemente verificada "
                 "para indicar ese procedimiento. Verifica el manual OEM aplicable a "
                 "marca, modelo, año y motor antes de intervenir. No se confirma ninguna falla.")
        return texto, {**metadatos, "usado": False, "modelo": None,
                       "modo": "consulta_tecnica_degradada", "motivo_degradado": str(exc)}


def proteger_ruta_informativa(funcion):
    contrato = signature(funcion)

    @wraps(funcion)
    def protegida(*args, **kwargs):
        parametros = contrato.bind(*args, **kwargs)
        parametros.apply_defaults()
        respuesta, meta = funcion(*args, **kwargs)
        if (parametros.arguments.get("tipo_consulta") == "consulta_tecnica"
                and meta.get("modo") != "consulta_tecnica_en_cola"):
            return proteger_respuesta_informativa(parametros.arguments["pregunta"], respuesta, meta)
        return respuesta, meta
    return protegida
