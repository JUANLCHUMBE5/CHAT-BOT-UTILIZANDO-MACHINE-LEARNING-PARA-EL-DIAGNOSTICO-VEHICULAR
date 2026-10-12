"""Extractor de hechos diagnósticos, detección de correcciones, modificadores y reinicio de casos."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

from src.core.conversacion.detector_polaridad import DetectorPolaridad
from src.core.conversacion.diccionario_automotriz import (
    extraer_hechos_linguisticos,
    normalizar_jerga_automotriz,
)
from src.core.conversacion.models import (
    ConversationState,
    DtcStatus,
    EstadoOperativo,
    FactState,
    FactType,
    QuestionIntent,
)

PATRONES_REINICIO = [
    re.compile(r"^\s*(?:quiero\s+)?cancelar(?:\s+(?:el\s+)?(?:caso|diagn[oó]stico|consulta))?\s*[.!]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*nuevo\s*[.!]?\s*$", re.IGNORECASE),
    re.compile(r"\b(otro\s+(carro|auto|veh[ií]culo))\b", re.IGNORECASE),
    re.compile(r"\b(nuevo\s+diagn[oó]stico|nuevo\s+caso)\b", re.IGNORECASE),
    re.compile(r"\b(reiniciar|empezar\s+de\s+nuevo|comenzar\s+de\s+nuevo)\b", re.IGNORECASE),
    re.compile(r"\b(limpiar\s+sesi[oó]n|caso\s+nuevo)\b", re.IGNORECASE),
    re.compile(r"\b(vamos\s+con\s+otro\s+cliente|termin[eÃ©]\s+ese|tengo\s+uno\s+nuevo)\b", re.IGNORECASE),
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
    r"\b(demora\s+(?:(?:mucho|bastante|demasiado)\s+)?en\s+(?:arrancar|prender|encender)|"
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
    (re.compile(r"\b(toyota)\b", re.IGNORECASE), "Toyota"),
    (re.compile(r"\b(nissan)\b", re.IGNORECASE), "Nissan"),
    (re.compile(r"\b(hyundai)\b", re.IGNORECASE), "Hyundai"),
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
    (re.compile(r"\b(accent)\b", re.IGNORECASE), "Accent"),
    (re.compile(r"\b(tucson)\b", re.IGNORECASE), "Tucson"),
    (re.compile(r"\b(santa\s*fe)\b", re.IGNORECASE), "Santa Fe"),
    (re.compile(r"\b(civic)\b", re.IGNORECASE), "Civic"),
    (re.compile(r"\b(cr-?v|cr\s*v)\b", re.IGNORECASE), "CR-V"),
    (re.compile(r"\b(sail)\b", re.IGNORECASE), "Sail"),
    (re.compile(r"\b(d-?max|dmax)\b", re.IGNORECASE), "D-Max"),
    (re.compile(r"\b(gol)\b", re.IGNORECASE), "Gol"),
    (re.compile(r"\b(ranger)\b", re.IGNORECASE), "Ranger"),
    (re.compile(r"\b(swift)\b", re.IGNORECASE), "Swift"),
    (re.compile(r"\b(vitara|grand\s*vitara)\b", re.IGNORECASE), "Vitara"),
]

PATRON_PLACA_EXPLICITA = re.compile(
    r"\b(?:placa|patente)\s*(?:es\s+|:\s*|\s+)?([A-Za-z0-9]{2,3}[-\s]?[0-9]{3,4})\b",
    re.IGNORECASE,
)
PATRON_PLACA_FORMATO = re.compile(
    r"\b([A-Za-z][0-9A-Za-z]{2}[-\s][0-9]{3})\b"
)

PATRON_DTC = re.compile(r"\b([PBUCpbuc][0-3][0-9A-Fa-f]{3})\b")
PATRON_ANIO = re.compile(r"\b(19[89]\d|20[0-2]\d)\b")
PATRON_MEDICION = re.compile(
    r"\b(\d+(\.\d+)?)\s*(psi|bar|v|volts|voltios|ohm|ohmios|kpa|mm)\b", re.IGNORECASE
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
    r"\b(?:lecturas?\s+(?:raras?|irregulares?|anormales?)|valores?\s+(?:raros?|irregulares?|anormales?))"
    r".{0,55}\b(?:sensor\s+)?maf\b|"
    r"\b(?:desconect[eé]|solt[eé]|saqu[eé])\b.{0,30}\b(?:sensor\s+)?maf\b|"
    r"\b(?:sensor\s+)?maf\b.{0,30}\b(?:desconectad[oa]|desconect[eé])\b",
    re.IGNORECASE,
)
PATRON_SENSOR_OXIGENO = re.compile(r"\b(sensor\s+(?:de\s+)?ox[ií]geno|sonda\s+lambda|sensor\s+o2)\b", re.IGNORECASE)


PATRONES_SALUDO = [
    re.compile(r"^\s*(hola+|buen(?:as|os)?(?:\s+(?:d[ií]as|tardes|noches))?|qu[eé]\s+tal|saludos?|alo|al[oó])\s*[!.,]*\s*$", re.IGNORECASE),
    re.compile(r"^\s*(hola+\s+(?:buenas|buenos\s+d[ií]as|buenas\s+tardes|amigo|maestro|carbot|bot))\s*[!.,]*\s*$", re.IGNORECASE),
]


PATRONES_SOLICITUD_DETALLE = [
    re.compile(r"\b(m[aá]s\s+detalles?|dame\s+m[aá]s\s+detalles?|detallar|detalle)\b", re.IGNORECASE),
    re.compile(r"\b(c[oó]mo\s+(?:lo\s+)?reviso|c[oó]mo\s+(?:se\s+)?prueba|c[oó]mo\s+compruebo)\b", re.IGNORECASE),
    re.compile(r"\b(c[oó]mo\s+(?:reviso|compruebo)\s+(?:la\s+)?(?:1|2|3|primera|segunda|tercera))\b", re.IGNORECASE),
    re.compile(r"\b(expl[ií]came|explica|por\s+qu[eé]|paso\s+a\s+paso|procedimiento)\b", re.IGNORECASE),
]


class ExtractorHechos:
    """Extrae hechos clínicos y gestiona correcciones, modificadores y reinicio conversacional."""

    @staticmethod
    def es_saludo(texto: str) -> bool:
        """Determina si el usuario envió únicamente un saludo de cortesía."""
        if not texto:
            return False
        return any(p.match(texto.strip()) for p in PATRONES_SALUDO)

    @staticmethod
    def es_solicitud_detalle(texto: str) -> bool:
        """Determina si el usuario solicita más detalles o el procedimiento técnico de comprobación."""
        if not texto:
            return False
        return any(p.search(texto.strip()) for p in PATRONES_SOLICITUD_DETALLE)

    @classmethod
    def extraer_placa(cls, texto: str) -> Optional[str]:
        """Extrae la placa vehicular peruana asegurando no confundirla con códigos DTC."""
        if not texto:
            return None
        m_exp = PATRON_PLACA_EXPLICITA.search(texto)
        if m_exp:
            candidato = m_exp.group(1).upper().replace(" ", "-")
            if not re.match(r"^[PBUCpbuc][0-3][0-9A-Fa-f]{3}$", candidato):
                if "-" not in candidato and len(candidato) == 6:
                    candidato = f"{candidato[:3]}-{candidato[3:]}"
                return candidato
        for m in PATRON_PLACA_FORMATO.finditer(texto):
            candidato = m.group(1).upper().replace(" ", "-")
            if not re.match(r"^[PBUCpbuc][0-3][0-9A-Fa-f]{3}$", candidato):
                return candidato
        return None

    @staticmethod
    def es_reinicio_solicitado(texto: str) -> bool:
        """Determina si el usuario solicita iniciar un caso nuevo."""
        if not texto:
            return False
        if any(p.search(texto) for p in PATRONES_REINICIO):
            return True
        txt = "".join(
            c for c in unicodedata.normalize("NFD", texto.lower())
            if unicodedata.category(c) != "Mn"
        )
        return bool(
            re.search(
                r"\b(otro\s+(?:carro|auto|vehiculo|veh.culo)|nuevo\s+(?:caso|diagnostico)|"
                r"caso\s+nuevo|vamos\s+con\s+otro\s+cliente|termine\s+ese|tengo\s+uno\s+nuevo)\b",
                txt,
            )
        )

    @staticmethod
    def es_cancelacion_solicitada(texto: str) -> bool:
        """Distingue cancelar/cerrar el caso de continuar con un caso nuevo."""
        if not texto:
            return False
        return bool(PATRONES_REINICIO[0].fullmatch(texto.strip()))

    @staticmethod
    def clasificar_solicitud_caso(texto: str) -> Dict[str, Any] | None:
        """Reconoce comandos explícitos de caso nuevo o reanudación, no alusiones vagas."""
        if not texto:
            return None
        normalizado = "".join(
            caracter
            for caracter in unicodedata.normalize("NFD", texto.casefold())
            if unicodedata.category(caracter) != "Mn"
        )
        limpio = " ".join(normalizado.split())

        if re.fullmatch(r"(?:quiero\s+)?cancelar(?:\s+(?:el\s+)?(?:caso|diagnostico|consulta))?[.!]*", limpio):
            return {"accion": "cancelar", "preservar_vehiculo": False}

        patron_uuid = (
            r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
        )
        reanudar = re.search(
            rf"\b(?:retomar|reanudar|continuar|volver\s+a)\s+(?:el\s+)?"
            rf"(?:caso|diagnostico)(?:\s+(?:anterior|previo))?(?:\s+{patron_uuid})?\b",
            limpio,
        )
        if reanudar:
            objetivo = reanudar.group(1)
            return {
                "accion": "reanudar",
                "case_id": objetivo,
                "caso_anterior": "anterior" in reanudar.group(0) or "previo" in reanudar.group(0),
            }

        mismo_vehiculo = bool(
            re.search(r"\b(?:mismo|misma)\s+(?:vehiculo|carro|auto|coche|placa)\b", limpio)
            or re.search(r"\bcon\s+la\s+misma\s+placa\b", limpio)
        )
        otro_vehiculo = bool(
            re.search(r"\b(?:otro|otra)\s+(?:vehiculo|carro|auto|coche)\b", limpio)
            or re.search(r"\bcambio\s+de\s+vehiculo\b", limpio)
        )
        nuevo_caso = bool(
            re.search(
                r"\b(?:nuevo|otro)\s+(?:caso|diagnostico|problema)\b|"
            r"\b(?:falla|problema)\s+diferente\b|"
            r"\btengo\s+otra\s+(?:falla|consulta)\b|"
                r"\ben\s+el\s+mismo\s+vehiculo[, ]+ahora\s+"
                r"(?:el\s+)?(?:problema|falla)\s+es\b|"
            r"\b(?:cambiemos|pasemos)\s+(?:a\s+)?otro\s+caso\b|"
                r"\b(?:empezar|empecemos|comenzar|comencemos|iniciar|iniciemos)\s+"
                r"(?:todo\s+)?(?:de\s+nuevo|desde\s+cero)\b|"
                r"\breiniciar\s+(?:el\s+)?(?:caso|diagnostico)\b|"
                r"\botro\s+(?:vehiculo|carro|auto|coche)\b|"
                r"\b(?:tengo|llego|lleg[oó])\s+(?:un\s+)?otro\s+"
                r"(?:vehiculo|carro|auto|coche|caso|problema)\b|"
                r"\b(?:olvida|olvidemos)\s+lo\s+anterior\b|"
                r"^nuevo[.!]*$",
                limpio,
            )
        )
        if nuevo_caso:
            return {
                "accion": "nuevo_caso",
                "preservar_vehiculo": mismo_vehiculo and not otro_vehiculo,
                "otro_vehiculo": otro_vehiculo,
            }
        return None

    @staticmethod
    def contiene_informacion_diagnostica(texto: str) -> bool:
        """Detecta si un mensaje de nuevo caso ya incluye sintomas, pruebas o mediciones."""
        if not texto:
            return False
        patrones = [
            PATRON_NO_ARRANCA,
            PATRON_GIRO_LLAVE,
            PATRON_CLIC_UNICO,
            PATRON_CLICS_REPETIDOS,
            PATRON_DEMORA_ARRANQUE,
            PATRON_DTC,
            PATRON_MEDICION,
            PATRON_MEZCLA_REPORTADA,
            PATRON_CAUSAL_INYECCION,
            PATRON_HALLAZGO_MAF,
            re.compile(
                r"\b(?:aire\s+acondicionado|climatizaci[o\u00f3]n|compresor|no\s+enfr[i\u00ed]a)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(recalienta|recalentar|recalntar|se\s+calienta|temperatura\s+(?:del\s+motor\s+)?(?:sube|empieza\s+a\s+subir|alta)|"
                r"pierde\s+(?:agua|refrigerante|l[iÃ­]quido)|fuga|gotea|"
                r"no\s+enfr[iÃ­]a|sale\s+aire\s+(?:caliente|tibio)|"
                r"vibra|vibraci[oó]n|tiembla|jalonea|tironea|cascabelea|cascabeleo|"
                r"pierde\s+(?:fuerza|potencia)|no\s+jala|"
                r"demora\s+en\s+(?:enganchar|entrar|acoplar)|reversa|"
                r"golpe|ruido|zumbido|chillido|frena\s+mal|pedal\s+esponjoso)\b",
                re.IGNORECASE,
            ),
        ]
        return any(p.search(texto) for p in patrones)

    PATRON_CORRECCION_EXPLICITA = re.compile(
        r"\b("
        r"me\s+equivoqu[eé]|me\s+confund[ií]|quise\s+decir|"
        r"en\s+realidad|no\s+es\s+eso|no\s+es\s+(?:as[ií]|por\s+ah[ií]|fr[ií]o|caliente)|"
        r"no\s+es\s+que\s+no\s+(?:arranque|prenda|encienda)|s[ií]\s+arranca|arranca\s+y\s+se\s+apaga|"
        r"ninguna\s+de\s+(?:esas|las|ellas|opciones|anteriores)|"
        r"ninguno\s+de\s+(?:esos|los|ellos|anteriores)|"
        r"el\s+problema\s+realmente|el\s+problema\s+en\s+realidad|"
        r"eso\s+no\s+ocurre|no\s+ocurre\s+eso|lo\s+que\s+pasa\s+es\s+que|"
        r"corrijo|me\s+refiero\s+a|en\s+verdad|"
        r"no,\s*el\s+problema|no\s+es\s+por\s+ah[ií]"
        r")\b|"
        r"^(?:no|ninguna|ninguno)[.,! ]",
        re.IGNORECASE,
    )

    @classmethod
    def detectar_correcciones(cls, texto: str) -> List[Tuple[str, str, str, FactType]]:
        """Detecta frases correctivas como 'me equivoqué, es caliente', 'ninguna de esas opciones, el problema es que demora en arrancar'."""
        correcciones: List[Tuple[str, str, str, FactType]] = []
        if not texto:
            return correcciones
        texto_l = texto.lower()
        if not cls.PATRON_CORRECCION_EXPLICITA.search(texto_l):
            return correcciones

        if re.search(
            r"\b(no\s+es\s+que\s+no\s+(?:arranque|prenda|encienda)|s[ií]\s+arranca\s*[, ]+(?:pero\s+)?se\s+apaga|arranca\s+y\s+se\s+apaga)\b",
            texto_l,
        ):
            correcciones.append(("sintoma_arranca_y_se_apaga", "arranca y se apaga", "sintoma", FactType.SINTOMA))
            correcciones.append(("sintoma_motor_no_arranca", "ausente", "polaridad", FactType.CONDICION))
            correcciones.append(("motor_arranca", "SI", "condicion", FactType.CONDICION))
            correcciones.append(("estado_operativo", "RALENTI", "condicion", FactType.CONDICION))

        if re.search(r"\b(caliente|en\s+caliente|calent[oó]|calienta|despu[eé]s\s+de\s+calentar|ya\s+caliente)\b", texto_l) or re.search(r"\b(?:reci[eé]n\s+)?a\s+los\s+\d+\s*minutos\b", texto_l):
            correcciones.append(("temperatura", "caliente", "temperatura", FactType.CONDICION))
        elif re.search(r"\b(fr[ií]o|en\s+fr[ií]o|por\s+la\s+mañana)\b", texto_l) and not re.search(
            r"\b(?:en\s+fr[ií]o\s+(?:arranca|prende|funciona|anda)\s+(?:perfecto|bien|normal)|en\s+fr[ií]o\s+no\s+(?:falla|pasa)|no\s+(?:es|falla)\s+en\s+fr[ií]o)\b",
            texto_l,
        ):
            correcciones.append(("temperatura", "frío", "temperatura", FactType.CONDICION))

        if re.search(r"\b(detenido\s+en\s+ralent[ií]|en\s+ralent[ií]|parado\s+en\s+el\s+sem[aá]foro)\b", texto_l):
            correcciones.append(("condicion_operacion", "detenido en ralentí", "condicion", FactType.CONDICION))
            correcciones.append(("estado_operativo", "RALENTI", "condicion", FactType.CONDICION))
        elif re.search(r"\b((?:tambi[eé]n\s+)?(?:ocurre\s+|pasa\s+)?acelerando|al\s+acelerar(?:\s+(?:en\s+carretera|bajo\s+carga))?|en\s+carretera\s+a\s+alta\s+velocidad|en\s+marcha)\b", texto_l):
            correcciones.append(("condicion_operacion", "al acelerar en marcha", "condicion", FactType.CONDICION))
            correcciones.append(("estado_operativo", "MARCHA", "condicion", FactType.CONDICION))

        if re.search(r"\b(no\s+(?:tiene|hay|prende|est[aá]\s+encendido)\s+(?:el\s+)?check|check\s+(?:engine\s+)?apagado|sin\s+check)\b", texto_l):
            correcciones.append(("sintoma_testigo_check_engine", "ausente", "polaridad", FactType.CONDICION))
        elif re.search(r"\b(s[ií]\s+(?:tiene|prende)\s+check|check\s+(?:engine\s+)?(?:s[ií]\s+)?est[aá]\s+encendido)\b", texto_l):
            correcciones.append(("sintoma_testigo_check_engine", "testigo check engine", "sintoma", FactType.SINTOMA))

        if any(w in texto_l for w in ("demora en arrancar", "demora en encender", "demora al arrancar", "tarda en arrancar", "cuesta prender", "le cuesta encender", "demora por las mañanas")):
            correcciones.append(("sintoma_demora_arranque", "demora en arrancar", "sintoma", FactType.SINTOMA))
            correcciones.append(("estado_operativo", "ARRANQUE", "condicion", FactType.CONDICION))
        return correcciones

    @staticmethod
    def _registrar_rechazos_explicitos(estado: ConversationState, texto: str) -> List[Dict[str, Any]]:
        """Guarda rechazos conversacionales sin convertirlos en fallas físicamente confirmadas."""
        normalizado = "".join(
            c for c in unicodedata.normalize("NFD", (texto or "").casefold())
            if unicodedata.category(c) != "Mn"
        )
        componentes = (
            ("bobina", r"\b(?:bobinas?|coil(?:s|\s+pack)?)\b"),
            ("bujia", r"\b(?:bujias?|spark\s+plugs?)\b"),
            ("inyector", r"\b(?:inyectores?|injectores?)\b"),
            ("bateria", r"\b(?:baterias?|acumulador)\b"),
            ("alternador", r"\balternadores?\b"),
            ("maf", r"\bmaf\b"),
            ("map", r"\bmap\b"),
            ("iac", r"\biac\b"),
            ("cuerpo_aceleracion", r"\bcuerpo(?:\s+de)?\s+aceleracion\b"),
            ("bomba_combustible", r"\bbomba\s+de\s+(?:combustible|gasolina)\b"),
            ("sensor_oxigeno", r"\b(?:sensor\s+de\s+oxigeno|sonda\s+lambda|o2)\b"),
            ("termostato", r"\btermostato\b"),
            ("radiador", r"\bradiador\b"),
            ("frenos", r"\b(?:frenos?|pastillas?|discos?\s+de\s+freno)\b"),
            ("suspension", r"\b(?:suspension|amortiguadores?|rotulas?)\b"),
            ("embrague", r"\b(?:embrague|clutch)\b"),
        )
        salida: List[Dict[str, Any]] = []
        normalidad = re.compile(
            r"\b(?:esta\s+bien|estan\s+bien|esta\s+normal|estan\s+normales|"
            r"funciona\s+(?:bien|normal)|salio\s+normal|resultado\s+normal|"
            r"ya\s+(?:la|lo|las|los)?\s*revis(?:e|aron)|se\s+reviso\s+y\s+salio\s+normal)\b"
        )
        revision_contextual = bool(re.search(
            r"\b(?:(?:eso|esa\s+parte|ese\s+componente|ese\s+punto)\s+)?"
            r"(?:ya\s+(?:(?:lo|la|las|los)\s+)?(?:revise|cheque|probe)|"
            r"esta\s+bien|esta\s+normal|salio\s+normal)\b",
            normalizado,
        ))
        ultima_pregunta = estado.ultima_pregunta() or {}
        pregunta_texto = str(ultima_pregunta.get("texto", ""))
        pregunta_normalizada = "".join(
            c for c in unicodedata.normalize("NFD", pregunta_texto.casefold())
            if unicodedata.category(c) != "Mn"
        )
        familias_pregunta = {
            familia for familia, patron in componentes
            if re.search(patron, pregunta_normalizada)
        }
        componentes_por_contexto = (
            familias_pregunta if revision_contextual and len(familias_pregunta) == 1 else set()
        )
        for familia, patron in componentes:
            if not re.search(patron, normalizado) and familia not in componentes_por_contexto:
                continue
            rechazo_explicito = bool(
                re.search(
                    r"\b(?:no\s+es|descart[ea]|no\s+corresponde|no\s+falla|sigue\s+(?:igual|igualita)|"
                    r"la\s+falla\s+sigue|persiste|cambi[eé]\s+nuev[oa]s?)\b",
                    normalizado,
                )
                or normalidad.search(normalizado)
            )
            if not rechazo_explicito:
                continue
            marcador = f"componente:{familia}"
            if marcador not in estado.hipotesis_descartadas:
                estado.hipotesis_descartadas.append(marcador)
            hecho = estado.registrar_hecho(
                campo=f"rechazo_usuario_{familia}",
                valor="componente reportado como revisado/descartado; sin confirmación física independiente",
                categoria="rechazo_hipotesis_usuario",
                estado=FactState.AMBIGUO,
                texto_crudo=texto,
                tipo=FactType.CONDICION,
            )
            salida.append(hecho.to_dict())

        rechazo_generico = bool(
            re.search(
                r"\b(?:esa|esta|la misma)\s+(?:falla|hipotesis)\s+(?:ya\s+)?"
                r"(?:fue\s+)?(?:descartada|no\s+coincide)\b|"
                r"\bno\s+coincide\s+con\s+mi\s+vehiculo\b|"
                r"\bte\s+(?:estoy\s+diciendo|dije)\b.{0,55}\b(?:descartada|ya\s+la\s+revise)\b|"
                r"\bya\s+hice\s+esa\s+prueba\s+y\s+salio\s+normal\b",
                normalizado,
            )
        )
        if rechazo_generico:
            pregunta = ultima_pregunta
            pregunta_hipotesis = pregunta.get("hipotesis") or []
            if pregunta_hipotesis or (
                pregunta.get("intent") == QuestionIntent.CONFIRMACION_ALTERNATIVA.value
                or re.search(r"\b(?:falla|hipotesis)\b", pregunta.get("texto", ""), re.IGNORECASE)
            ):
                hecho_evaluado = estado.obtener_hecho("hipotesis_en_evaluacion")
                objetivo_activo = (
                    hecho_evaluado.valor if hecho_evaluado else estado.falla_principal
                )
                if not objetivo_activo and pregunta_hipotesis:
                    objetivo_activo = pregunta_hipotesis[0]
                objetivos = [objetivo_activo] if objetivo_activo else []
            else:
                objetivos = []
            for indice, objetivo in enumerate(objetivos):
                nombre = str(objetivo.get("falla", "") if isinstance(objetivo, dict) else objetivo).strip()
                if not nombre:
                    continue
                if nombre not in estado.hipotesis_descartadas:
                    estado.hipotesis_descartadas.append(nombre)
                hecho = estado.registrar_hecho(
                    campo=f"rechazo_usuario_hipotesis_{indice + 1}",
                    valor="rechazo verbal del mecánico; no equivale a una falla física confirmada",
                    categoria="rechazo_hipotesis_usuario",
                    estado=FactState.AMBIGUO,
                    texto_crudo=texto,
                    tipo=FactType.CONDICION,
                )
                salida.append(hecho.to_dict())
        return salida

    @classmethod
    def extraer_y_actualizar(
        cls,
        estado: ConversationState,
        texto_usuario: str,
    ) -> List[Dict[str, Any]]:
        """Procesa el mensaje del usuario y actualiza el ConversationState acumulativo."""
        hechos_extraidos: List[Dict[str, Any]] = []
        texto_normalizado = normalizar_jerga_automotriz(texto_usuario)
        estado.historial_mensajes_usuario.append(texto_usuario)
        estado.turno_actual += 1

        # 1. Comprobar si hay correcciones explícitas
        corrs = cls.detectar_correcciones(texto_usuario)
        if corrs:
            estado.last_user_correction = texto_usuario
            for campo, nuevo_val, cat, tipo_f in corrs:
                if campo == "sintoma_demora_arranque":
                    estado.eliminar_hecho("sintoma_climatizacion")
                    estado.eliminar_hecho("falla_confirmada_usuario")
                    estado.eliminar_hecho("condicion_operacion")
                    estado.estado_operativo = EstadoOperativo.ARRANQUE
                    estado.dominio_probable = "ARRANQUE"
                elif campo == "estado_operativo":
                    try:
                        estado.estado_operativo = EstadoOperativo(nuevo_val)
                    except (ValueError, TypeError):
                        pass
                est_f = FactState.AUSENTE_NEGADO if (cat == "polaridad" and nuevo_val == "ausente") else FactState.CONFIRMADO
                h = estado.registrar_hecho(
                    campo=campo,
                    valor=nuevo_val,
                    categoria=cat,
                    estado=est_f,
                    texto_crudo=texto_usuario,
                    tipo=tipo_f,
                )
                hechos_extraidos.append(h.to_dict())

        # 1.5 Extracción de placa vehicular
        placa_encontrada = cls.extraer_placa(texto_usuario)
        if placa_encontrada:
            if estado.placa and estado.placa != placa_encontrada:
                # Si es una corrección explícita de placa ('me equivoqué de placa', etc.),
                # no reiniciar el vehículo completo.
                es_correccion = bool(
                    re.search(
                        r"\b(me\s+equivoqu[eé]|corrijo|la\s+placa\s+correcta|no\s+era\s+esa\s+placa)\b",
                        texto_usuario,
                        re.IGNORECASE,
                    )
                )
                if not es_correccion:
                    estado.reiniciar()
                    estado.historial_mensajes_usuario.append(texto_usuario)
                    estado.turno_actual = 1
            estado.placa = placa_encontrada
            h_placa = estado.registrar_hecho(
                "placa",
                placa_encontrada,
                categoria="vehiculo",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_placa.to_dict())

        # 2. Extracción de marca / modelo / año / combustible con soporte de correcciones
        marcas_encontradas: List[Tuple[int, str]] = []
        for patron, marca in PATRONES_MARCA:
            for m in patron.finditer(texto_usuario):
                marcas_encontradas.append((m.start(), marca))

        if marcas_encontradas:
            marcas_encontradas.sort(key=lambda x: x[0])
            nueva_marca = marcas_encontradas[-1][1]
            if estado.marca and estado.marca != nueva_marca:
                p_prev = estado.placa or placa_encontrada
                estado.reiniciar()
                estado.historial_mensajes_usuario.append(texto_usuario)
                estado.turno_actual = 1
                if p_prev:
                    estado.placa = p_prev
                    estado.registrar_hecho(
                        "placa",
                        p_prev,
                        categoria="vehiculo",
                        texto_crudo=texto_usuario,
                        tipo=FactType.CONDICION,
                    )
            estado.marca = nueva_marca
            h = estado.registrar_hecho(
                "marca",
                nueva_marca,
                categoria="vehiculo",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h.to_dict())

        m_anio = PATRON_ANIO.search(texto_usuario)
        if m_anio:
            nuevo_anio = m_anio.group(1)
            if not estado.anio or estado.anio != nuevo_anio:
                estado.anio = nuevo_anio
                h = estado.registrar_hecho(
                    "anio",
                    nuevo_anio,
                    categoria="vehiculo",
                    texto_crudo=texto_usuario,
                    tipo=FactType.CONDICION,
                )
                hechos_extraidos.append(h.to_dict())

        modelos_encontrados: List[Tuple[int, str]] = []
        for patron, mod in PATRONES_MODELO:
            for m in patron.finditer(texto_usuario):
                modelos_encontrados.append((m.start(), mod))

        if modelos_encontrados:
            modelos_encontrados.sort(key=lambda x: x[0])
            nuevo_mod = modelos_encontrados[-1][1]
            if estado.modelo and estado.modelo != nuevo_mod:
                m_prev = estado.marca
                p_prev = estado.placa or placa_encontrada
                a_prev = estado.anio
                estado.reiniciar()
                estado.historial_mensajes_usuario.append(texto_usuario)
                estado.turno_actual = 1
                if m_prev:
                    estado.marca = m_prev
                    estado.registrar_hecho(
                        "marca",
                        m_prev,
                        categoria="vehiculo",
                        texto_crudo=texto_usuario,
                        tipo=FactType.CONDICION,
                    )
                if p_prev:
                    estado.placa = p_prev
                    estado.registrar_hecho(
                        "placa",
                        p_prev,
                        categoria="vehiculo",
                        texto_crudo=texto_usuario,
                        tipo=FactType.CONDICION,
                    )
                if a_prev:
                    estado.anio = a_prev
                    estado.registrar_hecho(
                        "anio",
                        a_prev,
                        categoria="vehiculo",
                        texto_crudo=texto_usuario,
                        tipo=FactType.CONDICION,
                    )
            estado.modelo = nuevo_mod
            h = estado.registrar_hecho(
                "modelo",
                nuevo_mod,
                categoria="vehiculo",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h.to_dict())

        for patron, comb in PATRONES_COMBUSTIBLE:
            if patron.search(texto_usuario):
                nuevo_comb = comb
                if not estado.combustible or estado.combustible != nuevo_comb:
                    estado.combustible = nuevo_comb
                    h = estado.registrar_hecho(
                        "combustible",
                        nuevo_comb,
                        categoria="vehiculo",
                        texto_crudo=texto_usuario,
                        tipo=FactType.CONDICION,
                    )
                    hechos_extraidos.append(h.to_dict())
                break

        # 2.5 Extracción de transmisión
        texto_l_trans = texto_usuario.lower()
        if re.search(r"\b(mec[aá]nic[oa]|manual)\b", texto_l_trans) and any(
            w in texto_l_trans for w in ("caja", "transmision", "transmisión", "velocidades", "cambios", "embrague")
        ):
            h_trans = estado.registrar_hecho(
                "transmision",
                "MANUAL",
                categoria="perfil",
                estado=FactState.CONFIRMADO,
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_trans.to_dict())
        elif re.search(r"\b(autom[aá]tic[oa]|cvt)\b", texto_l_trans) and any(
            w in texto_l_trans for w in ("caja", "transmision", "transmisión")
        ):
            val_trans = "CVT" if "cvt" in texto_l_trans else "AUTOMATICA"
            h_trans = estado.registrar_hecho(
                "transmision",
                val_trans,
                categoria="perfil",
                estado=FactState.CONFIRMADO,
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_trans.to_dict())

        # 3. Extracción de DTC (DTC_OBSERVADO explícito)
        for dtc in PATRON_DTC.findall(texto_usuario):
            dtc_canonico = dtc.upper()
            campo = f"dtc_{dtc_canonico}"
            estado.dtc_status = DtcStatus.DTC_OBSERVADO
            h = estado.registrar_hecho(campo, dtc_canonico, categoria="dtc", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        # 4. Extracción de mediciones físicas cuantitativas
        from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas
        mediciones_cuantitativas = InterpreteRespuestasCortas._extraer_todas_mediciones(
            texto_usuario.lower(),
            intent_str="MEDICION_TECNICA",
            texto_preg="",
            pending_q=estado.pending_question,
        )
        for val, unidad, condicion in mediciones_cuantitativas:
            if unidad in ("V", "mV"):
                campo_v = f"medicion_voltaje_{condicion}" if condicion else "medicion_voltaje"
                tipo_v = "voltaje_bateria" if condicion in ("reposo", "durante_arranque", "contacto_on") else "voltaje_alternador"
                valor_str = f"{val} {unidad}" + (f" ({condicion})" if condicion else "")
                h_m = estado.registrar_hecho(campo_v, valor_str, categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h_m.to_dict())
                estado.registrar_medicion(tipo=tipo_v, valor=val, unidad=unidad, contexto=condicion or "bateria", prueba=campo_v, estado="observado")
                estado.registrar_prueba_completada(campo_v, f"{val} {unidad}")
                if condicion == "durante_arranque":
                    if val < 9.6:
                        h_c = estado.registrar_hecho("caida_tension_excesiva", "SI", categoria="medicion", tipo=FactType.CONDICION)
                    else:
                        h_c = estado.registrar_hecho("caida_tension_excesiva", "NO", categoria="medicion", tipo=FactType.CONDICION)
                        h_a = estado.registrar_hecho("voltaje_arranque_normal", "SI", categoria="medicion", tipo=FactType.CONDICION)
                        hechos_extraidos.append(h_a.to_dict())
                    hechos_extraidos.append(h_c.to_dict())
                elif condicion == "reposo" and val >= 12.4:
                    h_r = estado.registrar_hecho("voltaje_reposo_normal", "SI", categoria="medicion", tipo=FactType.CONDICION)
                    hechos_extraidos.append(h_r.to_dict())
            elif unidad in ("PSI", "bar", "kPa"):
                campo_p = "medicion_presion"
                h_p = estado.registrar_hecho(campo_p, f"{val} {unidad}", categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h_p.to_dict())
                estado.registrar_medicion(tipo="presion_combustible", valor=val, unidad=unidad, contexto="riel_inyeccion", prueba=campo_p, estado="observado")
                estado.registrar_prueba_completada(campo_p, f"{val} {unidad}")

        m_med = PATRON_MEDICION.search(texto_usuario)
        if m_med:
            med_val = m_med.group(0).lower()
            h = estado.registrar_hecho("medicion", med_val, categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        # Conservar evidencia explícita del MAP/carga absoluta en el caso activo.
        # No inventa una lectura numérica ni declara una avería confirmada.
        if PATRON_MAP_FUERA_RANGO.search(texto_usuario):
            h_map = estado.registrar_hecho(
                "sensor_map_estado",
                "carga absoluta / sensor MAP reportado fuera de rango",
                categoria="medicion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_map.to_dict())

        # Preservar los hallazgos de mezcla/inyección como reportes del mecánico,
        # sin elevarlos a falla confirmada ni inventar una lectura instrumental.
        mezcla = PATRON_MEZCLA_REPORTADA.search(texto_usuario)
        if mezcla and not re.search(
            r"\b(?:no\s+(?:hay|presenta|arroja|marca)|descart(?:o|amos))\b.{0,35}"
            r"\bmezcla\s+" + mezcla.group(1) + r"\b",
            texto_usuario,
            re.IGNORECASE,
        ):
            h_mezcla = estado.registrar_hecho(
                f"mezcla_{mezcla.group(1).lower()}_reportada",
                f"mezcla {mezcla.group(1).lower()} reportada por el usuario",
                categoria="sintoma",
                texto_crudo=texto_usuario,
                tipo=FactType.SINTOMA,
            )
            hechos_extraidos.append(h_mezcla.to_dict())

        if PATRON_CAUSAL_INYECCION.search(texto_normalizado):
            h_inyeccion = estado.registrar_hecho(
                "caudal_inyectores_reportado",
                "usuario reporta caudal insuficiente en inyectores",
                categoria="sistema",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_inyeccion.to_dict())

        if PATRON_HALLAZGO_MAF.search(texto_normalizado):
            h_maf = estado.registrar_hecho(
                "sensor_maf_lectura_anomala_reportada",
                "usuario reporta lecturas anómalas del MAF",
                categoria="medicion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_maf.to_dict())

        if PATRON_SENSOR_OXIGENO.search(texto_usuario) and re.search(
            r"\b(?:cambi[eé]|reemplaz[eé]|instal[eé])\b.{0,35}"
            r"\b(?:sensor|sonda|lambda|ox[ií]geno|o2)\b|"
            r"\b(?:sensor|sonda|lambda|ox[ií]geno|o2)\b.{0,35}"
            r"\b(?:cambi[eé]|reemplaz[eé]|instal[eé])\b",
            texto_usuario,
            re.IGNORECASE,
        ):
            h_sensor = estado.registrar_hecho(
                "sensor_oxigeno_reemplazado_reportado",
                "usuario reporta sensor de oxígeno reemplazado; síntoma persiste",
                categoria="antecedente",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_sensor.to_dict())

        hechos_extraidos.extend(cls._registrar_rechazos_explicitos(estado, texto_usuario))

        # 5. Componentes revisados o reemplazados
        texto_l = texto_usuario.lower()
        if any(c in texto_l for c in ("ya cambie", "ya cambié", "ya las cambié", "ya las cambie", "ya los cambié", "ya los cambie", "ya le cambié", "ya se cambiaron", "ya se cambió", "nuevo", "nueva", "cambiamos", "recién cambiado", "recien cambiado", "recién cambié")):
            for pieza in ("bujias", "bujías", "bobinas", "bobina", "bomba", "filtro", "termostato", "pastillas", "aceite"):
                if pieza in texto_l:
                    canon = "bujías" if "buj" in pieza else ("bobinas" if "bobin" in pieza else pieza)
                    h = estado.registrar_hecho(f"reemplazado_{canon}", f"{canon} reemplazado(a)", categoria="antecedente", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                    hechos_extraidos.append(h.to_dict())

        if any(c in texto_l for c in ("ya revise", "ya revisé", "probe", "probé", "intercambie", "intercambié", "descarte", "descarté", "esta bien", "está bien", "esta ok", "está ok")):
            for pieza in ("bujias", "bujías", "bobinas", "bobina", "bomba", "fusible", "presion", "presión", "compresion", "compresión", "bateria", "batería", "alternador", "arrancador"):
                if pieza in texto_l:
                    canon = "bujías" if "buj" in pieza else ("bobinas" if "bobin" in pieza else ("batería" if "bater" in pieza else pieza))
                    h = estado.registrar_hecho(f"probado_{canon}", f"{canon} probado/descartado", categoria="componente_descartado", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                    hechos_extraidos.append(h.to_dict())

        # 5b. Componentes o sistemas no revisados explícitamente (Fase 9.14)
        for campo_nr, val_nr in DetectorPolaridad.extraer_componentes_no_revisados(texto_usuario):
            h = estado.registrar_hecho(
                campo_nr, val_nr, categoria="inspeccion_pendiente",
                estado=FactState.NO_REVISADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h.to_dict())

        # 5c. Declaraciones de funcionamiento normal de subsistemas (Fase 9.14)
        for campo_norm, val_norm in DetectorPolaridad.extraer_sistemas_normales(texto_usuario):
            h = estado.registrar_hecho(
                campo_norm, val_norm, categoria="sistema_normal",
                estado=FactState.AUSENTE_NEGADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h.to_dict())

        # 5c.1 Resultado explícito de prueba de chispa (Hotfix Sentra H02)
        # Diferencia disponibilidad de la herramienta de un resultado
        # técnico ya observado durante la comprobación.
        menciona_chispa = bool(
            re.search(
                r"\b(chispa|salto\s+de\s+chispa|probador\s+de\s+chispa)\b",
                texto_l,
            )
        )

        chispa_ausente = bool(
            menciona_chispa
            and re.search(
                r"\b("
                r"no\s+(?:hay|tiene|da|sale|se\s+observa|se\s+ve)\s+(?:ninguna\s+)?chispa"
                r"|sin\s+chispa"
                r"|no\s+salta\s+chispa"
                r"|chispa\s+ausente"
                r")\b",
                texto_l,
            )
        )

        chispa_presente = bool(
            menciona_chispa
            and not chispa_ausente
            and re.search(
                r"\b("
                r"se\s+observa(?:\s+una)?\s+chispa"
                r"|se\s+ve(?:\s+una)?\s+chispa"
                r"|hay\s+chispa"
                r"|da\s+chispa"
                r"|chispa\s+(?:azul|azulada|constante|uniforme|fuerte)"
                r"|salto\s+(?:constante\s+)?de\s+chispa"
                r")\b",
                texto_l,
            )
        )

        if chispa_ausente:
            h = estado.registrar_hecho(
                "resultado_prueba_chispa",
                "chispa ausente",
                categoria="prueba_diagnostica",
                estado=FactState.CONFIRMADO,
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            estado.registrar_prueba_completada(
                "prueba_chispa",
                "SIN_CHISPA",
                detalles={"texto_crudo": texto_usuario},
            )
            hechos_extraidos.append(h.to_dict())

        elif chispa_presente:
            h = estado.registrar_hecho(
                "resultado_prueba_chispa",
                "chispa presente y observable",
                categoria="prueba_diagnostica",
                estado=FactState.CONFIRMADO,
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            estado.registrar_prueba_completada(
                "prueba_chispa",
                "CHISPA_PRESENTE",
                detalles={"texto_crudo": texto_usuario},
            )
            hechos_extraidos.append(h.to_dict())

        # 5d. Disponibilidad o indisponibilidad explícita de herramientas del taller (Fase 11.3)
        if re.search(r"\b(s[ií]\s+(?:tengo|cuento|dispongo)|tengo\s+(?:un\s+)?|cuento\s+con\s+(?:un\s+)?|lo\s+tengo|ya\s+lo\s+conect[eé]|s[ií]\s+maestro.*(?:man[oó]metro|mult[ií]metro|esc[aá]ner|tester))\b", texto_l):
            if "manometro" in texto_l or "manómetro" in texto_l or "presion" in texto_l:
                estado.marcar_herramienta_disponible("manometro")
                h = estado.registrar_hecho("manometro_disponible", "SI", categoria="herramienta", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())
            if "multimetro" in texto_l or "multímetro" in texto_l or "tester" in texto_l:
                estado.marcar_herramienta_disponible("multimetro")
                h = estado.registrar_hecho("multimetro_disponible", "SI", categoria="herramienta", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())
            if "escaner" in texto_l or "escáner" in texto_l or "scanner" in texto_l:
                estado.marcar_herramienta_disponible("escaner")
                h = estado.registrar_hecho("escaner_disponible", "SI", categoria="herramienta", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())
            if "osciloscopio" in texto_l:
                estado.marcar_herramienta_disponible("osciloscopio")
                h = estado.registrar_hecho("osciloscopio_disponible", "SI", categoria="herramienta", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())

        if re.search(r"\b(no\s+(?:tengo|cuento|dispongo|se\s+ha\s+conectado|est[aá]\s+conectado|conect[eé]|se\s+conect[oó])|sin\s+|todav[ií]a\s+no\s+(?:se\s+ha\s+)?conectado|a[uú]n\s+no\s+(?:se\s+ha\s+)?conectado)\b", texto_l):
            if "escaner" in texto_l or "escáner" in texto_l or "scanner" in texto_l or "obd" in texto_l:
                estado.marcar_herramienta_indisponible("escaner")
                estado.dtc_status = DtcStatus.DTC_DESCONOCIDO
                h = estado.registrar_hecho("escaner_disponible", "NO", categoria="herramienta", estado=FactState.NO_APLICA, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())
            if "osciloscopio" in texto_l:
                estado.marcar_herramienta_indisponible("osciloscopio")
                h = estado.registrar_hecho("osciloscopio_disponible", "NO", categoria="herramienta", estado=FactState.NO_APLICA, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())
            if "manometro" in texto_l or "manómetro" in texto_l:
                estado.marcar_herramienta_indisponible("manometro")
                h = estado.registrar_hecho("manometro_disponible", "NO", categoria="herramienta", estado=FactState.NO_APLICA, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())
            if "multimetro" in texto_l or "multímetro" in texto_l or "tester" in texto_l:
                estado.marcar_herramienta_indisponible("multimetro")
                h = estado.registrar_hecho("multimetro_disponible", "NO", categoria="herramienta", estado=FactState.NO_APLICA, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())

        if re.search(r"\b(no\s+s[eé]\s+si\s+(?:tiene|hay)|no\s+me\s+he\s+fijado\s+si\s+(?:tiene|hay)|no\s+tengo\s+idea\s+si)\b", texto_l):
            if any(w in texto_l for w in ("codigo", "codigos", "código", "códigos", "dtc")):
                estado.dtc_status = DtcStatus.DTC_DESCONOCIDO
                h = estado.registrar_hecho("codigos_dtc_observados", "desconocido", categoria="dtc", estado=FactState.DESCONOCIDO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())

        # 5e. Comprobación de acople de compresor de A/C (Fase 11.3)
        es_acople_positivo = bool(
            re.search(
                r"\b(compresor\s+s[ií]\s+acopla|s[ií]\s+acopla|s[ií],?\s+se\s+escucha\s+el\s+clic|"
                r"escucho\s+el\s+clic|se\s+oye\s+el\s+clic|el\s+compresor\s+entra|"
                r"entra\s+el\s+compresor|engancha\s+el\s+compresor|el\s+compresor\s+engancha|"
                r"bajan\s+(?:un\s+poco\s+|ligeramente\s+)?las\s+(?:revoluciones|rpm))\b",
                texto_l,
            )
            and not re.search(r"\bno\s+(?:acopla|entra|engancha|se\s+escucha)\b", texto_l)
        )
        es_acople_negativo = bool(
            re.search(
                r"\b(no\s+acopla|no\s+entra|no\s+engancha|no\s+pega|"
                r"no\s+se\s+(?:escucha|oye)\s+(?:el\s+)?clic|silencio\s+total|no\s+activa)\b",
                texto_l,
            )
            and any(w in texto_l for w in ("compresor", "clic", "acopla", "entra", "a/c", "clima"))
        )
        es_acople_desconocido = bool(
            re.search(r"\b(no\s+s[eé]\s+si\s+acopla|no\s+s[eé]\s+si\s+entra|no\s+me\s+fij[eé]\s+si\s+acopla)\b", texto_l)
        )
        if es_acople_desconocido:
            h = estado.registrar_hecho(
                "compresor_acopla", "desconocido", categoria="inspeccion",
                estado=FactState.DESCONOCIDO, texto_crudo=texto_usuario, tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h.to_dict())
        elif es_acople_positivo:
            h = estado.registrar_hecho(
                "compresor_acopla", "SI", categoria="inspeccion",
                estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION,
            )
            estado.registrar_prueba_completada("acople_compresor", "SI")
            hechos_extraidos.append(h.to_dict())
        elif es_acople_negativo:
            h = estado.registrar_hecho(
                "compresor_acopla", "NO", categoria="inspeccion",
                estado=FactState.CONFIRMADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION,
            )
            estado.registrar_prueba_completada("acople_compresor", "NO")
            hechos_extraidos.append(h.to_dict())

        # 6. Extracción de Modificadores y Distinción Semántica A/C (Fase 11 Etapa 2)
        es_queja_climatizacion = bool(
            re.search(
                r"\b(no\s+enfr[ií]a|enfr[ií]a\s+(?:poco|nada|casi\s+nada)|deja\s+de\s+enfriar|"
                r"solo\s+enfr[ií]a|enfr[ií]a\s+(?:solo|cuando)|"
                r"sale\s+aire\s+(?:caliente|tibio|ambiente|a\s+temperatura\s+ambiente)|"
                r"sin\s+gas(?:\s+r134a)?|falta\s+(?:de\s+)?gas\s+(?:al\s+aire|r134a)|"
                r"compresor\s+(?:no\s+entra|no\s+acopla|no\s+pega|no\s+arranca|no\s+activa)|"
                r"clima\s+(?:no\s+enfr[ií]a|calienta|no\s+sopla\s+fr[ií]o)|"
                r"aire\s+(?:caliente|tibio|no\s+tira\s+fr[ií]o)|"
                r"fuga\s+de\s+gas\s+(?:r134a|del\s+aire))\b",
                texto_l,
            )
        )
        tiene_mencion_ac = bool(re.search(r"\b(a/c|aire\s+acondicionado|clima|el\s+ac)\b", texto_l))

        if es_queja_climatizacion:
            # Caso B: A/C como avería principal de Climatización
            estado.dominio_probable = "CLIMATIZACION"
            h = estado.registrar_hecho(
                "sintoma_climatizacion",
                "aire acondicionado no enfría / sale aire caliente",
                categoria="sintoma",
                texto_crudo=texto_usuario,
                tipo=FactType.SINTOMA,
            )
            hechos_extraidos.append(h.to_dict())
            if re.search(r"\b(sem[aá]foro|detenido|al\s+parar|al\s+detener)\b", texto_l) and re.search(r"\b(manejando|en\s+movimiento|velocidad)\b", texto_l):
                h_op = estado.registrar_hecho(
                    "condicion_operacion",
                    "deja de enfriar detenido en semáforo",
                    categoria="condicion",
                    texto_crudo=texto_usuario,
                    tipo=FactType.CONDICION,
                )
                hechos_extraidos.append(h_op.to_dict())
        elif tiene_mencion_ac:
            # Caso A: A/C como condición operacional de carga para el motor
            h = estado.registrar_hecho(
                "modificador_ac",
                "A/C encendido",
                categoria="modificador",
                texto_crudo=texto_usuario,
                tipo=FactType.MODIFICADOR,
            )
            hechos_extraidos.append(h.to_dict())

        es_queja_refrigeracion = bool(
            re.search(
                r"\b(recalienta|recalentar|recalentando|recalent[oó]|se\s+recalienta|"
                r"el\s+auto\s+recalienta|el\s+carro\s+recalienta|motor\s+recalienta|"
                r"hierve|hirviendo|levanta\s+temperatura|se\s+calienta|calienta\s+el\s+motor|"
                r"(?:se\s+(?:le\s+)?sube|sube|subi[oó])\s+(?:la\s+)?temperatura|"
                r"temperatura\s+(?:del\s+motor\s+)?(?:est[aá]\s+)?subiendo|"
                r"temperatura\s+(?:sube|al\s+tope|volando|elevada|alta)|"
                r"aguja\s+de\s+temperatura|"
                r"(?:bota|botando|sale|echando)\s+vapor|vapor\s+(?:bajo|del|por\s+el)\s+cap[oó]|"
                r"termostato|electroventilador|motoventilador|manguera\s+(?:inferior|superior)?(?:\s+del)?\s+radiador)\b",
                texto_l,
            )
            and not re.search(r"\bno\s+(?:se\s+)?(?:recalienta|calienta|hierve)\b", texto_l)
        )
        if es_queja_refrigeracion:
            estado.dominio_probable = "REFRIGERACION"
            h_ref = estado.registrar_hecho(
                "sintoma_sobrecalentamiento",
                "sobrecalentamiento del motor / sistema de refrigeración",
                categoria="sintoma",
                texto_crudo=texto_usuario,
                tipo=FactType.SINTOMA,
            )
            hechos_extraidos.append(h_ref.to_dict())

        if re.search(r"\b(luces?\s+prendidas?|luces?\s+altas?|prendo\s+las\s+luces?|con\s+luces?|luces?\s+(?:se\s+ponen\s+)?tenues?|bajan?\s+las\s+luces?|luces?\s+bajas?)\b", texto_l):
            luces_tenues = bool(re.search(r"\b(tenues?|bajan?\s+las\s+luces?|luces?\s+bajas?)\b", texto_l))
            valor_luces = "luces tenues" if luces_tenues else "luces encendidas"
            h = estado.registrar_hecho("modificador_luces", valor_luces, categoria="modificador", texto_crudo=texto_usuario, tipo=FactType.MODIFICADOR)
            hechos_extraidos.append(h.to_dict())

        # 7. Extracción de condiciones operacionales lingüísticas
        ling = extraer_hechos_linguisticos(texto_usuario)
        for k, v in ling.items():
            if corrs and any(c[0] == k for c in corrs):
                continue
            cat = "temperatura" if k == "temperatura" else ("cambio_accion" if k == "evolucion_accion" else "condicion")
            h = estado.registrar_hecho(k, v, categoria=cat, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        # 7.1 Hechos de transmision: el estado operativo puede seguir en MARCHA,
        # pero la queja principal pertenecer a la caja automatica.
        menciona_caja_automatica = bool(re.search(
            r"\b(?:caja\s+(?:de\s+cambios\s+)?autom[aá]tica|transmisi[oó]n\s+autom[aá]tica|dsg|cvt)\b",
            texto_l,
        ))
        if menciona_caja_automatica:
            tipo_caja = "DSG" if re.search(r"\bdsg\b", texto_l) else (
                "CVT" if re.search(r"\bcvt\b", texto_l) else "automática"
            )
            estado.transmision = tipo_caja

        golpe_cambios = bool(
            re.search(r"\b(?:golpe(?:a|teo|tea)?|patea|tironea)\b", texto_l)
            and re.search(r"\b(?:pasar|cambiar|meter|seleccionar|entrar)\b", texto_l)
            and re.search(r"\b(?:cambios?|marchas?|velocidades?|d|r)\b", texto_l)
            and (
                menciona_caja_automatica
                or estado.transmision
                or re.search(r"\b(?:caja|transmisi[oó]n|embrague|clutch|cambios?)\b", texto_l)
            )
        )
        if golpe_cambios:
            h = estado.registrar_hecho(
                "sintoma_golpeteo_al_cambiar",
                "golpeteo al pasar cambios",
                categoria="sintoma",
                texto_crudo=texto_usuario,
                tipo=FactType.SINTOMA,
            )
            hechos_extraidos.append(h.to_dict())

        es_reversa = bool(re.search(r"\b(reversa|retroceso|marcha\s+atr[aá]s)\b", texto_l))
        demora_acople = bool(
            re.search(r"\b(demora|tarda)\b.{0,45}\b(enganchar|entrar|acoplar)\b", texto_l)
        )
        golpe_acople = bool(
            re.search(r"\b(entra|engancha|acopla)\b.{0,35}\b(golpe|golpea|patea)\b", texto_l)
        )
        if es_reversa and demora_acople:
            estado.transmision = "Automatica" if "automático" in texto_l or "automatico" in texto_l else estado.transmision
            h = estado.registrar_hecho(
                "sintoma_demora_acople_reversa", "reversa demora en enganchar",
                categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA,
            )
            hechos_extraidos.append(h.to_dict())
            h = estado.registrar_hecho(
                "condicion_operacion", "al seleccionar reversa",
                categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h.to_dict())
        if es_reversa and golpe_acople:
            h = estado.registrar_hecho(
                "sintoma_golpe_acople_reversa", "reversa entra con golpe",
                categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA,
            )
            hechos_extraidos.append(h.to_dict())

        # 8. Extracción estructurada de hechos de arranque (Fase 9.6)
        es_no_arranca_componente = bool(
            re.search(
                r"\b(?:electroventilador|motoventilador|ventilador|electro|compresor)\s+(?:no\s+)",
                texto_usuario.lower(),
            )
        )
        es_arranca_y_se_apaga = bool(
            re.search(
                r"\b(no\s+es\s+que\s+no\s+(?:arranque|prenda|encienda)|s[ií]\s+arranca\s*[, ]+(?:pero\s+)?se\s+apaga|arranca\s+y\s+se\s+apaga)\b",
                texto_usuario.lower(),
            )
        )
        if es_arranca_y_se_apaga:
            estado.eliminar_hecho("sintoma_motor_no_arranca")
            h_arr = estado.registrar_hecho(
                "sintoma_arranca_y_se_apaga",
                "arranca y se apaga",
                categoria="sintoma",
                texto_crudo=texto_usuario,
                tipo=FactType.SINTOMA,
            )
            hechos_extraidos.append(h_arr.to_dict())
            h_mot = estado.registrar_hecho(
                "motor_arranca",
                "SI",
                categoria="condicion",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h_mot.to_dict())
        elif PATRON_NO_ARRANCA.search(texto_usuario) and not es_no_arranca_componente:
            h = estado.registrar_hecho("motor_arranca", "NO", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        if PATRON_GIRO_LLAVE.search(texto_usuario):
            h = estado.registrar_hecho("evento", "giro_llave", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        if PATRON_CLIC_UNICO.search(texto_usuario):
            h = estado.registrar_hecho("ruido_arranque", "clic_unico", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
            hechos_extraidos.append(h.to_dict())
        elif PATRON_CLICS_REPETIDOS.search(texto_usuario):
            h = estado.registrar_hecho("ruido_arranque", "clics_repetidos", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
            hechos_extraidos.append(h.to_dict())

        if PATRON_TABLERO_PRENDE.search(texto_usuario):
            h = estado.registrar_hecho("tablero_enciende", "SI", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        if PATRON_RADIO_PRENDE.search(texto_usuario):
            h = estado.registrar_hecho("radio_enciende", "SI", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        if PATRON_LUCES_ATENUAN.search(texto_usuario):
            h = estado.registrar_hecho("luces_se_atenuan", "SI", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        if PATRON_ANTECEDENTE_MARCHA.search(texto_usuario):
            h = estado.registrar_hecho("antecedente_motor_en_marcha", "SI", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        # 9. Síntomas primarios con polaridad explícita (Fase 9.14)
        for campo_s, val_s, estado_s in DetectorPolaridad.extraer_sintomas(texto_usuario):
            if golpe_cambios and campo_s == "sintoma_ruido_anómalo":
                continue
            h = estado.registrar_hecho(
                campo_s, val_s, categoria="sintoma", estado=estado_s,
                texto_crudo=texto_usuario, tipo=FactType.SINTOMA,
            )
            hechos_extraidos.append(h.to_dict())

        if (
            not es_arranca_y_se_apaga
            and PATRON_NO_ARRANCA.search(texto_normalizado.lower())
            and not es_no_arranca_componente
            and not estado.obtener_hecho("sintoma_motor_no_arranca")
        ):
            h = estado.registrar_hecho("sintoma_motor_no_arranca", "motor no arranca", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
            hechos_extraidos.append(h.to_dict())

        if PATRON_DEMORA_ARRANQUE.search(texto_usuario):
            h = estado.registrar_hecho("sintoma_demora_arranque", "demora en arrancar", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
            hechos_extraidos.append(h.to_dict())
            if not estado.obtener_hecho("condicion_operacion"):
                h_c = estado.registrar_hecho("condicion_operacion", "al dar arranque en frío", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h_c.to_dict())

        # 9b. Extracción de hechos de ubicación, velocidad, comportamiento y polaridad (Fase 11.5)
        if re.search(r"\b(en\s+el\s+volante|en\s+el\s+tim[oó]n|en\s+la\s+direcci[oó]n|volante|tim[oó]n)\b", texto_l):
            h = estado.registrar_hecho("ubicacion_sintoma", "en el volante", categoria="ubicacion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())
        if re.search(r"\b(en\s+el\s+pedal|pedal\s+de\s+freno)\b", texto_l):
            if re.search(r"\b(no\s+siento|casi\s+no|sin\s+vibraci[oó]n|no\s+vibra|apenas)\b", texto_l):
                h = estado.registrar_hecho("vibracion_pedal", "mínima o nula", categoria="polaridad", estado=FactState.AUSENTE_NEGADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())
        if re.search(r"\b(resto\s+del\s+veh[ií]culo|carrocer[ií]a|asiento|todo\s+el\s+carro|todo\s+el\s+veh[ií]culo)\b", texto_l):
            if re.search(r"\b(no\s+vibra|tampoco\s+vibra|sin\s+vibraci[oó]n|no\s+se\s+siente)\b", texto_l):
                h = estado.registrar_hecho("vibracion_carroceria", "ausente", categoria="polaridad", estado=FactState.AUSENTE_NEGADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())

        if re.search(r"\b(a\s+(?:una\s+)?velocidad\s+media\s+o\s+alta|a\s+alta\s+velocidad|en\s+carretera\s+a\s+velocidad|a\s+cierta\s+velocidad|a\s+m[aá]s\s+de\s+\d+)\b", texto_l):
            h = estado.registrar_hecho("condicion_velocidad", "a velocidad media o alta", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        if re.search(r"\b(sin\s+frenar\s+(?:no\s+siente|no\s+vibra|no\s+pasa)|al\s+no\s+frenar\s+no|si\s+no\s+freno\s+no)\b", texto_l):
            h = estado.registrar_hecho("falla_sin_frenar", "no vibra sin frenar", categoria="polaridad", estado=FactState.AUSENTE_NEGADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        if re.search(r"\b(todav[ií]a\s+no\s+he\s+revisado\s+el\s+veh[ií]culo|a[uú]n\s+no\s+se\s+ha\s+revisado|no\s+he\s+revisado\s+nada)\b", texto_l):
            h = estado.registrar_hecho("inspeccion_vehiculo", "no revisado aún en taller", categoria="inspeccion_pendiente", estado=FactState.NO_REVISADO, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        if re.search(r"\b(gira\s+(?:con\s+)?buena\s+velocidad|gira\s+r[aá]pido|gira\s+normal)\b", texto_l):
            h = estado.registrar_hecho("giro_motor", "gira rápido con buena velocidad", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        # Disparador específico de pedal de freno
        if re.search(r"\b((?:cuando|al)\s+(?:piso|pisa|se\s+pisa)\s+el\s+(?:pedal\s+de\s+)?freno|pisar\s+el\s+(?:pedal\s+de\s+)?freno)\b", texto_l):
            h_pedal_freno = estado.registrar_hecho("condicion_operacion", "al pisar el pedal de freno", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_pedal_freno.to_dict())

        # 10. Inferencia contextual de EstadoOperativo y detección de contradicciones (Fase 9.6 y 9.10)
        res_op = cls.inferir_estado_operativo(estado, texto_usuario)
        nuevo_estado_op, es_conflicto = res_op[0], res_op[1]
        if nuevo_estado_op != EstadoOperativo.DESCONOCIDO or not any(c[0] == "estado_operativo" for c in corrs):
            estado.estado_operativo = nuevo_estado_op

        if nuevo_estado_op == EstadoOperativo.FRENADO and not estado.obtener_hecho("condicion_operacion"):
            h_freno = estado.registrar_hecho("condicion_operacion", "al frenar", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h_freno.to_dict())

        if es_conflicto:
            h = estado.registrar_hecho(
                "conflicto_operativo",
                "arranque_vs_marcha",
                categoria="conflicto",
                texto_crudo=texto_usuario,
                tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(h.to_dict())

        return hechos_extraidos

    @classmethod
    def inferir_estado_operativo(
        cls,
        estado: ConversationState,
        texto_usuario: str,
    ) -> Tuple[EstadoOperativo, bool, Dict[str, Any]]:
        """
        Infiere el EstadoOperativo contextual con prioridad de evidencia temporal (Fase 9.10).
        Distingue señales del mensaje actual de señales heredadas, impidiendo que
        un estado antiguo de arranque anule una condición actual de frenado o marcha.
        """
        texto_l = texto_usuario.lower()
        hechos_confirmados = {
            k: h.valor for k, h in estado.hechos.items() if h.estado == FactState.CONFIRMADO
        }

        # 1. Señales explícitas del mensaje actual
        es_no_arranca_comp = bool(
            re.search(
                r"\b(?:electroventilador|motoventilador|ventilador|electro|compresor)\s+(?:no\s+)",
                texto_l,
            )
        )
        arranque_actual = bool(
            (PATRON_NO_ARRANCA.search(texto_l) and not es_no_arranca_comp)
            or PATRON_GIRO_LLAVE.search(texto_l)
            or PATRON_DEMORA_ARRANQUE.search(texto_l)
        )
        frenado_actual = bool(
            re.search(r"\b(al\s+frenar|frenando|cuando\s+fren[ao]|frena(ndo)?|pedal\s+de\s+freno|al\s+pisar\s+el\s+(?:pedal\s+de\s+)?freno)\b", texto_l)
            and not DetectorPolaridad.es_condicion_negada(r"\b(al\s+frenar|frenando|cuando\s+fren[ao]|al\s+pisar\s+el\s+(?:pedal\s+de\s+)?freno|frena)\b", texto_l)
        )
        ralenti_actual = bool(
            re.search(r"\b(en\s+ralent[ií]|en\s+el\s+sem[aá]foro|detenido(\s+en\s+ralent[ií])?|en\s+neutro|parado\s+esperando)\b", texto_l)
            and not DetectorPolaridad.es_condicion_negada(r"\b(en\s+ralent[ií]|detenido|en\s+neutro)\b", texto_l)
        )
        marcha_actual = bool(
            re.search(
                r"\b(en\s+carretera|a\s+\d+\s*km/h|circulando|en\s+marcha|andando|anda|al\s+andar|a\s+velocidad|"
                r"acelerando|al\s+acelerar|bajo\s+aceleraci[oó]n|acelerando\s+con\s+fuerza|voy\s+a\s+\d+|cuando\s+voy\s+a|manejando|al\s+manejar|"
                r"despu[eé]s\s+de\s+\d+\s+minutos|pistas?\s+irregulares?|baches?|trocha|calamina|empedrado)\b",
                texto_l,
            )
        )
        estacionado_actual = bool(
            re.search(r"\b(estacionado|parqueado)\b", texto_l)
            and not arranque_actual
            and not marcha_actual
        )

        # 2. Señales heredadas del caso activo previo
        arranque_heredado = bool(
            hechos_confirmados.get("motor_arranca") == "NO"
            or hechos_confirmados.get("ruido_arranque") in ("clic_unico", "clics_repetidos")
            or hechos_confirmados.get("evento") == "giro_llave"
            or "sintoma_motor_no_arranca" in hechos_confirmados
            or "sintoma_demora_arranque" in hechos_confirmados
            or "sintoma_chasquido_de_arranque_clac" in hechos_confirmados
        )
        frenado_heredado = bool(
            hechos_confirmados.get("condicion_operacion") == "al frenar"
            or "sintoma_anomalía_en_frenos" in hechos_confirmados
            or "sintoma_anomalia_en_frenos" in hechos_confirmados
        )
        ralenti_heredado = bool(hechos_confirmados.get("condicion_operacion") == "detenido en ralentí")
        marcha_heredada = bool(
            hechos_confirmados.get("condicion_operacion") in ("en carretera a velocidad", "al acelerar bajo carga")
        )

        metadata = {
            "seniales_mensaje": {
                "senial_arranque": arranque_actual,
                "senial_frenado": frenado_actual,
                "senial_ralenti": ralenti_actual,
                "senial_marcha": marcha_actual,
                "senial_estacionado": estacionado_actual,
                "es_contradictorio_interno": arranque_actual and (marcha_actual or frenado_actual),
            },
            "seniales_heredadas": {
                "senial_arranque": arranque_heredado,
                "senial_frenado": frenado_heredado,
                "senial_ralenti": ralenti_heredado,
                "senial_marcha": marcha_heredada,
            },
            "estado_previo": estado.estado_operativo,
        }

        # 3. Detección de Contradicción Operativa Interna en el mensaje actual (Escenario H)
        if arranque_actual and (marcha_actual or frenado_actual):
            metadata["estado_detectado_mensaje_actual"] = EstadoOperativo.ARRANQUE
            return EstadoOperativo.ARRANQUE, True, metadata

        # 4. Prioridad Temporal de Evidencia: Señal Explícita del Mensaje Actual MANDA
        if frenado_actual:
            metadata["estado_detectado_mensaje_actual"] = EstadoOperativo.FRENADO
            return EstadoOperativo.FRENADO, False, metadata
        if marcha_actual:
            metadata["estado_detectado_mensaje_actual"] = EstadoOperativo.MARCHA
            return EstadoOperativo.MARCHA, False, metadata
        if ralenti_actual:
            metadata["estado_detectado_mensaje_actual"] = EstadoOperativo.RALENTI
            return EstadoOperativo.RALENTI, False, metadata
        if arranque_actual:
            metadata["estado_detectado_mensaje_actual"] = EstadoOperativo.ARRANQUE
            return EstadoOperativo.ARRANQUE, False, metadata
        if estacionado_actual:
            metadata["estado_detectado_mensaje_actual"] = EstadoOperativo.ESTACIONADO
            return EstadoOperativo.ESTACIONADO, False, metadata

        # 5. Sin señal actual explícita: conservar señales heredadas
        metadata["estado_detectado_mensaje_actual"] = EstadoOperativo.DESCONOCIDO
        if arranque_heredado:
            return EstadoOperativo.ARRANQUE, False, metadata
        if frenado_heredado:
            return EstadoOperativo.FRENADO, False, metadata
        if ralenti_heredado:
            return EstadoOperativo.RALENTI, False, metadata
        if marcha_heredada:
            return EstadoOperativo.MARCHA, False, metadata

        return EstadoOperativo.DESCONOCIDO, False, metadata
