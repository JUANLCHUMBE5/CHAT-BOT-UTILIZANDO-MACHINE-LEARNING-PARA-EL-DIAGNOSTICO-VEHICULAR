"""Patrones regex y constantes de detección para extracción de hechos automotrices."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

PATRONES_REINICIO = [
    re.compile(
        r"^\s*(?:quiero\s+)?cancelar(?:(?:\s+el)?\s+(?:caso|diagn[oó]stico|consulta))?\s*[.!]?\s*$",
        re.IGNORECASE,
    ),
    re.compile(r"^\s*(?:nuevo|neuvo)\s*[.!]?\s*$", re.IGNORECASE),
    re.compile(r"\b(otro\s+(carro|auto|veh[ií]culo))\b", re.IGNORECASE),
    re.compile(r"\b((?:nuevo|neuvo)\s+diagn[oó]stico|(?:nuevo|neuvo)\s+caso)\b", re.IGNORECASE),
    re.compile(r"\b(reiniciar|empezar\s+de\s+nuevo|comenzar\s+de\s+nuevo)\b", re.IGNORECASE),
    re.compile(r"\b(limpiar\s+sesi[oó]n|caso\s+(?:nuevo|neuvo))\b", re.IGNORECASE),
    re.compile(
        r"\b(vamos\s+con\s+otro\s+cliente|termin[eé]\s+ese|tengo\s+uno\s+(?:nuevo|neuvo))\b", re.IGNORECASE
    ),
]

PATRON_NO_ARRANCA = re.compile(
    r"\b(no\s+(?:quiso|quiere|llega\s+a|pudo|vuelve\s+a)?\s*(?:arrancar|arranca|prender|prende|encender|enciende|da\s+arranque|partir|parte))\b(?!\s+(?:el\s+|la\s+)?(?:check|testigo|luz|luces|foco|tablero|ac|aire|radio))",
    re.IGNORECASE,
)
PATRON_GIRO_LLAVE = re.compile(
    r"\b((?:le\s+)?doy\s+(?:a\s+)?la\s+llave|al\s+girar\s+la\s+llave|giro\s+la\s+llave|doy\s+llave|al\s+dar\s+arranque|presiono\s+el\s+bot[oó]n|al\s+darle\s+(?:a\s+la\s+llave|arranque))\b",
    re.IGNORECASE,
)
PATRON_CLIC_UNICO = re.compile(
    r"\b(un\s+(?:solo\s+)?clic|clic\s+seco(,\s*una\s+sola\s+vez)?|un\s+solo\s+clac|clac\s+seco|un\s+chasquido\s+seco|un\s+solo\s+golpe\s+seco|hace\s+como\s+un\s+clic\s+seco)\b",
    re.IGNORECASE,
)
PATRON_CLICS_REPETIDOS = re.compile(
    r"\b(clac[\s-]+clac|clic[\s-]+clic|tac[\s-]+tac|metralleta|chasquidos?\s+repetidos?|clics?\s+r[aá]pidos?|rateo\s+de\s+arranque)\b",
    re.IGNORECASE,
)
PATRON_TABLERO_PRENDE = re.compile(
    r"\b((?:luces?\s+del\s+)?tablero\s+(?:s[ií]\s+)?(?:prenden?|encienden?|ilumina)|tablero\s+(?:s[ií]\s+)?(?:prende|enciende))\b",
    re.IGNORECASE,
)
PATRON_RADIO_PRENDE = re.compile(
    r"\b((?:la\s+)?radio\s+(?:tambi[eé]n\s+)?(?:prende|enciende|funciona|anda)|radio\s+tambi[eé]n)\b",
    re.IGNORECASE,
)
PATRON_LUCES_ATENUAN = re.compile(
    r"\b(luces?\s+(?:(?:del\s+)?tablero\s+)?(?:se\s+)?(?:aten[uú]an|bajan|apagan|caen|parpadean|se\s+ponen\s+tenues|tenues)|se\s+bajan\s+las\s+luces|se\s+aten[uú]an\s+las\s+luces|luces\s+se\s+van|se\s+(?:apagan|bajan|aten[uú]an)\s+(?:por\s+completo|totalmente|del\s+todo|mucho))\b",
    re.IGNORECASE,
)
PATRON_ANTECEDENTE_MARCHA = re.compile(
    r"\b(ven[ií]a\s+manejando|en\s+carretera|a\s+los\s+\d+\s+minutos\s+de\s+manejar|despu[eé]s\s+de\s+(?:manejar|andar|correr)|andando|iba\s+en\s+marcha|se\s+apag[oó]\s+(?:andando|en\s+marcha|corriendo))\b",
    re.IGNORECASE,
)
PATRON_DEMORA_ARRANQUE = re.compile(
    r"\b(demora\s+(?:(?:mucho|bastante|demasiado|(?:unos?\s+)?(?:\\d+|un|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\s+segundos?)\s+)?en\s+(?:arrancar|prender|encender)|"
    r"le\s+cuesta\s+(?:arrancar|prender|encender)|"
    r"tarda\s+(?:(?:mucho|bastante|demasiado)\s+)?en\s+(?:arrancar|prender|encender)|"
    r"da\s+marcha\s+(?:varios\s+segundos|un\s+rato)\s+antes\s+de\s+encender|"
    r"dificultad\s+(?:de|para|al)\s+arranc(?:ar|e)|"
    r"arranque\s+largo|le\s+cuesta\s+el\s+primer\s+arranque|"
    r"demora\s+por\s+las\s+mañanas|tarda\s+en\s+la\s+mañana|"
    r"en\s+las\s+mañanas\s+demora|demora\s+en\s+fr[ií]o)\b",
    re.IGNORECASE,
)

PATRONES_MARCA = [
    (re.compile(r"\b(toyota|toyoyta|toyta)\b", re.IGNORECASE), "Toyota"),
    (re.compile(r"\b(nissan|nisan)\b", re.IGNORECASE), "Nissan"),
    (re.compile(r"\b(hyundai|iundai|hyunday|hiundai)\b", re.IGNORECASE), "Hyundai"),
    (re.compile(r"\b(kia)\b", re.IGNORECASE), "Kia"),
    (re.compile(r"\b(chevrolet|chevy)\b", re.IGNORECASE), "Chevrolet"),
    (re.compile(r"\b(ford)\b", re.IGNORECASE), "Ford"),
    (re.compile(r"\b(honda)\b", re.IGNORECASE), "Honda"),
    (re.compile(r"\b(volkswagen|vw)\b", re.IGNORECASE), "Volkswagen"),
    (re.compile(r"\b(suzuki)\b", re.IGNORECASE), "Suzuki"),
    (re.compile(r"\b(mitsubishi)\b", re.IGNORECASE), "Mitsubishi"),
    (re.compile(r"\b(mazda)\b", re.IGNORECASE), "Mazda"),
    (re.compile(r"\b(renault)\b", re.IGNORECASE), "Renault"),
    (re.compile(r"\b(peugeot)\b", re.IGNORECASE), "Peugeot"),
    (re.compile(r"\b(subaru)\b", re.IGNORECASE), "Subaru"),
    (re.compile(r"\b(isuzu)\b", re.IGNORECASE), "Isuzu"),
    (re.compile(r"\b(chery)\b", re.IGNORECASE), "Chery"),
    (re.compile(r"\b(byd)\b", re.IGNORECASE), "BYD"),
    (re.compile(r"\b(geely)\b", re.IGNORECASE), "Geely"),
    (re.compile(r"\b(changan)\b", re.IGNORECASE), "Changan"),
    (re.compile(r"\b(great\s*wall|gwm)\b", re.IGNORECASE), "Great Wall"),
    (re.compile(r"\b(jac)\b", re.IGNORECASE), "JAC"),
]

PATRONES_COMBUSTIBLE = [
    (re.compile(r"\b(glp)\b", re.IGNORECASE), "GLP"),
    (re.compile(r"\b(gnv)\b", re.IGNORECASE), "GNV"),
    (re.compile(r"\b(gasolina|nafta)\b", re.IGNORECASE), "Gasolina"),
    (re.compile(r"\b(di[eé]sel|petr[oó]leo)\b", re.IGNORECASE), "Diésel"),
]

PATRONES_MODELO = [
    (re.compile(r"\bsoluto\b", re.IGNORECASE), "Soluto"),
    (re.compile(r"\blogan\b", re.IGNORECASE), "Logan"),
    (re.compile(r"\b(corolla)\b", re.IGNORECASE), "Corolla"),
    (re.compile(r"\b(yaris)\b", re.IGNORECASE), "Yaris"),
    (re.compile(r"\b(hilux)\b", re.IGNORECASE), "Hilux"),
    (re.compile(r"\b(rav4|rav-4|rav\s*4)\b", re.IGNORECASE), "RAV4"),
    (re.compile(r"\b(etios)\b", re.IGNORECASE), "Etios"),
    (re.compile(r"\b(sentra)\b", re.IGNORECASE), "Sentra"),
    (re.compile(r"\b(versa)\b", re.IGNORECASE), "Versa"),
    (re.compile(r"\b(tiida)\b", re.IGNORECASE), "Tiida"),
    (re.compile(r"\b(kicks)\b", re.IGNORECASE), "Kicks"),
    (re.compile(r"\b(frontier)\b", re.IGNORECASE), "Frontier"),
    (re.compile(r"\b(rio)\b", re.IGNORECASE), "Rio"),
    (re.compile(r"\b(cerato)\b", re.IGNORECASE), "Cerato"),
    (re.compile(r"\b(picanto)\b", re.IGNORECASE), "Picanto"),
    (re.compile(r"\b(sportage)\b", re.IGNORECASE), "Sportage"),
    (re.compile(r"\b(sorento)\b", re.IGNORECASE), "Sorento"),
    (re.compile(r"\b(elantra)\b", re.IGNORECASE), "Elantra"),
    (re.compile(r"\b(accent|acent)\b", re.IGNORECASE), "Accent"),
    (re.compile(r"\b(tucson)\b", re.IGNORECASE), "Tucson"),
    (re.compile(r"\b(santa\s*fe)\b", re.IGNORECASE), "Santa Fe"),
    (re.compile(r"\b(civic)\b", re.IGNORECASE), "Civic"),
    (re.compile(r"\b(cr-?v|cr\s*v)\b", re.IGNORECASE), "CR-V"),
    (re.compile(r"\b(sail)\b", re.IGNORECASE), "Sail"),
    (re.compile(r"\b(d-?max|dmax)\b", re.IGNORECASE), "D-Max"),
    (re.compile(r"\b(gol)\b", re.IGNORECASE), "Gol"),
    (re.compile(r"\b(ranger)\b", re.IGNORECASE), "Ranger"),
    (re.compile(r"\b(amarok)\b", re.IGNORECASE), "Amarok"),
    (re.compile(r"\b(tracker)\b", re.IGNORECASE), "Tracker"),
    (re.compile(r"\b(swift)\b", re.IGNORECASE), "Swift"),
    (re.compile(r"\b(vitara|grand\s*vitara)\b", re.IGNORECASE), "Vitara"),
    (re.compile(r"\b(fiesta)\b", re.IGNORECASE), "Fiesta"),
    (re.compile(r"\b(focus)\b", re.IGNORECASE), "Focus"),
    (re.compile(r"\b(?:mazda\s*3|mazda3)\b", re.IGNORECASE), "3"),
    (re.compile(r"\b(cruze)\b", re.IGNORECASE), "Cruze"),
    (re.compile(r"\b(l200|l-200)\b", re.IGNORECASE), "L200"),
    (re.compile(r"\b(colorado)\b", re.IGNORECASE), "Colorado"),
    (re.compile(r"\b(ecosport|eco\s*sport)\b", re.IGNORECASE), "Ecosport"),
    (re.compile(r"\b(duster)\b", re.IGNORECASE), "Duster"),
    (re.compile(r"\b(vento)\b", re.IGNORECASE), "Vento"),
    (re.compile(r"\b(onix)\b", re.IGNORECASE), "Onix"),
    (re.compile(r"\b(prisma)\b", re.IGNORECASE), "Prisma"),
    (re.compile(r"\b(tiguan)\b", re.IGNORECASE), "Tiguan"),
]

PATRON_NEGACION_VEHICULAR = re.compile(
    r"(?:\bno\b|\bno\s+(?:es|era|fue|ser[ií]a)\b|\bnunca\s+fue\b|\btampoco\s+(?:es|era)?\b|\bdescart(?:o|ado)\b|\bmenos\b|\ben\s+vez\s+de\b)\s*(?:un\b|una\b|el\b|la\b|\s)*(?:[a-záéíóú0-9-]+\s+)?$",
    re.IGNORECASE,
)
PATRON_ANTECEDENTE_VEHICULAR = re.compile(
    r"(?:"
    r"\b(?:tiene|ten[i\u00ed]a)?\s*(?:su\s+|el\s+|la\s+|mi\s+|un\s+|una\s+)?otro\s+(?:auto|carro|veh[i\u00ed]culo|coche|camioneta)(?:\s+(?:del?\s+cliente|que\s+tiene))?(?:\s+(?:que\s+)?(?:es|era|fue))?\b|"
    r"\b(?:otro|otra)\s+(?:carro|auto|veh[i\u00ed]culo|coche|camioneta)\s+del?\s+cliente(?:\s+(?:es|era|fue))?\b|"
    r"\b(?:veh[i\u00ed]culo|auto|carro|coche|camioneta)\s+anterior(?:\s+(?:es|era|fue))?\b|"
    r"\b(?:el|la)\s+(?:auto|carro|veh[i\u00ed]culo|coche|camioneta)\s+de\s+ayer(?:\s+(?:era|fue))?\b|"
    r"\bantes\s+(?:de\s+(?:este|mi|el)\s+)?(?:revis[e\u00e9]|vi|atend[i\u00ed]|ten[i\u00ed]|era|tuve)\b|"
    r"\bel\s+anterior\s+(?:era|fue|carro|auto|veh[i\u00ed]culo)\b|"
    r"\b(?:en\s+un|en\s+el|como\s+en\s+un|como\s+un|al\s+igual\s+que\s+(?:en\s+)?(?:un|el)?)\b"
    r")(?:(?:\s+(?:es|era|fue))?\s+(?:un|una|el|la|este|mi))?(?:\s+[a-z\u00e1\u00e9\u00ed\u00f3\u00fa0-9-]+)?\s*$",
    re.IGNORECASE,
)
PATRON_COMPARATIVO_POST = re.compile(
    r"^(?:[a-z\u00e1\u00e9\u00ed\u00f3\u00fa0-9-]+\s+)?(?:,\s*)?(?:"
    r"pero\s+(?:estamos|sigo|sigue|seguimos|aqu[i\u00ed]|vamos\s+a)\s+(?:revisando|viendo|con|atendiendo|enfocados\s+en)\s+este|"
    r"pero\s+(?:este|aqu[i\u00ed])\s+es|"
    r"era\s+(?:de\s+)?(?:ayer|antes|otro|otra|la\s+semana\s+pasada)|"
    r"fue\s+ayer|del?\s+otro|del?\s+anterior|"
    r"me\s+pas[o\u00f3]|pasaba|ten[i\u00ed]|vi|recuerdo|ocurr[i\u00ed]|fallaba"
    r")",
    re.IGNORECASE,
)
PATRON_AFIRMACION_VEHICULAR = re.compile(
    r"(?:\bes\b|\bera\b|\btengo\b|\ben\b|\bdel?\b|\bpara\b|\bcorrijo\b|\bcorrecci[oó]n\b|\bme\s+equivoqu[eé](?:,\s*era|\s*es)?\b)\s*(?:un\b|una\b|\s)*$",
    re.IGNORECASE,
)
PATRON_CORRECCION_VEHICULO = re.compile(
    r"(?:\b(?:me\s+equivoqu[eé]|no\s+es|no\s+era|corrijo|correcci[oó]n|quise\s+decir|en\s+realidad|en\s+verdad|en\s+vez\s+de)\b|,\s*no\s+)",
    re.IGNORECASE,
)


def seleccionar_entidad_vehicular(
    texto: str,
    coincidencias: List[Tuple[int, int, str]],
    entidad_actual: Optional[str] = None,
) -> Tuple[Optional[str], bool]:
    """Retorna (nueva_entidad, fue_negada_actual) evaluando polaridad y antecedentes."""
    candidatos_validos: List[Tuple[int, str, int]] = []
    fue_negada_actual = False
    texto_l = (texto or "").lower()

    mencion_otro_vehiculo = bool(
        entidad_actual
        and re.search(
            r"\b(?:su\s+)?otro\s+(?:veh[ií]culo|carro|auto|coche|camioneta)\b"
            r".{0,80}\b(?:pero|aunque)\b.{0,60}\b(?:revisamos?|revisando|trabajamos?|diagnosticamos?)"
            r"\s+(?:este|el\s+actual|el\s+mismo)\b",
            texto_l,
        )
    )
    if mencion_otro_vehiculo:
        return None, False

    for start, end, nombre in coincidencias:
        prefijo = texto[:start].rstrip(" ,;:")
        ventana_pre = prefijo[-75:] if len(prefijo) > 75 else prefijo

        es_negado = bool(
            PATRON_NEGACION_VEHICULAR.search(ventana_pre)
            or re.search(
                r"\bno\s+(?:es|era)\s+(?:[a-záéíóú0-9-]+\s+)*" + re.escape(nombre.lower()) + r"\b", texto_l
            )
        )

        if es_negado:
            if entidad_actual and entidad_actual.casefold() == nombre.casefold():
                fue_negada_actual = True
            continue

        sufijo = texto[end:].lstrip(" ,;:")
        ventana_post = sufijo[:75]
        es_comparativo = bool(
            PATRON_ANTECEDENTE_VEHICULAR.search(ventana_pre) or PATRON_COMPARATIVO_POST.search(ventana_post)
        )
        if es_comparativo:
            candidatos_validos.append((start, nombre, 1))
            continue

        if PATRON_CORRECCION_VEHICULO.search(ventana_pre):
            prioridad = 4
        elif PATRON_AFIRMACION_VEHICULAR.search(ventana_pre):
            prioridad = 3
        else:
            prioridad = 2
        candidatos_validos.append((start, nombre, prioridad))

    if not candidatos_validos:
        return (None, fue_negada_actual)

    candidatos_validos.sort(key=lambda x: (x[2], x[0]), reverse=True)
    if entidad_actual and candidatos_validos[0][2] <= 1:
        return (None, fue_negada_actual)
    return (candidatos_validos[0][1], fue_negada_actual)


_seleccionar_entidad_vehicular = seleccionar_entidad_vehicular

PATRON_PLACA_EXPLICITA = re.compile(
    r"\b(?:placa|patente)\s*(?:es\s+|:\s*|\s+)?([A-Za-z0-9]{2,3}[-\s]?[0-9]{3,4})\b",
    re.IGNORECASE,
)
PATRON_PLACA_FORMATO = re.compile(r"\b([A-Za-z][0-9A-Za-z]{2}[-\s][0-9]{3,4})\b")

PATRON_DTC = re.compile(r"\b([PBUCpbuc][0-3][0-9A-Fa-f]{3})\b")
PATRON_ANIO = re.compile(
    r"\b(19[89]\d|20[0-2]\d)\b(?!\s*(?:rpm|revoluciones|km|km/h|bar|psi|kpa|ml|cc|grados|v|mv|hz|ohmios|horas?|dias?|pesos?|soles?|dolares?))\b",
    re.IGNORECASE,
)
PATRON_MEDICION = re.compile(
    r"\b(-?\d+(?:[.,]\d+)?)\s*(psi|bar|kpa|mbar|inhg|mv|v(?:oltios?|olts?)?|ma|miliamperios?|a(?:mperios?)?|amp|ohm(?:ios)?|kohm|Ω|°c|°f|rpm|km/h|%|mm|ms|ml|cm3|cc|g/s|nm)\b",
    re.IGNORECASE,
)
PATRON_MAP_FUERA_RANGO = re.compile(
    r"\b(carga\s+absoluta|sensor\s+map|map)\b.{0,70}\b(fuera\s+de\s+rango|"
    r"fueron\s+de\s+rango|alto|bajo|irregular|an[oó]malo|anormal)\b|"
    r"\b(fuera\s+de\s+rango|fueron\s+de\s+rango|alto|bajo|irregular|an[oó]malo|anormal)\b.{0,70}"
    r"\b(carga\s+absoluta|sensor\s+map|map)\b",
    re.IGNORECASE,
)
PATRON_MEZCLA_REPORTADA = re.compile(r"\bmezcla\s+(pobre|rica)\b", re.IGNORECASE)
PATRON_CAUSAL_INYECCION = re.compile(
    r"\b(?:inyectores?|injectores?|inyecci[oó]n)\b.{0,55}\b(?:no\s+inyectan\s+(?:lo\s+)?suficiente|"
    r"inyectan\s+(?:poco|insuficiente)|caudal\s+(?:bajo|insuficiente)|"
    r"no\s+entregan\s+(?:lo\s+)?suficiente)\b|"
    r"\b(?:no\s+inyectan\s+(?:lo\s+)?suficiente|caudal\s+(?:bajo|insuficiente))\b.{0,55}"
    r"\b(?:inyectores?|injectores?|inyecci[oó]n)\b",
    re.IGNORECASE,
)
PATRON_HALLAZGO_MAF = re.compile(
    r"\b(?:el\s+)?maf\b.{0,55}\b(?:lecturas?\s+(?:raras?|irregulares?|anormales?)|"
    r"valores?\s+(?:raros?|irregulares?|anormales?)|fuera\s+de\s+rango|no\s+mide\s+bien)\b|"
    r"\b(?:lecturas?\\s+(?:raras?|irregulares?|anormales?)|valores?\\s+(?:raros?|irregulares?|anormales?))"
    r".{0,55}\b(?:sensor\s+)?maf\b|"
    r"\b(?:desconect[eé]|solt[eé]|saqu[eé])\b.{0,30}\b(?:sensor\s+)?maf\b|"
    r"\b(?:sensor\s+)?maf\b.{0,30}\b(?:desconectad[oa]|desconect[eé])\b",
    re.IGNORECASE,
)
PATRON_SENSOR_OXIGENO = re.compile(
    r"\b(sensor\s+(?:de\s+)?ox[ií]geno|sonda\s+lambda|sensor\s+o2)\b", re.IGNORECASE
)

PATRONES_SALUDO = [
    re.compile(
        r"^\s*(hola+|buen(?:as|os)?(?:\s+(?:d[ií]as|tardes|noches))?|qu[eé]\s+tal|saludos?|alo|al[oó])\s*[!.,]*\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(hola+\s+(?:(?:amigo|maestro|carbot|bot)\s+)?(?:buenas|buenos\s+d[ií]as|buenas\s+tardes|buenas\s+noches|amigo|maestro|carbot|bot)?)\s*[!.,]*\s*$",
        re.IGNORECASE,
    ),
]

PATRONES_SOLICITUD_DETALLE = [
    re.compile(r"\b(m[aá]s\s+detalles?|dame\s+m[aá]s\s+detalles?|detallar|detalle)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:c[oó]mo\s+(?:(?:lo|la|los|las|se|puedo|debo|podemos|hay\s+que)\s+)?"
        r"(?:medir|comprobar|probar|calibrar|ajustar|revisar|chequear|checar|testear|purgar|diagnosticar|desarmar|limpiar|armar|reaprender|instalar|"
        r"hacer\s+(?:la\s+)?(?:prueba|medici[oó]n|calibraci[oó]n|revisi[oó]n|purga)))\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:c[oó]mo\s+(?:(?:lo|la|los|las|se)\s+)?"
        r"(?:mide|mido|comprueba|compruebo|prueba|pruebo|calibra|calibro|ajusta|ajusto|revisa|reviso|chequea|chequeo|checa|testea|purga|purgo|purgar|reaprende))\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:c[oó]mo\s+(?:(?:se|lo|la)\s+)?(?:revisa|reviso|revisar|comprueba|compruebo|comprobar|mide|mido|medir|prueba|pruebo|probar)\s+"
        r"(?:la\s+|el\s+)?(?:1|2|3|primera|segunda|tercera|opci[oó]n\s+\d+|hip[oó]tesis\s+\d+))\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:paso\s+a\s+paso|procedimiento\s+(?:de\s+|para\s+)?|"
        r"gu[ií]a\s+para\s+(?:medir|probar|calibrar|revisar)|"
        r"instrucciones\s+para\s+(?:medir|probar|calibrar|revisar)|"
        r"expl[ií]came\s+(?:el\s+procedimiento|paso\s+a\s+paso|c[oó]mo\s+se\s+hace)|"
        r"tolerancia|especificaci[oó]n|(?:c[oó]mo\s+(?:se\s+)?(?:usa|utiliza|coloca|monta|mide\s+con)\s+)?reloj\s+comparador\s+paso\s+a\s+paso)\b",
        re.IGNORECASE,
    ),
]
