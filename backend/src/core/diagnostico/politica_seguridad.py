"""Política centralizada de seguridad para respuestas diagnósticas críticas de CarBot."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Optional, Tuple

from src.core.conversacion.polaridad_proposiciones import polaridad_evento
from src.core.diagnostico.banners_seguridad import (
    BANNER_ACEITE,
    BANNER_BATERIA_MOTOR_ENCENDIDO,
    BANNER_BLOQUEO_REGENERACION_DILUCION,
    BANNER_COMBUSTIBLE,
    BANNER_DIESEL_ALTA_PRESION,
    BANNER_DIESEL_EMBALAMIENTO,
    BANNER_FRENO,
    BANNER_FRENO_PRECAUCION,
    BANNER_HV,
    BANNER_RADIADOR_CALIENTE,
    BANNER_SUSPENSION_CRITICA,
    BANNER_TEMPERATURA,
    PRERREQUISITOS_REGENERACION_DPF_OEM,
)


class SeveridadSeguridad(str, Enum):
    """Niveles de severidad de riesgo para la seguridad física y del vehículo."""
    CRITICAL_STOP = "CRITICAL_STOP"          # Peligro de vida / pérdida de frenos / incendio / fundición inminente
    URGENT_INSPECTION = "URGENT_INSPECTION"  # Inspección prioritaria antes de continuar marcha prolongada
    NORMAL_DIAGNOSTIC = "NORMAL_DIAGNOSTIC"  # Diagnóstico técnico estándar de taller


from src.core.diagnostico.patrones_seguridad import (
    PATRON_ACCION_APERTURA_REFRIGERACION,
    PATRON_ACEITE_CRITICO,
    PATRON_ALTA_TENSION,
    PATRON_APERTURA_RADIADOR_CALIENTE,
    PATRON_CALOR_REFRIGERACION,
    PATRON_COMBUSTIBLE_CRITICO,
    PATRON_CORRECCION_ACEITE_COMPROBADA,
    PATRON_DIESEL_ALTA_PRESION_TACTIL,
    PATRON_DIESEL_EMBALAMIENTO_CRITICO,
    PATRON_ENFRIAMIENTO_CONFIRMADO,
    PATRON_FRENO_CRITICO,
    PATRON_FRENO_PRECAUCION,
    PATRON_INDICIOS_DILUCION_ACEITE,
    PATRON_OBJETO_REFRIGERACION,
    PATRON_SOLICITUD_REGENERACION_DPF,
    PATRON_SUSPENSION_CRITICA,
    PATRON_TEMPERATURA_CRITICA,
)


class PoliticaSeguridad:
    """Capa centralizada de auditoría y aplicación de directivas de seguridad en respuestas."""

    PRERREQUISITOS_REGENERACION_DPF_OEM = PRERREQUISITOS_REGENERACION_DPF_OEM

    @classmethod
    def _hay_dilucion_aceite_activa(
        cls,
        texto_usuario: str,
        estado: Optional[Any] = None,
    ) -> bool:
        """Determina si existe reporte activo de dilución de aceite o sobrellenado peligroso."""
        txt_l = texto_usuario.lower()
        if PATRON_CORRECCION_ACEITE_COMPROBADA.search(txt_l):
            return False

        if PATRON_INDICIOS_DILUCION_ACEITE.search(txt_l):
            return True

        if estado is not None:
            hechos = getattr(estado, "hechos", {})
            for k, h in hechos.items():
                campo = str(getattr(h, "campo", "")).lower()
                st = getattr(h, "estado", None)
                st_val = str(getattr(st, "value", st)).upper()
                if (
                    k in ("reemplazado_aceite", "aceite_reemplazado", "aceite_drenado_reemplazado")
                    or ("aceite" in campo and "reemplazado" in campo)
                ):
                    if st_val in ("CONFIRMADO", "ACTIVO", "SI"):
                        return False

            for k, h in hechos.items():
                campo = str(getattr(h, "campo", "")).lower()
                st = getattr(h, "estado", None)
                st_val = str(getattr(st, "value", st)).upper()
                if (
                    k in ("aceite_sobrellenado_diluido", "dilucion_aceite_combustible")
                    or "dilucion" in campo
                    or "sobrellenado" in campo
                    or ("aceite" in campo and "maximo" in campo)
                ):
                    if st_val not in ("DESCARTADO", "CORREGIDO", "AUSENTE_NEGADO"):
                        return True

            hist = getattr(estado, "historial_mensajes_usuario", [])
            if hist:
                dilucion_idx = -1
                correccion_idx = -1
                for idx, msg in enumerate(hist):
                    msg_l = msg.lower()
                    if PATRON_INDICIOS_DILUCION_ACEITE.search(msg_l):
                        dilucion_idx = idx
                    if PATRON_CORRECCION_ACEITE_COMPROBADA.search(msg_l):
                        correccion_idx = idx

                if dilucion_idx != -1 and correccion_idx <= dilucion_idx:
                    return True

        return False

    @classmethod
    def _hay_recalentamiento_activo(
        cls,
        texto_usuario: str,
        estado: Optional[Any] = None,
    ) -> bool:
        """Determina si existe evidencia activa de sobrecalentamiento/alta temperatura."""
        txt_l = texto_usuario.lower()
        if PATRON_ENFRIAMIENTO_CONFIRMADO.search(txt_l):
            return False

        if PATRON_CALOR_REFRIGERACION.search(txt_l) or PATRON_TEMPERATURA_CRITICA.search(txt_l):
            return True

        if estado is not None:
            hist = getattr(estado, "historial_mensajes_usuario", [])
            for msg in reversed(hist):
                msg_l = msg.lower()
                if PATRON_ENFRIAMIENTO_CONFIRMADO.search(msg_l):
                    return False
                if PATRON_CALOR_REFRIGERACION.search(msg_l) or PATRON_TEMPERATURA_CRITICA.search(msg_l):
                    return True

            hechos = getattr(estado, "hechos", {})
            for k, h in hechos.items():
                if k in ("sintoma_sobrecalentamiento", "temperatura_alta_refrigerante"):
                    st = getattr(h, "estado", None)
                    st_val = str(getattr(st, "value", st)).upper()
                    if st_val not in ("DESCARTADO", "CORREGIDO", "AUSENTE_NEGADO"):
                        return True

        return False

    @classmethod
    def _hay_solicitud_apertura_refrigeracion(cls, texto_usuario: str) -> bool:
        """Detecta intención de abrir, destapar, aflojar o retirar tapón/radiador/depósito."""
        txt_l = texto_usuario.lower()
        if PATRON_ACCION_APERTURA_REFRIGERACION.search(txt_l) and PATRON_OBJETO_REFRIGERACION.search(txt_l):
            return True
        return bool(PATRON_APERTURA_RADIADOR_CALIENTE.search(txt_l))

    @classmethod
    def _hay_apertura_radiador_caliente_peligrosa(
        cls,
        texto_usuario: str,
        estado: Optional[Any] = None,
    ) -> bool:
        """Determina si se intenta abrir el sistema presurizado mientras está caliente."""
        if not cls._hay_solicitud_apertura_refrigeracion(texto_usuario):
            return False
        return cls._hay_recalentamiento_activo(texto_usuario, estado)

    @classmethod
    def _hay_peligro_combustible_no_negado(cls, texto_usuario: str, txt_comb: str) -> bool:
        """Verifica por cláusula si existe al menos un indicio de peligro de combustible no negado."""
        matches = list(PATRON_COMBUSTIBLE_CRITICO.finditer(texto_usuario))
        if matches:
            return any(
                polaridad_evento(texto_usuario, m.start(), m.end()) != "negado"
                for m in matches
            )
        # Sin un evento en la entrada, conservar el control sobre el diagnóstico.
        return bool(PATRON_COMBUSTIBLE_CRITICO.search(txt_comb))

    @classmethod
    def evaluar_severidad(
        cls,
        texto_usuario: str,
        diagnostico_ml: str = "",
        estado: Optional[Any] = None,
    ) -> Tuple[SeveridadSeguridad, Optional[str]]:
        """Evalúa si la condición descrita requiere un banner de seguridad crítico."""
        txt_comb = f"{texto_usuario} {diagnostico_ml}".lower()

        # 1. Comprobación de fuga de combustible Common Rail a alta presión (búsqueda táctil / contacto directo)
        if PATRON_DIESEL_ALTA_PRESION_TACTIL.search(texto_usuario):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_DIESEL_ALTA_PRESION

        # 2. Comprobación de regeneración DPF con dilución de aceite o prerrequisitos pendientes
        if PATRON_SOLICITUD_REGENERACION_DPF.search(texto_usuario):
            if cls._hay_dilucion_aceite_activa(texto_usuario, estado):
                return SeveridadSeguridad.CRITICAL_STOP, BANNER_BLOQUEO_REGENERACION_DILUCION
            txt_l = texto_usuario.lower()
            if PATRON_CORRECCION_ACEITE_COMPROBADA.search(txt_l) or (
                estado and any("reemplazado_aceite" in k or "aceite" in k for k in getattr(estado, "hechos", {}))
            ):
                causa_reparada = bool(
                    re.search(
                        r"\b(?:repar[eé]|cambi[eé]|solucion[eé]|correg[ií]|revis[eé]|arregl[eé])\b.{0,40}\b(?:inyector|inyectores|termostato|sensor|causa|origen|goteo)\b",
                        txt_l,
                    )
                    or (estado and any("reparado" in k or "reemplazado_inyector" in k for k in getattr(estado, "hechos", {})))
                )
                if not causa_reparada:
                    return SeveridadSeguridad.URGENT_INSPECTION, BANNER_BLOQUEO_REGENERACION_DILUCION
                return SeveridadSeguridad.NORMAL_DIAGNOSTIC, PRERREQUISITOS_REGENERACION_DPF_OEM

        # 3. Solicitud de abrir/destapar sistema de refrigeración en caliente
        if cls._hay_apertura_radiador_caliente_peligrosa(texto_usuario, estado):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_RADIADOR_CALIENTE

        if PATRON_DIESEL_EMBALAMIENTO_CRITICO.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_DIESEL_EMBALAMIENTO
        if PATRON_FRENO_CRITICO.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_FRENO
        if PATRON_ACEITE_CRITICO.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_ACEITE
        if PATRON_COMBUSTIBLE_CRITICO.search(txt_comb):
            if cls._hay_peligro_combustible_no_negado(texto_usuario, txt_comb):
                return SeveridadSeguridad.CRITICAL_STOP, BANNER_COMBUSTIBLE
        if PATRON_TEMPERATURA_CRITICA.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_TEMPERATURA
        if PATRON_ALTA_TENSION.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_HV
        if PATRON_SUSPENSION_CRITICA.search(txt_comb):
            return SeveridadSeguridad.URGENT_INSPECTION, BANNER_SUSPENSION_CRITICA
        if PATRON_FRENO_PRECAUCION.search(txt_comb):
            return SeveridadSeguridad.URGENT_INSPECTION, BANNER_FRENO_PRECAUCION

        return SeveridadSeguridad.NORMAL_DIAGNOSTIC, None

    @classmethod
    def enriquecer_respuesta_seguridad(
        cls,
        respuesta_texto: str,
        texto_usuario: str,
        diagnostico_ml: str = "",
        estado: Optional[Any] = None,
    ) -> str:
        """Garantiza que toda respuesta frente a una condición crítica presente la advertencia obligatoria."""
        sev, banner = cls.evaluar_severidad(texto_usuario, diagnostico_ml, estado=estado)
        if banner is None:
            return cls.interceptar_maniobras_peligrosas(respuesta_texto)

        # Si es banner de Common Rail, bloqueo de regeneración o radiador caliente, debe ser la respuesta íntegra prioritaria
        if banner in (BANNER_DIESEL_ALTA_PRESION, BANNER_BLOQUEO_REGENERACION_DILUCION, BANNER_RADIADOR_CALIENTE):
            return banner.strip()

        banner_clean = banner.strip()
        if banner_clean in respuesta_texto:
            return respuesta_texto

        resp_modificada = respuesta_texto
        if sev == SeveridadSeguridad.CRITICAL_STOP and banner == BANNER_HV:
            resp_modificada = re.sub(
                r"\b(p[oó]ngase|use)\s+guantes\s+(?:diel[eé]ctricos\s+)?clase\s+0\s+y\s+(?:repare|desarme|revise|manipule|toque)\b",
                "la manipulación con guantes Clase 0 está reservada exclusivamente a técnicos certificados",
                resp_modificada,
                flags=re.IGNORECASE,
            )

        resp_modificada = cls.interceptar_maniobras_peligrosas(resp_modificada)
        return f"{banner}{resp_modificada}".strip()

    @classmethod
    def interceptar_maniobras_peligrosas(
        cls,
        respuesta_texto: str,
    ) -> str:
        """Intercepta instrucciones operativas peligrosas en respuestas generadas."""
        respuesta = respuesta_texto or ""
        patron_bateria = re.compile(
            r"\b(?:desconect(?:a|e|ar)|retir(?:a|e|ar)|quit(?:a|e|ar))"
            r".{0,45}\b(?:borne|terminal|bater[ií]a)\b"
            r".{0,80}\b(?:motor\s+(?:encendido|en\s+marcha|funcionando)|"
            r"veh[ií]culo\s+encendido)\b",
            re.IGNORECASE,
        )

        patron_bateria_inverso = re.compile(
            r"\b(?:motor\s+(?:encendido|en\s+marcha|funcionando)|"
            r"veh[ií]culo\s+encendido)\b"
            r".{0,80}\b(?:desconect(?:a|e|ar)|retir(?:a|e|ar)|quit(?:a|e|ar))"
            r".{0,45}\b(?:borne|terminal|bater[ií]a)\b",
            re.IGNORECASE,
        )

        prefijos_negacion = (
            "no ", "nunca ", "evite ", "prohibido ", "sin ",
            "no intente ", "no abrir", "no retirar", "no quitar", "no se debe ",
        )

        bateria_peligrosa = False
        for m in patron_bateria.finditer(respuesta):
            pre = respuesta[max(0, m.start() - 30):m.start()].lower()
            if not any(w in pre for w in prefijos_negacion):
                bateria_peligrosa = True
                break
        if not bateria_peligrosa:
            for m in patron_bateria_inverso.finditer(respuesta):
                sub_txt = m.group(0)
                m_v = re.search(r"\b(?:desconect(?:a|e|ar)|retir(?:a|e|ar)|quit(?:a|e|ar))\b", sub_txt, re.IGNORECASE)
                if m_v:
                    idx = m_v.start()
                    pre = sub_txt[max(0, idx - 30):idx].lower()
                    if not any(w in pre for w in prefijos_negacion):
                        bateria_peligrosa = True
                        break

        patron_radiador = re.compile(
            r"\b(?:abr(?:e|ir)|retir(?:a|e|ar)|quit(?:a|e|ar))"
            r".{0,50}\b(?:tap[oó]n|tapa)"
            r".{0,40}\b(?:radiador|dep[oó]sito|refrigerante)\b"
            r".{0,90}\b(?:caliente|motor\s+caliente|temperatura\s+alta)\b",
            re.IGNORECASE,
        )

        patron_radiador_inverso = re.compile(
            r"\b(?:motor\s+caliente|refrigerante\s+caliente|"
            r"temperatura\s+alta)\b"
            r".{0,90}\b(?:abr(?:e|ir)|retir(?:a|e|ar)|quit(?:a|e|ar))"
            r".{0,50}\b(?:tap[oó]n|tapa)"
            r".{0,40}\b(?:radiador|dep[oó]sito)\b",
            re.IGNORECASE,
        )

        radiador_peligroso = False
        for m in patron_radiador.finditer(respuesta):
            pre = respuesta[max(0, m.start() - 30):m.start()].lower()
            if not any(w in pre for w in prefijos_negacion):
                radiador_peligroso = True
                break
        if not radiador_peligroso:
            for m in patron_radiador_inverso.finditer(respuesta):
                sub_txt = m.group(0)
                m_v = re.search(r"\b(?:abr(?:e|ir)|retir(?:a|e|ar)|quit(?:a|e|ar))\b", sub_txt, re.IGNORECASE)
                if m_v:
                    idx = m_v.start()
                    pre = sub_txt[max(0, idx - 30):idx].lower()
                    if not any(w in pre for w in prefijos_negacion):
                        radiador_peligroso = True
                        break

        banners = []
        if bateria_peligrosa:
            banners.append(BANNER_BATERIA_MOTOR_ENCENDIDO.strip())
        if radiador_peligroso:
            banners.append(BANNER_RADIADOR_CALIENTE.strip())
        if not banners:
            return respuesta

        recomendaciones = []
        if bateria_peligrosa:
            recomendaciones.append("Para comprobar el sistema de carga, mida el voltaje con un multímetro sin desconectar la batería.")
        if radiador_peligroso:
            recomendaciones.append("Para revisar refrigeración, apague el motor y espere a que enfríe antes de abrir cualquier tapón.")
        return f"{'\n\n'.join(banners)}\n\n{' '.join(recomendaciones)}".strip()
