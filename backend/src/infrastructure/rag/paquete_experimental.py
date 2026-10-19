"""Carga explícita de un paquete experimental sellado; jamás reconstruye índices."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import faiss
import joblib
import numpy as np

SCHEMA = "carbot.rag.experimental/1"
VERSION = "RAG-03G-256"
RECIPE = "titulo+LF+texto;tfidf;float32;l2"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verificar_manifiesto(manifest, root):
    root = Path(root).resolve()
    if manifest.get("schema") != SCHEMA or manifest.get("version") != VERSION:
        raise ValueError("Esquema o versión experimental no soportado")
    if manifest.get("receta") != RECIPE or manifest.get("corpus_validado") is not False:
        raise ValueError("Receta/gobernanza inválida")
    roles = manifest.get("roles", {})
    if set(roles) != {"corpus", "vectorizador", "indice", "fragmentos"}:
        raise ValueError("Roles obligatorios incompletos")
    files = manifest.get("archivos", {})
    if not files or any(p not in files for p in roles.values()):
        raise ValueError("Inventario incompleto")
    for rel, spec in files.items():
        p = (root / rel).resolve()
        if not p.is_relative_to(root) or not p.is_file():
            raise ValueError(f"Archivo ausente o ruta inválida: {rel}")
        if p.stat().st_size != spec["bytes"] or sha(p) != spec["sha256"]:
            raise ValueError(f"Hash/tamaño inválido: {rel}")
    return {key: root / rel for key, rel in roles.items()}


def validar_vectores(corpus, vec, index, manifest, root, tolerancia=1e-6):
    try:
        paths = verificar_manifiesto(manifest, root)
        if corpus != json.loads(paths["corpus"].read_text(encoding="utf-8")):
            raise ValueError("Corpus en memoria difiere del artefacto sellado, incluidos metadatos")
        ids = [d["doc_id"] for d in corpus]
        if len(ids) != 256 or len(set(ids)) != len(ids) or ids != manifest["orden_doc_ids"]:
            raise ValueError("Corpus, identificadores u orden no corresponden al manifiesto")
        if index.ntotal != len(ids) or index.d != 35240 or manifest["dimension"] != index.d:
            raise ValueError("Dimensión/recuento experimental incorrecto")
        # Metadatos adicionales también están ligados al hash del corpus, no solo al TF-IDF.
        x = vec.transform([d["titulo"] + "\n" + d["texto"] for d in corpus]).toarray().astype("float32")
        if x.shape != (len(ids), index.d):
            raise ValueError("Dimensión del vectorizador incompatible")
        faiss.normalize_L2(x)
        actual = index.reconstruct_n(0, index.ntotal)
        if not np.isfinite(x).all() or not np.isfinite(actual).all():
            raise ValueError("Vectores no finitos")
        error = np.max(np.abs(x - actual), axis=1)
        limite = min(float(tolerancia), 1e-6)
        if not 0 <= limite <= 1e-6:
            raise ValueError("Tolerancia inválida")
        bad = [
            {"indice": int(i), "doc_id": ids[i], "max_error": float(error[i])}
            for i in np.flatnonzero(error > limite)
        ]
        if bad:
            return False, bad, "Correspondencia vectorial inválida"
        return True, [], f"256 vectores verificados; error máximo {float(error.max())}"
    except (OSError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        return False, [], str(exc)


def cargar_paquete(root):
    root = Path(root)
    manifest = json.loads(
        (root / "machine_learning/rag/experimentos/rag03c/manifiesto_rag03g.json").read_text(encoding="utf-8")
    )
    # Validar TODOS los hashes antes de deserializar joblib.
    paths = verificar_manifiesto(manifest, root)
    corpus = json.loads(paths["corpus"].read_text(encoding="utf-8"))
    vec = joblib.load(paths["vectorizador"])
    index = faiss.read_index(str(paths["indice"]))
    ok, _, reason = validar_vectores(corpus, vec, index, manifest, root)
    if not ok:
        raise ValueError(reason)
    return corpus, vec, index, manifest
