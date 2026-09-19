"""Validador de compatibilidad técnica de hipótesis y control de descartes previos (Fase 9.8).

Asegura que las hipótesis presentadas al mecánico sean físicamente consistentes con los hechos
confirmados del vehículo (combustible, transmisión) y que no se repitan hipótesis previamente
rechazadas a menos que exista nueva evidencia clínica que lo justifique.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from src.core.conversacion.models import ConversationState, FactState


class ValidadorCompatibilidad:
    """Valida la compatibilidad técnica de las hipótesis del clasificador ML."""

    @classmethod
    def es_evidencia_espuria(cls, texto: str) -> bool:
        """Determina si un texto recibido carece de contenido clínico automotriz válido.

        Detecta números telefónicos, secuencias de dígitos, IDs, UUIDs, timestamps
        o tokens sin ningún término vehicular o sintomático.
        """
        if not texto:
            return True
        t_clean = texto.strip()

        # 1. Patrones de teléfono (Perú: 9 dígitos iniciando en 9, o con prefijo internacional +51)
        # Formatos: 920809965, 920 809 965, 920-809-965, +51 920 809 965
        t_digits = re.sub(r"\D", "", t_clean)
        if len(t_digits) in (9, 11) and (t_digits.startswith("9") or t_digits.startswith("519")):
            # Si el texto solo contiene el número con espacios/guiones/símbolos
            if len(re.sub(r"[\d\s+\-().]", "", t_clean)) < 3:
                return True

        # 2. Secuencia puramente numérica o con más del 60% de dígitos
        caracteres_alfanumericos = re.findall(r"[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]", t_clean)
        if not caracteres_alfanumericos:
            return True
        digitos = [c for c in caracteres_alfanumericos if c.isdigit()]
        if len(digitos) / len(caracteres_alfanumericos) > 0.6:
            # Si más del 60% son dígitos y no tiene términos de medición válidos (v, voltios, psi, bar, rpm)
            tiene_unidad_medida = bool(re.search(r"\b(v|voltios|psi|bar|rpm|km|grados|c|ohms|ohmios|in\s*hg)\b", t_clean, re.IGNORECASE))
            if not tiene_unidad_medida:
                return True

        # 3. Textos con menos de 4 letras alfabéticas totales
        letras = [c for c in caracteres_alfanumericos if not c.isdigit()]
        if len(letras) < 4:
            return True

        # 4. Verificación de UUID o hash hexadecimal (ej. 368d0d6b...)
        if re.fullmatch(r"[0-9a-fA-F\-]{8,36}", t_clean):
            return True

        return False

    @classmethod
    def validar_compatibilidad_hipotesis(
        cls,
        falla: str,
        estado: Optional[ConversationState],
    ) -> Tuple[bool, Optional[str]]:
        """Verifica si una falla mecánica es compatible con los hechos confirmados del vehículo.

        Retorna (es_compatible, motivo_incompatibilidad).
        """
        if not estado or not estado.hechos:
            return True, None

        falla_l = falla.lower()

        # A. Reglas de combustible
        hecho_combustible = estado.obtener_hecho("combustible") or estado.obtener_hecho("tipo_combustible")
        if hecho_combustible and hecho_combustible.estado == FactState.CONFIRMADO:
            comb = str(hecho_combustible.valor).upper()

            # Gasolina, GLP, GNV incompatibles con sistemas exclusivos Diésel (AdBlue, DPF, FAP, Urea)
            if comb in ("GASOLINA", "GNV", "GLP"):
                if re.search(r"\b(adblue|def|diesel|di[eé]sel|dpf|fap|urea|filtro de particulas)\b", falla_l):
                    return False, f"INCOMPATIBLE_CON_HECHO_CONFIRMADO: Combustible={comb} incompatible con sistemas Diésel/AdBlue/DPF"

            # Diésel incompatible con bujías/bobinas de encendido por chispa o inyectores GNV/GLP
            elif comb == "DIESEL":
                if re.search(r"\b(bujia|buj[ií]as|bobina de encendido|gnv|glp)\b", falla_l):
                    return False, f"INCOMPATIBLE_CON_HECHO_CONFIRMADO: Combustible={comb} no utiliza bujías de encendido por chispa ni gas"

        # B. Reglas de transmisión
        hecho_transmision = estado.obtener_hecho("transmision") or estado.obtener_hecho("caja")
        if hecho_transmision and hecho_transmision.estado == FactState.CONFIRMADO:
            trans = str(hecho_transmision.valor).upper()
            if trans == "MANUAL":
                if any(tc in falla_l for tc in ("caja automatica", "convertidor de par", "cuerpo de valvulas")):
                    return False, f"INCOMPATIBLE_CON_HECHO_CONFIRMADO: Transmisión={trans} incompatible con caja automática"
            elif trans in ("AUTOMATICA", "CVT"):
                if "embrague" in falla_l and any(te in falla_l for te in ("patinando", "plato opresor", "collarin")):
                    return False, f"INCOMPATIBLE_CON_HECHO_CONFIRMADO: Transmisión={trans} incompatible con embrague manual tradicional"

        return True, None

    @classmethod
    def filtrar_y_ordenar_para_presentacion(
        cls,
        predicciones_raw: List[Dict[str, Any]],
        estado: Optional[ConversationState],
        nueva_evidencia: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Filtra y ordena las hipótesis candidatas para la presentación final al usuario.

        Retorna (hipotesis_final_presentada, exclusiones_registradas).
        """
        if not predicciones_raw:
            return [], []

        descartadas_previas = set()
        if estado and getattr(estado, "hipotesis_descartadas", None):
            descartadas_previas = {h.strip().lower() for h in estado.hipotesis_descartadas}

        candidatas_compatibles: List[Dict[str, Any]] = []
        exclusiones: List[Dict[str, Any]] = []

        # Evaluar cada predicción de la lista RAW
        for pred in predicciones_raw:
            falla = pred.get("falla", "")
            prob = pred.get("probabilidad", 0.0)
            falla_l = falla.strip().lower()

            # 1. Validar compatibilidad con hechos confirmados
            es_compatible, motivo_incomp = cls.validar_compatibilidad_hipotesis(falla, estado)
            if not es_compatible:
                exclusiones.append({
                    "falla": falla,
                    "probabilidad_raw": prob,
                    "motivo": "INCOMPATIBLE_CON_HECHO_CONFIRMADO",
                    "detalle": motivo_incomp,
                })
                continue

            # 2. Validar descarte previo si no hay nueva evidencia que justifique reconsideración
            if falla_l in descartadas_previas:
                # Comprobar si la nueva evidencia menciona explícitamente el componente para reconsiderarlo
                reconsiderable = False
                if nueva_evidencia:
                    palabras_falla = [w for w in re.findall(r"\w+", falla_l) if len(w) > 4]
                    if any(w in nueva_evidencia.lower() for w in palabras_falla):
                        reconsiderable = True

                if not reconsiderable:
                    exclusiones.append({
                        "falla": falla,
                        "probabilidad_raw": prob,
                        "motivo": "RECHAZADA_PREVIAMENTE_SIN_NUEVA_EVIDENCIA",
                        "detalle": f"Hipótesis '{falla}' descartada por el usuario en turno previo",
                    })
                    continue

            candidatas_compatibles.append({
                "falla": falla,
                "probabilidad": prob,
            })

        # Si todas fueron filtradas, rescatar las compatibles aunque hayan sido descartadas
        if not candidatas_compatibles:
            for pred in predicciones_raw:
                falla = pred.get("falla", "")
                es_comp, _ = cls.validar_compatibilidad_hipotesis(falla, estado)
                if es_comp:
                    candidatas_compatibles.append({
                        "falla": falla,
                        "probabilidad": pred.get("probabilidad", 0.0),
                    })

        # Limitar a Top 3 para presentación
        return candidatas_compatibles[:3], exclusiones
