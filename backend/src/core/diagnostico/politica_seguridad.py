"""Política centralizada de seguridad para respuestas diagnósticas críticas de CarBot."""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional, Tuple


class SeveridadSeguridad(str, Enum):
    """Niveles de severidad de riesgo para la seguridad física y del vehículo."""
    CRITICAL_STOP = "CRITICAL_STOP"          # Peligro de vida / pérdida de frenos / incendio / fundición inminente
    URGENT_INSPECTION = "URGENT_INSPECTION"  # Inspección prioritaria antes de continuar marcha prolongada
    NORMAL_DIAGNOSTIC = "NORMAL_DIAGNOSTIC"  # Diagnóstico técnico estándar de taller


# Patrones deterministas de condiciones críticas
PATRON_FRENO_CRITICO = re.compile(
    r"\b(pedal\s+(?:se\s+fue|se\s+va|llego|llega)\s+al\s+fondo|pedal\s+al\s+piso|"
    r"se\s+queda\s+sin\s+frenos?|sin\s+presi[oó]n\s+de\s+frenos?|pedal\s+sin\s+resistencia|"
    r"fuga\s+(?:grave|severa|importante|abundante)?\s*de\s+l[ií]quido\s+de\s+frenos?|"
    r"charco\s+de\s+l[ií]quido\b.{0,30}\bfreno|"
    r"bomba\s+de\s+freno\s+reventada|freno\s+no\s+responde)\b",
    re.IGNORECASE,
)

PATRON_ACEITE_CRITICO = re.compile(
    r"\b((?:luz\s+(?:roja\s+)?(?:de\s+)?|testigo\s+(?:rojo\s+)?(?:de\s+)?)(?:presi[oó]n\s+de\s+)?aceite\b.{0,50}\b(?:encend|prend|son|suen|ruido|cascabeleo|met[aá]lic|golpete)|"
    r"presi[oó]n\s+de\s+aceite\s+(?:en\s+)?(?:cero|0|baja|nula)|"
    r"sin\s+presi[oó]n\s+de\s+aceite|bomba\s+de\s+aceite\s+rota)\b",
    re.IGNORECASE,
)

PATRON_COMBUSTIBLE_CRITICO = re.compile(
    r"\b(fuga\s+(?:de\s+)?(?:gasolina|nafta|combustible)|gotea\s+(?:gasolina|nafta|combustible)|"
    r"fuga\s+cerca\s+del\s+escape|olor\s+fuert(?:e|emente)\s+a\s+(?:gasolina|nafta|combustible)|"
    r"chorrea\s+gasolina|l[ií]nea\s+de\s+gasolina\s+rota)\b",
    re.IGNORECASE,
)

PATRON_TEMPERATURA_CRITICA = re.compile(
    r"\b(temperatura\s+(?:al\s+m[aá]ximo|en\s+zona\s+roja|al\s+tope|pegada\s+al\s+m[aá]ximo)|"
    r"sale\s+vapor\s+(?:blanco\s+)?(?:del\s+motor|debajo\s+del\s+cap[oó]|por\s+el\s+cap[oó])|hierve\s+el\s+refrigerante|"
    r"sobrecalentamiento\s+(?:extremo|severo)|humo\s+de\s+vapor\s+blanco\s+en\s+vano)\b",
    re.IGNORECASE,
)

PATRON_ALTA_TENSION = re.compile(
    r"\b(alta\s+tensi[oó]n|alto\s+voltaje|aislamiento\s+(?:de\s+)?(?:alto\s+voltaje|alta\s+tensi[oó]n|hv)|"
    r"cable(?:ado)?\s+naranja|bater[ií]a\s+de\s+tracci[oó]n|bater[ií]a\s+hv|inversor\s+igbt|inversor\s+el[eé]ctrico|"
    r"falla\s+de\s+aislamiento\s+el[eé]ctrico|propulsi[oó]n\s+ev)\b",
    re.IGNORECASE,
)


BANNER_FRENO = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: NO CONDUCIR EL VEHÍCULO**\n"
    "Existe riesgo inminente de pérdida total del sistema de frenos por falla hidráulica severa. "
    "Por su seguridad, inmovilice el vehículo de inmediato y solicite traslado en grúa para inspección profesional. "
    "Bajo ninguna circunstancia intente conducir hasta el taller.\n\n"
)

BANNER_ACEITE = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: APAGUE EL MOTOR INMEDIATAMENTE**\n"
    "La presión de aceite en cero o el testigo de aceite encendido con ruidos mecánicos indica falta total de lubricación. "
    "Mantener el motor en marcha provocará fundición o destrucción irreversible de metales internos. "
    "No vuelva a dar arranque hasta verificar el nivel y la presión mecánica.\n\n"
)

BANNER_COMBUSTIBLE = (
    "🔥 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO INMINENTE DE INCENDIO**\n"
    "Fuga activa de combustible detectada. No intente arrancar el motor ni accionar componentes eléctricos. "
    "Mantenga alejadas fuentes de ignición o calor y solicite asistencia técnica profesional en un área ventilada.\n\n"
)

BANNER_TEMPERATURA = (
    "⚠️ **ADVERTENCIA CRÍTICA DE SEGURIDAD: SOBRECALENTAMIENTO SEVERO**\n"
    "Detenga el vehículo en un lugar seguro y apague el motor. "
    "NUNCA intente abrir el tapón del radiador ni del depósito de refrigerante mientras el motor esté caliente: "
    "el líquido presurizado causará quemaduras graves inmediatas.\n\n"
)

BANNER_HV = (
    "⚡ **ADVERTENCIA DE SEGURIDAD: SISTEMA DE ALTA TENSIÓN (EV/HÍBRIDO)**\n"
    "Los sistemas de propulsión eléctrica e híbrida operan con tensiones letales (> 300V DC). "
    "Está estrictamente prohibido que el usuario o personal no capacitado toque, desconecte o manipule cables naranjas, el inversor o la batería de tracción. "
    "La intervención exige derivación obligatoria a un técnico certificado en alta tensión y protocolos normados.\n\n"
)


class PoliticaSeguridad:
    """Capa centralizada de auditoría y aplicación de directivas de seguridad en respuestas."""

    @classmethod
    def evaluar_severidad(
        cls,
        texto_usuario: str,
        diagnostico_ml: str = "",
    ) -> Tuple[SeveridadSeguridad, Optional[str]]:
        """Evalúa si la condición descrita requiere un banner de seguridad crítico."""
        txt_comb = f"{texto_usuario} {diagnostico_ml}".lower()

        if PATRON_FRENO_CRITICO.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_FRENO
        if PATRON_ACEITE_CRITICO.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_ACEITE
        if PATRON_COMBUSTIBLE_CRITICO.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_COMBUSTIBLE
        if PATRON_TEMPERATURA_CRITICA.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_TEMPERATURA
        if PATRON_ALTA_TENSION.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_HV

        return SeveridadSeguridad.NORMAL_DIAGNOSTIC, None

    @classmethod
    def enriquecer_respuesta_seguridad(
        cls,
        respuesta_texto: str,
        texto_usuario: str,
        diagnostico_ml: str = "",
    ) -> str:
        """
        Garantiza que toda respuesta frente a una condición crítica presente
        la advertencia obligatoria al inicio y no contenga instrucciones peligrosas.
        """
        sev, banner = cls.evaluar_severidad(texto_usuario, diagnostico_ml)
        if banner is None:
            return respuesta_texto

        # Si la respuesta ya incluye el banner exacto, no duplicar
        banner_clean = banner.strip()
        if banner_clean in respuesta_texto:
            return respuesta_texto

        # Para alta tensión, sanear posibles invitaciones peligrosas a reparar con guantes
        resp_modificada = respuesta_texto
        if sev == SeveridadSeguridad.CRITICAL_STOP and banner == BANNER_HV:
            # Reemplazar recomendaciones riesgosas de manipulación casera por derivación técnica
            resp_modificada = re.sub(
                r"\b(p[oó]ngase|use)\s+guantes\s+(?:diel[eé]ctricos\s+)?clase\s+0\s+y\s+(?:repare|desarme|revise|manipule|toque)\b",
                "la manipulación con guantes Clase 0 está reservada exclusivamente a técnicos certificados",
                resp_modificada,
                flags=re.IGNORECASE,
            )

        return f"{banner}{resp_modificada}".strip()
