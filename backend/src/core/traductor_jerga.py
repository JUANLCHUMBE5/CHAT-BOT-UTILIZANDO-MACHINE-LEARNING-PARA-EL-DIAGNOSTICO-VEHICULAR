"""Normalización de jerga de taller de Perú y otros países de LATAM.

El objetivo no es diagnosticar mediante reemplazos, sino convertir nombres
regionales de piezas y síntomas a vocabulario técnico peruano que el pipeline
ML + RAG pueda interpretar de forma consistente.
"""

from __future__ import annotations

import re

# Variantes frecuentes de dictado/ASR y escritura informal. Son equivalencias
# automotrices cerradas: evitamos un corrector difuso general que pueda cambiar
# nombres de modelos, marcas o componentes válidos.
DICCIONARIO_VARIANTES_ENTRADA: tuple[tuple[str, str], ...] = (
    (
        r"\bhumo blanco\b[^.]{0,100}\b(?:consume|pierde)\s+(?:el\s+)?refrigerante\b",
        "vapor blanco consume refrigerante posible empaque de culata",
    ),
    (
        r"\b(?:pasta|grasa|color|parece)\s+(?:como\s+)?caf[eé]\s+con\s+leche\b|"
        r"\b(?:mayonesa|nata|crema)\s+(?:en\s+la\s+tapa|en\s+el\s+aceite|pegada)\b|"
        r"\baceite\s+(?:lechoso|emulsionado|blanquecino|con\s+agua)\b|"
        r"\bcaf[eé]\s+con\s+leche\b",
        "aceite de motor parece leche con cafe chocolatada se mezcla el agua con el aceite",
    ),
    (
        r"\bmangueras?\s+(?:[a-z]+\s+)*(?:duras?|infladas?|hinchadas?|como\s+piedra)\b|"
        r"\bburbujeo\s+(?:violento\s+)?(?:en\s+el\s+dep[oó]sito|en\s+el\s+radiador)\b|"
        r"\bburbujas\s+en\s+el\s+(?:dep[oó]sito|refrigerante|radiador)\b",
        "el radiador bota burbujas con el motor encendido y consume agua",
    ),
    (
        r"\bhumo\s+blanco\s+(?:espeso|denso)?\s*(?:y\s+)?dulce\b",
        "sale bastante humo blanco espeso por el tubo de escape bota vapor blanco",
    ),
    (
        r"\bp\s*0*300\b",
        "codigo p0300 de falla de encendido multiple misfire en cilindros, revisar bujias o bobinas",
    ),
    (r"\bg\s*[.\-]?\s*n\s*[.\-]?\s*[bv]\b|\b(?:gnb|gnev|genebe)\b", "gnv"),
    (r"\bg\s*[.\-]?\s*l\s*[.\-]?\s*[bp]\b|\b(?:glb|gelepe)\b", "glp"),
    (r"\bgas licuado(?: de petr[oó]leo)?\b|\b(?:autogas|propano)\b", "glp"),
    (r"\b(?:menjar|menejar|manegar)\b", "manejar"),
    (r"\bvibraci[oó]n(?:es)?\b", "vibracion"),
    (
        r"\b(?:se\s+)?(?:vuelve|pone|queda)\s+chanch[oa]\b|"
        r"\b(?:se\s+)?(?:chanchea|chanchaea|achancha|achanchea|chanchonea)\b",
        "pierde potencia y presenta tirones al acelerar",
    ),
)

# Las frases más específicas deben ir antes que las palabras individuales.
# No se incluyen equivalencias regionales ambiguas (por ejemplo, ``cardán`` no
# se transforma en ``palier``) porque podrían cambiar el sistema diagnosticado.
DICCIONARIO_JERGA_LATAM: tuple[tuple[str, str], ...] = (
    # Frenos: México, Chile, Centroamérica y Caribe -> término usado en Perú.
    (r"\b(?:galletas?|balatas?|fricciones?)\s+de\s+freno\b", "pastillas de freno"),
    (r"\b(?:balatas?|fricciones?)\b", "pastillas de freno"),
    (r"\bbandas?\s+de\s+freno\b", "zapatas de freno"),
    (r"\b(?:maestro|bomba maestra)\s+de\s+frenos?\b", "bomba principal de freno"),
    (r"\bflexible\s+de\s+freno\b", "manguera de freno"),
    (r"\bbooster\b", "servofreno"),
    # Embrague y transmisión.
    (r"\b(?:cloche|croche|clutch)\b", "embrague"),
    (r"\b(?:balero|ruleman|rulemán)\s+de\s+(?:clutch|embrague)\b", "rodamiento de embrague"),
    (r"\b(?:semi[ -]?eje|flecha)\b", "palier"),
    (r"\b(?:balero|ruleman|rulemán)\b", "rodamiento"),
    (r"\bslushbox\b", "caja automática"),
    # Arranque, carga y encendido.
    (r"\b(?:burro de arranque|motor de partida|starter|marcha)\b", "motor de arranque"),
    (r"\brelevador\b", "rele"),
    (r"\bbug[ií]a\b", "bujia"),
    # Motor, refrigeración y escape.
    (r"\b(?:banda|correa)\s+(?:de\s+)?(?:tiempo|distribucion|distribución)\b", "faja de distribucion"),
    (r"\b(?:banda|correa)\s+(?:serpentina|de accesorios?)\b", "faja de accesorios"),
    (r"\b(?:cabezote|cabeza del motor)\b", "culata"),
    (r"\b(?:empacadura|empaquetadura|guarnicion|guarnición)\s+de\s+(?:culata|cabeza)\b", "empaque de culata"),
    (r"\b(?:mofle|mufla|exosto)\b", "silenciador de escape"),
    (r"\b(?:anticongelante|coolant)\b", "refrigerante"),
    # Suspensión, dirección, ruedas y carrocería.
    (r"\b(?:shock|shock absorber)\b", "amortiguador"),
    (r"\b(?:bota|acordeon|acordeón)\s+(?:de\s+)?homocinetica\b", "fuelle de junta homocinetica"),
    (r"\b(?:cubierta|caucho|goma)\s+(?:del\s+)?(?:auto|carro|vehiculo|vehículo|rueda)\b", "llanta"),
    (r"\bneumatico\b", "llanta"),
    (r"\b(?:latoneria|latonería|hojalateria|hojalatería|desabolladura)\s+y\s+pintura\b", "planchado y pintura"),
    (r"\b(?:cajuela|baul|baúl)\b", "maletera"),
    (r"\bcofre\b", "capot"),
    (r"\b(?:volante de direccion|volante de dirección)\b", "timon"),
    (r"\b(?:elevavidrios|elevalunas|alzavidrios|alzacristales)\b", "elevador de vidrio"),
    (r"\b(?:plumillas|escobillas)\s+(?:del\s+)?limpiaparabrisas\b", "plumas de limpiaparabrisas"),
)


DICCIONARIO_JERGA_PERUANA: tuple[tuple[str, str], ...] = (
    (r"\bcaña\b", "vehiculo"),
    (r"\bcascabelea\b", "preignicion o falla de bujias por cascabeleo"),
    (r"\bcascabeleando\b", "preignicion o falla de bujias"),
    (r"\bcabecea\b", "vibracion e inestabilidad en el motor"),
    (r"\bse chupa\b", "pierde potencia y se aguanta al acelerar"),
    (r"\bse aguanta\b", "perdida de fuerza al acelerar"),
    (r"\bzapatea\b", "vibracion por desbalanceo o discos de freno alabeados"),
    (r"\bzapateo\b", "vibracion en freno o aceleracion"),
    (r"\bbota vapor\b", "sobrecalentamiento y expulsion de refrigerante"),
    (r"\b(?:taca\s*taca|traque\s*traque|clac\s*clac|cla\s*cla)\b", "chasquido clac clac en junta homocinetica o palier"),
    (r"\b(?:doblar|doblo|giro|girar|doblando|girando)\s+(?:en\s+u|todo\s+el\s+tim[oó]n|el\s+tim[oó]n\s+a\s+tope)\b", "girar el timon a tope en curva cerrada palier"),
    (r"\b(?:grasa\s+negra|grasa\s+botada|grasa\s+esparcida)\b", "fuga de grasa por fuelle roto de palier o junta homocinetica"),
    (r"\b(?:fuelle|guardapolvo)\s+(?:roto|rajado|abierto|picado)\b", "fuelle roto de junta homocinetica con perdida de grasa"),
    (r"\bpedal esponjoso\b", "pedal de freno esponjoso por aire o fuga hidraulica"),
    (r"\bpedal largo\b", "recorrido excesivo del pedal de freno"),
    (r"\bchillido de faja\b", "chillido de faja de accesorios"),
    (r"\bhumo garzo\b", "humo azul por consumo de aceite"),
    (r"\bhumo azul\b", "humo azul por consumo de aceite"),
    (r"\bhumo negro\b", "humo negro por mezcla rica o combustion incompleta"),
    (r"\bhumo blanco\b", "humo blanco o vapor por ingreso de refrigerante"),
    (r"\bplumas\b", "plumas de limpiaparabrisas"),
    (r"\bchapa\b", "cerradura de puerta"),
    (r"\bpestillo\b", "mecanismo de cierre de puerta"),
    (r"\ben minimo\b", "motor en ralenti sin acelerar"),
    (r"\bjalonea\b", "presenta tirones al circular o acelerar"),
    (r"\bgolpe en baches\b", "golpe de suspension al pasar baches"),
    (r"\bgolpe en buches\b", "golpe de suspension al pasar baches"),
    (r"\btrancazo seco\b", "golpe seco en suspension"),
    (r"\brasca el cambio\b", "dificultad o raspado al engranar cambios"),
)


def normalizar_jerga_peruana(texto: str) -> str:
    """Convierte jerga peruana y regional LATAM a términos técnicos peruanos."""
    if not texto:
        return ""

    texto_procesado = texto.lower()
    diccionarios = (
        DICCIONARIO_VARIANTES_ENTRADA
        + DICCIONARIO_JERGA_LATAM
        + DICCIONARIO_JERGA_PERUANA
    )
    for patron, reemplazo in diccionarios:
        texto_procesado = re.sub(patron, reemplazo, texto_procesado, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", texto_procesado).strip()


if __name__ == "__main__":
    prueba = "Mi caña usa balatas, cascabelea y el burro de arranque hace clic"
    print("Texto original:", prueba)
    print("Texto normalizado:", normalizar_jerga_peruana(prueba))
