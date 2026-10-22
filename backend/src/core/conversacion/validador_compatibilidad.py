"""Validador de compatibilidad técnica de hipótesis y control de descartes previos (Fase 9.8).

Asegura que las hipótesis presentadas al mecánico sean físicamente consistentes con los hechos
confirmados del vehículo (combustible, transmisión) y que no se repitan hipótesis previamente
rechazadas a menos que exista nueva evidencia clínica que lo justifique.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

from src.config import settings
from src.core.conversacion.prioridad_inspeccion import ordenar_inspeccion
from src.core.conversacion.models import ConversationState, FactState
from src.core.conversacion.ruteador_sistema import (
    detectar_ruta_sistema,
    hipotesis_compatibles_con_ruta,
    requisito_tecnico_ausente,
    tiene_descarte_de_componente,
)

_COMPONENTES_HIPOTESIS = (
    ("bobina", re.compile(r"\b(?:bobinas?|coil(?:s|\s+pack)?)\b")),
    ("bujia_precalentamiento", re.compile(r"\b(?:precalentamiento|incandescentes?|glow\s*plugs?|calentadores?)\b")),
    ("bujia", re.compile(r"\b(?:buj[ií]as?|spark\s+plugs?)\b")),
    ("inyector", re.compile(r"\b(?:inyectores?|injectores?|inyector[a-z]*)\b")),
    ("bateria", re.compile(r"\b(?:bater[ií]as?|acumulador)\b")),
    ("alternador", re.compile(r"\b(?:alternadores?)\b")),
    ("motor_arranque", re.compile(r"\b(?:motor\s+de\s+arranque|arrancador|solenoide)\b")),
    ("maf", re.compile(r"\b(?:maf|sensor\s+de\s+flujo\s+de\s+aire)\b")),
    ("map", re.compile(r"\b(?:map|sensor\s+de\s+presi[oó]n\s+del\s+m[uú]ltiple)\b")),
    ("iac", re.compile(r"\b(?:iac|v[aá]lvula\s+de\s+control\s+de\s+aire)\b")),
    ("cuerpo_aceleracion", re.compile(r"\b(?:cuerpo\s+de\s+aceleraci[oó]n|mariposa)\b")),
    ("bomba_combustible", re.compile(r"\b(?:bomba\s+de\s+combustible|bomba\s+de\s+gasolina)\b")),
    ("sensor_oxigeno", re.compile(r"\b(?:sensor\s+de\s+ox[ií]geno|sonda\s+lambda|sensor\s+o2)\b")),
    ("termostato", re.compile(r"\b(?:termostato)\b")),
    ("radiador", re.compile(r"\b(?:radiador|mangueras?\s+del\s+radiador)\b")),
    ("frenos", re.compile(r"\b(?:frenos?|pastillas?|discos?\s+de\s+freno)\b")),
    ("suspension", re.compile(r"\b(?:suspensi[oó]n|amortiguadores?|r[oó]tulas?)\b")),
    ("embrague", re.compile(r"\b(?:embrague|clutch)\b")),
)
_PATRON_EVIDENCIA_ANOMALA = re.compile(
    r"\b(?:detect[eéó]|encontr[eéó]|registr[eéó]|marc[oó]|mide|midi[oó]|sali[oó]|result[oó]|"
    r"presenta|confirm[oó]|se observa|se ve)\b.{0,70}\b(?:anormal|irregular|bajo|baja|alt[oa]|"
    r"fuera de rango|d[eé]bil|intermitente|defectuos[oa]|dañad[oa]|sin chispa|no funciona)\b",
    re.IGNORECASE,
)
_PATRON_RESULTADO_NORMAL = re.compile(
    r"\b(?:est[aá] bien|est[aá] normal|funciona bien|funciona normal|sal[ií]o normal|"
    r"resultado normal|sin anomal[ií]a|no presenta falla)\b",
    re.IGNORECASE,
)


def _normalizar_hipotesis(texto: str) -> str:
    texto = unicodedata.normalize("NFD", str(texto or "").casefold())
    return " ".join(
        "".join(c for c in texto if unicodedata.category(c) != "Mn").split()
    )


def _familias_componente(texto: str) -> set[str]:
    normalizado = _normalizar_hipotesis(texto)
    es_precalentamiento = bool(re.search(r"\b(?:precalentamiento|incandescentes?|glow\s*plugs?|calentadores?)\b", normalizado))
    familias = set()
    for familia, patron in _COMPONENTES_HIPOTESIS:
        if patron.search(normalizado):
            if familia == "bujia" and es_precalentamiento:
                continue
            familias.add(familia)
    return familias


def _evidencia_nueva_reabre(falla: str, evidencia: Optional[str]) -> bool:
    """Solo permite reconsiderar tras un resultado anómalo explícito del mismo componente."""
    if not evidencia:
        return False
    familias = _familias_componente(falla) & _familias_componente(evidencia)
    if not familias or _PATRON_RESULTADO_NORMAL.search(evidencia):
        return False
    return bool(_PATRON_EVIDENCIA_ANOMALA.search(evidencia))


def hipotesis_rechazada_en_texto(texto: str, descartadas: Optional[List[str]]) -> bool:
    """Detecta una causa rechazada en una síntesis libre, incluyendo alias de componentes."""
    salida = _normalizar_hipotesis(texto)
    if not salida:
        return False
    for rechazada in descartadas or []:
        if rechazada.startswith("componente:"):
            familia = rechazada.split(":", 1)[1]
            if familia in _familias_componente(salida):
                return True
            continue
        label = _normalizar_hipotesis(rechazada)
        familias = _familias_componente(label)
        if label and label in salida:
            return True
        if familias and familias & _familias_componente(salida):
            return True
    return False


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
        if not estado or (not estado.hechos and not estado.historial_mensajes_usuario and not estado.combustible):
            return True, None

        falla_l = falla.lower()

        # A. Reglas de combustible
        hecho_combustible = estado.obtener_hecho("combustible") or estado.obtener_hecho("tipo_combustible")
        comb_raw = str(getattr(estado, "combustible", "") or (hecho_combustible.valor if hecho_combustible else "")).strip()
        if comb_raw:
            comb = "".join(
                c for c in unicodedata.normalize("NFD", comb_raw.lower())
                if unicodedata.category(c) != "Mn"
            ).upper()

            # Gasolina, GLP, GNV incompatibles con sistemas exclusivos Diésel (AdBlue, DPF, FAP, Urea, Common Rail Diesel, Precalentamiento)
            if comb in ("GASOLINA", "GNV", "GLP", "NAFTA"):
                if re.search(r"\b(adblue|def|diesel|dpf|fap|urea|filtro de particulas|common rail diesel|precalentamiento|incandescentes?|glow\s*plugs?)\b", falla_l):
                    return False, f"INCOMPATIBLE_CON_HECHO_CONFIRMADO: Combustible={comb} incompatible con sistemas Diésel/AdBlue/DPF/Precalentamiento"

            # Diésel incompatible con encendido por chispa, carburadores o sistemas de gasolina/gas (conservando bujías de precalentamiento)
            elif comb == "DIESEL":
                es_precalentamiento = bool(re.search(r"\b(?:precalentamiento|incandescentes?|glow\s*plugs?|calentadores?)\b", falla_l))
                if not es_precalentamiento and re.search(r"\b(bujia|buj[ií]as|bobina|gasolina|bomba de gasolina|gnv|glp|carburador|chispa)\b", falla_l):
                    return False, f"INCOMPATIBLE_CON_HECHO_CONFIRMADO: Combustible={comb} no utiliza componentes de gasolina, chispa ni gas"

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

        # C. Reglas de sistema de arranque y batería (Fase 2 - Mediciones Cuantitativas)
        caida_excesiva = estado.obtener_hecho("caida_tension_excesiva")
        voltaje_arranque_normal = estado.obtener_hecho("voltaje_arranque_normal")
        if (caida_excesiva and caida_excesiva.valor == "NO") or (voltaje_arranque_normal and voltaje_arranque_normal.valor == "SI"):
            if any(term in falla_l for term in (
                "fuga parasita", "fuga parásita", "consumo nocturno",
                "bateria descargada", "batería descargada", "bateria en mal estado",
                "batería en mal estado", "bornes sulfatados", "borne sulfatado",
            )):
                return False, "INCOMPATIBLE_CON_HECHO_CONFIRMADO: Voltaje normal en arranque (>= 9.6V) descarta batería descargada y consumo parásito"

        # D. Reglas de alternador y carga en marcha
        texto_hist = " ".join(getattr(estado, "historial_mensajes_usuario", []) or []).lower()
        if any(w in texto_hist for w in ("motor prendido", "motor encendido", "en marcha", "andando", "luces altas")):
            if any(term in falla_l for term in ("fuga parasita", "fuga parásita", "consumo nocturno")):
                return False, "INCOMPATIBLE_CON_HECHO_CONFIRMADO: Con motor prendido corresponde evaluar alternador/carga, no fuga en reposo"

        # E. Reglas de combustible dual (GLP / GNV) y descarte de componentes de gasolina
        if any(g in texto_hist for g in ("glp", "gnv", "a gas", "conmuta a gas", "dual glp", "dual gnv")):
            gasolina_buena = any(
                w in texto_hist for w in (
                    "gasolina anda perfecto", "a gasolina anda perfecto", "en gasolina anda bien",
                    "a gasolina anda bien", "a gasolina perfecto", "gasolina sin problema",
                    "en gasolina no tiene ningún problema", "en gasolina no falla", "a gasolina acelera parejito"
                )
            ) or any(
                w in texto_hist for w in ("conmuta a gas empieza", "falla a gas", "solo a gas", "cuando pasa a gas")
            )
            if gasolina_buena and any(bg in falla_l for bg in ("bomba de gasolina", "presion de gasolina", "presión de gasolina", "inyectores sucios")):
                return False, "INCOMPATIBLE_CON_HECHO_CONFIRMADO: El vehículo opera correctamente en gasolina; la falla ocurre únicamente al conmutar a gas (GLP/GNV)"

        # F. Reglas de ruidos mecánicos en suspensión/ruedas vs motor de arranque
        if any(w in texto_hist for w in ("rompemuelles", "baches", "pistas rotas", "rueda delantera", "rueda trasera", "al amortiguar", "suspension", "suspensión")):
            if any(term in falla_l for term in ("motor de arranque", "solenoide", "carbones gastados", "bendix")):
                return False, "INCOMPATIBLE_CON_HECHO_CONFIRMADO: La queja es un ruido en rodamiento/suspensión en marcha; no corresponde a motor de arranque"

        # G. Regla de motor que gira con fuerza vs batería descargada
        if any(w in texto_hist for w in ("gira motor con fuerza", "gira con fuerza", "arranque potente", "motor gira bien")):
            if any(term in falla_l for term in ("bateria descargada", "batería descargada", "bornes sulfatados")):
                return False, "INCOMPATIBLE_CON_HECHO_CONFIRMADO: El motor de arranque gira con fuerza, lo que físicamente descarta batería descargada"

        return True, None

    @classmethod
    def filtrar_hipotesis_almacenadas(
        cls,
        hipotesis: List[Dict[str, Any]],
        estado: Optional[ConversationState],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Filtra hipótesis ya persistidas sin alterar sus probabilidades.

        Las predicciones crudas se conservan en trazabilidad; esta función solo
        decide cuáles pueden volver a presentarse al mecánico.
        """
        compatibles: List[Dict[str, Any]] = []
        excluidas: List[Dict[str, Any]] = []
        for hipotesis_item in hipotesis or []:
            falla = str(hipotesis_item.get("falla", ""))
            compatible, motivo = cls.validar_compatibilidad_hipotesis(falla, estado)
            if compatible:
                compatibles.append(dict(hipotesis_item))
            else:
                excluidas.append({
                    "falla": falla,
                    "probabilidad_raw": hipotesis_item.get("probabilidad", 0.0),
                    "motivo": "INCOMPATIBLE_CON_HECHO_CONFIRMADO",
                    "detalle": motivo,
                })
        return compatibles, excluidas

    @staticmethod
    def _clave_hipotesis(falla: str) -> str:
        """Genera una clave estable para no presentar dos veces la misma falla.

        El Linear SVM puede devolver la misma etiqueta con diferencias menores de
        mayúsculas, tildes o puntuación. Para el mecánico eso no constituye una
        alternativa diagnóstica distinta.
        """
        sin_tildes = unicodedata.normalize("NFD", falla or "")
        sin_tildes = "".join(
            caracter for caracter in sin_tildes
            if unicodedata.category(caracter) != "Mn"
        )
        return re.sub(r"[^a-z0-9]+", " ", sin_tildes.lower()).strip()

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

        descartadas_previas = list(
            getattr(estado, "hipotesis_descartadas", []) if estado else []
        )

        candidatas_compatibles: List[Dict[str, Any]] = []
        exclusiones: List[Dict[str, Any]] = []
        claves_presentadas: set[str] = set()
        ruta = detectar_ruta_sistema(estado, nueva_evidencia)

        # Masa de probabilidad de candidatos viables ante descarte físico de hipótesis dominantes incompatibles
        exclusiones_incompatibles_raw: set[str] = set()
        for p_cand in predicciones_raw:
            f_cand = p_cand.get("falla", "")
            es_comp_cand, _ = cls.validar_compatibilidad_hipotesis(f_cand, estado)
            if not es_comp_cand or not hipotesis_compatibles_con_ruta(f_cand, ruta.sistema):
                exclusiones_incompatibles_raw.add(f_cand)

        masa_compatible = sum(
            float(p.get("probabilidad", 0.0) or 0.0)
            for p in predicciones_raw
            if p.get("falla", "") not in exclusiones_incompatibles_raw
        )

        # Evaluar cada predicción de la lista RAW
        for pred in predicciones_raw:
            falla = pred.get("falla", "")
            prob = pred.get("probabilidad", 0.0)
            origen_probabilidad = str(pred.get("origen_probabilidad", "SVM")).upper()

            requisito = requisito_tecnico_ausente(estado, falla, nueva_evidencia)
            if requisito:
                compatible, motivo = cls.validar_compatibilidad_hipotesis(falla, estado)
                exclusiones.append({"falla": falla, "probabilidad_raw": prob,
                                    "motivo": ("EQUIPAMIENTO_NO_CONFIRMADO" if compatible
                                               else "INCOMPATIBLE_CON_HECHO_CONFIRMADO"),
                                    "detalle": requisito if compatible else motivo})
                continue

            if not hipotesis_compatibles_con_ruta(falla, ruta.sistema):
                exclusiones.append({
                    "falla": falla,
                    "probabilidad_raw": prob,
                    "motivo": "SISTEMA_INCOMPATIBLE_CON_EVIDENCIA",
                    "detalle": f"Ruta activa {ruta.sistema}: {', '.join(ruta.evidencia)}",
                })
                continue

            if tiene_descarte_de_componente(estado, falla):
                exclusiones.append({
                    "falla": falla,
                    "probabilidad_raw": prob,
                    "motivo": "RECHAZADA_PREVIAMENTE_SIN_NUEVA_EVIDENCIA",
                    "detalle": "El mecánico ya informó que este componente fue revisado o descartado.",
                })
                continue

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

            # Probabilidad efectiva condicional si se descartaron hipótesis incompatibles dominantes
            prob_eval = float(prob or 0)
            if exclusiones_incompatibles_raw and masa_compatible > 0 and prob_eval > 0:
                prob_condicional = prob_eval / masa_compatible
                prob_eval = max(prob_eval, prob_condicional)

            if (
                origen_probabilidad == "SVM"
                and prob_eval < settings.diagnostic.min_presentable_confidence
            ):
                exclusiones.append({
                    "falla": falla, "probabilidad_raw": prob,
                    "motivo": "CONFIANZA_INSUFICIENTE_PARA_PRESENTAR",
                })
                continue

            # El descarte del mecánico rige por componente/hipótesis, no solo
            # por coincidencia literal. Se conserva como rechazo reportado,
            # no como confirmación física. Solo evidencia anómala nueva del
            # mismo componente permite reconsiderar la candidata.
            familias_falla = _familias_componente(falla)
            rechazos_aplicables = []
            for rechazada in descartadas_previas:
                if rechazada.startswith("componente:"):
                    aplica = rechazada.split(":", 1)[1] in familias_falla
                else:
                    etiqueta_rechazada = _normalizar_hipotesis(rechazada)
                    aplica = bool(
                        etiqueta_rechazada == _normalizar_hipotesis(falla)
                        or (
                            familias_falla
                            and familias_falla & _familias_componente(etiqueta_rechazada)
                        )
                    )
                if aplica:
                    rechazos_aplicables.append(rechazada)

            if rechazos_aplicables:
                if _evidencia_nueva_reabre(falla, nueva_evidencia):
                    exclusiones.append({
                        "falla": falla,
                        "probabilidad_raw": prob,
                        "motivo": "RECONSIDERADA_CON_EVIDENCIA_NUEVA",
                        "detalle": "Se conserva la candidata por un resultado anómalo nuevo del mismo componente; no confirma la falla.",
                    })
                else:
                    exclusiones.append({
                        "falla": falla,
                        "probabilidad_raw": prob,
                        "motivo": "RECHAZADA_PREVIAMENTE_SIN_NUEVA_EVIDENCIA",
                        "detalle": f"Hipótesis o componente rechazado por el usuario: {', '.join(rechazos_aplicables)}",
                    })
                    continue

            clave = cls._clave_hipotesis(falla)
            if not clave or clave in claves_presentadas:
                exclusiones.append({
                    "falla": falla,
                    "probabilidad_raw": prob,
                    "motivo": "DUPLICADA_EN_TOP",
                    "detalle": "La misma hipótesis ya está presentada como una alternativa anterior.",
                })
                continue

            candidatas_compatibles.append({
                "falla": falla,
                "probabilidad": round(prob_eval, 4),
                "origen_probabilidad": origen_probabilidad,
            })
            claves_presentadas.add(clave)

        # Limitar a Top 3 para presentación
        return ordenar_inspeccion(candidatas_compatibles, estado)[:3], exclusiones
