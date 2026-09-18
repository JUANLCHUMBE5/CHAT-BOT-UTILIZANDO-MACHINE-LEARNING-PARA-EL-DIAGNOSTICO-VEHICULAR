"""Módulo de detección de polaridad clínica: hechos presentes, ausentes-negados y no revisados (Fase 9.14)."""

from __future__ import annotations

import re
from typing import List, Tuple

from src.core.conversacion.models import FactState

# Catálogo de síntomas con patrones positivos y patrones de negación explícita
DEFINICIONES_SINTOMAS: List[Tuple[str, re.Pattern, re.Pattern]] = [
    (
        "vibración",
        re.compile(r"\b(vibraci[oó]n|vibracion|tiembla|zapatea|vibra)\b", re.IGNORECASE),
        re.compile(
            r"\b(no\s+(?:se\s+|le\s+|me\s+)?(?:siente\s+)?(?:vibra|tiembla|zapatea|vibraci[oó]n)|"
            r"al\s+frenar\s+no\s+vibra|sin\s+vibraci[oó]n|cero\s+vibraci[oó]n)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "apagado de motor",
        re.compile(r"\b(apagado\s+de\s+motor|se\s+apaga|se\s+me\s+apaga|se\s+muere)\b", re.IGNORECASE),
        re.compile(r"\b(no\s+(?:se\s+)?(?:apaga|muere|apago|apag[oó]|apagado\s+de\s+motor))\b", re.IGNORECASE),
    ),
    (
        "pérdida de potencia",
        re.compile(
            r"\b(p[eé]rdida\s+de\s+potencia|no\s+jala|se\s+chupa|pierde\s+fuerza|"
            r"perdi[aáoó]\s+fuerza|sin\s+fuerza|se\s+ahoga|chanchea|se\s+aguanta|est[aá]\s+chancho)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\b(no\s+(?:pierde\s+fuerza|pierde\s+potencia|se\s+ahoga|se\s+chupa|se\s+aguanta)|fuerza\s+normal)\b", re.IGNORECASE),
    ),
    (
        "sobrecalentamiento",
        re.compile(
            r"\b(sobrecalentamiento|hierve|levanta\s+temperatura|se\s+calienta|"
            r"temperatura\s+(?:del\s+motor\s+)?(?:est[aá]\s+)?subiendo|"
            r"temperatura\s+sube|temperatura\s+(?:m[aá]s\s+de\s+lo\s+normal|elevada|alta))\b",
            re.IGNORECASE,
        ),
        re.compile(r"\b(no\s+(?:se\s+)?(?:calienta|hierve|levanta\s+temperatura)|temperatura\s+normal)\b", re.IGNORECASE),
    ),
    (
        "fuga de refrigerante",
        re.compile(
            r"\b(fuga\s+(?:visible\s+)?(?:de\s+)?(?:l[ií]quido\s+)?refrigerante|"
            r"fuga\s+(?:de\s+)?(?:l[ií]quido|agua)|bota\s+(?:el\s+)?(?:agua|refrigerante)|"
            r"gotea\s+(?:agua|refrigerante|l[ií]quido)|pierde\s+(?:agua|refrigerante|l[ií]quido)|"
            r"fuga\s+visible|fuga\s+proviene|manguera\s+(?:inferior|superior)?\s*(?:del\s+)?radiador)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(no\s+(?:hay|veo|presenta|tiene)\s+fuga|no\s+bota\s+(?:agua|refrigerante)|sin\s+fugas?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "funcionamiento irregular / misfire",
        re.compile(r"\b(misfire|ratea|cabecea|tironea|jalonea)\b", re.IGNORECASE),
        re.compile(r"\b(no\s+(?:ratea|cabecea|tironea|jalonea|falla\s+el\s+motor))\b", re.IGNORECASE),
    ),
    (
        "humo blanco / ebullición refrigerante",
        re.compile(r"\b(humo\s+blanco|burbujea)\b", re.IGNORECASE),
        re.compile(r"\b(no\s+(?:bota|echa|sale)?\s*humo\s+blanco|no\s+burbujea)\b", re.IGNORECASE),
    ),
    (
        "chasquido de arranque clac",
        re.compile(r"\b(clac|chasquido|tac\s+seco|clic)\b", re.IGNORECASE),
        re.compile(r"\b(no\s+hace\s+(?:ning[uú]n\s+)?(?:clic|clac|chasquido))\b", re.IGNORECASE),
    ),
    (
        "alto consumo de combustible",
        re.compile(r"\b(consume\s+mucha\s+(?:gasolina|nafta)|gasta\s+mucha|alto\s+consumo|consumo\s+excesivo)\b", re.IGNORECASE),
        re.compile(r"\b(consumo\s+normal|no\s+consume\s+de\s+m[aá]s)\b", re.IGNORECASE),
    ),
    (
        "ruido anómalo",
        re.compile(
            r"\b(suena\s+feo|ruido\s+extr[aá]ño|traqueteo|traquetea|sonajero|golpeteo|chillido|chirrido|zumbido|"
            r"zumba|golpe(?:\s+en|\s+seco|\s+delantero)?|golpea|crujido|a[uú]lla|sonido)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(no\s+(?:hace|se\s+oye|se\s+escucha|hay)\s+(?:ning[uú]n\s+)?(?:ruido|golpeteo|chillido|sonido)|"
            r"no\s+hace\s+ruido\s+al\s+girar)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "anomalía en frenos",
        re.compile(r"\b(frena\s+raro|frenos\s+raros|frena\s+mal|freno\s+raro|anomal[ií]a\s+en\s+frenos)\b", re.IGNORECASE),
        re.compile(r"\b(frena\s+bien|frena\s+normal|no\s+frena\s+mal)\b", re.IGNORECASE),
    ),
    (
        "patinado de transmisión / embrague",
        re.compile(r"\b(patina\s+el\s+embrague|embrague\s+patina|caja\s+patina|patina\s+la\s+marcha)\b", re.IGNORECASE),
        re.compile(r"\b(no\s+patina|sin\s+patinar|no\s+patina\s+el\s+embrague)\b", re.IGNORECASE),
    ),
    (
        "olor a combustible",
        re.compile(r"\b(olor\s+a\s+(?:gasolina|nafta|combustible|gas))\b", re.IGNORECASE),
        re.compile(r"\b(no\s+huele\s+a\s+(?:gasolina|nafta|combustible|gas))\b", re.IGNORECASE),
    ),
    (
        "testigo check engine",
        re.compile(r"\b(testigo\s+prendido|check\s+engine\s+encendido|luz\s+en\s+el\s+tablero)\b", re.IGNORECASE),
        re.compile(
            r"\b(no\s+(?:aparece|hay|se\s+enciende|se\s+prende|prende)\s+(?:ninguna?\s+)?(?:luz|testigo|check|aviso)(?:\s+en\s+el\s+tablero)?|"
            r"sin\s+luces?\s+de\s+advertencia|ninguna\s+luz\s+de\s+advertencia)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "falla de climatización / aire acondicionado no enfría",
        re.compile(
            r"\b(no\s+enfr[ií]a|enfr[ií]a\s+(?:poco|nada|casi\s+nada)|deja\s+de\s+enfriar|"
            r"solo\s+enfr[ií]a|enfr[ií]a\s+(?:solo|cuando)|"
            r"sale\s+aire\s+(?:caliente|tibio|ambiente|a\s+temperatura\s+ambiente)|"
            r"sin\s+gas(?:\s+r134a)?|falta\s+(?:de\s+)?gas\s+(?:al\s+aire|r134a)|"
            r"compresor\s+(?:no\s+entra|no\s+acopla|no\s+pega|no\s+arranca|no\s+activa)|"
            r"clima\s+(?:no\s+enfr[ií]a|calienta|no\s+sopla\s+fr[ií]o)|"
            r"aire\s+(?:caliente|tibio|no\s+tira\s+fr[ií]o)|"
            r"fuga\s+de\s+gas\s+(?:r134a|del\s+aire))\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(aire\s+(?:acondicionado\s+)?enfr[ií]a\s+bien|clima\s+enfr[ií]a\s+bien|enfr[ií]a\s+normal|"
            r"no\s+falla\s+el\s+aire|aire\s+normal)\b",
            re.IGNORECASE,
        ),
    ),
]



class DetectorPolaridad:
    """Extrae polaridad clínica diferenciando evidencia positiva, negativa y no revisada."""

    @staticmethod
    def es_condicion_negada(condicion_regex: str, texto: str) -> bool:
        """Determina si la condición aparece subordinada inmediatamente a una negación."""
        for m in re.finditer(condicion_regex, texto, re.IGNORECASE):
            resto = texto[m.end():]
            if re.match(r"^\s*,?\s*no\b", resto, re.IGNORECASE):
                return True
        return False

    @classmethod
    def extraer_sintomas(cls, texto: str) -> List[Tuple[str, str, FactState]]:
        """
        Retorna lista de (campo, valor, FactState), donde FactState puede ser
        CONFIRMADO (presente) o AUSENTE_NEGADO (ausente por afirmación del usuario).
        """
        resultados: List[Tuple[str, str, FactState]] = []
        txt_l = texto.lower()

        for nombre_sintoma, pat_pos, pat_neg in DEFINICIONES_SINTOMAS:
            m_neg = pat_neg.search(txt_l)
            m_pos = pat_pos.search(txt_l)

            if m_neg:
                # Comprobar si además hay una mención positiva genuina fuera del ámbito de la negación
                hay_positivo_genuino = False
                if m_pos:
                    neg_start, neg_end = m_neg.start(), m_neg.end()
                    for m in pat_pos.finditer(txt_l):
                        if m.end() <= neg_start or m.start() >= neg_end + 15:
                            hay_positivo_genuino = True
                            break

                campo = f"sintoma_{nombre_sintoma.replace(' ', '_').replace('/', '_')}"
                if hay_positivo_genuino:
                    resultados.append((campo, nombre_sintoma, FactState.CONFIRMADO))
                else:
                    resultados.append((campo, nombre_sintoma, FactState.AUSENTE_NEGADO))
            elif m_pos:
                campo = f"sintoma_{nombre_sintoma.replace(' ', '_').replace('/', '_')}"
                resultados.append((campo, nombre_sintoma, FactState.CONFIRMADO))

        if re.search(r"\btemperatura\s+(?:del\s+motor\s+)?empieza\s+a\s+subir\b", txt_l):
            resultados.append(("sintoma_sobrecalentamiento", "sobrecalentamiento", FactState.CONFIRMADO))

        if re.search(
            r"\bperdiendo\s+(?:agua|refrigerante|l[iÃ­]quido|l.quido)(?:\s+refrigerante)?\b",
            txt_l,
        ):
            resultados.append(("sintoma_fuga_de_refrigerante", "fuga de refrigerante", FactState.CONFIRMADO))

        return resultados

    @staticmethod
    def _normalizar_sin_tildes(s: str) -> str:
        import unicodedata
        nfkd = unicodedata.normalize("NFD", s)
        return "".join(c for c in nfkd if unicodedata.category(c) != "Mn").lower()

    @classmethod
    def extraer_componentes_no_revisados(cls, texto: str) -> List[Tuple[str, str]]:
        """Identifica componentes o subsistemas que el usuario afirma NO haber revisado aún."""
        resultados: List[Tuple[str, str]] = []
        txt_l = texto.lower()
        txt_sin_tildes = cls._normalizar_sin_tildes(texto)

        patron_no_rev = re.compile(
            r"\b(?:todav[ií]a\s+no|a[uú]n\s+no|no)\s+(?:he|se\s+ha|hemos|se\s+han|han)?\s*"
            r"(?:revisado|revis[eé]|revisamos|chequeado|chequ[eé]|checado|comprobado|comprob[eé]|mirado|inspeccionado|inspeccion[eé]|medido|med[ií]|tocado|visto)\b",
            re.IGNORECASE,
        )
        if not patron_no_rev.search(txt_l):
            return resultados

        piezas = (
            ("suspension", "suspensión", "suspension"),
            ("amortiguador", "amortiguadores", "amortiguadores"),
            ("rotula", "rótulas", "rotulas"),
            ("freno", "frenos", "frenos"),
            ("bateria", "batería", "bateria"),
            ("alternador", "alternador", "alternador"),
            ("arranque", "motor de arranque", "arranque"),
            ("bujia", "bujías", "bujias"),
            ("bobina", "bobinas", "bobinas"),
            ("caja", "caja de cambios", "caja"),
            ("atf", "aceite ATF", "atf"),
            ("bomba", "bomba de combustible", "bomba"),
            ("combustible", "sistema de combustible", "sistema_combustible"),
            ("inyector", "inyectores", "inyectores"),
            ("fusible", "fusibles", "fusibles"),
            ("presion", "presión de combustible", "presion"),
            ("escaner", "escáner OBD-II", "escaner"),
            ("scanner", "escáner OBD-II", "escaner"),
            ("codigo", "códigos DTC", "codigos_dtc"),
        )
        detecto = False
        for k_p, nombre_p, campo_p in piezas:
            if k_p in txt_sin_tildes:
                resultados.append((f"revision_{campo_p}", f"{nombre_p} no revisado(a)"))
                detecto = True

        if not detecto and re.search(r"\b(nada|ning[uú]n\s+componente)\b", txt_l):
            resultados.append(("revision_previa", "ninguna revisión previa"))

        return resultados

    @staticmethod
    def extraer_sistemas_normales(texto: str) -> List[Tuple[str, str]]:
        """Identifica declaraciones explícitas de funcionamiento normal."""
        resultados: List[Tuple[str, str]] = []
        txt_l = texto.lower()

        patron = re.compile(
            r"\b(?:el\s+)?(motor|caja|transmisi[oó]n|frenos?|direcci[oó]n|alternador|aire|clima)\s+"
            r"(?:funciona|anda|marcha|responde|est[aá])\s+(?:normal|bien|perfecto|sin\s+problemas?)\b",
            re.IGNORECASE,
        )
        for m in patron.finditer(txt_l):
            sis = m.group(1).lower()
            canon = "motor" if "motor" in sis else ("transmisión" if "trans" in sis or "caja" in sis else sis)
            resultados.append((f"funcionamiento_{canon}", f"{canon} funciona normal"))

        if re.search(r"\bhacia\s+adelante\s+(?:los\s+cambios\s+)?se\s+sienten\s+normales\b", txt_l):
            resultados.append(("cambios_adelante", "cambios hacia adelante normales"))

        return resultados
