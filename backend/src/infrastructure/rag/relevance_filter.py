"""
Filtro y reordenador de relevancia multiseñal para procedimientos RAG.
Ajusta la puntuación de similitud coseno de FAISS utilizando:
- Coherencia con el Macro-Sistema inferido (MOTOR, FRENOS, etc.).
- Presencia y coincidencia de códigos DTC (autoridad diagnóstica).
- Coincidencia con hipótesis Top 1 / Top 2 / Top 3 del clasificador ML.
- Compatibilidad vehicular por marca y modelo (evita contaminación entre marcas).
"""

from __future__ import annotations

import unicodedata
from typing import Any, Dict, List, Optional

_TERMINOS_GENERICOS = {
    "cual", "como", "procedimiento", "prueba", "revisar", "vehiculo", "motor",
    "sistema", "falla", "problema", "manual", "tecnico", "consulta", "hacer",
}


def _normalizar(texto: str) -> str:
    if not texto:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )


def tiene_anclaje_lexico(consulta: str, candidato: Dict[str, Any], minimo: int = 2) -> bool:
    """Exige términos técnicos compartidos cuando la consulta no tiene área enrutable."""
    consulta_tokens = {
        token for token in _normalizar(consulta).split()
        if len(token) >= 5 and token not in _TERMINOS_GENERICOS
    }
    documento = _normalizar(f"{candidato.get('titulo', '')} {candidato.get('documento', '')}")
    coincidencias = {token for token in consulta_tokens if token in documento}
    return len(coincidencias) >= minimo


def reordenar_candidatos_rag(
    candidatos: List[Dict[str, Any]],
    macro_sistema: Optional[str] = None,
    top_fallas: Optional[List[Dict[str, Any]]] = None,
    codigos_dtc: Optional[List[str]] = None,
    confianza_ml: Optional[float] = None,
    marca: Optional[str] = None,
    modelo: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Reordena los candidatos recuperados por FAISS aplicando pesos multiseñal adaptativos.
    Cada candidato es un dict con:
    {"indice": int, "titulo": str, "documento": str, "similitud": float, "metadatos": dict}
    """
    if not candidatos:
        return []

    dtcs_norm = [c.strip().upper() for c in (codigos_dtc or []) if c]
    sistema_objetivo = (macro_sistema or "").strip().upper()
    conf_ml = float(confianza_ml) if confianza_ml is not None else 0.70

    marca_norm = _normalizar(marca or "")
    modelo_norm = _normalizar(modelo or "")
    es_marca_generica = marca_norm in ("", "generico", "vehiculo generico", "n/a", "desconocido", "none")

    top_fallas_norm = []
    top_probs = []
    for f_item in (top_fallas or [])[:3]:
        f_nom = f_item.get("falla") if isinstance(f_item, dict) else getattr(f_item, "falla", str(f_item))
        f_pr = float(f_item.get("probabilidad", 0.0) if isinstance(f_item, dict) else getattr(f_item, "probabilidad", 0.0))
        if f_nom:
            top_fallas_norm.append(_normalizar(f_nom))
            top_probs.append(f_pr)

    candidatos_ajustados = []
    for c in candidatos:
        score_base = float(c.get("similitud", 0.0))
        meta = c.get("metadatos", {}) or {}
        tit_norm = _normalizar(c.get("titulo", ""))
        doc_sistema = str(meta.get("sistema", "")).strip().upper()
        doc_falla = _normalizar(str(meta.get("falla", "")))
        doc_dtcs = [str(d).strip().upper() for d in meta.get("codigos_dtc", []) if d]
        scope = meta.get("vehicle_scope", "UNIVERSAL")
        doc_make = _normalizar(meta.get("make") or "")
        doc_model = _normalizar(meta.get("model") or "")

        factor_ajuste = 1.0

        # 1. Ajuste por DTC: Prioridad máxima cuando hay coincidencia oficial
        coincide_dtc = False
        if dtcs_norm:
            coincide_dtc = any(
                dtc in doc_dtcs or _normalizar(dtc) in tit_norm
                for dtc in dtcs_norm
            )
            if coincide_dtc:
                factor_ajuste *= 3.50

        # 2. Ajuste por Macro-Sistema ML (Adaptativo y continuo)
        if sistema_objetivo and sistema_objetivo != "DESCONOCIDO":
            if doc_sistema == sistema_objetivo:
                factor_ajuste *= 1.60
            elif doc_sistema and doc_sistema != sistema_objetivo:
                if coincide_dtc:
                    pass
                elif conf_ml < 0.70 or score_base >= 0.55:
                    factor_ajuste *= 0.80
                else:
                    factor_supresion = 0.35 if dtcs_norm else 0.60
                    factor_ajuste *= factor_supresion

        # 3. Ajuste por coincidencia con Top 1, Top 2, Top 3 de ML (proporcional a probabilidad)
        if top_fallas_norm and doc_falla:
            for f_norm, p_val in zip(top_fallas_norm, top_probs):
                if doc_falla in f_norm or f_norm in doc_falla:
                    factor_ajuste *= (1.15 + (p_val * 1.50))
                    break

        # 4. Ajuste por compatibilidad vehicular (Marca y Modelo)
        # Evita atribuir manuales específicos de una marca (ej. Toyota) a un vehículo de otra marca (ej. Nissan)
        if not es_marca_generica:
            if scope == "VEHICLE_SPECIFIC":
                if doc_make and (doc_make in marca_norm or marca_norm in doc_make):
                    factor_ajuste *= 1.40
                    if modelo_norm and doc_model and (doc_model in modelo_norm or modelo_norm in doc_model):
                        factor_ajuste *= 1.25
                else:
                    # Penalizar severamente manuales específicos de otra marca
                    factor_ajuste *= 0.05
            elif scope == "UNIVERSAL":
                # Los procedimientos universales se mantienen neutros como orientación general
                pass

        score_ajustado = score_base * factor_ajuste

        candidatos_ajustados.append({
            **c,
            "score_original": score_base,
            "similitud": score_ajustado,
            "factor_ajuste": round(factor_ajuste, 3),
        })

    # Ordenar descendente por similitud ajustada real
    candidatos_ajustados.sort(key=lambda x: x["similitud"], reverse=True)

    # Normalizar similitud final en rango [0.0, 1.0] para contratos del sistema
    for c in candidatos_ajustados:
        c["similitud"] = min(1.0, round(c["similitud"], 4))

    return candidatos_ajustados
