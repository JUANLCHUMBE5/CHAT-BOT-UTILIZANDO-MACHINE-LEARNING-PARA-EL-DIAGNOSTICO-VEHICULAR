"""Diccionario automotriz extensible de sinónimos, jerga de taller y normalización contextual."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

# Mapeo de términos directos y piezas mecánicas a su forma canónica
EQUIVALENCIAS_TERMINOLOGICAS: List[Tuple[re.Pattern, str]] = [
    # Error ortográfico frecuente en mensajes de WhatsApp de taller.
    (re.compile(r"\binjector(es)?\b", re.IGNORECASE), r"inyector\1"),
    (re.compile(r"\brpoblemas?\b|\bporblemas?\b", re.IGNORECASE), "problemas"),
    (re.compile(r"\bvehciuelos?\b|\bvehiuclos?\b", re.IGNORECASE), "vehículo"),
    # Frenos
    (re.compile(r"\b(mordaza(s)?)\b", re.IGNORECASE), "cáliper"),
    (re.compile(r"\b(caliper(s)?)\b", re.IGNORECASE), "cáliper"),
    (re.compile(r"\b(pedal\s+(esponjoso|aguado|gomoso|fofo))\b", re.IGNORECASE), "pedal de freno esponjoso"),
    (re.compile(r"\b(pedal\s+(duro|de\s+piedra|como\s+palo))\b", re.IGNORECASE), "pedal de freno duro servofreno"),
    # Embrague
    (re.compile(r"\b(crapodina(s)?)\b", re.IGNORECASE), "collarín de embrague"),
    (re.compile(r"\b(collarin|collarín)\b", re.IGNORECASE), "collarín de embrague"),
    (re.compile(r"\b(embrague\s+patina|clutch\s+patina|disco\s+patina)\b", re.IGNORECASE), "embrague patinando"),
    (
        re.compile(
            r"\b(zapatea(?:\s+feo)?\s+al\s+arrancar(?:\s+en\s+primera)?|zapateo(\s+de\s+embrague)?|"
            r"trepidaci[oó]n\s+al\s+salir|al\s+arrancar\s+en\s+primera\s+zapatea)\b",
            re.IGNORECASE,
        ),
        "trepidación zapateo de embrague",
    ),
    (
        re.compile(
            r"\b(pedal\s+vibra\s+cuando\s+lo\s+suelto|vibra\s+al\s+soltar\s+el\s+pedal|"
            r"pedal\s+vibra\s+al\s+soltar)\b",
            re.IGNORECASE,
        ),
        "vibración en pedal de embrague",
    ),
    (
        re.compile(
            r"\b(?:revoluciones\s+suben|rpm\s+suben)\b.{0,40}\bno\s+avanza\b|"
            r"\bno\s+avanza\b.{0,40}\b(?:revoluciones\s+suben|rpm\s+suben)\b",
            re.IGNORECASE,
        ),
        "embrague patinando suben revoluciones no avanza",
    ),
    (
        re.compile(
            r"\bhuele\s+a\s+quemado\b.{0,30}\b(?:no\s+avanza|subida|cuesta)\b|"
            r"\b(?:no\s+avanza|subida|cuesta)\b.{0,30}\bhuele\s+a\s+quemado\b",
            re.IGNORECASE,
        ),
        "embrague patinando olor a quemado",
    ),
    # Rodamientos
    (re.compile(r"\b(rodaje(s)?|rodamientos?)\b", re.IGNORECASE), "rodamiento"),
    # Síntomas de motor
    (re.compile(r"\b(zapatea|tiembla|timebla|tiemlba|vibra)\b", re.IGNORECASE), "vibración"),
    (re.compile(r"\b(se\s+muere|se\s+apaga|se\s+me\s+apaga)\b", re.IGNORECASE), "apagado de motor"),
    (re.compile(r"\b(no\s+jala|esta\s+chancho|está\s+chancho|chanchea|se\s+aguanta|aguantado|se\s+queda|se\s+chupa|amarrado|pesado|(pierde|perd[ií][aáoó]|sin|falta\s+de)\s+fuerza|se\s+ahog(a|aba|ó|o)|no\s+(?:puedo\s+)?pasar\s+de\s+\d+)\b", re.IGNORECASE), "pérdida de potencia"),
    (re.compile(r"\b(ratea|cabecea|corcovea)\b", re.IGNORECASE), "funcionamiento irregular misfire"),
    (re.compile(r"\b(recalienta|recalentar|recalentando|recalent[oó]|se\s+recalienta|hierve|levanta\s+temperatura|calienta\s+demasiado|se\s+calienta|hirviendo|aguja\s+al\s+tope|bota\s+vapor)\b", re.IGNORECASE), "sobrecalentamiento"),
    (re.compile(r"\b(clac|clic|tac\s+seco|chasquido\s+seco)\b", re.IGNORECASE), "chasquido clac seco"),
    (re.compile(r"\b(humo\s+blanco\s+espeso|vapor\s+por\s+escape)\b", re.IGNORECASE), "humo blanco refrigerante"),
    (re.compile(r"\b(humo\s+negro|olor\s+a\s+nafta\s+cruda)\b", re.IGNORECASE), "humo negro exceso combustible"),
    (re.compile(r"\b(humo\s+azul(ado)?)\b", re.IGNORECASE), "humo azul consumo aceite"),
    (re.compile(r"\b(chicote|pedal\s+(?:qued[oó]|al)\s+fondo)\b", re.IGNORECASE), "embrague pedal al fondo chicote"),
    (re.compile(r"\b(acelerado|queda\s+acelerado|ralent[ií]\s+alto|chupa\s+aire|fuga\s+de\s+vac[ií]o)\b", re.IGNORECASE), "ralenti acelerado fuga vacio"),
]

# Patrones contextuales de condiciones de operación
PATRONES_CONDICION: List[Tuple[re.Pattern, str, str]] = [
    # (patrón, categoría, valor canónico)
    (
        re.compile(
            r"\b((al\s+girar(?!\s+la\s+llave|\s+el\s+motor|\s+el\s+arranque)|girando|cuando\s+giro|al\s+doblar|doblando|cuando\s+doblo)(\s+la\s+direcci[oó]n)?|en\s+curva|toda\s+la\s+direcci[oó]n)\b",
            re.IGNORECASE,
        ),
        "condicion_operacion",
        "al doblar la dirección",
    ),
    (
        re.compile(
            r"\b(al\s+frenar|cuando\s+freno|(al\s+pisar|pisando)(\s+el(\s+pedal)?(\s+de)?)?\s+freno)\b",
            re.IGNORECASE,
        ),
        "condicion_operacion",
        "al frenar",
    ),
    (
        re.compile(
            r"\b((?:en\s+el|al)\s+sem[aá]foro|sem[aá]foro\s+(?:en\s+)?rojo|luz\s+roja\s+del\s+sem[aá]foro|parado(\s+esperando)?|estando\s+parado|detenido|en\s+ralent[ií]|en\s+neutro)\b",
            re.IGNORECASE,
        ),
        "condicion_operacion",
        "detenido en ralentí",
    ),
    (
        re.compile(
            r"\b(al\s+acelerar|cuando\s+acelero|pisando\s+el\s+acelerador|en\s+subida|en\s+cuesta|bajo\s+carga|al\s+subir(\s+pendientes?)?|subiendo(\s+pendientes?)?|en\s+pendientes?)\b",
            re.IGNORECASE,
        ),
        "condicion_operacion",
        "al acelerar bajo carga",
    ),
    (
        re.compile(
            r"\b((?:en|por|al\s+pasar\s+por)\s+(?:pistas?\s+irregulares?|baches?|huecos?|trocha|calamina|empedrado|adoquines?)|terreno\s+irregular)\b",
            re.IGNORECASE,
        ),
        "condicion_operacion",
        "en pistas irregulares o baches",
    ),
    (
        re.compile(
            r"\b((?:a|cuando\s+va\s+a)\s+\d+\s*(?:km/h|kilometros|kmh|kph)?|a\s+alta\s+velocidad|(?:en|a\s+la)\s+carretera|a\s+(?:m[aá]s\s+de\s+)?(80|90|100|120)\s*(?:km/h)?|en\s+pista|en\s+viaje|en\s+ruta|circulando|en\s+marcha|andando|voy\s+a\s+\d+)\b",
            re.IGNORECASE,
        ),
        "condicion_operacion",
        "en carretera a velocidad",
    ),
]

# Patrones de temperatura
PATRONES_TEMPERATURA: List[Tuple[re.Pattern, str]] = [
    (
        re.compile(
            r"\b(en\s+fr[ií]o|primer\s+arranque|por\s+la\s+mañana|motor\s+fr[ií]o|^fr[ií]o$)\b",
            re.IGNORECASE,
        ),
        "frío",
    ),
    (
        re.compile(
            r"\b(en\s+caliente|despu[eé]s\s+de\s+calentar|ya\s+caliente|calent[oó]|calienta|calentar|"
            r"tras\s+andar|motor\s+caliente|cuando\s+(?:el\s+\w+\s+)?calienta|"
            r"al\s+calentar|(?:solo\s+)?pasa\s+caliente|^caliente$)\b",
            re.IGNORECASE,
        ),
        "caliente",
    ),
]

# Patrones de respuesta a acciones
PATRONES_EVOLUCION: List[Tuple[re.Pattern, str]] = [
    (
        re.compile(
            r"\b(mejora\s+al\s+acelerar|si\s+acelero\s+mejora|cuando\s+acelero\s+mejora|cuando\s+acelero\s+se\s+le\s+pasa|acelerando\s+empareja|al\s+acelerar\s+empareja|al\s+acelerar\s+mejora)\b",
            re.IGNORECASE,
        ),
        "mejora al acelerar",
    ),
    (
        re.compile(
            r"\b(mejora\s+al\s+(?:reducir|bajar|disminuir)\s+(?:la\s+)?velocidad|al\s+(?:reducir|bajar|disminuir)\s+(?:la\s+)?velocidad\s+mejora|si\s+(?:reduzco|bajo|disminuyo)\s+(?:la\s+)?velocidad\s+mejora)\b",
            re.IGNORECASE,
        ),
        "mejora al reducir velocidad",
    ),
    (
        re.compile(
            r"\b(si\s+acelero\s+empeora|al\s+acelerar\s+falla\s+m[aá]s|falla\s+m[aá]s\s+al\s+acelerar)\b",
            re.IGNORECASE,
        ),
        "empeora al acelerar",
    ),
    (
        re.compile(
            r"\b(casi\s+se\s+apaga|est[aá]\s+por\s+apagarse|amaga\s+con\s+apagarse)\b",
            re.IGNORECASE,
        ),
        "amenaza de apagado",
    ),
    (
        re.compile(
            r"\b(rpm\s+suben\s+y\s+bajan|aguja\s+oscila|revoluciones\s+inestables|suben\s+y\s+bajan\s+solas)\b",
            re.IGNORECASE,
        ),
        "oscilación de RPM",
    ),
]


def normalizar_jerga_automotriz(texto: str) -> str:
    """Aplica normalización conservando trazabilidad sin sustituciones ciegas peligrosas."""
    if not texto:
        return ""
    resultado = texto
    for patron, reemplazo in EQUIVALENCIAS_TERMINOLOGICAS:
        resultado = patron.sub(reemplazo, resultado)
    return resultado


def extraer_hechos_linguisticos(texto: str) -> Dict[str, Any]:
    """Extrae condiciones, temperaturas y evoluciones basadas en contexto."""
    hechos: Dict[str, Any] = {}
    if not texto:
        return hechos

    # 1. Condición de operación
    for patron, _, valor in PATRONES_CONDICION:
        m = patron.search(texto)
        if m:
            # Desacoplar si la condición está subordinada a una negación (ej. 'al frenar no vibra')
            resto = texto[m.end():]
            if re.match(r"^\s*,?\s*no\b", resto, re.IGNORECASE):
                continue
            if "al acelerar" in valor and re.search(r"\b(mejora|empareja|se\s+le\s+pasa)\b", texto, re.IGNORECASE):
                continue
            hechos["condicion_operacion"] = valor
            break

    # 2. Temperatura
    # Si la mención de frío es de funcionamiento normal ('arranca perfecto en frío') y la falla ocurre al calentar / andar:
    if re.search(r"\b(?:en\s+fr[ií]o\s+(?:arranca|prende|funciona|anda)\s+(?:perfecto|bien|normal)|en\s+fr[ií]o\s+no\s+(?:falla|pasa))\b", texto, re.IGNORECASE):
        if re.search(r"\b(calient[eé]|calent[oó]|calienta|despu[eé]s\s+de\s+\d+\s*min|a\s+los\s+\d+\s*min)\b", texto, re.IGNORECASE):
            hechos["temperatura"] = "caliente"
    if "temperatura" not in hechos:
        for patron, valor in PATRONES_TEMPERATURA:
            coincidencia = patron.search(texto)
            if not coincidencia:
                continue
            # Una condición de inspección (nivel revisado con motor frío,
            # medición con motor apagado) no redefine cuándo ocurre la falla.
            contexto_inspeccion = bool(re.search(
                r"\b(?:nivel|refrigerante|aceite|med[ií]|medici[oó]n|revis[eé]|comprob[eé]|"
                r"contacto\s+puesto|motor\s+apagado)\b",
                texto,
                re.IGNORECASE,
            ))
            contexto_falla = bool(re.search(
                r"\b(?:falla|ocurre|pasa|ratea|demora|arranca|se\s+apaga|pierde\s+potencia|ruido)\b",
                texto,
                re.IGNORECASE,
            ))
            if contexto_inspeccion and not contexto_falla:
                continue
            if coincidencia:
                hechos["temperatura"] = valor
                break

    # 3. Evolución o respuesta
    for patron, valor in PATRONES_EVOLUCION:
        if patron.search(texto):
            hechos["evolucion_accion"] = valor
            break

    # 4. Síntomas clave reportados
    for patron, valor in EQUIVALENCIAS_TERMINOLOGICAS:
        if valor.startswith(r"inyector") or "\\" in valor:
            continue
        if patron.search(texto):
            clave_s = f"sintoma_{valor.replace(' ', '_')}"
            hechos[clave_s] = valor

    return hechos
