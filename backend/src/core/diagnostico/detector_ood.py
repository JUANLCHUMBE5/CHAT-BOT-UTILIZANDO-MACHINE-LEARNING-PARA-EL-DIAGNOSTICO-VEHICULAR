"""Detector y abstención segura de síntomas automotrices fuera de catálogo (OOD).

Detecta sistemas y componentes claramente ajenos a las 61 clases canónicas
del Linear SVM de CarBot, evitando diagnósticos forzados y alucinaciones.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional, Tuple


def _normalizar_ood(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto.lower())
    limpio = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return " ".join(limpio.split())


# Patrones de síntomas explícitos del dominio canónico de CarBot (motor, encendido, frenos, carga, etc.)
PATRONES_IN_DOMAIN_FUERTES = [
    r"\b(?:check engine|p0\d{3}|p1\d{3}|p2\d{3}|misfire|falla de cilindro)\b",
    r"\b(?:bujia|bujias|bobina|bobinas|inyector|inyectores|cuerpo de aceleracion|mariposa)\b",
    r"\b(?:tiembla|ratea|cabecea|cascabelea|humo negro|humo blanco|humo azul)\b",
    r"\b(?:alternador|bateria|borne|arrancador|motor de arranque)\b",
    r"\b(?:pastilla|pastillas|disco de freno|discos de freno|bomba de freno|cilindro maestro)\b",
    r"\b(?:termostato|electroventilador|bomba de agua|radiador|refrigerante|recalienta)\b",
    r"\b(?:amortiguador|amortiguadores|trapecio|terminal|rotula|palier|homocinetica)\b",
    r"\b(?:embrague|disco de embrague|collarin|plato opresor)\b",
]


@dataclass(frozen=True)
class DefinicionOOD:
    categoria: str
    patrones_positivos: list[str]
    patrones_negativos: list[str]
    sistema_objetivo: str
    mensaje_abstencion: str
    detalle_tecnico: str


REGLAS_OOD: list[DefinicionOOD] = [
    DefinicionOOD(
        categoria="AIRBAG_SRS_BCM",
        patrones_positivos=[
            r"\b(?:airbag|srs|bolsa de aire|bolsas de aire)\b",
            r"\b(?:cable espiral|cinta reloj|clockspring|cinta del timon)\b",
            r"\bluz (?:roja )?(?:del )?airbag\b",
            r"\btestigo (?:del )?airbag\b",
        ],
        patrones_negativos=[],
        sistema_objetivo="Seguridad Pasiva / Módulo SRS / BCM",
        mensaje_abstencion=(
            "El síntoma corresponde al sistema de seguridad pasiva (Airbag / SRS / Clockspring). "
            "CarBot no tiene módulos de diagnóstico de colisión ni pirotécnicos en su catálogo de 61 clases. "
            "Por seguridad, se debe escanear el módulo SRS y no manipular cables amarillos ni pirotécnicos con multímetro."
        ),
        detalle_tecnico="Sistema de Airbag / SRS fuera de cobertura oficial de 61 clases.",
    ),
    DefinicionOOD(
        categoria="GLP_GNV_CONVERSION",
        patrones_positivos=[
            r"\b(?:conmutador de gas|tanque de (?:glp|gnv)|fase de gas|riel de gas|inyectores de gas)\b",
            r"\b(?:reductor de (?:glp|gnv)|vaporizador de (?:glp|gnv)|calibracion de gas)\b",
            r"\b(?:se regresa|se pasa|cambia|no pasa) solo? a gas(?:olina)?\b",
            r"\bpita (?:el )?conmutador\b",
            r"\b(?:pita|chilla|bip)\b.{0,30}\b(?:llave selectora|conmutador|equipo de gas)\b",
            r"\b(?:llave selectora|llave de gas)\b.{0,30}\b(?:pita|chilla|bip|parpadea|no pasa a gas)\b",
            r"\b(?:auto|carro|vehiculo) a gas glp\b.{0,40}\b(?:no pasa a gas|se queda en gasolina|llave selectora)\b",
            r"\b(?:no pasa a gas|se queda en gasolina)\b",
        ],
        patrones_negativos=[],
        sistema_objetivo="Combustibles Alternativos (GLP / GNV)",
        mensaje_abstencion=(
            "El síntoma corresponde al sistema de conversión a GLP/GNV (reductor, conmutador, mapa o inyección de gas). "
            "CarBot diagnostica sistemas de inyección primaria de gasolina y diésel, no kits de 5ta generación de gas. "
            "Se requiere calibración con la interfaz y software específico de la ECU de gas."
        ),
        detalle_tecnico="Sistema de Gas GLP/GNV fuera de cobertura oficial de 61 clases.",
    ),
    DefinicionOOD(
        categoria="DIRECCION_EPS_ELECTRONICA",
        patrones_positivos=[
            r"\b(?:direccion electroasistida|direccion asistida electrica|direccion eps)\b",
            r"\b(?:timon electrico|volante electrico)\b.{0,30}\b(?:duro|dur[ií]simo|bloqueado|pesado|traba)\b",
            r"\b(?:testigo|luz)\s+(?:del?\s+)?eps\b",
            r"\b(?:sensor de par|sensor de torque|motor del timon|acoplador elastico del timon|estrellita del timon)\b",
        ],
        patrones_negativos=[
            r"\b(?:cremallera hidraulica|liquido de direccion|bomba de direccion)\b",
        ],
        sistema_objetivo="Dirección Electroasistida (EPS)",
        mensaje_abstencion=(
            "El síntoma corresponde a la dirección electroasistida (EPS / columna o sensor de par). "
            "El catálogo actual de CarBot cubre cremalleras mecánicas e hidráulicas, pero no la electrónica EPS ni su motor de columna. "
            "Se requiere escanear el módulo EPS y verificar alimentación de alta corriente (fusible 60A/80A) y sensor de par."
        ),
        detalle_tecnico="Dirección Electrónica EPS fuera de cobertura oficial de 61 clases.",
    ),
    DefinicionOOD(
        categoria="RED_CAN_INMOVILIZADOR_CENTRAL",
        patrones_positivos=[
            r"\b(?:red can|can bus|can-h|can-l|linea can)\b.{0,40}\b(?:en corto|abierta|sin comunicacion|caida)\b",
            r"\b(?:no hay|sin)\s+comunicacion\s+(?:can|con ecm|con bcm|con tcm)\b",
            r"\b(?:candadito|candado|llave)\s+(?:parpadea|destella|titila)\b|\b(?:parpadea|destella|titila)\s+(?:el\s+)?(?:candadito|candado|llave)\b",
            r"\bchip de la llave\b.{0,30}\b(?:desprogramado|no reconoce)\b",
        ],
        patrones_negativos=[],
        sistema_objetivo="Redes Multiplexadas CAN Bus / Inmovilizador Central",
        mensaje_abstencion=(
            "El síntoma corresponde a una pérdida de comunicación en el bus de datos CAN o desincronización del inmovilizador (IMMO). "
            "CarBot no incluye en sus 61 clases el diagnóstico topológico de redes ni transponders de llave. "
            "Se requiere verificar resistencia de 60 Ω entre pines 6 y 14 del DLC y estado de autorización de arranque en escáner."
        ),
        detalle_tecnico="Redes CAN e Inmovilizador fuera de cobertura oficial de 61 clases.",
    ),
    DefinicionOOD(
        categoria="HVAC_COMPUERTA_MEZCLA_CALEFACCION",
        patrones_positivos=[
            r"\b(?:compuerta de mezcla|actuador de mezcla|blend door|servomotor de mezcla)\b",
            r"\bclac[- ]clac\b.{0,40}\b(?:detras del tablero|debajo del tablero)\b.{0,40}\b(?:caliente|frio|temperatura)\b",
            r"\b(?:termistor|sensor)\s+(?:del\s+)?evaporador\b",
            r"\bclimatizador bizona\b.{0,60}\b(?:caliente.*frio|frio.*caliente|compuerta)\b",
            r"\bcompuerta\b.{0,30}\b(?:tac[- ]tac|trabada|atascada)\b",
            r"\b(?:aire caliente por (?:el )?(?:lado del )?piloto|frio por (?:el )?copiloto)\b",
        ],
        patrones_negativos=[
            r"\b(?:compresor|r134a|gas refrigerante|presion de alta|presion de baja)\b",
        ],
        sistema_objetivo="Climatización / Compuertas y Distribución de Aire (HVAC)",
        mensaje_abstencion=(
            "El síntoma corresponde al mecanismo de compuertas de mezcla/distribución o servomotores HVAC detrás del tablero. "
            "El catálogo oficial de A/C de CarBot cubre el circuito de refrigeración (compresor y fugas), no actuadores de compuerta. "
            "Se recomienda realizar calibración de actuadores de compuerta o inspección física del servomotor de mezcla."
        ),
        detalle_tecnico="Compuertas y actuadores de mezcla HVAC fuera de cobertura oficial de 61 clases.",
    ),
    DefinicionOOD(
        categoria="TRANSMISION_NO_CUBIERTA_CONVERTIDOR",
        patrones_positivos=[
            r"\b(?:convertidor de par|convertidor de torque)\b.{0,30}\b(?:patina|resbala|falla|vibracion)\b",
            r"\bmecatronica\s+dsg\b.{0,40}\b(?:acumulador|presion hidraulica|reventado)\b",
            r"\b(?:caja|transmision)\s+(?:automatica\s+)?dsg\b",
            r"\b(?:caja|transmision)\s+de\s+doble\s+embrague\s+dsg\b",
            r"\b(?:caja|transmision)\s+(?:automatica\s+)?cvt\b",
        ],
        patrones_negativos=[],
        sistema_objetivo="Transmisión Hidráulica Automática / Mecatrónica DSG",
        mensaje_abstencion=(
            "El síntoma corresponde a la hidromecánica interna de transmisión (convertidor de par o acumulador de mecatrónica DSG). "
            "Las clases oficiales de transmisión cubren embrague manual y sobrecalentamiento/solenoides generales, no reconstrucción de mecatrónica ni convertidor. "
            "Se requiere lectura de datos en vivo de presiones hidráulicas y recorrido de horquillas con escáner."
        ),
        detalle_tecnico="Transmisiones específicas (convertidor/mecatrónica) fuera de cobertura oficial de 61 clases.",
    ),
]


def detectar_sintoma_fuera_de_catalogo(texto: str) -> Tuple[bool, Optional[DefinicionOOD]]:
    """Determina deterministamente si un síntoma pertenece a un sistema automotriz OOD.
    
    Si el mensaje es un caso mixto o una transición que aporta evidencia concreta
    de un síntoma canónico de las 61 clases (ej. 'pero también el motor tiembla con P0300'),
    se prioriza el diagnóstico in-domain para no bloquear la consulta del mecánico.
    """
    if not texto or not isinstance(texto, str):
        return False, None

    texto_norm = _normalizar_ood(texto)

    # Si hay una queja canónica fuerte con síntomas mecánicos precisos en el mismo mensaje,
    # el sistema debe permitir que el clasificador canónico evalúe el síntoma válido.
    tiene_in_domain_fuerte = any(re.search(pat, texto_norm) for pat in PATRONES_IN_DOMAIN_FUERTES)

    for regla in REGLAS_OOD:
        coincide_pos = any(re.search(pat, texto_norm) for pat in regla.patrones_positivos)
        if coincide_pos:
            coincide_neg = any(re.search(pat, texto_norm) for pat in regla.patrones_negativos)
            if not coincide_neg:
                # Si coincide con OOD pero también contiene un síntoma in-domain fuerte,
                # verificamos si la mención OOD es meramente incidental/transición (ej. 'entendido lo del airbag pero...')
                if tiene_in_domain_fuerte and re.search(r"\b(?:pero|ademas|tambien|aparte)\b", texto_norm):
                    continue
                return True, regla

    return False, None
