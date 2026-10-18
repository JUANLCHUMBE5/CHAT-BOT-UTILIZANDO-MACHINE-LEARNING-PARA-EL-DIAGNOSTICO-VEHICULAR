"""Detección de correcciones explícitas y registro de rechazos conversacionales."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Tuple

from src.core.conversacion.models import (
    ConversationState,
    FactState,
    FactType,
    QuestionIntent,
)

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


def detectar_correcciones(texto: str) -> List[Tuple[str, str, str, FactType]]:
    """Detecta frases correctivas como 'me equivoqué, es caliente', etc."""
    correcciones: List[Tuple[str, str, str, FactType]] = []
    if not texto:
        return correcciones
    texto_l = texto.lower()
    if not PATRON_CORRECCION_EXPLICITA.search(texto_l):
        return correcciones

    if re.search(
        r"\b(s[ií]\s+arranca\s*[, ]+(?:pero\s+)?se\s+apaga|arranca\s+y\s+se\s+apaga|arranca\s*[, ]+(?:pero\s+)?(?:luego\s+)?se\s+apaga)\b",
        texto_l,
    ) or (
        re.search(r"\bno\s+es\s+que\s+no\s+(?:arranque|prenda|encienda)\b", texto_l)
        and re.search(r"\b(?:se\s+)?apaga\b", texto_l)
    ):
        correcciones.append(("sintoma_arranca_y_se_apaga", "arranca y se apaga", "sintoma", FactType.SINTOMA))
        correcciones.append(("sintoma_motor_no_arranca", "ausente", "polaridad", FactType.CONDICION))
        correcciones.append(("motor_arranca", "SI", "condicion", FactType.CONDICION))
        correcciones.append(("estado_operativo", "RALENTI", "condicion", FactType.CONDICION))
    elif re.search(
        r"\b(no\s+es\s+que\s+no\s+(?:arranque|prenda|encienda)|(?:el\s+)?motor\s+arranca\s+(?:bien|al\s+toque|normal|r[aá]pido))\b",
        texto_l,
    ):
        correcciones.append(("sintoma_motor_no_arranca", "ausente", "polaridad", FactType.CONDICION))
        correcciones.append(("motor_arranca", "SI", "condicion", FactType.CONDICION))

    if re.search(r"\b(caliente|en\s+caliente|calent[oó]|calienta|despu[eés]\s+de\s+calentar|ya\s+caliente)\b", texto_l) or re.search(r"\b(?:reci[eén]\s+)?a\s+los\s+\d+\s*minutos\b", texto_l):
        correcciones.append(("temperatura", "caliente", "temperatura", FactType.CONDICION))
    elif re.search(r"\b(fr[ií]o|en\s+fr[ií]o|por\s+la\s+mañana)\b", texto_l) and not re.search(
        r"\b(?:en\s+fr[ií]o\s+(?:arranca|prende|funciona|anda)\s+(?:perfecto|bien|normal)|en\s+fr[ií]o\s+no\s+(?:falla|pasa)|no\s+(?:es|falla)\s+en\s+fr[ií]o)\b",
        texto_l,
    ):
        correcciones.append(("temperatura", "frío", "temperatura", FactType.CONDICION))

    if re.search(r"\b(detenido\s+en\s+ralent[ií]|en\s+ralent[ií]|parado\s+en\s+el\s+sem[aá]foro)\b", texto_l):
        correcciones.append(("condicion_operacion", "detenido en ralentí", "condicion", FactType.CONDICION))
        correcciones.append(("estado_operativo", "RALENTI", "condicion", FactType.CONDICION))
    elif re.search(r"\b((?:tambi[eén]\s+)?(?:ocurre\s+|pasa\s+)?acelerando|al\s+acelerar(?:\s+(?:en\s+carretera|bajo\s+carga))?|en\s+carretera\s+a\s+alta\s+velocidad|en\s+marcha)\b", texto_l):
        correcciones.append(("condicion_operacion", "al acelerar en marcha", "condicion", FactType.CONDICION))
        correcciones.append(("estado_operativo", "MARCHA", "condicion", FactType.CONDICION))

    if re.search(r"\b(no\s+(?:tiene|hay|prende|est[aá]\s+encendido)\s+(?:el\s+)?check|check\s+(?:engine\s+)?apagado|sin\s+check)\b", texto_l):
        correcciones.append(("sintoma_testigo_check_engine", "ausente", "polaridad", FactType.CONDICION))
    elif re.search(r"\b(s[ií]\s+(?:tiene|prende)\s+check|check\s+(?:engine\s+)?(?:s[ií]\s+)?est[aá]\s+encendido)\b", texto_l):
        correcciones.append(("sintoma_testigo_check_engine", "testigo check engine", "sintoma", FactType.SINTOMA))

    if re.search(
        r"\b(?:demora|tarda)\s+(?:(?:mucho|bastante|demasiado|(?:unos?\s+)?(?:\d+|un|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\s+segundos?)\s+)?"
        r"(?:en\s+)?(?:arrancar|prender|encender)\b|\b(?:cuesta\s+prender|le\s+cuesta\s+encender|demora\s+por\s+las\s+mañanas)\b",
        texto_l,
    ):
        correcciones.append(("sintoma_demora_arranque", "demora en arrancar", "sintoma", FactType.SINTOMA))
        correcciones.append(("estado_operativo", "ARRANQUE", "condicion", FactType.CONDICION))
    if re.search(
        r"\b(?:no\s+(?:presenta|tiene|muestra)\s+|sin\s+)(?:p[eéd]rdida\s+de\s+potencia|p[eéd]rdida\s+de\s+fuerza)\b",
        texto_l,
    ):
        correcciones.append(("sintoma_pérdida_de_potencia", "ausente", "polaridad", FactType.SINTOMA))
    return correcciones


def registrar_rechazos_explicitos(estado: ConversationState, texto: str) -> List[Dict[str, Any]]:
    """Guarda rechazos conversacionales sin convertirlos en fallas físicamente confirmadas."""
    normalizado = "".join(
        c for c in unicodedata.normalize("NFD", (texto or "").casefold())
        if unicodedata.category(c) != "Mn"
    )
    componentes = (
        ("bobina", r"\b(?:bobinas?|coil(?:s|\s+pack)?)\b"),
        ("bujia_precalentamiento", r"\b(?:bujias?\s+(?:de\s+)?precalentamiento|bujias?\s+incandescentes?|calentadores?|glow\s*plugs?)\b"),
        ("bujia", r"\b(?:bujias?|spark\s+plugs?)(?!\s+(?:de\s+)?precalentamiento|\s+incandesc)\b"),
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
        r"ya\s+(?:la|lo|las|los)?\s*revis(?:e|aron)|se\s+reviso\s+y\s+salio\s+normal|"
        r"da\s+buena\s+chispa|chispa\s+buena|presion\s+buena|buena\s+presion|"
        r"manda\s+buena\s+presion|inyecta\s+bien|pulso\s+bueno)\b"
    )
    reemplazo_nuevo = re.compile(
        r"\b(?:cambi[eé]\s+(?:las?\s+|los?\s+)?|cambi[eé]\s+nuev[oa]s?|son\s+nuev[oa]s?|puse\s+nuev[oa]s?|"
        r"estan\s+nuev[oa]s?|recien\s+cambiad[oa]s?|nuev[oa]s?\s+originales?)\b"
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
        clausulas = re.split(r"[.;,!?]|\bpero\b", normalizado)
        texto_componente = " ".join(c for c in clausulas if re.search(patron, c))
        if not texto_componente and familia in componentes_por_contexto:
            texto_componente = normalizado
        es_nuevo = bool(reemplazo_nuevo.search(texto_componente))
        es_comprobado = bool(normalidad.search(texto_componente))
        rechazo_explicito = bool(
            re.search(
                r"\b(?:no\s+(?:es|son)|descart[ea]|no\s+corresponde|no\s+falla|sigue\s+(?:igual|igualita)|"
                r"la\s+falla\s+sigue|persiste)\b",
                texto_componente,
            )
            or es_comprobado
        )

        if es_nuevo:
            h_nuevo = estado.registrar_hecho(
                campo=f"componente_reemplazado_{familia}",
                valor="componente reemplazado nuevo; no insistir como causa inicial sin evidencia funcional",
                categoria="componente_reemplazado",
                estado=FactState.CONFIRMADO,
                texto_crudo=texto,
                tipo=FactType.CONDICION,
            )
            salida.append(h_nuevo.to_dict())

        if not rechazo_explicito:
            continue
        if re.search(r"\bno\s+(?:lo\s+|la\s+)?(?:revise|probe|medi|comprobe|descarte)\b", texto_componente):
            continue

        if not es_nuevo or re.search(r"\b(?:descart[ea]|no\s+(?:es|son))\b", texto_componente):
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

        if es_comprobado:
            h_comp = estado.registrar_hecho(
                campo=f"componente_comprobado_{familia}",
                valor="componente comprobado físicamente en funcionamiento normal",
                categoria="verificacion_fisica",
                estado=FactState.CONFIRMADO,
                texto_crudo=texto,
                tipo=FactType.CONDICION,
            )
            salida.append(h_comp.to_dict())

    herramientas_no_disp = (
        ("manometro", r"\b(?:man[oó]metro|medidor\s+de\s+presi[oó]n)\b"),
        ("osciloscopio", r"\bosciloscopio\b"),
        ("escaner", r"\b(?:esc[aá]ner|scanner)\b"),
        ("multimetro", r"\b(?:mult[ií]metro|tester)\b"),
        ("vacuometro", r"\bvacu[oó]metro\b"),
        ("reloj_comparador", r"\breloj\s+comparador\b"),
        ("compresimetro", r"\bcompres[ií]metro\b"),
    )
    for h_nom, h_pat in herramientas_no_disp:
        if re.search(h_pat, normalizado) and re.search(
            r"\b(?:no\s+(?:tengo|cuento\s+con|dispongo\s+de|poseo|hay)|sin)\b",
            normalizado,
        ):
            marcador_h = f"herramienta_no_disponible:{h_nom}"
            if marcador_h not in estado.hipotesis_descartadas:
                estado.hipotesis_descartadas.append(marcador_h)
            hecho_h = estado.registrar_hecho(
                campo=f"herramienta_no_disponible_{h_nom}",
                valor=f"El taller no dispone de {h_nom}",
                categoria="recurso_taller",
                estado=FactState.CONFIRMADO,
                texto_crudo=texto,
                tipo=FactType.CONDICION,
            )
            salida.append(hecho_h.to_dict())

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


_registrar_rechazos_explicitos = registrar_rechazos_explicitos
