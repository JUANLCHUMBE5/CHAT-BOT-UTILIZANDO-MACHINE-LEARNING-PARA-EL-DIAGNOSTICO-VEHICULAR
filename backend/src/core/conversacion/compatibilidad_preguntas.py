"""Compatibilidad semántica entre preguntas y el contexto diagnóstico activo."""

from __future__ import annotations

import unicodedata
from typing import Optional, Tuple

from src.core.conversacion.models import (
    ConversationState,
    DtcStatus,
    EstadoOperativo,
    FactState,
    QuestionIntent,
)


def _normalizar(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", (texto or "").lower())
        if unicodedata.category(c) != "Mn"
    )


class CompatibilidadPreguntas:
    """Aplica la pertinencia clínica antes de ordenar por ganancia de información."""

    @classmethod
    def dominio_actual(cls, estado: ConversationState) -> str:
        # 1. Si el estado operativo es inequívoco (ARRANQUE o FRENADO), manda sobre dominios no compatibles
        if estado.estado_operativo == EstadoOperativo.ARRANQUE:
            return "ARRANQUE"
        if estado.estado_operativo == EstadoOperativo.FRENADO:
            return "FRENOS"

        # 2. Por hechos confirmados explícitos en el caso clínico activo
        for campo, hecho in estado.hechos.items():
            if hecho.estado != FactState.CONFIRMADO:
                continue
            c = campo.lower()
            if any(k in c for k in ("demora_arranque", "motor_arranca", "ruido_arranque")):
                return "ARRANQUE"
            if any(k in c for k in ("climatizacion", "compresor_acopla")):
                return "CLIMATIZACION"
            if any(k in c for k in ("freno", "pastilla", "disco")):
                return "FRENOS"
            if any(k in c for k in ("reversa", "transmision", "caja")):
                return "TRANSMISION"
            if any(k in c for k in ("suspension", "bache", "rotula", "amortiguador")):
                return "SUSPENSION"

        # 3. Dominio probable asignado al caso
        dominio = str(getattr(estado, "dominio_probable", "DESCONOCIDO") or "DESCONOCIDO")
        if dominio != "DESCONOCIDO":
            return dominio

        # 4. Fallback por EstadoOperativo restante
        if estado.estado_operativo in (EstadoOperativo.MARCHA, EstadoOperativo.RALENTI):
            return "MARCHA_MOTOR"
        return "DESCONOCIDO"

    @classmethod
    def tiene_evidencia_subsistema(cls, dominio_sub: str, estado: ConversationState) -> bool:
        """Comprueba si existe justificación clínica objetiva (síntoma, estado o hipótesis) para el subsistema."""
        if dominio_sub in ("GENERAL", "DESCONOCIDO"):
            return True

        # A. Evidencia por EstadoOperativo activo
        if dominio_sub == "ARRANQUE" and estado.estado_operativo == EstadoOperativo.ARRANQUE:
            return True
        if dominio_sub == "FRENOS" and estado.estado_operativo == EstadoOperativo.FRENADO:
            return True
        if dominio_sub == "MARCHA_MOTOR" and estado.estado_operativo in (EstadoOperativo.MARCHA, EstadoOperativo.RALENTI):
            return True

        # B. Evidencia por hechos confirmados en el caso activo
        for campo, hecho in estado.hechos.items():
            if hecho.estado != FactState.CONFIRMADO:
                continue
            c = _normalizar(campo)
            v = _normalizar(str(hecho.valor))
            if dominio_sub == "SUSPENSION" and any(k in c or k in v for k in ("suspension", "bache", "rotula", "amortiguador", "trapecio", "rueda")):
                return True
            if dominio_sub == "FRENOS" and any(k in c or k in v for k in ("freno", "disco", "pastilla", "pedal")):
                return True
            if dominio_sub == "CLIMATIZACION" and any(k in c or k in v for k in ("aire acondicionado", "clima", "compresor", "r134a", "enfria")):
                return True
            if dominio_sub == "TRANSMISION" and any(k in c or k in v for k in ("caja", "embrague", "transmision", "atf", "acople", "reversa")):
                return True
            if dominio_sub == "ARRANQUE" and any(k in c or k in v for k in ("arranque", "solenoide", "llave", "bateria")):
                return True
            if dominio_sub == "ELECTRICO" and any(k in c or k in v for k in ("bateria", "alternador", "voltaje", "multimetro", "fusible")):
                return True
            if dominio_sub == "MARCHA_MOTOR" and any(k in c or k in v for k in ("motor", "refrigerante", "temperatura", "sobrecalentamiento", "misfire", "potencia", "humo")):
                return True

        # C. Evidencia por hipótesis activas C1 Top-3 (si ya existen)
        if estado.top3_actual:
            top_texto = _normalizar(" ".join(str(h.get("falla", "")) for h in estado.top3_actual))
            if dominio_sub == "SUSPENSION" and any(k in top_texto for k in ("suspension", "amortiguador", "bujes", "rotula")):
                return True
            if dominio_sub == "FRENOS" and any(k in top_texto for k in ("freno", "disco", "pastilla", "abs")):
                return True
            if dominio_sub == "CLIMATIZACION" and any(k in top_texto for k in ("aire", "clima", "compresor")):
                return True
            if dominio_sub == "TRANSMISION" and any(k in top_texto for k in ("caja", "transmision", "embrague", "atf")):
                return True
            if dominio_sub == "ARRANQUE" and any(k in top_texto for k in ("arranque", "bateria", "solenoide", "common rail")):
                return True
            if dominio_sub == "ELECTRICO" and any(k in top_texto for k in ("bateria", "alternador", "carga")):
                return True
            if dominio_sub == "MARCHA_MOTOR" and any(k in top_texto for k in ("inyeccion", "bujia", "bobina", "refrigerante", "valvula")):
                return True

        return False

    @staticmethod
    def dominio_pregunta(intent: QuestionIntent, texto: str) -> str:
        txt = _normalizar(texto)
        if any(k in txt for k in ("reversa", "transmision", "caja", "atf", "acople", "embrague")):
            return "TRANSMISION"
        if any(k in txt for k in ("freno", "frenar", "pedal esponjoso", "pastilla", "disco")):
            return "FRENOS"
        if any(k in txt for k in ("aire acondicionado", "compresor", "a c", "clima", "enfria", "r134a")):
            return "CLIMATIZACION"
        if any(k in txt for k in ("suspension", "amortiguador", "bache", "rotula", "bujes", "trapecio")):
            return "SUSPENSION"
        if intent in (
            QuestionIntent.COMPORTAMIENTO_ARRANQUE,
            QuestionIntent.CAIDA_TENSION_ARRANQUE,
            QuestionIntent.TEMPERATURA_AMBIENTAL_ARRANQUE,
        ) or any(k in txt for k in ("dificultad para arrancar", "demora en encender", "dar marcha", "cuesta prender", "al dar contacto", "al girar la llave")):
            return "ARRANQUE"
        if intent == QuestionIntent.MEDICION_VOLTAJE or any(k in txt for k in ("multimetro", "voltaje de reposo", "alternador", "borne")):
            return "ELECTRICO"
        if intent == QuestionIntent.TEMPERATURA_APARICION and "motor" in txt:
            return "MARCHA_MOTOR"
        if intent == QuestionIntent.CONDICION_OPERACION and any(
            k in txt for k in ("ralenti", "acelerar", "carretera")
        ):
            return "MARCHA_MOTOR"
        return "GENERAL"

    @staticmethod
    def diferencial_justifica_temperatura(estado: ConversationState, dominio: str) -> bool:
        """Permite temperatura fuera de motor solo con hipótesis térmica vigente."""
        if dominio in ("MARCHA_MOTOR", "ARRANQUE"):
            return True
        etiquetas = " ".join(str(h.get("falla", "")) for h in estado.top3_actual)
        etiquetas = _normalizar(etiquetas)
        if dominio == "TRANSMISION":
            return any(
                k in etiquetas
                for k in ("atf", "aceite de caja", "viscos", "solenoide", "cuerpo de valvulas")
            )
        return False

    @classmethod
    def contradice_hecho_negado(cls, texto: str, estado: ConversationState) -> bool:
        """Verifica si la pregunta presupone un síntoma o condición explícitamente negada por el usuario."""
        txt = _normalizar(texto)
        for k, h in estado.hechos.items():
            if h.estado != FactState.AUSENTE_NEGADO:
                continue
            v = _normalizar(h.valor)
            # 1. Vibración negada (ej. al frenar no vibra el volante)
            if ("vibracion" in v or "vibra" in v) and ("vibracion" in txt or "vibra" in txt):
                return True
            # 2. Apagado negado
            if ("apaga" in v or "muere" in v) and ("apaga" in txt or "se muere" in txt):
                return True
            # 3. Pérdida de fuerza/potencia negada
            if ("fuerza" in v or "potencia" in v) and ("fuerza" in txt or "potencia" in txt):
                return True
            # 4. Sobrecalentamiento negado
            if ("calienta" in v or "hierve" in v) and ("calienta" in txt or "hierve" in txt):
                return True
            # 5. Misfire / tironeo negado
            if ("tironea" in v or "misfire" in v or "ratea" in v) and ("tironea" in txt or "ratea" in txt):
                return True
            # 6. Humo blanco negado
            if "humo" in v and "humo" in txt:
                return True
            # 7. Testigo / check engine negado
            if ("check" in v or "testigo" in v or "luz" in v) and ("check" in txt or "testigo" in txt):
                return True
            # 8. Frenos negados (ej. al frenar no vibra, frena bien)
            if ("freno" in v or "frenar" in v) and ("freno" in txt or "frenar" in txt):
                # Solo si la pregunta asume problema de frenos
                if any(w in txt for w in ("frenar", "freno", "pedal", "pastillas")):
                    return True
            # 9. Patinado negado
            if "patina" in v and "patina" in txt:
                return True
            # 10. Olor a combustible negado
            if ("olor" in v or "gasolina" in v) and "olor" in txt:
                return True
            # 11. Motor normal
            if "motor funciona normal" in v and "motor" in txt and any(w in txt for w in ("falla", "frio", "caliente")):
                return True
        return False

    @classmethod
    def es_pertinente_obd2(cls, estado: ConversationState, dominio: str) -> Tuple[bool, Optional[str]]:
        """
        Determina la elegibilidad clínica de preguntas OBD-II/DTC.
        En dominios puramente mecánicos (suspensión, frenos convencionales), OBD-II solo
        es admisible si existe evidencia electrónica (testigos, sensores, control de estabilidad,
        código reportado, o hipótesis diagnóstica con módulo electrónico).
        No debe desplazar inspecciones mecánicas pendientes ni alternativas de Plan B.
        """
        if estado.dtc_status == DtcStatus.DTC_OBSERVADO:
            return True, None

        hechos_norm = " ".join(
            f"{h.campo} {h.valor}" for h in estado.hechos.values()
            if h.estado != FactState.AUSENTE_NEGADO
        )
        hechos_norm = _normalizar(hechos_norm)

        evidencia_electronica = (
            "check engine", "testigo", "luz de", "abs", "esc", "esp", "sensor",
            "dtc", "escaner", "scanner", "codigo", "falla electronica", "traccion",
        )
        if any(e in hechos_norm for e in evidencia_electronica):
            return True, None

        # En dominios no restringidos mecánicamente (DESCONOCIDO, MARCHA_MOTOR, ARRANQUE, ELECTRICO, TRANSMISION), OBD-II es admisible
        if dominio not in ("SUSPENSION", "FRENOS"):
            return True, None

        # En suspensión y frenos puramente mecánicos sin evidencia electrónica:
        top_fallas = " ".join(str(h.get("falla", "")) for h in estado.top3_actual)
        top_fallas = _normalizar(top_fallas)
        if any(e in top_fallas for e in ("abs", "sensor", "electronica", "valvula")):
            return True, None

        return False, "SIN_JUSTIFICACION_ELECTRONICA"

    @classmethod
    def validar(
        cls,
        intent: QuestionIntent,
        texto: str,
        estado: ConversationState,
    ) -> Tuple[bool, Optional[str]]:
        # 0. Compuerta estricta: No repreguntar síntomas ya negados por el usuario
        if cls.contradice_hecho_negado(texto, estado):
            return False, "CONTRADICE_HECHO_CONFIRMADO"

        dominio = cls.dominio_actual(estado)
        dominio_pregunta = cls.dominio_pregunta(intent, texto)

        # 0.1 Validación clínica de OBD-II / Códigos DTC
        if intent == QuestionIntent.CODIGO_DTC:
            pertinente_obd, motivo_obd = cls.es_pertinente_obd2(estado, dominio)
            if not pertinente_obd:
                return False, motivo_obd

        # 0.2 Compuerta clínica de evidencia por subsistema (Fase 11.4.1)
        # Una pregunta de un subsistema específico no puede presentarse si el caso activo carece totalmente de evidencia
        if dominio_pregunta not in ("GENERAL", "DESCONOCIDO"):
            if not cls.tiene_evidencia_subsistema(dominio_pregunta, estado):
                return False, f"SIN_EVIDENCIA_SUBSISTEMA_{dominio_pregunta}"

        if dominio == "DESCONOCIDO" or dominio_pregunta == "GENERAL":
            return True, None
        if dominio_pregunta == dominio:
            return True, None

        if intent == QuestionIntent.TEMPERATURA_APARICION:
            # En un caso de arranque, una pregunta sobre temperatura del motor
            # puede ser válida si existe antecedente de marcha. La precondición
            # concreta se comprueba después en GeneradorPreguntas.
            if dominio == "ARRANQUE" and dominio_pregunta == "MARCHA_MOTOR":
                return True, None
            if cls.diferencial_justifica_temperatura(estado, dominio):
                return False, "INCOMPATIBLE_REDACCION_DOMINIO"
            return False, "INCOMPATIBLE_DOMINIO"

        compatibles = {
            "ARRANQUE": {"ELECTRICO"},
            "ELECTRICO": {"ARRANQUE"},
        }
        if dominio_pregunta in compatibles.get(dominio, set()):
            return True, None
        return False, "INCOMPATIBLE_DOMINIO"
