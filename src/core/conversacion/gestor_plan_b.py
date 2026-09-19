"""Módulo de gestión de herramientas, Plan B sin herramientas y prevención de bucles (Fase 9.11).

Centraliza la detección de indisponibilidad de instrumental técnico, la selección
de alternativas sensoriales (visuales, acústicas, táctiles) y el avance ordenado
hacia la derivación profesional sin repetir pruebas inviables.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.core.conversacion.models import (
    ConversationState,
    FactState,
    FactType,
    QuestionIntent,
)


@dataclass(frozen=True)
class HerramientaAutomotriz:
    clave: str
    nombre_canonico: str
    terminos: Tuple[str, ...]
    patron_mencion: re.Pattern


CATALOGO_HERRAMIENTAS: Dict[str, HerramientaAutomotriz] = {
    "multimetro": HerramientaAutomotriz(
        clave="multimetro",
        nombre_canonico="multímetro / tester automotriz",
        terminos=("multímetro", "multimetro", "tester", "voltímetro", "voltimetro"),
        patron_mencion=re.compile(r"\b(mult[ií]metro|tester|volt[ií]metro)\b", re.IGNORECASE),
    ),
    "manometro": HerramientaAutomotriz(
        clave="manometro",
        nombre_canonico="manómetro de presión de combustible",
        terminos=("manómetro", "manometro", "medidor de presión", "presión de gasolina"),
        patron_mencion=re.compile(r"\b(man[oó]metro|medir\s+(?:la\s+)?presi[oó]n|presi[oó]n\s+de\s+(?:gasolina|combustible))\b", re.IGNORECASE),
    ),
    "chispa": HerramientaAutomotriz(
        clave="chispa",
        nombre_canonico="probador de chispa / herramientas de encendido",
        terminos=("chispa", "probador de chispa", "sacar bujías", "llave de bujías"),
        patron_mencion=re.compile(r"\b(comprobar\s+(?:la\s+)?chispa|probador\s+de\s+chispa|llave\s+de\s+buj[ií]as?|sacar\s+(?:las\s+)?buj[ií]as?|chispa)\b", re.IGNORECASE),
    ),
    "escaner": HerramientaAutomotriz(
        clave="escaner",
        nombre_canonico="escáner de diagnóstico OBD-II",
        terminos=("escáner", "escaner", "scanner", "obd", "obd2", "lector de códigos"),
        patron_mencion=re.compile(r"\b(esc[aá]ner|scanner|lector\s+obd|obd2?)\b", re.IGNORECASE),
    ),
    "compresimetro": HerramientaAutomotriz(
        clave="compresimetro",
        nombre_canonico="compresímetro de motor",
        terminos=("compresímetro", "compresimetro", "medir compresión"),
        patron_mencion=re.compile(r"\b(compres[ií]metro|medir\s+(?:la\s+)?compresi[oó]n)\b", re.IGNORECASE),
    ),
    "vacuometro": HerramientaAutomotriz(
        clave="vacuometro",
        nombre_canonico="vacuómetro de vacío de admisión",
        terminos=("vacuómetro", "vacuometro", "medidor de vacío"),
        patron_mencion=re.compile(r"\b(vacu[oó]metro|medidor\s+de\s+vac[ií]o)\b", re.IGNORECASE),
    ),
    "elevador": HerramientaAutomotriz(
        clave="elevador",
        nombre_canonico="elevador de taller / gata hidráulica",
        terminos=("elevador", "gata", "fosa", "caballetes"),
        patron_mencion=re.compile(r"\b(elevador|gata(\s+hidr[aá]ulica)?|fosa|caballetes)\b", re.IGNORECASE),
    ),
    "reloj_comparador": HerramientaAutomotriz(
        clave="reloj_comparador",
        nombre_canonico="reloj comparador de carátula",
        terminos=("reloj comparador", "micrómetro", "vernier"),
        patron_mencion=re.compile(r"\b(reloj\s+comparador|micr[oó]metro|vernier)\b", re.IGNORECASE),
    ),
    "osciloscopio": HerramientaAutomotriz(
        clave="osciloscopio",
        nombre_canonico="osciloscopio automotriz",
        terminos=("osciloscopio", "osciloscopio digital", "oscilograma"),
        patron_mencion=re.compile(r"\b(osciloscopio|oscilograma)\b", re.IGNORECASE),
    ),
    "general": HerramientaAutomotriz(
        clave="general",
        nombre_canonico="herramientas de taller",
        terminos=("herramientas", "instrumentos", "equipo"),
        patron_mencion=re.compile(r"\b(herramientas?|instrumental|equipo|llaves)\b", re.IGNORECASE),
    ),
}

PATRON_NO_TENGO = re.compile(
    r"\b((?:no|tampoco|ni)\s+(?:tengo|cuento\s+con|dispongo\s+de|poseo)|"
    r"sin\s+herramientas?|ninguna\s+herramienta|cero\s+herramientas)\b",
    re.IGNORECASE,
)

PATRON_NO_SE_USAR = re.compile(
    r"\b(no\s+s[eé]\s+(?:usar(?:lo|la)?|c[oó]mo\s+usar(?:lo|la)?|ocupar(?:lo|la)?)|no\s+tengo\s+experiencia\s+usando)\b",
    re.IGNORECASE,
)

PATRON_NO_REVISADO = re.compile(
    r"\b(no\s+(?:lo\s+)?he\s+(?:revisado|probado|chequeado|checado|verificado|mirado)|"
    r"no\s+he\s+revisado\s+nada|todav[ií]a\s+no|a[uú]n\s+no\s+(?:lo\s+)?(?:reviso|s[eé])|"
    r"no\s+revis[eé]\s+(?:nada|todav[ií]a)?)\b",
    re.IGNORECASE,
)

PATRON_NO_SABE_REALIZAR = re.compile(
    r"\b("
    r"(?:no\s+s[eé]|no\s+sabemos|no\s+sabr[ií]a|no\s+s[eé]\s+bien)\s+(?:bien\s+)?(?:c[oó]mo\s+)?(?:comprobar|revisar|verificar|chequear|checar|medir|probar|hacer(?:lo|la)?|ver|mirar)|"
    r"c[oó]mo\s+(?:se\s+)?(?:comprueba|revisa|verifica|mide|prueba|chequea|hace)|"
    r"no\s+s[eé]\s+(?:hacer|comprobar|revisar|medir)|"
    r"no\s+tengo\s+experiencia\s+(?:comprobando|revisando|midiendo)|"
    r"no\s+s[eé]\s+c[oó]mo\s+(?:hacer|comprobar|revisar|medir)"
    r")\b",
    re.IGNORECASE,
)

PATRON_CONSIGUIO_HERRAMIENTA = re.compile(
    r"\b(ya\s+(?:consegu[ií]|tengo|me\s+prestaron)|ahora\s+s[ií]\s+tengo|consegu[ií]\s+(?:un|una))\b",
    re.IGNORECASE,
)


class GestorPlanB:
    """Gestor de disponibilidad de herramientas y selección de Plan B técnico."""

    @classmethod
    def detectar_indisponibilidad_en_texto(cls, texto: str, texto_preg: str = "") -> List[str]:
        """Detecta qué herramientas específicas o generales el usuario declara no poseer."""
        texto_l = texto.lower().strip()
        texto_preg_l = texto_preg.lower().strip() if texto_preg else ""
        herramientas_detectadas: List[str] = []

        es_negacion_general = bool(PATRON_NO_TENGO.search(texto_l))
        es_no_sabe_usar = bool(PATRON_NO_SE_USAR.search(texto_l))
        es_negacion_directa = texto_l in ("no", "ninguno", "ninguna", "nop", "cero", "nada de eso")

        if not (es_negacion_general or es_no_sabe_usar or es_negacion_directa):
            return []

        # Si el usuario responde sobre una herramienta preguntada previamente
        if (es_negacion_directa or es_no_sabe_usar or es_negacion_general) and texto_preg_l:
            for clave, h in CATALOGO_HERRAMIENTAS.items():
                if clave != "general" and h.patron_mencion.search(texto_preg_l):
                    if clave not in herramientas_detectadas:
                        herramientas_detectadas.append(clave)
            if not herramientas_detectadas and any(w in texto_preg_l for w in ("herramienta", "tester", "medidor")):
                herramientas_detectadas.append("general")

        # Evaluar herramientas específicas mencionadas en el texto del usuario
        for clave, h in CATALOGO_HERRAMIENTAS.items():
            if clave == "general":
                continue
            if h.patron_mencion.search(texto_l) and clave not in herramientas_detectadas:
                herramientas_detectadas.append(clave)

        # Si no especificó ninguna en particular pero dijo "no tengo herramientas", marcar "general"
        if not herramientas_detectadas and (es_negacion_general or es_no_sabe_usar):
            herramientas_detectadas.append("general")

        return herramientas_detectadas

    @classmethod
    def detectar_no_revisado(cls, texto: str) -> bool:
        """Indica si el usuario manifiesta que aún no ha realizado la comprobación."""
        return bool(PATRON_NO_REVISADO.search(texto.lower()))

    @classmethod
    def detectar_no_sabe_realizar(cls, texto: str) -> bool:
        """Indica si el usuario manifiesta no saber cómo realizar una comprobación o inspección."""
        return bool(PATRON_NO_SABE_REALIZAR.search(texto.lower()))

    @classmethod
    def detectar_no_sabe_usar(cls, texto: str) -> bool:
        """Indica si el usuario afirma no saber cómo operar una herramienta."""
        return bool(PATRON_NO_SE_USAR.search(texto.lower()))

    @classmethod
    def detectar_recuperacion_herramienta(cls, texto: str, texto_preg: str = "") -> List[str]:
        """Detecta herramientas que el usuario confirmó tener, consiguió o le prestaron."""
        texto_l = texto.lower().strip()
        texto_preg_l = texto_preg.lower().strip() if texto_preg else ""
        es_afirmacion_directa = any(
            w in texto_l
            for w in (
                "si", "sí", "si tengo", "sí tengo", "tengo uno", "tengo tester",
                "dispongo", "lo tengo", "ya lo conecte", "ya lo conecté", "cuento con",
                "sí maestro", "si maestro", "tengo un", "tengo una",
            )
        )
        tiene_mencion_herramienta_usuario = any(
            h.patron_mencion.search(texto_l) for clave, h in CATALOGO_HERRAMIENTAS.items() if clave != "general"
        )
        tiene_mencion_herramienta_pregunta = any(
            h.patron_mencion.search(texto_preg_l) for clave, h in CATALOGO_HERRAMIENTAS.items() if clave != "general"
        )
        if not (
            (PATRON_CONSIGUIO_HERRAMIENTA.search(texto_l) and (tiene_mencion_herramienta_usuario or tiene_mencion_herramienta_pregunta))
            or (es_afirmacion_directa and (tiene_mencion_herramienta_pregunta or tiene_mencion_herramienta_usuario))
        ):
            return []

        recuperadas: List[str] = []
        if es_afirmacion_directa and tiene_mencion_herramienta_pregunta:
            for clave, h in CATALOGO_HERRAMIENTAS.items():
                if clave != "general" and h.patron_mencion.search(texto_preg_l):
                    recuperadas.append(clave)

        for clave, h in CATALOGO_HERRAMIENTAS.items():
            if clave == "general":
                continue
            if h.patron_mencion.search(texto_l) and clave not in recuperadas:
                recuperadas.append(clave)
        return recuperadas

    @classmethod
    def registrar_bloqueos_en_estado(
        cls,
        estado: ConversationState,
        texto_usuario: str,
        texto_preg: str = "",
    ) -> Dict[str, Any]:
        """Actualiza el ConversationState con herramientas bloqueadas o desbloqueadas."""
        hechos_registrados = {}

        # 1. Herramientas conseguidas posteriormente (desbloqueo)
        recuperadas = cls.detectar_recuperacion_herramienta(texto_usuario, texto_preg)
        for her in recuperadas:
            estado.desbloquear_herramienta(her)
            h = estado.registrar_hecho(
                f"{her}_disponible",
                "SI",
                categoria="herramienta",
                tipo=FactType.CONDICION,
                texto_crudo=texto_usuario,
            )
            hechos_registrados[f"{her}_disponible"] = h.to_dict()

        # 2. Detección de no revisado (sin descartar la hipótesis)
        if cls.detectar_no_revisado(texto_usuario):
            h = estado.registrar_hecho(
                "estado_inspeccion_previa",
                "no_revisado_aun",
                categoria="inspeccion",
                tipo=FactType.CONDICION,
                texto_crudo=texto_usuario,
            )
            hechos_registrados["estado_inspeccion_previa"] = h.to_dict()

        # 2b. Detección de no saber realizar la prueba (requiere procedimiento o Plan B)
        if cls.detectar_no_sabe_realizar(texto_usuario):
            h = estado.registrar_hecho(
                "dificultad_procedimiento_inspeccion",
                "no_sabe_realizar",
                categoria="plan_b",
                tipo=FactType.CONDICION,
                texto_crudo=texto_usuario,
                estado=FactState.NO_SABE_REALIZAR,
            )
            hechos_registrados["dificultad_procedimiento_inspeccion"] = h.to_dict()

        # 3. Detección de no saber usar la herramienta
        if cls.detectar_no_sabe_usar(texto_usuario):
            h = estado.registrar_hecho(
                "dificultad_operacion_herramienta",
                "SI",
                categoria="herramienta",
                tipo=FactType.CONDICION,
                texto_crudo=texto_usuario,
            )
            hechos_registrados["dificultad_operacion_herramienta"] = h.to_dict()

        # 4. Indisponibilidad de herramientas (bloqueo)
        indisponibles = cls.detectar_indisponibilidad_en_texto(texto_usuario, texto_preg)
        for her in indisponibles:
            estado.bloquear_herramienta(her)
            h = estado.registrar_hecho(
                f"{her}_disponible",
                "NO",
                categoria="herramienta",
                tipo=FactType.CONDICION,
                texto_crudo=texto_usuario,
            )
            hechos_registrados[f"{her}_disponible"] = h.to_dict()

            # Bloquear pruebas primarias asociadas a esta herramienta
            if her in ("chispa", "general"):
                estado.bloquear_prueba("comprobar_chispa_bobinas", her, "Usuario sin herramienta para chispa")
            if her in ("manometro", "general"):
                estado.bloquear_prueba("medir_presion_gasolina", her, "Usuario sin manómetro")
            if her in ("multimetro", "general"):
                estado.bloquear_prueba("medicion_voltaje_multimetro", her, "Usuario sin multímetro")
            if her in ("escaner", "general"):
                estado.bloquear_prueba("lectura_codigos_escaner", her, "Usuario sin escáner")

        return hechos_registrados

    @classmethod
    def obtener_plan_b_para_falla(
        cls,
        falla: str,
        estado: ConversationState,
    ) -> Optional[Tuple[str, str, QuestionIntent]]:
        """
        Retorna (prueba_plan_b, pregunta_plan_b, intent) para la falla diagnosticada.
        Garantiza que la alternativa seleccionada sea realizable sin herramientas y no se repita.
        """
        falla_l = (
            falla.lower()
            .replace("í", "i")
            .replace("á", "a")
            .replace("é", "e")
            .replace("ó", "o")
            .replace("ú", "u")
        )

        herramientas_bloqueadas = estado.herramientas_no_disponibles
        sin_herramientas = "general" in herramientas_bloqueadas

        # 1. Sistema de encendido: Bujías / Bobinas (Misfire)
        if "bujia" in falla_l or "bobina" in falla_l:
            if "chispa" in herramientas_bloqueadas or sin_herramientas or estado.es_prueba_bloqueada("comprobar_chispa_bobinas"):
                # Si el Plan B ya fue preguntado o respondido, pasar a Plan C (Inspección acústica / olor o derivación)
                if estado.ya_preguntado_texto("Al revisar visualmente las bobinas"):
                    return (
                        "comprobación de olor a combustible crudo por el tubo de escape al acelerar.",
                        "¿Percibes un olor fuerte a gasolina cruda en el escape o notas humo negro cuando el motor tironea?",
                        QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                    )
                return (
                    "inspección visual de bobinas y cables (grietas o sulfato) y verificar si hay aceite en los pozos de bujía.",
                    "Entiendo, sin herramientas para chispa. Al revisar visualmente las bobinas y cables: ¿notas grietas, cables resecos o presencia de aceite en los pozos de bujía?",
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                )

        # 2. Sistema de combustible: Bomba de gasolina / Inyectores / Presión
        if "combustible" in falla_l or "bomba" in falla_l or "presion" in falla_l or "inyector" in falla_l:
            if "manometro" in herramientas_bloqueadas or sin_herramientas or estado.es_prueba_bloqueada("medir_presion_gasolina"):
                if estado.ya_preguntado_texto("zumbido de la bomba"):
                    return (
                        "observación del comportamiento del tironeo según el nivel de combustible en el tanque.",
                        "¿El tironeo o pérdida de fuerza empeora significativamente cuando el tanque tiene un cuarto de gasolina o menos?",
                        QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                    )
                return (
                    "comprobación acústica del zumbido de la bomba en el tanque al girar la llave a ON sin dar arranque.",
                    "Entiendo, sin manómetro. Al poner contacto en ON sin dar marcha: ¿se escucha el zumbido de la bomba en el tanque durante 2 a 3 segundos?",
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                )

        # 3. Batería / Alternador / Arranque
        if "bateria" in falla_l or "borne" in falla_l or "alternador" in falla_l or "arranque" in falla_l:
            if "multimetro" in herramientas_bloqueadas or sin_herramientas or estado.es_prueba_bloqueada("medicion_voltaje_multimetro"):
                if estado.ya_preguntado_texto("luces del tablero bajan bastante"):
                    return (
                        "inspección física de terminales de batería y presencia de sarro blanquecino en los bornes.",
                        "¿Los bornes de la batería presentan sarro blanco/verdoso o terminales flojos que se muevan con la mano?",
                        QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                    )
                return (
                    "inspección visual de atenuación de luces de tablero o faros al accionar el arranque.",
                    "Entiendo, no tienes multímetro. Cuando intentas arrancar, ¿las luces del tablero bajan bastante de intensidad o permanecen casi igual?",
                    QuestionIntent.COMPORTAMIENTO_ARRANQUE,
                )

        # 4. Frenos: Discos alabeados / Pastillas
        if "disco" in falla_l or "pastilla" in falla_l or "freno" in falla_l:
            if "reloj_comparador" in herramientas_bloqueadas or "elevador" in herramientas_bloqueadas or sin_herramientas or estado.es_prueba_no_sabe_realizar():
                if estado.ya_preguntado_texto("alumbra con una linterna"):
                    return (
                        "medición de alabeo de disco con reloj comparador en taller especializado.",
                        "Para medir con exactitud el alabeo del disco se requiere reloj comparador en taller. ¿Deseas recomendaciones para evitar cristalizar las pastillas?",
                        QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                    )
                return (
                    "inspección visual a través de los rines para detectar surcos profundos o coloración azulada en los discos.",
                    "Sin desmontar la rueda: al alumbra con una linterna a través del rin hacia el disco, ¿se observan surcos profundos al tacto o marcas azuladas de sobrecalentamiento?",
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                )

        # 5. Suspensión / Dirección: Rótulas, trapecios, bujes, amortiguador
        if any(k in falla_l for k in ("suspension", "buje", "rotula", "rótula", "trapecio", "bieleta", "amortiguador")):
            if not estado.ya_preguntado_texto("movimientos cortos de vaivén"):
                return (
                    "comprobación segura de holgura mediante vaivén de dirección en plano sin elevar el vehículo.",
                    "Para comprobarlo de forma segura sin levantar el vehículo ni correr riesgos: con el auto estacionado en plano y motor apagado, gira el volante bruscamente con movimientos cortos de vaivén de lado a lado, o empuja la carrocería hacia abajo. ¿Se percibe un 'clac-clac' metálico seco o juego muerto?",
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                )
            return (
                "inspección técnica en taller con elevador hidráulico y palanca especializada.",
                "Para verificar con total precisión la holgura interna de trapecios o rótulas se requiere elevar el auto con seguridad en taller. ¿Prefieres que te resuma las precauciones antes de llevarlo a revisión?",
                QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
            )

        # 6. Transmisión: Nivel / Estado de ATF
        if "transmision" in falla_l or "caja" in falla_l or "atf" in falla_l:
            if not estado.ya_preguntado_texto("retira la varilla"):
                return (
                    "comprobación segura del fluido ATF mediante varilla medidora o goteo en piso.",
                    "Para revisarlo de forma segura: con el auto en plano y motor tibio en P, retira la varilla de transmisión (suele decir ATF) y límpiala con papel blanco. ¿El fluido se ve rojizo transparente, o negro/marrón con olor a quemado?",
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                )

        # 7. Climatización: Compresor / A/C
        if "aire" in falla_l or "clima" in falla_l or "compresor" in falla_l:
            if not estado.ya_comprobado_o_respondido("acople_compresor") and not estado.ya_preguntado_texto("clic metálico claro"):
                return (
                    "comprobación acústica segura de acople del compresor en ralentí.",
                    "Para comprobarlo fácilmente sin desarmar: con el motor encendido en ralentí y el capó abierto, activa el botón A/C al máximo. ¿Se escucha un 'clic' metálico claro en el compresor y bajan un instante las revoluciones?",
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                )
            elif not estado.ya_preguntado_texto("electroventilador del condensador"):
                return (
                    "inspección visual de flujo de refrigerante y electroventilador de condensador.",
                    "Para verificar si la falta de frío se debe a pérdida de carga o condensación deficiente: ¿gira el electroventilador del condensador al encender el A/C y las tuberías de servicio del vano motor se sienten una fría y la otra caliente?",
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                )

        # 8. Si no hay herramientas para nada y se agotaron alternativas sensoriales
        if (sin_herramientas or estado.es_prueba_no_sabe_realizar()) and len(estado.preguntas_realizadas) >= 2:
            return (
                "inspección técnica en taller automotriz con escáner y manómetro profesional.",
                "Debido a que esta avería requiere comprobar componentes internos sin desmontar a ciegas, ¿deseas que te oriente con las precauciones antes de llevarlo al taller?",
                QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
            )

        return None

    @classmethod
    def obtener_plan_b_por_inspeccion(
        cls,
        dominio: str,
        ultima_preg: str,
        estado: ConversationState,
    ) -> Optional[Tuple[str, str, QuestionIntent]]:
        """
        Retorna (prueba_plan_b, pregunta_plan_b, intent) con un procedimiento observable seguro
        cuando el usuario no sabe realizar una inspección o carece del método adecuado.
        """
        dominio_norm = (dominio or "").upper()
        preg_norm = (ultima_preg or "").lower()

        # 1. SUSPENSION: holgura de bujes / rótulas / terminales
        if dominio_norm == "SUSPENSION" or any(w in preg_norm for w in ("buje", "rotula", "rótula", "suspension", "holgura")):
            if not estado.ya_preguntado_texto("movimientos cortos de vaivén"):
                return (
                    "comprobación segura de holgura mediante vaivén de dirección en plano sin elevar el vehículo.",
                    "Para comprobarlo de forma segura sin levantar el vehículo ni correr riesgos: con el auto estacionado en plano y motor apagado, gira el volante bruscamente con movimientos cortos de vaivén de lado a lado, o empuja la carrocería hacia abajo. ¿Se percibe un 'clac-clac' metálico seco o juego muerto?",
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                )
            return (
                "inspección técnica en taller con elevador hidráulico y palanca especializada.",
                "Para verificar con total precisión la holgura interna de trapecios o rótulas se requiere elevar el auto con seguridad en taller. ¿Prefieres que te resuma las precauciones antes de llevarlo a revisión?",
                QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
            )

        # 2. FRENOS: medición de espesor o estado de discos / pastillas
        if dominio_norm == "FRENOS" or any(w in preg_norm for w in ("disco", "pastilla", "freno", "espesor")):
            if not estado.ya_preguntado_texto("alumbra con una linterna"):
                return (
                    "inspección visual segura del disco y pastilla a través de los rines con linterna.",
                    "Sin desmontar la rueda: al alumbra con una linterna a través del rin hacia el disco, ¿se observan surcos profundos al tacto o marcas azuladas de sobrecalentamiento?",
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                )
            return (
                "medición de alabeo de disco con reloj comparador en taller especializado.",
                "Para medir con exactitud el alabeo del disco se requiere reloj comparador en taller. ¿Deseas recomendaciones para evitar cristalizar las pastillas?",
                QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
            )

        # 3. MOTOR / ENCENDIDO: comprobación de chispa
        if any(w in preg_norm for w in ("chispa", "bobina", "bujia", "bujía")):
            if not estado.ya_preguntado_texto("aguja de revoluciones"):
                return (
                    "comprobación segura sin riesgo eléctrico observando RPM y olor en escape.",
                    "Para evitar riesgos eléctricos de alta tensión: al dar arranque, ¿la aguja de revoluciones (RPM) del tablero oscila ligeramente o notas un fuerte olor a gasolina cruda en el escape?",
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                )

        # 4. TRANSMISION: revisión de nivel o estado de ATF
        if dominio_norm == "TRANSMISION" or any(w in preg_norm for w in ("atf", "transmision", "caja", "aceite")):
            if not estado.ya_preguntado_texto("retira la varilla"):
                return (
                    "comprobación segura del fluido ATF mediante varilla medidora o goteo en piso.",
                    "Para revisarlo de forma segura: con el auto en plano y motor tibio en P, retira la varilla de transmisión (suele decir ATF) y límpiala con papel blanco. ¿El fluido se ve rojizo transparente, o negro/marrón con olor a quemado?",
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                )

        # 5. CLIMATIZACION: comprobación de acople de compresor
        if dominio_norm == "CLIMATIZACION" or any(w in preg_norm for w in ("compresor", "aire acondicionado", "clima", "enfria")):
            if not estado.ya_comprobado_o_respondido("acople_compresor") and not estado.ya_preguntado_texto("clic metálico claro"):
                return (
                    "comprobación acústica segura de acople del compresor en ralentí.",
                    "Para comprobarlo fácilmente sin desarmar: con el motor encendido en ralentí y el capó abierto, activa el botón A/C al máximo. ¿Se escucha un 'clic' metálico claro en el compresor y bajan un instante las revoluciones?",
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                )
            elif not estado.ya_preguntado_texto("electroventilador del condensador"):
                return (
                    "inspección visual de flujo de refrigerante y electroventilador de condensador.",
                    "Para verificar si la falta de frío se debe a pérdida de carga o condensación deficiente: ¿gira el electroventilador del condensador al encender el A/C y las tuberías de servicio del vano motor se sienten una fría y la otra caliente?",
                    QuestionIntent.PLAN_B_SIN_HERRAMIENTAS,
                )

        # 6. Fallback a falla top1 si existe
        if estado.top3_actual:
            top1_cand = estado.top3_actual[0].get("falla", "")
            return cls.obtener_plan_b_para_falla(top1_cand, estado)

        return None
