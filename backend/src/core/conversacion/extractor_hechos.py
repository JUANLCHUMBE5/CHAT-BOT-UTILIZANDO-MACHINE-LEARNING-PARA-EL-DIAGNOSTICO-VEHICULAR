"""Extractor de hechos diagnósticos, detección de correcciones, modificadores y reinicio de casos."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Tuple

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
)

PATRONES_REINICIO = [
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
    (re.compile(r"\b(sentra)\b", re.IGNORECASE), "Sentra"),
    (re.compile(r"\b(versa)\b", re.IGNORECASE), "Versa"),
    (re.compile(r"\b(rio)\b", re.IGNORECASE), "Rio"),
    (re.compile(r"\b(civic)\b", re.IGNORECASE), "Civic"),
    (re.compile(r"\b(elantra)\b", re.IGNORECASE), "Elantra"),
    (re.compile(r"\b(picanto)\b", re.IGNORECASE), "Picanto"),
    (re.compile(r"\b(sail)\b", re.IGNORECASE), "Sail"),
    (re.compile(r"\b(gol)\b", re.IGNORECASE), "Gol"),
    (re.compile(r"\b(tucson)\b", re.IGNORECASE), "Tucson"),
    (re.compile(r"\b(sportage)\b", re.IGNORECASE), "Sportage"),
    (re.compile(r"\b(ranger)\b", re.IGNORECASE), "Ranger"),
]

PATRON_DTC = re.compile(r"\b([PBUCpbuc][0-3][0-9A-Fa-f]{3})\b")
PATRON_ANIO = re.compile(r"\b(19[89]\d|20[0-2]\d)\b")
PATRON_MEDICION = re.compile(
    r"\b(\d+(\.\d+)?)\s*(psi|bar|v|volts|voltios|ohm|ohmios|kpa|mm)\b", re.IGNORECASE
)


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
            re.compile(
                r"\b(se\s+calienta|temperatura\s+(?:del\s+motor\s+)?(?:sube|empieza\s+a\s+subir|alta)|"
                r"pierde\s+(?:agua|refrigerante|l[iÃ­]quido)|fuga|gotea|"
                r"no\s+enfr[iÃ­]a|sale\s+aire\s+(?:caliente|tibio)|"
                r"vibra|tiembla|jalonea|tironea|pierde\s+fuerza|no\s+jala|"
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

        if re.search(r"\b(caliente|en\s+caliente)\b", texto_l):
            correcciones.append(("temperatura", "caliente", "temperatura", FactType.CONDICION))
        elif re.search(r"\b(fr[ií]o|en\s+fr[ií]o|por\s+la\s+mañana)\b", texto_l):
            correcciones.append(("temperatura", "frío", "temperatura", FactType.CONDICION))

        if re.search(r"\b(detenido\s+en\s+ralent[ií]|en\s+ralent[ií]|parado\s+en\s+el\s+sem[aá]foro)\b", texto_l):
            correcciones.append(("condicion_operacion", "detenido en ralentí", "condicion", FactType.CONDICION))
        elif re.search(r"\b(al\s+acelerar\s+en\s+carretera|en\s+carretera\s+a\s+alta\s+velocidad)\b", texto_l):
            correcciones.append(("condicion_operacion", "en carretera a velocidad", "condicion", FactType.CONDICION))

        if any(w in texto_l for w in ("demora en arrancar", "demora en encender", "demora al arrancar", "tarda en arrancar", "cuesta prender", "le cuesta encender", "demora por las mañanas")):
            correcciones.append(("sintoma_demora_arranque", "demora en arrancar", "sintoma", FactType.SINTOMA))
            correcciones.append(("estado_operativo", "ARRANQUE", "condicion", FactType.CONDICION))
        return correcciones

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
                h = estado.registrar_hecho(
                    campo=campo,
                    valor=nuevo_val,
                    categoria=cat,
                    estado=FactState.CONFIRMADO,
                    texto_crudo=texto_usuario,
                    tipo=tipo_f,
                )
                hechos_extraidos.append(h.to_dict())

        # 2. Extracción de marca / modelo / año / combustible
        for patron, marca in PATRONES_MARCA:
            if patron.search(texto_usuario):
                if estado.marca and estado.marca != marca:
                    estado.reiniciar()
                    estado.historial_mensajes_usuario.append(texto_usuario)
                    estado.turno_actual = 1
                estado.marca = marca
                h = estado.registrar_hecho("marca", marca, categoria="vehiculo", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())
                break

        m_anio = PATRON_ANIO.search(texto_usuario)
        if m_anio and not estado.anio:
            estado.anio = m_anio.group(1)
            h = estado.registrar_hecho("anio", m_anio.group(1), categoria="vehiculo", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        for patron, mod in PATRONES_MODELO:
            if patron.search(texto_usuario):
                if estado.modelo and estado.modelo != mod:
                    m_prev = estado.marca
                    estado.reiniciar()
                    estado.historial_mensajes_usuario.append(texto_usuario)
                    estado.turno_actual = 1
                    if m_prev:
                        estado.marca = m_prev
                        estado.registrar_hecho("marca", m_prev, categoria="vehiculo", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                estado.modelo = mod
                h = estado.registrar_hecho("modelo", mod, categoria="vehiculo", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())
                break

        for patron, comb in PATRONES_COMBUSTIBLE:
            if patron.search(texto_usuario) and not estado.combustible:
                estado.combustible = comb
                h = estado.registrar_hecho("combustible", comb, categoria="vehiculo", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h.to_dict())
                break

        # 3. Extracción de DTC (DTC_OBSERVADO explícito)
        for dtc in PATRON_DTC.findall(texto_usuario):
            dtc_canonico = dtc.upper()
            campo = f"dtc_{dtc_canonico}"
            estado.dtc_status = DtcStatus.DTC_OBSERVADO
            h = estado.registrar_hecho(campo, dtc_canonico, categoria="dtc", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        # 4. Extracción de mediciones físicas
        m_med = PATRON_MEDICION.search(texto_usuario)
        if m_med:
            med_val = m_med.group(0).lower()
            h = estado.registrar_hecho("medicion", med_val, categoria="medicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        # 5. Componentes revisados o reemplazados
        texto_l = texto_usuario.lower()
        if any(c in texto_l for c in ("ya cambie", "ya cambié", "ya las cambié", "ya las cambie", "ya los cambié", "ya los cambie", "ya le cambié", "ya se cambiaron", "ya se cambió", "nuevo", "nueva", "cambiamos", "recién cambiado", "recien cambiado", "recién cambié")):
            for pieza in ("bujias", "bujías", "bobinas", "bobina", "bomba", "filtro", "termostato", "pastillas", "aceite"):
                if pieza in texto_l:
                    canon = "bujías" if "buj" in pieza else ("bobinas" if "bobin" in pieza else pieza)
                    h = estado.registrar_hecho(f"reemplazado_{canon}", f"{canon} reemplazado(a)", categoria="antecedente", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                    hechos_extraidos.append(h.to_dict())

        if any(c in texto_l for c in ("ya revise", "ya revisé", "probe", "probé", "intercambie", "intercambié", "descarte", "descarté")):
            for pieza in ("bujias", "bujías", "bobinas", "bobina", "bomba", "fusible", "presion", "presión", "compresion", "compresión"):
                if pieza in texto_l:
                    canon = "bujías" if "buj" in pieza else ("bobinas" if "bobin" in pieza else pieza)
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

        if re.search(r"\b(no\s+(?:tengo|cuento|dispongo)|sin\s+)\b", texto_l):
            if "escaner" in texto_l or "escáner" in texto_l or "scanner" in texto_l:
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

        if re.search(r"\b(luces?\s+prendidas?|luces?\s+altas?|prendo\s+las\s+luces?|con\s+luces?|luces?\s+(?:se\s+ponen\s+)?tenues?|bajan?\s+las\s+luces?|luces?\s+bajas?)\b", texto_l):
            luces_tenues = bool(re.search(r"\b(tenues?|bajan?\s+las\s+luces?|luces?\s+bajas?)\b", texto_l))
            valor_luces = "luces tenues" if luces_tenues else "luces encendidas"
            h = estado.registrar_hecho("modificador_luces", valor_luces, categoria="modificador", texto_crudo=texto_usuario, tipo=FactType.MODIFICADOR)
            hechos_extraidos.append(h.to_dict())

        # 7. Extracción de condiciones operacionales lingüísticas
        ling = extraer_hechos_linguisticos(texto_usuario)
        for k, v in ling.items():
            cat = "temperatura" if k == "temperatura" else ("cambio_accion" if k == "evolucion_accion" else "condicion")
            h = estado.registrar_hecho(k, v, categoria=cat, texto_crudo=texto_usuario, tipo=FactType.CONDICION)
            hechos_extraidos.append(h.to_dict())

        # 7.1 Hechos de transmision: el estado operativo puede seguir en MARCHA,
        # pero la queja principal pertenecer a la caja automatica.
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
        if PATRON_NO_ARRANCA.search(texto_usuario):
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
            h = estado.registrar_hecho(
                campo_s, val_s, categoria="sintoma", estado=estado_s,
                texto_crudo=texto_usuario, tipo=FactType.SINTOMA,
            )
            hechos_extraidos.append(h.to_dict())

        if PATRON_NO_ARRANCA.search(texto_normalizado.lower()) and not estado.obtener_hecho("sintoma_motor_no_arranca"):
            h = estado.registrar_hecho("sintoma_motor_no_arranca", "motor no arranca", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
            hechos_extraidos.append(h.to_dict())

        if PATRON_DEMORA_ARRANQUE.search(texto_usuario):
            h = estado.registrar_hecho("sintoma_demora_arranque", "demora en arrancar", categoria="sintoma", texto_crudo=texto_usuario, tipo=FactType.SINTOMA)
            hechos_extraidos.append(h.to_dict())
            if not estado.obtener_hecho("condicion_operacion"):
                h_c = estado.registrar_hecho("condicion_operacion", "al dar arranque en frío", categoria="condicion", texto_crudo=texto_usuario, tipo=FactType.CONDICION)
                hechos_extraidos.append(h_c.to_dict())

        # 10. Inferencia contextual de EstadoOperativo y detección de contradicciones (Fase 9.6 y 9.10)
        res_op = cls.inferir_estado_operativo(estado, texto_usuario)
        nuevo_estado_op, es_conflicto = res_op[0], res_op[1]
        estado.estado_operativo = nuevo_estado_op
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
        arranque_actual = bool(
            PATRON_NO_ARRANCA.search(texto_l)
            or PATRON_GIRO_LLAVE.search(texto_l)
            or PATRON_DEMORA_ARRANQUE.search(texto_l)
        )
        frenado_actual = bool(
            re.search(r"\b(al\s+frenar|frenando|cuando\s+freno|pedal\s+de\s+freno|al\s+pisar\s+el\s+freno)\b", texto_l)
            and not DetectorPolaridad.es_condicion_negada(r"\b(al\s+frenar|frenando|cuando\s+freno|al\s+pisar\s+el\s+freno)\b", texto_l)
        )
        ralenti_actual = bool(
            re.search(r"\b(en\s+ralent[ií]|en\s+el\s+sem[aá]foro|detenido(\s+en\s+ralent[ií])?|en\s+neutro|parado\s+esperando)\b", texto_l)
            and not DetectorPolaridad.es_condicion_negada(r"\b(en\s+ralent[ií]|detenido|en\s+neutro)\b", texto_l)
        )
        marcha_actual = bool(
            re.search(
                r"\b(en\s+carretera|a\s+\d+\s*km/h|circulando|en\s+marcha|andando|anda|al\s+andar|a\s+velocidad|"
                r"acelerando\s+con\s+fuerza|voy\s+a\s+\d+|cuando\s+voy\s+a|manejando|al\s+manejar|"
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
