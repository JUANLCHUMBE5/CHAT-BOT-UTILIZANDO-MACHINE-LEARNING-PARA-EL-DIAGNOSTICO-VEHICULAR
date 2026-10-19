"""
Filtro y reordenador de relevancia multiseñal para procedimientos RAG.
Ajusta la puntuación de similitud coseno de FAISS utilizando:
- Coherencia con el Macro-Sistema inferido (MOTOR, FRENOS, etc.).
- Presencia y coincidencia de códigos DTC (autoridad diagnóstica).
- Coincidencia con hipótesis Top 1 / Top 2 / Top 3 del clasificador ML.
- Compatibilidad vehicular por marca y modelo (evita contaminación entre marcas).
- Controlador OEM de especificaciones cuantitativas y compatibilidad de taller.
"""

from __future__ import annotations

import unicodedata
from typing import Any, Dict, List, Optional

from src.infrastructure.rag.controlador_especificaciones_oem import clasificar_y_filtrar_oem

_TERMINOS_GENERICOS = {
    "cual",
    "como",
    "procedimiento",
    "prueba",
    "revisar",
    "vehiculo",
    "motor",
    "sistema",
    "falla",
    "problema",
    "manual",
    "tecnico",
    "consulta",
    "hacer",
    "medir",
    "pasos",
    "diagnostico",
    "especificacion",
    "tolerancia",
    "para",
    "este",
    "esta",
    "estos",
    "estas",
    "unos",
    "unas",
    "sobre",
    "entre",
    "desde",
    "hasta",
    "donde",
    "cuando",
    "pero",
    "sino",
    "cada",
    "mismo",
    "misma",
    "otro",
    "otra",
    "otros",
    "otras",
    "tener",
    "tiene",
    "tienen",
    "estar",
    "estan",
    "puede",
    "pueden",
    "debe",
    "deben",
    "haber",
    "habia",
    "habian",
    "tambien",
    "ralenti",
}


def _normalizar(texto: str) -> str:
    if not texto:
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def tiene_anclaje_lexico(consulta: str, candidato: Dict[str, Any], minimo: int = 2) -> bool:
    """Exige términos técnicos compartidos cuando la consulta no tiene área enrutable."""
    consulta_tokens = {
        token
        for token in _normalizar(consulta).split()
        if len(token) >= 5 and token not in _TERMINOS_GENERICOS
    }
    documento = _normalizar(f"{candidato.get('titulo', '')} {candidato.get('documento', '')}")
    coincidencias = {token for token in consulta_tokens if token in documento}
    return len(coincidencias) >= minimo


def _tiene_anclaje_pertinente(consulta: Optional[str], candidato: Dict[str, Any], score_base: float) -> bool:
    """Verifica si un documento tiene anclaje técnico genuino con la consulta antes de recibir impulso SVM o Macro-sistema."""
    if not consulta:
        return score_base >= 0.12
    tokens_consulta = {
        token
        for token in _normalizar(consulta).split()
        if len(token) >= 4 and token not in _TERMINOS_GENERICOS
    }
    titulo_doc = _normalizar(candidato.get("titulo", ""))
    texto_doc = _normalizar(f"{titulo_doc} {candidato.get('documento', '')}")
    coincide_titulo = any(t in titulo_doc for t in tokens_consulta)
    coincidencias_cuerpo = sum(1 for t in tokens_consulta if t in texto_doc)

    if coincide_titulo:
        return score_base >= 0.05
    return coincidencias_cuerpo >= 2 and score_base >= 0.10


def _coinciden_fallas(falla_doc: str, falla_modelo: str) -> bool:
    """Comprueba coincidencia semántica o solapamiento multitérmino entre falla de metadatos y clase de modelo."""
    if not falla_doc or not falla_modelo:
        return False
    if falla_doc in falla_modelo or falla_modelo in falla_doc:
        return True
    tokens_doc = {t for t in _normalizar(falla_doc).split() if len(t) >= 4 and t not in _TERMINOS_GENERICOS}
    tokens_mod = {
        t for t in _normalizar(falla_modelo).split() if len(t) >= 4 and t not in _TERMINOS_GENERICOS
    }
    return len(tokens_doc.intersection(tokens_mod)) >= 2


def reordenar_candidatos_rag(
    candidatos: List[Dict[str, Any]],
    macro_sistema: Optional[str] = None,
    top_fallas: Optional[List[Dict[str, Any]]] = None,
    codigos_dtc: Optional[List[str]] = None,
    confianza_ml: Optional[float] = None,
    marca: Optional[str] = None,
    modelo: Optional[str] = None,
    consulta: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Reordena los candidatos devueltos por FAISS calculando una similitud multiseñal ponderada.
    Conserva la similitud pura (score_base) y calcula similitud_rerank.
    """
    if not candidatos:
        return []

    sistema_objetivo = (macro_sistema or "").strip().upper()
    conf_ml = float(confianza_ml) if confianza_ml is not None else 0.70

    dtcs_norm = [c.strip().upper() for c in (codigos_dtc or []) if c]
    marca_norm = _normalizar(marca or "")
    modelo_norm = _normalizar(modelo or "")
    es_marca_generica = marca_norm in (
        "",
        "generico",
        "vehiculo generico",
        "n/a",
        "desconocido",
        "none",
        "universal",
        "multimarca",
    )

    top_fallas_norm: List[str] = []
    top_probs: List[float] = []
    if top_fallas:
        for f in top_fallas[:3]:
            if isinstance(f, dict):
                f_name = f.get("falla") or f.get("nombre") or ""
                p = float(f.get("probabilidad", 0.50))
            elif isinstance(f, (list, tuple)) and len(f) >= 2:
                f_name = str(f[0])
                p = float(f[1])
            else:
                f_name = getattr(f, "falla", str(f))
                p = float(getattr(f, "probabilidad", 0.50))
            if f_name:
                top_fallas_norm.append(_normalizar(f_name))
                top_probs.append(p)

    candidatos_ajustados: List[Dict[str, Any]] = []

    for c in candidatos:
        meta = c.get("metadatos", {}) or {}
        score_base = float(c.get("similitud", 0.0))
        factor_ajuste = 1.0

        doc_sistema = str(meta.get("sistema", "")).strip().upper()
        doc_falla = _normalizar(str(meta.get("falla", "")))
        doc_dtcs = [
            str(d).strip().upper()
            for d in (meta.get("codigos_dtc") or meta.get("dtcs_relacionados") or [])
            if d
        ]
        tit_norm = _normalizar(c.get("titulo", ""))

        scope = str(meta.get("vehicle_scope") or meta.get("scope") or "UNIVERSAL").upper()
        doc_make = _normalizar(meta.get("make") or meta.get("marca") or c.get("marca") or "")
        doc_model = _normalizar(meta.get("model") or meta.get("modelo") or c.get("modelo") or "")

        # 1. Ajuste por DTC: Prioridad máxima cuando hay coincidencia oficial
        coincide_dtc = False
        if dtcs_norm:
            coincide_dtc = any(dtc in doc_dtcs or _normalizar(dtc) in tit_norm for dtc in dtcs_norm)
            if coincide_dtc:
                factor_ajuste *= 3.50

        # 2. Ajuste por Macro-Sistema ML (Adaptativo y continuo)
        sistemas_afines = {
            ("INSTRUMENTAL", "MOTOR"),
            ("MOTOR", "INSTRUMENTAL"),
            ("TRANSMISION", "MOTOR"),
            ("SUSPENSION", "DIRECCION"),
            ("DIRECCION", "SUSPENSION"),
        }
        es_sistema_afin = (sistema_objetivo, doc_sistema) in sistemas_afines

        if sistema_objetivo and sistema_objetivo != "DESCONOCIDO":
            if doc_sistema == sistema_objetivo:
                if _tiene_anclaje_pertinente(consulta, c, score_base):
                    factor_ajuste *= 1.60
                else:
                    factor_ajuste *= 1.05
            elif es_sistema_afin:
                if _tiene_anclaje_pertinente(consulta, c, score_base):
                    factor_ajuste *= 1.15
                else:
                    factor_ajuste *= 0.90
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
            if _tiene_anclaje_pertinente(consulta, c, score_base):
                for f_norm, p_val in zip(top_fallas_norm, top_probs):
                    if _coinciden_fallas(doc_falla, f_norm):
                        factor_ajuste *= 1.15 + (p_val * 1.50)
                        break

        # 4. Ajuste por compatibilidad vehicular (Marca y Modelo)
        # Permite coincidencia por tokens de marca y modelo para evitar descartar "Hyundai Accent" frente a "Hyundai Motor America"
        if not es_marca_generica:
            doc_make_tokens = {
                t
                for t in doc_make.split()
                if len(t) >= 3 and t not in ("motor", "america", "motors", "company", "group")
            }
            marca_tokens = {t for t in marca_norm.split() if len(t) >= 3}
            make_coincide = bool(doc_make_tokens.intersection(marca_tokens)) or (
                doc_make in marca_norm or marca_norm in doc_make
            )

            doc_model_tokens = {t for t in doc_model.split() if len(t) >= 3}
            modelo_tokens = {t for t in modelo_norm.split() if len(t) >= 3}
            model_coincide = (
                bool(doc_model_tokens.intersection(modelo_tokens))
                or (doc_model in modelo_norm or modelo_norm in doc_model)
                or any(t in doc_model for t in marca_tokens)
            )

            if scope == "VEHICLE_SPECIFIC":
                if make_coincide:
                    factor_ajuste *= 1.40
                    if model_coincide:
                        factor_ajuste *= 1.25
                else:
                    # Penalizar severamente manuales específicos de otra marca
                    factor_ajuste *= 0.05
            elif scope == "UNIVERSAL":
                # Los procedimientos universales se mantienen neutros como orientación general
                pass

        # 5. Integración OEM RAG-03E: Control y Tipificación de Especificaciones y Compatibilidad
        categoria_doc, factor_oem, dictamen_seg = clasificar_y_filtrar_oem(
            consulta=consulta or "",
            candidato=c,
            vehiculo_consulta=f"{marca or ''} {modelo or ''}".strip(),
            sistema_consulta=sistema_objetivo or "",
        )
        factor_ajuste *= factor_oem

        score_ajustado = score_base * factor_ajuste

        candidatos_ajustados.append(
            {
                **c,
                "score_base": score_base,
                "score_original": score_base,
                "similitud_rerank": score_ajustado,
                "similitud": score_ajustado,
                "factor_ajuste": round(factor_ajuste, 3),
                "categoria_doc": categoria_doc,
                "dictamen_seguridad": dictamen_seg,
            }
        )

    # Ordenar descendente por similitud ajustada real
    candidatos_ajustados.sort(key=lambda x: x["similitud"], reverse=True)

    # Normalizar similitud final en rango [0.0, 1.0] para contratos del sistema
    for c in candidatos_ajustados:
        c["similitud"] = min(1.0, round(c["similitud"], 4))

    return candidatos_ajustados
